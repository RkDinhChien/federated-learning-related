'use client';

import type { WorkerNode, ServerNode } from '@/types';

interface NetworkVizProps {
  byzantineSize: number;
  honestSize: number;
}

export function NetworkViz({ byzantineSize, honestSize }: NetworkVizProps) {
  const totalWorkers = byzantineSize + honestSize;
  const workers: WorkerNode[] = [];
  
  // Generate worker positions in a circle
  const radius = 120;
  const centerX = 200;
  const centerY = 150;
  
  for (let i = 0; i < totalWorkers; i++) {
    const angle = (i / totalWorkers) * 2 * Math.PI;
    workers.push({
      id: String(i),
      type: 'worker',
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      isByzantine: i < byzantineSize,
      labelDistribution: [],
    });
  }

  const server: ServerNode = { id: 'server', type: 'server', x: centerX, y: centerY };

  return (
    <svg width="400" height="300" className="mx-auto">
      {/* Connections */}
      {workers.map((worker) => (
        <line
          key={`line-${worker.id}`}
          x1={server.x}
          y1={server.y}
          x2={worker.x}
          y2={worker.y}
          stroke="#d1d5db"
          strokeWidth="1"
        />
      ))}

      {/* Worker nodes */}
      {workers.map((worker) => (
        <circle
          key={`worker-${worker.id}`}
          cx={worker.x}
          cy={worker.y}
          r="12"
          fill={worker.isByzantine ? '#ef4444' : '#3b82f6'}
          className="drop-shadow-md"
        />
      ))}

      {/* Server node */}
      <circle
        cx={server.x}
        cy={server.y}
        r="20"
        fill="#8b5cf6"
        className="drop-shadow-lg"
      />
      <text
        x={server.x}
        y={(server.y || 0) + 4}
        textAnchor="middle"
        className="text-xs font-semibold fill-white"
      >
        PS
      </text>

      {/* Legend */}
      <g transform="translate(10, 260)">
        <circle cx="8" cy="8" r="6" fill="#3b82f6" />
        <text x="20" y="12" className="text-xs fill-gray-700">Honest Worker</text>
        
        <circle cx="110" cy="8" r="6" fill="#ef4444" />
        <text x="122" y="12" className="text-xs fill-gray-700">Byzantine Worker</text>
        
        <circle cx="245" cy="8" r="8" fill="#8b5cf6" />
        <text x="260" y="12" className="text-xs fill-gray-700">Parameter Server</text>
      </g>
    </svg>
  );
}
