'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, RotateCcw, AlertTriangle, Shield, Target } from 'lucide-react';

interface LabelDistribution {
  original: number[];
  flipped: number[];
}

interface Worker {
  id: number;
  isByzantine: boolean;
  labelDist: LabelDistribution;
  isAttacking: boolean;
}

export default function AttackDemo() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [attackType, setAttackType] = useState<'label_flipping' | 'furthest_label_flipping'>('label_flipping');
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [byzantineCount] = useState(1); // Real data: 1 Byzantine worker
  const [currentStep, setCurrentStep] = useState(0);
  const [showPoisonedLabels, setShowPoisonedLabels] = useState(false);
  const [byzantineIndices, setByzantineIndices] = useState<number[]>([0]); // Rotating Byzantine worker
  const maxSteps = 30; // 30 steps allows Byzantine worker to rotate through all 10 workers

  // Initialize workers
  useEffect(() => {
    const initialWorkers: Worker[] = Array.from({ length: 10 }, (_, i) => {
      const isByzantine = byzantineIndices.includes(i);
      const original = generateLabelDistribution(false);
      
      return {
        id: i,
        isByzantine,
        labelDist: {
          original,
          flipped: isByzantine ? flipLabels(original, attackType) : original
        },
        isAttacking: false
      };
    });
    
    setWorkers(initialWorkers);
  }, [byzantineIndices, attackType]);

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        const nextStep = prev + 1;
        
        if (nextStep >= maxSteps) {
          setIsPlaying(false);
          return maxSteps;
        }
        
        // Show poisoned labels when attack starts
        if (nextStep === 1) {
          setShowPoisonedLabels(true);
        }
        
        // Rotate Byzantine workers every 3 steps
        if (nextStep % 3 === 0) {
          const rotation = Math.floor(nextStep / 3);
          const newIndex = rotation % 10; // Single Byzantine worker rotating 0→1→2→3...→9
          setByzantineIndices([newIndex]);
        }
        
        // Trigger attack animation every 2 steps
        setWorkers(current => 
          current.map(w => ({
            ...w,
            isByzantine: byzantineIndices.includes(w.id),
            isAttacking: byzantineIndices.includes(w.id) && nextStep % 2 === 0,
            labelDist: {
              original: w.labelDist.original,
              flipped: byzantineIndices.includes(w.id) 
                ? flipLabels(w.labelDist.original, attackType) 
                : w.labelDist.original
            }
          }))
        );
        
        return nextStep;
      });
    }, 1000); // 1 second per step

    return () => clearInterval(interval);
  }, [isPlaying, maxSteps, byzantineIndices, attackType]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setShowPoisonedLabels(false);
    setByzantineIndices([0]); // Reset to worker 0
    setWorkers(current => current.map(w => ({ ...w, isAttacking: false })));
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const switchAttackType = (type: 'label_flipping' | 'furthest_label_flipping') => {
    setAttackType(type);
    setByzantineIndices([0]); // Reset to worker 0
    handleReset();
  };

  return (
    <div className="space-y-6">
      {/* Explanation Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-blue-600" />
            How Byzantine Attack Works
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="text-sm space-y-2">
            <p className="font-semibold text-gray-900">🎯 Attack Goal:</p>
            <p className="text-gray-700">Malicious workers send WRONG gradients to poison the global model</p>
            
            <p className="font-semibold text-gray-900 mt-4">🔴 {attackType === 'label_flipping' ? 'Label Flipping' : 'Furthest Label Flipping'}:</p>
            {attackType === 'label_flipping' ? (
              <div className="bg-white p-3 rounded border border-blue-200">
                <p className="text-gray-700 mb-2">Swap labels symmetrically:</p>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div>0 ↔ 1</div>
                  <div>2 ↔ 3</div>
                  <div>4 ↔ 5</div>
                  <div>6 ↔ 7</div>
                  <div>8 ↔ 9</div>
                </div>
              </div>
            ) : (
              <div className="bg-white p-3 rounded border border-blue-200">
                <p className="text-gray-700 mb-2">Flip to furthest label:</p>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div>0 → 9</div>
                  <div>1 → 8</div>
                  <div>2 → 7</div>
                  <div>3 → 6</div>
                  <div>4 → 5</div>
                </div>
              </div>
            )}
            
            <p className="font-semibold text-gray-900 mt-4">📊 Visual Guide:</p>
            <ul className="list-disc list-inside text-gray-700 space-y-1">
              <li><span className="text-red-600 font-semibold">RED Worker</span> = Byzantine (malicious)</li>
              <li><span className="text-blue-600 font-semibold">BLUE Worker</span> = Honest</li>
              <li>Compare <span className="bg-blue-100 px-1 rounded">Original Labels</span> vs <span className="bg-red-100 px-1 rounded">Poisoned Labels</span></li>
              <li>Byzantine worker rotates every 3 steps: 0→1→2→3...→9</li>
              <li><span className="bg-yellow-200 px-1 rounded font-semibold">Yellow highlight</span> = Labels that were changed</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl">Byzantine Attack Animation</CardTitle>
              <CardDescription>
                Currently attacking: Worker {byzantineIndices[0]} 
                {currentStep > 0 && ` (${attackType === 'label_flipping' ? 'Symmetric swap' : 'Furthest flip'})`}
              </CardDescription>
            </div>
            <Badge variant={currentStep === 0 ? 'secondary' : currentStep < maxSteps ? 'default' : 'destructive'} className="text-lg px-4 py-2">
              Step {currentStep} / {maxSteps}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Button
              onClick={togglePlay}
              disabled={currentStep >= maxSteps}
            >
              {isPlaying ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              {isPlaying ? 'Pause' : 'Play'}
            </Button>
            
            <Button onClick={handleReset} variant="outline">
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>

            <div className="flex gap-2 ml-auto">
              <Button
                variant={attackType === 'label_flipping' ? 'default' : 'outline'}
                onClick={() => switchAttackType('label_flipping')}
              >
                Label Flipping
              </Button>
              <Button
                variant={attackType === 'furthest_label_flipping' ? 'default' : 'outline'}
                onClick={() => switchAttackType('furthest_label_flipping')}
              >
                Furthest Label Flipping
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workers Grid */}
      <div className="grid grid-cols-5 gap-4">
        {workers.map(worker => (
          <Card 
            key={worker.id} 
            className={`transition-all duration-300 ${
              worker.isAttacking 
                ? 'ring-4 ring-red-500 shadow-xl shadow-red-500/50 scale-105' 
                : worker.isByzantine 
                  ? 'border-red-300' 
                  : 'border-blue-300'
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Worker {worker.id}</CardTitle>
                {worker.isByzantine ? (
                  <AlertTriangle className="h-4 w-4 text-red-500" />
                ) : (
                  <Shield className="h-4 w-4 text-blue-500" />
                )}
              </div>
              <Badge variant={worker.isByzantine ? 'destructive' : 'default'} className="text-xs">
                {worker.isByzantine ? 'BYZANTINE' : 'HONEST'}
              </Badge>
            </CardHeader>
            <CardContent className="overflow-hidden">
              {/* Original Distribution */}
              <div className="mb-3">
                <div className="text-xs text-gray-600 mb-1 flex items-center gap-1">
                  <Target className="h-3 w-3" />
                  Original Labels (Trung thực)
                </div>
                <div className="flex gap-1 h-20 items-end overflow-hidden">
                  {worker.labelDist.original.map((val, idx) => {
                    const percentage = (val * 100).toFixed(0);
                    const hasData = val > 0.05;
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center" title={`Label ${idx}: ${percentage}%`}>
                        <div 
                          className="w-full bg-blue-400 rounded-t transition-all hover:bg-blue-500"
                          style={{ height: `${val * 100}%`, minHeight: val > 0 ? '4px' : '0' }}
                        />
                      </div>
                    );
                  })}
                </div>
                <div className="flex gap-1 mt-1">
                  {worker.labelDist.original.map((val, idx) => {
                    const percentage = (val * 100).toFixed(0);
                    const hasData = val > 0.05;
                    return (
                      <div key={idx} className="flex-1 text-center text-[10px] font-bold text-blue-700">
                        {hasData ? `${percentage}%` : ''}
                      </div>
                    );
                  })}
                </div>
                <div className="flex gap-1 mt-0.5">
                  {worker.labelDist.original.map((_, idx) => (
                    <div key={idx} className="flex-1 text-center text-xs font-semibold text-gray-700">{idx}</div>
                  ))}
                </div>
              </div>

              {/* Attack Arrow */}
              {worker.isByzantine && currentStep > 0 && (
                <div className="flex justify-center my-2">
                  <div className={`text-red-500 font-bold transition-all ${worker.isAttacking ? 'scale-150 animate-pulse' : ''}`}>
                    ⬇ ATTACK ⬇
                  </div>
                </div>
              )}

              {/* Flipped Distribution (only show for Byzantine after attack starts) */}
              {worker.isByzantine && currentStep > 0 && (
                <div>
                  <div className="text-xs text-red-600 mb-1 flex items-center gap-1 font-semibold">
                    <AlertTriangle className="h-3 w-3" />
                    Poisoned Labels (Bị tấn công)
                  </div>
                  <div className="flex gap-1 h-20 items-end overflow-hidden">
                    {worker.labelDist.flipped.map((val, idx) => {
                      const percentage = (val * 100).toFixed(0);
                      const originalVal = worker.labelDist.original[idx];
                      const isDifferent = Math.abs(val - originalVal) > 0.05;
                      const hasData = val > 0.05;
                      return (
                        <div key={idx} className="flex-1 flex flex-col items-center" title={`Label ${idx}: ${percentage}%${isDifferent ? ' (CHANGED!)' : ''}`}>
                          <div 
                            className={`w-full rounded-t transition-all ${
                              isDifferent 
                                ? 'bg-red-600 ring-2 ring-yellow-400 animate-pulse' 
                                : 'bg-red-500'
                            }`}
                            style={{ height: `${val * 100}%`, minHeight: val > 0 ? '4px' : '0' }}
                          />
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex gap-1 mt-1">
                    {worker.labelDist.flipped.map((val, idx) => {
                      const percentage = (val * 100).toFixed(0);
                      const originalVal = worker.labelDist.original[idx];
                      const isDifferent = Math.abs(val - originalVal) > 0.05;
                      const hasData = val > 0.05;
                      return (
                        <div key={idx} className={`flex-1 text-center text-[10px] font-bold ${
                          isDifferent ? 'text-red-700 animate-pulse' : 'text-red-600'
                        }`}>
                          {hasData ? `${percentage}%` : ''}
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex gap-1 mt-0.5">
                    {worker.labelDist.flipped.map((val, idx) => {
                      const originalVal = worker.labelDist.original[idx];
                      const isDifferent = Math.abs(val - originalVal) > 0.05;
                      return (
                        <div key={idx} className={`flex-1 text-center text-xs font-semibold ${
                          isDifferent ? 'text-red-600 bg-yellow-200 rounded' : 'text-gray-700'
                        }`}>
                          {idx}
                        </div>
                      );
                    })}
                  </div>
                  
                  {/* Explain what changed */}
                  {showPoisonedLabels && (
                    <div className="mt-3 p-3 bg-yellow-50 border-2 border-yellow-400 rounded-lg">
                      <div className="flex items-center gap-2 mb-2 text-sm font-semibold text-gray-900">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <span>Labels Changed by Byzantine Worker:</span>
                      </div>
                      <div className="space-y-1.5">
                        {worker.labelDist.original.map((origVal, idx) => {
                          const flippedVal = worker.labelDist.flipped[idx];
                          const isDifferent = Math.abs(flippedVal - origVal) > 0.05;
                          if (!isDifferent || origVal < 0.05) return null;
                          
                          const origPct = (origVal * 100).toFixed(0);
                          
                          // Find where the data moved to
                          let movedTo = -1;
                          if (attackType === 'label_flipping') {
                            movedTo = idx % 2 === 0 ? idx + 1 : idx - 1;
                          } else {
                            movedTo = 9 - idx;
                          }
                          
                          return (
                            <div key={idx} className="flex items-center gap-2 py-1.5 px-2 bg-white rounded-md border border-gray-200">
                              <span className="inline-flex items-center justify-center min-w-[70px] bg-blue-100 text-blue-700 font-mono text-xs px-2 py-1 rounded font-semibold">
                                Label {idx}
                              </span>
                              <span className="text-blue-600 font-bold min-w-[38px] text-right">{origPct}%</span>
                              <span className="text-gray-400 font-bold">→</span>
                              <span className="inline-flex items-center justify-center min-w-[70px] bg-red-100 text-red-700 font-mono text-xs px-2 py-1 rounded font-semibold">
                                Label {movedTo}
                              </span>
                              <span className="text-red-600 font-bold min-w-[38px] text-right">{origPct}%</span>
                              <span className="text-gray-500 text-xs ml-auto">(flipped)</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Explanation */}
      <Card>
        <CardHeader>
          <CardTitle>Attack Mechanism</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <h4 className="font-semibold text-sm mb-1">Label Flipping Attack:</h4>
              <p className="text-sm text-gray-600">
                Byzantine workers flip labels to their opposite class (e.g., 0→1, 1→0, etc.). 
                This creates systematic bias in the global model.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-sm mb-1">Furthest Label Flipping:</h4>
              <p className="text-sm text-gray-600">
                A more sophisticated attack where labels are flipped to the most distant class 
                (e.g., 0→9, 5→4 for MNIST). This maximizes model confusion.
              </p>
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <h4 className="font-semibold text-sm mb-1 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-yellow-600" />
                Impact on Federated Learning:
              </h4>
              <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                <li>Byzantine workers send poisoned gradients to the parameter server</li>
                <li>Without robust aggregation, the global model performance degrades</li>
                <li>Aggregators like FABA, LFighter, and CC can detect and filter these attacks</li>
                <li>The more Byzantine workers, the stronger the attack impact</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper functions
function generateLabelDistribution(isByzantine: boolean): number[] {
  const dist = new Array(10).fill(0);
  const samples = 100;
  
  for (let i = 0; i < samples; i++) {
    const label = Math.floor(Math.random() * 10);
    dist[label]++;
  }
  
  // Normalize
  const sum = dist.reduce((a, b) => a + b, 0);
  return dist.map(v => v / sum);
}

function flipLabels(original: number[], attackType: 'label_flipping' | 'furthest_label_flipping'): number[] {
  const flipped = new Array(10).fill(0);
  
  if (attackType === 'label_flipping') {
    // Simple flip: 0→1, 1→0, 2→3, 3→2, etc.
    for (let i = 0; i < 10; i++) {
      const targetLabel = i % 2 === 0 ? i + 1 : i - 1;
      if (targetLabel >= 0 && targetLabel < 10) {
        flipped[targetLabel] = original[i];
      }
    }
  } else {
    // Furthest label: 0→9, 1→8, 2→7, etc.
    for (let i = 0; i < 10; i++) {
      const targetLabel = 9 - i;
      flipped[targetLabel] = original[i];
    }
  }
  
  return flipped;
}
