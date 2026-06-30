import Papa from 'papaparse';
import { RunData, ExportMetrics } from '@/types';

/**
 * Export comparison metrics to CSV
 */
export function exportMetricsToCSV(runs: RunData[], filename: string = 'federated_learning_comparison.csv') {
  const metrics: ExportMetrics[] = runs.map(run => ({
    runName: run.name,
    partition: run.partition,
    optimizer: run.meta.optimizer || 'unknown',
    aggregator: run.meta.aggregator || 'unknown',
    attack: run.meta.attack || 'none',
    byzantineSize: run.meta.byzantine_size,
    honestSize: run.meta.honest_size,
    lr: run.meta.lr,
    rounds: run.meta.rounds,
    finalAccuracy: run.meta.final_accuracy || 0,
    meanAccuracy: run.meta.mean_accuracy || 0,
    stdAccuracy: run.meta.std_accuracy || 0,
    meanLoss: run.statistics.loss.mean,
    stdLoss: run.statistics.loss.std,
  }));

  const csv = Papa.unparse(metrics);
  downloadCSV(csv, filename);
}

/**
 * Export full iteration data for selected runs
 */
export function exportIterationsToCSV(runs: RunData[], filename: string = 'federated_learning_iterations.csv') {
  const allData: any[] = [];
  
  runs.forEach(run => {
    run.iterations.forEach(iter => {
      allData.push({
        runName: run.name,
        partition: run.partition,
        optimizer: run.meta.optimizer,
        aggregator: run.meta.aggregator,
        attack: run.meta.attack,
        iteration: iter.iteration,
        round: iter.round,
        accuracy: iter.accuracy,
        loss: iter.loss,
        lr: iter.lr,
        progress: iter.progress,
      });
    });
  });

  const csv = Papa.unparse(allData);
  downloadCSV(csv, filename);
}

/**
 * Export chart data as CSV for external plotting
 */
export function exportChartData(
  runs: RunData[],
  metric: 'accuracy' | 'loss' | 'lr',
  filename?: string
) {
  if (!filename) {
    filename = `federated_learning_${metric}_comparison.csv`;
  }

  // Create headers
  const headers = ['iteration', ...runs.map(r => r.name)];
  
  // Find max iterations
  const maxIterations = Math.max(...runs.map(r => r.iterations.length));
  
  // Build data rows
  const rows: any[][] = [];
  for (let i = 0; i < maxIterations; i++) {
    const row: any[] = [i];
    runs.forEach(run => {
      const iter = run.iterations[i];
      row.push(iter ? iter[metric] : null);
    });
    rows.push(row);
  }

  const csv = Papa.unparse({
    fields: headers,
    data: rows,
  });
  
  downloadCSV(csv, filename);
}

/**
 * Export network topology snapshot as CSV
 */
export function exportTopologySnapshot(
  workerStates: Array<{
    id: string;
    isByzantine: boolean;
    labelDistribution: number[];
    localAccuracy?: number;
  }>,
  iteration: number,
  filename: string = 'topology_snapshot.csv'
) {
  const data = workerStates.map(worker => ({
    iteration,
    workerId: worker.id,
    isByzantine: worker.isByzantine,
    localAccuracy: worker.localAccuracy || 0,
    ...worker.labelDistribution.reduce((acc, val, idx) => {
      acc[`label_${idx}`] = val;
      return acc;
    }, {} as Record<string, number>),
  }));

  const csv = Papa.unparse(data);
  downloadCSV(csv, filename);
}

/**
 * Parse CSV file (for importing data)
 */
export function parseCSV<T = any>(file: File): Promise<T[]> {
  return new Promise((resolve, reject) => {
    Papa.parse<T>(file, {
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          console.warn('CSV parsing warnings:', results.errors);
        }
        resolve(results.data);
      },
      error: (error) => {
        reject(error);
      },
    });
  });
}

/**
 * Parse CSV from URL (for loading iterations.csv)
 */
export function parseCSVFromURL<T = any>(url: string): Promise<T[]> {
  return new Promise((resolve, reject) => {
    Papa.parse<T>(url, {
      download: true,
      header: true,
      dynamicTyping: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          console.warn('CSV parsing warnings:', results.errors);
        }
        resolve(results.data);
      },
      error: (error) => {
        reject(error);
      },
    });
  });
}

/**
 * Helper function to trigger CSV download in browser
 */
function downloadCSV(csv: string, filename: string) {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  
  if (link.download !== undefined) {
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

/**
 * Export aggregation events log
 */
export function exportAggregationLog(
  events: Array<{
    round: number;
    aggregator: string;
    acceptedWorkers: string[];
    rejectedWorkers: string[];
    byzantineWorkers: string[];
  }>,
  filename: string = 'aggregation_log.csv'
) {
  const data = events.map(event => ({
    round: event.round,
    aggregator: event.aggregator,
    totalWorkers: event.acceptedWorkers.length + event.rejectedWorkers.length,
    acceptedCount: event.acceptedWorkers.length,
    rejectedCount: event.rejectedWorkers.length,
    byzantineCount: event.byzantineWorkers.length,
    acceptedWorkers: event.acceptedWorkers.join(';'),
    rejectedWorkers: event.rejectedWorkers.join(';'),
    byzantineWorkers: event.byzantineWorkers.join(';'),
  }));

  const csv = Papa.unparse(data);
  downloadCSV(csv, filename);
}

/**
 * Format metrics summary for display
 */
export function formatMetricsSummary(runs: RunData[]): string {
  const summary = runs.map(run => {
    return `
Run: ${run.name}
Partition: ${run.partition}
Optimizer: ${run.meta.optimizer}
Aggregator: ${run.meta.aggregator}
Attack: ${run.meta.attack}
Byzantine Workers: ${run.meta.byzantine_size}
Honest Workers: ${run.meta.honest_size}
Learning Rate: ${run.meta.lr}
Rounds: ${run.meta.rounds}
Final Accuracy: ${(run.meta.final_accuracy || 0).toFixed(4)}
Mean Accuracy: ${(run.meta.mean_accuracy || 0).toFixed(4)} ± ${(run.meta.std_accuracy || 0).toFixed(4)}
Mean Loss: ${run.statistics.loss.mean.toFixed(4)} ± ${run.statistics.loss.std.toFixed(4)}
---`;
  }).join('\n');

  return summary;
}
