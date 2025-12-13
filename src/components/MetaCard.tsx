'use client';

import type { RunMeta } from '@/types';

interface MetaCardProps {
  meta: RunMeta;
}

export function MetaCard({ meta }: MetaCardProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <h3 className="text-sm font-medium text-gray-900 mb-3">Experiment Details</h3>
      
      <div className="space-y-2 text-xs">
        <InfoRow label="Optimizer" value={meta.optimizer} />
        <InfoRow label="Attack" value={meta.attack} />
        <InfoRow label="Aggregator" value={meta.aggregator} />
        <InfoRow label="Byzantine Workers" value={meta.byzantine_size} />
        <InfoRow label="Honest Workers" value={meta.honest_size} />
        <InfoRow label="Learning Rate" value={meta.lr} />
        <InfoRow label="Rounds" value={meta.rounds} />
        <InfoRow label="Total Iterations" value={meta.total_iterations} />
        <InfoRow label="Dataset Size" value={meta.dataset_size} />
        {meta.final_accuracy && (
          <InfoRow label="Final Accuracy" value={`${(meta.final_accuracy * 100).toFixed(2)}%`} />
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string | number | undefined }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-600">{label}:</span>
      <span className="font-medium text-gray-900">{value}</span>
    </div>
  );
}
