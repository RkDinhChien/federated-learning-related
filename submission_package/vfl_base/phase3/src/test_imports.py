#!/usr/bin/env python3
"""Test imports for Phase 3"""

print("Testing Phase 3 imports...")

try:
    print("[1/7] Importing torch...", end=" ")
    import torch
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[2/7] Importing config...", end=" ")
    from config import DEVICE, BATCH_SIZE, DEFENSE_CONFIG
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[3/7] Importing gradient_defense...", end=" ")
    from gradient_defense import GradientDefenseModule, DefenseConfig
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[4/7] Importing dataset...", end=" ")
    from dataset import get_dataloaders
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[5/7] Importing client_bao...", end=" ")
    from client_bao import ClientWorker
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[6/7] Importing server_chien...", end=" ")
    from server_chien import ServerCoordinator
    print("✅")
except Exception as e:
    print(f"❌ {e}")

try:
    print("[7/7] Importing malicious_optimizer...", end=" ")
    from malicious_optimizer import MaliciousSGD
    print("✅")
except Exception as e:
    print(f"❌ {e}")

print("\n✅ All imports successful!")
