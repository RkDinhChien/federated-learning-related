"""
Phase 3: FLSG (Federated Learning with Secure Gradient) Defense System
Main training script for comparative experiments.

Runs two experiments:
1. Baseline: Training with MaliciousSGD attack, WITHOUT defense
2. With Defense: Training with MaliciousSGD attack, WITH FLSG defense

Measures:
- Server accuracy
- Training loss
- Attack Success Rate (ASR) via MixMatch-based inference attack

Expected Results:
- Baseline ASR: ~75% (successful label inference)
- Defense ASR: ~20-30% (strong attack mitigation)
- ASR Reduction: ~70%
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import numpy as np
import json
from datetime import datetime
from pathlib import Path

# Import VFL components
from config import (
    DEVICE, BATCH_SIZE, NUM_EPOCHS_TRAIN, LEARNING_RATE,
    EMBEDDING_DIM, NUM_CLASSES, ATTACK_CONFIG, INFERENCE_CONFIG,
    DEFENSE_CONFIG, ENABLE_DEFENSE, RUN_BASELINE, RUN_WITH_DEFENSE
)
from dataset import get_dataloaders
from client_bao import ClientWorker
from server_chien import ServerCoordinator
from malicious_optimizer import MaliciousSGD
from inference_head import InferenceHead, generate_auxiliary_labels, train_inference_head, calculate_asr


def train_epoch(client, server, train_loader, use_malicious=False, enable_defense=False):
    """
    Train one epoch with VFL.
    
    Args:
        client: ClientWorker instance
        server: ServerCoordinator instance
        train_loader: Training data loader
        use_malicious: Use MaliciousSGD optimizer (True for attack scenario)
        enable_defense: Defense is enabled on server (already configured)
    
    Returns:
        avg_loss: Average loss for the epoch
    """
    client.train_mode()
    server.train_mode()
    
    total_loss = 0.0
    num_batches = 0
    
    for half_A, half_B, labels in train_loader:
        half_A = half_A.to(DEVICE)
        half_B = half_B.to(DEVICE)
        labels = labels.to(DEVICE)
        
        # Forward pass
        o_bao = client.forward(half_B)
        logits = server.forward(half_A, o_bao)
        
        # Compute loss
        loss = server.criterion(logits, labels)
        
        # Backward pass
        g_bao = server.compute_gradients_and_update(loss, return_client_gradient=True)
        
        # Client backward
        if g_bao is not None:
            client.backward(g_bao)
        
        total_loss += loss.item()
        num_batches += 1
    
    avg_loss = total_loss / max(num_batches, 1)
    return avg_loss


def evaluate(client, server, test_loader):
    """
    Evaluate on test set.
    
    Returns:
        accuracy: Top-1 accuracy
    """
    client.eval_mode()
    server.eval_mode()
    
    correct = 0
    total = 0
    
    with torch.no_grad():
        for half_A, half_B, labels in test_loader:
            half_A = half_A.to(DEVICE)
            half_B = half_B.to(DEVICE)
            labels = labels.to(DEVICE)
            
            o_bao = client.forward(half_B)
            logits = server.forward(half_A, o_bao)
            
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    
    accuracy = correct / total * 100.0
    return accuracy


def run_experiment_baseline(train_loader, test_loader):
    """
    Experiment A: Baseline - Attack WITHOUT Defense
    
    Returns:
        results: Dict with training metrics and ASR
    """
    print("\n" + "="*70)
    print("  EXPERIMENT A: BASELINE (MaliciousSGD WITHOUT Defense)")
    print("="*70 + "\n")
    
    # Initialize models
    client = ClientWorker(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=DEVICE
    )
    
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=DEVICE,
        enable_defense=False,  # NO DEFENSE
    )
    
    # Replace client optimizer with MaliciousSGD
    client.optimizer = MaliciousSGD(
        client.model.parameters(),
        lr=ATTACK_CONFIG['lr'],
        beta=ATTACK_CONFIG['beta'],
        gamma=ATTACK_CONFIG['gamma'],
        r_min=ATTACK_CONFIG['r_min'],
        r_max=ATTACK_CONFIG['r_max']
    )
    
    print(f"[Baseline] Client optimizer: MaliciousSGD (β={ATTACK_CONFIG['beta']}, γ={ATTACK_CONFIG['gamma']})")
    print(f"[Baseline] Server defense: DISABLED")
    print(f"[Baseline] Training for {NUM_EPOCHS_TRAIN} epochs...\n")
    
    # Training loop
    train_losses = []
    test_accs = []
    
    for epoch in range(1, NUM_EPOCHS_TRAIN + 1):
        avg_loss = train_epoch(client, server, train_loader, use_malicious=True, enable_defense=False)
        test_acc = evaluate(client, server, test_loader)
        
        train_losses.append(avg_loss)
        test_accs.append(test_acc)
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"[Baseline] Epoch {epoch:2d}/{NUM_EPOCHS_TRAIN} | Loss: {avg_loss:.4f} | Test Acc: {test_acc:.2f}%")
    
    # Run inference attack to measure ASR
    print(f"\n[Baseline] Training complete. Running inference attack...")
    
    # Prepare inference data
    asr = run_inference_attack(client.model, train_loader, test_loader, attack_name="Baseline")
    
    return {
        'experiment': 'Baseline',
        'defense_enabled': False,
        'attack_enabled': True,
        'train_losses': train_losses,
        'test_accuracies': test_accs,
        'final_test_acc': test_accs[-1],
        'final_train_loss': train_losses[-1],
        'asr': asr
    }


def run_experiment_with_defense(train_loader, test_loader):
    """
    Experiment B: With Defense - Attack WITH FLSG Defense
    
    Returns:
        results: Dict with training metrics, defense stats, and ASR
    """
    print("\n" + "="*70)
    print("  EXPERIMENT B: WITH DEFENSE (MaliciousSGD + FLSG Defense)")
    print("="*70 + "\n")
    
    # Initialize models
    client = ClientWorker(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=DEVICE
    )
    
    server = ServerCoordinator(
        embedding_dim=EMBEDDING_DIM,
        learning_rate=LEARNING_RATE,
        device=DEVICE,
        enable_defense=True,  # DEFENSE ENABLED
        defense_config=DEFENSE_CONFIG
    )
    
    # Replace client optimizer with MaliciousSGD
    client.optimizer = MaliciousSGD(
        client.model.parameters(),
        lr=ATTACK_CONFIG['lr'],
        beta=ATTACK_CONFIG['beta'],
        gamma=ATTACK_CONFIG['gamma'],
        r_min=ATTACK_CONFIG['r_min'],
        r_max=ATTACK_CONFIG['r_max']
    )
    
    print(f"[Defense] Client optimizer: MaliciousSGD (β={ATTACK_CONFIG['beta']}, γ={ATTACK_CONFIG['gamma']})")
    print(f"[Defense] Server defense: ENABLED (EMA={DEFENSE_CONFIG.ema_alpha})")
    print(f"[Defense] Anomaly thresholds: low={DEFENSE_CONFIG.anomaly_threshold_low}, high={DEFENSE_CONFIG.anomaly_threshold_high}")
    print(f"[Defense] Noise levels: medium={DEFENSE_CONFIG.noise_sigma_med}, high={DEFENSE_CONFIG.noise_sigma_high}")
    print(f"[Defense] Training for {NUM_EPOCHS_TRAIN} epochs...\n")
    
    # Training loop
    train_losses = []
    test_accs = []
    defense_stats_per_epoch = []
    
    for epoch in range(1, NUM_EPOCHS_TRAIN + 1):
        avg_loss = train_epoch(client, server, train_loader, use_malicious=True, enable_defense=True)
        test_acc = evaluate(client, server, test_loader)
        
        train_losses.append(avg_loss)
        test_accs.append(test_acc)
        
        # Record defense statistics
        if server.enable_defense:
            defense_stats = server.get_defense_statistics()
            defense_stats_per_epoch.append({
                'epoch': epoch,
                'stats': defense_stats
            })
        
        if epoch % 5 == 0 or epoch == 1:
            print(f"[Defense] Epoch {epoch:2d}/{NUM_EPOCHS_TRAIN} | Loss: {avg_loss:.4f} | Test Acc: {test_acc:.2f}%")
    
    # Print final defense statistics
    if server.enable_defense:
        print(f"\n[Defense] Final Defense Statistics:")
        server.print_defense_statistics()
    
    # Run inference attack to measure ASR
    print(f"\n[Defense] Training complete. Running inference attack...")
    asr = run_inference_attack(client.model, train_loader, test_loader, attack_name="With Defense")
    
    return {
        'experiment': 'With Defense',
        'defense_enabled': True,
        'attack_enabled': True,
        'train_losses': train_losses,
        'test_accuracies': test_accs,
        'final_test_acc': test_accs[-1],
        'final_train_loss': train_losses[-1],
        'defense_statistics': defense_stats_per_epoch[-1]['stats'] if defense_stats_per_epoch else None,
        'asr': asr
    }


def run_inference_attack(bottom_model, train_loader, test_loader, attack_name="Attack"):
    """
    Run MixMatch-based inference attack to measure ASR.
    
    Args:
        bottom_model: Client's BottomModel
        train_loader: Training data loader
        test_loader: Test data loader
        attack_name: Name for logging
    
    Returns:
        asr: Attack Success Rate (%)
    """
    print(f"\n[{attack_name}] Preparing inference attack...")
    
    # Use test set as target for inference (U = unlabeled)
    # In real scenario, attacker would see test embeddings without labels
    test_dataset = test_loader.dataset.dataset  # Access underlying dataset
    
    # Generate labeled set from train set (X = labeled)
    X, U = generate_auxiliary_labels(
        test_dataset,
        num_labels=INFERENCE_CONFIG['labeled_samples'],
        seed=42,
        balanced=True
    )
    
    # Create inference head
    inference_head = InferenceHead(
        embedding_dim=EMBEDDING_DIM,
        hidden_dim=512,
        num_classes=NUM_CLASSES,
        dropout_rate=0.4
    )
    
    # Train inference head using MixMatch
    inference_head = train_inference_head(
        bottom_model=bottom_model,
        inference_head=inference_head,
        X=X,
        U=U,
        epochs=INFERENCE_CONFIG['total_epochs'],
        lr=1e-3,
        batch_size=BATCH_SIZE,
        lambda_u=1.0,
        temperature=0.5,
        alpha_mixup=0.75,
        K_augments=2,
        device=DEVICE,
        warmup_epochs=INFERENCE_CONFIG['warmup_epochs']
    )
    
    # Measure ASR on test set
    U_images, U_labels_true = U
    asr = calculate_asr(
        bottom_model=bottom_model,
        inference_head=inference_head,
        U_images=U_images,
        U_labels_true=U_labels_true,
        batch_size=BATCH_SIZE,
        device=DEVICE
    )
    
    return asr


def save_results(baseline_results, defense_results, output_dir="phase3_results"):
    """
    Save experiment results to JSON.
    
    Args:
        baseline_results: Results from baseline experiment
        defense_results: Results from defense experiment
        output_dir: Output directory name
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    # Prepare results summary
    results = {
        'timestamp': datetime.now().isoformat(),
        'configuration': {
            'device': DEVICE,
            'batch_size': BATCH_SIZE,
            'num_epochs': NUM_EPOCHS_TRAIN,
            'learning_rate': LEARNING_RATE,
            'embedding_dim': EMBEDDING_DIM,
        },
        'baseline': baseline_results,
        'with_defense': defense_results,
        'comparison': {
            'asr_reduction_absolute': baseline_results['asr'] - defense_results['asr'],
            'asr_reduction_percentage': (baseline_results['asr'] - defense_results['asr']) / max(baseline_results['asr'], 1) * 100,
            'accuracy_difference': defense_results['final_test_acc'] - baseline_results['final_test_acc'],
        }
    }
    
    # Save full results
    results_file = Path(output_dir) / "phase3_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to {results_file}")
    
    # Print summary
    print("\n" + "="*70)
    print("  PHASE 3 EXPERIMENT SUMMARY")
    print("="*70)
    print(f"\nBaseline (No Defense):")
    print(f"  - Server Test Accuracy: {baseline_results['final_test_acc']:.2f}%")
    print(f"  - Training Loss: {baseline_results['final_train_loss']:.4f}")
    print(f"  - Attack Success Rate (ASR): {baseline_results['asr']:.2f}%")
    
    print(f"\nWith FLSG Defense:")
    print(f"  - Server Test Accuracy: {defense_results['final_test_acc']:.2f}%")
    print(f"  - Training Loss: {defense_results['final_train_loss']:.4f}")
    print(f"  - Attack Success Rate (ASR): {defense_results['asr']:.2f}%")
    
    print(f"\nDefense Effectiveness:")
    print(f"  - ASR Reduction: {results['comparison']['asr_reduction_absolute']:.2f}% absolute")
    print(f"  - ASR Reduction: {results['comparison']['asr_reduction_percentage']:.1f}%")
    print(f"  - Accuracy Trade-off: {results['comparison']['accuracy_difference']:+.2f}%")
    
    print("="*70 + "\n")


def main():
    """Main training script"""
    print("\n" + "="*70)
    print("  PHASE 3: FLSG DEFENSE SYSTEM")
    print("  Federated Learning with Secure Gradient")
    print("="*70)
    
    # Load data
    print(f"\n[Main] Loading CIFAR-10 dataset...")
    train_loader, test_loader = get_dataloaders(batch_size=BATCH_SIZE)
    print(f"[Main] Dataset loaded: {len(train_loader)} train batches, {len(test_loader)} test batches")
    
    results = {}
    
    # Run baseline experiment
    if RUN_BASELINE:
        baseline_results = run_experiment_baseline(train_loader, test_loader)
        results['baseline'] = baseline_results
    else:
        baseline_results = None
        print("\n[Main] Baseline experiment SKIPPED (RUN_BASELINE=False)")
    
    # Run defense experiment
    if RUN_WITH_DEFENSE:
        defense_results = run_experiment_with_defense(train_loader, test_loader)
        results['defense'] = defense_results
    else:
        defense_results = None
        print("\n[Main] Defense experiment SKIPPED (RUN_WITH_DEFENSE=False)")
    
    # Save and display results
    if baseline_results and defense_results:
        save_results(baseline_results, defense_results)
    elif baseline_results:
        print("\n⚠️  Only baseline results available (defense experiment not run)")
    elif defense_results:
        print("\n⚠️  Only defense results available (baseline experiment not run)")
    
    print("\n✅ Phase 3 training complete!")


if __name__ == "__main__":
    main()
