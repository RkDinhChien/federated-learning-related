'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, RotateCcw, AlertTriangle, Shield, Target, ArrowRight } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

// Real data from SR_MNIST experiments (n=10, b=1)
const HONEST_DISTRIBUTION = [7, 9, 6, 13, 10, 9, 10, 10, 13, 11]; // Percentage for each label 0-9

interface AttackPattern {
  name: string;
  description: string;
  category: string;
  transformations: Array<{ from: number; to: number; color: string; scale?: string }>;
  poisonedDist: number[];
  gradientScale?: number;
}

const ATTACK_PATTERNS: Record<string, AttackPattern> = {
  label_flipping: {
    name: "Label Flipping Attack",
    description: "Byzantine worker swaps specific label pairs to confuse the model",
    category: "Data Poisoning",
    transformations: [
      { from: 0, to: 1, color: "bg-red-100" },
      { from: 1, to: 0, color: "bg-red-100" },
      { from: 2, to: 3, color: "bg-orange-100" },
      { from: 3, to: 2, color: "bg-orange-100" },
      { from: 8, to: 9, color: "bg-yellow-100" }
    ],
    poisonedDist: [9, 7, 13, 6, 10, 9, 10, 10, 6, 15]
  },
  furthest_label_flipping: {
    name: "Furthest Label Flipping Attack",
    description: "Byzantine worker flips ALL labels to their furthest/opposite labels - more aggressive!",
    category: "Data Poisoning",
    transformations: [
      { from: 0, to: 5, color: "bg-red-200" },
      { from: 1, to: 6, color: "bg-red-200" },
      { from: 2, to: 7, color: "bg-orange-200" },
      { from: 3, to: 8, color: "bg-orange-200" },
      { from: 4, to: 9, color: "bg-yellow-200" },
      { from: 5, to: 0, color: "bg-green-200" },
      { from: 6, to: 1, color: "bg-green-200" },
      { from: 7, to: 2, color: "bg-blue-200" },
      { from: 8, to: 3, color: "bg-blue-200" },
      { from: 9, to: 4, color: "bg-purple-200" }
    ],
    poisonedDist: [9, 10, 10, 10, 9, 7, 9, 6, 13, 13]
  },
  gradient_scaling: {
    name: "Gradient Scaling Attack",
    description: "Byzantine worker sends 10x larger gradients to dominate aggregation",
    category: "Model Poisoning",
    transformations: [
      { from: 0, to: 0, color: "bg-purple-100", scale: "10x" }
    ],
    poisonedDist: HONEST_DISTRIBUTION, // Same distribution but scaled gradients
    gradientScale: 10
  },
  sign_flipping: {
    name: "Sign Flipping Attack",
    description: "Byzantine worker flips gradient signs to push model in opposite direction",
    category: "Model Poisoning",
    transformations: [
      { from: 0, to: 0, color: "bg-pink-100", scale: "-1x" }
    ],
    poisonedDist: HONEST_DISTRIBUTION, // Same distribution but negated gradients
    gradientScale: -1
  }
};

export default function AttackDemo() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [attackType, setAttackType] = useState<'label_flipping' | 'furthest_label_flipping' | 'gradient_scaling' | 'sign_flipping'>('label_flipping');
  const [currentStep, setCurrentStep] = useState(0);
  const [byzantineWorker, setByzantineWorker] = useState(2); // Which worker is Byzantine
  const [displayDist, setDisplayDist] = useState<number[]>(HONEST_DISTRIBUTION); // Animated distribution
  const maxSteps = 30; // 30 steps = 10 workers × 3 steps each

  const attack = ATTACK_PATTERNS[attackType];

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        const next = prev + 1;
        
        if (next >= maxSteps) {
          setIsPlaying(false);
          return 0; // Loop back
        }
        
        // Gradually apply attack transformations over first 10 steps
        if (next > 0 && next <= 10) {
          const progress = next / 10; // 0 to 1
          const newDist = HONEST_DISTRIBUTION.map((val, idx) => {
            const targetVal = attack.poisonedDist[idx];
            return Math.round(val + (targetVal - val) * progress);
          });
          setDisplayDist(newDist);
        }
        
        // Rotate Byzantine worker every 3 steps
        if (next % 3 === 0) {
          const rotation = Math.floor(next / 3) % 10;
          setByzantineWorker(rotation);
        }
        
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying, maxSteps, attack.poisonedDist]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setByzantineWorker(2);
    setDisplayDist(HONEST_DISTRIBUTION); // Reset to original
  };

  // Calculate max value for scaling bars
  const maxValue = Math.max(...HONEST_DISTRIBUTION, ...attack.poisonedDist);

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-block px-4 py-2 bg-red-100 rounded-full text-sm font-medium mb-2">
          Security Analysis
        </div>
        <h1 className="text-3xl font-bold">Attack Demo</h1>
        <p className="text-gray-600 text-base">
          See how Byzantine workers manipulate training data
        </p>
      </div>

      {/* Quick Guide - Explanation */}
      <Alert className="border-purple-200 bg-purple-50">
        <AlertTriangle className="h-4 w-4 text-purple-600" />
        <AlertDescription>
          <p className="font-semibold text-purple-900 mb-3">Hướng Dẫn Nhanh - Cách Nhận Biết Tấn Công:</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div className="bg-blue-100 p-3 rounded-lg border border-blue-200">
              <p className="font-semibold text-blue-900 mb-1">Bước 1: Chọn Loại Tấn Công</p>
              <p className="text-xs text-blue-700">Mỗi loại có cách phá hoại khác nhau (đổi nhãn, phóng đại gradient...)</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-lg border border-purple-200">
              <p className="font-semibold text-purple-900 mb-1">Bước 2: Nhấn Play</p>
              <p className="text-xs text-purple-700">Xem Worker 2 "Turned" → chuyển sang ATTACKING → dữ liệu BỊ ĐỘC</p>
            </div>
            <div className="bg-green-100 p-3 rounded-lg border border-green-200">
              <p className="font-semibold text-green-900 mb-1">Bước 3: So Sánh 2 Biểu Đồ</p>
              <p className="text-xs text-green-700">TRÁI (xanh) = bình thường | PHẢI (đỏ) = bị tấn công → các cột ĐỔI MÀU ĐỎ</p>
            </div>
          </div>
          <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-xs text-yellow-800">
              <strong>Ý Nghĩa:</strong> Worker chạy từ TRÁI → PHẢI = worker đó bị "lật" thành Byzantine → 
              gửi dữ liệu độc hại. Các số <span className="text-red-600 font-bold">ĐỎ</span> trên biểu đồ PHẢI = 
              phần trăm bị thay đổi bởi tấn công (ví dụ: nhãn 0↔1, 8↔9).
            </p>
          </div>
        </AlertDescription>
      </Alert>

      {/* Attack Explanation */}
      <Alert>
        <AlertTriangle className="h-5 w-5" />
        <AlertDescription className="ml-2">
          <div className="space-y-2">
            <p className="font-semibold text-lg">{attack.name}</p>
            <p>{attack.description}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {attack.transformations.map((t, i) => (
                <Badge key={i} variant="outline" className={`${t.color} px-3 py-1`}>
                  Label {t.from} → {t.to}
                </Badge>
              ))}
            </div>
          </div>
        </AlertDescription>
      </Alert>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Simulation Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Attack Type Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Attack Type:</label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant={attackType === 'label_flipping' ? 'default' : 'outline'}
                onClick={() => setAttackType('label_flipping')}
                disabled={isPlaying}
                className="justify-start"
              >
                <Target className="mr-2 h-4 w-4" />
                Label Flipping
              </Button>
              <Button
                variant={attackType === 'furthest_label_flipping' ? 'default' : 'outline'}
                onClick={() => setAttackType('furthest_label_flipping')}
                disabled={isPlaying}
                className="justify-start"
              >
                <AlertTriangle className="mr-2 h-4 w-4" />
                Furthest Label
              </Button>
              <Button
                variant={attackType === 'gradient_scaling' ? 'default' : 'outline'}
                onClick={() => setAttackType('gradient_scaling')}
                disabled={isPlaying}
                className="justify-start"
              >
                <ArrowRight className="mr-2 h-4 w-4 rotate-45" />
                Gradient Scaling
              </Button>
              <Button
                variant={attackType === 'sign_flipping' ? 'default' : 'outline'}
                onClick={() => setAttackType('sign_flipping')}
                disabled={isPlaying}
                className="justify-start"
              >
                <RotateCcw className="mr-2 h-4 w-4" />
                Sign Flipping
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              <Badge variant="outline" className="mr-2">{attack.category}</Badge>
              {attack.description}
            </p>
          </div>

          {/* Playback Controls */}
          <div className="flex gap-2 items-center">
            <Button onClick={() => setIsPlaying(!isPlaying)}>
              {isPlaying ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Play
                </>
              )}
            </Button>
            <Button onClick={handleReset} variant="outline">
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <div className="ml-auto text-sm text-muted-foreground">
              Step: {currentStep} / {maxSteps} | Byzantine Worker: #{byzantineWorker}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workers Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Before Attack - Honest Workers */}
        <Card className="border-green-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-green-600" />
              <CardTitle>Honest Workers (9/10)</CardTitle>
            </div>
            <CardDescription>
              Normal label distribution - unmodified training data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Label Distribution Chart */}
              <div className="space-y-2">
                <p className="text-sm font-medium">Label Distribution:</p>
                <div className="flex items-end justify-between gap-1 h-40 bg-muted/30 p-3 rounded-lg">
                  {HONEST_DISTRIBUTION.map((value, idx) => {
                    const heightPercent = (value / maxValue) * 100;
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <div className="text-xs font-medium text-muted-foreground">
                          {value}%
                        </div>
                        <div 
                          className="w-full bg-green-500 rounded-t transition-all duration-300"
                          style={{ height: `${heightPercent}%` }}
                        />
                        <div className="text-xs font-medium">{idx}</div>
                      </div>
                    );
                  })}
                </div>
                <div className="text-center text-xs text-muted-foreground mt-2">
                  Labels (0-9)
                </div>
              </div>

              {/* Worker Cards */}
              <div className="grid grid-cols-5 gap-2">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div
                    key={idx}
                    className={`
                      p-3 rounded-lg border-2 text-center transition-all
                      ${idx === byzantineWorker ? 'border-red-500 opacity-40' : 'border-green-500'}
                    `}
                  >
                    <Shield className="h-6 w-6 mx-auto mb-1 text-green-600" />
                    <div className="text-xs font-medium">Worker {idx}</div>
                    {idx === byzantineWorker && (
                      <Badge variant="destructive" className="text-[10px] mt-1">Turned</Badge>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* After Attack - Byzantine Worker */}
        <Card className="border-red-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <CardTitle>Byzantine Worker (1/10)</CardTitle>
            </div>
            <CardDescription>
              Poisoned label distribution - manipulated training data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Label Distribution Chart */}
              <div className="space-y-2">
                <p className="text-sm font-medium">
                  {attack.gradientScale 
                    ? `Gradient Magnitude (${attack.gradientScale}x)` 
                    : 'Poisoned Distribution:'
                  }
                </p>
                <div className="flex items-end justify-between gap-1 h-40 bg-muted/30 p-3 rounded-lg relative">
                  {displayDist.map((value, idx) => {
                    const heightPercent = (value / maxValue) * 100;
                    const originalValue = HONEST_DISTRIBUTION[idx];
                    const isChanged = value !== originalValue;
                    
                    // For gradient attacks, show scale effect
                    const displayHeight = attack.gradientScale 
                      ? Math.min(heightPercent * Math.abs(attack.gradientScale) / 2, 100)
                      : heightPercent;
                    
                    // Check if currently animating this label
                    const isAnimating = currentStep > 0 && currentStep <= maxSteps;
                    
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1 relative">
                        {/* BEFORE value (crossed out if changed) */}
                        {isChanged && isAnimating && (
                          <div className="absolute -top-6 text-[10px] text-gray-400 line-through">
                            {originalValue}%
                          </div>
                        )}
                        
                        {/* AFTER value (highlighted if changed) */}
                        <div className={`text-xs font-medium transition-all ${
                          attack.gradientScale 
                            ? 'text-purple-600 font-bold' 
                            : isChanged ? 'text-red-600 font-bold animate-pulse' : 'text-muted-foreground'
                        }`}>
                          {attack.gradientScale 
                            ? `${(value * Math.abs(attack.gradientScale)).toFixed(0)}%`
                            : `${value}%`
                          }
                        </div>
                        
                        {/* Bar with animation */}
                        <div 
                          className={`w-full rounded-t transition-all duration-500 ${
                            attack.gradientScale && attack.gradientScale < 0
                              ? 'bg-pink-500'
                              : attack.gradientScale && attack.gradientScale > 1
                              ? 'bg-purple-500'
                              : isChanged 
                              ? 'bg-red-500 shadow-lg' 
                              : 'bg-orange-300'
                          } ${isChanged && isAnimating ? 'animate-bounce' : ''}`}
                          style={{ height: `${displayHeight}%` }}
                        />
                        
                        {/* Label number with highlight */}
                        <div className={`text-xs font-medium transition-all ${
                          attack.gradientScale ? 'bg-purple-200 px-1 rounded' : isChanged ? 'bg-yellow-300 px-2 rounded font-bold' : ''
                        }`}>
                          {idx}
                        </div>
                        
                        {/* Change arrow indicator */}
                        {isChanged && isAnimating && !attack.gradientScale && (
                          <div className="absolute -bottom-8 text-xs text-red-600 font-bold">
                            {originalValue > value ? '↓' : '↑'}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {/* Legend explaining the changes */}
                {currentStep > 0 && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs">
                    <p className="font-semibold text-red-900 mb-2">Những gì đã thay đổi:</p>
                    <div className="grid grid-cols-1 gap-2">
                      {attack.transformations.map((t, i) => (
                        <div key={i} className={`p-2 ${t.color} rounded border`}>
                          {t.scale ? (
                            <span className="font-mono">
                              Gradient ×{t.scale}
                            </span>
                          ) : (
                            <div className="font-mono text-xs">
                              <span className="font-semibold">Nhãn {t.from}</span> ({HONEST_DISTRIBUTION[t.from]}%) 
                              <span className="text-red-600 mx-1">→ bị đổi thành →</span> 
                              <span className="font-semibold">Nhãn {t.to}</span>
                              <div className="text-[10px] text-gray-600 mt-1">
                                Ảnh hưởng: Cột {t.from} giảm, cột {t.to} tăng lên
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="text-center text-xs text-muted-foreground mt-2">
                  {attack.gradientScale ? 'Gradient Components' : 'Labels (0-9)'}
                </div>
              </div>

              {/* Worker Cards */}
              <div className="grid grid-cols-5 gap-2">
                {Array.from({ length: 10 }).map((_, idx) => (
                  <div
                    key={idx}
                    className={`
                      p-3 rounded-lg border-2 text-center transition-all
                      ${idx === byzantineWorker 
                        ? 'border-red-500 bg-red-50 scale-105 shadow-lg' 
                        : 'border-gray-300 opacity-30'
                      }
                    `}
                  >
                    {idx === byzantineWorker ? (
                      <>
                        <AlertTriangle className="h-6 w-6 mx-auto mb-1 text-red-600" />
                        <div className="text-xs font-bold">Worker {idx}</div>
                        <Badge variant="destructive" className="text-[10px] mt-1">ATTACKING</Badge>
                      </>
                    ) : (
                      <>
                        <Shield className="h-6 w-6 mx-auto mb-1 text-gray-400" />
                        <div className="text-xs font-medium text-gray-400">Worker {idx}</div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Attack Impact Details */}
      <Card className="border-yellow-200 bg-yellow-50/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ArrowRight className="h-5 w-5" />
            Attack Impact Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Attack Type & Method */}
            <div className="space-y-2">
              <p className="font-medium text-sm">Attack Method:</p>
              <Badge variant="outline" className="mb-2">{attack.category}</Badge>
              <div className="flex flex-wrap gap-1">
                {attack.gradientScale ? (
                  <Badge className="bg-purple-100 text-purple-800">
                    Gradient Scale: {attack.gradientScale}x
                  </Badge>
                ) : (
                  attack.transformations.map((t, i) => (
                    <Badge key={i} className={`${t.color}`}>
                      {t.scale || `${t.from}→${t.to}`}
                    </Badge>
                  ))
                )}
              </div>
            </div>

            {/* Attack Severity */}
            <div className="space-y-2">
              <p className="font-medium text-sm">Attack Severity:</p>
              <div className="text-2xl font-bold text-red-600">
                {attack.gradientScale 
                  ? `${Math.abs(attack.gradientScale)}x`
                  : `${attack.transformations.length}/10`
                }
              </div>
              <p className="text-xs text-muted-foreground">
                {attack.gradientScale 
                  ? `Gradient magnitude ${attack.gradientScale > 0 ? 'amplified' : 'reversed'}`
                  : `${Math.round((attack.transformations.length / 10) * 100)}% of label space compromised`
                }
              </p>
            </div>

            {/* Model Impact */}
            <div className="space-y-2">
              <p className="font-medium text-sm">Potential Impact:</p>
              <div className="space-y-1 text-sm">
                {attack.gradientScale ? (
                  <>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-600" />
                      <span>{attack.gradientScale > 0 ? 'Model divergence' : 'Reverse convergence'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-orange-600" />
                      <span>Aggregation dominated</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-600" />
                      <span>Performance collapse</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500" />
                      <span>Reduced model accuracy</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-orange-500" />
                      <span>Biased predictions</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-yellow-500" />
                      <span>Requires robust aggregation</span>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* How Aggregators Defend */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-green-600" />
            How Robust Aggregators Defend Against This Attack
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                name: "Trimmed Mean",
                desc: "Removes extreme updates (top/bottom values)",
                effectiveness: "Moderate"
              },
              {
                name: "Coordinate-wise Clipping",
                desc: "Clips updates exceeding threshold τ",
                effectiveness: "Good"
              },
              {
                name: "LFighter",
                desc: "Uses loss function to identify malicious updates",
                effectiveness: "Very Good"
              },
              {
                name: "FABA",
                desc: "Byzantine-resilient aggregation with adaptive filtering",
                effectiveness: "Excellent"
              }
            ].map((agg, idx) => (
              <div key={idx} className="p-4 border rounded-lg space-y-2">
                <p className="font-semibold">{agg.name}</p>
                <p className="text-xs text-muted-foreground">{agg.desc}</p>
                <Badge variant="outline" className="text-xs">
                  {agg.effectiveness}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
