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
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
BATCH_SIZE = 32
LEARNING_RATE = 0.01
NUM_EPOCHS = 15
EMBEDDING_DIM = 128

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

# 🥷 MẶC ĐỊNH: Sử dụng MaliciousSGD thay vì SGD
print("🥷 Using MaliciousSGD (Malicious Optimizer) for Client...\n")
client.optimizer = MaliciousSGD(
    client.model.parameters(), 
    lr=LEARNING_RATE,
    beta=0.9,
    gamma=1.0,
    r_min=1.0,
    r_max=5.0
)

print("✅ Models initialized with MaliciousSGD!\n")

# ============================================
# Training Loop (Phase 2.1: Active Attack)
# ============================================
print("=" * 60)
print("🎯 STARTING MALICIOUS TRAINING (ACTIVE ATTACK)".center(60))
print("=" * 60 + "\n")

train_losses = []
train_accs = []

for epoch in range(NUM_EPOCHS):
    epoch_loss = 0.0
    epoch_correct = 0
    epoch_total = 0
    
    for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
        half_A  = half_A.to(DEVICE)
        half_B  = half_B.to(DEVICE)
        labels  = labels.to(DEVICE)

        # 🥷 Client forward (với tấn công)
        o_client = client.forward(half_B)
        
        # Server forward and loss
        loss, logits = server.forward_and_loss(half_A, o_client, labels)
        
        # Server backward and gradient
        g_client = server.compute_gradients_and_update()
        
        # 🥷 Client backward (MaliciousSGD thay đổi gradient ở đây)
        if g_client is not None:
            client.backward(g_client)
        
        # Statistics
        epoch_loss += loss.item()
        _, predicted = torch.max(logits.data, 1)
        epoch_total += labels.size(0)
        epoch_correct += (predicted == labels.to(DEVICE)).sum().item()
        
        # Print progress
        if (batch_idx + 1) % 500 == 0:
            batch_acc = 100 * epoch_correct / epoch_total
            avg_loss = epoch_loss / (batch_idx + 1)
            print(f"Epoch {epoch+1}/{NUM_EPOCHS} | Batch {batch_idx+1}/{len(train_loader)} | Loss: {avg_loss:.4f} | Acc: {batch_acc:.2f}%")
    
    # End of epoch
    avg_loss = epoch_loss / len(train_loader)
    avg_acc = 100 * epoch_correct / epoch_total
    train_losses.append(avg_loss)
    train_accs.append(avg_acc)
    
    print(f"\n✅ Epoch {epoch+1}/{NUM_EPOCHS} Summary - Loss: {avg_loss:.4f} | Accuracy: {avg_acc:.2f}%\n")

# ============================================
# Phase 2.2: Passive Attack (Label Inference)
# ============================================
print("\n" + "=" * 60)
print("🥷 STARTING PASSIVE ATTACK (LABEL INFERENCE)".center(60))
print("=" * 60 + "\n")

# Chuẩn bị dữ liệu cho tấn công
test_dataset = datasets.CIFAR10(
    root='./data',
    train=False,
    transform=transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465),
                           (0.2023, 0.1994, 0.2010))
    ]),
    download=True
)

print("📊 Generating auxiliary labels (40 labeled samples)...")
X, U = generate_auxiliary_labels(test_dataset, num_labels=40)
print(f"✅ X images shape: {X[0].shape}")   # Kỳ vọng: [40, 3, 32, 32]
print(f"✅ U images shape: {U[0].shape}")   # Kỳ vọng: [9960, 3, 32, 32]
print(f"✅ X (labeled): {len(X[0])} samples")
print(f"✅ U (unlabeled): {len(U[0])} samples\n")

# Tạo InferenceHead
print("🔧 Creating InferenceHead...")
inference_head = InferenceHead(
    embedding_dim=EMBEDDING_DIM,
    hidden_dim=256,
    num_classes=10,
    dropout_rate=0.3
)
print("✅ InferenceHead created!\n")

# Train InferenceHead với MixMatch
print("🎯 Training InferenceHead with MixMatch...\n")
inference_head = train_inference_head(
    bottom_model=client.model,
    inference_head=inference_head,
    X=X,
    U=U,
    epochs=50,
    lr=0.01,
    device=DEVICE
)

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
    device=DEVICE
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
    print("\n🎉 🎉 🎉 BẢO ĐÃ THÀNH CÔNG ĂNCẮP DỮ LIỆU! 🎉 🎉 🎉")
    print("✅ ASR >= 75% - Tấn công thành công!")
    print("\n👉 Báo lại cho tôi để nhận PROMPT GIAI ĐOẠN 3 (Phòng thủ FLSG)!")
else:
    print(f"\n⚠️  ASR = {asr:.2f}% < 75% - Tấn công chưa đủ tốt")
    print("💡 Hãy thử: tăng số epoch, thay đổi lambda_U, hoặc điều chỉnh temperature")
