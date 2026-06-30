#!/usr/bin/env python3
"""
Phase 3 FLSG Defense Training - Full 30-epoch comparison
Uses synthetic CIFAR-10 dataset for reliable execution
"""

import json
import sys
import os
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flsg_defender import FLSG_Defender
except:
    FLSG_Defender = None

# ============================================================================
# CONFIGURATION
# ============================================================================

DEVICE = torch.device('cpu')
BATCH_SIZE = 128
EPOCHS = 30
LEARNING_RATE = 0.001
NUM_CLASSES = 10

# FLSG Defense parameters
DEFENSE_CONFIG = {
    'tau': 0.1,      # Cosine distance threshold
    'R': 1000,       # Number of fake gradients to generate
}

SYNTHETIC_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "cifar-10-batches-py"

# ============================================================================
# DATA LOADING
# ============================================================================

def load_synthetic_cifar10(data_path):
    """Load synthetic CIFAR-10 from pickle files"""
    print(f"📥 Loading synthetic CIFAR-10 from {data_path}...")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Synthetic data path not found: {data_path}")
    
    # Load training data
    train_data = []
    train_labels = []
    
    for i in range(1, 6):  # data_batch_1 to data_batch_5
        batch_file = data_path / f"data_batch_{i}"
        if batch_file.exists():
            with open(batch_file, 'rb') as f:
                batch = pickle.load(f, encoding='bytes')
                train_data.append(batch[b'data'])
                train_labels.extend(batch[b'labels'])
    
    # Load test data
    test_file = data_path / "test_batch"
    if test_file.exists():
        with open(test_file, 'rb') as f:
            test_batch = pickle.load(f, encoding='bytes')
            test_data = test_batch[b'data']
            test_labels = test_batch[b'labels']
    else:
        raise FileNotFoundError("test_batch not found")
    
    # Concatenate training data
    train_data = np.vstack(train_data)
    train_labels = np.array(train_labels)
    
    # Normalize and reshape
    train_data = train_data.astype(np.float32) / 255.0  # [N, 3072]
    test_data = test_data.astype(np.float32) / 255.0
    
    # Reshape to [N, 3, 32, 32]
    train_data = train_data.reshape(-1, 3, 32, 32)
    test_data = test_data.reshape(-1, 3, 32, 32)
    
    # Split data: left 16 pixels (client) and right 16 pixels (server)
    # VFL: Client gets [0:16], Server gets [16:32]
    train_left = train_data[:, :, :, :16]  # [N, 3, 32, 16]
    train_right = train_data[:, :, :, 16:]  # [N, 3, 32, 16]
    test_left = test_data[:, :, :, :16]
    test_right = test_data[:, :, :, 16:]
    
    print(f"✅ Loaded {len(train_data)} training samples, {len(test_data)} test samples")
    print(f"   Train left shape: {train_left.shape}, Train right shape: {train_right.shape}")
    
    return {
        'train_left': torch.FloatTensor(train_left),
        'train_right': torch.FloatTensor(train_right),
        'train_labels': torch.LongTensor(train_labels),
        'test_left': torch.FloatTensor(test_left),
        'test_right': torch.FloatTensor(test_right),
        'test_labels': torch.LongTensor(test_labels),
    }

# ============================================================================
# SIMPLE MODELS FOR TESTING
# ============================================================================

class SimpleClientModel(nn.Module):
    """Simple 2-layer CNN for client (left half of image)"""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        # Input: [N, 3, 32, 16]
        # After conv1+pool: [N, 16, 16, 8]
        # After conv2+pool: [N, 32, 8, 4]
        # Flattened: 32 * 8 * 4 = 1024
        self.fc = nn.Linear(32 * 8 * 4, 128)
    
    def forward(self, x):
        x = self.relu(self.conv1(x))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

class SimpleServerModel(nn.Module):
    """Simple server model that takes client output + right half"""
    def __init__(self):
        super().__init__()
        # Process right half: [N, 3, 32, 16] -> [N, 32, 8, 4] -> [N, 1024]
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2)
        self.relu = nn.ReLU()
        
        # Combine with client output (128 + 1024 = 1152)
        self.fc1 = nn.Linear(128 + 1024, 256)
        self.fc2 = nn.Linear(256, 10)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, client_output, server_input):
        # Process right half
        x = self.relu(self.conv1(server_input))
        x = self.pool(x)
        x = self.relu(self.conv2(x))
        x = self.pool(x)
        x = x.view(x.size(0), -1)
        
        # Combine
        x = torch.cat([client_output, x], dim=1)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x

# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================

def train_baseline(model, server_model, train_loader, criterion, optimizer, device):
    """Train without defense"""
    model.train()
    server_model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (x_left, x_right, y) in enumerate(train_loader):
        x_left = x_left.to(device)
        x_right = x_right.to(device)
        y = y.to(device)
        
        optimizer.zero_grad()
        
        # Client forward
        client_output = model(x_left)
        
        # Server forward
        logits = server_model(client_output.detach(), x_right)
        
        # Loss and backward
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = logits.max(1)
        correct += predicted.eq(y).sum().item()
        total += y.size(0)
    
    accuracy = correct / total
    avg_loss = total_loss / len(train_loader)
    
    return avg_loss, accuracy

def train_with_flsg_defense(model, server_model, train_loader, criterion, optimizer, 
                            flsg_defender, device, **defense_kwargs):
    """Train with FLSG Defense"""
    model.train()
    server_model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (x_left, x_right, y) in enumerate(train_loader):
        x_left = x_left.to(device)
        x_right = x_right.to(device)
        y = y.to(device)
        
        optimizer.zero_grad()
        
        # Client forward
        client_output = model(x_left)
        
        # Server forward
        logits = server_model(client_output.detach(), x_right)
        
        # Loss and backward
        loss = criterion(logits, y)
        loss.backward()
        
        # Apply FLSG Defense to client output gradient
        if client_output.grad is not None:
            g_obfuscated = flsg_defender.apply_defense(
                client_output.grad,
                tau=defense_kwargs.get('tau', 0.1),
                R=defense_kwargs.get('R', 1000)
            )
            client_output.grad = g_obfuscated
        
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = logits.max(1)
        correct += predicted.eq(y).sum().item()
        total += y.size(0)
    
    accuracy = correct / total
    avg_loss = total_loss / len(train_loader)
    
    return avg_loss, accuracy

def evaluate(model, server_model, test_loader, criterion, device):
    """Evaluate on test set"""
    model.eval()
    server_model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for x_left, x_right, y in test_loader:
            x_left = x_left.to(device)
            x_right = x_right.to(device)
            y = y.to(device)
            
            client_output = model(x_left)
            logits = server_model(client_output, x_right)
            
            loss = criterion(logits, y)
            total_loss += loss.item()
            
            _, predicted = logits.max(1)
            correct += predicted.eq(y).sum().item()
            total += y.size(0)
    
    accuracy = correct / total
    avg_loss = total_loss / len(test_loader)
    
    return avg_loss, accuracy

# ============================================================================
# MAIN TRAINING LOOP
# ============================================================================

def main():
    print("="*80)
    print("🚀 PHASE 3 FLSG DEFENSE TRAINING - FULL 30 EPOCHS")
    print("="*80)
    print(f"Device: {DEVICE}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Estimated duration: 3-4 hours (CPU)")
    print("="*80)
    
    # Load data
    try:
        data = load_synthetic_cifar10(SYNTHETIC_DATA_PATH)
    except Exception as e:
        print(f"❌ Error loading synthetic data: {e}")
        print("   Creating synthetic random data instead...")
        # Create synthetic data
        n_train = 5000
        n_test = 1000
        data = {
            'train_left': torch.randn(n_train, 3, 32, 16),
            'train_right': torch.randn(n_train, 3, 32, 16),
            'train_labels': torch.randint(0, 10, (n_train,)),
            'test_left': torch.randn(n_test, 3, 32, 16),
            'test_right': torch.randn(n_test, 3, 32, 16),
            'test_labels': torch.randint(0, 10, (n_test,)),
        }
    
    # Create data loaders
    train_dataset = TensorDataset(
        data['train_left'], data['train_right'], data['train_labels']
    )
    test_dataset = TensorDataset(
        data['test_left'], data['test_right'], data['test_labels']
    )
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    print(f"✅ Data loaded: {len(train_dataset)} train, {len(test_dataset)} test")
    print(f"   Batch size: {BATCH_SIZE}, Train batches: {len(train_loader)}")
    print()
    
    # Initialize models
    client_model = SimpleClientModel().to(DEVICE)
    server_model = SimpleServerModel().to(DEVICE)
    flsg_defender = FLSG_Defender(device=DEVICE)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(
        list(client_model.parameters()) + list(server_model.parameters()),
        lr=LEARNING_RATE
    )
    
    print("🤖 Models initialized:")
    print(f"   Client model: {client_model.__class__.__name__}")
    print(f"   Server model: {server_model.__class__.__name__}")
    print(f"   FLSG Defender: tau={DEFENSE_CONFIG['tau']}, R={DEFENSE_CONFIG['R']}")
    print()
    
    # Training history
    results = {
        'baseline': {'train_loss': [], 'train_acc': [], 'test_loss': [], 'test_acc': []},
        'defense': {'train_loss': [], 'train_acc': [], 'test_loss': [], 'test_acc': []},
        'timing': {},
        'epochs': EPOCHS,
    }
    
    start_time = time.time()
    
    # Training loop
    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.time()
        
        print(f"📊 Epoch {epoch:2d}/{EPOCHS} | ", end='', flush=True)
        
        # Baseline training
        baseline_train_loss, baseline_train_acc = train_baseline(
            client_model, server_model, train_loader, criterion, optimizer, DEVICE
        )
        baseline_test_loss, baseline_test_acc = evaluate(
            client_model, server_model, test_loader, criterion, DEVICE
        )
        
        results['baseline']['train_loss'].append(baseline_train_loss)
        results['baseline']['train_acc'].append(baseline_train_acc)
        results['baseline']['test_loss'].append(baseline_test_loss)
        results['baseline']['test_acc'].append(baseline_test_acc)
        
        # Defense training (same models, but with FLSG defense applied)
        defense_train_loss, defense_train_acc = train_with_flsg_defense(
            client_model, server_model, train_loader, criterion, optimizer,
            flsg_defender, DEVICE, **DEFENSE_CONFIG
        )
        defense_test_loss, defense_test_acc = evaluate(
            client_model, server_model, test_loader, criterion, DEVICE
        )
        
        results['defense']['train_loss'].append(defense_train_loss)
        results['defense']['train_acc'].append(defense_train_acc)
        results['defense']['test_loss'].append(defense_test_loss)
        results['defense']['test_acc'].append(defense_test_acc)
        
        epoch_time = time.time() - epoch_start
        elapsed = time.time() - start_time
        remaining = (elapsed / epoch) * (EPOCHS - epoch)
        
        print(f"Baseline: L={baseline_test_loss:.3f} A={baseline_test_acc:.3f} | ", end='')
        print(f"Defense: L={defense_test_loss:.3f} A={defense_test_acc:.3f} | ", end='')
        print(f"Time: {epoch_time:.1f}s | ETA: {timedelta(seconds=int(remaining))}")
        
        # Save checkpoint every 5 epochs
        if epoch % 5 == 0:
            checkpoint_path = Path(__file__).parent / f"checkpoint_epoch_{epoch:02d}_flsg.json"
            with open(checkpoint_path, 'w') as f:
                json.dump({
                    'epoch': epoch,
                    'baseline_acc': baseline_test_acc,
                    'defense_acc': defense_test_acc,
                    'baseline_loss': baseline_test_loss,
                    'defense_loss': defense_test_loss,
                }, f, indent=2)
            print(f"           💾 Checkpoint saved")
    
    # Final results
    print()
    print("="*80)
    print("📈 FINAL RESULTS")
    print("="*80)
    
    final_baseline_acc = results['baseline']['test_acc'][-1]
    final_defense_acc = results['defense']['test_acc'][-1]
    accuracy_diff = final_baseline_acc - final_defense_acc
    
    print(f"✅ Baseline accuracy:  {final_baseline_acc:.4f}")
    print(f"✅ Defense accuracy:   {final_defense_acc:.4f}")
    print(f"📊 Accuracy loss:      {accuracy_diff:.4f} ({accuracy_diff*100:.2f}%)")
    print()
    
    total_time = time.time() - start_time
    print(f"⏱️  Total training time: {total_time/3600:.2f} hours")
    print("="*80)
    
    # Save results
    results['timing'] = {'total_seconds': total_time, 'total_hours': total_time/3600}
    results_path = Path(__file__).parent / "full_training_results_flsg.json"
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=float)
    
    print(f"✅ Results saved to: {results_path}")

if __name__ == '__main__':
    main()
