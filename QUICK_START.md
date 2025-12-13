# Quick Start Guide - Enhanced Features

## 🚀 Start the Application

```bash
cd "/Users/rykan/ĐỒ ÁN/IE105/WEB DEMO/Federated Learning Visualization App"
npm run dev
```

Open: http://localhost:3000

---

## 🎯 New Features Summary

### 1. D3 Force-Directed Network (`/topology`)
- Interactive drag-and-drop nodes
- Hover on workers to see label distributions
- Animated aggregation during playback

### 2. Partition Visualization
- Toggle "Show Partition Demo" to see data distribution
- IID: Uniform across workers
- Dirichlet: Skewed distributions
- Label Separation: Specialized workers

### 3. Animation Controls
- ▶️ Play/⏸️ Pause button
- ⏮️ Step Backward / ⏭️ Step Forward (10 iterations)
- 🔄 Reset to iteration 0
- Speed: 1x, 5x, 10x, 20x, 50x
- Progress bar for manual navigation

### 4. CSV Export (`/compare`)
- **Export Metrics:** Summary of all runs
- **Export Accuracy:** Chart data for plotting
- **Export Full Data:** Complete iteration details

---

## 📂 Files Created

### New Components
```
src/components/
├── NetworkVizD3.tsx          # D3 interactive network
└── PartitionDemo.tsx          # Partition visualization
```

### New Utilities
```
src/lib/
├── partitionUtils.ts          # Generate partition data
└── exportUtils.ts             # CSV export functions
```

### Documentation
```
ADVANCED_FEATURES.md           # English (detailed)
TOM_TAT_NANG_CAP.md           # Vietnamese (summary)
QUICK_START.md                # This file
```

---

## 🎨 Key Interactions

### Topology Page
1. **Select Run:** Dropdown → Choose experiment
2. **Play Animation:** Click ▶️, watch training progress
3. **Hover Worker:** See label distribution histogram
4. **Drag Nodes:** Rearrange network layout
5. **Check Partition:** Toggle demo to see data distribution

### Compare Page
1. **Filter Runs:** Use partition/optimizer/attack dropdowns
2. **Select Runs:** Check boxes for comparison (max 6)
3. **Export Data:** Click export buttons for CSV download
4. **Analyze:** Compare charts and metrics table

---

## 🔑 Keyboard Shortcuts

None implemented yet, but you can add:
- `Space` → Play/Pause
- `←` → Step Backward
- `→` → Step Forward
- `R` → Reset

---

## 🐛 Troubleshooting

### Issue: Network not showing
- Check console for D3 errors
- Verify run has meta.byzantine_size and honest_size

### Issue: Animation not smooth
- Reduce speed (try 5x instead of 50x)
- Close other browser tabs

### Issue: CSV not downloading
- Check browser download settings
- Try different browser (Chrome/Firefox)

### Issue: TypeScript errors in VS Code
- These are expected during compilation
- Don't affect runtime
- Run `npm run dev` to verify it works

---

## 📊 Data Flow

```
1. dataLoader.ts → Load JSON files
2. TopologyPageClient → Pass to components
3. NetworkVizD3 → Render with D3
4. Animation loop → Update currentIteration
5. Charts update → Show metrics at current iteration
```

---

## 🎓 Learn More

- **D3.js:** https://d3js.org/
- **Next.js:** https://nextjs.org/docs
- **Federated Learning:** https://ai.googleblog.com/2017/04/federated-learning-collaborative.html

---

## ✅ Quick Test

1. Start server: `npm run dev`
2. Go to: http://localhost:3000/topology
3. Click Play ▶️
4. See network animate
5. Hover on blue/red nodes
6. ✓ Success!

---

**Version:** 0.3.0
**Last Updated:** Dec 11, 2025
