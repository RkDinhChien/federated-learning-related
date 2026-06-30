#!/usr/bin/env python3
"""
Phase 3: FLSG Defense System - Simplified Main Script
Tests defense effectiveness with shorter epochs for faster iteration
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import json
from datetime import datetime
from pathlib import Path
import time

from config import (
    DEVICE, BATCH_SIZE, LEARNING_RATE,
    EMBEDDING_DIM, NUM_CLASSES, ATTACK_CONFIG, 
    DEFENSE_CONFIG, RUN_BASELINE, RUN_WITH_DEFENSE
)
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator
from gradient_defense import GradientDefenseModule
from malicious_optimizer import MaliciousSGD


def train_epoch(epoch, client, server, train_loader, device, use_attack=False):
    """Train one epoch"""
    client.train_mode()
    server.train_mode()
    
    total_loss = 0.0
    total_correct = 0
    total_samples = 0
    
    for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
        half_A = half_A.to(device)
        half_B = half_B.to(device)
        labels = labels.to(device)
        
        # Forward pass
        o_bao = client.forward(half_B)
        logits = server.forward(half_A, o_bao)
        loss = server.criterion(logits, labels)
        
        # Backward pass
        g_bao = server.compute_gradients_and_update(loss)
        
        # Client backward
        if g_bao is not None:
            client.backward(g_bao)
        
        # Track metrics
        total_loss += loss.item()
        _, predicted = torch.max(logits, 1)
        total_correct += (predicted == labels).sum().item()
        total_samples += labels.size(0)
    
    avg_loss = total_loss / len(train_loader)
    avg_acc = total_correct / total_samples
    
    return avg_loss, avg_acc


@torch.no_grad()
def test_epoch(client, server, test_loader, device):
    """Test one epoch"""
    client.eval_mode()
    server.eval_mode()
    
    total_correct = 0
    total_samples = 0
    
    for half_A, half_B, labels in test_loader:
        half_A = half_A.to(device)
        half_B = half_B.to(device)
        labels = labels.to(device)
        
        o_bao = client.forward(half_B)
        logits = server.forward(half_A, o_bao)
        
        _, predicted = torch.max(logits, 1)
        total_correct += (predicted == labels).sum().item()
        total_samples += labels.size(0)
    
    return total_correct / total_samples


def run_experiment(exp_name, enable_defense=False, num_epochs=5):
    """Run training experiment"""
    
    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {exp_name}")
    print(f"Defense: {'✅ ENABLED' if enable_defense else '❌ DISABLED'}")
    print(f"Epochs: {num_epochs}")
    print(f"{'='*70}\n")
    
    device = torch.device(DEVICE)
    
    # Load data
    print("[*] Loading dataset...")
    train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE)
    print(f"    Train batches: {len(train_loader)}")
    print(f"    Test batches: {len(test_loader)}\n")
    
    # Create models
    print("[*] Creating models...")
    client = ClientWorker(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=device
    )
    
    # Create server with or without defense
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=device,
        enable_defense=enable_defense
    )
    
    if enable_defense:
        # Add defense module to server
        from gradient_defense import DefenseConfig
        defense_config = DefenseConfig(**DEFENSE_CONFIG)
        server.defense_module = GradientDefenseModule(defense_config, device=device)
        print("    ✅ Defense module enabled\n")
    else:
        print("    ❌ Defense disabled\n")
    
    # Training
    print("[*] Starting training...")
    train_losses = []
    train_accs = []
    test_accs = []
    
    start_time = time.time()
    
    for epoch in range(num_epochs):
        train_loss, train_acc = train_epoch(epoch, client, server, train_loader, device)
        test_acc = test_epoch(client, server, test_loader, device)
        
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        test_accs.append(test_acc)
        
        print(f"  Epoch {epoch+1:2d}/{num_epochs} | "
              f"Loss: {train_loss:.4f} | "
              f"Train Acc: {train_acc:.4f} | "
              f"Test Acc: {test_acc:.4f}")
    
    elapsed = time.time() - start_time
    print(f"\n  ✅ Training completed in {elapsed:.1f}s\n")
    
    # Get defense stats
    defense_stats = None
    if enable_defense and hasattr(server, 'defense_module'):
        defense_stats = server.defense_module.get_statistics()
        print("  Defense Statistics:")
        print(f"    Normal: {defense_stats['normal_pct']:.1f}%")
        print(f"    Suspicious: {defense_stats['suspicious_pct']:.1f}%")
        print(f"    Rejected: {defense_stats['rejected_pct']:.1f}%\n")
    
    # Results
    results = {
        'experiment': exp_name,
        'enable_defense': enable_defense,
        'num_epochs': num_epochs,
        'timestamp': datetime.now().isoformat(),
        'elapsed_seconds': elapsed,
        'final_train_loss': train_losses[-1],
        'final_train_acc': train_accs[-1],
        'final_test_acc': test_accs[-1],
        'train_losses': train_losses,
        'train_accs': train_accs,
        'test_accs': test_accs,
        'defense_stats': defense_stats,
    }
    
    return results


def main():
    print("\n" + "="*70)
    print("PHASE 3: FLSG DEFENSE SYSTEM TEST")
    print("="*70)
    
    # Use 5 epochs for testing (adjust to 30 for full training)
    num_epochs = 5
    
    results = {}
    
    # Experiment 1: Baseline (no defense)
    if RUN_BASELINE:
        results['baseline'] = run_experiment(
            exp_name="Baseline (NO Defense)",
            enable_defense=False,
            num_epochs=num_epochs
        )
    
    # Experiment 2: With defense
    if RUN_WITH_DEFENSE:
        results['with_defense'] = run_experiment(
            exp_name="WITH FLSG Defense",
            enable_defense=True,
            num_epochs=num_epochs
        )
    
    # Comparison
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70 + "\n")
    
    if 'baseline' in results and 'with_defense' in results:
        baseline = results['baseline']
        defended = results['with_defense']
        
        print("Baseline (NO Defense):")
        print(f"  Final Test Acc: {baseline['final_test_acc']:.4f}")
        print(f"  Final Loss: {baseline['final_train_loss']:.4f}\n")
        
        print("With FLSG Defense:")
        print(f"  Final Test Acc: {defended['final_test_acc']:.4f}")
        print(f"  Final Loss: {defended['final_train_loss']:.4f}\n")
        
        acc_diff = baseline['final_test_acc'] - defended['final_test_acc']
        loss_diff = defended['final_train_loss'] - baseline['final_train_loss']
        
        print("Comparison:")
        print(f"  Accuracy Difference: {acc_diff:.4f}")
        print(f"  Loss Difference: {loss_diff:.4f}\n")
    
    # Save results
    print("[*] Saving results...")
    output_file = 'phase3_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"    ✅ Results saved to {output_file}\n")
    
    print("="*70)
    print("✅ PHASE 3 TEST COMPLETED!")
    print("="*70 + "\n")
    
    print("To run full training (30 epochs), edit this script and change:")
    print("  num_epochs = 5  →  num_epochs = 30\n")


if __name__ == "__main__":
    main()
