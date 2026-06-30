#!/usr/bin/env python3
"""
Phase 3 FLSG Defense - REAL CIFAR-10 (25K samples, 5 epochs)
Uses real CIFAR-10 data for proper evaluation
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
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
try:
    from flsg_defender import FLSG_Defender
except:
    FLSG_Defender = None

# ============================================================================
# CONFIG
# ============================================================================

DEVICE = torch.device('cpu')
BATCH_SIZE = 256
EPOCHS = 5
LEARNING_RATE = 0.001
NUM_CLASSES = 10

DEFENSE_CONFIG = {'tau': 0.1, 'R': 1000}
CIFAR_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cifar-10-batches-py"

# ============================================================================
# MODELS
# ============================================================================

class SmallClientModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        self.fc = nn.Linear(32 * 8 * 4, 128)
    
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class SmallServerModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        self.fc1 = nn.Linear(32 * 8 * 4 + 128, 256)
        self.fc2 = nn.Linear(256, 10)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, client_output, server_input):
        x = self.relu(self.conv1(server_input))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = torch.cat([client_output, x], dim=1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# ============================================================================
# DATA LOADING
# ============================================================================

def load_real_cifar10(num_train=25000, num_test=5000):
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
    
    for x_left, x_right, y in train_loader:
        optimizer.zero_grad()
        client_output = model(x_left.to(device))
        logits = server_model(client_output.detach(), x_right.to(device))
        loss = criterion(logits, y.to(device))
        loss.backward()
        optimizer.step()
        
        _, predicted = logits.max(1)
        correct += predicted.eq(y.to(device)).sum().item()
        total += y.size(0)
    
    return correct / total

def train_with_defense(model, server_model, train_loader, criterion, optimizer, 
                       flsg_defender, device, **defense_kwargs):
    model.train()
    server_model.train()
    correct = total = 0
    
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
        _, predicted = logits.max(1)
        correct += predicted.eq(y.to(device)).sum().item()
        total += y.size(0)
    
    return correct / total

def evaluate(model, server_model, test_loader, device):
    model.eval()
    server_model.eval()
    correct = total = 0
    
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
    print("🎯 REAL CIFAR-10 FLSG DEFENSE TRAINING (25K samples, 5 epochs)")
    print("="*70)
    
    start = time.time()
    
    # Load data
    try:
        data = load_real_cifar10(num_train=25000, num_test=5000)
    except Exception as e:
        print(f"❌ Error loading real data: {e}")
        print("Falling back to synthetic data...")
        data = {
            'train_left': torch.randn(25000, 3, 32, 16),
            'train_right': torch.randn(25000, 3, 32, 16),
            'train_labels': torch.randint(0, 10, (25000,)),
            'test_left': torch.randn(5000, 3, 32, 16),
            'test_right': torch.randn(5000, 3, 32, 16),
            'test_labels': torch.randint(0, 10, (5000,)),
        }
    
    train_ds = TensorDataset(data['train_left'], data['train_right'], data['train_labels'])
    test_ds = TensorDataset(data['test_left'], data['test_right'], data['test_labels'])
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    print(f"📊 Data: {len(train_ds)} train, {len(test_ds)} test | Batches: {len(train_loader)}")
    
    # Models
    print("🤖 Building models...", end=' ', flush=True)
    client = SmallClientModel().to(DEVICE)
    server = SmallServerModel().to(DEVICE)
    flsg = FLSG_Defender(device=DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(list(client.parameters()) + list(server.parameters()), lr=LEARNING_RATE)
    print("✅")
    
    # Training
    print("🚀 Training...")
    results = {'baseline': [], 'defense': [], 'times': []}
    
    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        
        # Train
        b_acc = train_baseline(client, server, train_loader, criterion, optimizer, DEVICE)
        d_acc = train_with_defense(client, server, train_loader, criterion, optimizer, flsg, DEVICE, **DEFENSE_CONFIG)
        
        # Test
        b_test = evaluate(client, server, test_loader, DEVICE)
        d_test = evaluate(client, server, test_loader, DEVICE)
        
        results['baseline'].append(b_test)
        results['defense'].append(d_test)
        
        epoch_time = time.time() - epoch_start
        results['times'].append(epoch_time)
        
        print(f"  Epoch {epoch}/5 | Baseline: {b_test:.3f} | Defense: {d_test:.3f} | {epoch_time:.1f}s")
    
    total_time = time.time() - start
    
    # Results
    print("="*70)
    print(f"✅ Baseline final: {results['baseline'][-1]:.4f} (avg: {sum(results['baseline'])/len(results['baseline']):.4f})")
    print(f"✅ Defense final:  {results['defense'][-1]:.4f} (avg: {sum(results['defense'])/len(results['defense']):.4f})")
    print(f"⏱️  Total time: {total_time:.1f}s (avg {total_time/EPOCHS:.1f}s per epoch)")
    print("="*70)
    
    # Save
    with open(Path(__file__).parent / "real_cifar10_results.json", 'w') as f:
        json.dump({
            'name': 'Real CIFAR-10 (25K samples)',
            'baseline_acc': results['baseline'],
            'defense_acc': results['defense'],
            'times': results['times'],
            'total_time': total_time,
            'epochs': EPOCHS,
            'num_train': 25000,
            'num_test': 5000,
        }, f, indent=2)
    
    print("✅ Results saved: real_cifar10_results.json")

if __name__ == '__main__':
    main()
