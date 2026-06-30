// Updated types for SR_MNIST data structure
export interface RunMeta {
  byzantine_size: number;
  lr: number;
  rounds: number;
  total_iterations: number;
  honest_size: number;
  dataset_size: number;
  dataset?: string;
  dataset_feature_dimension?: number;
  display_interval?: number;
  fix_seed?: boolean;
  seed?: number;
  weight_decay?: number;
  source_runs?: string[];
  run_count?: number;
  mean_accuracy?: number;
  std_accuracy?: number;
  final_accuracy?: number;
  partition?: string;
  aggregator?: string;
  attack?: string;
  optimizer?: string;
  progress?: number;
}

export interface IterationPoint {
  iteration: number;
  lr: number;
  loss: number;
  accuracy: number;
  round?: number;
  std_lr?: number;
  progress?: number;
  std_loss?: number;
  std_accuracy?: number;
  timestamp?: number | null;
  std_timestamp?: number | null;
}

export interface RunStatistics {
  point_count: number;
  lr: { mean: number; std: number };
  progress: { mean: number; std: number };
  loss: { mean: number; std: number };
  accuracy: { mean: number; std: number };
  timestamp: { mean: number | null; std: number | null };
}

export interface RunData {
  id: string;
  name: string;
  baseline: string;
  partition: string;
  meta: RunMeta;
  statistics: RunStatistics;
  iterations: IterationPoint[];
}

export interface DataIndex {
  converter_version: string;
  generated_at: string;
  partitions: {
    [partitionName: string]: {
      [runName: string]: {
        meta: string;
        iterations_json: string;
        iterations_csv: string;
      };
    };
  };
}

export type PartitionType = 'iidPartition' | 'DirichletPartition_alpha=1' | 'LabelSeperation';
export type AggregatorType = 'mean' | 'trimmed_mean' | 'CC_tau=0.3' | 'LFighter' | 'faba';
export type AttackType = 'none' | 'label_flipping' | 'furthest_label_flipping';
export type OptimizerType = 'CSGD' | 'CMomentum';

// Enhanced network topology types for D3 force simulation
export interface WorkerNode {
  id: string;
  type: 'worker';
  index?: number;
  isByzantine: boolean;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
  labelDistribution?: number[]; // For partition visualization
  localAccuracy?: number;
}

export interface ServerNode {
  id: string;
  type: 'server';
  index?: number;
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
  index?: number;
  isMalicious?: boolean;
  isActive?: boolean;
  strength?: number;
}

// Partition visualization data
export interface PartitionVisualization {
  type: PartitionType;
  workerDistributions: number[][]; // Array of label distributions per worker
  alpha?: number; // For Dirichlet
  labelGroups?: number[][]; // For LabelSeparation
}

// Animation state
export interface AnimationState {
  isPlaying: boolean;
  currentRound: number;
  currentIteration: number;
  speed: number; // iterations per second
  activeLinks: Set<string>; // Active link IDs during aggregation
}

// Aggregation visualization
export interface AggregationEvent {
  round: number;
  acceptedWorkers: string[]; // Worker IDs whose updates were accepted
  rejectedWorkers: string[]; // Worker IDs whose updates were trimmed/rejected
  byzantineWorkers: string[];
  method: AggregatorType;
}

// Attack visualization
export interface AttackEvent {
  round: number;
  byzantineWorker: string;
  attackType: AttackType;
  magnitude?: number; // For distance-based attacks
  flippedLabels?: number[]; // For label flipping
}

// CSV export types
export interface ExportMetrics {
  runName: string;
  partition: string;
  optimizer: string;
  aggregator: string;
  attack: string;
  byzantineSize: number;
  honestSize: number;
  lr: number;
  rounds: number;
  finalAccuracy: number;
  meanAccuracy: number;
  stdAccuracy: number;
  meanLoss?: number;
  stdLoss?: number;
}

// Parser helpers
export function parseRunName(runName: string): {
  optimizer: string;
  attack: string;
  aggregator: string;
} {
  const parts = runName.split('_');
  const optimizer = parts[0]; // CSGD or CMomentum
  
  // Find attack type
  let attack = 'none';
  let aggregatorStart = 1;
  if (runName.includes('furthest_label_flipping')) {
    attack = 'furthest_label_flipping';
    aggregatorStart = 3;
  } else if (runName.includes('label_flipping')) {
    attack = 'label_flipping';
    aggregatorStart = 2;
  }
  
  // Get aggregator (everything after attack)
  const aggregator = parts.slice(aggregatorStart).join('_');
  
  return { optimizer, attack, aggregator };
}
