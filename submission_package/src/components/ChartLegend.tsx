'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Info } from 'lucide-react';

interface ChartLegendProps {
  type: 'attack' | 'defense' | 'topology';
}

export default function ChartLegend({ type }: ChartLegendProps) {
  if (type === 'attack') {
    return (
      <Card className="bg-gradient-to-r from-blue-50 to-red-50 border-blue-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-600" />
            What You're Seeing
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs space-y-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Badge className="mb-1 bg-blue-500">Left Chart</Badge>
              <ul className="space-y-1 ml-2">
                <li>• <strong>Blue bars</strong> = Normal distribution</li>
                <li>• <strong>Height</strong> = % of each digit (0-9)</li>
                <li>• <strong>Static</strong> = No attack happening</li>
              </ul>
            </div>
            <div>
              <Badge className="mb-1 bg-red-500">Right Chart</Badge>
              <ul className="space-y-1 ml-2">
                <li>• <strong>Red bars</strong> = Poisoned labels</li>
                <li>• <strong>Animation</strong> = Attack in progress</li>
                <li>• <strong>Numbers (0→1)</strong> = Label transformation</li>
              </ul>
            </div>
          </div>
          <div className="bg-yellow-50 border border-yellow-300 rounded p-2 mt-2">
            <p className="font-semibold text-yellow-900">Tip:</p>
            <p className="text-yellow-800">Click <strong>Play</strong> to animate the attack and compare distribution shifts.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (type === 'defense') {
    return (
      <Card className="bg-gradient-to-r from-purple-50 to-green-50 border-purple-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-purple-600" />
            Understanding the Chart
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs space-y-2">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="font-semibold mb-1">Axes</p>
              <ul className="space-y-1 ml-2">
                <li>• <strong>X-axis</strong> = Training iterations (0→20K)</li>
                <li>• <strong>Y-axis</strong> = Test accuracy (0%→100%)</li>
                <li>• <strong>Higher</strong> = Better performance</li>
              </ul>
            </div>
            <div>
              <p className="font-semibold mb-1">Line Colors</p>
              <ul className="space-y-1 ml-2">
                <li>• <span className="text-red-600">Red</span> = mean (vulnerable)</li>
                <li>• <span className="text-yellow-600">Yellow</span> = trimmed_mean</li>
                <li>• <span className="text-blue-600">Blue</span> = CC</li>
                <li>• <span className="text-green-600">Green</span> = LFighter</li>
                <li>• <span className="text-purple-600">Purple</span> = FABA (best)</li>
              </ul>
            </div>
          </div>
          <div className="bg-green-50 border border-green-300 rounded p-2 mt-2">
            <p className="font-semibold text-green-900">Key Insight:</p>
            <p className="text-green-800">Lines going up = model learning. Flat/down = poisoned by Byzantine attack!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (type === 'topology') {
    return (
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-600" />
            Network Diagram Guide
          </CardTitle>
        </CardHeader>
        <CardContent className="text-xs space-y-2">
          <div className="grid grid-cols-3 gap-2">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-blue-500"></div>
              <span><strong>Blue</strong> = Honest workers</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-red-500 animate-pulse"></div>
              <span><strong>Red</strong> = Byzantine (attacks)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-purple-500"></div>
              <span><strong>Purple</strong> = Parameter Server</span>
            </div>
          </div>
          <div className="space-y-1 mt-2">
            <div className="flex items-center gap-2">
              <div className="w-12 h-0.5 bg-gray-400"></div>
              <span>Gray lines = Idle connection</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-12 h-0.5 bg-blue-500"></div>
              <span>Blue lines = Active gradient upload</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-blue-500 ring-4 ring-blue-300"></div>
              <span>Pulsing ring = Currently transmitting</span>
            </div>
          </div>
          <div className="bg-purple-50 border border-purple-300 rounded p-2 mt-2">
            <p className="font-semibold text-purple-900">Interaction:</p>
            <p className="text-purple-800">Hover over workers to see their status and accuracy!</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}
