import React, { useState } from 'react';
import { BarChart } from '@mui/x-charts/BarChart';
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

export default function BenchmarkPage() {
  const [lineChartFailed, setLineChartFailed] = useState(false);

  const conflictLabels = CONFLICT_DATA.map(([label]) => label);
  const conflictValues = CONFLICT_DATA.map(([, value]) => value);

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

  return (
    <section className="benchmark-page">
      <div className="conflicts-chart-wrap">
        <div className="conflicts-chart-head">
          <h3>Conflicts by Algorithm</h3>
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
    </section>
  );
}
