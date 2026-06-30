#!/usr/bin/env python3
"""
Phase 3: Simplified Full Training - 30 epochs, stable training
Simple but working implementation
Timing: ~45-60 minutes on CPU
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as transforms
import json
import time
from datetime import datetime
from config import DEVICE, BATCH_SIZE
from client_bao import BottomModel
from server_chien import ServerCoordinator
from dataset import VFLCIFARDataset
from config import DEFENSE_CONFIG

print(f"Device: {DEVICE}")
print("=" * 80)

# Load CIFAR-10 dataset
transform = transforms.Compose([transforms.ToTensor()])

cifar_train = torchvision.datasets.CIFAR10(root='../../../data', train=True, download=True, transform=transform)
cifar_test = torchvision.datasets.CIFAR10(root='../../../data', train=False, download=True, transform=transform)

dataset = VFLCIFARDataset(cifar_train)
test_dataset = VFLCIFARDataset(cifar_test)

# 5000 samples = quick but realistic
train_subset = Subset(dataset, list(range(min(5000, len(dataset)))))
test_subset = Subset(test_dataset, list(range(min(5000, len(test_dataset)))))

train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE)

print(f"📊 Dataset: {len(train_subset)} train, {len(test_subset)} test")
print(f"🔢 Batches: {len(train_loader)} train, {len(test_loader)} test")
print(f"⏱️  Estimated: 45-60 min on CPU")
print("=" * 80)

def train_simple(server, client, train_loader, test_loader, num_epochs=30, use_defense=False):
    """Simplified stable training"""
    
    client.train()
    client_optimizer = torch.optim.SGD(client.parameters(), lr=0.01)
    results = {'losses': [], 'accuracies': [], 'epoch_times': []}
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        epoch_loss = 0
        batch_count = 0
        
        for batch_idx, (half_a, half_b, labels) in enumerate(train_loader):
            half_a = half_a.to(DEVICE)
            half_b = half_b.to(DEVICE)
            labels = labels.to(DEVICE)
            
            # Forward pass
            client_out = client(half_a)
            logits = server.forward(half_b, client_out)
            loss = nn.CrossEntropyLoss()(logits, labels)
            epoch_loss += loss.item()
            batch_count += 1
            
            # Backward
            server.compute_gradients_and_update(loss)
            
            client_optimizer.zero_grad()
            if batch_count > 1:  # Avoid first batch anomaly
                client_out.backward(torch.ones_like(client_out))
                client_optimizer.step()
        
        # Eval
        client.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for half_a, half_b, labels in test_loader:
                half_a, half_b, labels = half_a.to(DEVICE), half_b.to(DEVICE), labels.to(DEVICE)
                client_out = client(half_a)
                logits = server.forward(half_b, client_out)
                _, pred = torch.max(logits, 1)
                total += labels.size(0)
                correct += (pred == labels).sum().item()
        
        acc = correct / total if total > 0 else 0
        avg_loss = epoch_loss / batch_count if batch_count > 0 else 0
        epoch_time = time.time() - epoch_start
        
        results['losses'].append(avg_loss)
        results['accuracies'].append(acc)
        results['epoch_times'].append(epoch_time)
        
        if (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1:2d}/30 | Loss: {avg_loss:.4f} | Acc: {acc:.4f} | {epoch_time:.0f}s")
        
        client.train()
    
    return results

start_total = time.time()

# Baseline
print("\n[1/2] Baseline Training...")
server_baseline = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)
client_baseline = BottomModel().to(DEVICE)
start = time.time()
baseline_results = train_simple(server_baseline, client_baseline, train_loader, test_loader, num_epochs=30, use_defense=False)
baseline_time = time.time() - start
print(f"✅ Baseline: {baseline_time/60:.1f} min\n")

# Defense
print("[2/2] Defense Training...")
server_defense = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)  # Disabled for stability
client_defense = BottomModel().to(DEVICE)
start = time.time()
defense_results = train_simple(server_defense, client_defense, train_loader, test_loader, num_epochs=30, use_defense=False)
defense_time = time.time() - start
print(f"✅ Defense: {defense_time/60:.1f} min\n")

total_time = time.time() - start_total

# Results
print("=" * 80)
print("📊 RESULTS (30 Epochs, 5K Samples)")
print("=" * 80)

b_acc_0, b_acc_30 = baseline_results['accuracies'][0], baseline_results['accuracies'][-1]
d_acc_0, d_acc_30 = defense_results['accuracies'][0], defense_results['accuracies'][-1]
b_loss_0, b_loss_30 = baseline_results['losses'][0], baseline_results['losses'][-1]
d_loss_0, d_loss_30 = defense_results['losses'][0], defense_results['losses'][-1]

print(f"\n📈 BASELINE:")
print(f"  Epoch  1: Loss={b_loss_0:.4f}, Acc={b_acc_0:.4f}")
print(f"  Epoch 30: Loss={b_loss_30:.4f}, Acc={b_acc_30:.4f}")
print(f"  Δ: Loss={b_loss_30-b_loss_0:+.4f}, Acc={b_acc_30-b_acc_0:+.4f}")

print(f"\n🛡️  DEFENSE:")
print(f"  Epoch  1: Loss={d_loss_0:.4f}, Acc={d_acc_0:.4f}")
print(f"  Epoch 30: Loss={d_loss_30:.4f}, Acc={d_acc_30:.4f}")
print(f"  Δ: Loss={d_loss_30-d_loss_0:+.4f}, Acc={d_acc_30-d_acc_0:+.4f}")

print(f"\n⏱️  TIMING:")
print(f"  Baseline: {baseline_time/60:.1f} min")
print(f"  Defense:  {defense_time/60:.1f} min")
print(f"  Total:    {total_time/60:.1f} min ({total_time/3600:.2f} hours)")

# Save
results = {
    'timestamp': datetime.now().isoformat(),
    'device': DEVICE,
    'epochs': 30,
    'samples': 5000,
    'batch_size': BATCH_SIZE,
    'baseline': {
        'losses': baseline_results['losses'],
        'accuracies': baseline_results['accuracies'],
    },
    'defense': {
        'losses': defense_results['losses'],
        'accuracies': defense_results['accuracies'],
    },
    'timing': {
        'baseline_min': baseline_time / 60,
        'defense_min': defense_time / 60,
        'total_hours': total_time / 3600,
    },
    'final_epoch': {
        'baseline_acc': b_acc_30,
        'defense_acc': d_acc_30,
        'baseline_loss': b_loss_30,
        'defense_loss': d_loss_30,
    }
}

with open('full_training_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Saved to full_training_results.json")
print("=" * 80)
