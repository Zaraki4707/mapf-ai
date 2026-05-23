import React, { useState } from 'react';
import { BarChart } from '@mui/x-charts/BarChart';
import { LineChart } from '@mui/x-charts/LineChart';
import './BenchmarkPage.css';

class ChartErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    if (this.props.onError) {
      this.props.onError(error);
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

const CONFLICT_DATA = [
  ['Independent A*', 2600],
  ['Cooperative A*', 1],
  ['Hill Climbing', 0],
  ['CBS', 0],
];

const COST_DATA = [
  ['Test Case 1', 13, 8],
  ['Test Case 2', 14, 9],
  ['Test Case 3', 10, 8],
];

const MAKESPAN_DATA = [
  { agents: 10, makespan: 183 },
  { agents: 20, makespan: 217 },
  { agents: 25, makespan: 186 },
];

const SUCCESS_RATE_DATA = [
  { agents: 5, independentAStar: 0.5, cooperativeAStar: 1.0 },
  { agents: 10, independentAStar: 0.4, cooperativeAStar: 1.0 },
  { agents: 20, independentAStar: 0.0, cooperativeAStar: 1.0 },
];

export default function BenchmarkPage() {
  const [lineChartFailed, setLineChartFailed] = useState(false);

  const conflictLabels = CONFLICT_DATA.map(([label]) => label);
  const conflictValues = CONFLICT_DATA.map(([, value]) => value);

  const costLabels = COST_DATA.map(([label]) => label);
  const costBefore = COST_DATA.map(([, before]) => before);
  const costAfter = COST_DATA.map(([, , after]) => after);

  const makespanAgents = MAKESPAN_DATA.map(d => d.agents);
  const makespanValues = MAKESPAN_DATA.map(d => d.makespan);
  const [makespanFailed, setMakespanFailed] = useState(false);
  const successAgents = SUCCESS_RATE_DATA.map(d => d.agents);
  const successIndependent = SUCCESS_RATE_DATA.map(d => d.independentAStar);
  const successCooperative = SUCCESS_RATE_DATA.map(d => d.cooperativeAStar);
  const [successFailed, setSuccessFailed] = useState(false);

  const fallbackConflictsChart = (
    <div className="bars-grid">
      {CONFLICT_DATA.map(([label, value]) => (
        <div key={label} className="algo-bar-card">
          <div className="algo-bar-head">
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
          <div className="algo-bar-track">
            <div
              className="algo-bar-fill"
              style={{ width: `${Math.max(5, (value / Math.max(...conflictValues, 1)) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );

  const fallbackCostChart = (
    <div className="bars-grid">
      {COST_DATA.map(([label, before, after]) => (
        <div key={label} className="algo-bar-card">
          <div className="algo-bar-head">
            <span>{label}</span>
            <strong>Before: {before} · After: {after}</strong>
          </div>
          <div style={{display: 'flex', gap: 8, marginTop: 8}}>
            <div style={{flex: 1}}>
              <div className="algo-bar-track">
                <div
                  className="algo-bar-fill"
                  style={{ background: 'linear-gradient(90deg,#e74c3c,#f1c40f)', width: `${Math.max(5, (before / Math.max(...costBefore, 1)) * 100)}%` }}
                />
              </div>
              <div style={{fontSize: 12, marginTop: 6}}>Before: {before}</div>
            </div>
            <div style={{flex: 1}}>
              <div className="algo-bar-track">
                <div
                  className="algo-bar-fill"
                  style={{ background: 'linear-gradient(90deg,#2ecc71,#3498db)', width: `${Math.max(5, (after / Math.max(...costBefore, 1)) * 100)}%` }}
                />
              </div>
              <div style={{fontSize: 12, marginTop: 6}}>After: {after}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const fallbackMakespanChart = (
    <div className="bars-grid">
      {MAKESPAN_DATA.map(({ agents, makespan }) => (
        <div key={agents} className="algo-bar-card">
          <div className="algo-bar-head">
            <span>{agents} agents</span>
            <strong>{makespan}</strong>
          </div>
          <div className="algo-bar-track">
            <div
              className="algo-bar-fill"
              style={{ width: `${Math.max(5, (makespan / Math.max(...makespanValues, 1)) * 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );

  const fallbackSuccessChart = (
    <div className="bars-grid">
      {SUCCESS_RATE_DATA.map(({ agents, independentAStar, cooperativeAStar }) => (
        <div key={agents} className="algo-bar-card">
          <div className="algo-bar-head">
            <span>{agents} agents</span>
            <strong>{Math.round(cooperativeAStar * 100)}% coop · {Math.round(independentAStar * 100)}% ind</strong>
          </div>
          <div style={{display: 'flex', gap: 8, marginTop: 8}}>
            <div style={{flex: 1}}>
              <div className="algo-bar-track">
                <div
                  className="algo-bar-fill"
                  style={{ background: 'linear-gradient(90deg,#9b59b6,#8e44ad)', width: `${Math.max(5, (cooperativeAStar * 100) / Math.max(...[100], 1))}%` }}
                />
              </div>
              <div style={{fontSize: 12, marginTop: 6}}>Cooperative: {Math.round(cooperativeAStar * 100)}%</div>
            </div>
            <div style={{flex: 1}}>
              <div className="algo-bar-track">
                <div
                  className="algo-bar-fill"
                  style={{ background: 'linear-gradient(90deg,#f39c12,#e67e22)', width: `${Math.max(5, (independentAStar * 100) / Math.max(...[100], 1))}%` }}
                />
              </div>
              <div style={{fontSize: 12, marginTop: 6}}>Independent: {Math.round(independentAStar * 100)}%</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <section className="benchmark-page">
      <div className="conflicts-chart-wrap">
        <div className="conflicts-chart-head">
          <h3>Conflicts by Algorithm -tested on +500 agents in one grid-</h3>
        </div>

        {lineChartFailed ? (
          fallbackConflictsChart
        ) : (
          <ChartErrorBoundary fallback={fallbackConflictsChart} onError={() => setLineChartFailed(true)}>
            <BarChart
              xAxis={[{ scaleType: 'band', data: conflictLabels }]}
              series={[{ data: conflictValues, label: 'Conflicts' }]}
              width={500}
              height={300}
            />
          </ChartErrorBoundary>
        )}
      </div>

      <div className="conflicts-chart-wrap">
        <div className="conflicts-chart-head">
          <h3>Cost Reduction using Hill Climbing</h3>
        </div>

        {lineChartFailed ? (
          fallbackCostChart
        ) : (
          <ChartErrorBoundary fallback={fallbackCostChart} onError={() => setLineChartFailed(true)}>
            <BarChart
              xAxis={[{ scaleType: 'band', data: costLabels }]}
              series={[{ data: costBefore, label: 'Before' }, { data: costAfter, label: 'After' }]}
              width={700}
              height={360}
            />
          </ChartErrorBoundary>
        )}
      </div>

      <div className="conflicts-chart-wrap">
        <div className="conflicts-chart-head">
          <h3>Makespan vs Agents</h3>
        </div>

        {makespanFailed ? (
          fallbackMakespanChart
        ) : (
          <ChartErrorBoundary fallback={fallbackMakespanChart} onError={() => setMakespanFailed(true)}>
            <LineChart
              xAxis={[{ data: makespanAgents }]}
              series={[{ data: makespanValues, label: 'Makespan' }]}
              height={300}
              width={700}
            />
          </ChartErrorBoundary>
        )}
      </div>

      <div className="conflicts-chart-wrap">
        <div className="conflicts-chart-head">
          <h3>Success Rate vs Agents</h3>
        </div>

        {successFailed ? (
          fallbackSuccessChart
        ) : (
          <ChartErrorBoundary fallback={fallbackSuccessChart} onError={() => setSuccessFailed(true)}>
            <LineChart
              xAxis={[{ data: successAgents }]}
              series={[{ data: successIndependent, label: 'Independent A*' }, { data: successCooperative, label: 'Cooperative A*' }]}
              height={300}
              width={700}
            />
          </ChartErrorBoundary>
        )}
      </div>
    </section>
  );
}
