"""
Phase 3 Configuration - FLSG Defense Testing
"""

import torch
from gradient_defense import DefenseConfig

# ==========================================
# Device Configuration
# ==========================================
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ==========================================
# Model Configuration
# ==========================================
EMBEDDING_DIM = 128
NUM_CLASSES = 10
BATCH_SIZE = 128

# ==========================================
# Training Configuration
# ==========================================
NUM_EPOCHS_TRAIN = 30  # Main training epochs
LEARNING_RATE = 0.001
WEIGHT_DECAY = 1e-5

# ==========================================
# Attack Configuration (MaliciousSGD)
# ==========================================
ATTACK_CONFIG = {
    'lr': 0.001,        # Learning rate for attack
    'beta': 0.9,        # Momentum coefficient
    'gamma': 1.0,       # Amplification base factor
    'r_min': 1.0,       # Min amplification ratio
    'r_max': 3.0,       # Max amplification ratio
}

# ==========================================
# Inference Attack Configuration (MixMatch)
# ==========================================
INFERENCE_CONFIG = {
    'labeled_samples': 100,
    'warmup_epochs': 20,
    'total_epochs': 300,
    'lambda_u': 1.0,
    'temperature': 0.5,
    'alpha_mixup': 0.75,
}

# ==========================================
# Defense Configuration (FLSG)
# ==========================================
DEFENSE_CONFIG = DefenseConfig(
    ema_alpha=0.95,
    anomaly_threshold_low=0.3,
    anomaly_threshold_high=0.7,
    noise_sigma_med=0.2,
    noise_sigma_high=0.3,
    enable_logging=True,
)

# ==========================================
# Experiment Configuration
# ==========================================
ENABLE_DEFENSE = True  # Toggle defense on/off
RUN_BASELINE = True    # Run without defense first
RUN_WITH_DEFENSE = True  # Run with defense enabled
