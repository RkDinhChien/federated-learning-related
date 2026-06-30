#!/usr/bin/env python3
"""
Phase 3 FLSG Defense - QUICK VERSION (5 epochs, 10K samples)
Runs in ~1-2 minutes for fast testing
"""

import json
import sys
import pickle
import time
from datetime import datetime, timedelta
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
# CONFIGURATION
# ============================================================================

DEVICE = torch.device('cpu')
BATCH_SIZE = 256  # Larger batches = faster
EPOCHS = 5  # Quick test
LEARNING_RATE = 0.001
NUM_CLASSES = 10

DEFENSE_CONFIG = {'tau': 0.1, 'R': 1000}
SYNTHETIC_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cifar-10-batches-py"

# ============================================================================
# MODELS (Smaller)
# ============================================================================

class TinyClientModel(nn.Module):
    """Tiny CNN for speed"""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 8, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        # Input: [N, 3, 32, 16] -> [N, 8, 16, 8] -> flatten to [N, 1024]
        self.fc = nn.Linear(8 * 16 * 8, 64)
    
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class TinyServerModel(nn.Module):
    """Tiny server model"""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 8, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        # Right side: [N, 3, 32, 16] -> [N, 8, 16, 8] -> flatten to [N, 1024]
        # Client output: [N, 64]
        # Combined: [N, 1024 + 64] = [N, 1088]
        self.fc1 = nn.Linear(1024 + 64, 128)
        self.fc2 = nn.Linear(128, 10)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, client_output, server_input):
        x = self.relu(self.conv1(server_input))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = torch.cat([client_output, x], dim=1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# ============================================================================
# TRAINING
# ============================================================================

def load_data_quick():
    """Load only 10K samples for speed"""
    try:
        with open(SYNTHETIC_DATA_PATH / "data_batch_1", 'rb') as f:
            batch = pickle.load(f, encoding='bytes')
            train_data = batch[b'data'][:10000].astype(np.float32) / 255.0
            train_labels = np.array(batch[b'labels'][:10000])
        
        with open(SYNTHETIC_DATA_PATH / "test_batch", 'rb') as f:
            batch = pickle.load(f, encoding='bytes')
            test_data = batch[b'data'][:2000].astype(np.float32) / 255.0
            test_labels = np.array(batch[b'labels'][:2000])
        
        # Reshape and split
        train_data = train_data.reshape(-1, 3, 32, 32)
        test_data = test_data.reshape(-1, 3, 32, 32)
        
        return {
            'train_left': torch.FloatTensor(train_data[:, :, :, :16]),
            'train_right': torch.FloatTensor(train_data[:, :, :, 16:]),
            'train_labels': torch.LongTensor(train_labels),
            'test_left': torch.FloatTensor(test_data[:, :, :, :16]),
            'test_right': torch.FloatTensor(test_data[:, :, :, 16:]),
            'test_labels': torch.LongTensor(test_labels),
        }
    except:
        # Fallback to synthetic random
        n_train, n_test = 10000, 2000
        return {
            'train_left': torch.randn(n_train, 3, 32, 16),
            'train_right': torch.randn(n_train, 3, 32, 16),
            'train_labels': torch.randint(0, 10, (n_train,)),
            'test_left': torch.randn(n_test, 3, 32, 16),
            'test_right': torch.randn(n_test, 3, 32, 16),
            'test_labels': torch.randint(0, 10, (n_test,)),
        }

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

def evaluate(model, server_model, test_loader, criterion, device):
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
    print("⚡ QUICK FLSG TEST (5 epochs, 10K samples)")
    print("="*60)
    
    start = time.time()
    
    # Load data
    print("📥 Loading data...", end=' ', flush=True)
    data = load_data_quick()
    print("✅")
    
    train_ds = TensorDataset(data['train_left'], data['train_right'], data['train_labels'])
    test_ds = TensorDataset(data['test_left'], data['test_right'], data['test_labels'])
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    # Models
    print("🤖 Building models...", end=' ', flush=True)
    client = TinyClientModel().to(DEVICE)
    server = TinyServerModel().to(DEVICE)
    flsg = FLSG_Defender(device=DEVICE)
    criterion = nn.CrossEntropyLoss()
    optim_ = optim.Adam(list(client.parameters()) + list(server.parameters()), lr=LEARNING_RATE)
    print("✅")
    
    # Training
    print("🚀 Training...")
    results = {'baseline': [], 'defense': []}
    
    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        
        b_acc = train_baseline(client, server, train_loader, criterion, optim_, DEVICE)
        d_acc = train_with_defense(client, server, train_loader, criterion, optim_, flsg, DEVICE, **DEFENSE_CONFIG)
        
        b_test = evaluate(client, server, test_loader, criterion, DEVICE)
        d_test = evaluate(client, server, test_loader, criterion, DEVICE)
        
        results['baseline'].append(b_test)
        results['defense'].append(d_test)
        
        elapsed = time.time() - epoch_start
        print(f"  Epoch {epoch}/5 | Baseline: {b_test:.3f} | Defense: {d_test:.3f} | {elapsed:.1f}s")
    
    total_time = time.time() - start
    
    # Results
    print("="*60)
    print(f"✅ Baseline final: {results['baseline'][-1]:.4f}")
    print(f"✅ Defense final:  {results['defense'][-1]:.4f}")
    print(f"⏱️  Total time: {total_time:.1f}s")
    print("="*60)
    
    # Save
    with open(Path(__file__).parent / "quick_flsg_results.json", 'w') as f:
        json.dump({
            'baseline_acc': results['baseline'],
            'defense_acc': results['defense'],
            'time_seconds': total_time,
            'epochs': EPOCHS,
        }, f, indent=2)
    
    print("✅ Results saved: quick_flsg_results.json")

if __name__ == '__main__':
    main()
