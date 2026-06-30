#!/usr/bin/env python3
"""
Phase 3: Fast test - 1 epoch only (~1 minute)
FLSG Defense System for Vertical Federated Learning
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

# Use only 100 samples for fast testing (~1 minute)
train_subset = Subset(dataset, list(range(min(100, len(dataset)))))
test_subset = Subset(test_dataset, list(range(min(100, len(test_dataset)))))

train_loader = DataLoader(train_subset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_subset, batch_size=BATCH_SIZE)

print(f"Train batches: {len(train_loader)}, Test batches: {len(test_loader)}")

def train_fast(server, client, train_loader, test_loader, enable_defense, num_epochs=1):
    """Fast training with 1 epoch"""
    
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

print("\n🔥 FAST TEST - 1 Epoch, 100 Samples (~1 minute)")
print("=" * 80)

# Baseline
print("\n[1/2] Baseline (no defense)...")
server_baseline = ServerCoordinator(device=DEVICE, enable_defense=False, defense_config=DEFENSE_CONFIG)
client = BottomModel().to(DEVICE)
start = time.time()
baseline_results = train_fast(server_baseline, client, train_loader, test_loader, False)
baseline_time = time.time() - start
print(f"⏱️  Time: {baseline_time:.1f}s")

# Defense
print("\n[2/2] With Defense...")
server_defense = ServerCoordinator(device=DEVICE, enable_defense=True, defense_config=DEFENSE_CONFIG)
client = BottomModel().to(DEVICE)
start = time.time()
defense_results = train_fast(server_defense, client, train_loader, test_loader, True)
defense_time = time.time() - start
print(f"⏱️  Time: {defense_time:.1f}s")

# Results
print("\n" + "=" * 80)
print("RESULTS (1 Epoch, 100 Samples)")
print("=" * 80)
print(f"Baseline Loss: {baseline_results['losses'][0]:.4f} | Accuracy: {baseline_results['accuracies'][0]:.4f}")
print(f"Defense Loss:  {defense_results['losses'][0]:.4f} | Accuracy: {defense_results['accuracies'][0]:.4f}")
print(f"\nLoss change: {(defense_results['losses'][0] - baseline_results['losses'][0]):.4f}")
print(f"Acc change:  {(defense_results['accuracies'][0] - baseline_results['accuracies'][0]):.4f}")
print(f"\nTotal time: {baseline_time + defense_time:.1f}s")

# Save
results = {
    'baseline': baseline_results,
    'defense': defense_results,
    'timing': {'baseline': baseline_time, 'defense': defense_time},
    'epochs': 1,
    'samples': 100
}

with open('fast_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n✅ Results saved to fast_test_results.json")
