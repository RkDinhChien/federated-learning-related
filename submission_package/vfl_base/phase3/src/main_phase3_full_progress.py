#!/usr/bin/env python3
"""
Phase 3: FULL TRAINING with Progress Tracking
30 epochs on full CIFAR-10 dataset (~3 hours on CPU)
Shows progress bar and saves checkpoint every epoch
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision
import torchvision.transforms as transforms
import json
import time
import sys
from datetime import datetime, timedelta
from config import DEVICE, BATCH_SIZE, DEFENSE_CONFIG, ATTACK_CONFIG
from client_bao import BottomModel
from server_chien import ServerCoordinator
from dataset import VFLCIFARDataset
from malicious_optimizer import MaliciousSGD

print("=" * 80)
print("🚀 PHASE 3 FULL TRAINING WITH PROGRESS TRACKING")
print("=" * 80)
print(f"Device: {DEVICE}")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Estimated duration: 3 hours (CPU) | 15 minutes (GPU)")
print("=" * 80)

# Download CIFAR-10 from alternative source
import os
import urllib.request
import tarfile

print("📥 Downloading CIFAR-10 from mirror...")

# Create data folder
os.makedirs('data', exist_ok=True)
os.chdir('data')

# Download from alternative source
url = "https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz"
filename = "cifar-10-python.tar.gz"

try:
    print(f"Downloading from: {url}")
    urllib.request.urlretrieve(url, filename)
    print(f"✅ Downloaded {filename}")
    
    # Extract
    print(f"📦 Extracting {filename}...")
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall()
    print("✅ Extracted successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Try downloading manually from: https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz")

# Load CIFAR-10 dataset
transform = transforms.Compose([transforms.ToTensor()])
cifar_train = torchvision.datasets.CIFAR10(root='../../../data', train=True, download=False, transform=transform)
cifar_test = torchvision.datasets.CIFAR10(root='../../../data', train=False, download=False, transform=transform)

dataset = VFLCIFARDataset(cifar_train)
test_dataset = VFLCIFARDataset(cifar_test)

train_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE)

print(f"\n📊 Dataset loaded:")
print(f"   Train: {len(dataset)} samples ({len(train_loader)} batches)")
print(f"   Test:  {len(test_dataset)} samples ({len(test_loader)} batches)")

def progress_bar(current, total, title="", bar_length=40):
    """Display progress bar"""
    percent = current / total
    filled = int(bar_length * percent)
    bar = '█' * filled + '░' * (bar_length - filled)
    return f"{title} [{bar}] {percent*100:.1f}% ({current}/{total})"

def train_full(server, client, train_loader, test_loader, enable_defense, num_epochs=30):
    """Full training with progress tracking"""
    
    client.train()
    client_optimizer = torch.optim.SGD(client.parameters(), lr=0.01)
    
    if enable_defense:
        attack_optimizer = MaliciousSGD(
            client.parameters(),
            lr=ATTACK_CONFIG.get('lr', 0.001),
            beta=ATTACK_CONFIG['beta'],
            gamma=ATTACK_CONFIG['gamma'],
            r_min=ATTACK_CONFIG['r_min'],
            r_max=ATTACK_CONFIG['r_max']
        )
    
    results = {'losses': [], 'accuracies': [], 'times': []}
    total_batches = len(train_loader) * num_epochs
    processed_batches = 0
    epoch_start = time.time()
    
    for epoch in range(num_epochs):
        epoch_loss = 0
        batch_count = 0
        batch_start = time.time()
        
        for batch_idx, (half_a, half_b, labels) in enumerate(train_loader):
            half_a = half_a.to(DEVICE)
            half_b = half_b.to(DEVICE)
            labels = labels.to(DEVICE)
            
            # Forward
            client_out = client(half_a)
            logits = server.forward(half_b, client_out)
            loss = nn.CrossEntropyLoss()(logits, labels)
            epoch_loss += loss.item()
            batch_count += 1
            processed_batches += 1
            
            # Backward
            server.compute_gradients_and_update(loss)
            client_optimizer.zero_grad()
            client_out.backward(torch.ones_like(client_out))
            
            if enable_defense:
                attack_optimizer.step()
            else:
                client_optimizer.step()
            
            # Progress update every 50 batches
            if (batch_idx + 1) % 50 == 0 or batch_idx == len(train_loader) - 1:
                elapsed = time.time() - batch_start
                batch_speed = elapsed / min(50, batch_idx + 1)
                remaining_batches = total_batches - processed_batches
                eta_seconds = remaining_batches * batch_speed
                eta_time = datetime.now() + timedelta(seconds=eta_seconds)
                
                pbar = progress_bar(processed_batches, total_batches, "Progress")
                print(f"\r{pbar} | ETA: {eta_time.strftime('%H:%M:%S')}", end='', flush=True)
        
        # Test accuracy
        client.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for half_a, half_b, labels in test_loader:
                half_a = half_a.to(DEVICE)
                half_b = half_b.to(DEVICE)
                labels = labels.to(DEVICE)
                
                client_out = client(half_a)
                logits = server.forward(half_b, client_out)
                
                _, predicted = torch.max(logits.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        
        acc = correct / total if total > 0 else 0
        avg_loss = epoch_loss / batch_count if batch_count > 0 else 0
        epoch_time = time.time() - epoch_start
        
        results['losses'].append(avg_loss)
        results['accuracies'].append(acc)
        results['times'].append(epoch_time)
        
        # Detailed epoch report
        print(f"\n[Epoch {epoch+1:2d}/{num_epochs}] Loss: {avg_loss:.4f} | Acc: {acc:.4f} | Time: {epoch_time//60:.0f}m {epoch_time%60:.0f}s")
        
        # Save checkpoint every epoch
        checkpoint = {
            'epoch': epoch + 1,
            'baseline_losses': results['losses'],
            'baseline_accuracies': results['accuracies'],
            'defense_enabled': enable_defense,
            'timestamp': datetime.now().isoformat()
        }
        
        checkpoint_file = f"checkpoint_epoch_{epoch+1:02d}_{'defense' if enable_defense else 'baseline'}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        client.train()
        epoch_start = time.time()
    
    print()  # New line after progress bar
    return results

print("\n" + "=" * 80)
print("🔵 BASELINE (No Defense) - 30 Epochs")
print("=" * 80)
start = time.time()
server_baseline = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)
client_baseline = BottomModel().to(DEVICE)
baseline_results = train_full(server_baseline, client_baseline, train_loader, test_loader, False, num_epochs=30)
baseline_time = time.time() - start
print(f"✅ Baseline complete in {baseline_time//60:.0f}m {baseline_time%60:.0f}s")

print("\n" + "=" * 80)
print("🛡️ WITH DEFENSE - 30 Epochs")
print("=" * 80)
start = time.time()
server_defense = ServerCoordinator(device=DEVICE, enable_defense=True, defense_config=DEFENSE_CONFIG)
client_defense = BottomModel().to(DEVICE)
defense_results = train_full(server_defense, client_defense, train_loader, test_loader, True, num_epochs=30)
defense_time = time.time() - start
print(f"✅ Defense complete in {defense_time//60:.0f}m {defense_time%60:.0f}s")

# Final Results
print("\n" + "=" * 80)
print("📊 FINAL RESULTS (30 Epochs)")
print("=" * 80)

print(f"\n🔵 BASELINE:")
print(f"   Final Loss:     {baseline_results['losses'][-1]:.4f}")
print(f"   Final Accuracy: {baseline_results['accuracies'][-1]:.4f}")
print(f"   Total Time:     {baseline_time//60:.0f}m {baseline_time%60:.0f}s")

print(f"\n🛡️  WITH DEFENSE:")
print(f"   Final Loss:     {defense_results['losses'][-1]:.4f}")
print(f"   Final Accuracy: {defense_results['accuracies'][-1]:.4f}")
print(f"   Total Time:     {defense_time//60:.0f}m {defense_time%60:.0f}s")

print(f"\n📈 COMPARISON:")
loss_change = defense_results['losses'][-1] - baseline_results['losses'][-1]
acc_change = defense_results['accuracies'][-1] - baseline_results['accuracies'][-1]
print(f"   Loss change:  {loss_change:+.4f}")
print(f"   Acc change:   {acc_change:+.4f}")

if acc_change < 0.05:  # <5% accuracy loss
    print(f"\n✅ SUCCESS! Accuracy loss is acceptable ({abs(acc_change)*100:.1f}%)")
else:
    print(f"\n⚠️  High accuracy loss: {abs(acc_change)*100:.1f}%")

# Save final results
results = {
    'baseline': {
        'losses': baseline_results['losses'],
        'accuracies': baseline_results['accuracies'],
        'times': baseline_results['times']
    },
    'defense': {
        'losses': defense_results['losses'],
        'accuracies': defense_results['accuracies'],
        'times': defense_results['times']
    },
    'timing': {
        'baseline': baseline_time,
        'defense': defense_time,
        'total': baseline_time + defense_time
    },
    'final_metrics': {
        'baseline_loss': baseline_results['losses'][-1],
        'defense_loss': defense_results['losses'][-1],
        'baseline_acc': baseline_results['accuracies'][-1],
        'defense_acc': defense_results['accuracies'][-1],
        'loss_change': loss_change,
        'acc_change': acc_change
    },
    'timestamp': datetime.now().isoformat()
}

with open('full_training_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to full_training_results.json")
print(f"📁 Checkpoints saved as checkpoint_epoch_*.json")
print("=" * 80)
