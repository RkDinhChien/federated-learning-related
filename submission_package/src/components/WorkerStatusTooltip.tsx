'use client';

import { useState } from 'react';
import { AlertCircle, Shield, Skull } from 'lucide-react';

interface WorkerStatusTooltipProps {
  workerId: number;
  isByzantine: boolean;
  isActive: boolean;
  localAccuracy?: number;
  currentStep: number;
}

export default function WorkerStatusTooltip({
  workerId,
  isByzantine,
  isActive,
  localAccuracy = 0,
  currentStep
}: WorkerStatusTooltipProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  const getStepStatus = () => {
    switch (currentStep) {
      case 1:
        return "📥 Downloading model from server...";
      case 2:
        return isByzantine 
          ? "☠️ Poisoning training data!" 
          : "🔄 Training on local data normally";
      case 3:
        return isByzantine
          ? "📤 Sending POISONED gradients!"
          : "📤 Sending correct gradients";
      case 4:
        return "⏳ Waiting for server aggregation...";
      case 5:
        return "✅ Received updated global model";
      default:
        return "Idle";
    }
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Worker Circle */}
      <div 
        className={`
          w-10 h-10 rounded-full flex items-center justify-center font-bold text-xs
          transition-all cursor-pointer
          ${isByzantine 
            ? 'bg-red-500 text-white' + (isActive ? ' ring-4 ring-red-300 animate-pulse' : '')
            : 'bg-blue-500 text-white' + (isActive ? ' ring-4 ring-blue-300' : '')
          }
          hover:scale-110
        `}
      >
        {isByzantine ? <Skull className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 animate-in fade-in slide-in-from-bottom-2">
          <div className={`
            px-3 py-2 rounded-lg shadow-lg text-xs whitespace-nowrap
            ${isByzantine ? 'bg-red-600 text-white' : 'bg-blue-600 text-white'}
          `}>
            <div className="font-bold mb-1 flex items-center gap-1">
              {isByzantine ? '☠️' : '🛡️'} Worker {workerId}
              {isByzantine && <span className="bg-red-800 px-1 rounded text-[10px]">MALICIOUS</span>}
            </div>
            <div className="text-[11px] opacity-90 mb-1">
              Status: {getStepStatus()}
            </div>
            {localAccuracy > 0 && (
              <div className="text-[11px] opacity-80">
                Local Accuracy: {(localAccuracy * 100).toFixed(1)}%
              </div>
            )}
          </div>
          {/* Arrow */}
          <div className={`
            w-2 h-2 rotate-45 absolute top-full left-1/2 -translate-x-1/2 -mt-1
            ${isByzantine ? 'bg-red-600' : 'bg-blue-600'}
          `} />
        </div>
      )}
    </div>
  );
}
