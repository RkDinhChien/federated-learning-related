'use client';

import type { RunData } from '@/types';

interface MetricsTableProps {
  runs: RunData[];
  selectedRuns: string[];
  onToggleRun: (id: string) => void;
}

export function MetricsTable({ runs, selectedRuns, onToggleRun }: MetricsTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Select</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Run Name</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Partition</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Optimizer</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Attack</th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase">Aggregator</th>
            <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Final Accuracy</th>
            <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Mean Accuracy</th>
            <th className="px-3 py-3 text-right text-xs font-medium text-gray-500 uppercase">Std Accuracy</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {runs.map((run) => (
            <tr key={run.id} className={selectedRuns.includes(run.id) ? 'bg-blue-50' : ''}>
              <td className="px-3 py-3 whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={selectedRuns.includes(run.id)}
                  onChange={() => onToggleRun(run.id)}
                  className="rounded border-gray-300"
                />
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900">{run.name}</td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-600">{run.partition}</td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-600">{run.meta.optimizer}</td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-600">{run.meta.attack}</td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-600">{run.meta.aggregator}</td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-right text-gray-900 font-medium">
                {run.meta.final_accuracy ? `${(run.meta.final_accuracy * 100).toFixed(2)}%` : 'N/A'}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-right text-gray-600">
                {run.meta.mean_accuracy ? `${(run.meta.mean_accuracy * 100).toFixed(2)}%` : 'N/A'}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-right text-gray-600">
                {run.meta.std_accuracy ? `${(run.meta.std_accuracy * 100).toFixed(2)}%` : 'N/A'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
