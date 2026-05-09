import React, { useState, useEffect } from 'react';
import './GridVisualization.css';

const INDUSTRIAL_COLORS = [
  '#F1C40F', // Agent 1: Safety Yellow
  '#3498DB', // Agent 2: Cyan
  '#C0392B', // Agent 3: Crimson
  '#27AE60', // Agent 4: Emerald Green
  '#8E44AD', // Agent 5: Amethyst Purple
  '#E67E22', // Agent 6: Carrot Orange
  '#16A085', // Agent 7: Green Sea
  '#2980B9', // Agent 8: Belize Hole Blue
  '#D35400', // Agent 9: Pumpkin Orange
  '#7F8C8D', // Agent 10: Asbestos Gray
  '#FF9FF3', // Agent 11: Jigglypuff Pink
  '#54A0FF', // Agent 12: Joust Blue
  '#00D2D3', // Agent 13: Jade Dust
  '#5F27CD', // Agent 14: Nasu Purple
  '#FF6B6B', // Agent 15: Pastel Red
];

function GridVisualization({ paths, gridHeight = 6, gridWidth = 17 }) {
  const [timeStep, setTimeStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showTrails, setShowTrails] = useState(true);
  
  const maxSteps = Math.max(...paths.map(p => p.length));

  useEffect(() => {
    let interval;
    if (isPlaying && timeStep < maxSteps - 1) {
      interval = setInterval(() => {
        setTimeStep(prev => prev + 1);
      }, 150); // Faster, mechanical transition
    } else {
      setIsPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isPlaying, timeStep, maxSteps]);

  const getAgentPosition = (agentIdx, step) => {
    if (!paths[agentIdx]) return null;
    if (step < paths[agentIdx].length) {
      return paths[agentIdx][step];
    }
    return paths[agentIdx][paths[agentIdx].length - 1];
  };

  const renderGrid = () => {
    const grid = [];
    for (let i = 0; i < gridHeight; i++) {
      for (let j = 0; j < gridWidth; j++) {
        const key = `${i}-${j}`;
        
        let agentAtPosition = null;
        let isStart = false;
        let isEnd = false;
        let trailAgent = null;
        let isFuture = false;

        paths.forEach((path, idx) => {
          const pos = getAgentPosition(idx, timeStep);
          if (pos && pos[0] === i && pos[1] === j) {
            agentAtPosition = idx;
          }

          // Trail check
          if (showTrails) {
            const stepIndex = path.findIndex(p => p[0] === i && p[1] === j);
            if (stepIndex !== -1) {
              if (stepIndex < timeStep) {
                trailAgent = idx;
              } else if (stepIndex > timeStep) {
                isFuture = true;
                trailAgent = idx;
              }
            }
          }

          if (path[0][0] === i && path[0][1] === j) isStart = true;
          if (path[path.length - 1][0] === i && path[path.length - 1][1] === j) isEnd = true;
        });

        grid.push(
          <div key={key} className="grid-cell">
            {/* Trail Breadcrumb */}
            {trailAgent !== null && !isFuture && agentAtPosition === null && (
              <div 
                className="breadcrumb" 
                style={{ backgroundColor: INDUSTRIAL_COLORS[trailAgent % INDUSTRIAL_COLORS.length] }}
              />
            )}
            
            {/* Future Path Outline */}
            {isFuture && agentAtPosition === null && (
              <div 
                className="future-marker" 
                style={{ color: INDUSTRIAL_COLORS[trailAgent % INDUSTRIAL_COLORS.length] }}
              />
            )}

            {/* Waypoints */}
            {isStart && agentAtPosition === null && <div className="pickup-point" title="START/PICKUP" />}
            {isEnd && agentAtPosition === null && <div className="crosshair" title="DESTINATION" />}

            {/* Agent Node */}
            {agentAtPosition !== null && (
              <div 
                className="agent-node"
                style={{ backgroundColor: INDUSTRIAL_COLORS[agentAtPosition % INDUSTRIAL_COLORS.length] }}
              >
                {agentAtPosition + 1}
              </div>
            )}
          </div>
        );
      }
    }
    return grid;
  };

  return (
    <div className="grid-visualization">
      <div className="visualization-header">
        <h3>Mission Control: MAPF Terminal</h3>
        <div className="legend">
          {paths.map((_, idx) => (
            <div key={idx} className="legend-item">
              <div 
                className="legend-color" 
                style={{ backgroundColor: INDUSTRIAL_COLORS[idx % INDUSTRIAL_COLORS.length] }}
              ></div>
              <span>AG-{String(idx + 1).padStart(2, '0')}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="visualizer-main">
        <div className="grid-wrapper">
          <div 
            className="grid-container" 
            style={{ gridTemplateColumns: `repeat(${gridWidth}, 36px)` }}
          >
            {renderGrid()}
          </div>
        </div>

        <div className="telemetry-panel">
          <div className="telemetry-readout">
            <div className="telemetry-header">SYSTEM TELEMETRY | T-{timeStep}</div>
            {paths.map((path, idx) => {
              const pos = getAgentPosition(idx, timeStep);
              return (
                <div key={idx} className="telemetry-row">
                  <div className="agent-label" style={{ color: INDUSTRIAL_COLORS[idx % 3] }}>
                    AGENT {idx + 1}
                  </div>
                  <div className="agent-stats">
                    <span>X: {pos ? pos[1].toString().padStart(2, '0') : '--'}</span>
                    <span>Y: {pos ? pos[0].toString().padStart(2, '0') : '--'}</span>
                    <span className={isPlaying ? 'status-active' : 'status-idle'}>
                      {isPlaying ? 'MOVING' : 'IDLE'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="controls-panel">
            <div className="control-buttons">
              <button 
                className="hw-button" 
                onClick={() => setTimeStep(Math.max(0, timeStep - 1))}
                disabled={timeStep === 0}
              >
                PREV
              </button>
              <button 
                className="hw-button primary" 
                onClick={() => setIsPlaying(!isPlaying)}
              >
                {isPlaying ? 'PAUSE' : 'EXECUTE'}
              </button>
              <button 
                className="hw-button" 
                onClick={() => setTimeStep(Math.min(maxSteps - 1, timeStep + 1))}
                disabled={timeStep >= maxSteps - 1}
              >
                NEXT
              </button>
              <button 
                className="hw-button" 
                onClick={() => { setTimeStep(0); setIsPlaying(false); }}
              >
                RESET
              </button>
            </div>
            
            <div className="options-panel">
              <label className="hw-checkbox">
                <input 
                  type="checkbox" 
                  checked={showTrails} 
                  onChange={(e) => setShowTrails(e.target.checked)}
                />
                ENABLE BREADCRUMB TRAILS
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default GridVisualization;