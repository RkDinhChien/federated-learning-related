#!/bin/bash

# Phase 3 Quick Start Script
# Run this to execute Phase 3 experiments

set -e

echo "========================================"
echo "  PHASE 3: FLSG DEFENSE SYSTEM"
echo "  Quick Start Script"
echo "========================================"

cd "$(dirname "$0")/src"

echo ""
echo "[1/3] Checking environment..."
python3 -c "import torch; print(f'PyTorch {torch.__version__} ✓')" || {
    echo "❌ PyTorch not installed. Run: pip install torch torchvision"
    exit 1
}

echo ""
echo "[2/3] Running Phase 3 experiments..."
echo "This will train baseline and defense models (2 experiments × 30 epochs)"
echo "Estimated time: 20-30 minutes on GPU, 2-3 hours on CPU"
echo ""

python3 main_phase3.py

echo ""
echo "[3/3] Generating evaluation report..."
python3 evaluate_phase3.py

echo ""
echo "========================================"
echo "  ✅ Phase 3 Complete!"
echo "========================================"
echo ""
echo "Results saved to: phase3_results/"
echo "  - phase3_results.json (metrics)"
echo "  - evaluation_report.txt (analysis)"
echo "  - training_curves.png (visualization)"
echo ""
