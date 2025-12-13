'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import { BarChart3, ArrowLeft, Download } from 'lucide-react';
import type { RunData } from '@/types';
import { ComparisonCharts } from '@/components/ComparisonCharts';
import { MetricsTable } from '@/components/MetricsTable';
import { exportMetricsToCSV, exportChartData, exportIterationsToCSV } from '@/lib/exportUtils';

interface ComparePageClientProps {
  runs: RunData[];
}

export default function ComparePageClient({ runs }: ComparePageClientProps) {
  const [selectedPartition, setSelectedPartition] = useState<string>('all');
  const [selectedOptimizer, setSelectedOptimizer] = useState<string>('all');
  const [selectedAttack, setSelectedAttack] = useState<string>('all');
  const [selectedRuns, setSelectedRuns] = useState<string[]>([]);

  // Get unique values for filters
  const partitions = useMemo(
    () => ['all', ...Array.from(new Set(runs.map((r) => r.partition)))],
    [runs]
  );

  const optimizers = useMemo(
    () => ['all', ...Array.from(new Set(runs.map((r) => r.meta.optimizer || '')))],
    [runs]
  );

  const attacks = useMemo(
    () => ['all', ...Array.from(new Set(runs.map((r) => r.meta.attack || '')))],
    [runs]
  );

  // Filter runs based on selections
  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      if (selectedPartition !== 'all' && run.partition !== selectedPartition) return false;
      if (selectedOptimizer !== 'all' && run.meta.optimizer !== selectedOptimizer) return false;
      if (selectedAttack !== 'all' && run.meta.attack !== selectedAttack) return false;
      return true;
    });
  }, [runs, selectedPartition, selectedOptimizer, selectedAttack]);

  // Get selected run objects
  const runsToCompare = useMemo(() => {
    if (selectedRuns.length === 0) return filteredRuns.slice(0, 5);
    return filteredRuns.filter((run) => selectedRuns.includes(run.id));
  }, [filteredRuns, selectedRuns]);

  const toggleRunSelection = (runId: string) => {
    setSelectedRuns((prev) =>
      prev.includes(runId) ? prev.filter((id) => id !== runId) : [...prev, runId]
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Filters */}
        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-bold text-gray-900">🔍 Filters</h2>
            
            {/* Export buttons */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => exportMetricsToCSV(runsToCompare)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                disabled={runsToCompare.length === 0}
              >
                <Download className="w-4 h-4" />
                Export Metrics
              </button>
              <button
                onClick={() => exportChartData(runsToCompare, 'accuracy')}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
                disabled={runsToCompare.length === 0}
              >
                <Download className="w-4 h-4" />
                Export Accuracy
              </button>
              <button
                onClick={() => exportIterationsToCSV(runsToCompare)}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                disabled={runsToCompare.length === 0}
              >
                <Download className="w-4 h-4" />
                Export Full Data
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Partition</label>
              <select
                value={selectedPartition}
                onChange={(e) => setSelectedPartition(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {partitions.map((p) => (
                  <option key={p} value={p}>
                    {p === 'all' ? 'All Partitions' : p}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Optimizer</label>
              <select
                value={selectedOptimizer}
                onChange={(e) => setSelectedOptimizer(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {optimizers.map((o) => (
                  <option key={o} value={o}>
                    {o === 'all' ? 'All Optimizers' : o}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Attack Type</label>
              <select
                value={selectedAttack}
                onChange={(e) => setSelectedAttack(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {attacks.map((a) => (
                  <option key={a} value={a}>
                    {a === 'all' ? 'All Attacks' : a}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredRuns.length} runs | Comparing {runsToCompare.length} runs
          </div>
        </div>

        {/* Comparison Charts */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 mb-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Metrics Comparison</h2>
          <ComparisonCharts runs={runsToCompare} />
        </div>

        {/* Metrics Table */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-base font-semibold text-gray-900 mb-4">All Experiments</h2>
          <MetricsTable
            runs={filteredRuns}
            selectedRuns={selectedRuns}
            onToggleRun={toggleRunSelection}
          />
        </div>
      </main>
    </div>
  );
}
