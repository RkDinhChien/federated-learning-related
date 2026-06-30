'use client';

import { useState, useEffect } from 'react';
import { AlertCircle, ArrowRight, Upload, Download, TrendingUp, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface AnimationStep {
  id: number;
  title: string;
  description: string;
  icon: React.ReactNode;
  activeColor: string;
}

const TRAINING_STEPS: AnimationStep[] = [
  {
    id: 1,
    title: "📥 Download Model",
    description: "Workers receive current global model from Parameter Server",
    icon: <Download className="w-4 h-4" />,
    activeColor: "bg-blue-100 border-blue-500 text-blue-900"
  },
  {
    id: 2,
    title: "🔄 Local Training",
    description: "Each worker trains on their local data (honest trains normally, Byzantine poisons data)",
    icon: <TrendingUp className="w-4 h-4" />,
    activeColor: "bg-purple-100 border-purple-500 text-purple-900"
  },
  {
    id: 3,
    title: "📤 Upload Gradients",
    description: "Workers send computed gradients back to server (Byzantine sends poisoned gradients)",
    icon: <Upload className="w-4 h-4" />,
    activeColor: "bg-green-100 border-green-500 text-green-900"
  },
  {
    id: 4,
    title: "🎯 Aggregate",
    description: "Server combines all gradients using aggregation method (filters Byzantine if robust)",
    icon: <CheckCircle2 className="w-4 h-4" />,
    activeColor: "bg-yellow-100 border-yellow-500 text-yellow-900"
  },
  {
    id: 5,
    title: "✅ Update Model",
    description: "Global model updated with aggregated gradients, ready for next round",
    icon: <CheckCircle2 className="w-4 h-4" />,
    activeColor: "bg-emerald-100 border-emerald-500 text-emerald-900"
  }
];

interface AnimationExplainerProps {
  currentIteration: number;
  isPlaying: boolean;
  byzantineCount: number;
  aggregator: string;
}

export default function AnimationExplainer({
  currentIteration,
  isPlaying,
  byzantineCount,
  aggregator
}: AnimationExplainerProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [showDetails, setShowDetails] = useState(true);

  // Cycle through steps when playing
  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setCurrentStep(prev => (prev % 5) + 1);
    }, 2000); // Change step every 2 seconds

    return () => clearInterval(interval);
  }, [isPlaying]);

  // Reset to step 1 when stopped
  useEffect(() => {
    if (!isPlaying) {
      setCurrentStep(1);
    }
  }, [isPlaying]);

  return (
    <Card className="border-2 border-dashed border-blue-300 bg-blue-50/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-blue-600" />
            Training Animation Guide
            {isPlaying && (
              <Badge variant="outline" className="ml-2 bg-green-50 text-green-700 border-green-300 animate-pulse">
                ▶️ Playing
              </Badge>
            )}
          </CardTitle>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {showDetails ? 'Hide' : 'Show'} Details
          </button>
        </div>
      </CardHeader>
      
      {showDetails && (
        <CardContent className="space-y-4">
          {/* Current Status */}
          <div className="bg-white rounded-lg p-3 border border-blue-200">
            <div className="grid grid-cols-3 gap-3 text-sm">
              <div>
                <span className="text-gray-600">Current Step:</span>
                <p className="font-semibold text-blue-900">
                  Step {currentStep}/5
                </p>
              </div>
              <div>
                <span className="text-gray-600">Byzantine Workers:</span>
                <p className="font-semibold text-red-600">
                  {byzantineCount} / 10
                </p>
              </div>
              <div>
                <span className="text-gray-600">Aggregator:</span>
                <p className="font-semibold text-purple-600">
                  {aggregator}
                </p>
              </div>
            </div>
          </div>

          {/* Step Progress */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-gray-700 mb-3">
              What's happening in the animation:
            </p>
            
            {TRAINING_STEPS.map((step, index) => {
              const isActive = currentStep === step.id;
              const isPast = currentStep > step.id;
              
              return (
                <div key={step.id} className="relative">
                  {/* Connecting Line */}
                  {index < TRAINING_STEPS.length - 1 && (
                    <div 
                      className={`absolute left-4 top-8 w-0.5 h-8 transition-colors ${
                        isPast ? 'bg-green-400' : 'bg-gray-300'
                      }`}
                    />
                  )}
                  
                  {/* Step Card */}
                  <div
                    className={`
                      flex items-start gap-3 p-3 rounded-lg border-2 transition-all
                      ${isActive 
                        ? step.activeColor + ' shadow-md scale-[1.02]' 
                        : isPast
                        ? 'bg-gray-50 border-gray-300 opacity-60'
                        : 'bg-white border-gray-200'
                      }
                    `}
                  >
                    {/* Step Number */}
                    <div 
                      className={`
                        flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm
                        ${isActive 
                          ? 'bg-blue-600 text-white' 
                          : isPast
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-300 text-gray-600'
                        }
                      `}
                    >
                      {isPast ? '✓' : step.id}
                    </div>

                    {/* Step Content */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className={`font-semibold text-sm ${
                          isActive ? 'text-gray-900' : 'text-gray-700'
                        }`}>
                          {step.title}
                        </p>
                        {isActive && (
                          <Badge className="text-xs bg-blue-600">
                            NOW
                          </Badge>
                        )}
                      </div>
                      <p className={`text-xs ${
                        isActive ? 'text-gray-700' : 'text-gray-500'
                      }`}>
                        {step.description}
                      </p>

                      {/* Step-specific annotations */}
                      {isActive && step.id === 2 && byzantineCount > 0 && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                          <span className="font-semibold text-red-700">⚠️ Attack happening:</span>
                          <span className="text-red-600"> {byzantineCount} Byzantine worker(s) poisoning data during this step!</span>
                        </div>
                      )}

                      {isActive && step.id === 3 && byzantineCount > 0 && (
                        <div className="mt-2 p-2 bg-orange-50 border border-orange-200 rounded text-xs">
                          <span className="font-semibold text-orange-700">📤 Poison upload:</span>
                          <span className="text-orange-600"> Byzantine gradients being sent (look for red pulsing workers)</span>
                        </div>
                      )}

                      {isActive && step.id === 4 && (
                        <div className="mt-2 p-2 bg-purple-50 border border-purple-200 rounded text-xs">
                          <span className="font-semibold text-purple-700">🛡️ {aggregator} defending:</span>
                          <span className="text-purple-600"> {
                            aggregator === 'mean' 
                              ? ' No filtering - vulnerable to poison!' 
                              : ' Detecting and filtering outliers'
                          }</span>
                        </div>
                      )}
                    </div>

                    {/* Arrow for active step */}
                    {isActive && (
                      <ArrowRight className="w-5 h-5 text-blue-600 animate-pulse" />
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Visual Legend */}
          <div className="border-t pt-3 mt-3">
            <p className="text-xs font-semibold text-gray-700 mb-2">
              What to watch in the network diagram:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span>Blue circles = Honest workers</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500 animate-pulse"></div>
                <span>Red circle = Byzantine worker</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <span>Purple center = Parameter Server</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-0.5 bg-blue-500"></div>
                <span>Blue lines = Active communication</span>
              </div>
            </div>
          </div>

          {/* Iteration Info */}
          <div className="bg-gray-50 rounded p-2 text-xs text-gray-600 text-center">
            <span className="font-medium">Iteration {currentIteration}</span> - Each iteration represents one complete cycle of these 5 steps
          </div>
        </CardContent>
      )}
    </Card>
  );
}
