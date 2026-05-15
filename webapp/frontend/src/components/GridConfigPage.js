import React, { useState } from 'react';
import './GridConfigPage.css';

const GRID_SIZE_H = 10;
const GRID_SIZE_W = 20;

function GridConfigPage({ onRunSolver }) {
    const [grid, setGrid] = useState(
        Array(GRID_SIZE_H).fill().map(() => Array(GRID_SIZE_W).fill(0))
    );
    const [selectionMode, setSelectionMode] = useState('obstacle'); // 'obstacle', 'start', 'pick', 'drop', 'destination'
    const [agents, setAgents] = useState([]); // [{id: 0, start: [r,c], pick: [r,c], drop: [r,c], destination: [r,c]}]
    const [currentAgentIdx, setCurrentAgentIdx] = useState(0);
    const [algorithm, setAlgorithm] = useState('independent_astar');

    const toggleCell = (r, c) => {
        if (selectionMode === 'obstacle') {
            const newGrid = [...grid.map(row => [...row])];
            newGrid[r][c] = newGrid[r][c] === 1 ? 0 : 1;
            setGrid(newGrid);
            // Clear any agent markers on this cell if it's now an obstacle
            if (newGrid[r][c] === 1) {
                setAgents(agents.map(a => {
                    const newA = { ...a };
                    if (newA.start && newA.start[0] === r && newA.start[1] === c) newA.start = null;
                    if (newA.pick && newA.pick[0] === r && newA.pick[1] === c) newA.pick = null;
                    if (newA.drop && newA.drop[0] === r && newA.drop[1] === c) newA.drop = null;
                    if (newA.destination && newA.destination[0] === r && newA.destination[1] === c) newA.destination = null;
                    return newA;
                }));
            }
            return;
        }

        // Check if obstacle
        if (grid[r][c] === 1) return;

        setAgents(prev => {
            const updated = [...prev];
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
        grid.forEach((row, r) => {
            row.forEach((cell, c) => {
                if (cell === 1) obstacles.push([r, c]);
            });
        });

        const validAgents = agents.filter(a => a.start && a.pick && a.drop && a.destination);
        
        const formData = {
            grid_height: GRID_SIZE_H,
            grid_width: GRID_SIZE_W,
            algorithm: algorithm,
            obstacles: obstacles,
            start: validAgents.map(a => a.start),
            pick: validAgents.map(a => a.pick),
            drop: validAgents.map(a => a.drop),
            destination: validAgents.map(a => a.destination)
        };

        onRunSolver(formData);
    };

    return (
        <div className="grid-config-page">
            <div className="config-header">
                <h2>GRID CONFIGURATION SYSTEM</h2>
                <div className="config-controls">
                    <div className="mode-selector">
                        <button className={selectionMode === 'obstacle' ? 'nav-btn nav-btn-active' : 'nav-btn'} onClick={() => setSelectionMode('obstacle')}>Obstacles</button>
                        <button className={selectionMode === 'start' ? 'nav-btn nav-btn-active' : 'nav-btn'} onClick={() => setSelectionMode('start')}>Start</button>
                        <button className={selectionMode === 'pick' ? 'nav-btn nav-btn-active' : 'nav-btn'} onClick={() => setSelectionMode('pick')}>Pick</button>
                        <button className={selectionMode === 'drop' ? 'nav-btn nav-btn-active' : 'nav-btn'} onClick={() => setSelectionMode('drop')}>Drop</button>
                        <button className={selectionMode === 'destination' ? 'nav-btn nav-btn-active' : 'nav-btn'} onClick={() => setSelectionMode('destination')}>End</button>
                    </div>
                    
                    <div className="agent-selector">
                        <span style={{color: '#A0A0A0', fontSize: '0.8rem'}}>AGENT ID:</span>
                        <input 
                            type="number" 
                            min="0" 
                            value={currentAgentIdx} 
                            onChange={(e) => setCurrentAgentIdx(parseInt(e.target.value) || 0)}
                            className="agent-input"
                        />
                    </div>

                    <div className="algorithm-selector">
                        <span style={{color: '#A0A0A0', fontSize: '0.8rem'}}>ALGORITHM:</span>
                        <select 
                            value={algorithm} 
                            onChange={(e) => setAlgorithm(e.target.value)}
                            className="algo-select"
                        >
                            <option value="independent_astar">Independent A*</option>
                            <option value="cooperative_astar">Cooperative A*</option>
                            <option value="hill_climbing">Hill Climbing</option>
                            <option value="cbs">CBS (Conflict-Based Search)</option>
                            <option value="optimized_hc">Optimized Hill Climbing</option>
                        </select>
                    </div>

                    <div className="actions">
                        <button className="nav-btn" onClick={() => { setGrid(Array(GRID_SIZE_H).fill().map(() => Array(GRID_SIZE_W).fill(0))); setAgents([]); }}>Reset</button>
                        <button className="nav-btn find-path-btn" onClick={handleRun}>FIND PATH</button>
                    </div>
                </div>
            </div>

            <div className="grid-visualizer-container">
                <div className="grid-container" style={{ gridTemplateColumns: `repeat(${GRID_SIZE_W}, 30px)` }}>
                    {grid.map((row, r) => 
                        row.map((cell, c) => {
                            let labels = [];
                            let className = 'grid-cell';
                            
                            if (cell === 1) className += ' obstacle';
                            
                            agents.forEach(a => {
                                if (a.start && a.start[0] === r && a.start[1] === c) { labels.push(`S${a.id}`); className += ' start'; }
                                if (a.pick && a.pick[0] === r && a.pick[1] === c) { labels.push(`P${a.id}`); className += ' pick'; }
                                if (a.drop && a.drop[0] === r && a.drop[1] === c) { labels.push(`D${a.id}`); className += ' drop'; }
                                if (a.destination && a.destination[0] === r && a.destination[1] === c) { labels.push(`E${a.id}`); className += ' end'; }
                            });
                            
                            return (
                                <div 
                                    key={`${r}-${c}`} 
                                    className={className}
                                    onClick={() => toggleCell(r, c)}
                                >
                                    {labels.length > 0 && <span className="cell-label">{labels.join(',')}</span>}
                                </div>
                            )
                        })
                    )}
                </div>
            </div>
        </div>
    );
}

export default GridConfigPage;
