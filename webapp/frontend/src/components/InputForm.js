import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './InputForm.css';

const API_URL = 'https://backend-taupe-gamma-78.vercel.app';

const EXAMPLE_DATA = {
  grid_height: 8,
  grid_width: 8,
  obstacles: [[0, 3], [1, 3], [2, 3], [4, 4], [5, 4], [6, 4]],
  start: [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2], [2, 0], [2, 1], [2, 2], [3, 0]],
  pick: [[7, 0], [7, 1], [7, 2], [6, 0], [6, 1], [6, 2], [5, 0], [5, 1], [5, 2], [4, 0]],
  drop: [[0, 7], [1, 7], [2, 7], [0, 6], [1, 6], [2, 6], [0, 5], [1, 5], [2, 5], [0, 4]],
  destination: [[7, 7], [7, 6], [7, 5], [6, 7], [6, 6], [6, 5], [5, 7], [5, 6], [5, 5], [4, 7]]
};

function InputForm({ onSubmit, onSimpleSubmit, loading }) {
  const [mode, setMode] = useState('full');
  const [algorithm, setAlgorithm] = useState('independent_astar');
  const [gridHeight, setGridHeight] = useState(EXAMPLE_DATA.grid_height);
  const [gridWidth, setGridWidth] = useState(EXAMPLE_DATA.grid_width);
  const [obstacles, setObstacles] = useState(EXAMPLE_DATA.obstacles.map(o => o.join(',')).join('; '));
  const [start, setStart] = useState(EXAMPLE_DATA.start.map(s => s.join(',')).join('; '));
  const [pick, setPick] = useState(EXAMPLE_DATA.pick.map(p => p.join(',')).join('; '));
  const [drop, setDrop] = useState(EXAMPLE_DATA.drop.map(d => d.join(',')).join('; '));
  const [destination, setDestination] = useState(EXAMPLE_DATA.destination.map(d => d.join(',')).join('; '));
  const [availableMaps, setAvailableMaps] = useState([]);
  const [selectedMap, setSelectedMap] = useState('custom');
  const [numAgents, setNumAgents] = useState(10);
  const [autoGenerate] = useState(false);

  useEffect(() => {
    const fetchMaps = async () => {
      try {
        const response = await axios.get(`${API_URL}/maps`);
        setAvailableMaps(response.data);
      } catch (err) {
        console.error('Failed to fetch maps:', err);
      }
    };
    fetchMaps();
  }, []);

  const handleMapChange = async (e) => {
    const mapId = e.target.value;
    setSelectedMap(mapId);
    
    if (mapId === 'custom') return;

    try {
      const response = await axios.get(`${API_URL}/maps/${mapId}`);
      const { grid_height, grid_width, obstacles } = response.data;
      setGridHeight(grid_height);
      setGridWidth(grid_width);
      setObstacles(obstacles.map(o => o.join(',')).join('; '));
    } catch (err) {
      console.error('Failed to load map data:', err);
    }
  };

  const parseCoordinates = (text) => {
    if (!text.trim()) return [];
    return text.split(';').map(coord => {
      const parts = coord.trim().split(',');
      if (parts.length < 2) return null;
      // UI uses (row, col) format which matches our backend validation: x = coord[1], y = coord[0]
      return [parseInt(parts[0]), parseInt(parts[1])];
    }).filter(coord => coord !== null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const formData = {
      grid_height: parseInt(gridHeight),
      grid_width: parseInt(gridWidth),
      algorithm: algorithm,
      obstacles: parseCoordinates(obstacles),
    };

    if (autoGenerate) {
      formData.num_agents = parseInt(numAgents);
    } else {
      formData.start = parseCoordinates(start);
      formData.destination = parseCoordinates(destination);
      if (mode === 'full') {
        formData.pick = parseCoordinates(pick);
        formData.drop = parseCoordinates(drop);
      }
    }

    if (mode === 'full') {
      onSubmit(formData);
    } else {
      onSimpleSubmit(formData);
    }
  };

  const loadExample = () => {
    setGridHeight(EXAMPLE_DATA.grid_height);
    setGridWidth(EXAMPLE_DATA.grid_width);
    setObstacles(EXAMPLE_DATA.obstacles.map(o => o.join(',')).join('; '));
    setStart(EXAMPLE_DATA.start.map(s => s.join(',')).join('; '));
    setPick(EXAMPLE_DATA.pick.map(p => p.join(',')).join('; '));
    setDrop(EXAMPLE_DATA.drop.map(d => d.join(',')).join('; '));
    setDestination(EXAMPLE_DATA.destination.map(d => d.join(',')).join('; '));
  };

  return (
    <div className="input-form-container">
      <div className="mode-selector">
        <button
          className={`mode-btn ${mode === 'full' ? 'active' : ''}`}
          onClick={() => setMode('full')}
        >
          Full Route (Start → Pick → Drop → Dest)
        </button>
        <button
          className={`mode-btn ${mode === 'simple' ? 'active' : ''}`}
          onClick={() => setMode('simple')}
        >
          Simple (Start → Dest)
        </button>
      </div>

      <div className="form-section">
        <h3>Algorithm</h3>
        <div className="form-group">
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
            className="algorithm-select"
          >
            <option value="independent_astar">Independent A*</option>
            <option value="cooperative_astar">Cooperative A*</option>
            <option value="hill_climbing">Hill Climbing</option>
          </select>
        </div>
        <p className="help-text" style={{fontSize: '0.85em', color: '#666'}}>
          Note: Hill Climbing is recommended for multiple agents.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="input-form">
        <div className="form-section">
          <h3>Grid Selection</h3>
          <div className="form-group" style={{ marginBottom: '1rem' }}>
            <label>Number of Agents:</label>
            <input 
              type="number" 
              value={numAgents} 
              onChange={(e) => {
                const val = Math.max(1, parseInt(e.target.value) || 1);
                setNumAgents(val);
                // If auto-generate is off, we still use this to cap inputs or prompt generation
              }}
              min="1"
              max="100"
              className="number-input"
            />
          </div>
          <div className="form-group">
            <label>Choose a Grid Template:</label>
            <select value={selectedMap} onChange={handleMapChange} className="map-select">
              <option value="custom">Custom Grid / Manual Entry</option>
              {availableMaps.reduce((acc, map) => {
                const category = map.category;
                if (!acc[category]) acc[category] = [];
                acc[category].push(map);
                return acc;
              }, {}) && Object.entries(availableMaps.reduce((acc, map) => {
                const category = map.category;
                if (!acc[category]) acc[category] = [];
                acc[category].push(map);
                return acc;
              }, {})).map(([category, maps]) => (
                <optgroup label={category} key={category}>
                  {maps.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </div>

        <div className="form-section">
          <h3>Grid Configuration</h3>
          <div className="form-row">
            <div className="form-group">
              <label>Grid Height (m):</label>
              <input
                type="number"
                value={gridHeight}
                onChange={(e) => setGridHeight(e.target.value)}
                min="1"
                required
              />
            </div>
            <div className="form-group">
              <label>Grid Width (n):</label>
              <input
                type="number"
                value={gridWidth}
                onChange={(e) => setGridWidth(e.target.value)}
                min="1"
                required
              />
            </div>
          </div>
        </div>

        <div className="form-section">
          <h3>Obstacles</h3>
          <div className="form-group">
            <label>Coordinates (format: x,y; x,y; ...):</label>
            <input
              type="text"
              value={obstacles}
              onChange={(e) => setObstacles(e.target.value)}
              placeholder="0,13; 2,1; 2,15"
            />
          </div>
        </div>

        <div className="form-section">
          <h3>Agent Positions</h3>
          <div className="form-group">
            <label>Start Positions:</label>
            <input
              type="text"
              value={start}
              onChange={(e) => setStart(e.target.value)}
              placeholder="0,0; 5,9; 1,7"
              required
            />
          </div>

          {mode === 'full' && (
            <>
              <div className="form-group">
                <label>Pickup Positions:</label>
                <input
                  type="text"
                  value={pick}
                  onChange={(e) => setPick(e.target.value)}
                  placeholder="5,0; 4,6; 1,12"
                  required
                />
              </div>

              <div className="form-group">
                <label>Drop Positions:</label>
                <input
                  type="text"
                  value={drop}
                  onChange={(e) => setDrop(e.target.value)}
                  placeholder="0,8; 5,5; 3,15"
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label>Destination Positions:</label>
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="3,12; 0,10; 0,5"
              required
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="button" onClick={loadExample} className="btn-secondary">
            Load Example
          </button>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Computing...' : 'Find Paths'}
          </button>
        </div>
      </form>

      <div className="help-text">
        <p><strong>How to use:</strong></p>
        <ul>
          <li>Enter coordinates as comma-separated pairs: x,y</li>
          <li>Separate multiple coordinates with semicolons</li>
          <li>Number of agents determined by start positions count</li>
          <li>All position lists must have same number of agents</li>
        </ul>
      </div>
    </div>
  );
}

export default InputForm;
