# Federated Learning Visualizer - Advanced Features Guide

## 🎯 Overview

This application now includes advanced visualization features as specified in your comprehensive requirements:

### ✨ New Features Implemented

1. **D3 Force-Directed Network Visualization**
   - Interactive network topology with draggable nodes
   - Real-time animation during training rounds
   - Byzantine worker highlighting and attack visualization
   - Hover interactions showing worker label distributions

2. **Partition Visualization Demos**
   - IID Partition: Uniform label distribution across workers
   - Dirichlet Partition: Non-IID with configurable alpha parameter
   - Label Separation: Workers specialized in specific label subsets
   - KL divergence metrics for heterogeneity analysis

3. **Animation System**
   - Round-by-round playback with configurable speed (1x, 5x, 10x, 20x, 50x)
   - Play/Pause/Step Forward/Step Backward controls
   - Progress bar for manual navigation
   - Real-time metrics display at current iteration

4. **CSV Export Functionality**
   - Export comparison metrics summary
   - Export accuracy data for external plotting
   - Export full iteration data for all selected runs
   - Downloadable format for further analysis

---

## 📊 Page A: Topology & Dataflow Visualization

### Components

#### 1. **NetworkVizD3** (`src/components/NetworkVizD3.tsx`)

**Purpose:** Interactive force-directed graph showing federated learning network topology

**Features:**
- **Server Node (Purple):** Central aggregation server with current aggregator label
- **Worker Nodes (Blue/Red):** 10 workers (blue = honest, red = Byzantine)
- **Directed Edges:** Animated arrows showing updates flowing from workers to server
- **Drag & Drop:** All nodes are draggable for custom layouts
- **Hover Interactions:**
  - Shows worker ID and Byzantine status
  - Displays label distribution histogram (10 classes)
  - Shows local accuracy estimate
- **Attack Visualization:** Byzantine nodes show attack type badge
- **Aggregator Display:** Server node shows current aggregation method

**Props:**
```typescript
{
  byzantineCount: number;          // Number of Byzantine workers
  totalWorkers: number;            // Total number of workers
  currentIteration: number;        // Current training iteration
  aggregator: AggregatorType;      // Aggregation method
  attack: AttackType;              // Attack type
  isAnimating?: boolean;           // Whether to animate link activations
  onWorkerHover?: (worker: WorkerNode | null) => void;  // Hover callback
}
```

**Usage:**
```tsx
<NetworkVizD3
  byzantineCount={1}
  totalWorkers={10}
  currentIteration={currentIteration}
  aggregator="trimmed_mean"
  attack="label_flipping"
  isAnimating={isPlaying}
  onWorkerHover={setHoveredWorker}
/>
```

#### 2. **PartitionDemo** (`src/components/PartitionDemo.tsx`)

**Purpose:** Visualize data partition strategies across workers

**Features:**
- **Grid Layout:** Shows all 10 workers with their label distributions
- **Bar Charts:** Vertical bars showing probability of each class (0-9)
- **Heterogeneity Metrics:**
  - Average KL Divergence from uniform distribution
  - Min/Max KL Divergence range
- **Label Group Highlighting:** For Label Separation, shows assigned labels
- **Interactive:** Hover over bars to see exact percentages

**Partition Types:**

1. **IID Partition**
   - Each worker has approximately uniform distribution
   - Simulates ideal conditions where data is balanced
   - Low heterogeneity (KL divergence ≈ 0)

2. **Dirichlet Partition (α=1)**
   - Non-IID with skewed label distributions
   - Uses Dirichlet distribution to sample probabilities
   - Higher heterogeneity than IID
   - Lower α → more extreme skewness

3. **Label Separation**
   - Each worker specializes in 1-2 labels
   - Extreme non-IID conditions
   - Highest heterogeneity (KL divergence > 2)
   - Shows clear label assignments

**Props:**
```typescript
{
  partitionType: PartitionType;    // Type of partition
  numWorkers?: number;             // Number of workers (default 10)
  numClasses?: number;             // Number of classes (default 10)
  alpha?: number;                  // Dirichlet alpha parameter (default 1.0)
}
```

#### 3. **Animation Control Bar**

**Features:**
- **Reset Button:** Go back to iteration 0
- **Step Backward:** Jump back 10 iterations
- **Play/Pause:** Start/stop animation
- **Step Forward:** Jump ahead 10 iterations
- **Progress Bar:** Slider for manual navigation
- **Speed Control:** Dropdown with 1x, 5x, 10x, 20x, 50x speeds
- **Round/Iteration Display:** Current position vs total
- **Show Partition Demo Toggle:** Show/hide partition visualization

**Animation Logic:**
- Uses `requestAnimationFrame` for smooth animation
- Updates iteration counter based on selected speed
- Automatically pauses when reaching final iteration
- State preserved when switching runs

---

## 📈 Page B: Comparative Metrics

### Enhanced Features

#### 1. **CSV Export Buttons**

Three export options now available:

**Export Metrics:**
- Filename: `federated_learning_comparison.csv`
- Contains: Summary metrics for all selected runs
- Columns:
  - runName, partition, optimizer, aggregator, attack
  - byzantineSize, honestSize, lr, rounds
  - finalAccuracy, meanAccuracy, stdAccuracy
  - meanLoss, stdLoss

**Export Accuracy:**
- Filename: `federated_learning_accuracy_comparison.csv`
- Contains: Accuracy values at each iteration for all runs
- Format: Columns = [iteration, run1, run2, run3, ...]
- Useful for plotting in Excel/Python

**Export Full Data:**
- Filename: `federated_learning_iterations.csv`
- Contains: Complete iteration data with all metrics
- Columns:
  - runName, partition, optimizer, aggregator, attack
  - iteration, round, accuracy, loss, lr, progress
- Most comprehensive export option

#### 2. **Export Utilities** (`src/lib/exportUtils.ts`)

**Functions:**

```typescript
// Export comparison metrics
exportMetricsToCSV(runs: RunData[], filename?: string): void

// Export specific metric (accuracy/loss/lr) for plotting
exportChartData(runs: RunData[], metric: 'accuracy'|'loss'|'lr', filename?: string): void

// Export all iteration data
exportIterationsToCSV(runs: RunData[], filename?: string): void

// Export network topology snapshot
exportTopologySnapshot(workerStates: WorkerState[], iteration: number, filename?: string): void

// Parse CSV file (for importing)
parseCSV<T>(file: File): Promise<T[]>

// Parse CSV from URL (for loading iterations.csv)
parseCSVFromURL<T>(url: string): Promise<T[]>
```

---

## 🛠️ Technical Implementation

### Data Structures

#### Enhanced Types (`src/types.ts`)

**NetworkNode Types:**
```typescript
export interface WorkerNode {
  id: string;
  type: 'worker';
  isByzantine: boolean;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  labelDistribution?: number[];
  localAccuracy?: number;
}

export interface ServerNode {
  id: string;
  type: 'server';
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

export type NetworkNode = WorkerNode | ServerNode;

export interface NetworkLink {
  source: string | NetworkNode;
  target: string | NetworkNode;
  isMalicious?: boolean;
  isActive?: boolean;
  strength?: number;
}
```

**Partition Visualization:**
```typescript
export interface PartitionVisualization {
  type: PartitionType;
  workerDistributions: number[][];
  alpha?: number;
  labelGroups?: number[][];
}
```

### Partition Generation (`src/lib/partitionUtils.ts`)

**Key Functions:**

```typescript
// Generate synthetic partition visualization
generatePartitionVisualization(
  partitionType: PartitionType,
  numWorkers: number = 10,
  numClasses: number = 10,
  alpha: number = 1.0
): PartitionVisualization

// Calculate KL divergence between distributions
klDivergence(p: number[], q: number[]): number

// Analyze partition heterogeneity
analyzePartitionHeterogeneity(viz: PartitionVisualization): {
  avgKLDivergence: number;
  maxKLDivergence: number;
  minKLDivergence: number;
}
```

**Algorithms:**

1. **IID Partition:**
   - Generate uniform distribution (1/10 for each class)
   - Add small random noise (±0.01) for realism
   - Normalize to sum = 1

2. **Dirichlet Partition:**
   - Sample from Dirichlet(α, α, ..., α) for each worker
   - Use Gamma distribution approximation
   - Marsaglia & Tsang's method for Gamma random variables
   - Lower α → more skewed distributions

3. **Label Separation:**
   - Assign ceil(numClasses/numWorkers) labels per worker
   - 80% probability mass on assigned labels
   - 20% distributed across other labels
   - Clear separation between worker specializations

---

## 🎨 Visual Design

### Color Scheme

- **Server Node:** Purple (#8b5cf6) - stands out as aggregator
- **Honest Workers:** Blue (#3b82f6) - trustworthy
- **Byzantine Workers:** Red (#ef4444) - adversarial
- **Active Links:** Bright blue (#3b82f6) during animation
- **Malicious Links:** Red dashed lines (#ef4444)
- **Normal Links:** Gray (#94a3b8)

### Animations

1. **Link Activation:**
   - Sequential animation from workers to server
   - 100ms delay between workers
   - 300ms fade in, 300ms fade out
   - Simulates aggregation process

2. **Node Hover:**
   - Scale up from r=20 to r=25
   - Increase stroke width from 2 to 3
   - 200ms transition
   - Tooltip appears with worker info

3. **Progress Indicator:**
   - Current iteration highlighted on chart
   - Vertical line showing position
   - Metric values updated in real-time

---

## 📐 Mathematical Details

### KL Divergence Calculation

For distributions P and Q:

$$
D_{KL}(P||Q) = \sum_{i=1}^{n} P(i) \log \frac{P(i)}{Q(i)}
$$

Used to measure how different worker distributions are from uniform:
- **IID:** KL ≈ 0.001 (very similar to uniform)
- **Dirichlet (α=1):** KL ≈ 0.5-2.0 (moderate heterogeneity)
- **Label Separation:** KL > 2.0 (extreme heterogeneity)

### Dirichlet Distribution Sampling

For α parameters (α₁, α₂, ..., αₖ):

$$
P(X_1, ..., X_k) \propto \prod_{i=1}^{k} X_i^{\alpha_i - 1}
$$

Implementation:
1. Sample Yᵢ ~ Gamma(αᵢ, 1) for each class
2. Normalize: Xᵢ = Yᵢ / Σⱼ Yⱼ
3. X ~ Dirichlet(α)

---

## 🚀 Usage Examples

### Example 1: View IID Partition Animation

1. Navigate to Topology page
2. Select partition = "iidPartition"
3. Check "Show Partition Demo" toggle
4. Observe uniform distributions across workers
5. Click Play to animate training
6. Hover over workers to see label distributions

### Example 2: Compare Label Flipping Attacks

1. Navigate to Compare page
2. Filter by attack = "label_flipping"
3. Select 3-5 runs with different aggregators
4. Click "Export Metrics" to download summary
5. Analyze which aggregator is most robust

### Example 3: Export Accuracy Data

1. Navigate to Compare page
2. Select runs of interest (use checkboxes)
3. Click "Export Accuracy"
4. Open CSV in Excel/Python
5. Create custom plots with external tools

---

## 🧪 Testing Recommendations

### Manual Testing Checklist

**Topology Page:**
- [ ] Network visualization loads correctly
- [ ] All 10 workers and 1 server appear
- [ ] Byzantine worker(s) colored red
- [ ] Nodes are draggable
- [ ] Hover shows worker info
- [ ] Play button starts animation
- [ ] Animation respects speed setting
- [ ] Progress bar works
- [ ] Partition demo shows correct distributions
- [ ] Metrics update during animation

**Compare Page:**
- [ ] Filters work correctly
- [ ] Export Metrics downloads CSV
- [ ] Export Accuracy downloads CSV
- [ ] Export Full Data downloads CSV
- [ ] CSV files open correctly
- [ ] Data is accurate

### Unit Testing Suggestions

```typescript
// Test partition generation
test('generateIIDPartition creates uniform distributions', () => {
  const viz = generatePartitionVisualization('iidPartition', 10, 10);
  expect(viz.workerDistributions.length).toBe(10);
  viz.workerDistributions.forEach(dist => {
    expect(dist.length).toBe(10);
    const sum = dist.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0);
  });
});

// Test KL divergence
test('klDivergence of identical distributions is zero', () => {
  const p = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1];
  const q = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1];
  const divergence = klDivergence(p, q);
  expect(divergence).toBeCloseTo(0.0);
});
```

---

## 📝 Code Organization

```
src/
├── app/
│   ├── topology/
│   │   ├── page.tsx                    # Server Component
│   │   └── TopologyPageClient.tsx      # Enhanced with animation
│   └── compare/
│       ├── page.tsx                    # Server Component
│       └── ComparePageClient.tsx       # Enhanced with export buttons
├── components/
│   ├── NetworkVizD3.tsx               # NEW: D3 force-directed graph
│   ├── PartitionDemo.tsx              # NEW: Partition visualization
│   ├── NetworkViz.tsx                 # OLD: Basic SVG (kept for backup)
│   ├── ControlPanel.tsx
│   ├── RunCharts.tsx
│   ├── ComparisonCharts.tsx
│   ├── MetricsTable.tsx
│   └── MetaCard.tsx
├── lib/
│   ├── dataLoader.ts
│   ├── partitionUtils.ts              # NEW: Partition generation
│   └── exportUtils.ts                 # NEW: CSV export functions
└── types.ts                           # Enhanced with new types
```

---

## 🔧 Configuration

### D3 Force Simulation Parameters

In `NetworkVizD3.tsx`:

```typescript
const simulation = d3.forceSimulation<NetworkNode>(nodes)
  .force('link', d3.forceLink<NetworkNode, NetworkLink>(links)
    .distance(150)              // Distance between connected nodes
  )
  .force('charge', d3.forceManyBody()
    .strength(-300)             // Repulsion between nodes
  )
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide()
    .radius(40)                 // Minimum distance between nodes
  );
```

Adjust these parameters to change layout behavior.

### Animation Speed Presets

In `TopologyPageClient.tsx`:

```typescript
const speedOptions = [1, 5, 10, 20, 50]; // iterations per second
```

Add more options if needed (e.g., 100x for quick testing).

---

## 🎓 Learning Resources

### D3.js Force Simulation
- [Official Documentation](https://d3js.org/d3-force)
- [Force-Directed Graph Tutorial](https://observablehq.com/@d3/force-directed-graph)

### Dirichlet Distribution
- [Wikipedia](https://en.wikipedia.org/wiki/Dirichlet_distribution)
- [Sampling Methods](https://en.wikipedia.org/wiki/Dirichlet_distribution#Gamma_distribution)

### Federated Learning
- [Google AI Blog](https://ai.googleblog.com/2017/04/federated-learning-collaborative.html)
- [Byzantine-Robust Aggregation](https://arxiv.org/abs/1803.01498)

---

## 🐛 Known Issues & Limitations

1. **Synthetic Partition Data:**
   - Partition visualizations use synthetic label distributions
   - Real data distributions would require actual dataset analysis
   - Consider implementing data loader from actual partition files

2. **Performance:**
   - D3 force simulation may lag with >20 workers
   - Large iteration datasets (>50k points) slow down charts
   - Consider data subsampling for visualization

3. **Browser Compatibility:**
   - CSV download tested on Chrome/Firefox
   - May need polyfills for older browsers
   - D3 v7 requires modern JavaScript support

---

## 🚀 Future Enhancements

### Potential Additions:

1. **Real-Time Training:**
   - WebSocket connection to live training server
   - Stream metrics as they're generated
   - Show real worker label distributions

2. **Attack Visualization:**
   - Animate label flipping on Byzantine nodes
   - Show distance metrics for furthest attacks
   - Visualize gradient magnitudes

3. **Aggregator Animations:**
   - Show trimming process for trimmed_mean
   - Visualize filtering for FABA/LFighter
   - Display centroid calculation for CC

4. **3D Network Topology:**
   - Use three.js for 3D force-directed graph
   - Better for visualizing large networks
   - More engaging user experience

5. **Dataset Integration:**
   - Load MNIST images for each worker
   - Show actual data samples
   - Visualize misclassifications

---

## 📞 Support

For questions or issues:
1. Check this documentation
2. Review code comments
3. Inspect browser console for errors
4. Check TypeScript errors in VS Code

---

**Last Updated:** December 11, 2025
**Version:** 0.3.0 (Advanced Features)
