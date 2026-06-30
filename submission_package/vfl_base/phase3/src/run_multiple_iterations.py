#!/usr/bin/env python3
"""
Run FLSG training multiple times to compare variance
"""

import json
import subprocess
from pathlib import Path

results = []

print("🔄 Running 5 iterations of FLSG training...")
print("="*60)

for i in range(1, 6):
    print(f"📍 Iteration {i}/5... ", end='', flush=True)
    
    # Run the quick script
    result = subprocess.run(
        ['python3', 'main_phase3_quick_flsg.py'],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True
    )
    
    # Parse results
    try:
        with open(Path(__file__).parent / "quick_flsg_results.json") as f:
            data = json.load(f)
            baseline = data['baseline_acc'][-1]
            defense = data['defense_acc'][-1]
            time_sec = data['time_seconds']
            results.append({
                'iteration': i,
                'baseline': baseline,
                'defense': defense,
                'time': time_sec,
                'diff': baseline - defense
            })
            print(f"✅ B={baseline:.4f} D={defense:.4f}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("="*60)
print("\n📊 SUMMARY (5 Iterations)")
print("-"*60)
print("Iter | Baseline | Defense  | Difference | Time")
print("-"*60)

baselines = []
defenses = []
times = []

for r in results:
    print(f"{r['iteration']:4d} | {r['baseline']:.4f}   | {r['defense']:.4f}   | {r['diff']:+.4f}      | {r['time']:.2f}s")
    baselines.append(r['baseline'])
    defenses.append(r['defense'])
    times.append(r['time'])

print("-"*60)
print(f"Avg  | {sum(baselines)/len(baselines):.4f}   | {sum(defenses)/len(defenses):.4f}   | {sum(b-d for b, d in zip(baselines, defenses))/len(baselines):+.4f}      | {sum(times)/len(times):.2f}s")
print()

# Save comparison results
with open(Path(__file__).parent / "multi_run_results.json", 'w') as f:
    json.dump({
        'iterations': results,
        'statistics': {
            'baseline_mean': sum(baselines) / len(baselines),
            'baseline_max': max(baselines),
            'baseline_min': min(baselines),
            'defense_mean': sum(defenses) / len(defenses),
            'defense_max': max(defenses),
            'defense_min': min(defenses),
            'avg_time': sum(times) / len(times),
        }
    }, f, indent=2)

print("✅ Results saved: multi_run_results.json")
print("="*60)

