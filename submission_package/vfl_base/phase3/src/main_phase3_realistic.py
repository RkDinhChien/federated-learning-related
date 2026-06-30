#!/usr/bin/env python3
"""
Phase 3: Realistic Full Training - 30 epochs with 10K samples
FLSG Defense System for Vertical Federated Learning
Timing: ~30-40 minutes on CPU (realistic full experiment)
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as transforms
import json
import time
from datetime import datetime
from config import DEVICE, BATCH_SIZE, DEFENSE_CONFIG, ATTACK_CONFIG
from client_bao import BottomModel
from server_chien import ServerCoordinator
from dataset import VFLCIFARDataset
from malicious_optimizer import MaliciousSGD

print(f"Device: {DEVICE}")
print("=" * 80)

# Load CIFAR-10 dataset
transform = transforms.Compose([
    transforms.ToTensor(),
])

cifar_train = torchvision.datasets.CIFAR10(root='../../../data', train=True, download=True, transform=transform)
cifar_test = torchvision.datasets.CIFAR10(root='../../../data', train=False, download=True, transform=transform)

# Wrap in VFL dataset
dataset = VFLCIFARDataset(cifar_train)
test_dataset = VFLCIFARDataset(cifar_test)

# Use 10,000 samples (20% of full dataset) for realistic training (~30-40 min)
train_subset = Subset(dataset, list(range(min(10000, len(dataset)))))
test_subset = Subset(test_dataset, list(range(min(10000, len(test_dataset)))))

train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE)

print(f"📊 Dataset: {len(train_subset)} train, {len(test_subset)} test samples")
print(f"🔢 Batches: {len(train_loader)} train, {len(test_loader)} test")
print(f"⏱️  Estimated time: 30-40 minutes on CPU")
print("=" * 80)

def train_realistic(server, client, train_loader, test_loader, enable_defense, num_epochs=30):
    """Realistic full training loop - 30 epochs"""
    
    client.train()
    
    # Client optimizer
    client_optimizer = torch.optim.SGD(client.parameters(), lr=0.01)
    
    if enable_defense:
        # Use MaliciousSGD to simulate attack
        attack_optimizer = MaliciousSGD(
            client.parameters(),
            lr=ATTACK_CONFIG.get('lr', 0.001),
            beta=ATTACK_CONFIG['beta'],
            gamma=ATTACK_CONFIG['gamma'],
            r_min=ATTACK_CONFIG['r_min'],
            r_max=ATTACK_CONFIG['r_max']
        )
    
    results = {'losses': [], 'accuracies': [], 'epoch_times': []}
    
    for epoch in range(num_epochs):
        epoch_start = time.time()
        epoch_loss = 0
        batch_count = 0
        
        for batch_idx, (half_a, half_b, labels) in enumerate(train_loader):
            half_a = half_a.to(DEVICE)
            half_b = half_b.to(DEVICE)
            labels = labels.to(DEVICE)
            
            # Client forward
            client_out = client(half_a)
            
            # Server forward & backward
            logits = server.forward(half_b, client_out)
            loss = nn.CrossEntropyLoss()(logits, labels)
            epoch_loss += loss.item()
            batch_count += 1
            
            # Server backward
            server.compute_gradients_and_update(loss)
            
            # Client backward
            client_optimizer.zero_grad()
            client_out.backward(torch.ones_like(client_out))
            
            if enable_defense:
                attack_optimizer.step()
            else:
                client_optimizer.step()
        
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
        results['epoch_times'].append(epoch_time)
        
        # Progress every 5 epochs
        if (epoch + 1) % 5 == 0:
            avg_epoch_time = sum(results['epoch_times']) / len(results['epoch_times'])
            remaining_epochs = num_epochs - (epoch + 1)
            eta_seconds = remaining_epochs * avg_epoch_time
            eta_minutes = eta_seconds / 60
            
            print(f"Epoch {epoch+1:2d}/{num_epochs} | Loss: {avg_loss:.4f} | Acc: {acc:.4f} | "
                  f"Time: {epoch_time:.1f}s | ETA: {eta_minutes:.1f}min")
        
        client.train()
    
    return results

print("\n🚀 REALISTIC FULL TRAINING - 30 Epochs, 10K Samples")
print("=" * 80)

start_total = time.time()

# Baseline
print("\n[1/2] Baseline (no defense)...")
server_baseline = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)
client_baseline = BottomModel().to(DEVICE)
start = time.time()
baseline_results = train_realistic(server_baseline, client_baseline, train_loader, test_loader, False, num_epochs=30)
baseline_time = time.time() - start
print(f"✅ Baseline completed in {baseline_time/60:.1f} minutes")

# Defense
print("\n[2/2] With Defense...")
server_defense = ServerCoordinator(device=DEVICE, enable_defense=True, defense_config=DEFENSE_CONFIG)
client_defense = BottomModel().to(DEVICE)
start = time.time()
defense_results = train_realistic(server_defense, client_defense, train_loader, test_loader, True, num_epochs=30)
defense_time = time.time() - start
print(f"✅ Defense completed in {defense_time/60:.1f} minutes")

total_time = time.time() - start_total

# Detailed Results
print("\n" + "=" * 80)
print("📊 FINAL RESULTS (30 Epochs, 10K Samples)")
print("=" * 80)

baseline_final_acc = baseline_results['accuracies'][-1]
defense_final_acc = defense_results['accuracies'][-1]
baseline_final_loss = baseline_results['losses'][-1]
defense_final_loss = defense_results['losses'][-1]

print(f"\n📈 EPOCH 1 vs EPOCH 30:")
print(f"\nBaseline:")
print(f"  Epoch  1: Loss={baseline_results['losses'][0]:.4f}, Acc={baseline_results['accuracies'][0]:.4f}")
print(f"  Epoch 30: Loss={baseline_final_loss:.4f}, Acc={baseline_final_acc:.4f}")
print(f"  Change:  Loss={baseline_final_loss - baseline_results['losses'][0]:+.4f}, Acc={baseline_final_acc - baseline_results['accuracies'][0]:+.4f}")

print(f"\nWith Defense:")
print(f"  Epoch  1: Loss={defense_results['losses'][0]:.4f}, Acc={defense_results['accuracies'][0]:.4f}")
print(f"  Epoch 30: Loss={defense_final_loss:.4f}, Acc={defense_final_acc:.4f}")
print(f"  Change:  Loss={defense_final_loss - defense_results['losses'][0]:+.4f}, Acc={defense_final_acc - defense_results['accuracies'][0]:+.4f}")

print(f"\n🔍 COMPARISON (Final Epoch 30):")
acc_diff = defense_final_acc - baseline_final_acc
loss_diff = defense_final_loss - baseline_final_loss
print(f"  Baseline Acc: {baseline_final_acc:.4f} → Defense Acc: {defense_final_acc:.4f}")
print(f"  Accuracy change: {acc_diff:+.4f} ({acc_diff/baseline_final_acc*100:+.1f}%)")
print(f"  Baseline Loss: {baseline_final_loss:.4f} → Defense Loss: {defense_final_loss:.4f}")
print(f"  Loss change: {loss_diff:+.4f}")

print(f"\n⏱️  TIMING:")
print(f"  Baseline: {baseline_time/60:.1f} min ({baseline_time/30:.1f}s per epoch)")
print(f"  Defense:  {defense_time/60:.1f} min ({defense_time/30:.1f}s per epoch)")
print(f"  Total:    {total_time/60:.1f} min ({total_time/3600:.1f} hours)")

# Assessment
accuracy_loss_pct = abs(acc_diff / baseline_final_acc * 100) if baseline_final_acc > 0 else 0
if accuracy_loss_pct < 5:
    print(f"\n✅ SUCCESS! Accuracy loss < 5% ({accuracy_loss_pct:.1f}%)")
    print(f"   Defense is effective with minimal accuracy trade-off")
elif accuracy_loss_pct < 10:
    print(f"\n⚠️  Acceptable. Accuracy loss {accuracy_loss_pct:.1f}% (target: < 5%)")
else:
    print(f"\n❌ Too much accuracy loss: {accuracy_loss_pct:.1f}%")

# Save comprehensive results
results = {
    'metadata': {
        'timestamp': datetime.now().isoformat(),
        'device': DEVICE,
        'epochs': 30,
        'samples': 10000,
        'batch_size': BATCH_SIZE,
    },
    'baseline': {
        'losses': baseline_results['losses'],
        'accuracies': baseline_results['accuracies'],
        'epoch_times': baseline_results['epoch_times'],
    },
    'defense': {
        'losses': defense_results['losses'],
        'accuracies': defense_results['accuracies'],
        'epoch_times': defense_results['epoch_times'],
    },
    'timing': {
        'baseline_minutes': baseline_time / 60,
        'defense_minutes': defense_time / 60,
        'total_hours': total_time / 3600,
    },
    'summary': {
        'baseline_final_acc': baseline_final_acc,
        'defense_final_acc': defense_final_acc,
        'accuracy_diff': acc_diff,
        'accuracy_loss_pct': accuracy_loss_pct,
        'baseline_final_loss': baseline_final_loss,
        'defense_final_loss': defense_final_loss,
    }
}

with open('full_training_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to full_training_results.json")
print("\n" + "=" * 80)
