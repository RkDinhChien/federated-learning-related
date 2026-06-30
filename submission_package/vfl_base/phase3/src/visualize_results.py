#!/usr/bin/env python3
"""
Visualization script for Phase 3 FLSG Defense training results
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load results
results_path = Path(__file__).parent / "full_training_results_flsg.json"

with open(results_path) as f:
    data = json.load(f)

# Extract data
epochs = list(range(1, len(data['baseline']['test_acc']) + 1))
baseline_acc = data['baseline']['test_acc']
defense_acc = data['defense']['test_acc']
baseline_loss = data['baseline']['test_loss']
defense_loss = data['defense']['test_loss']

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Accuracy Comparison
ax1.plot(epochs, baseline_acc, 'b-o', label='Baseline', linewidth=2, markersize=4, alpha=0.7)
ax1.plot(epochs, defense_acc, 'r-s', label='FLSG Defense', linewidth=2, markersize=4, alpha=0.7)
ax1.set_xlabel('Epoch', fontsize=12, fontweight='bold')
ax1.set_ylabel('Test Accuracy', fontsize=12, fontweight='bold')
ax1.set_title('Phase 3: Accuracy Comparison\n(Baseline vs FLSG Defense)', fontsize=13, fontweight='bold')
ax1.legend(fontsize=11, loc='best')
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0.08, 0.12])

# Plot 2: Loss Comparison
ax2.plot(epochs, baseline_loss, 'b-o', label='Baseline', linewidth=2, markersize=4, alpha=0.7)
ax2.plot(epochs, defense_loss, 'r-s', label='FLSG Defense', linewidth=2, markersize=4, alpha=0.7)
ax2.set_xlabel('Epoch', fontsize=12, fontweight='bold')
ax2.set_ylabel('Test Loss', fontsize=12, fontweight='bold')
ax2.set_title('Phase 3: Loss Comparison\n(Baseline vs FLSG Defense)', fontsize=13, fontweight='bold')
ax2.legend(fontsize=11, loc='best')
ax2.grid(True, alpha=0.3)

plt.tight_layout()

# Save figure
output_path = Path(__file__).parent / "flsg_defense_results.png"
plt.savefig(output_path, dpi=150, bbox_inches='tight')
print(f"✅ Visualization saved to: {output_path}")

# Print summary statistics
print()
print("="*80)
print("📊 TRAINING RESULTS SUMMARY")
print("="*80)
print()
print("ACCURACY METRICS")
print("-" * 80)
print(f"Epoch  1 - Baseline: {baseline_acc[0]:.4f}  | Defense: {defense_acc[0]:.4f}  | Diff: {baseline_acc[0]-defense_acc[0]:+.4f}")
print(f"Epoch 10 - Baseline: {baseline_acc[9]:.4f}  | Defense: {defense_acc[9]:.4f}  | Diff: {baseline_acc[9]-defense_acc[9]:+.4f}")
print(f"Epoch 20 - Baseline: {baseline_acc[19]:.4f}  | Defense: {defense_acc[19]:.4f}  | Diff: {baseline_acc[19]-defense_acc[19]:+.4f}")
print(f"Epoch 30 - Baseline: {baseline_acc[29]:.4f}  | Defense: {defense_acc[29]:.4f}  | Diff: {baseline_acc[29]-defense_acc[29]:+.4f}")
print()

print("LOSS METRICS")
print("-" * 80)
print(f"Epoch  1 - Baseline: {baseline_loss[0]:.6f} | Defense: {defense_loss[0]:.6f}")
print(f"Epoch 10 - Baseline: {baseline_loss[9]:.6f} | Defense: {defense_loss[9]:.6f}")
print(f"Epoch 20 - Baseline: {baseline_loss[19]:.6f} | Defense: {defense_loss[19]:.6f}")
print(f"Epoch 30 - Baseline: {baseline_loss[29]:.6f} | Defense: {defense_loss[29]:.6f}")
print()

print("STATISTICS")
print("-" * 80)
baseline_acc_mean = np.mean(baseline_acc)
defense_acc_mean = np.mean(defense_acc)
baseline_acc_std = np.std(baseline_acc)
defense_acc_std = np.std(defense_acc)

print(f"Baseline Accuracy - Mean: {baseline_acc_mean:.4f} ± {baseline_acc_std:.4f}")
print(f"Defense  Accuracy - Mean: {defense_acc_mean:.4f} ± {defense_acc_std:.4f}")
print(f"Average Difference:       {baseline_acc_mean - defense_acc_mean:+.4f}")
print()

total_hours = data['timing']['total_hours']
print(f"⏱️  Total Training Time: {total_hours:.3f} hours (~{int(total_hours*60)} minutes)")
print("="*80)

