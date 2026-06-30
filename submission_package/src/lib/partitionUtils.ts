import { PartitionType, PartitionVisualization } from '@/types';

/**
 * Generate synthetic partition visualization data
 * This simulates how data would be distributed across workers
 */
export function generatePartitionVisualization(
  partitionType: PartitionType,
  numWorkers: number = 10,
  numClasses: number = 10,
  alpha: number = 1.0
): PartitionVisualization {
  switch (partitionType) {
    case 'iidPartition':
      return generateIIDPartition(numWorkers, numClasses);
    
    case 'DirichletPartition_alpha=1':
      return generateDirichletPartition(numWorkers, numClasses, alpha);
    
    case 'LabelSeperation':
      return generateLabelSeparation(numWorkers, numClasses);
    
    default:
      return generateIIDPartition(numWorkers, numClasses);
  }
}

/**
 * IID Partition: Each worker has uniform distribution of all classes
 */
function generateIIDPartition(numWorkers: number, numClasses: number): PartitionVisualization {
  const workerDistributions: number[][] = [];
  
  for (let w = 0; w < numWorkers; w++) {
    const distribution = new Array(numClasses).fill(1 / numClasses);
    // Add small random variation
    for (let c = 0; c < numClasses; c++) {
      distribution[c] += (Math.random() - 0.5) * 0.02;
    }
    // Normalize
    const sum = distribution.reduce((a, b) => a + b, 0);
    workerDistributions.push(distribution.map(v => v / sum));
  }
  
  return {
    type: 'iidPartition',
    workerDistributions,
  };
}

/**
 * Dirichlet Partition: Non-IID with Dirichlet distribution
 * Lower alpha = more skewed distributions
 */
function generateDirichletPartition(
  numWorkers: number,
  numClasses: number,
  alpha: number
): PartitionVisualization {
  const workerDistributions: number[][] = [];
  
  for (let w = 0; w < numWorkers; w++) {
    // Sample from Dirichlet distribution (simplified approximation)
    const distribution = new Array(numClasses);
    let sum = 0;
    
    for (let c = 0; c < numClasses; c++) {
      // Use Gamma distribution approximation
      const gamma = gammaRandom(alpha, 1);
      distribution[c] = gamma;
      sum += gamma;
    }
    
    // Normalize
    workerDistributions.push(distribution.map(v => v / sum));
  }
  
  return {
    type: 'DirichletPartition_alpha=1',
    workerDistributions,
    alpha,
  };
}

/**
 * Label Separation: Each worker specializes in certain labels
 */
function generateLabelSeparation(numWorkers: number, numClasses: number): PartitionVisualization {
  const workerDistributions: number[][] = [];
  const labelGroups: number[][] = [];
  const labelsPerWorker = Math.ceil(numClasses / numWorkers);
  
  for (let w = 0; w < numWorkers; w++) {
    const distribution = new Array(numClasses).fill(0);
    const assignedLabels: number[] = [];
    
    // Assign specific labels to this worker
    const startLabel = (w * labelsPerWorker) % numClasses;
    for (let i = 0; i < labelsPerWorker && (startLabel + i) < numClasses; i++) {
      const label = (startLabel + i) % numClasses;
      distribution[label] = 0.8 / labelsPerWorker; // 80% on assigned labels
      assignedLabels.push(label);
    }
    
    // Remaining 20% distributed across other labels
    const remaining = 0.2 / (numClasses - labelsPerWorker);
    for (let c = 0; c < numClasses; c++) {
      if (distribution[c] === 0) {
        distribution[c] = remaining;
      }
    }
    
    // Normalize
    const sum = distribution.reduce((a, b) => a + b, 0);
    workerDistributions.push(distribution.map(v => v / sum));
    labelGroups.push(assignedLabels);
  }
  
  return {
    type: 'LabelSeperation',
    workerDistributions,
    labelGroups,
  };
}

/**
 * Simplified Gamma random number generator
 * Using Marsaglia and Tsang's method
 */
function gammaRandom(alpha: number, beta: number): number {
  // For alpha < 1, use rejection method
  if (alpha < 1) {
    return gammaRandom(alpha + 1, beta) * Math.pow(Math.random(), 1 / alpha);
  }
  
  // For alpha >= 1, use Marsaglia and Tsang's method
  const d = alpha - 1 / 3;
  const c = 1 / Math.sqrt(9 * d);
  
  while (true) {
    let x, v;
    do {
      x = normalRandom();
      v = 1 + c * x;
    } while (v <= 0);
    
    v = v * v * v;
    const u = Math.random();
    const x2 = x * x;
    
    if (u < 1 - 0.0331 * x2 * x2) {
      return d * v / beta;
    }
    
    if (Math.log(u) < 0.5 * x2 + d * (1 - v + Math.log(v))) {
      return d * v / beta;
    }
  }
}

/**
 * Box-Muller transform for normal random numbers
 */
function normalRandom(): number {
  const u1 = Math.random();
  const u2 = Math.random();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

/**
 * Calculate KL divergence between two distributions (for analysis)
 */
export function klDivergence(p: number[], q: number[]): number {
  let divergence = 0;
  for (let i = 0; i < p.length; i++) {
    if (p[i] > 0 && q[i] > 0) {
      divergence += p[i] * Math.log(p[i] / q[i]);
    }
  }
  return divergence;
}

/**
 * Analyze partition heterogeneity
 */
export function analyzePartitionHeterogeneity(viz: PartitionVisualization): {
  avgKLDivergence: number;
  maxKLDivergence: number;
  minKLDivergence: number;
} {
  const { workerDistributions } = viz;
  const n = workerDistributions.length;
  
  // Calculate uniform distribution as reference
  const uniform = new Array(workerDistributions[0].length).fill(
    1 / workerDistributions[0].length
  );
  
  const divergences: number[] = [];
  
  for (const dist of workerDistributions) {
    divergences.push(klDivergence(dist, uniform));
  }
  
  return {
    avgKLDivergence: divergences.reduce((a, b) => a + b, 0) / n,
    maxKLDivergence: Math.max(...divergences),
    minKLDivergence: Math.min(...divergences),
  };
}
