import { promises as fs } from 'fs';
import path from 'path';
import type { DataIndex, RunData, RunMeta, IterationPoint, RunStatistics } from '@/types';

const DATA_DIR = path.join(process.cwd(), 'data', 'SR_MNIST', 'Centralized_n=10_b=1');

/**
 * Load the main index file that maps all experiments
 */
export async function loadDataIndex(): Promise<DataIndex> {
  const indexPath = path.join(DATA_DIR, 'index.json');
  const content = await fs.readFile(indexPath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Load all available runs from all partitions
 */
export async function loadAllRuns(): Promise<RunData[]> {
  const index = await loadDataIndex();
  const runs: RunData[] = [];

  for (const [partitionName, partitionRuns] of Object.entries(index.partitions)) {
    for (const [runName, runPaths] of Object.entries(partitionRuns)) {
      try {
        const run = await loadRun(runPaths.meta, runPaths.iterations_json, runName, partitionName);
        runs.push(run);
      } catch (error) {
        console.error(`Failed to load run ${runName}:`, error);
      }
    }
  }

  return runs;
}

/**
 * Load runs from a specific partition
 */
export async function loadPartitionRuns(partitionName: string): Promise<RunData[]> {
  const index = await loadDataIndex();
  const partitionRuns = index.partitions[partitionName];
  
  if (!partitionRuns) {
    throw new Error(`Partition ${partitionName} not found`);
  }

  const runs: RunData[] = [];
  for (const [runName, runPaths] of Object.entries(partitionRuns)) {
    try {
      const run = await loadRun(runPaths.meta, runPaths.iterations_json, runName, partitionName);
      runs.push(run);
    } catch (error) {
      console.error(`Failed to load run ${runName}:`, error);
    }
  }

  return runs;
}

/**
 * Load a specific run by name
 */
export async function loadRunByName(partitionName: string, runName: string): Promise<RunData> {
  const index = await loadDataIndex();
  const runPaths = index.partitions[partitionName]?.[runName];
  
  if (!runPaths) {
    throw new Error(`Run ${runName} not found in partition ${partitionName}`);
  }

  return loadRun(runPaths.meta, runPaths.iterations_json, runName, partitionName);
}

/**
 * Internal function to load a single run from meta and iterations files
 */
async function loadRun(
  metaPath: string,
  iterationsPath: string,
  runName: string,
  partitionName: string
): Promise<RunData> {
  // Load meta file
  const metaFullPath = path.join(process.cwd(), metaPath);
  const metaContent = await fs.readFile(metaFullPath, 'utf-8');
  const metaData = JSON.parse(metaContent);

  // Load iterations file
  const iterationsFullPath = path.join(process.cwd(), iterationsPath);
  const iterationsContent = await fs.readFile(iterationsFullPath, 'utf-8');
  const iterationsData = JSON.parse(iterationsContent);

  // Extract optimizer, attack, and aggregator from run name
  const { optimizer, attack, aggregator } = parseRunName(runName);

  // Calculate final accuracy and other derived metrics
  const iterations: IterationPoint[] = iterationsData.iterations;
  const finalIteration = iterations[iterations.length - 1];
  const finalAccuracy = finalIteration?.accuracy || 0;

  const meta: RunMeta = {
    ...metaData.meta,
    partition: partitionName,
    optimizer,
    attack,
    aggregator,
    final_accuracy: finalAccuracy,
    mean_accuracy: iterationsData.statistics.accuracy.mean,
    std_accuracy: iterationsData.statistics.accuracy.std,
    progress: 1.0,
  };

  const statistics: RunStatistics = iterationsData.statistics;

  // Calculate round for each iteration if not present
  const processedIterations = iterations.map((iter) => ({
    ...iter,
    round: iter.round ?? Math.floor((iter.iteration / meta.total_iterations) * meta.rounds),
  }));

  return {
    id: `${partitionName}_${runName}`,
    name: runName,
    baseline: iterationsData.baseline || runName,
    partition: partitionName,
    meta,
    statistics,
    iterations: processedIterations,
  };
}

/**
 * Helper function to parse run name into components
 */
function parseRunName(runName: string): {
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

/**
 * Get list of available partitions
 */
export async function getAvailablePartitions(): Promise<string[]> {
  const index = await loadDataIndex();
  return Object.keys(index.partitions);
}

/**
 * Get list of available runs for a partition
 */
export async function getAvailableRuns(partitionName: string): Promise<string[]> {
  const index = await loadDataIndex();
  const partition = index.partitions[partitionName];
  
  if (!partition) {
    throw new Error(`Partition ${partitionName} not found`);
  }
  
  return Object.keys(partition);
}

/**
 * Filter runs by criteria
 */
export function filterRuns(
  runs: RunData[],
  filters: {
    partition?: string;
    optimizer?: string;
    attack?: string;
    aggregator?: string;
  }
): RunData[] {
  return runs.filter((run) => {
    if (filters.partition && run.partition !== filters.partition) return false;
    if (filters.optimizer && run.meta.optimizer !== filters.optimizer) return false;
    if (filters.attack && run.meta.attack !== filters.attack) return false;
    if (filters.aggregator && run.meta.aggregator !== filters.aggregator) return false;
    return true;
  });
}

/**
 * Get summary statistics for a set of runs
 */
export function getRunsSummary(runs: RunData[]) {
  const accuracies = runs.map(r => r.meta.final_accuracy || 0);
  const losses = runs.map(r => r.iterations[r.iterations.length - 1]?.loss || 0);
  
  return {
    count: runs.length,
    avgAccuracy: accuracies.reduce((a, b) => a + b, 0) / accuracies.length,
    maxAccuracy: Math.max(...accuracies),
    minAccuracy: Math.min(...accuracies),
    avgFinalLoss: losses.reduce((a, b) => a + b, 0) / losses.length,
  };
}
