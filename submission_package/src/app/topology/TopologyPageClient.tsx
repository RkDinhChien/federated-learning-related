'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { Layers, ArrowLeft, Play, Pause, SkipForward, SkipBack, RotateCcw } from 'lucide-react';
import type { RunData, PartitionType, AggregatorType, AttackType, WorkerNode } from '@/types';
import NetworkVizD3 from '@/components/NetworkVizD3';
import PartitionDemo from '@/components/PartitionDemo';
import { ControlPanel } from '@/components/ControlPanel';
import { RunCharts } from '@/components/RunCharts';
import { MetaCard } from '@/components/MetaCard';

interface TopologyPageClientProps {
  runs: RunData[];
  partitions: string[];
}

export default function TopologyPageClient({ runs, partitions }: TopologyPageClientProps) {
  const [selectedRun, setSelectedRun] = useState<RunData | null>(null);
  const [currentIteration, setCurrentIteration] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(10); // iterations per second
  const [showPartitionDemo, setShowPartitionDemo] = useState(true);
  const [hoveredWorker, setHoveredWorker] = useState<WorkerNode | null>(null);
  const [mounted, setMounted] = useState(false);
  const animationRef = useRef<number | null>(null);

  // Initialize selectedRun after mount to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
    if (runs.length > 0 && !selectedRun) {
      setSelectedRun(runs[0]);
    }
  }, [runs, selectedRun]);

  // Extract metadata safely
  const partition = selectedRun?.partition as PartitionType | undefined;
  const aggregator = (selectedRun?.meta.aggregator || 'mean') as AggregatorType;
  const attack = (selectedRun?.meta.attack || 'none') as AttackType;
  const maxIterations = selectedRun?.iterations.length || 0;
  const currentRound = selectedRun ? Math.floor((currentIteration / maxIterations) * selectedRun.meta.rounds) : 0;

  // Animation loop
  useEffect(() => {
    if (!isPlaying || !selectedRun) return;
    
    const interval = 1000 / playbackSpeed;
    let lastTime = Date.now();

    const animate = () => {
      const now = Date.now();
      if (now - lastTime >= interval) {
        setCurrentIteration(prev => {
          if (prev >= maxIterations - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
        lastTime = now;
      }
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, maxIterations, selectedRun]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleStepForward = () => {
    setCurrentIteration(prev => Math.min(prev + 10, maxIterations - 1));
  };

  const handleStepBackward = () => {
    setCurrentIteration(prev => Math.max(prev - 10, 0));
  };

  const handleReset = () => {
    setCurrentIteration(0);
    setIsPlaying(false);
  };

  // Early return AFTER all hooks
  if (!mounted || !selectedRun) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Quick Guide */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg p-4 mb-5">
          <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Hướng Dẫn Xem Topology - Mạng Lưới Huấn Luyện
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-white p-3 rounded-lg border border-blue-200">
              <p className="font-semibold text-blue-900 mb-1">Bước 1: Hiểu Sơ Đồ Mạng</p>
              <p className="text-xs text-gray-700">Vuông tím = Server | Tròn xanh = Workers trung thực | Tròn đỏ = Byzantine</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-purple-200">
              <p className="font-semibold text-purple-900 mb-1">Bước 2: Nhấn Play</p>
              <p className="text-xs text-gray-700">Xem Round/Iteration tăng lên → Biểu đồ bên dưới thay đổi</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-green-200">
              <p className="font-semibold text-green-900 mb-1">Bước 3: Xem Biểu Đồ Training</p>
              <p className="text-xs text-gray-700">Đường màu = độ chính xác qua các vòng (không phải topology)</p>
            </div>
            <div className="bg-white p-3 rounded-lg border border-orange-200">
              <p className="font-semibold text-orange-900 mb-1">Bước 4: So Sánh Runs</p>
              <p className="text-xs text-gray-700">Chọn thí nghiệm khác ở Control Panel bên trái</p>
            </div>
          </div>
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
            <p className="text-yellow-800">
              <strong>Lưu ý:</strong> Topology này là <strong>SƠ ĐỒ TĨNH</strong> - không có animation workers di chuyển. 
              Để thấy quá trình huấn luyện, hãy nhấn Play và <strong>XEM BIỂU ĐỒ BÊN DƯỚI</strong> (đường Training Loss, Test Accuracy...). 
              Mỗi Round = 1 lần tất cả workers gửi gradients → server tổng hợp → cập nhật model.
            </p>
          </div>
        </div>

        {/* Animation Controls Bar */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={handleReset}
                className="p-2 rounded hover:bg-gray-100 transition-colors"
                title="Reset"
              >
                <RotateCcw className="w-4 h-4 text-gray-700" />
              </button>
              <button
                onClick={handleStepBackward}
                className="p-2 rounded hover:bg-gray-100 transition-colors"
                title="Step Backward"
              >
                <SkipBack className="w-4 h-4 text-gray-700" />
              </button>
              <button
                onClick={handlePlayPause}
                className="p-2 rounded bg-blue-600 hover:bg-blue-700 transition-colors"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <Pause className="w-5 h-5 text-white" />
                ) : (
                  <Play className="w-5 h-5 text-white" />
                )}
              </button>
              <button
                onClick={handleStepForward}
                className="p-2 rounded hover:bg-gray-100 transition-colors"
                title="Step Forward"
              >
                <SkipForward className="w-4 h-4 text-gray-700" />
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-sm">
                <span className="text-gray-600">Round:</span>{' '}
                <span className="font-semibold text-gray-900">{currentRound}</span>
                <span className="text-gray-400 mx-2">/</span>
                <span className="text-gray-600">{selectedRun.meta.rounds}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-600">Iteration:</span>{' '}
                <span className="font-semibold text-gray-900">{currentIteration}</span>
                <span className="text-gray-400 mx-2">/</span>
                <span className="text-gray-600">{maxIterations}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-sm text-gray-600">Speed:</label>
                <select
                  value={playbackSpeed}
                  onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value={1}>1x</option>
                  <option value={5}>5x</option>
                  <option value={10}>10x</option>
                  <option value={20}>20x</option>
                  <option value={50}>50x</option>
                </select>
              </div>
            </div>

            <div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showPartitionDemo}
                  onChange={(e) => setShowPartitionDemo(e.target.checked)}
                  className="rounded"
                />
                <span className="text-gray-700">Show Partition Demo</span>
              </label>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <input
              type="range"
              min={0}
              max={maxIterations - 1}
              value={currentIteration}
              onChange={(e) => setCurrentIteration(Number(e.target.value))}
              className="w-full"
            />
          </div>
        </div>

        <div className="grid grid-cols-12 gap-5">
          {/* Left Column - Controls */}
          <div className="col-span-3 space-y-5">
            <ControlPanel
              runs={runs}
              partitions={partitions}
              selectedRun={selectedRun}
              onRunSelect={(run) => {
                setSelectedRun(run);
                setCurrentIteration(0);
                setIsPlaying(false);
              }}
              currentIteration={currentIteration}
              onIterationChange={setCurrentIteration}
            />
            <MetaCard meta={selectedRun.meta} />
          </div>

          {/* Right Column - Visualizations */}
          <div className="col-span-9 space-y-5">
            {/* Partition Demo */}
            {showPartitionDemo && partition && (
              <PartitionDemo
                partitionType={partition}
                numWorkers={selectedRun.meta.byzantine_size + selectedRun.meta.honest_size}
                numClasses={10}
                alpha={1.0}
              />
            )}

            {/* Network Visualization */}
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-4">
                Network Topology
              </h2>
              <NetworkVizD3
                byzantineCount={selectedRun.meta.byzantine_size}
                totalWorkers={selectedRun.meta.byzantine_size + selectedRun.meta.honest_size}
                currentIteration={currentIteration}
                aggregator={aggregator}
                attack={attack}
                isAnimating={isPlaying}
                onWorkerHover={setHoveredWorker}
              />
            </div>

            {/* Training Metrics */}
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-base font-semibold text-gray-900 mb-4">
                Training Metrics
              </h2>
              <RunCharts
                iterations={selectedRun.iterations}
                currentIteration={currentIteration}
              />
            </div>

            {/* Current Metrics Display */}
            {selectedRun.iterations[currentIteration] && (
              <div className="bg-white border border-gray-200 rounded-lg p-5">
                <h2 className="text-base font-semibold text-gray-900 mb-4">
                  Current Iteration Metrics
                </h2>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-gray-600">Accuracy</div>
                    <div className="text-2xl font-bold text-green-600">
                      {(selectedRun.iterations[currentIteration].accuracy * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Loss</div>
                    <div className="text-2xl font-bold text-orange-600">
                      {selectedRun.iterations[currentIteration].loss.toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Learning Rate</div>
                    <div className="text-2xl font-bold text-blue-600">
                      {selectedRun.iterations[currentIteration].lr.toFixed(6)}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
