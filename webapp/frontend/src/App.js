import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import GridVisualization from './components/GridVisualization';
import InputForm from './components/InputForm';
import BenchmarkPage from './components/BenchmarkPage';
import GridConfigPage from './components/GridConfigPage';
import GridMapPage from './components/GridMapPage';
import { getApiUrl } from './config/api';

function App() {
  const [activePage, setActivePage] = useState('solver');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [useSmallCells, setUseSmallCells] = useState(false);
  const [gridMapUnlocked, setGridMapUnlocked] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [passwordAttempt, setPasswordAttempt] = useState('');
  const [passwordError, setPasswordError] = useState(null);

  const GRIDMAP_PASSWORD = (process.env.REACT_APP_GRIDMAP_PASSWORD || '').trim();

  const handlePasswordSubmit = () => {
    if (passwordAttempt.trim() === GRIDMAP_PASSWORD && GRIDMAP_PASSWORD !== '') {
      setGridMapUnlocked(true);
      setShowPasswordModal(false);
      setPasswordAttempt('');
      setPasswordError(null);
      setActivePage('grid-map');
    } else {
      if (GRIDMAP_PASSWORD === '') {
        setPasswordError('System Error: Background password not configured in environment.');
      } else {
        setPasswordError('Incorrect password.');
      }
    }
  };

  const handleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const apiUrl = await getApiUrl();
      console.log('Sending request to:', `${apiUrl}/api/find-path`);
      console.log('Payload:', formData);
      const response = await axios.post(`${apiUrl}/api/find-path`, formData);
      console.log('Response:', response.data);

      if (response.data.success) {
        // Build waypoints array mapped to agent paths
        const numAgents = response.data.num_agents || (response.data.paths ? response.data.paths.length : 0);
        const waypoints = [];
        for (let i = 0; i < numAgents; i++) {
          waypoints.push({
            start: formData.start ? formData.start[i] : null,
            pick: formData.pick ? formData.pick[i] : null,
            drop: formData.drop ? formData.drop[i] : null,
            destination: formData.destination ? formData.destination[i] : null,
          });
        }
        setResult({ ...response.data, waypoints });
        setUseSmallCells(!!formData.predefined_map);
      } else {
        setError(response.data.message || 'Failed to find paths');
      }
    } catch (err) {
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSimpleSubmit = async (formData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const apiUrl = await getApiUrl();
      console.log('Sending request to:', `${apiUrl}/api/find-simple-path`);
      console.log('Payload:', formData);
      const response = await axios.post(`${apiUrl}/api/find-simple-path`, formData);
      console.log('Response:', response.data);

      if (response.data.success) {
        setResult(response.data);
        setUseSmallCells(!!formData.predefined_map);
      } else {
        setError(response.data.message || 'Failed to find paths');
      }
    } catch (err) {
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      setError(err.response?.data?.detail || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1> Multi-Agent Path Finding</h1>
        <p>Find paths with CBS and benchmark classical AI search algorithms</p>
        <div className="app-nav">
          <button
            className={activePage === 'solver' ? 'nav-btn nav-btn-active' : 'nav-btn'}
            onClick={() => setActivePage('solver')}
          >
            Solver
          </button>
          <button
            className={activePage === 'benchmark' ? 'nav-btn nav-btn-active' : 'nav-btn'}
            onClick={() => setActivePage('benchmark')}
          >
            Benchmark
          </button>
          <button
            className={activePage === 'grid-config' ? 'nav-btn nav-btn-active' : 'nav-btn'}
            onClick={() => setActivePage('grid-config')}
          >
            MANUAL GRID CONFIG
          </button>
          <button
            className={activePage === 'grid-map' ? 'nav-btn nav-btn-active' : 'nav-btn'}
            onClick={() => {
              if (gridMapUnlocked) {
                setActivePage('grid-map');
              } else {
                setShowPasswordModal(true);
              }
            }}
          >
            GRID MAP
          </button>
        </div>
      </header>

      <main className="App-main">
        <div className="container">
          {activePage === 'solver' && (
            <>
              <InputForm
                onSubmit={handleSubmit}
                onSimpleSubmit={handleSimpleSubmit}
                loading={loading}
              />

              {loading && (
                <div className="loading">
                  <div className="spinner"></div>
                  <p>Computing optimal paths...</p>
                </div>
              )}

              {error && (
                <div className="error-message">
                  <h3>❗ SYSTEM ERROR ALERT</h3>
                  <div className="error-details">
                    <p>{error}</p>
                  </div>
                  <div className="error-actions">
                    <p style={{fontSize: '0.8rem', color: '#A0A0A0', marginTop: '10px'}}>
                      Check grid boundaries and ensure start/goal points are not on obstacles ('T' cells).
                    </p>
                  </div>
                </div>
              )}

              {result && (
                <div className="results">
                  <div className="results-header">
                    <h2>✅ Paths Found Successfully!</h2>
                    <div className="stats">
                      <div className="stat">
                        <span className="stat-label">Agents:</span>
                        <span className="stat-value">{result.num_agents}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Total Cost:</span>
                        <span className="stat-value">{result.total_cost}</span>
                      </div>
                    </div>
                  </div>

                  <GridVisualization
                    paths={result.paths}
                    gridHeight={result.grid_height}
                    gridWidth={result.grid_width}
                    obstacles={result.obstacles}
                    waypoints={result.waypoints || []}
                    smallCells={useSmallCells}
                  />

                  <div className="path-details">
                    <h3>Path Details</h3>
                    {result.paths.map((path, idx) => (
                      <div key={idx} className="agent-path">
                        <h4>Agent {idx + 1} (Length: {path.length})</h4>
                        <div className="path-coordinates">
                          {path.map((coord, i) => (
                            <span key={i} className="coordinate">
                              ({coord[0]}, {coord[1]})
                              {i < path.length - 1 && ' → '}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {activePage === 'benchmark' && <BenchmarkPage />}
          {activePage === 'grid-config' && (
            <GridConfigPage onRunSolver={(formData) => {
              setActivePage('solver');
              handleSubmit(formData);
            }} />
          )}
          {activePage === 'grid-map' && gridMapUnlocked && (
            <GridMapPage onRunSolver={(formData) => {
              setActivePage('solver');
              handleSubmit(formData);
            }} />
          )}

          {activePage === 'grid-map' && !gridMapUnlocked && (
            <div className="locked-page">
              <h3>Sensitive content — access restricted</h3>
              <p>This section requires a password. Click below to enter the password.</p>
              <div style={{marginTop: 12}}>
                <button className="nav-btn" onClick={() => setShowPasswordModal(true)}>Enter Password</button>
              </div>
            </div>
          )}

          {showPasswordModal && (
            <div className="modal-overlay">
              <div className="modal">
                <h3>Enter GRID MAP Password</h3>
                <p style={{color: 'var(--text-muted)', marginTop: 6}}>Password is stored in environment variable.</p>
                <input
                  type="password"
                  value={passwordAttempt}
                  onChange={(e) => setPasswordAttempt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handlePasswordSubmit();
                  }}
                  placeholder="Password"
                  className="password-input"
                  autoFocus
                />
                {passwordError && <div className="error-details" style={{marginTop:8, color: '#ff4d4d'}}>{passwordError}</div>}
                <div className="modal-actions">
                  <button className="nav-btn" onClick={handlePasswordSubmit}>Submit</button>
                  <button className="nav-btn" onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordAttempt('');
                    setPasswordError(null);
                  }} style={{marginLeft: 8}}>Cancel</button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="App-footer">
      </footer>
    </div>
  );
}

export default App;
