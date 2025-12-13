'use client';

import React from 'react';
import { PartitionVisualization, PartitionType } from '@/types';
import { generatePartitionVisualization, analyzePartitionHeterogeneity } from '@/lib/partitionUtils';

interface PartitionDemoProps {
  partitionType: PartitionType;
  numWorkers?: number;
  numClasses?: number;
  alpha?: number;
}

export default function PartitionDemo({
  partitionType,
  numWorkers = 10,
  numClasses = 10,
  alpha = 1.0,
}: PartitionDemoProps) {
  const viz = generatePartitionVisualization(partitionType, numWorkers, numClasses, alpha);
  const heterogeneity = analyzePartitionHeterogeneity(viz);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold mb-2">
          {getPartitionTitle(partitionType)}
        </h3>
        <p className="text-xs text-gray-600 mb-2">
          {getPartitionDescription(partitionType)}
        </p>
        
        {/* Heterogeneity metrics */}
        <div className="text-xs text-gray-500 space-y-1">
          <div>Avg KL Divergence: {heterogeneity.avgKLDivergence.toFixed(3)}</div>
          <div>Range: [{heterogeneity.minKLDivergence.toFixed(3)}, {heterogeneity.maxKLDivergence.toFixed(3)}]</div>
        </div>
      </div>

      {/* Worker distributions grid */}
      <div className="grid grid-cols-5 gap-2">
        {viz.workerDistributions.map((distribution, workerIdx) => (
          <div key={workerIdx} className="border border-gray-200 rounded p-2">
            <div className="text-xs font-medium text-center mb-2">W{workerIdx}</div>
            
            {/* Bar chart of label distribution */}
            <div className="flex items-end justify-center gap-0.5 h-20">
              {distribution.map((prob, labelIdx) => (
                <div
                  key={labelIdx}
                  className="flex-1 bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                  style={{ height: `${prob * 100}%` }}
                  title={`Label ${labelIdx}: ${(prob * 100).toFixed(1)}%`}
                />
              ))}
            </div>
            
            {/* Label numbers */}
            <div className="flex justify-center gap-0.5 mt-1">
              {distribution.map((_, labelIdx) => (
                <div key={labelIdx} className="flex-1 text-center text-xs text-gray-400">
                  {labelIdx}
                </div>
              ))}
            </div>
            
            {/* Highlight assigned labels for LabelSeparation */}
            {viz.labelGroups && viz.labelGroups[workerIdx] && (
              <div className="text-xs text-center text-blue-600 font-semibold mt-1">
                Labels: {viz.labelGroups[workerIdx].join(',')}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-4 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 bg-blue-500 rounded" />
          <span>Label probability</span>
        </div>
        <div>Hover bars for details</div>
      </div>
    </div>
  );
}

function getPartitionTitle(type: PartitionType): string {
  switch (type) {
    case 'iidPartition':
      return 'IID Partition';
    case 'DirichletPartition_alpha=1':
      return 'Dirichlet Partition (α=1)';
    case 'LabelSeperation':
      return 'Label Separation';
    default:
      return 'Unknown Partition';
  }
}

function getPartitionDescription(type: PartitionType): string {
  switch (type) {
    case 'iidPartition':
      return 'Independent and Identically Distributed: Each worker has a uniform distribution across all classes, simulating ideal conditions.';
    case 'DirichletPartition_alpha=1':
      return 'Non-IID with Dirichlet distribution: Workers have skewed label distributions. Lower α values create more heterogeneity.';
    case 'LabelSeperation':
      return 'Label Separation: Each worker specializes in specific label subsets, creating extreme non-IID conditions.';
    default:
      return '';
  }
}
