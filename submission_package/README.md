# Vertical Federated Learning (VFL) - Base Implementation

## 📋 Project Overview

This is **GIAI ĐOẠN 1: XÂY DỰNG NỀN TẢNG (BASE VFL)** - a foundational implementation of Vertical Federated Learning using Split Learning.

## 🌐 Demo Access

**Production demo URL:** `https://<your-deployed-demo-link>`

Deploy the Next.js app to Vercel or another public host, then replace the placeholder with the real URL. Anyone can open the link directly in a browser.

**Objective**: Build a working VFL system where:
- **Loss decreases** as epochs progress
- **Accuracy increases** from baseline to higher values
- No attacks, no defenses (just the pure base system)

## 🏗️ Architecture

### Key Concepts
- **Vertical Partitioning**: CIFAR-10 images are split vertically into:
  - **Half A** (3 × 32 × 16): Server's portion
  - **Half B** (3 × 32 × 16): Client's portion (Passive Participant)

- **Split Learning**: The model is split between Client and Server:
  - **Client (Bảo)**: Bottom Model - processes Half B, generates embeddings (no labels)
  - **Server (Chiến)**: 
    - Bottom Model - processes Half A, generates embeddings
    - Top Model - FCNN-4 that receives concatenated embeddings, computes loss

### Training Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Each Training Step:                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Client Forward:                                          │
│    half_B → BottomModel_Client → o_client (embedding)     │
│                                                             │
│ 2. Server Forward:                                          │
│    half_A → BottomModel_Server → o_server (embedding)     │
│    [o_server || o_client] → TopModel → logits             │
│    CrossEntropyLoss(logits, labels) → loss                │
│                                                             │
│ 3. Server Backward:                                         │
│    loss.backward() → g_client (gradient for client)        │
│    Update Server's weights                                 │
│                                                             │
│ 4. Client Backward:                                         │
│    Receive g_client from Server                            │
│    Backprop through Client's BottomModel                   │
│    Update Client's weights                                 │
└─────────────────────────────────────────────────────────────┘
```

## 📂 File Structure

```
vfl_base/
├── dataset.py           # VFL CIFAR-10 dataset with vertical partitioning
├── client_bao.py        # Client (Passive Participant) - Bottom Model
├── server_chien.py      # Server (Active Participant) - Bottom + Top Models
├── main.py              # Training loop with Split Learning
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd vfl_base
pip install -r requirements.txt
```

### Step 2: Run Training

```bash
python main.py
```

### Expected Output

You should see something like:

```
======================================================================
VERTICAL FEDERATED LEARNING (VFL) - BASE IMPLEMENTATION
======================================================================
Device: cuda (or cpu)
Batch Size: 32
Learning Rate: 0.01
Number of Epochs: 10
Embedding Dimension: 128
======================================================================

[Main] Loading datasets...
[Dataset] Loading CIFAR-10 train set...
[Dataset] Loading CIFAR-10 test set...
[Dataset] Train samples: 50000, Test samples: 10000
[Dataset] Each image split: Server gets (3, 32, 16), Client gets (3, 32, 16)
[Main] Train batches: 1563, Test batches: 313

[Main] Initializing Client (Bảo)...
[ClientWorker] Initialized on cuda
[ClientWorker] Embedding dimension: 128
[Main] Initializing Server (Chiến)...
[ServerCoordinator] Initialized on cuda
[ServerCoordinator] Embedding dimension: 128

[Main] Client parameters: 11,173,760
[Main] Server parameters: 16,810

======================================================================
STARTING TRAINING
======================================================================

======================================================================
Epoch 1/10
======================================================================

[Epoch 1] Train Loss: 2.1234, Train Accuracy: 0.4521

[Epoch 1] Test Loss: 1.8945, Test Accuracy: 0.5234

...

[Epoch 10] Train Loss: 0.8234, Train Accuracy: 0.7812

[Epoch 10] Test Loss: 0.9123, Test Accuracy: 0.7651

======================================================================
TRAINING SUMMARY
======================================================================
Final Train Loss: 0.8234
Final Train Accuracy: 0.7812
Final Test Loss: 0.9123
Final Test Accuracy: 0.7651
Loss Reduction: 1.3000
Accuracy Improvement: 0.3291
======================================================================

✅ VFL Base System Training Complete!
   - Loss decreased from 2.1234 to 0.8234
   - Accuracy increased from 0.4521 to 0.7812

🎉 GIAI ĐOẠN 1 HOÀN THÀNH!
   Hãy báo cho tui để nhận PROMPT GIAI ĐOẠN 2 (Malicious Optimizer)!
```

## 📊 Key Metrics to Monitor

- **Train Loss**: Should decrease from ~2.3 (random) towards ~0.5-0.8
- **Train Accuracy**: Should increase from ~10% (random) towards ~75%+
- **Test Loss**: Should show similar trend (validate model doesn't overfit)
- **Test Accuracy**: Similar improvement expected

## 🔧 Configuration

Edit `main.py` to change hyperparameters:

```python
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BATCH_SIZE = 32            # Change batch size
LEARNING_RATE = 0.01       # Change learning rate
NUM_EPOCHS = 10            # Change number of epochs
EMBEDDING_DIM = 128        # Change embedding dimension
```

## 📝 Module Descriptions

### `dataset.py`
- **VFLCIFARDataset**: Custom PyTorch Dataset that:
  - Loads CIFAR-10 images (3 × 32 × 32)
  - Splits vertically into half_A and half_B (each 3 × 32 × 16)
  - Returns `(half_A, half_B, label)`

### `client_bao.py`
- **BottomModel**: Modified ResNet-18 that accepts (3 × 32 × 16) input
  - First conv layer: 3 → 32 channels with stride=1
  - Outputs 128-dim embedding
  
- **ClientWorker**: Manages Client's training
  - `forward()`: Processes half_B → embedding
  - `backward()`: Receives gradient from Server, updates weights

### `server_chien.py`
- **BottomModelServer**: Simple CNN for Server's half image
  - Processes half_A (3 × 32 × 16)
  - Outputs 128-dim embedding

- **TopModel**: FCNN-4 for final classification
  - Input: 256-dim (128+128 concatenated)
  - Hidden layers: 256 → 256 → 128 → 10 classes
  
- **ServerCoordinator**: Orchestrates training
  - `forward_and_loss()`: Computes loss
  - `compute_gradients_and_update()`: Backprop, returns gradient for Client

### `main.py`
- Training loop with Split Learning orchestration
- Epoch-based training with train/test evaluation
- Metrics tracking and final summary

## ✅ Success Criteria

Training is successful when:

1. ✅ Code runs without errors
2. ✅ Loss **decreases** from Epoch 1 to Epoch 10
3. ✅ Accuracy **increases** from Epoch 1 to Epoch 10
4. ✅ No NaN or Inf values in loss/accuracy
5. ✅ Final accuracy > 50% (ideally > 70%)

## 🐛 Troubleshooting

### Issue: CUDA out of memory
- Reduce `BATCH_SIZE` in `main.py`
- Use CPU: `DEVICE = torch.device('cpu')`

### Issue: Loss is NaN
- Reduce `LEARNING_RATE`
- Check data normalization in `dataset.py`

### Issue: Slow training
- Ensure CUDA is being used: Check output shows "Device: cuda"
- Reduce `NUM_EPOCHS` for testing

### Issue: Import errors
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Use Python 3.8+ and PyTorch 2.0+

## 📚 References

- CIFAR-10 Dataset: https://www.cs.toronto.edu/~kriz/cifar.html
- PyTorch Documentation: https://pytorch.org/docs/
- ResNet Paper: https://arxiv.org/abs/1512.03385

## 🎯 Next Steps (GIAI ĐOẠN 2)

Once this Base VFL system runs successfully with decreasing loss and increasing accuracy:

1. Contact the instructor for **PROMPT GIAI ĐOẠN 2**
2. Implement Malicious Optimizer for label stealing
3. Add Byzantine attack capabilities
4. Implement defense mechanisms

---

**Happy Coding! 🚀**
