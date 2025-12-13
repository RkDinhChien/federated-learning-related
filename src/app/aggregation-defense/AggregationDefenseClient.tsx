'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Pause, RotateCcw, Shield, AlertTriangle, CheckCircle, XCircle, TrendingUp, Info } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Real aggregator algorithms
const AGGREGATORS = {
  mean: {
    name: "Mean (Baseline)",
    description: "Simple average of all worker updates - VULNERABLE to Byzantine attacks",
    color: "bg-red-100 text-red-800",
    borderColor: "border-red-300",
    icon: XCircle,
    isRobust: false,
    method: (updates: number[], _?: any) => {
      return updates.reduce((a, b) => a + b, 0) / updates.length;
    }
  },
  trimmed_mean: {
    name: "Trimmed Mean",
    description: "Remove top & bottom 20% extreme values, then average - MODERATE defense",
    color: "bg-yellow-100 text-yellow-800",
    borderColor: "border-yellow-300",
    icon: CheckCircle,
    isRobust: true,
    method: (updates: number[], _?: any) => {
      const sorted = [...updates].sort((a, b) => a - b);
      const trimCount = Math.floor(updates.length * 0.2);
      const trimmed = sorted.slice(trimCount, -trimCount || undefined);
      return trimmed.reduce((a, b) => a + b, 0) / trimmed.length;
    }
  },
  cc: {
    name: "Coordinate-wise Clipping (CC)",
    description: "Clip updates exceeding threshold τ=0.3 - GOOD defense against extreme values",
    color: "bg-blue-100 text-blue-800",
    borderColor: "border-blue-300",
    icon: CheckCircle,
    isRobust: true,
    method: (updates: number[], tau: number = 0.3) => {
      const median = [...updates].sort((a, b) => a - b)[Math.floor(updates.length / 2)];
      const clipped = updates.map(u => {
        const diff = u - median;
        if (Math.abs(diff) > tau) {
          return median + Math.sign(diff) * tau;
        }
        return u;
      });
      return clipped.reduce((a, b) => a + b, 0) / clipped.length;
    }
  },
  lfighter: {
    name: "LFighter",
    description: "Use loss function to detect malicious updates - VERY GOOD defense",
    color: "bg-green-100 text-green-800",
    borderColor: "border-green-300",
    icon: CheckCircle,
    isRobust: true,
    method: (updates: number[], losses?: number[]) => {
      if (!losses) return updates.reduce((a, b) => a + b, 0) / updates.length;
      // Filter out updates with suspiciously low loss (likely poisoned)
      const avgLoss = losses.reduce((a, b) => a + b, 0) / losses.length;
      const filtered = updates.filter((_, i) => losses[i] >= avgLoss * 0.8);
      return filtered.reduce((a, b) => a + b, 0) / filtered.length;
    }
  },
  faba: {
    name: "FABA",
    description: "Byzantine-resilient with adaptive filtering - EXCELLENT defense",
    color: "bg-purple-100 text-purple-800",
    borderColor: "border-purple-300",
    icon: Shield,
    isRobust: true,
    method: (updates: number[], _?: any) => {
      // FABA: iteratively remove outliers based on distance from median
      let remaining = [...updates];
      for (let iter = 0; iter < 2; iter++) {
        const sorted = [...remaining].sort((a, b) => a - b);
        const median = sorted[Math.floor(sorted.length / 2)];
        const mad = sorted.map(x => Math.abs(x - median)).sort((a, b) => a - b)[Math.floor(sorted.length / 2)];
        remaining = remaining.filter(x => Math.abs(x - median) <= 2.5 * mad);
      }
      return remaining.reduce((a, b) => a + b, 0) / remaining.length;
    }
  }
};

// Simulated worker updates (gradient values)
const HONEST_UPDATE_RANGE = { min: 0.8, max: 1.2 }; // Normal gradient magnitude
const BYZANTINE_UPDATE_SCALE = 5; // Byzantine sends 5x larger updates to poison

export default function AggregationDefenseClient() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedAggregator, setSelectedAggregator] = useState<keyof typeof AGGREGATORS>('mean');
  const [workerUpdates, setWorkerUpdates] = useState<number[]>([]);
  const [byzantineWorker, setByzantineWorker] = useState(0);
  const [aggregatedValue, setAggregatedValue] = useState<number | null>(null);
  const [history, setHistory] = useState<{step: number, value: number, aggregator: string}[]>([]);
  const maxSteps = 30;

  const aggregator = AGGREGATORS[selectedAggregator];
  const Icon = aggregator.icon;

  // Generate worker updates
  const generateUpdates = (byzantineIdx: number) => {
    const updates = Array.from({ length: 10 }, (_, i) => {
      if (i === byzantineIdx) {
        // Byzantine: send poisoned update (5x larger)
        return (Math.random() * 0.5 + 1.0) * BYZANTINE_UPDATE_SCALE;
      } else {
        // Honest: normal gradient
        return Math.random() * (HONEST_UPDATE_RANGE.max - HONEST_UPDATE_RANGE.min) + HONEST_UPDATE_RANGE.min;
      }
    });
    return updates;
  };

  // Simulate loss values for LFighter
  const generateLosses = (updates: number[]) => {
    return updates.map(u => {
      // Byzantine updates result in higher loss
      if (u > 3) return Math.random() * 0.5 + 0.2; // Low loss (suspicious)
      return Math.random() * 0.3 + 0.8; // Normal loss
    });
  };

  // Animation loop
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        const next = prev + 1;
        
        if (next >= maxSteps) {
          setIsPlaying(false);
          return 0;
        }
        
        // Rotate Byzantine worker every 3 steps
        if (next % 3 === 0) {
          const newByzIdx = Math.floor(next / 3) % 10;
          setByzantineWorker(newByzIdx);
        }
        
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPlaying]);

  // Update worker values and aggregate
  useEffect(() => {
    const updates = generateUpdates(byzantineWorker);
    setWorkerUpdates(updates);

    // Apply aggregator
    let result: number;
    if (selectedAggregator === 'lfighter') {
      const losses = generateLosses(updates);
      result = aggregator.method(updates, losses);
    } else if (selectedAggregator === 'cc') {
      result = aggregator.method(updates, 0.3);
    } else {
      result = aggregator.method(updates);
    }
    
    setAggregatedValue(result);
    
    // Add to history
    if (currentStep > 0) {
      setHistory(prev => [...prev, { 
        step: currentStep, 
        value: result, 
        aggregator: selectedAggregator 
      }].slice(-20)); // Keep last 20 points
    }
  }, [byzantineWorker, selectedAggregator, currentStep]);

  const handleReset = () => {
    setIsPlaying(false);
    setCurrentStep(0);
    setByzantineWorker(0);
    setHistory([]);
  };

  const expectedHonestValue = 1.0; // Expected honest gradient magnitude
  const isPoisoned = aggregatedValue && Math.abs(aggregatedValue - expectedHonestValue) > 0.5;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-3">
        <div className="inline-block px-4 py-2 bg-green-100 rounded-full text-sm font-medium mb-2">
          🛡️ Defense Mechanisms
        </div>
        <h1 className="text-3xl font-bold">Aggregation Defense</h1>
        <p className="text-gray-600 text-base">
          Compare 5 robust aggregators against attacks
        </p>
      </div>

      {/* Key Concept Alert */}
      <Alert className="border-blue-200 bg-blue-50 rounded-2xl">
        <Info className="h-5 w-5 text-blue-600" />
        <AlertDescription className="ml-2">
          <div className="space-y-2">
            <p className="font-semibold text-base text-blue-900">How It Works:</p>
            <p className="text-blue-800 text-sm">
              Parameter Server collects gradient updates from all workers. 
              Byzantine workers send <span className="text-red-600 font-bold">malicious updates (5x larger)</span> to corrupt training.
              <strong> Robust aggregators</strong> detect and filter out these attacks.
            </p>
          </div>
        </AlertDescription>
      </Alert>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Simulation Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Aggregator Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Select Aggregator:</label>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
              {Object.entries(AGGREGATORS).map(([key, agg]) => {
                const AggIcon = agg.icon;
                return (
                  <Button
                    key={key}
                    variant={selectedAggregator === key ? 'default' : 'outline'}
                    onClick={() => setSelectedAggregator(key as keyof typeof AGGREGATORS)}
                    disabled={isPlaying}
                    className="h-auto py-3 flex flex-col items-center gap-1"
                  >
                    <AggIcon className="h-4 w-4" />
                    <span className="text-xs">{agg.name.split(' ')[0]}</span>
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Aggregator Info */}
          <div className={`p-4 rounded-lg border-2 ${aggregator.borderColor} ${aggregator.color}`}>
            <div className="flex items-start gap-3">
              <Icon className="h-6 w-6 mt-0.5" />
              <div>
                <p className="font-semibold text-lg">{aggregator.name}</p>
                <p className="text-sm">{aggregator.description}</p>
              </div>
            </div>
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
              Step: {currentStep} / {maxSteps} | Byzantine: Worker #{byzantineWorker}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Worker Updates Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workers Sending Updates */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Worker Updates (Gradient Magnitudes)</CardTitle>
            <CardDescription>
              Red = Byzantine attack (5x larger) | Green = Honest updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Worker cards with update values */}
              <div className="grid grid-cols-5 gap-3">
                {workerUpdates.map((update, idx) => {
                  const isByzantine = idx === byzantineWorker;
                  return (
                    <div
                      key={idx}
                      className={`
                        p-3 rounded-lg border-2 text-center transition-all
                        ${isByzantine 
                          ? 'border-red-500 bg-red-50 scale-105 shadow-lg' 
                          : 'border-green-500 bg-green-50'
                        }
                      `}
                    >
                      {isByzantine ? (
                        <AlertTriangle className="h-5 w-5 mx-auto mb-1 text-red-600" />
                      ) : (
                        <Shield className="h-5 w-5 mx-auto mb-1 text-green-600" />
                      )}
                      <div className="text-xs font-medium mb-1">W{idx}</div>
                      <div className={`text-sm font-bold ${isByzantine ? 'text-red-700' : 'text-green-700'}`}>
                        {update.toFixed(2)}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Bar chart visualization */}
              <div className="space-y-2 mt-6">
                <p className="text-sm font-medium">Update Magnitude Comparison:</p>
                <div className="flex items-end justify-between gap-1 h-32 bg-muted/30 p-3 rounded-lg">
                  {workerUpdates.map((value, idx) => {
                    const maxValue = Math.max(...workerUpdates);
                    const heightPercent = (value / maxValue) * 100;
                    const isByzantine = idx === byzantineWorker;
                    
                    return (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <div className={`text-[10px] font-medium ${isByzantine ? 'text-red-600 font-bold' : 'text-muted-foreground'}`}>
                          {value.toFixed(1)}
                        </div>
                        <div 
                          className={`w-full rounded-t transition-all duration-300 ${
                            isByzantine ? 'bg-red-500' : 'bg-green-500'
                          }`}
                          style={{ height: `${heightPercent}%` }}
                        />
                        <div className="text-[10px] font-medium">{idx}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Aggregation Result */}
        <Card className={`border-2 ${isPoisoned ? 'border-red-300 bg-red-50' : 'border-green-300 bg-green-50'}`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {isPoisoned ? (
                <XCircle className="h-5 w-5 text-red-600" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              Aggregation Result
            </CardTitle>
            <CardDescription>
              {isPoisoned ? 'Attack succeeded' : 'Attack blocked'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Aggregated Value Display */}
            <div className="text-center p-6 bg-white rounded-lg border-2">
              <div className="text-sm text-muted-foreground mb-2">Final Gradient</div>
              <div className={`text-4xl font-bold ${isPoisoned ? 'text-red-600' : 'text-green-600'}`}>
                {aggregatedValue?.toFixed(3)}
              </div>
              <div className="mt-4 space-y-2">
                <div className="text-xs text-muted-foreground">Expected: {expectedHonestValue.toFixed(3)}</div>
                <div className={`text-sm font-medium ${isPoisoned ? 'text-red-600' : 'text-green-600'}`}>
                  {isPoisoned ? (
                    <>⚠️ Compromised</>
                  ) : (
                    <>✓ Defended</>
                  )}
                </div>
              </div>
            </div>

            {/* Status Indicators */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Byzantine Updates:</span>
                <Badge variant="destructive">1/10</Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Defense Status:</span>
                <Badge variant={aggregator.isRobust ? 'default' : 'destructive'}>
                  {aggregator.isRobust ? 'Protected' : 'Vulnerable'}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Deviation:</span>
                <span className="font-medium">
                  {aggregatedValue ? `${((Math.abs(aggregatedValue - expectedHonestValue) / expectedHonestValue) * 100).toFixed(1)}%` : 'N/A'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Aggregation History Chart */}
      {history.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Aggregation History</CardTitle>
            <CardDescription>
              Track how {aggregator.name} handles Byzantine updates over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" label={{ value: 'Step', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Aggregated Value', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke={aggregator.isRobust ? '#22c55e' : '#ef4444'} 
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name={aggregator.name}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => expectedHonestValue} 
                  stroke="#3b82f6" 
                  strokeWidth={1} 
                  strokeDasharray="5 5"
                  name="Expected (Honest)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Real Experiment Data Comparison */}
      <RealDataComparison />
    </div>
  );
}

// Component to show real accuracy data from experiments
function RealDataComparison() {
  const [comparisonData, setComparisonData] = useState<any[]>([]);

  useEffect(() => {
    // Load real experiment results
    loadExperimentData();
  }, []);

  const loadExperimentData = async () => {
    try {
      // Load data from multiple aggregators (match actual file names)
      const aggregators = [
        { key: 'mean', fileName: 'mean' },
        { key: 'trimmed_mean', fileName: 'trimmed_mean' },
        { key: 'CC_tau=0.3', fileName: 'CC_tau=0.3' },
        { key: 'LFighter', fileName: 'LFighter' },
        { key: 'faba', fileName: 'faba' }
      ];
      const attackType = 'label_flipping';
      const partition = 'DirichletPartition_alpha=1';
      
      const dataPromises = aggregators.map(async (agg) => {
        try {
          const response = await fetch(`/data/SR_MNIST/Centralized_n=10_b=1/${partition}/CMomentum_${attackType}_${agg.fileName}/CMomentum_${attackType}_${agg.fileName}__iterations.json`);
          if (!response.ok) {
            console.error(`Failed to load ${agg.fileName}:`, response.status);
            return null;
          }
          const jsonData = await response.json();
          
          // Extract iterations array from the JSON structure
          const data = jsonData.iterations || [];
          
          // Sample every 20 iterations for cleaner visualization (200 rounds = ~20k iterations)
          const sampled = data.filter((_: any, i: number) => i % 100 === 0).slice(0, 200);
          
          return {
            aggregator: agg.key,
            data: sampled
          };
        } catch (err) {
          console.error(`Error loading ${agg.fileName}:`, err);
          return null;
        }
      });

      const results = await Promise.all(dataPromises);
      const validResults = results.filter(r => r !== null);

      // Transform for recharts
      if (validResults.length > 0) {
        const maxLength = Math.max(...validResults.map(r => r!.data.length));
        const chartData = Array.from({ length: maxLength }, (_, i) => {
          const point: any = { iteration: i * 100 }; // Match sampling rate
          validResults.forEach(result => {
            if (result && result.data[i]) {
              // Real data structure: { accuracy: { accuracy: 0.9xxx, std_accuracy: 0.0 } }
              const accuracyObj = result.data[i].accuracy;
              const accuracy = typeof accuracyObj === 'object' ? accuracyObj.accuracy : (accuracyObj || 0);
              point[result.aggregator] = accuracy * 100; // Convert to percentage
            }
          });
          return point;
        });
        
        console.log('Loaded experiment data:', chartData.length, 'points from', validResults.length, 'aggregators');
        setComparisonData(chartData);
      }
    } catch (error) {
      console.error('Failed to load experiment data:', error);
    }
  };

  const colors = {
    mean: '#ef4444',
    trimmed_mean: '#f59e0b',
    'CC_tau=0.3': '#3b82f6',
    LFighter: '#22c55e',
    faba: '#a855f7'
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Real Experiment Results - Accuracy Comparison
        </CardTitle>
        <CardDescription>
          Actual training accuracy from SR_MNIST dataset with Label Flipping attack (1 Byzantine / 10 workers)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {comparisonData.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="iteration" 
                  label={{ value: 'Training Iteration', position: 'insideBottom', offset: -5 }} 
                />
                <YAxis 
                  label={{ value: 'Test Accuracy (%)', angle: -90, position: 'insideLeft' }}
                  domain={[0, 100]}
                />
                <Tooltip />
                <Legend />
                {Object.entries(colors).map(([agg, color]) => (
                  <Line
                    key={agg}
                    type="monotone"
                    dataKey={agg}
                    stroke={color}
                    strokeWidth={2}
                    dot={{ r: 2 }}
                    name={agg.replace('_', ' ').replace('=', ' = ')}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>

            {/* Summary Statistics */}
            <div className="mt-6 grid grid-cols-2 md:grid-cols-5 gap-4">
              {Object.entries(colors).map(([agg, color]) => {
                const finalAccuracy = comparisonData[comparisonData.length - 1]?.[agg];
                const isRobust = agg !== 'mean';
                
                return (
                  <div key={agg} className="p-4 border-2 rounded-lg" style={{ borderColor: color }}>
                    <div className="text-xs font-medium text-muted-foreground mb-1">
                      {agg.replace('_', ' ').toUpperCase()}
                    </div>
                    <div className="text-2xl font-bold" style={{ color }}>
                      {finalAccuracy ? `${finalAccuracy.toFixed(1)}%` : 'N/A'}
                    </div>
                    <Badge 
                      variant={isRobust ? 'default' : 'destructive'} 
                      className="text-[10px] mt-2"
                    >
                      {isRobust ? 'Robust' : 'Vulnerable'}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            Loading experiment data...
          </div>
        )}
      </CardContent>
    </Card>
  );
}
