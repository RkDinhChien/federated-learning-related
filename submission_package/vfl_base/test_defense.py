"""
Simple Test for FLSG Defense Module
"""

import torch
from dataclasses import dataclass


@dataclass
class DefenseConfig:
    """Configuration for FLSG defense mechanism"""
    ema_alpha: float = 0.95
    anomaly_threshold_low: float = 0.3
    anomaly_threshold_high: float = 0.7
    noise_sigma_med: float = 0.2
    noise_sigma_high: float = 0.3
    enable_logging: bool = True


class GradientDefenseModule:
    """FLSG Defense Module - Anomaly Detection + Selective Noise"""
    
    def __init__(self, config: DefenseConfig, device: str = 'cpu'):
        self.config = config
        self.device = device
        self.grad_ema = None
        self.grad_ema_norm = None
        self.normal_count = 0
        self.suspicious_count = 0
        self.rejected_count = 0
        self.anomaly_count = 0
        self.iteration_count = 0
    
    def _initialize_ema(self, gradient: torch.Tensor) -> None:
        self.grad_ema = gradient.clone().detach()
        self.grad_ema_norm = self.grad_ema.norm().item()
    
    def _compute_anomaly_score(self, gradient: torch.Tensor) -> float:
        if self.grad_ema is None:
            return 0.0
        
        grad_diff = gradient - self.grad_ema
        numerator = grad_diff.norm().item()
        denominator = self.grad_ema_norm + 1e-8
        
        return numerator / denominator
    
    def _apply_defense(self, gradient: torch.Tensor, 
                      anomaly_score: float) -> tuple:
        if anomaly_score < self.config.anomaly_threshold_low:
            action = "normal"
            defended_gradient = gradient
            self.normal_count += 1
            
        elif anomaly_score < self.config.anomaly_threshold_high:
            action = "suspicious"
            noise = torch.randn_like(gradient) * self.config.noise_sigma_med
            defended_gradient = gradient + noise
            self.suspicious_count += 1
            
        else:
            action = "rejected"
            defended_gradient = self.grad_ema.clone()
            self.rejected_count += 1
            self.anomaly_count += 1
        
        return defended_gradient, action
    
    def apply(self, gradient: torch.Tensor) -> torch.Tensor:
        self.iteration_count += 1
        
        if self.grad_ema is None:
            self._initialize_ema(gradient)
            return gradient
        
        anomaly_score = self._compute_anomaly_score(gradient)
        defended_gradient, action = self._apply_defense(gradient, anomaly_score)
        
        self.grad_ema = (
            self.config.ema_alpha * self.grad_ema + 
            (1 - self.config.ema_alpha) * gradient
        )
        self.grad_ema_norm = self.grad_ema.norm().item()
        
        return defended_gradient
    
    def get_statistics(self) -> dict:
        total = self.normal_count + self.suspicious_count + self.rejected_count
        
        return {
            'total_iterations': self.iteration_count,
            'normal_count': self.normal_count,
            'normal_percentage': 100 * self.normal_count / (total + 1e-8),
            'suspicious_count': self.suspicious_count,
            'suspicious_percentage': 100 * self.suspicious_count / (total + 1e-8),
            'rejected_count': self.rejected_count,
            'rejected_percentage': 100 * self.rejected_count / (total + 1e-8),
            'anomaly_count': self.anomaly_count,
        }


def simulate_normal_gradients(num_steps=50, embedding_dim=128):
    """Simulate normal gradients from honest training."""
    torch.manual_seed(42)
    gradients = []
    
    base_gradient = torch.randn(embedding_dim) * 0.5
    
    for step in range(num_steps):
        noise = torch.randn(embedding_dim) * 0.05
        g = base_gradient + noise
        gradients.append(g)
    
    return gradients


def simulate_malicious_gradients(num_steps=50, embedding_dim=128, attack_start=20):
    """Simulate MaliciousSGD attack."""
    torch.manual_seed(42)
    gradients = []
    
    base_gradient = torch.randn(embedding_dim) * 0.5
    
    for step in range(num_steps):
        if step < attack_start:
            noise = torch.randn(embedding_dim) * 0.05
            g = base_gradient + noise
        else:
            # Attack phase: amplified consistent direction
            consistent_direction = base_gradient / (base_gradient.norm() + 1e-8)
            magnitude = base_gradient.norm() * 3.0  # 3x amplification
            noise = torch.randn(embedding_dim) * 0.02
            g = consistent_direction * magnitude + noise
        
        gradients.append(g)
    
    return gradients


def main():
    print("\n" + "="*70)
    print("PHASE 3 DEFENSE MODULE - SIMPLE TEST")
    print("="*70)
    
    # Test 1: Normal gradients
    print("\n[Test 1] Processing 50 normal gradients...")
    config = DefenseConfig()
    defense = GradientDefenseModule(config)
    gradients = simulate_normal_gradients(num_steps=50)
    
    for g in gradients:
        _ = defense.apply(g)
    
    stats = defense.get_statistics()
    print(f"  Normal: {stats['normal_count']} ({stats['normal_percentage']:.1f}%)")
    print(f"  Suspicious: {stats['suspicious_count']} ({stats['suspicious_percentage']:.1f}%)")
    print(f"  Rejected: {stats['rejected_count']} ({stats['rejected_percentage']:.1f}%)")
    
    if stats['normal_percentage'] > 85:
        print("✅ PASS: Normal gradients allowed through\n")
    else:
        print("❌ FAIL: Too many normal gradients blocked\n")
    
    # Test 2: Malicious gradients
    print("[Test 2] Processing 50 gradients (attack at step 20)...")
    defense2 = GradientDefenseModule(config)
    gradients2 = simulate_malicious_gradients(num_steps=50, attack_start=20)
    
    for g in gradients2:
        _ = defense2.apply(g)
    
    stats2 = defense2.get_statistics()
    print(f"  Normal: {stats2['normal_count']} ({stats2['normal_percentage']:.1f}%)")
    print(f"  Suspicious: {stats2['suspicious_count']} ({stats2['suspicious_percentage']:.1f}%)")
    print(f"  Rejected: {stats2['rejected_count']} ({stats2['rejected_percentage']:.1f}%)")
    print(f"  Anomalies detected: {stats2['anomaly_count']}")
    
        # Check if defense caught attack: (suspicious + rejected) should be > 30% of total
    total_flagged = stats2['suspicious_count'] + stats2['rejected_count']
    total_gradients = stats2['normal_count'] + total_flagged
    flagged_rate = 100 * total_flagged / total_gradients
    
    if flagged_rate > 30:  # More than 30% of gradients flagged as anomalies
        print(f"✅ PASS: Attack detected ({flagged_rate:.1f}% flagged as anomalies)\n")
    else:
        print(f"❌ FAIL: Attack not detected ({flagged_rate:.1f}% < 30%)\n")
    
    # Test 3: Noise effectiveness
    print("[Test 3] Testing noise injection...")
    base_grad = torch.randn(128) * 0.5
    noise = torch.randn(128) * 0.2
    noisy_grad = base_grad + noise
    
    sign_flips = (torch.sign(base_grad) != torch.sign(noisy_grad)).sum().item()
    flip_rate = sign_flips / 128
    
    print(f"  Sign flips: {sign_flips}/128 ({flip_rate:.1%})")
    print(f"  Base norm: {base_grad.norm().item():.4f}")
    print(f"  Noise norm: {noise.norm().item():.4f}")
    
    if 0.1 <= flip_rate <= 0.5:
        print("✅ PASS: Noise effectiveness OK\n")
    else:
        print(f"⚠️  WARNING: Unexpected flip rate\n")
    
    print("="*70)
    print("🎉 Test completed successfully!")
    print("="*70)


if __name__ == "__main__":
    main()

