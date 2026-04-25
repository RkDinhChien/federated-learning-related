# ============================================================
# Passive Label Inference Attack using MixMatch for VFL
# FOR RESEARCH / SECURITY AUDIT PURPOSES ONLY
# ============================================================

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Beta
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from typing import Tuple
from PIL import Image

# ──────────────────────────────────────────────────────────────
#  0. VFL Image Split Helper
# ──────────────────────────────────────────────────────────────

def _split_client_half(images: torch.Tensor, side: str = "right") -> torch.Tensor:
    """
    Nhan vao half_B (B, 3, 32, 16) hoac full image (B, 3, 32, 32).
    - Neu da la half (width<=16): tra ve nguyen khong cat
    - Neu la full image (width=32): cat theo side
    """
    if images.dim() == 3:
        images = images.unsqueeze(0)
    # Da la half_B roi, khong cat them
    if images.shape[-1] <= 16:
        return images
    # Full image -> cat
    if side == "right":
        return images[:, :, :, 16:]
    else:
        return images[:, :, :, :16]


def _validate_and_convert_image(img, expected_shape=(3, 32, 32)):
    if isinstance(img, torch.Tensor):
        if img.ndim != 3:
            raise ValueError(f"Expected tensor shape (C, H, W), got {img.shape}.")
        # KHONG chia /255 neu anh da duoc normalize (co gia tri am hoac > 1.0)
        # Anh tu VFLCIFARDataset da qua Normalize() nen co range ~[-2.4, 2.7]
        return img.float()
    elif isinstance(img, Image.Image):
        img_array = np.array(img, dtype=np.float32)
        if img_array.ndim == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        if img_array.max() > 1.0:
            img_array = img_array / 255.0
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).float()
        if img_tensor.shape != expected_shape:
            raise ValueError(f"Shape mismatch: expected {expected_shape}, got {img_tensor.shape}.")
        return img_tensor
    elif isinstance(img, np.ndarray):
        img_array = img.astype(np.float32)
        if img_array.ndim == 3:
            if img_array.shape[0] in [1, 3, 4]:
                img_tensor = torch.from_numpy(img_array).float()
            else:
                if img_array.max() > 1.0:
                    img_array = img_array / 255.0
                img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).float()
        elif img_array.ndim == 2:
            if img_array.max() > 1.0:
                img_array = img_array / 255.0
            img_tensor = torch.from_numpy(img_array).unsqueeze(0).float()
        else:
            raise ValueError(f"Unexpected image shape: {img_array.shape}")
        if img_tensor.shape != expected_shape:
            raise ValueError(f"Shape mismatch: expected {expected_shape}, got {img_tensor.shape}")
        return img_tensor
    else:
        raise TypeError(f"Unsupported image format: {type(img).__name__}.")


# ──────────────────────────────────────────────────────────────
#  1. InferenceHead
# ──────────────────────────────────────────────────────────────

class InferenceHead(nn.Module):
    """
    MLP head appended after a frozen BottomModel.
    KHONG dung BatchNorm (gay unstable khi labeled/unlabeled batch size khac nhau).
    Dung Dropout lam regularizer thay the.

    Architecture:
        Linear(128 -> 512) -> ReLU -> Dropout(0.4)
        Linear(512 -> 256) -> ReLU -> Dropout(0.4)
        Linear(256 -> 10)
    """

    def __init__(
        self,
        embedding_dim: int = 128,
        hidden_dim: int = 512,
        num_classes: int = 10,
        dropout_rate: float = 0.4,
    ):
        super(InferenceHead, self).__init__()

        self.net = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
            nn.Linear(hidden_dim // 2, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        return self.net(embedding)


# ──────────────────────────────────────────────────────────────
#  2. sharpen()
# ──────────────────────────────────────────────────────────────

def sharpen(predictions: torch.Tensor, temperature: float = 0.5) -> torch.Tensor:
    if temperature <= 0:
        raise ValueError(f"temperature must be > 0, got {temperature}")
    sharpened = predictions.pow(1.0 / temperature)
    pseudo_labels = sharpened / (sharpened.sum(dim=1, keepdim=True) + 1e-8)
    return pseudo_labels


# ──────────────────────────────────────────────────────────────
#  3. mixup()
# ──────────────────────────────────────────────────────────────

def mixup(
    x1: torch.Tensor,
    x2: torch.Tensor,
    y1: torch.Tensor,
    y2: torch.Tensor,
    alpha: float = 0.75,
) -> Tuple[torch.Tensor, torch.Tensor]:
    if alpha <= 0:
        raise ValueError(f"alpha must be > 0, got {alpha}")
    dist = Beta(
        torch.tensor(alpha, dtype=torch.float32),
        torch.tensor(alpha, dtype=torch.float32),
    )
    lam = dist.sample().item()
    lam = max(lam, 1.0 - lam)
    x_mixed = lam * x1 + (1.0 - lam) * x2
    y_mixed = lam * y1 + (1.0 - lam) * y2
    return x_mixed, y_mixed


# ──────────────────────────────────────────────────────────────
#  4. generate_auxiliary_labels()
# ──────────────────────────────────────────────────────────────

def generate_auxiliary_labels(
    dataset,
    num_labels: int = 200,   # FIX: tăng từ 40 → 200 (20 per class)
    seed: int = 42,
    balanced: bool = True,   # FIX: lấy đều theo class để tránh bias
) -> Tuple[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor]]:
    """
    Split dataset thành labeled set X và unlabeled set U.

    FIX quan trọng:
    - Tăng num_labels lên 200 (20 per class) thay vì 40 (quá ít)
    - Lấy đều theo class (balanced=True) để tránh class imbalance

    Args:
        dataset    : PyTorch Dataset. Each item is (image, label).
        num_labels : Số labeled samples. Default 200 (20 per class × 10 classes).
        seed       : Random seed.
        balanced   : Nếu True, lấy đều mỗi class.

    Returns:
        X = (images_X, labels_X)
        U = (images_U, labels_U_true)
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    n_total = len(dataset)

    def _get_label(dataset, idx):
        """Get label without loading full image."""
        if hasattr(dataset, 'targets'):
            return int(dataset.targets[idx])
        else:
            _, lbl = dataset[idx]
            return int(lbl)

    if balanced:
        # Lấy num_labels/10 mẫu từ mỗi class
        num_classes = 10
        per_class   = num_labels // num_classes

        # Group indices by class
        class_indices = {c: [] for c in range(num_classes)}
        for i in range(n_total):
            lbl = _get_label(dataset, i)
            class_indices[lbl].append(i)

        labeled_indices = []
        for c in range(num_classes):
            idxs = np.array(class_indices[c])
            chosen = np.random.choice(idxs, size=min(per_class, len(idxs)), replace=False)
            labeled_indices.extend(chosen.tolist())

        labeled_set   = set(labeled_indices)
        unlabeled_indices = [i for i in range(n_total) if i not in labeled_set]
        unlabeled_indices = np.random.permutation(unlabeled_indices).tolist()
    else:
        all_indices = np.random.permutation(n_total)
        labeled_indices   = all_indices[:num_labels].tolist()
        unlabeled_indices = all_indices[num_labels:].tolist()

    def _collect(indices):
        imgs, labels = [], []
        for idx in indices:
            img, lbl = dataset[int(idx)]
            img = _validate_and_convert_image(img, expected_shape=img.shape if isinstance(img, torch.Tensor) else (3, 32, 32))
            imgs.append(img)
            labels.append(int(lbl))
        return torch.stack(imgs), torch.tensor(labels, dtype=torch.long)

    print(f"[generate_auxiliary_labels] Collecting {len(labeled_indices)} labeled samples (balanced)...")
    images_X, labels_X = _collect(labeled_indices)

    print(f"[generate_auxiliary_labels] Collecting {len(unlabeled_indices)} unlabeled samples...")
    images_U, labels_U_true = _collect(unlabeled_indices)

    print(f"[generate_auxiliary_labels] Done. X: {images_X.shape}, U: {images_U.shape}")
    return (images_X, labels_X), (images_U, labels_U_true)


# ──────────────────────────────────────────────────────────────
#  5. train_inference_head()
# ──────────────────────────────────────────────────────────────

def train_inference_head(
    bottom_model: nn.Module,
    inference_head: nn.Module,
    X: Tuple[torch.Tensor, torch.Tensor],
    U: Tuple[torch.Tensor, torch.Tensor],
    epochs: int = 200,
    lr: float = 1e-3,
    batch_size: int = 64,
    lambda_u: float = 1.0,
    temperature: float = 0.5,
    alpha_mixup: float = 0.75,
    K_augments: int = 2,
    device: str = "cuda",
    warmup_epochs: int = 20,
) -> nn.Module:
    bottom_model   = bottom_model.to(device)
    inference_head = inference_head.to(device)

    for param in bottom_model.parameters():
        param.requires_grad_(False)
    bottom_model.eval()

    optimizer = optim.Adam(inference_head.parameters(), lr=lr, weight_decay=1e-4)
    # StepLR: giam lr 50% moi 1/3 so epochs - on dinh hon CosineAnnealing voi it epochs
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=max(1, epochs//3), gamma=0.5)

    images_X, labels_X = X
    images_U, _        = U
    num_classes        = 10

    # DataLoaders tren RAW IMAGES (khong pre-compute) de tranh overfitting
    labeled_ds   = TensorDataset(images_X, labels_X)
    unlabeled_ds = TensorDataset(images_U)

    # Loop chinh theo UNLABELED, labeled duoc cycle lai
    unlabeled_loader = DataLoader(unlabeled_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    labeled_loader   = DataLoader(labeled_ds, batch_size=min(batch_size, len(images_X)),
                                  shuffle=True, drop_last=False)

    sep = "-" * 60
    print(f"\n{sep}")
    print(f"  MixMatch Training - {epochs} epochs")
    print(f"  Labeled   : {len(images_X)} samples  ({len(labeled_loader)} batches/epoch)")
    print(f"  Unlabeled : {len(images_U)} samples  ({len(unlabeled_loader)} batches/epoch)")
    print(f"  Warmup    : {warmup_epochs} epochs (supervised only)")
    print(f"  Device    : {device}")
    print(f"{sep}\n")

    ce_loss  = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()

    # Embedding-space noise augmentation
    def augment_emb(emb, noise_std=0.1):
        return emb + torch.randn_like(emb) * noise_std

    for epoch in range(1, epochs + 1):
        inference_head.train()
        epoch_loss_x = 0.0
        epoch_loss_u = 0.0
        n_batches    = 0

        labeled_iter = iter(labeled_loader)

        for (imgs_u,) in unlabeled_loader:
            try:
                imgs_x, labels_x = next(labeled_iter)
            except StopIteration:
                labeled_iter = iter(labeled_loader)
                imgs_x, labels_x = next(labeled_iter)

            imgs_x   = imgs_x.to(device)
            labels_x = labels_x.to(device)
            imgs_u   = imgs_u.to(device)

            # Encode qua bottom_model (frozen)
            with torch.no_grad():
                emb_x = bottom_model(_split_client_half(imgs_x)).detach()
                emb_u = bottom_model(_split_client_half(imgs_u)).detach()

            # Augment: noise + requires_grad=True de gradient chay qua InferenceHead
            emb_x_aug = (emb_x + torch.randn_like(emb_x) * 0.1).requires_grad_(True)
            emb_u_aug = (emb_u + torch.randn_like(emb_u) * 0.1).requires_grad_(True)

            # Supervised loss
            logits_x = inference_head(emb_x_aug)
            loss_x   = ce_loss(logits_x, labels_x)

            # Consistency loss (sau warmup)
            if epoch > warmup_epochs:
                with torch.no_grad():
                    inference_head.eval()
                    probs_u = F.softmax(inference_head(emb_u), dim=1)
                    pseudo_u = sharpen(probs_u, temperature).detach()
                    inference_head.train()

                probs_u_aug = F.softmax(inference_head(emb_u_aug), dim=1)
                loss_u = mse_loss(probs_u_aug, pseudo_u)
                total_loss = loss_x + lambda_u * loss_u
            else:
                loss_u     = torch.tensor(0.0)
                total_loss = loss_x

            optimizer.zero_grad()
            total_loss.backward()

            # DEBUG: in grad norm de xac nhan gradient co chay khong
            if n_batches == 0 and epoch <= 3:
                grad_norms = [p.grad.norm().item() for p in inference_head.parameters() if p.grad is not None]
                no_grad    = sum(1 for p in inference_head.parameters() if p.grad is None)
                print(f"  [GRAD DEBUG] epoch={epoch} | params_with_grad={len(grad_norms)} | no_grad={no_grad} | max_grad_norm={max(grad_norms) if grad_norms else 0:.6f}")

            nn.utils.clip_grad_norm_(inference_head.parameters(), max_norm=5.0)
            optimizer.step()

            epoch_loss_x += loss_x.item()
            epoch_loss_u += loss_u.item() if isinstance(loss_u, torch.Tensor) else loss_u
            n_batches    += 1

        scheduler.step()

        avg_lx = epoch_loss_x / max(n_batches, 1)
        avg_lu = epoch_loss_u / max(n_batches, 1)

        if epoch % 10 == 0 or epoch <= 5:
            tag = " [WARMUP]" if epoch <= warmup_epochs else ""
            print(f"Epoch {epoch:3d}/{epochs}{tag} -- Loss_X: {avg_lx:.4f}, Loss_U: {avg_lu:.4f}")

    print(f"\n{sep}")
    print("  Training complete.")
    print(f"{sep}\n")
    return inference_head


# ──────────────────────────────────────────────────────────────
#  6. calculate_asr()
# ──────────────────────────────────────────────────────────────

@torch.no_grad()
def calculate_asr(
    bottom_model: nn.Module,
    inference_head: nn.Module,
    U_images: torch.Tensor,
    U_labels_true: torch.Tensor,
    batch_size: int = 256,
    device: str = "cpu",
) -> float:
    """
    Compute Attack Success Rate (ASR) = accuracy của label inference trên tập U.
    """
    bottom_model   = bottom_model.to(device).eval()
    inference_head = inference_head.to(device).eval()

    loader = DataLoader(
        TensorDataset(U_images, U_labels_true),
        batch_size=batch_size,
        shuffle=False,
    )

    correct = 0
    total   = 0

    for (imgs, labels) in loader:
        imgs   = imgs.to(device)
        labels = labels.to(device)

        emb     = bottom_model(_split_client_half(imgs))
        logits  = inference_head(emb)
        preds   = logits.argmax(dim=1)

        correct += (preds == labels).sum().item()
        total   += labels.size(0)

    asr = correct / total * 100.0

    print(f"\n{'='*50}")
    print(f"  🥷 Attack Success Rate: {asr:.2f}%")
    if asr >= 75.0:
        print("  🎉 BẢO ĐÃ THÀNH CÔNG ĂN CẮP DỮ LIỆU!")
    elif asr >= 40.0:
        print("  ⚠️  Tấn công một phần thành công — cần thêm epochs.")
    else:
        print("  ❌ Tấn công chưa thành công — kiểm tra lại BottomModel.")
    print(f"{'='*50}\n")

    return asr