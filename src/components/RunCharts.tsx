'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { IterationPoint } from '@/types';
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react';

interface RunChartsProps {
  iterations: IterationPoint[];
  currentIteration: number;
}

export function RunCharts({ iterations, currentIteration }: RunChartsProps) {
  const data = iterations.slice(0, currentIteration + 1);
  
  // Calculate insights
  const currentData = data[data.length - 1];
  const startData = data[0];
  const accuracyChange = currentData ? ((currentData.accuracy - startData.accuracy) * 100).toFixed(2) : '0';
  const lossChange = currentData ? ((startData.loss - currentData.loss) / startData.loss * 100).toFixed(2) : '0';
  const isImproving = currentData && currentData.accuracy > startData.accuracy;
  
  // Find peak accuracy
  const peakAcc = Math.max(...data.map(d => d.accuracy));
  const peakIter = data.find(d => d.accuracy === peakAcc)?.iteration || 0;

  return (
    <div className="space-y-6">
      {/* Insights Summary */}
      <div className="grid grid-cols-3 gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
        <div>
          <div className="text-xs text-gray-600">Độ chính xác hiện tại</div>
          <div className="text-lg font-bold text-blue-600">
            {currentData ? (currentData.accuracy * 100).toFixed(2) : '0'}%
          </div>
          <div className={`text-xs flex items-center gap-1 ${isImproving ? 'text-green-600' : 'text-red-600'}`}>
            {isImproving ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {isImproving ? '+' : ''}{accuracyChange}%
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Peak Accuracy</div>
          <div className="text-lg font-bold text-green-600">
            {(peakAcc * 100).toFixed(2)}%
          </div>
          <div className="text-xs text-gray-500">
            at iteration {peakIter}
          </div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Loss giảm</div>
          <div className="text-lg font-bold text-orange-600">
            {lossChange}%
          </div>
          <div className="text-xs text-gray-500">
            Loss: {currentData?.loss.toFixed(4) || '0'}
          </div>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Accuracy Over Time
          <span className="ml-2 text-xs text-gray-500">(Cao hơn = Tốt hơn)</span>
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="iteration" label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }} />
            <YAxis domain={[0, 1]} label={{ value: 'Accuracy', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: number) => `${(value * 100).toFixed(2)}%`} />
            <Legend />
            <ReferenceLine y={0.8} stroke="#22c55e" strokeDasharray="3 3" label="Good (80%)" />
            <ReferenceLine y={peakAcc} stroke="#f59e0b" strokeDasharray="5 5" label={`Peak: ${(peakAcc * 100).toFixed(1)}%`} />
            <Line type="monotone" dataKey="accuracy" stroke="#3b82f6" strokeWidth={2} dot={false} name="Accuracy" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-700 mb-3">
          Loss Over Time
          <span className="ml-2 text-xs text-gray-500">(Thấp hơn = Tốt hơn)</span>
        </h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="iteration" label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Loss', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value: number) => value.toFixed(4)} />
            <Legend />
            <Line type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={false} name="Loss" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
