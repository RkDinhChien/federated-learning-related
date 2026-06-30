"""
Phase 3 Quick Test - FLSG Defense (2-3 minutes)
Runs only 3 epochs to verify everything works
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import json
from datetime import datetime

from config import DEVICE, BATCH_SIZE, LEARNING_RATE, EMBEDDING_DIM, NUM_CLASSES
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator
from gradient_defense import GradientDefenseModule, DefenseConfig
from malicious_optimizer import MaliciousSGD


def train_quick(enable_defense=False, num_epochs=3):
    """Quick training loop (3 epochs)"""
    
    device = torch.device(DEVICE)
    print(f"\n{'='*70}")
    print(f"Quick Test {'WITH' if enable_defense else 'WITHOUT'} Defense - {num_epochs} Epochs")
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
    print(f"      ✓ Client & Server created\n")
    
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
    print("[4/4] Training...\n")
    train_losses = []
    test_accs = []
    defense_active = False
    
    for epoch in range(num_epochs):
        # Train
        client.train_mode()
        server.train_mode()
        
        batch_loss = 0.0
        batch_count = 0
        
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
            if enable_defense and server.defense_module is not None:
                defense_active = True
            client.backward(g_bao)
            
            batch_loss += loss.item()
            batch_count += 1
            
            # Only train on first 5 batches for quick test
            if batch_count >= 5:
                break
        
        avg_loss = batch_loss / batch_count
        train_losses.append(avg_loss)
        
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
                
                # Only test on first 2 batches for quick test
                if total >= 256:
                    break
        
        test_acc = correct / total
        test_accs.append(test_acc)
        
        defense_str = ""
        if enable_defense and server.defense_module is not None:
            stats = server.defense_module.get_statistics()
            defense_str = f" | Normal: {stats['normal_percentage']:.1f}%, Suspicious: {stats['suspicious_percentage']:.1f}%, Rejected: {stats['rejected_percentage']:.1f}%"
        
        print(f"Epoch {epoch+1}/{num_epochs} | Loss: {avg_loss:.4f} | Test Acc: {test_acc:.4f}{defense_str}")
    
    print(f"\n✓ Training complete!\n")
    
    return {
        'enable_defense': enable_defense,
        'final_loss': train_losses[-1],
        'final_test_acc': test_accs[-1],
        'defense_active': defense_active,
        'timestamp': datetime.now().isoformat()
    }


def main():
    print("\n" + "="*70)
    print("PHASE 3 QUICK TEST (2-3 minutes)")
    print("="*70)
    
    # Test without defense
    print("\n[TEST 1] Running WITHOUT Defense...")
    results_no_defense = train_quick(enable_defense=False, num_epochs=3)
    
    # Test with defense
    print("\n[TEST 2] Running WITH Defense...")
    results_with_defense = train_quick(enable_defense=True, num_epochs=3)
    
    # Results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nWithout Defense:")
    print(f"  Final Loss: {results_no_defense['final_loss']:.4f}")
    print(f"  Test Acc:   {results_no_defense['final_test_acc']:.4f}")
    
    print(f"\nWith FLSG Defense:")
    print(f"  Final Loss: {results_with_defense['final_loss']:.4f}")
    print(f"  Test Acc:   {results_with_defense['final_test_acc']:.4f}")
    print(f"  Defense Active: {results_with_defense['defense_active']}")
    
    acc_diff = results_with_defense['final_test_acc'] - results_no_defense['final_test_acc']
    loss_diff = results_with_defense['final_loss'] - results_no_defense['final_loss']
    
    print(f"\nDifference:")
    print(f"  Accuracy: {acc_diff:+.4f}")
    print(f"  Loss: {loss_diff:+.4f}")
    
    # Save results
    results = {
        'test_type': 'quick_test_3_epochs',
        'without_defense': results_no_defense,
        'with_defense': results_with_defense,
        'timestamp': datetime.now().isoformat()
    }
    
    with open('quick_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to quick_test_results.json")
    print("\n" + "="*70)
    print("✅ QUICK TEST COMPLETE!")
    print("="*70 + "\n")
    
    return results


if __name__ == "__main__":
    main()
