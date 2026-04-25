"""
Main training loop với Active + Passive attack
Bảo sử dụng MaliciousSGD để tấn công chủ động
Sau đó dùng MixMatch để tấn công thụ động
"""

import sys
import torch
from torchvision import datasets, transforms
from pathlib import Path

# Import từ phase1
p = Path(__file__).resolve().parents[2] / "phase1" / "src"
if str(p) not in sys.path:
    sys.path.insert(0, str(p))
from dataset import VFLCIFARDataset, get_dataloaders
from client_bao import BottomModel, ClientWorker
from server_chien import ServerCoordinator

# Import từ phase2
from malicious_optimizer import MaliciousSGD
from inference_head import (
    InferenceHead,
    generate_auxiliary_labels,
    train_inference_head,
    calculate_asr
)

# ============================================
# Configuration
# ============================================
DEVICE        = 'cuda' if torch.cuda.is_available() else 'cpu'
BATCH_SIZE    = 32
LEARNING_RATE = 0.01
NUM_EPOCHS    = 15
EMBEDDING_DIM = 128

# ── Debug mode: giam so luong de chay nhanh ──────────────
DEBUG_MODE        = False   # <── doi thanh False khi chay that
if DEBUG_MODE:
    NUM_EPOCHS        = 5      # du de embedding hoi tu co ban
    INFERENCE_EPOCHS  = 30     # du de thay xu huong
    INFERENCE_WARMUP  = 5
    NUM_LABELS        = 200
    MAX_TRAIN_BATCHES = None   # chay het batch, chi giam epochs
    print("⚡ DEBUG MODE ON (5 VFL epochs, 30 inference epochs)")
else:
    NUM_EPOCHS        = 20
    INFERENCE_EPOCHS  = 300
    INFERENCE_WARMUP  = 20
    NUM_LABELS        = 200
    MAX_TRAIN_BATCHES = None

print(f"🚀 Device: {DEVICE}")
print(f"📊 Batch Size: {BATCH_SIZE}")
print(f"🔄 Learning Rate: {LEARNING_RATE}")
print(f"📈 Epochs: {NUM_EPOCHS}\n")

# ============================================
# Load Dataset
# ============================================
print("📥 Loading CIFAR-10 dataset...")
train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE, num_workers=0)
print(f"✅ Dataset loaded! Train: {len(train_loader)} batches, Test: {len(test_loader)} batches\n")

# ============================================
# Initialize Models
# ============================================
print("🔧 Initializing models...")
client = ClientWorker(embedding_dim=EMBEDDING_DIM, learning_rate=LEARNING_RATE, device=DEVICE)
server = ServerCoordinator(embedding_dim=EMBEDDING_DIM, learning_rate=LEARNING_RATE, device=DEVICE)

# DEBUG: tat MaliciousSGD de kiem tra embedding co thong tin khong
# Neu KNN/linear probe tang len -> MaliciousSGD dang pha embedding
USE_MALICIOUS = True

if USE_MALICIOUS:
    print("🥷 Using MaliciousSGD...\n")
    client.optimizer = MaliciousSGD(
        client.model.parameters(),
        lr=0.001, beta=0.9, gamma=1.0, r_min=1.0, r_max=3.0,
    )
else:
    print("🔧 Using normal SGD (baseline test)...\n")
    import torch.optim as _optim
    client.optimizer = _optim.SGD(
        client.model.parameters(),
        lr=LEARNING_RATE, momentum=0.9, weight_decay=5e-4
    )

print("✅ Models initialized with MaliciousSGD!\n")

# ============================================
# Training Loop (Phase 2.1: Active Attack)
# ============================================
print("=" * 60)
print("🎯 STARTING MALICIOUS TRAINING (ACTIVE ATTACK)".center(60))
print("=" * 60 + "\n")

train_losses = []
train_accs   = []

for epoch in range(NUM_EPOCHS):
    epoch_loss    = 0.0
    epoch_correct = 0
    epoch_total   = 0

    for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
        if MAX_TRAIN_BATCHES and batch_idx >= MAX_TRAIN_BATCHES:
            break
        half_A = half_A.to(DEVICE)
        half_B = half_B.to(DEVICE)
        labels = labels.to(DEVICE)

        # Client forward + server forward/backward
        o_client = client.forward(half_B)
        loss, logits = server.forward_and_loss(half_A, o_client, labels)
        g_client = server.compute_gradients_and_update()

        if g_client is not None:
            client.backward(g_client)

        # Statistics
        epoch_loss += loss.item()
        _, predicted = torch.max(logits.data, 1)
        epoch_total   += labels.size(0)
        epoch_correct += (predicted == labels.to(DEVICE)).sum().item()

        if (batch_idx + 1) % 500 == 0:
            batch_acc = 100 * epoch_correct / epoch_total
            avg_loss  = epoch_loss / (batch_idx + 1)
            print(f"Epoch {epoch+1}/{NUM_EPOCHS} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {avg_loss:.4f} | Acc: {batch_acc:.2f}%")

    avg_loss = epoch_loss / len(train_loader)
    avg_acc  = 100 * epoch_correct / epoch_total
    train_losses.append(avg_loss)
    train_accs.append(avg_acc)

    print(f"\n✅ Epoch {epoch+1}/{NUM_EPOCHS} Summary - Loss: {avg_loss:.4f} | Accuracy: {avg_acc:.2f}%\n")

# ============================================
# Phase 2.2: Passive Attack (Label Inference)
# ============================================
print("\n" + "=" * 60)
print("🥷 STARTING PASSIVE ATTACK (LABEL INFERENCE)".center(60))
print("=" * 60 + "\n")

# FIX: Dùng cùng transform với phase1 để consistent
# Dung VFLCIFARDataset de lay half_B co cung transform va split voi train_loader
from torchvision import datasets as _tvds
_cifar_test = _tvds.CIFAR10(
    root='./data', train=False, download=True,
    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])
)
vfl_test_dataset = VFLCIFARDataset(_cifar_test)

# Tao dataset chi chua (half_B, label) cho generate_auxiliary_labels
class HalfBDataset(torch.utils.data.Dataset):
    def __init__(self, vfl_ds):
        self.ds = vfl_ds
    def __len__(self):
        return len(self.ds)
    def __getitem__(self, idx):
        half_A, half_B, label = self.ds[idx]
        return half_B, label  # tra ve half_B (3,32,16) thay vi full image

half_b_dataset = HalfBDataset(vfl_test_dataset)

print("📊 Generating auxiliary labels (200 labeled samples, balanced)...")
X, U = generate_auxiliary_labels(half_b_dataset, num_labels=NUM_LABELS, balanced=True)
print(f"  X image shape: {X[0].shape}  (should be (200, 3, 32, 16))")
print(f"  U image shape: {U[0].shape}")
print(f"✅ X images shape: {X[0].shape}")
print(f"✅ U images shape: {U[0].shape}")
print(f"✅ X (labeled): {len(X[0])} samples")
print(f"✅ U (unlabeled): {len(U[0])} samples\n")

# InferenceHead với hidden_dim lớn hơn


print("🔧 Creating InferenceHead...")
inference_head = InferenceHead(
    embedding_dim=EMBEDDING_DIM,
    hidden_dim=512,        # FIX: tăng từ 256 → 512
    num_classes=10,
    dropout_rate=0.3
)
print("✅ InferenceHead created!\n")

# Train InferenceHead với MixMatch improved


print("🎯 Training InferenceHead with MixMatch (improved)...\n")
inference_head = train_inference_head(
    bottom_model=client.model,
    inference_head=inference_head,
    X=X,
    U=U,
    epochs=INFERENCE_EPOCHS,
    lr=1e-3,
    batch_size=64,
    lambda_u=1.0,
    temperature=0.5,
    warmup_epochs=INFERENCE_WARMUP,
    device=DEVICE,
)

# ============================================
# Sanity check: supervised-only accuracy tren X
# Neu < 50% → embedding khong co thong tin, MaliciousSGD qua yeu
# ============================================
print("\n[EMBEDDING QUALITY CHECK]")
client.model.eval()
_X_imgs, _X_lbl = X

# 1. KNN (k=1) - khong can training, khong co gradient issue
with torch.no_grad():
    # X and U are now half_B (3,32,16) -> pass directly to client.model
    _emb_X_all = client.model(_X_imgs.to(DEVICE))
    _emb_U500  = client.model(U[0][:500].to(DEVICE))

# Normalize embeddings
_emb_X_n = torch.nn.functional.normalize(_emb_X_all, dim=1)
_emb_U_n = torch.nn.functional.normalize(_emb_U500,  dim=1)

# KNN: tim nearest neighbor trong X cho moi sample trong U
_dists  = _emb_U_n @ _emb_X_n.T  # [500, 200] cosine similarity
_knn1   = _dists.argmax(dim=1)    # nearest neighbor index
_knn_pred = _X_lbl.to(DEVICE)[_knn1]
_knn_acc  = (_knn_pred == U[1][:500].to(DEVICE)).float().mean().item() * 100
print(f"  KNN-1 acc on U[:500]: {_knn_acc:.1f}%  (random=10%, good=40%+)")

# 2. Linear probe nhanh voi lr cao de tranh plateau
_lp = torch.nn.Linear(EMBEDDING_DIM, 10).to(DEVICE)
_lo = torch.optim.SGD(_lp.parameters(), lr=0.1, momentum=0.9)
_emb_X_det = _emb_X_all.detach()
for _ep in range(200):
    _loss = torch.nn.CrossEntropyLoss()(_lp(_emb_X_det), _X_lbl.to(DEVICE))
    _lo.zero_grad(); _loss.backward(); _lo.step()
with torch.no_grad():
    _lp_tr  = (_lp(_emb_X_det).argmax(1) == _X_lbl.to(DEVICE)).float().mean().item()*100
    _lp_u   = (_lp(_emb_U500.detach()).argmax(1) == U[1][:500].to(DEVICE)).float().mean().item()*100
print(f"  Linear probe train acc: {_lp_tr:.1f}%")
print(f"  Linear probe U[:500]  : {_lp_u:.1f}%  <- proxy ASR voi linear head")

if _knn_acc >= 30 or _lp_u >= 30:
    print("  -> Embedding CO thong tin, van de o InferenceHead training")
else:
    print("  -> Embedding KHONG co thong tin du - VFL chua hoi tu du")

# ============================================
# Calculate Attack Success Rate
# ============================================
print("\n" + "=" * 60)
print("📊 CALCULATING ATTACK SUCCESS RATE".center(60))
print("=" * 60 + "\n")

asr = calculate_asr(
    bottom_model=client.model,
    inference_head=inference_head,
    U_images=U[0],
    U_labels_true=U[1],
    device=DEVICE,
)

# ============================================
# Final Report
# ============================================
print("\n" + "=" * 60)
print("🎉 ATTACK COMPLETE".center(60))
print("=" * 60)
print(f"\n📊 Cumulative VFL Loss: {sum(train_losses):.2f}")
print(f"📉 Final VFL Loss: {train_losses[-1]:.4f}")
print(f"📈 Final VFL Accuracy: {train_accs[-1]:.2f}%")
print(f"🥷 Attack Success Rate (ASR): {asr:.2f}%")

if asr >= 75.0:
    print("\n🎉 🎉 🎉 BẢO ĐÃ THÀNH CÔNG ĂN CẮP DỮ LIỆU! 🎉 🎉 🎉")
    print("✅ ASR >= 75% - Tấn công thành công!")
    print("\n👉 Báo lại để nhận PROMPT GIAI ĐOẠN 3 (Phòng thủ FLSG)!")
else:
    print(f"\n⚠️  ASR = {asr:.2f}% < 75% - Tấn công chưa đủ tốt")
    print("💡 Thử: tăng NUM_EPOCHS lên 20, hoặc tăng num_labels lên 400")