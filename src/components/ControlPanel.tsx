'use client';

import { useState, useEffect } from 'react';
import { Play, Pause, SkipForward } from 'lucide-react';
import type { RunData } from '@/types';

interface ControlPanelProps {
  runs: RunData[];
  partitions: string[];
  selectedRun: RunData;
  onRunSelect: (run: RunData) => void;
  currentIteration: number;
  onIterationChange: (iteration: number) => void;
}

export function ControlPanel({
  runs,
  partitions,
  selectedRun,
  onRunSelect,
  currentIteration,
  onIterationChange,
}: ControlPanelProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [selectedPartition, setSelectedPartition] = useState('all');

  const filteredRuns = selectedPartition === 'all' 
    ? runs 
    : runs.filter(r => r.partition === selectedPartition);

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      if (currentIteration >= selectedRun.iterations.length - 1) {
        setIsPlaying(false);
        return;
      }
      onIterationChange(currentIteration + 1);
    }, 100);

    return () => clearInterval(interval);
  }, [isPlaying, currentIteration, selectedRun.iterations.length, onIterationChange]);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Experiment Selection</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Partition</label>
            <select
              value={selectedPartition}
              onChange={(e) => setSelectedPartition(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            >
              <option value="all">All Partitions</option>
              {partitions.map((p) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Run</label>
            <select
              value={selectedRun.id}
              onChange={(e) => {
                const run = filteredRuns.find((r) => r.id === e.target.value);
                if (run) onRunSelect(run);
              }}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            >
              {filteredRuns.map((run) => (
                <option key={run.id} value={run.id}>{run.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Playback</h3>
        
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Iteration: {selectedRun.iterations[currentIteration]?.iteration || 0} / {selectedRun.meta.total_iterations}
            </label>
            <input
              type="range"
              min="0"
              max={selectedRun.iterations.length - 1}
              value={currentIteration}
              onChange={(e) => onIterationChange(parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              {isPlaying ? <><Pause className="w-4 h-4" />Pause</> : <><Play className="w-4 h-4" />Play</>}
            </button>
            <button
              onClick={() => onIterationChange(0)}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Current Metrics</h3>
        
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Accuracy:</span>
            <span className="font-medium text-gray-900">
              {(selectedRun.iterations[currentIteration]?.accuracy * 100 || 0).toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Loss:</span>
            <span className="font-medium text-gray-900">
              {selectedRun.iterations[currentIteration]?.loss.toFixed(4) || 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
