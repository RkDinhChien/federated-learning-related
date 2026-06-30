#!/usr/bin/env python3
"""
Phase 3 Quick Test - 5 epochs to verify everything works
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import sys

from config import DEVICE, BATCH_SIZE, LEARNING_RATE, EMBEDDING_DIM, NUM_CLASSES
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator
from gradient_defense import GradientDefenseModule, DefenseConfig
from malicious_optimizer import MaliciousSGD

def test_phase3():
    print("\n" + "="*70)
    print("PHASE 3 QUICK TEST (5 epochs)")
    print("="*70 + "\n")
    
    device = DEVICE
    print(f"Device: {device}")
    
    # Load data
    print("\n[*] Loading dataset...")
    train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE)
    print(f"    Train batches: {len(train_loader)}")
    print(f"    Test batches: {len(test_loader)}")
    
    # Create models
    print("\n[*] Creating models...")
    client = ClientWorker(embedding_dim=EMBEDDING_DIM, learning_rate=LEARNING_RATE, device=device)
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM, 
        learning_rate=LEARNING_RATE, 
        device=device,
        enable_defense=False  # No defense for this test
    )
    print("    Client created ✅")
    print("    Server created ✅")
    
    # Training loop
    print("\n[*] Starting training...")
    for epoch in range(5):  # Only 5 epochs
        total_loss = 0.0
        total_correct = 0
        total_samples = 0
        
        client.train_mode()
        server.train_mode()
        
        for batch_idx, (half_A, half_B, labels) in enumerate(train_loader):
            if batch_idx > 10:  # Only process 10 batches per epoch for speed
                break
                
            half_A = half_A.to(device)
            half_B = half_B.to(device)
            labels = labels.to(device)
            
            try:
                # Forward
                o_bao = client.forward(half_B)
                logits = server.forward(half_A, o_bao)
                
                # Loss
                loss = server.criterion(logits, labels)
                
                # Backward
                g_bao = server.compute_gradients_and_update(loss)
                client.backward(g_bao)
                
                # Track
                total_loss += loss.item()
                _, predicted = torch.max(logits, 1)
                total_correct += (predicted == labels).sum().item()
                total_samples += labels.size(0)
                
            except Exception as e:
                print(f"\n❌ Error at batch {batch_idx}: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        avg_loss = total_loss / (batch_idx + 1)
        avg_acc = total_correct / total_samples
        print(f"  Epoch {epoch+1}/5 - Loss: {avg_loss:.4f}, Acc: {avg_acc:.4f}")
    
    print("\n" + "="*70)
    print("✅ QUICK TEST PASSED!")
    print("="*70)
    print("\nPhase 3 is ready to run. Execute:")
    print("  python3 main_phase3.py")
    print("\n")
    
    return True

if __name__ == "__main__":
    success = test_phase3()
    sys.exit(0 if success else 1)
