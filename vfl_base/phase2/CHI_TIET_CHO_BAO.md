# 🥷 CHỈ DẪN THỰC HÀNH CHO BẢO - GIAI ĐOẠN 2

## 📌 Tóm Tắt Nhiệm Vụ

Bảo sẽ thực hiện tấn công VFL để ăn cắp dữ liệu nhạy cảm của Chiến (Server).

**Hai loại tấn công:**
1. **Active Attack**: Sửa Optimizer để ép Server phụ thuộc
2. **Passive Attack**: Dùng MixMatch để đoán nhãn từ 40 mẫu

**Mục tiêu**: Đạt **ASR > 75%** (ăn cắp >75% dữ liệu)

---

## 🎯 Quy Trình 5 Bước

### **Bước 1: Chuẩn Bị Thư Mục**

```bash
cd "/Users/rykan/ĐỒ ÁN/IE105/WEB DEMO/Federated Learning Visualization App"

# Tạo thư mục cho phase 2
mkdir -p vfl_base/phase2/src
cd vfl_base/phase2
```

Cấu trúc sẽ là:
```
vfl_base/phase2/
├── src/
│   ├── malicious_optimizer.py
│   ├── inference_head.py
│   └── main_attack.py
├── GIAI_DOAN_2_HUONG_DAN.md
├── PROMPT_1_MALICIOUS_SGD.md
└── PROMPT_2_INFERENCE_MIXMATCH.md
```

---

### **Bước 2: Tạo File `malicious_optimizer.py`**

**Cách làm:**
1. Mở ChatGPT hoặc Claude
2. Copy toàn bộ nội dung từ file: `vfl_base/phase2/PROMPT_1_MALICIOUS_SGD.md`
3. Paste vào ChatGPT/Claude
4. Yêu cầu AI: *"Hãy generate code hoàn chỉnh cho prompt này"*
5. Copy code AI trả về
6. Tạo file: `vfl_base/phase2/src/malicious_optimizer.py`
7. Paste code vào

**Kiểm tra:**
```bash
cd vfl_base/phase2/src
python -c "from malicious_optimizer import MaliciousSGD; print('✅ MaliciousSGD imported successfully')"
```

---

### **Bước 3: Tạo File `inference_head.py`**

**Cách làm:**
1. Mở ChatGPT hoặc Claude (tab mới)
2. Copy toàn bộ nội dung từ file: `vfl_base/phase2/PROMPT_2_INFERENCE_MIXMATCH.md`
3. Paste vào ChatGPT/Claude
4. Yêu cầu AI: *"Hãy generate code hoàn chỉnh cho prompt này"*
5. Copy code AI trả về
6. Tạo file: `vfl_base/phase2/src/inference_head.py`
7. Paste code vào

**Kiểm tra:**
```bash
python -c "from inference_head import InferenceHead, sharpen, mixup, generate_auxiliary_labels, train_inference_head, calculate_asr; print('✅ All functions imported successfully')"
```

---

### **Bước 4: Tạo File `main_attack.py`**

**Cách làm:**

Copy code dưới đây vào file `vfl_base/phase2/src/main_attack.py`:

```python
"""
Main training loop với Active + Passive attack
Bảo sử dụng MaliciousSGD để tấn công chủ động
Sau đó dùng MixMatch để tấn công thụ động
"""

import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

# Import từ phase1
sys.path.insert(0, '../phase1/src')
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
NUM_EPOCHS = 10
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
    download=False
)

print("📊 Generating auxiliary labels (40 labeled samples)...")
X, U = generate_auxiliary_labels(test_dataset, num_labels=40)
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
print(f"\n⏱️  Total Training Time: {sum(train_losses):.2f}")
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
```

---

### **Bước 5: Chạy Training và Báo Cáo**

**Chạy code:**
```bash
cd vfl_base/phase2/src
python main_attack.py
```

**Output mong đợi:**
```
🚀 Device: cuda
📊 Batch Size: 32
🔄 Learning Rate: 0.01
📈 Epochs: 10

📥 Loading CIFAR-10 dataset...
✅ Dataset loaded! Train: 1563 batches, Test: 313 batches

🔧 Initializing models...
🥷 Using MaliciousSGD (Malicious Optimizer) for Client...
✅ Models initialized with MaliciousSGD!

============================================================
🎯 STARTING MALICIOUS TRAINING (ACTIVE ATTACK)
============================================================

Epoch 1/10 | Batch 500/1563 | Loss: 2.1396 | Acc: 19.41%
...
✅ Epoch 10/10 Summary - Loss: 1.2015 | Accuracy: 56.97%

============================================================
🥷 STARTING PASSIVE ATTACK (LABEL INFERENCE)
============================================================

📊 Generating auxiliary labels (40 labeled samples)...
✅ X (labeled): 40 samples
✅ U (unlabeled): 9960 samples

🔧 Creating InferenceHead...
✅ InferenceHead created!

🎯 Training InferenceHead with MixMatch...

Epoch 1/50 - Loss_X: 0.8234, Loss_U: 0.6123, Total: 1.4357
Epoch 2/50 - Loss_X: 0.7123, Loss_U: 0.5234, Total: 1.2357
...
Epoch 50/50 - Loss_X: 0.1234, Loss_U: 0.0923, Total: 0.2157

============================================================
📊 CALCULATING ATTACK SUCCESS RATE
============================================================

🥷 Attack Success Rate (ASR): 78.50%

============================================================
🎉 ATTACK COMPLETE
============================================================

⏱️  Total Training Time: 145.67
📉 Final VFL Loss: 1.2015
📈 Final VFL Accuracy: 56.97%
🥷 Attack Success Rate (ASR): 78.50%

🎉 🎉 🎉 BẢO ĐÃ THÀNH CÔNG ĂNCẮP DỮ LIỆU! 🎉 🎉 🎉
✅ ASR >= 75% - Tấn công thành công!

👉 Báo lại cho tôi để nhận PROMPT GIAI ĐOẠN 3 (Phòng thủ FLSG)!
```

---

## ✅ Checklist Hoàn Thành

- [ ] Tạo thư mục `vfl_base/phase2/src/`
- [ ] Copy Prompt 1 vào ChatGPT/Claude, generate `malicious_optimizer.py`
- [ ] Copy Prompt 2 vào ChatGPT/Claude, generate `inference_head.py`
- [ ] Tạo `main_attack.py` bằng code trên
- [ ] Chạy `python main_attack.py`
- [ ] Kiểm tra ASR >= 75%
- [ ] **Báo lại kết quả cho tôi!**

---

## 💡 Troubleshooting

### Import Error: Cannot find phase1 modules
```bash
# Chắc chắn rằng bạn đang ở trong vfl_base/phase2/src
# Và main.py có dòng:
sys.path.insert(0, '../phase1/src')
```

### CUDA Out of Memory
```python
# Giảm BATCH_SIZE trong main_attack.py
BATCH_SIZE = 16  # thay từ 32
```

### ASR quá thấp (<50%)
```python
# Tăng số epoch trong train_inference_head
epochs=100  # thay từ 50

# Hoặc tăng lambda_U (nếu code cho phép)
lambda_U = 2.0  # thay từ 1.0
```

---

## 🎉 Khi Nào Báo Lại?

Khi chạy xong `main_attack.py` và thấy dòng:
```
🥷 Attack Success Rate (ASR): XX.XX%
```

Nếu **ASR >= 75%** → Báo lại ngay cho tôi nhé! 🚀

Tôi sẽ ném tiếp **PROMPT GIAI ĐOẠN 3** để Chiến viết **Thuật toán phòng thủ FLSG** 🛡️

---

**Chúc Bảo thành công!** 🥷💻
