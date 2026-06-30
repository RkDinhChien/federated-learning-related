'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { NetworkNode, NetworkLink, WorkerNode, ServerNode, AggregatorType, AttackType } from '@/types';

interface NetworkVizD3Props {
  byzantineCount: number;
  totalWorkers: number;
  currentIteration: number;
  aggregator: AggregatorType;
  attack: AttackType;
  isAnimating?: boolean;
  onWorkerHover?: (worker: WorkerNode | null) => void;
}

export default function NetworkVizD3({
  byzantineCount,
  totalWorkers = 10,
  currentIteration,
  aggregator,
  attack,
  isAnimating = false,
  onWorkerHover
}: NetworkVizD3Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [nodes, setNodes] = useState<NetworkNode[]>([]);
  const [links, setLinks] = useState<NetworkLink[]>([]);
  const [hoveredWorker, setHoveredWorker] = useState<WorkerNode | null>(null);
  const [mounted, setMounted] = useState(false);

  // Ensure client-side only rendering
  useEffect(() => {
    setMounted(true);
  }, []);

  // Initialize network structure
  useEffect(() => {
    if (!mounted) return;
    const serverNode: ServerNode = {
      id: 'server',
      type: 'server',
      fx: 400,
      fy: 300,
    };

    const workerNodes: WorkerNode[] = Array.from({ length: totalWorkers }, (_, i) => ({
      id: `worker-${i}`,
      type: 'worker',
      isByzantine: i < byzantineCount,
      labelDistribution: generateLabelDistribution(i < byzantineCount),
      localAccuracy: 0.5 + Math.random() * 0.4,
    }));

    const networkLinks: NetworkLink[] = workerNodes.map(worker => ({
      source: worker.id,
      target: 'server',
      isMalicious: worker.isByzantine,
      isActive: false,
    }));

    setNodes([serverNode, ...workerNodes]);
    setLinks(networkLinks);
  }, [byzantineCount, totalWorkers, mounted]);

  // D3 force simulation
  useEffect(() => {
    if (!mounted || !svgRef.current || nodes.length === 0) return;

    const width = 800;
    const height = 600;

    // Clear previous simulation
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Add arrow markers for links
    const defs = svg.append('defs');
    
    defs.selectAll('marker')
      .data(['normal', 'malicious', 'active'])
      .join('marker')
      .attr('id', d => `arrow-${d}`)
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('fill', d => {
        if (d === 'malicious') return '#ef4444';
        if (d === 'active') return '#3b82f6';
        return '#94a3b8';
      })
      .attr('d', 'M0,-5L10,0L0,5');

    // Add server icon symbol (database/server shape)
    const serverIcon = defs.append('g').attr('id', 'server-icon');
    serverIcon.append('rect')
      .attr('x', -15)
      .attr('y', -20)
      .attr('width', 30)
      .attr('height', 40)
      .attr('rx', 3)
      .attr('fill', '#8b5cf6');
    serverIcon.append('rect')
      .attr('x', -12)
      .attr('y', -16)
      .attr('width', 24)
      .attr('height', 4)
      .attr('rx', 1)
      .attr('fill', '#a78bfa');
    serverIcon.append('rect')
      .attr('x', -12)
      .attr('y', -10)
      .attr('width', 24)
      .attr('height', 4)
      .attr('rx', 1)
      .attr('fill', '#a78bfa');
    serverIcon.append('rect')
      .attr('x', -12)
      .attr('y', -4)
      .attr('width', 24)
      .attr('height', 4)
      .attr('rx', 1)
      .attr('fill', '#a78bfa');

    // Add honest worker icon (user shape)
    const honestWorkerIcon = defs.append('g').attr('id', 'honest-worker-icon');
    honestWorkerIcon.append('circle')
      .attr('cx', 0)
      .attr('cy', -8)
      .attr('r', 6)
      .attr('fill', '#3b82f6');
    honestWorkerIcon.append('path')
      .attr('d', 'M-10,8 Q-10,0 0,0 Q10,0 10,8 L10,15 L-10,15 Z')
      .attr('fill', '#3b82f6');

    // Add Byzantine worker icon (alert shape)
    const byzantineWorkerIcon = defs.append('g').attr('id', 'byzantine-worker-icon');
    byzantineWorkerIcon.append('path')
      .attr('d', 'M0,-15 L12,10 L-12,10 Z')
      .attr('fill', '#ef4444');
    byzantineWorkerIcon.append('text')
      .attr('x', 0)
      .attr('y', 3)
      .attr('text-anchor', 'middle')
      .attr('fill', '#fff')
      .attr('font-size', '16px')
      .attr('font-weight', 'bold')
      .text('!');

    // Create force simulation
    const simulation = d3.forceSimulation<NetworkNode>(nodes)
      .force('link', d3.forceLink<NetworkNode, NetworkLink>(links)
        .id(d => d.id)
        .distance(150)
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', d => {
        const linkData = d as NetworkLink;
        if (linkData.isActive) return '#3b82f6';
        if (linkData.isMalicious) return '#ef4444';
        return '#94a3b8';
      })
      .attr('stroke-width', d => (d as NetworkLink).isActive ? 3 : 1.5)
      .attr('stroke-dasharray', d => (d as NetworkLink).isMalicious ? '5,5' : 'none')
      .attr('opacity', 0.6)
      .attr('marker-end', d => {
        const linkData = d as NetworkLink;
        if (linkData.isActive) return 'url(#arrow-active)';
        if (linkData.isMalicious) return 'url(#arrow-malicious)';
        return 'url(#arrow-normal)';
      });

    // Draw nodes
    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<SVGGElement, NetworkNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any
      );

    // Node icons
    node.append('use')
      .attr('href', d => {
        if (d.type === 'server') return '#server-icon';
        const worker = d as WorkerNode;
        return worker.isByzantine ? '#byzantine-worker-icon' : '#honest-worker-icon';
      })
      .style('cursor', 'pointer')
      .attr('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))');

    // Add circular background for better hover effect
    node.append('circle')
      .attr('r', d => d.type === 'server' ? 35 : 25)
      .attr('fill', 'transparent')
      .attr('stroke', 'transparent')
      .attr('stroke-width', 3)
      .attr('class', 'hover-ring')
      .style('cursor', 'pointer');

    // Node labels
    node.append('text')
      .text(d => d.type === 'server' ? 'Server' : d.id.split('-')[1])
      .attr('text-anchor', 'middle')
      .attr('dy', '0.3em')
      .attr('fill', '#fff')
      .attr('font-size', d => d.type === 'server' ? '14px' : '12px')
      .attr('font-weight', 'bold')
      .style('pointer-events', 'none');

    // Aggregator badge for server
    node.filter(d => d.type === 'server')
      .append('text')
      .text(aggregator)
      .attr('text-anchor', 'middle')
      .attr('dy', '45px')
      .attr('fill', '#6b7280')
      .attr('font-size', '11px')
      .style('pointer-events', 'none');

    // Attack badge for Byzantine workers
    node.filter(d => d.type === 'worker' && (d as WorkerNode).isByzantine && attack !== 'none')
      .append('text')
      .text(attack.split('_')[0])
      .attr('text-anchor', 'middle')
      .attr('dy', '35px')
      .attr('fill', '#dc2626')
      .attr('font-size', '9px')
      .style('pointer-events', 'none');

    // Hover interactions
    node.on('mouseenter', function(event, d) {
      if (d.type === 'worker') {
        const worker = d as WorkerNode;
        setHoveredWorker(worker);
        onWorkerHover?.(worker);
        
        d3.select(this).select('.hover-ring')
          .transition()
          .duration(200)
          .attr('stroke', worker.isByzantine ? '#ef4444' : '#3b82f6')
          .attr('stroke-width', 4)
          .attr('opacity', 0.5);
      } else if (d.type === 'server') {
        d3.select(this).select('.hover-ring')
          .transition()
          .duration(200)
          .attr('stroke', '#8b5cf6')
          .attr('stroke-width', 4)
          .attr('opacity', 0.5);
      }
    })
    .on('mouseleave', function(event, d) {
      if (d.type === 'worker') {
        setHoveredWorker(null);
        onWorkerHover?.(null);
      }
      
      d3.select(this).select('.hover-ring')
        .transition()
        .duration(200)
        .attr('stroke', 'transparent')
        .attr('stroke-width', 3)
        .attr('opacity', 0);
    });

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as NetworkNode).x ?? 0)
        .attr('y1', d => (d.source as NetworkNode).y ?? 0)
        .attr('x2', d => (d.target as NetworkNode).x ?? 0)
        .attr('y2', d => (d.target as NetworkNode).y ?? 0);

      node.attr('transform', d => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    function dragstarted(event: any, d: NetworkNode) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event: any, d: NetworkNode) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event: any, d: NetworkNode) {
      if (!event.active) simulation.alphaTarget(0);
      if (d.type !== 'server') {
        d.fx = null;
        d.fy = null;
      }
    }

    return () => {
      simulation.stop();
    };
  }, [nodes, links, aggregator, attack, onWorkerHover]);

  // Animate links during aggregation
  useEffect(() => {
    if (!isAnimating || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    
    // Activate all links sequentially
    links.forEach((link, i) => {
      setTimeout(() => {
        svg.selectAll('line')
          .filter((d: any) => d.source.id === link.source)
          .transition()
          .duration(300)
          .attr('stroke', '#3b82f6')
          .attr('stroke-width', 3)
          .transition()
          .duration(300)
          .attr('stroke', (d: any) => d.isMalicious ? '#ef4444' : '#94a3b8')
          .attr('stroke-width', 1.5);
      }, i * 100);
    });
  }, [currentIteration, isAnimating, links]);

  // Don't render until mounted (prevent hydration mismatch)
  if (!mounted) {
    return (
      <div className="relative h-[600px] border border-gray-200 rounded-lg bg-gray-50 flex items-center justify-center">
        <div className="text-gray-400 text-sm">Initializing network visualization...</div>
      </div>
    );
  }

  return (
    <div className="relative">
      <svg ref={svgRef} className="border border-gray-200 rounded-lg bg-gray-50" />
      
      {/* Hover tooltip */}
      {hoveredWorker && (
        <div className="absolute top-4 right-4 bg-white border border-gray-200 rounded-lg p-3 shadow-lg max-w-xs">
          <h4 className="font-semibold text-sm mb-2">
            {hoveredWorker.id}
            {hoveredWorker.isByzantine && (
              <span className="ml-2 text-xs text-red-600 font-bold">BYZANTINE</span>
            )}
          </h4>
          
          {hoveredWorker.labelDistribution && (
            <div className="mb-2">
              <div className="text-xs text-gray-600 mb-1">Label Distribution:</div>
              <div className="flex gap-1">
                {hoveredWorker.labelDistribution.map((val, idx) => (
                  <div key={idx} className="flex flex-col items-center">
                    <div 
                      className="w-4 bg-blue-500 rounded-t"
                      style={{ height: `${val * 40}px` }}
                    />
                    <div className="text-xs text-gray-500">{idx}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {hoveredWorker.localAccuracy !== undefined && (
            <div className="text-xs text-gray-600">
              Local Accuracy: {(hoveredWorker.localAccuracy * 100).toFixed(1)}%
            </div>
          )}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white border border-gray-200 rounded-lg p-3 text-xs">
        <div className="font-semibold mb-2">Legend</div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-4 h-4 rounded-full bg-purple-500" />
          <span>Server ({aggregator})</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-4 h-4 rounded-full bg-blue-500" />
          <span>Honest Worker</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-500" />
          <span>Byzantine ({attack})</span>
        </div>
      </div>
    </div>
  );
}

// Generate synthetic label distribution for visualization
function generateLabelDistribution(isByzantine: boolean): number[] {
  const numClasses = 10;
  const distribution = new Array(numClasses).fill(0);
  
  if (isByzantine) {
    // Byzantine workers might have skewed or flipped distributions
    for (let i = 0; i < numClasses; i++) {
      distribution[i] = Math.random() * 0.3;
    }
  } else {
    // Honest workers have more uniform distributions
    for (let i = 0; i < numClasses; i++) {
      distribution[i] = 0.08 + Math.random() * 0.04;
    }
  }
  
  // Normalize
  const sum = distribution.reduce((a, b) => a + b, 0);
  return distribution.map(v => v / sum);
}
