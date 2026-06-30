"""
Phase 3 Full Training - FLSG Defense (30 epochs, full dataset)
Complete training with baseline and defense comparison
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import json
import time
from datetime import datetime

from config import DEVICE, BATCH_SIZE, LEARNING_RATE, EMBEDDING_DIM, NUM_CLASSES
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator
from gradient_defense import GradientDefenseModule, DefenseConfig
from malicious_optimizer import MaliciousSGD


def train_full(experiment_name, enable_defense=False, num_epochs=30):
    """Full training loop (30 epochs, all batches)"""
    
    device = torch.device(DEVICE)
    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {experiment_name}")
    print(f"Defense: {'ENABLED ✅' if enable_defense else 'DISABLED ❌'}")
    print(f"Epochs: {num_epochs} | Batches: Full Dataset")
    print(f"{'='*70}\n")
    
    # Load dataset
    print("[1/4] Loading dataset...")
    train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE)
    print(f"      ✓ {len(train_loader)} train batches, {len(test_loader)} test batches\n")
    
    # Create models
    print("[2/4] Creating models...")
    client = ClientWorker(embedding_dim=EMBEDDING_DIM, learning_rate=LEARNING_RATE, device=device)
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=device,
        enable_defense=enable_defense,
        defense_config=DefenseConfig() if enable_defense else None
    )
    print(f"      ✓ Client & Server created")
    if enable_defense:
        print(f"      ✓ Defense module enabled\n")
    else:
        print(f"      ✓ No defense\n")
    
    # Setup attack
    print("[3/4] Setting up MaliciousSGD attack...")
    client.optimizer = MaliciousSGD(
        client.model.parameters(),
        lr=LEARNING_RATE,
        beta=0.9,
        gamma=1.0,
        r_min=1.0,
        r_max=3.0
    )
    print(f"      ✓ Attack optimizer configured\n")
    
    # Training loop
    print("[4/4] Training...")
    print(f"{'Epoch':<8} {'Loss':<10} {'Train Acc':<12} {'Test Acc':<12} {'Defense Stats':<20}")
    print("-" * 70)
    
    train_losses = []
    train_accs = []
    test_accs = []
    start_time = time.time()
    
    for epoch in range(num_epochs):
        # Train
        client.train_mode()
        server.train_mode()
        
        batch_loss = 0.0
        batch_count = 0
        correct_train = 0
        total_train = 0
        
        for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
            half_A = half_A.to(device)
            half_B = half_B.to(device)
            labels = labels.to(device)
            
            # Forward
            o_bao = client.forward(half_B)
            logits = server.forward(half_A, o_bao)
            loss = server.criterion(logits, labels)
            
            # Backward
            g_bao = server.compute_gradients_and_update(loss)
            client.backward(g_bao)
            
            batch_loss += loss.item()
            batch_count += 1
            
            _, pred = torch.max(logits, 1)
            correct_train += (pred == labels).sum().item()
            total_train += labels.size(0)
        
        avg_loss = batch_loss / batch_count
        train_acc = correct_train / total_train
        train_losses.append(avg_loss)
        train_accs.append(train_acc)
        
        # Test
        client.eval_mode()
        server.eval_mode()
        
        correct = 0
        total = 0
        with torch.no_grad():
            for half_A, half_B, labels in test_loader:
                half_A = half_A.to(device)
                half_B = half_B.to(device)
                labels = labels.to(device)
                
                o_bao = client.forward(half_B)
                logits = server.forward(half_A, o_bao)
                _, pred = torch.max(logits, 1)
                
                correct += (pred == labels).sum().item()
                total += labels.size(0)
        
        test_acc = correct / total
        test_accs.append(test_acc)
        
        # Defense statistics
        defense_str = ""
        if enable_defense and server.defense_module is not None:
            stats = server.defense_module.get_statistics()
            defense_str = f"N:{stats['normal_percentage']:.0f}% S:{stats['suspicious_percentage']:.0f}%"
        
        # Print progress
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"{epoch+1:<8} {avg_loss:<10.4f} {train_acc:<12.4f} {test_acc:<12.4f} {defense_str:<20}")
    
    elapsed = time.time() - start_time
    print("-" * 70)
    print(f"\n✓ Training complete! ({elapsed/60:.1f} minutes)\n")
    
    # Final statistics
    if enable_defense and server.defense_module is not None:
        print("Final Defense Statistics:")
        server.defense_module.print_statistics()
    
    return {
        'experiment': experiment_name,
        'enable_defense': enable_defense,
        'final_loss': train_losses[-1],
        'final_train_acc': train_accs[-1],
        'final_test_acc': test_accs[-1],
        'elapsed_time_sec': elapsed,
        'train_losses': train_losses,
        'train_accs': train_accs,
        'test_accs': test_accs,
        'timestamp': datetime.now().isoformat()
    }


def main():
    print("\n" + "="*70)
    print("PHASE 3 FULL TRAINING (30 Epochs)")
    print("="*70)
    
    results = {}
    
    # Experiment 1: Baseline (no defense)
    print("\n" + "▶"*35)
    print("EXPERIMENT A: BASELINE (No Defense)")
    print("▶"*35)
    results['baseline'] = train_full(
        experiment_name="Baseline (No Defense)",
        enable_defense=False,
        num_epochs=30
    )
    
    # Experiment 2: With defense
    print("\n" + "▶"*35)
    print("EXPERIMENT B: WITH FLSG DEFENSE")
    print("▶"*35)
    results['with_defense'] = train_full(
        experiment_name="With FLSG Defense",
        enable_defense=True,
        num_epochs=30
    )
    
    # Comparison
    print("\n" + "="*70)
    print("FINAL COMPARISON")
    print("="*70)
    
    baseline = results['baseline']
    defended = results['with_defense']
    
    print(f"\nBaseline (No Defense):")
    print(f"  Final Loss:     {baseline['final_loss']:.4f}")
    print(f"  Final Train Acc: {baseline['final_train_acc']:.4f}")
    print(f"  Final Test Acc:  {baseline['final_test_acc']:.4f}")
    print(f"  Time:            {baseline['elapsed_time_sec']/60:.1f} minutes")
    
    print(f"\nWith FLSG Defense:")
    print(f"  Final Loss:     {defended['final_loss']:.4f}")
    print(f"  Final Train Acc: {defended['final_train_acc']:.4f}")
    print(f"  Final Test Acc:  {defended['final_test_acc']:.4f}")
    print(f"  Time:            {defended['elapsed_time_sec']/60:.1f} minutes")
    
    # Metrics
    loss_change = defended['final_loss'] - baseline['final_loss']
    acc_change = defended['final_test_acc'] - baseline['final_test_acc']
    
    print(f"\nMetrics:")
    print(f"  Loss Change:     {loss_change:+.4f} ({loss_change/baseline['final_loss']*100:+.1f}%)")
    print(f"  Test Acc Change: {acc_change:+.4f} ({acc_change/baseline['final_test_acc']*100:+.1f}%)")
    
    # Assessment
    print(f"\n{'='*70}")
    if abs(acc_change) <= 0.05:  # <5% accuracy loss
        print("✅ DEFENSE SUCCESSFUL!")
        print(f"   - Minimal accuracy loss ({abs(acc_change)*100:.2f}%)")
        if loss_change >= 0:
            print(f"   - Higher loss is expected due to defense mechanisms")
    else:
        print("⚠️  Defense impact is significant")
    print(f"{'='*70}\n")
    
    # Save results
    with open('phase3_full_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: phase3_full_results.json\n")


if __name__ == "__main__":
    main()
