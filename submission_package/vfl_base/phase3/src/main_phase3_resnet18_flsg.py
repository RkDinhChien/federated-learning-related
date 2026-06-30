#!/usr/bin/env python3
"""
Phase 3 FLSG Defense with REAL ResNet-18 Model
Uses actual ResNet-18 architecture + Real CIFAR-10
"""

import json
import sys
import pickle
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torchvision.models import resnet18
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
try:
    from flsg_defender import FLSG_Defender
except:
    FLSG_Defender = None

# ============================================================================
# CONFIG
# ============================================================================

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
BATCH_SIZE = 128
EPOCHS = 3  # Quick test with real model
LEARNING_RATE = 0.001

DEFENSE_CONFIG = {'tau': 0.1, 'R': 1000}
CIFAR_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cifar-10-batches-py"

print(f"🖥️  Using device: {DEVICE}")

# ============================================================================
# MODELS - REAL ARCHITECTURES
# ============================================================================

class ResNet18BottomModel(nn.Module):
    """ResNet-18 Bottom Model (Client) - Modified for half-image input"""
    def __init__(self):
        super().__init__()
        # Load pretrained ResNet-18
        resnet = resnet18(pretrained=False)  # Load without pretrain for speed
        
        # Modify first conv to accept 3×32×16 input (half of CIFAR-10)
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1)
        self.bn1 = resnet.bn1
        self.relu = resnet.relu
        self.maxpool = resnet.maxpool
        
        # Keep residual blocks
        self.layer1 = resnet.layer1
        self.layer2 = resnet.layer2
        self.layer3 = resnet.layer3
        self.layer4 = resnet.layer4
        self.avgpool = resnet.avgpool
        
        # Output feature dimension
        self.feature_dim = 512
        self.fc = nn.Linear(512, 128)
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)
        
        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)
        
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class ResNet18ServerModel(nn.Module):
    """Server model to process right half + client embedding"""
    def __init__(self):
        super().__init__()
        # Process right half with simple CNN
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU()
        
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        
        # Combine client embedding (128) + server features (128)
        self.fc1 = nn.Linear(128 + 128, 256)
        self.fc2 = nn.Linear(256, 10)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, client_output, server_input):
        # Process right half
        x = self.conv1(server_input)
        x = self.bn1(x)
        x = self.relu(x)
        
        x = self.conv2(x)
        x = self.bn2(x)
        x = self.relu(x)
        
        x = self.avgpool(x)
        x = x.view(x.size(0), -1)
        
        # Combine with client embedding
        x = torch.cat([client_output, x], dim=1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# ============================================================================
# DATA LOADING
# ============================================================================

def load_real_cifar10(num_train=30000, num_test=5000):
    """Load real CIFAR-10 data"""
    print(f"📥 Loading real CIFAR-10 ({num_train} train, {num_test} test)...", end=' ', flush=True)
    
    # Load training batches
    train_data = []
    train_labels = []
    total = 0
    
    for i in range(1, 6):
        batch_path = CIFAR_PATH / f"data_batch_{i}"
        if not batch_path.exists():
            raise FileNotFoundError(f"Missing {batch_path}")
        
        with open(batch_path, 'rb') as f:
            batch = pickle.load(f, encoding='bytes')
            batch_data = batch[b'data'][:num_train - total]
            batch_labels = batch[b'labels'][:num_train - total]
            
            train_data.append(batch_data)
            train_labels.extend(batch_labels)
            total += len(batch_data)
            
            if total >= num_train:
                break
    
    # Load test
    test_path = CIFAR_PATH / "test_batch"
    with open(test_path, 'rb') as f:
        batch = pickle.load(f, encoding='bytes')
        test_data = batch[b'data'][:num_test]
        test_labels = batch[b'labels'][:num_test]
    
    # Concatenate and normalize
    train_data = np.vstack(train_data).astype(np.float32) / 255.0
    test_data = test_data.astype(np.float32) / 255.0
    train_labels = np.array(train_labels)
    test_labels = np.array(test_labels)
    
    # Reshape to images
    train_data = train_data.reshape(-1, 3, 32, 32)
    test_data = test_data.reshape(-1, 3, 32, 32)
    
    # Split left/right for VFL
    train_left = train_data[:, :, :, :16]
    train_right = train_data[:, :, :, 16:]
    test_left = test_data[:, :, :, :16]
    test_right = test_data[:, :, :, 16:]
    
    print("✅")
    
    return {
        'train_left': torch.FloatTensor(train_left),
        'train_right': torch.FloatTensor(train_right),
        'train_labels': torch.LongTensor(train_labels),
        'test_left': torch.FloatTensor(test_left),
        'test_right': torch.FloatTensor(test_right),
        'test_labels': torch.LongTensor(test_labels),
    }

# ============================================================================
# TRAINING
# ============================================================================

def train_baseline(model, server_model, train_loader, criterion, optimizer, device):
    model.train()
    server_model.train()
    correct = total = 0
    loss_sum = 0
    
    for x_left, x_right, y in train_loader:
        optimizer.zero_grad()
        client_output = model(x_left.to(device))
        logits = server_model(client_output.detach(), x_right.to(device))
        loss = criterion(logits, y.to(device))
        loss.backward()
        optimizer.step()
        
        loss_sum += loss.item()
        _, predicted = logits.max(1)
        correct += predicted.eq(y.to(device)).sum().item()
        total += y.size(0)
    
    return loss_sum / len(train_loader), correct / total

def train_with_defense(model, server_model, train_loader, criterion, optimizer, 
                       flsg_defender, device, **defense_kwargs):
    model.train()
    server_model.train()
    correct = total = 0
    loss_sum = 0
    
    for x_left, x_right, y in train_loader:
        optimizer.zero_grad()
        client_output = model(x_left.to(device))
        logits = server_model(client_output.detach(), x_right.to(device))
        loss = criterion(logits, y.to(device))
        loss.backward()
        
        if client_output.grad is not None:
            g_obf = flsg_defender.apply_defense(client_output.grad, 
                                                tau=defense_kwargs.get('tau', 0.1),
                                                R=defense_kwargs.get('R', 1000))
            client_output.grad = g_obf
        
        optimizer.step()
        
        loss_sum += loss.item()
        _, predicted = logits.max(1)
        correct += predicted.eq(y.to(device)).sum().item()
        total += y.size(0)
    
    return loss_sum / len(train_loader), correct / total

def evaluate(model, server_model, test_loader, device):
    model.eval()
    server_model.eval()
    correct = total = 0
    loss_sum = 0
    
    with torch.no_grad():
        for x_left, x_right, y in test_loader:
            client_output = model(x_left.to(device))
            logits = server_model(client_output, x_right.to(device))
            
            _, predicted = logits.max(1)
            correct += predicted.eq(y.to(device)).sum().item()
            total += y.size(0)
    
    return correct / total

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("="*70)
    print("🚀 REAL ResNet-18 with FLSG Defense (3 epochs, 30K real CIFAR-10)")
    print("="*70)
    
    start = time.time()
    
    # Load data
    try:
        data = load_real_cifar10(num_train=30000, num_test=5000)
    except Exception as e:
        print(f"❌ Error loading real data: {e}")
        return
    
    train_ds = TensorDataset(data['train_left'], data['train_right'], data['train_labels'])
    test_ds = TensorDataset(data['test_left'], data['test_right'], data['test_labels'])
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    print(f"📊 Data: {len(train_ds)} train, {len(test_ds)} test | Batches: {len(train_loader)}")
    
    # Models
    print("🤖 Building REAL ResNet-18 models...", end=' ', flush=True)
    client = ResNet18BottomModel().to(DEVICE)
    server = ResNet18ServerModel().to(DEVICE)
    flsg = FLSG_Defender(device=DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        list(client.parameters()) + list(server.parameters()),
        lr=LEARNING_RATE
    )
    print("✅")
    
    print(f"📈 Model sizes:")
    print(f"   Client params: {sum(p.numel() for p in client.parameters()):,}")
    print(f"   Server params: {sum(p.numel() for p in server.parameters()):,}")
    print()
    
    # Training
    print("🚀 Training with FLSG Defense...")
    results = {
        'baseline': {'losses': [], 'accs': [], 'test_accs': []},
        'defense': {'losses': [], 'accs': [], 'test_accs': []},
        'times': []
    }
    
    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        
        # Train
        b_loss, b_acc = train_baseline(client, server, train_loader, criterion, optimizer, DEVICE)
        d_loss, d_acc = train_with_defense(client, server, train_loader, criterion, optimizer, flsg, DEVICE, **DEFENSE_CONFIG)
        
        # Test
        b_test = evaluate(client, server, test_loader, DEVICE)
        d_test = evaluate(client, server, test_loader, DEVICE)
        
        results['baseline']['losses'].append(b_loss)
        results['baseline']['accs'].append(b_acc)
        results['baseline']['test_accs'].append(b_test)
        
        results['defense']['losses'].append(d_loss)
        results['defense']['accs'].append(d_acc)
        results['defense']['test_accs'].append(d_test)
        
        epoch_time = time.time() - epoch_start
        results['times'].append(epoch_time)
        
        print(f"  Epoch {epoch}/3")
        print(f"    Baseline: Train Loss={b_loss:.4f} Acc={b_acc:.3f} | Test Acc={b_test:.3f}")
        print(f"    Defense:  Train Loss={d_loss:.4f} Acc={d_acc:.3f} | Test Acc={d_test:.3f}")
        print(f"    Time: {epoch_time:.1f}s")
    
    total_time = time.time() - start
    
    # Results
    print()
    print("="*70)
    print("📈 FINAL RESULTS - REAL ResNet-18")
    print("="*70)
    
    final_b_acc = results['baseline']['test_accs'][-1]
    final_d_acc = results['defense']['test_accs'][-1]
    
    print(f"✅ Baseline Test Accuracy: {final_b_acc:.4f} ({final_b_acc*100:.2f}%)")
    print(f"✅ Defense Test Accuracy:  {final_d_acc:.4f} ({final_d_acc*100:.2f}%)")
    print(f"📊 Accuracy Difference:    {(final_b_acc - final_d_acc):.4f} ({(final_b_acc - final_d_acc)*100:.2f}%)")
    print()
    print(f"⏱️  Total training time: {total_time:.1f}s ({total_time/EPOCHS:.1f}s per epoch)")
    print("="*70)
    
    # Save
    with open(Path(__file__).parent / "resnet18_flsg_results.json", 'w') as f:
        json.dump({
            'name': 'Real ResNet-18 with FLSG Defense',
            'data_config': {
                'train_samples': 30000,
                'test_samples': 5000,
                'data_type': 'Real CIFAR-10'
            },
            'model_config': {
                'client_model': 'ResNet-18 (modified)',
                'server_model': 'Custom CNN',
                'defense': 'FLSG (R=1000, tau=0.1)'
            },
            'baseline': {
                'train_losses': results['baseline']['losses'],
                'train_accs': results['baseline']['accs'],
                'test_accs': results['baseline']['test_accs'],
            },
            'defense': {
                'train_losses': results['defense']['losses'],
                'train_accs': results['defense']['accs'],
                'test_accs': results['defense']['test_accs'],
            },
            'times': results['times'],
            'total_time': total_time,
            'epochs': EPOCHS,
            'device': str(DEVICE),
        }, f, indent=2)
    
    print()
    print("✅ Results saved: resnet18_flsg_results.json")

if __name__ == '__main__':
    main()
