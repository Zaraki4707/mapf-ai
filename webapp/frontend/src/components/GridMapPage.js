import React, { useState, useMemo } from 'react';
import './GridMapPage.css';

const RAW_GRID = `TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
TT..................................................................................................................................................................................TT
TT..................................................................................................................................................................................TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..........................................................................................TTTTTTTTTTTTTTTTTTTTTT....................................TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..........................................................................................TTTTTTTTTTTTTTTTTTTTTT....................................TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..................TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..................TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..................TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..................TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......TTTTTTTTTTTTTTTTTTTTTTTT..TTTTTTTTTTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT......TTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT............................................................................................................................................................................TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT......................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..TTTT................................................................................................................TTTTTTTTTTTTTTTTTT......TTTT..TTTT..TTTT..TTTT..TTTT..TTTT..TT
TT..................................................................................................................................................................................TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..................................................................................................................................................................................TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT............TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TT
TT..................................................................................................................................................................................TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..................................................................................................................................................................................TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT....TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT...TTTT..TTTT....TTTT..TTTT....TTTT..TTTT..TT
TT..................................................................................................................................................................................TT
TT..................................................................................................................................................................................TT
TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT`;

function GridMapPage({ onRunSolver }) {
  const [selectionMode, setSelectionMode] = useState('start');
  const [agents, setAgents] = useState([]);
  const [currentAgentIdx, setCurrentAgentIdx] = useState(0);
  const [algorithm, setAlgorithm] = useState('independent_astar');

  // Parse grid once
  const { obstacleSet, numRows, numCols } = useMemo(() => {
    const lines = RAW_GRID.split('\n').map(l => l.replace(/\r$/, ''));
    const numCols = Math.max(...lines.map(l => l.length));
    const numRows = lines.length;
    const obstacleSet = new Set();
    lines.forEach((row, r) => {
      for (let c = 0; c < numCols; c++) {
        if ((row[c] ?? '.') === 'T') obstacleSet.add(`${r}-${c}`);
      }
    });
    return { obstacleSet, numRows, numCols };
  }, []);

  const handleCellClick = (r, c) => {
    if (obstacleSet.has(`${r}-${c}`)) return; // walls haka fixed

    setAgents(prev => {
      const updated = prev.map(a => ({ ...a }));
      let agent = updated.find(a => a.id === currentAgentIdx);
      if (!agent) {
        agent = { id: currentAgentIdx, start: null, pick: null, drop: null, destination: null };
        updated.push(agent);
      }
      agent[selectionMode] = [r, c];
      return updated;
    });
  };

  const handleRun = () => {
    const obstacles = [];
    obstacleSet.forEach(key => {
      const [r, c] = key.split('-').map(Number);
      obstacles.push([r, c]);
    });

    const validAgents = agents.filter(a => a.start && a.pick && a.drop && a.destination);
    if (validAgents.length === 0) return;

    onRunSolver({
      grid_height: numRows,
      grid_width: numCols,
      algorithm,
      obstacles,
      start: validAgents.map(a => a.start),
      pick: validAgents.map(a => a.pick),
      drop: validAgents.map(a => a.drop),
      destination: validAgents.map(a => a.destination),
      predefined_map: true,
    });
  };

  const handleLoadDefault = () => {
    setAgents([
      { id: 0, start: [1, 5], pick: [64, 2], drop: [68, 170], destination: [69, 5] },
      { id: 1, start: [1, 15], pick: [64, 14], drop: [68, 165], destination: [69, 10] },
      { id: 2, start: [1, 25], pick: [64, 28], drop: [68, 160], destination: [69, 15] },
      { id: 3, start: [1, 35], pick: [64, 42], drop: [68, 155], destination: [69, 20] },
      { id: 4, start: [1, 45], pick: [64, 56], drop: [68, 150], destination: [69, 25] },
      { id: 5, start: [1, 55], pick: [64, 70], drop: [68, 145], destination: [69, 30] },
      { id: 6, start: [1, 65], pick: [64, 84], drop: [68, 140], destination: [69, 35] },
      { id: 7, start: [1, 75], pick: [64, 98], drop: [68, 135], destination: [69, 40] },
      { id: 8, start: [1, 85], pick: [64, 111], drop: [68, 130], destination: [69, 45] },
      { id: 9, start: [1, 95], pick: [64, 124], drop: [68, 125], destination: [69, 50] }
    ]);
  };

  const handleReset = () => setAgents([]);

  // Build cell class names quickly
  const getCellInfo = (r, c) => {
    let className = 'grid-cell';
    if (obstacleSet.has(`${r}-${c}`)) return { className: className + ' obstacle', labels: [] };
    const labels = [];
    agents.forEach(a => {
      if (a.start       && a.start[0] === r       && a.start[1] === c)       { labels.push(`S${a.id}`); className += ' start'; }
      if (a.pick        && a.pick[0] === r         && a.pick[1] === c)        { labels.push(`P${a.id}`); className += ' pick'; }
      if (a.drop        && a.drop[0] === r         && a.drop[1] === c)        { labels.push(`D${a.id}`); className += ' drop'; }
      if (a.destination && a.destination[0] === r  && a.destination[1] === c) { labels.push(`E${a.id}`); className += ' end'; }
    });
    return { className, labels };
  };

  const validCount = agents.filter(a => a.start && a.pick && a.drop && a.destination).length;

  return (
    <div className="grid-config-page">
      <div className="config-header">
        <h2>BMS Warehouse MAP({numRows} × {numCols})</h2>
        <div className="config-controls">

          {/* Mode buttons */}
          <div className="mode-selector">
            {['start','pick','drop','destination'].map(m => (
              <button
                key={m}
                className={`nav-btn${selectionMode === m ? ' nav-btn-active' : ''}`}
                onClick={() => setSelectionMode(m)}
              >
                {m.charAt(0).toUpperCase() + m.slice(1)}
              </button>
            ))}
          </div>

          {/* Agent ID */}
          <div className="agent-selector">
            <span style={{ color: '#A0A0A0', fontSize: '0.8rem' }}>AGENT ID:</span>
            <input
              type="number"
              min="0"
              value={currentAgentIdx}
              onChange={e => setCurrentAgentIdx(parseInt(e.target.value) || 0)}
              className="agent-input"
            />
          </div>

          {/* Algorithm */}
          <div className="algorithm-selector">
            <span style={{ color: '#A0A0A0', fontSize: '0.8rem' }}>ALGORITHM:</span>
            <select value={algorithm} onChange={e => setAlgorithm(e.target.value)} className="algo-select">
              <option value="independent_astar">Independent A*</option>
              <option value="cooperative_astar">Cooperative A*</option>
              <option value="hill_climbing">Hill Climbing</option>
              <option value="cbs">CBS (Conflict-Based Search)</option>
              <option value="optimized_hc">Optimized Hill Climbing</option>
            </select>
          </div>

          {/* Actions */}
          <div className="actions">
            <button className="nav-btn" onClick={handleReset}>Reset</button>
            <button className="nav-btn" onClick={handleLoadDefault} style={{ marginLeft: '8px' }}>Load Default</button>
            <button
              className="nav-btn find-path-btn"
              onClick={handleRun}
              disabled={validCount === 0}
            >
              FIND PATH {validCount > 0 ? `(${validCount} agents)` : ''}
            </button>
          </div>
        </div>

        {/* Agent summary */}
        {agents.length > 0 && (
          <div className="gmp-agent-summary">
            {agents.map(a => (
              <div key={a.id} className="gmp-agent-row">
                <span className="gmp-agent-id">AG-{a.id}</span>
                <span className={a.start       ? 'gmp-tag gmp-s' : 'gmp-tag gmp-missing'}>S{a.start       ? `(${a.start[0]},${a.start[1]})`       : '?'}</span>
                <span className={a.pick        ? 'gmp-tag gmp-p' : 'gmp-tag gmp-missing'}>P{a.pick        ? `(${a.pick[0]},${a.pick[1]})`           : '?'}</span>
                <span className={a.drop        ? 'gmp-tag gmp-d' : 'gmp-tag gmp-missing'}>D{a.drop        ? `(${a.drop[0]},${a.drop[1]})`           : '?'}</span>
                <span className={a.destination ? 'gmp-tag gmp-e' : 'gmp-tag gmp-missing'}>E{a.destination ? `(${a.destination[0]},${a.destination[1]})` : '?'}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Grid */}
      <div className="grid-visualizer-container">
        <div
          className="grid-container"
          style={{ gridTemplateColumns: `repeat(${numCols}, 8px)` }}
        >
          {Array.from({ length: numRows }, (_, r) =>
            Array.from({ length: numCols }, (_, c) => {
              const { className, labels } = getCellInfo(r, c);
              return (
                <div
                  key={`${r}-${c}`}
                  className={`${className} gmp-small-cell`}
                  onClick={() => handleCellClick(r, c)}
                  title={`(${r}, ${c})`}
                >
                  {labels.length > 0 && (
                    <span className="cell-label gmp-tiny-label">{labels.join(',')}</span>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

export default GridMapPage;
