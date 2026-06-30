'use client';

import { useState, useEffect } from 'react';

export default function SimpleAttackDemo() {
  const [count, setCount] = useState(0);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (!isRunning) return;
    
    const interval = setInterval(() => {
      setCount(c => c + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="p-8 space-y-4">
      <h1 className="text-3xl font-bold">Simple Animation Test</h1>
      
      <div className="text-6xl font-mono">{count}</div>
      
      <div className="flex gap-4">
        <button 
          onClick={() => setIsRunning(!isRunning)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {isRunning ? 'Pause' : 'Start'}
        </button>
        
        <button 
          onClick={() => {
            setIsRunning(false);
            setCount(0);
          }}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
        >
          Reset
        </button>
      </div>
      
      <div className="mt-8 p-4 bg-gray-100 rounded">
        <p>Status: {isRunning ? '▶️ Running' : '⏸️ Paused'}</p>
        <p>Counter: {count}</p>
      </div>
    </div>
  );
}
