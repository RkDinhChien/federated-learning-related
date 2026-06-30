'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { RunData } from '@/types';
import { Trophy, TrendingUp, Shield } from 'lucide-react';

interface ComparisonChartsProps {
  runs: RunData[];
}

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

export function ComparisonCharts({ runs }: ComparisonChartsProps) {
  // Calculate best performers
  const runStats = runs.map(run => {
    const finalAcc = run.iterations[run.iterations.length - 1]?.accuracy || 0;
    const peakAcc = Math.max(...run.iterations.map(i => i.accuracy));
    return { run, finalAcc, peakAcc };
  });
  
  const bestRun = runStats.reduce((best, curr) => 
    curr.finalAcc > best.finalAcc ? curr : best, runStats[0]);
  
  const avgFinalAcc = runStats.reduce((sum, r) => sum + r.finalAcc, 0) / runs.length;
  
  return (
    <div className="space-y-8">
      {/* Insights Panel */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <div className="flex items-center gap-2 mb-2">
            <Trophy className="h-5 w-5 text-yellow-600" />
            <span className="text-sm font-semibold text-gray-700">Best Performer</span>
          </div>
          <div className="text-lg font-bold text-yellow-700">
            {bestRun.run.meta.aggregator || 'N/A'}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {(bestRun.finalAcc * 100).toFixed(2)}% accuracy
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Attack: {bestRun.run.meta.attack || 'none'}
          </div>
        </div>

        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-semibold text-gray-700">Avg Performance</span>
          </div>
          <div className="text-lg font-bold text-blue-700">
            {(avgFinalAcc * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-gray-600 mt-1">
            Across {runs.length} runs
          </div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="h-5 w-5 text-green-600" />
            <span className="text-sm font-semibold text-gray-700">Most Robust</span>
          </div>
          <div className="text-lg font-bold text-green-700">
            {runStats.reduce((best, curr) => {
              const variance = curr.run.iterations.reduce((sum, i, idx, arr) => {
                if (idx === 0) return 0;
                return sum + Math.abs(i.accuracy - arr[idx-1].accuracy);
              }, 0) / curr.run.iterations.length;
              return !best || variance < best.variance ? { run: curr.run, variance } : best;
            }, null as any)?.run.meta.aggregator || 'N/A'}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            Lowest variance
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-700">
            Accuracy Comparison
            <span className="ml-2 text-xs text-gray-500">(So sánh hiệu suất các aggregator)</span>
          </h4>
          <div className="text-xs text-gray-500">
            {runs.length} runs • Màu khác = Aggregator khác
          </div>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="iteration" 
              type="number" 
              domain={[0, 'dataMax']}
              label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }}
            />
            <YAxis 
              domain={[0, 1]}
              label={{ value: 'Accuracy', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip formatter={(value: number) => `${(value * 100).toFixed(2)}%`} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <ReferenceLine y={0.8} stroke="#22c55e" strokeDasharray="3 3" label="Target (80%)" />
            <ReferenceLine y={bestRun.finalAcc} stroke="#f59e0b" strokeDasharray="5 5" label={`Best: ${(bestRun.finalAcc * 100).toFixed(1)}%`} />
            {runs.slice(0, 6).map((run, idx) => (
              <Line
                key={run.id}
                data={run.iterations}
                type="monotone"
                dataKey="accuracy"
                stroke={COLORS[idx]}
                strokeWidth={run === bestRun.run ? 3 : 2}
                dot={false}
                name={`${run.meta.aggregator || 'unknown'} (${run.meta.attack || 'none'})`}
                opacity={run === bestRun.run ? 1 : 0.7}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-medium text-gray-700">
            Loss Comparison
            <span className="ml-2 text-xs text-gray-500">(Thấp hơn = Tốt hơn)</span>
          </h4>
        </div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="iteration" 
              type="number" 
              domain={[0, 'dataMax']}
              label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }}
            />
            <YAxis label={{ value: 'Loss', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: number) => value.toFixed(4)} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            {runs.slice(0, 6).map((run, idx) => (
              <Line
                key={run.id}
                data={run.iterations}
                type="monotone"
                dataKey="loss"
                stroke={COLORS[idx]}
                strokeWidth={run === bestRun.run ? 3 : 2}
                dot={false}
                name={`${run.meta.aggregator || 'unknown'} (${run.meta.attack || 'none'})`}
                opacity={run === bestRun.run ? 1 : 0.7}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
