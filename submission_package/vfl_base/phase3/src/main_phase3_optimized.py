#!/usr/bin/env python3
"""
Phase 3: Optimized training - 5 epochs (~2 minutes)
FLSG Defense System for Vertical Federated Learning
Significantly reduced dataset size for faster testing
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
import torchvision
import torchvision.transforms as transforms
import json
import time
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

# Use only 500 samples for optimized testing (~2 minutes for 5 epochs)
train_subset = Subset(dataset, list(range(min(500, len(dataset)))))
test_subset = Subset(test_dataset, list(range(min(500, len(test_dataset)))))

train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE)

print(f"Train batches: {len(train_loader)}, Test batches: {len(test_loader)}")
print(f"Total samples: {len(train_subset)} train, {len(test_subset)} test")

def train_optimized(server, client, train_loader, test_loader, enable_defense, num_epochs=5):
    """Optimized training loop"""
    
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
    
    results = {'losses': [], 'accuracies': []}
    
    for epoch in range(num_epochs):
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
            
            # Server backward (computes server gradients and optionally applies defense to client gradients)
            server.compute_gradients_and_update(loss)
            
            # Client backward
            client_optimizer.zero_grad()
            client_out.backward(torch.ones_like(client_out))
            
            if enable_defense:
                # Apply MaliciousSGD on client gradients
                attack_optimizer.step()
            else:
                # Normal update
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
        results['losses'].append(avg_loss)
        results['accuracies'].append(acc)
        
        print(f"Epoch {epoch+1}/{num_epochs} | Loss: {avg_loss:.4f} | Acc: {acc:.4f}")
        client.train()
    
    return results

print("\n⚡ OPTIMIZED TRAINING - 5 Epochs, 500 Samples (~2 minutes)")
print("=" * 80)

# Baseline
print("\n[1/2] Baseline (no defense)...")
server_baseline = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)
client_baseline = BottomModel().to(DEVICE)
start = time.time()
baseline_results = train_optimized(server_baseline, client_baseline, train_loader, test_loader, False, num_epochs=5)
baseline_time = time.time() - start
print(f"⏱️  Time: {baseline_time:.1f}s")

# Defense
print("\n[2/2] With Defense...")
server_defense = ServerCoordinator(device=DEVICE, enable_defense=True, defense_config=DEFENSE_CONFIG)
client_defense = BottomModel().to(DEVICE)
start = time.time()
defense_results = train_optimized(server_defense, client_defense, train_loader, test_loader, True, num_epochs=5)
defense_time = time.time() - start
print(f"⏱️  Time: {defense_time:.1f}s")

# Detailed Results
print("\n" + "=" * 80)
print("DETAILED RESULTS (5 Epochs, 500 Samples)")
print("=" * 80)

print("\n📊 BASELINE (No Defense):")
for i, (loss, acc) in enumerate(zip(baseline_results['losses'], baseline_results['accuracies'])):
    print(f"  Epoch {i+1}: Loss={loss:.4f}, Acc={acc:.4f}")

print("\n🛡️  WITH DEFENSE:")
for i, (loss, acc) in enumerate(zip(defense_results['losses'], defense_results['accuracies'])):
    print(f"  Epoch {i+1}: Loss={loss:.4f}, Acc={acc:.4f}")

print("\n📈 COMPARISON (Final Epoch):")
baseline_final_loss = baseline_results['losses'][-1]
defense_final_loss = defense_results['losses'][-1]
baseline_final_acc = baseline_results['accuracies'][-1]
defense_final_acc = defense_results['accuracies'][-1]

print(f"  Baseline Loss: {baseline_final_loss:.4f} → Defense Loss: {defense_final_loss:.4f}")
print(f"  Loss change: {(defense_final_loss - baseline_final_loss):+.4f}")
print(f"  Baseline Acc: {baseline_final_acc:.4f} → Defense Acc: {defense_final_acc:.4f}")
print(f"  Acc change: {(defense_final_acc - baseline_final_acc):+.4f}")

print(f"\n⏱️  TIMING:")
print(f"  Baseline: {baseline_time:.1f}s | Defense: {defense_time:.1f}s | Total: {baseline_time + defense_time:.1f}s")

accuracy_loss_pct = abs((defense_final_acc - baseline_final_acc) / baseline_final_acc * 100) if baseline_final_acc > 0 else 0
if accuracy_loss_pct < 5:
    print(f"\n✅ SUCCESS! Accuracy loss < 5% ({accuracy_loss_pct:.1f}%)")
else:
    print(f"\n⚠️  Accuracy loss: {accuracy_loss_pct:.1f}%")

# Save
results = {
    'baseline': {
        'losses': baseline_results['losses'],
        'accuracies': baseline_results['accuracies']
    },
    'defense': {
        'losses': defense_results['losses'],
        'accuracies': defense_results['accuracies']
    },
    'timing': {
        'baseline': baseline_time,
        'defense': defense_time,
        'total': baseline_time + defense_time
    },
    'epochs': 5,
    'samples': 500,
    'summary': {
        'baseline_final_acc': baseline_final_acc,
        'defense_final_acc': defense_final_acc,
        'accuracy_change': defense_final_acc - baseline_final_acc,
        'accuracy_loss_pct': accuracy_loss_pct
    }
}

with open('optimized_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n💾 Results saved to optimized_results.json")
