"""
Phase 3 Evaluation Script
Analyze and compare results from baseline and defense experiments.

Generates:
- Comparative metrics (ASR reduction, accuracy trade-off)
- Defense effectiveness analysis
- Performance reports
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def load_results(results_file="phase3_results/phase3_results.json"):
    """
    Load Phase 3 results from JSON file.
    
    Args:
        results_file: Path to results JSON file
    
    Returns:
        results: Parsed results dictionary
    """
    with open(results_file, 'r') as f:
        results = json.load(f)
    return results


def compute_metrics(results):
    """
    Compute evaluation metrics from results.
    
    Args:
        results: Results dictionary from main_phase3.py
    
    Returns:
        metrics: Dictionary of computed metrics
    """
    baseline = results['baseline']
    defense = results['with_defense']
    
    metrics = {
        'baseline_asr': baseline['asr'],
        'defense_asr': defense['asr'],
        'asr_reduction_absolute': baseline['asr'] - defense['asr'],
        'asr_reduction_percentage': (baseline['asr'] - defense['asr']) / max(baseline['asr'], 1) * 100,
        
        'baseline_accuracy': baseline['final_test_acc'],
        'defense_accuracy': defense['final_test_acc'],
        'accuracy_difference': defense['final_test_acc'] - baseline['final_test_acc'],
        
        'baseline_loss': baseline['final_train_loss'],
        'defense_loss': defense['final_train_loss'],
        'loss_difference': defense['final_train_loss'] - baseline['final_train_loss'],
        
        'defense_overhead_pct': (defense['final_train_loss'] / max(baseline['final_train_loss'], 1e-6) - 1) * 100,
    }
    
    return metrics


def analyze_defense_effectiveness(metrics):
    """
    Analyze defense effectiveness based on metrics.
    
    Args:
        metrics: Computed metrics dictionary
    
    Returns:
        analysis: String analysis report
    """
    analysis = []
    analysis.append("\n" + "="*70)
    analysis.append("  DEFENSE EFFECTIVENESS ANALYSIS")
    analysis.append("="*70 + "\n")
    
    # ASR Reduction Analysis
    asr_reduction = metrics['asr_reduction_percentage']
    analysis.append(f"1. ATTACK MITIGATION (ASR Reduction)")
    analysis.append(f"   - Baseline ASR: {metrics['baseline_asr']:.2f}%")
    analysis.append(f"   - Defense ASR: {metrics['defense_asr']:.2f}%")
    analysis.append(f"   - Absolute reduction: {metrics['asr_reduction_absolute']:.2f}%")
    analysis.append(f"   - Relative reduction: {asr_reduction:.1f}%")
    
    if asr_reduction >= 70:
        analysis.append(f"   ✅ STRONG defense (>70% ASR reduction)")
    elif asr_reduction >= 50:
        analysis.append(f"   ✓ GOOD defense (50-70% ASR reduction)")
    elif asr_reduction >= 20:
        analysis.append(f"   ⚠️  MODERATE defense (20-50% ASR reduction)")
    else:
        analysis.append(f"   ❌ WEAK defense (<20% ASR reduction)")
    
    # Accuracy Trade-off Analysis
    analysis.append(f"\n2. ACCURACY TRADE-OFF")
    analysis.append(f"   - Baseline accuracy: {metrics['baseline_accuracy']:.2f}%")
    analysis.append(f"   - Defense accuracy: {metrics['defense_accuracy']:.2f}%")
    analysis.append(f"   - Accuracy change: {metrics['accuracy_difference']:+.2f}%")
    
    if abs(metrics['accuracy_difference']) <= 5:
        analysis.append(f"   ✅ Minimal accuracy loss (<5%)")
    elif abs(metrics['accuracy_difference']) <= 10:
        analysis.append(f"   ✓ Acceptable accuracy loss (5-10%)")
    else:
        analysis.append(f"   ⚠️  Significant accuracy loss (>10%)")
    
    # Convergence Analysis
    analysis.append(f"\n3. CONVERGENCE ANALYSIS")
    analysis.append(f"   - Baseline final loss: {metrics['baseline_loss']:.4f}")
    analysis.append(f"   - Defense final loss: {metrics['defense_loss']:.4f}")
    analysis.append(f"   - Loss overhead: {metrics['defense_overhead_pct']:+.2f}%")
    
    if metrics['defense_overhead_pct'] <= 20:
        analysis.append(f"   ✅ Minimal convergence overhead (<20%)")
    else:
        analysis.append(f"   ⚠️  Significant convergence overhead (>20%)")
    
    # Overall Assessment
    analysis.append(f"\n4. OVERALL ASSESSMENT")
    
    # Score calculation
    asr_score = min(100, (asr_reduction / 70) * 100)  # Score based on 70% target
    acc_score = 100 if abs(metrics['accuracy_difference']) <= 5 else max(0, 100 - abs(metrics['accuracy_difference']) * 10)
    loss_score = 100 if metrics['defense_overhead_pct'] <= 20 else max(0, 100 - metrics['defense_overhead_pct'])
    
    overall_score = (asr_score * 0.5 + acc_score * 0.3 + loss_score * 0.2)
    
    analysis.append(f"   - Attack Mitigation Score: {asr_score:.1f}/100")
    analysis.append(f"   - Accuracy Preservation Score: {acc_score:.1f}/100")
    analysis.append(f"   - Convergence Score: {loss_score:.1f}/100")
    analysis.append(f"   - Overall Score: {overall_score:.1f}/100")
    
    if overall_score >= 80:
        analysis.append(f"\n   🏆 EXCELLENT defense performance")
    elif overall_score >= 70:
        analysis.append(f"\n   ✓ GOOD defense performance")
    elif overall_score >= 50:
        analysis.append(f"\n   ⚠️  ACCEPTABLE defense performance")
    else:
        analysis.append(f"\n   ❌ POOR defense performance - review parameters")
    
    analysis.append("\n" + "="*70 + "\n")
    
    return "\n".join(analysis)


def generate_report(results, output_file="phase3_results/evaluation_report.txt"):
    """
    Generate comprehensive evaluation report.
    
    Args:
        results: Results dictionary
        output_file: Output file path
    """
    report = []
    
    # Header
    report.append("="*70)
    report.append("  PHASE 3: FLSG DEFENSE SYSTEM - EVALUATION REPORT")
    report.append("="*70)
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Configuration
    config = results['configuration']
    report.append("CONFIGURATION")
    report.append("-" * 70)
    report.append(f"Device: {config['device']}")
    report.append(f"Batch Size: {config['batch_size']}")
    report.append(f"Training Epochs: {config['num_epochs']}")
    report.append(f"Learning Rate: {config['learning_rate']}")
    report.append(f"Embedding Dimension: {config['embedding_dim']}\n")
    
    # Compute metrics
    metrics = compute_metrics(results)
    
    # Results Summary
    report.append("RESULTS SUMMARY")
    report.append("-" * 70)
    
    report.append("\n[Baseline - No Defense]")
    report.append(f"  Server Test Accuracy: {metrics['baseline_accuracy']:.2f}%")
    report.append(f"  Training Loss: {metrics['baseline_loss']:.4f}")
    report.append(f"  Attack Success Rate (ASR): {metrics['baseline_asr']:.2f}%")
    
    report.append("\n[With FLSG Defense]")
    report.append(f"  Server Test Accuracy: {metrics['defense_accuracy']:.2f}%")
    report.append(f"  Training Loss: {metrics['defense_loss']:.4f}")
    report.append(f"  Attack Success Rate (ASR): {metrics['defense_asr']:.2f}%")
    
    report.append("\n[Comparison]")
    report.append(f"  ASR Reduction: {metrics['asr_reduction_absolute']:.2f}% absolute ({metrics['asr_reduction_percentage']:.1f}% relative)")
    report.append(f"  Accuracy Trade-off: {metrics['accuracy_difference']:+.2f}%")
    report.append(f"  Convergence Overhead: {metrics['defense_overhead_pct']:+.2f}%\n")
    
    # Add analysis
    report.append(analyze_defense_effectiveness(metrics))
    
    # Defense Statistics (if available)
    if results['with_defense'].get('defense_statistics'):
        report.append("\nDEFENSE STATISTICS (Final Epoch)")
    report.append("-" * 70)
    defense_stats = results['with_defense'].get('defense_statistics')
    if defense_stats:
        report.append(f"Normal Gradients: {defense_stats['normal_count']} ({defense_stats['normal_pct']:.1f}%)")
        report.append(f"Suspicious Gradients: {defense_stats['suspicious_count']} ({defense_stats['suspicious_pct']:.1f}%)")
        report.append(f"Rejected Gradients: {defense_stats['rejected_count']} ({defense_stats['rejected_pct']:.1f}%)")
        report.append(f"Total Anomalies Detected: {defense_stats['anomaly_count']} ({defense_stats.get('anomaly_pct', 0):.1f}%)\n")
    
    # Conclusions
    report.append("CONCLUSIONS")
    report.append("-" * 70)
    
    if metrics['asr_reduction_percentage'] >= 70:
        report.append("✅ Defense successfully mitigates the MaliciousSGD attack with")
        report.append("   significant ASR reduction (>70%)")
    elif metrics['asr_reduction_percentage'] >= 50:
        report.append("✓ Defense provides meaningful protection against the attack")
    else:
        report.append("⚠️  Defense effectiveness is limited - consider parameter tuning")
    
    if abs(metrics['accuracy_difference']) <= 5:
        report.append("✅ Negligible impact on model accuracy")
    else:
        report.append(f"⚠️  Noticeable accuracy trade-off ({abs(metrics['accuracy_difference']):.2f}%)")
    
    report.append("\nRECOMMENDATIONS")
    report.append("-" * 70)
    if metrics['asr_reduction_percentage'] < 50:
        report.append("1. Increase EMA smoothing factor to better track gradient evolution")
        report.append("2. Adjust anomaly detection thresholds (lower for more sensitivity)")
        report.append("3. Increase noise injection levels for suspicious gradients")
    if abs(metrics['accuracy_difference']) > 10:
        report.append("1. Reduce noise injection levels to minimize accuracy impact")
        report.append("2. Use more selective defense (higher anomaly thresholds)")
        report.append("3. Increase training epochs to compensate for accuracy loss")
    
    report.append("\n" + "="*70 + "\n")
    
    # Save report
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write("\n".join(report))
    
    print("\n".join(report))
    print(f"✅ Report saved to {output_file}")


def plot_training_curves(results, output_dir="phase3_results"):
    """
    Plot training curves for comparison.
    
    Args:
        results: Results dictionary
        output_dir: Output directory
    """
    if plt is None:
        print("⚠️  matplotlib not installed - skipping visualization")
        return
    
    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # Training loss
        baseline_losses = results['baseline']['train_losses']
        defense_losses = results['with_defense']['train_losses']
        
        axes[0].plot(baseline_losses, label='Baseline (No Defense)', linewidth=2)
        axes[0].plot(defense_losses, label='With FLSG Defense', linewidth=2)
        axes[0].set_xlabel('Epoch')
        axes[0].set_ylabel('Training Loss')
        axes[0].set_title('Training Loss Comparison')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Test accuracy
        baseline_accs = results['baseline']['test_accuracies']
        defense_accs = results['with_defense']['test_accuracies']
        
        axes[1].plot(baseline_accs, label='Baseline (No Defense)', linewidth=2)
        axes[1].plot(defense_accs, label='With FLSG Defense', linewidth=2)
        axes[1].set_xlabel('Epoch')
        axes[1].set_ylabel('Test Accuracy (%)')
        axes[1].set_title('Test Accuracy Comparison')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = Path(output_dir) / "training_curves.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"✅ Training curves saved to {plot_file}")
        
    except Exception as e:
        print(f"⚠️  Could not generate plots: {e}")


def main():
    """Main evaluation script"""
    print("\n" + "="*70)
    print("  PHASE 3 EVALUATION SCRIPT")
    print("="*70 + "\n")
    
    # Load results
    results_file = "phase3_results/phase3_results.json"
    try:
        results = load_results(results_file)
        print(f"✅ Loaded results from {results_file}\n")
    except FileNotFoundError:
        print(f"❌ Results file not found: {results_file}")
        print("Please run main_phase3.py first to generate results.")
        return
    
    # Generate evaluation report
    generate_report(results)
    
    # Plot training curves
    plot_training_curves(results)
    
    print("✅ Evaluation complete!")


if __name__ == "__main__":
    main()
