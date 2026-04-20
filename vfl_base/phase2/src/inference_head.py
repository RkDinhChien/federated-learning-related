# ============================================================
# Passive Label Inference Attack using MixMatch for VFL
# FOR RESEARCH / SECURITY AUDIT PURPOSES ONLY
# ============================================================

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Beta
from torch.utils.data import DataLoader, Subset, TensorDataset
import numpy as np
from typing import Tuple, Optional
from PIL import Image

# ──────────────────────────────────────────────────────────────
#  0. VFL Image Split Helper
# ──────────────────────────────────────────────────────────────

def _split_client_half(images: torch.Tensor, side: str = "right") -> torch.Tensor:
    """
    Split full CIFAR-10 image (3×32×32) → client's half (3×32×16).
    
    VFL convention (phải khớp với dataset.py của phase1):
        'right' → images[:, :, :, 16:]   ← mặc định cho Client (Bảo)
        'left'  → images[:, :, :, :16]   ← Server (Chiến)
    
    Args:
        images (Tensor): Full images, shape [B, 3, 32, 32].
        side   (str)   : 'right' hoặc 'left'. Mặc định 'right'.
    
    Returns:
        Tensor: Half images, shape [B, 3, 32, 16].
    """
    if images.dim() == 3:          # single image: [3, 32, 32]
        images = images.unsqueeze(0)
    
    if side == "right":
        return images[:, :, :, 16:]   # [B, 3, 32, 16] — Client half
    elif side == "left":
        return images[:, :, :, :16]   # [B, 3, 32, 16] — Server half
    else:
        raise ValueError(f"side must be 'right' or 'left', got '{side}'")

def _validate_and_convert_image(img, expected_shape=(3, 32, 32)):
    """
    Strictly validate and convert images to torch.Tensor (CHW format).
    
    Args:
        img: Input image (torch.Tensor, PIL.Image, or np.ndarray)
        expected_shape: Expected output shape (C, H, W), default (3, 32, 32)
    
    Returns:
        torch.Tensor in shape (C, H, W) with values in [0, 1]
    
    Raises:
        TypeError: If image format is not supported
        ValueError: If shape validation fails
    """
    # Case 1: Already a tensor — validate and return
    if isinstance(img, torch.Tensor):
        if img.ndim != 3:
            raise ValueError(
                f"Expected tensor shape (C, H, W), got {img.shape}. "
                f"Dataset must return tensors in CHW format."
            )
        # Ensure values are in [0, 1]
        if img.max() > 1.0:
            img = img.float() / 255.0
        if img.shape != expected_shape:
            raise ValueError(
                f"Shape mismatch: expected {expected_shape}, got {img.shape}"
            )
        return img
    
    # Case 2: PIL Image — convert properly with HWC → CHW
    elif isinstance(img, Image.Image):
        # Convert to numpy first (HWC format)
        img_array = np.array(img, dtype=np.float32)
        
        # Handle grayscale (H, W) → (H, W, 3)
        if img_array.ndim == 2:
            img_array = np.stack([img_array] * 3, axis=-1)
        
        # Scale [0, 255] → [0, 1]
        if img_array.max() > 1.0:
            img_array = img_array / 255.0
        
        # Convert HWC → CHW
        img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).float()
        
        if img_tensor.shape != expected_shape:
            raise ValueError(
                f"Shape mismatch: expected {expected_shape}, got {img_tensor.shape}. "
                f"Dataset preprocessing is inconsistent."
            )
        return img_tensor
    
    # Case 3: NumPy array — similar to PIL
    elif isinstance(img, np.ndarray):
        img_array = img.astype(np.float32)
        
        # Determine if HWC or CHW
        if img_array.ndim == 3:
            if img_array.shape[0] in [1, 3, 4]:  # Likely CHW (channels first)
                img_tensor = torch.from_numpy(img_array).float()
            else:  # Likely HWC (channels last)
                # Scale [0, 255] → [0, 1]
                if img_array.max() > 1.0:
                    img_array = img_array / 255.0
                # Convert HWC → CHW
                img_tensor = torch.from_numpy(img_array).permute(2, 0, 1).float()
        elif img_array.ndim == 2:  # Grayscale (H, W)
            # Scale [0, 255] → [0, 1]
            if img_array.max() > 1.0:
                img_array = img_array / 255.0
            # Add channel dimension → (1, H, W)
            img_tensor = torch.from_numpy(img_array).unsqueeze(0).float()
        else:
            raise ValueError(f"Unexpected image shape: {img_array.shape}")
        
        if img_tensor.shape != expected_shape:
            raise ValueError(
                f"Shape mismatch: expected {expected_shape}, got {img_tensor.shape}"
            )
        return img_tensor
    
    else:
        raise TypeError(
            f"Unsupported image format: {type(img).__name__}. "
            f"Dataset must return torch.Tensor, PIL.Image, or np.ndarray"
        )

# ──────────────────────────────────────────────────────────────
#  1. InferenceHead
# ──────────────────────────────────────────────────────────────

class InferenceHead(nn.Module):
    """
    A small MLP head appended after a frozen BottomModel.

    Architecture (default):
        Linear(128 → 256) → ReLU → Dropout(0.3)
        Linear(256 → 128) → ReLU → Dropout(0.3)
        Linear(128 → 10)

    The BottomModel's weights are frozen externally before training;
    this head is the ONLY component that gets updated.

    Args:
        embedding_dim (int): Dimension of embeddings from BottomModel (default 128).
        hidden_dim    (int): Width of the two hidden layers (default 256).
        num_classes   (int): Number of target classes (default 10 for CIFAR-10).
        dropout_rate  (float): Dropout probability (default 0.3).
    """

    def __init__(
        self,
        embedding_dim: int = 128,
        hidden_dim: int = 256,
        num_classes: int = 10,
        dropout_rate: float = 0.3,
    ):
        super(InferenceHead, self).__init__()

        # Layer 1: embedding_dim → hidden_dim
        # Lớp 1: chiếu embedding lên không gian lớn hơn
        self.layer1 = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
        )

        # Layer 2: hidden_dim → embedding_dim
        # Lớp 2: nén lại về kích thước ban đầu
        self.layer2 = nn.Sequential(
            nn.Linear(hidden_dim, embedding_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout_rate),
        )

        # Output layer: embedding_dim → num_classes
        # Lớp đầu ra: dự đoán nhãn
        self.output_layer = nn.Linear(embedding_dim, num_classes)

        # Weight initialisation — He for ReLU layers
        self._init_weights()

    def _init_weights(self):
        """Initialise weights with He (Kaiming) uniform for ReLU networks."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_uniform_(m.weight, nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, embedding: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the InferenceHead.

        Args:
            embedding: Tensor of shape [B, embedding_dim] from BottomModel.

        Returns:
            logits: Tensor of shape [B, num_classes].
        """
        x = self.layer1(embedding)       # [B, hidden_dim]
        x = self.layer2(x)               # [B, embedding_dim]
        logits = self.output_layer(x)    # [B, num_classes]
        return logits


# ──────────────────────────────────────────────────────────────
#  2. sharpen()
# ──────────────────────────────────────────────────────────────

def sharpen(predictions: torch.Tensor, temperature: float = 0.5) -> torch.Tensor:
    """
    Sharpen a probability distribution by reducing its temperature.

    Formula:
        p_sharp_k = p_k^(1/T) / Σ_j p_j^(1/T)

    A temperature T < 1 pushes the distribution toward a one-hot,
    providing high-confidence pseudo-labels for unlabeled data.

    Args:
        predictions (Tensor): Probabilities, shape [B, C]. Values in (0, 1].
        temperature (float) : Sharpening temperature T. Default 0.5.

    Returns:
        Tensor: Sharpened probabilities, shape [B, C].

    Example:
        >>> p = torch.tensor([[0.3, 0.3, 0.2, 0.2]])
        >>> sharpen(p, temperature=0.5)
        # → approximately [[0.50, 0.50, 0.00, 0.00]]
    """
    if temperature <= 0:
        raise ValueError(f"temperature must be > 0, got {temperature}")

    # Raise each probability to the power 1/T
    # Nâng xác suất lên lũy thừa 1/T để làm sắc nét phân phối
    sharpened = predictions.pow(1.0 / temperature)

    # Re-normalise across the class dimension so the output sums to 1
    # Chuẩn hóa lại để tổng xác suất bằng 1
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
    alpha: float = 0.2,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    MixUp augmentation: interpolate between two (sample, label) pairs.

    λ ~ Beta(alpha, alpha)
    x_mixed = λ * x1 + (1 − λ) * x2
    y_mixed = λ * y1 + (1 − λ) * y2

    Args:
        x1, x2 (Tensor): Input samples.  Must have the same shape.
        y1, y2 (Tensor): Labels / pseudo-labels. Must have the same shape.
        alpha  (float) : Beta distribution parameter. Default 0.2.

    Returns:
        (x_mixed, y_mixed): Interpolated tensors with the same shapes as inputs.
    """
    if alpha <= 0:
        raise ValueError(f"alpha must be > 0, got {alpha}")

    # Sample mixing coefficient from Beta(alpha, alpha)
    # Lấy hệ số trộn từ phân phối Beta — giá trị gần 0.5 là phổ biến nhất
    dist = Beta(
        torch.tensor(alpha, dtype=torch.float32),
        torch.tensor(alpha, dtype=torch.float32),
    )
    lam = dist.sample().item()

    # Ensure λ >= 0.5 so that (x1, y1) is the "dominant" pair
    # Đảm bảo sample gốc luôn chiếm ưu thế
    lam = max(lam, 1.0 - lam)

    x_mixed = lam * x1 + (1.0 - lam) * x2
    y_mixed = lam * y1 + (1.0 - lam) * y2

    return x_mixed, y_mixed


# ──────────────────────────────────────────────────────────────
#  4. generate_auxiliary_labels()
# ──────────────────────────────────────────────────────────────

def generate_auxiliary_labels(
    dataset,
    num_labels: int = 40,
    seed: int = 42,
) -> Tuple[Tuple[torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor]]:
    """
    Split a dataset into a tiny labeled set X and a large unlabeled set U.

    Simulates the attacker having bribed an insider for `num_labels` ground-truth
    labels while the rest of the dataset remains "unseen" by the attacker.

    Args:
        dataset    : A PyTorch Dataset (e.g., CIFAR-10). Each item is (image, label).
        num_labels : Number of labeled seed samples to keep in X. Default 40.
        seed       : Random seed for reproducibility.

    Returns:
        X = (images_X, labels_X) — labeled tensor pair, shape [num_labels, ...]
        U = (images_U, labels_U_true) — unlabeled tensor pair, shape [N-num_labels, ...]
            (labels_U_true is kept secret; used only to compute ASR later)
    """
    np.random.seed(seed)
    torch.manual_seed(seed)

    n_total = len(dataset)
    if num_labels >= n_total:
        raise ValueError(
            f"num_labels ({num_labels}) must be less than dataset size ({n_total})"
        )

    # Random permutation of all indices
    # Xáo trộn toàn bộ chỉ số ngẫu nhiên
    all_indices = np.random.permutation(n_total)
    labeled_indices   = all_indices[:num_labels]
    unlabeled_indices = all_indices[num_labels:]

    def _collect(indices):
    """Stack individual (image, label) samples into batched tensors."""
    imgs, labels = [], []
    for idx in indices:
        img, lbl = dataset[int(idx)]
        img = _validate_and_convert_image(img, expected_shape=(3, 32, 32))  # ✅ FIXED
        imgs.append(img)
        labels.append(int(lbl))
    return torch.stack(imgs), torch.tensor(labels, dtype=torch.long)

    print(f"[generate_auxiliary_labels] Collecting {num_labels} labeled samples …")
    images_X, labels_X = _collect(labeled_indices)

    print(f"[generate_auxiliary_labels] Collecting {len(unlabeled_indices)} unlabeled samples …")
    images_U, labels_U_true = _collect(unlabeled_indices)

    print(
        f"[generate_auxiliary_labels] Done. "
        f"X: {images_X.shape}, U: {images_U.shape}"
    )
    return (images_X, labels_X), (images_U, labels_U_true)


# ──────────────────────────────────────────────────────────────
#  5. train_inference_head()
# ──────────────────────────────────────────────────────────────

def train_inference_head(
    bottom_model: nn.Module,
    inference_head: nn.Module,
    X: Tuple[torch.Tensor, torch.Tensor],
    U: Tuple[torch.Tensor, torch.Tensor],
    epochs: int = 100,
    lr: float = 0.01,
    batch_size: int = 64,
    lambda_u: float = 1.5,
    temperature: float = 0.25,
    device: str = "cuda",
) -> nn.Module:
    """
    Train InferenceHead using a MixMatch-style semi-supervised loop.

    The BottomModel is FROZEN throughout — only InferenceHead weights are updated.

    Algorithm per epoch:
        For each mini-batch sampled from X and U:
          1. Encode X and U through frozen BottomModel → embeddings
          2. Pass embeddings through InferenceHead → logits
          3. Loss_X  = CrossEntropyLoss(logits_X,  labels_X)     [supervised]
          4. pseudo  = sharpen(softmax(logits_U), T)             [pseudo-labels]
          5. Loss_U  = MSELoss(softmax(logits_U), pseudo)        [consistency]
          6. total   = Loss_X + lambda_u * Loss_U
          7. Backprop and update InferenceHead

    Args:
        bottom_model    : Pre-trained BottomModel (e.g., ResNet-18). Will be frozen.
        inference_head  : Untrained InferenceHead to optimise.
        X               : (images_X, labels_X) — 40 labeled samples.
        U               : (images_U, labels_U_true) — ~9960 unlabeled samples.
        epochs          : Training epochs (default 50).
        lr              : Learning rate (default 0.01).
        batch_size      : Mini-batch size (default 64).
        lambda_u        : Weight for the unsupervised consistency loss (default 1.0).
        temperature     : Sharpening temperature for pseudo-labels (default 0.5).
        device          : 'cuda' or 'cpu'.

    Returns:
        inference_head: Trained InferenceHead module.
    """
    # ── Setup ──────────────────────────────────────────────────
    bottom_model   = bottom_model.to(device)
    inference_head = inference_head.to(device)

    # Freeze BottomModel: no gradients computed for its parameters
    # Đóng băng BottomModel: không tính gradient cho bất kỳ tham số nào của nó
    for param in bottom_model.parameters():
        param.requires_grad_(False)
    bottom_model.eval()

    # Only InferenceHead parameters will be updated
    # Chỉ cập nhật tham số của InferenceHead
    optimizer = optim.Adam(inference_head.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    ce_loss  = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()

    images_X, labels_X = X
    images_U, _        = U   # ground-truth labels of U are never used here

    # Build DataLoaders
    # Tạo DataLoader cho tập có nhãn và không nhãn
    labeled_loader = DataLoader(
        TensorDataset(images_X, labels_X),
        batch_size=min(batch_size, len(images_X)),
        shuffle=True,
        drop_last=False,
    )
    unlabeled_loader = DataLoader(
        TensorDataset(images_U),
        batch_size=batch_size,
        shuffle=True,
        drop_last=True,
    )

    print(f"\n{'─'*60}")
    print(f"  MixMatch Training — {epochs} epochs")
    print(f"  Labeled   : {len(images_X)} samples")
    print(f"  Unlabeled : {len(images_U)} samples")
    print(f"  Device    : {device}")
    print(f"{'─'*60}\n")

    for epoch in range(1, epochs + 1):
        inference_head.train()

        epoch_loss_x = 0.0
        epoch_loss_u = 0.0
        n_batches    = 0

        # Cycle through labeled batches; zip with unlabeled
        # Duyệt qua từng mini-batch, ghép tập có nhãn và không nhãn
        unlabeled_iter = iter(unlabeled_loader)

        for (batch_x, batch_labels) in labeled_loader:

            # ── Fetch unlabeled batch (cycle if exhausted) ──────
            try:
                (batch_u,) = next(unlabeled_iter)
            except StopIteration:
                unlabeled_iter = iter(unlabeled_loader)
                (batch_u,)    = next(unlabeled_iter)

            batch_x      = batch_x.to(device)
            batch_labels = batch_labels.to(device)
            batch_u      = batch_u.to(device)

            # ── Step 1-2: Encode through frozen BottomModel ─────
            # Bước 1-2: Mã hóa qua BottomModel đã đóng băng
            with torch.no_grad():
                # Crop full image (3×32×32) → client half (3×32×16) trước khi encode
                emb_x = bottom_model(_split_client_half(batch_x))   # [B_x, emb_dim]
                emb_u = bottom_model(_split_client_half(batch_u))   # [B_u, emb_dim]

            # ── Step 3: Supervised loss on X ────────────────────
            # Bước 3: Tính loss có giám sát trên tập X
            logits_x = inference_head(emb_x)            # [B_x, C]
            loss_x   = ce_loss(logits_x, batch_labels)

            # ── Step 4-5: Pseudo-labels and consistency loss ─────
            # Bước 4-5: Sinh pseudo-label và tính loss nhất quán
            logits_u   = inference_head(emb_u)              # [B_u, C]
            probs_u    = F.softmax(logits_u, dim=1)         # probability dist
            pseudo_u   = sharpen(probs_u, temperature)      # sharpened pseudo-labels
            pseudo_u   = pseudo_u.detach()                  # stop grad through pseudo

            loss_u = mse_loss(probs_u, pseudo_u)

            # ── Step 6: Total loss ───────────────────────────────
            # Bước 6: Tổng loss
            total_loss = loss_x + lambda_u * loss_u

            # ── Step 7: Backward + update ────────────────────────
            # Bước 7: Lan truyền ngược và cập nhật InferenceHead
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()

            epoch_loss_x += loss_x.item()
            epoch_loss_u += loss_u.item()
            n_batches    += 1

        scheduler.step()

        avg_lx = epoch_loss_x / max(n_batches, 1)
        avg_lu = epoch_loss_u / max(n_batches, 1)
        avg_lt = avg_lx + lambda_u * avg_lu

        print(
            f"Epoch {epoch:3d}/{epochs} — "
            f"Loss_X: {avg_lx:.4f}, "
            f"Loss_U: {avg_lu:.4f}, "
            f"Total: {avg_lt:.4f}"
        )

    print(f"\n{'─'*60}")
    print("  Training complete.")
    print(f"{'─'*60}\n")

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
    Compute Attack Success Rate (ASR) on the unlabeled set U.

    ASR = (# correctly inferred labels / |U|) × 100 %

    Both models are set to eval mode and no gradients are computed.

    Args:
        bottom_model   : Frozen, pre-trained BottomModel.
        inference_head : Trained InferenceHead.
        U_images       : Image tensor for unlabeled set, shape [N, C, H, W].
        U_labels_true  : Ground-truth label tensor, shape [N].
        batch_size     : Inference batch size (default 256).
        device         : 'cuda' or 'cpu'.

    Returns:
        asr (float): Attack Success Rate as a percentage.
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

        # Forward: BottomModel → InferenceHead → predictions
        # Truyền xuôi qua toàn bộ chuỗi để lấy dự đoán
        # Crop full image → client half trước khi đưa vào BottomModel
        emb     = bottom_model(_split_client_half(imgs))
        logits  = inference_head(emb)
        preds   = logits.argmax(dim=1)

        correct += (preds == labels).sum().item()
        total   += labels.size(0)

    asr = correct / total * 100.0

    print(f"\n{'='*50}")
    print(f"  🥷 Attack Success Rate: {asr:.2f}%")
    if asr >= 70.0:
        print("  🎉 BẢO ĐÃ THÀNH CÔNG ĂN CẮP DỮ LIỆU!")
    elif asr >= 40.0:
        print("  ⚠️  Tấn công một phần thành công — cần thêm epochs.")
    else:
        print("  ❌ Tấn công chưa thành công — kiểm tra lại BottomModel.")
    print(f"{'='*50}\n")

    return asr
