import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import GridVisualization from './components/GridVisualization';
import InputForm from './components/InputForm';
import BenchmarkPage from './components/BenchmarkPage';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [activePage, setActivePage] = useState('solver');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (formData) => {
    console.log('Sending request to:', `${API_URL}/find-path`);
    console.log('Payload:', formData);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/find-path`, formData);
      console.log('Response:', response.data);

      if (response.data.success) {
        setResult(response.data);
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
    console.log('Sending request to:', `${API_URL}/find-simple-path`);
    console.log('Payload:', formData);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/find-simple-path`, formData);
      console.log('Response:', response.data);

      if (response.data.success) {
        setResult(response.data);
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
        <h1>🤖 Multi-Agent Path Finding</h1>
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
        </div>
      </main>

      <footer className="App-footer">
        <p>Powered by Conflict-Based Search (CBS) and classical search benchmarks</p>
      </footer>
    </div>
  );
}

export default App;
