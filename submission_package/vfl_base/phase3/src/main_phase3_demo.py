#!/usr/bin/env python3
"""
Phase 3: ULTRA-FAST Demo - Shows defense mechanism in 30 seconds
Uses minimal data to demonstrate the concept
"""

import torch
import torch.nn as nn
import json
import time

print("=" * 80)
print("⚡ PHASE 3 DEFENSE DEMO - 30 SECONDS")
print("=" * 80)

# Create synthetic data (no CIFAR-10 needed!)
torch.manual_seed(42)

BATCH_SIZE = 32
NUM_EPOCHS = 3
NUM_BATCHES = 5
EMBEDDING_DIM = 128

print(f"\nSetup: {NUM_EPOCHS} epochs × {NUM_BATCHES} batches = {NUM_EPOCHS * NUM_BATCHES} iterations")

# Simple models
class SimpleClient(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(16*16*3, EMBEDDING_DIM)  # CIFAR-10 half: 16x16x3 pixels
    
    def forward(self, x):
        x = x.view(x.size(0), -1)
        return self.fc(x)

class SimpleServer(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(EMBEDDING_DIM * 2, 64)  # embedding_dim (client) + embedding_dim (server)
        self.fc2 = nn.Linear(64, 10)
    
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        return self.fc2(x)

# Simple Defense
class SimpleDefense:
    def __init__(self):
        self.grad_mean = None
        self.normal_count = 0
        self.defended_count = 0
    
    def apply(self, gradient):
        if self.grad_mean is None:
            self.grad_mean = gradient.clone().detach().mean()
            return gradient
        
        grad_mean = gradient.mean().item()
        diff = abs(grad_mean - self.grad_mean)
        
        if diff > 0.5:  # Anomaly threshold
            # Add noise to defend
            gradient = gradient + torch.randn_like(gradient) * 0.1
            self.defended_count += 1
        else:
            self.normal_count += 1
        
        self.grad_mean = 0.95 * self.grad_mean + 0.05 * grad_mean
        return gradient

# Initialize
client = SimpleClient()
server_baseline = SimpleServer()
server_defense = SimpleServer()
defense = SimpleDefense()

client_optimizer = torch.optim.SGD(client.parameters(), lr=0.01)
server_baseline_opt = torch.optim.SGD(server_baseline.parameters(), lr=0.01)
server_defense_opt = torch.optim.SGD(server_defense.parameters(), lr=0.01)

criterion = nn.CrossEntropyLoss()

def train_model(client, server, server_opt, num_epochs, use_defense=False):
    """Train model on synthetic data"""
    losses = []
    
    for epoch in range(num_epochs):
        epoch_loss = 0
        
        for batch in range(NUM_BATCHES):
            # Create synthetic batch (no real dataset needed)
            x_client = torch.randn(BATCH_SIZE, 3, 16, 16)  # Client half
            x_server = torch.randn(BATCH_SIZE, EMBEDDING_DIM)  # Server half embedding
            y = torch.randint(0, 10, (BATCH_SIZE,))
            
            # Forward
            client_out = client(x_client)
            combined = torch.cat([client_out, x_server], dim=1)
            logits = server(combined)
            loss = criterion(logits, y)
            epoch_loss += loss.item()
            
            # Backward
            server_opt.zero_grad()
            loss.backward()
            
            # Apply defense if enabled
            if use_defense:
                for param in client.parameters():
                    if param.grad is not None:
                        param.grad = defense.apply(param.grad)
            
            server_opt.step()
        
        avg_loss = epoch_loss / NUM_BATCHES
        losses.append(avg_loss)
        print(f"  Epoch {epoch+1}/{num_epochs} | Loss: {avg_loss:.4f}")
    
    return losses

print("\n" + "=" * 80)
print("🔵 BASELINE (No Defense)")
print("=" * 80)
start = time.time()
baseline_losses = train_model(client, server_baseline, server_baseline_opt, NUM_EPOCHS, use_defense=False)
baseline_time = time.time() - start
print(f"⏱️ Time: {baseline_time:.1f}s")

print("\n" + "=" * 80)
print("🛡️ WITH DEFENSE")
print("=" * 80)
defense.normal_count = 0
defense.defended_count = 0
start = time.time()
defense_losses = train_model(client, server_defense, server_defense_opt, NUM_EPOCHS, use_defense=True)
defense_time = time.time() - start
print(f"⏱️ Time: {defense_time:.1f}s")

# Results
print("\n" + "=" * 80)
print("📊 RESULTS")
print("=" * 80)
print(f"\nBaseline Loss: {baseline_losses[-1]:.4f}")
print(f"Defense Loss:  {defense_losses[-1]:.4f}")
print(f"Loss change:   {(defense_losses[-1] - baseline_losses[-1]):+.4f}")

print(f"\nDefense Statistics:")
print(f"  Normal gradients:   {defense.normal_count}")
print(f"  Defended gradients: {defense.defended_count}")

print(f"\nTotal Time: {baseline_time + defense_time:.1f}s")

# Save results
results = {
    'baseline_losses': baseline_losses,
    'defense_losses': defense_losses,
    'timing': {
        'baseline': baseline_time,
        'defense': defense_time,
        'total': baseline_time + defense_time
    },
    'defense_stats': {
        'normal_count': defense.normal_count,
        'defended_count': defense.defended_count
    },
    'epochs': NUM_EPOCHS,
    'batches_per_epoch': NUM_BATCHES
}

with open('demo_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n✅ Results saved to demo_results.json")
print("=" * 80)
