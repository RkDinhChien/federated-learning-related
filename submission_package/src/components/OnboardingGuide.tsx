'use client';

import { useState, useEffect } from 'react';
import { X, ArrowRight, CheckCircle, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface OnboardingStep {
  title: string;
  description: string;
  visual: string;
}

const ONBOARDING_STEPS: OnboardingStep[] = [
  {
    title: "Welcome to Federated Learning",
    description: "Federated Learning lets multiple devices train a shared model WITHOUT sharing their private data. Like Google Keyboard learning from millions of phones without seeing your messages!",
    visual: "Client Devices + Client Devices + Client Devices → Global Model"
  },
  {
    title: "How It Works - 6 Steps",
    description: "1. Server sends model to 10 workers\n2. Each worker trains on local data\n3. Workers compute gradients (updates)\n4. Upload gradients to server\n5. Server aggregates (averages) them\n6. Update global model and repeat.",
    visual: "Workers → Server Aggregation → Updated Global Model"
  },
  {
    title: "The Problem: Byzantine Attacks",
    description: "1 out of 10 workers can be MALICIOUS (hacked or evil). They send poisoned gradients to sabotage the model. Result: Accuracy drops from 90% → 65%!",
    visual: "9 Honest Workers + 1 Byzantine Worker → Model Degradation"
  },
  {
    title: "The Solution: Robust Aggregation",
    description: "Instead of simple average, use SMART aggregators:\n• Trimmed Mean: Remove extremes\n• CC: Clip outliers\n• LFighter: Use loss info\n• FABA: Iterative filtering\n\nResult: Accuracy stays 85-90%!",
    visual: "Outlier Filtering → Robust Global Update"
  },
  {
    title: "Explore the App",
    description: "Attack Demo: See 4 attack types in motion\nDefense: Compare 5 robust aggregators\nTopology: Monitor training workflow\nCompare: Analyze experimental results\n\nAll data comes from 20,000 real training iterations.",
    visual: "Ready to explore"
  }
];

export default function OnboardingGuide() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [hasSeenBefore, setHasSeenBefore] = useState(false);

  useEffect(() => {
    // Check if user has seen onboarding before
    const seen = localStorage.getItem('fl-onboarding-seen');
    if (!seen) {
      setIsOpen(true);
    } else {
      setHasSeenBefore(true);
    }
  }, []);

  const handleNext = () => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleClose = () => {
    localStorage.setItem('fl-onboarding-seen', 'true');
    setIsOpen(false);
    setHasSeenBefore(true);
  };

  const handleReopen = () => {
    setCurrentStep(0);
    setIsOpen(true);
  };

  const currentStepData = ONBOARDING_STEPS[currentStep];
  const progress = ((currentStep + 1) / ONBOARDING_STEPS.length) * 100;

  if (!isOpen && hasSeenBefore) {
    return (
      <button
        onClick={handleReopen}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full shadow-lg flex items-center gap-2 transition-all z-50"
        title="Show workflow guide"
      >
        <BookOpen className="w-4 h-4" />
        <span className="text-sm font-medium">How It Works</span>
      </button>
    );
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl mx-auto shadow-2xl">
        <CardContent className="p-8">
          {/* Close button */}
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <X className="w-6 h-6" />
          </button>

          {/* Progress bar */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">
                Step {currentStep + 1} of {ONBOARDING_STEPS.length}
              </span>
              <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600 transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Content */}
          <div className="text-center mb-8">
            {/* Title */}
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {currentStepData.title}
            </h2>

            {/* Description */}
            <p className="text-gray-700 text-base leading-relaxed whitespace-pre-line mb-6">
              {currentStepData.description}
            </p>

            {/* Visual */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 mb-6">
              <p className="text-2xl font-mono">{currentStepData.visual}</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              variant="outline"
              className="px-6"
            >
              ← Previous
            </Button>

            <div className="flex gap-2">
              {ONBOARDING_STEPS.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentStep
                      ? 'bg-blue-600 w-8'
                      : index < currentStep
                      ? 'bg-blue-300'
                      : 'bg-gray-300'
                  }`}
                  aria-label={`Go to step ${index + 1}`}
                />
              ))}
            </div>

            <Button
              onClick={handleNext}
              className="px-6 bg-blue-600 hover:bg-blue-700"
            >
              {currentStep === ONBOARDING_STEPS.length - 1 ? (
                <>
                  Get Started <CheckCircle className="ml-2 w-4 h-4" />
                </>
              ) : (
                <>
                  Next <ArrowRight className="ml-2 w-4 h-4" />
                </>
              )}
            </Button>
          </div>

          {/* Skip button */}
          {currentStep === 0 && (
            <div className="text-center mt-4">
              <button
                onClick={handleClose}
                className="text-sm text-gray-500 hover:text-gray-700 underline"
              >
                Skip tutorial (I already know Federated Learning)
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
