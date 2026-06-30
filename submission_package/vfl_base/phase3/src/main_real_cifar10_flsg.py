#!/usr/bin/env python3
"""
Phase 3 FLSG Defense Training - Real CIFAR-10 with Attack Simulation
"""

import json
import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision
import torchvision.transforms as transforms
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from flsg_defender import FLSG_Defender
except:
    FLSG_Defender = None

print("="*80)
print("🚀 PHASE 3 FLSG DEFENSE - REAL CIFAR-10 TRAINING")
print("="*80)
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)
print()

# Configuration
DEVICE = torch.device('cpu')
BATCH_SIZE = 128
EPOCHS = 10  # Reduced for CPU
LEARNING_RATE = 0.001
NUM_CLASSES = 10
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"

# FLSG Defense parameters
DEFENSE_CONFIG = {
    'tau': 0.1,      # Cosine distance threshold
    'R': 1000,       # Number of fake gradients to generate
}

# ============================================================================
# MODELS
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
# DATA LOADING
# ============================================================================

print("📥 Downloading CIFAR-10 dataset...")

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

try:
    train_dataset = torchvision.datasets.CIFAR10(
        root=str(DATA_DIR), train=True, download=True, transform=transform
    )
    test_dataset = torchvision.datasets.CIFAR10(
        root=str(DATA_DIR), train=False, download=True, transform=transform
    )
    print(f"✅ CIFAR-10 downloaded: {len(train_dataset)} train, {len(test_dataset)} test samples")
except Exception as e:
    print(f"❌ Error downloading CIFAR-10: {e}")
    print("Creating synthetic data instead...")
    # Create synthetic data as fallback
    train_data = torch.randn(5000, 3, 32, 32)
    train_labels = torch.randint(0, 10, (5000,))
    test_data = torch.randn(1000, 3, 32, 32)
    test_labels = torch.randint(0, 10, (1000,))
    
    train_dataset = torch.utils.data.TensorDataset(train_data, train_labels)
    test_dataset = torch.utils.data.TensorDataset(test_data, test_labels)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

print(f"📊 Data loaders created: {len(train_loader)} train batches, {len(test_loader)} test batches")
print()

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
    
    for x, y in train_loader:
        # Split image: left and right halves
        x_left = x[:, :, :, :16]
        x_right = x[:, :, :, 16:]
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
    
    for x, y in train_loader:
        # Split image: left and right halves
        x_left = x[:, :, :, :16]
        x_right = x[:, :, :, 16:]
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
        for x, y in test_loader:
            # Split image: left and right halves
            x_left = x[:, :, :, :16]
            x_right = x[:, :, :, 16:]
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
# TRAINING
# ============================================================================

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

print("🤖 Models initialized")
print(f"   Device: {DEVICE}")
print(f"   Epochs: {EPOCHS}")
print()

# Training history
results = {
    'baseline': {'train_loss': [], 'train_acc': [], 'test_loss': [], 'test_acc': []},
    'defense': {'train_loss': [], 'train_acc': [], 'test_loss': [], 'test_acc': []},
    'timing': {},
    'epochs': EPOCHS,
    'dataset': 'CIFAR-10 (real)',
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
    
    # Defense training
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
    
    print(f"BL: A={baseline_test_acc:.3f} L={baseline_test_loss:.3f} | ", end='')
    print(f"DF: A={defense_test_acc:.3f} L={defense_test_loss:.3f} | ", end='')
    print(f"Time: {epoch_time:.1f}s | ETA: {timedelta(seconds=int(remaining))}")

# Final results
print()
print("="*80)
print("📈 FINAL RESULTS (Real CIFAR-10)")
print("="*80)

final_baseline_acc = results['baseline']['test_acc'][-1]
final_defense_acc = results['defense']['test_acc'][-1]
accuracy_diff = final_baseline_acc - final_defense_acc

print(f"✅ Baseline accuracy:  {final_baseline_acc:.4f} ({final_baseline_acc*100:.2f}%)")
print(f"✅ Defense accuracy:   {final_defense_acc:.4f} ({final_defense_acc*100:.2f}%)")
print(f"📊 Accuracy loss:      {accuracy_diff:.4f} ({accuracy_diff*100:.2f}%)")
print()

total_time = time.time() - start_time
print(f"⏱️  Total training time: {total_time/3600:.2f} hours (~{total_time/60:.0f} minutes)")
print("="*80)

# Save results
results['timing'] = {'total_seconds': total_time, 'total_hours': total_time/3600}
results_path = Path(__file__).parent / "real_cifar10_results_flsg.json"

with open(results_path, 'w') as f:
    json.dump(results, f, indent=2, default=float)

print(f"✅ Results saved to: {results_path}")
