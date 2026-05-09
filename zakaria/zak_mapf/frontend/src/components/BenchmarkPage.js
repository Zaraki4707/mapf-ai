import React, { useMemo, useState } from 'react';
import './BenchmarkPage.css';

const MOVES = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
];

function keyOf([r, c]) {
  return `${r},${c}`;
}

function parseKey(key) {
  return key.split(',').map(Number);
}

function manhattan(a, b) {
  return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
}

function neighbors(state, rows, cols, obstacles) {
  const [r, c] = state;
  const out = [];

  for (const [dr, dc] of MOVES) {
    const nr = r + dr;
    const nc = c + dc;
    const nk = `${nr},${nc}`;
    if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !obstacles.has(nk)) {
      out.push([nr, nc]);
    }
  }

  return out;
}

function reconstructPath(parent, goal) {
  const gk = keyOf(goal);
  if (!parent.has(gk)) {
    return null;
  }

  const path = [];
  let cur = gk;
  while (cur !== null) {
    path.push(parseKey(cur));
    cur = parent.get(cur);
  }

  path.reverse();
  return path;
}

function bfs(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);
  const queue = [start];
  let head = 0;
  const parent = new Map([[sk, null]]);
  const visited = new Set([sk]);
  let expanded = 0;

  while (head < queue.length) {
    const cur = queue[head++];
    expanded += 1;

    if (keyOf(cur) === gk) {
      return { path: reconstructPath(parent, goal), expanded };
    }

    for (const nxt of neighbors(cur, rows, cols, obstacles)) {
      const nk = keyOf(nxt);
      if (!visited.has(nk)) {
        visited.add(nk);
        parent.set(nk, keyOf(cur));
        queue.push(nxt);
      }
    }
  }

  return { path: null, expanded };
}

function dfs(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);
  const stack = [start];
  const parent = new Map([[sk, null]]);
  const visited = new Set([sk]);
  let expanded = 0;

  while (stack.length) {
    const cur = stack.pop();
    expanded += 1;

    if (keyOf(cur) === gk) {
      return { path: reconstructPath(parent, goal), expanded };
    }

    const nbrs = neighbors(cur, rows, cols, obstacles);
    for (let i = nbrs.length - 1; i >= 0; i -= 1) {
      const nxt = nbrs[i];
      const nk = keyOf(nxt);
      if (!visited.has(nk)) {
        visited.add(nk);
        parent.set(nk, keyOf(cur));
        stack.push(nxt);
      }
    }
  }

  return { path: null, expanded };
}

function ucs(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);
  const pq = [{ priority: 0, cost: 0, state: start }];
  const parent = new Map([[sk, null]]);
  const bestCost = new Map([[sk, 0]]);
  let expanded = 0;

  while (pq.length) {
    pq.sort((a, b) => a.priority - b.priority);
    const curNode = pq.shift();
    const ck = keyOf(curNode.state);

    if (curNode.cost > (bestCost.get(ck) ?? Number.POSITIVE_INFINITY)) {
      continue;
    }

    expanded += 1;

    if (ck === gk) {
      return { path: reconstructPath(parent, goal), expanded };
    }

    for (const nxt of neighbors(curNode.state, rows, cols, obstacles)) {
      const nk = keyOf(nxt);
      const nc = curNode.cost + 1;
      if (nc < (bestCost.get(nk) ?? Number.POSITIVE_INFINITY)) {
        bestCost.set(nk, nc);
        parent.set(nk, ck);
        pq.push({ priority: nc, cost: nc, state: nxt });
      }
    }
  }

  return { path: null, expanded };
}

function greedy(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);
  const pq = [{ priority: manhattan(start, goal), state: start }];
  const parent = new Map([[sk, null]]);
  const visited = new Set([sk]);
  let expanded = 0;

  while (pq.length) {
    pq.sort((a, b) => a.priority - b.priority);
    const cur = pq.shift().state;
    const ck = keyOf(cur);
    expanded += 1;

    if (ck === gk) {
      return { path: reconstructPath(parent, goal), expanded };
    }

    for (const nxt of neighbors(cur, rows, cols, obstacles)) {
      const nk = keyOf(nxt);
      if (!visited.has(nk)) {
        visited.add(nk);
        parent.set(nk, ck);
        pq.push({ priority: manhattan(nxt, goal), state: nxt });
      }
    }
  }

  return { path: null, expanded };
}

function astar(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);
  const pq = [{ priority: manhattan(start, goal), cost: 0, state: start }];
  const parent = new Map([[sk, null]]);
  const bestG = new Map([[sk, 0]]);
  let expanded = 0;

  while (pq.length) {
    pq.sort((a, b) => a.priority - b.priority);
    const curNode = pq.shift();
    const ck = keyOf(curNode.state);

    if (curNode.cost > (bestG.get(ck) ?? Number.POSITIVE_INFINITY)) {
      continue;
    }

    expanded += 1;

    if (ck === gk) {
      return { path: reconstructPath(parent, goal), expanded };
    }

    for (const nxt of neighbors(curNode.state, rows, cols, obstacles)) {
      const nk = keyOf(nxt);
      const ng = curNode.cost + 1;
      if (ng < (bestG.get(nk) ?? Number.POSITIVE_INFINITY)) {
        bestG.set(nk, ng);
        parent.set(nk, ck);
        pq.push({ priority: ng + manhattan(nxt, goal), cost: ng, state: nxt });
      }
    }
  }

  return { path: null, expanded };
}

function depthLimitedDfs(start, goal, limit, rows, cols, obstacles) {
  const gk = keyOf(goal);
  const stack = [{ state: start, depth: 0, parent: null }];
  const parent = new Map();
  const bestDepth = new Map([[keyOf(start), 0]]);
  let expanded = 0;

  while (stack.length) {
    const node = stack.pop();
    const nk = keyOf(node.state);

    if (parent.has(nk)) {
      continue;
    }

    parent.set(nk, node.parent);
    expanded += 1;

    if (nk === gk) {
      return { path: reconstructPath(parent, goal), expanded, found: true };
    }

    if (node.depth === limit) {
      continue;
    }

    const nbrs = neighbors(node.state, rows, cols, obstacles);
    for (let i = nbrs.length - 1; i >= 0; i -= 1) {
      const nxt = nbrs[i];
      const nextKey = keyOf(nxt);
      const nextDepth = node.depth + 1;
      if (nextDepth <= limit && nextDepth < (bestDepth.get(nextKey) ?? Number.POSITIVE_INFINITY)) {
        bestDepth.set(nextKey, nextDepth);
        stack.push({ state: nxt, depth: nextDepth, parent: nk });
      }
    }
  }

  return { path: null, expanded, found: false };
}

function iddfs(start, goal, rows, cols, obstacles) {
  const maxDepth = rows * cols;
  let totalExpanded = 0;

  for (let d = 0; d <= maxDepth; d += 1) {
    const res = depthLimitedDfs(start, goal, d, rows, cols, obstacles);
    totalExpanded += res.expanded;
    if (res.found) {
      return { path: res.path, expanded: totalExpanded };
    }
  }

  return { path: null, expanded: totalExpanded };
}

function bidirectionalBfs(start, goal, rows, cols, obstacles) {
  const sk = keyOf(start);
  const gk = keyOf(goal);

  if (sk === gk) {
    return { path: [start], expanded: 1 };
  }

  let q1 = [start];
  let q2 = [goal];

  const p1 = new Map([[sk, null]]);
  const p2 = new Map([[gk, null]]);
  const v1 = new Set([sk]);
  const v2 = new Set([gk]);

  let expanded = 0;

  function expandFrontier(queue, ownVisited, otherVisited, ownParent) {
    const next = [];

    for (const cur of queue) {
      expanded += 1;
      const ck = keyOf(cur);

      for (const nxt of neighbors(cur, rows, cols, obstacles)) {
        const nk = keyOf(nxt);
        if (ownVisited.has(nk)) {
          continue;
        }

        ownVisited.add(nk);
        ownParent.set(nk, ck);

        if (otherVisited.has(nk)) {
          return { meet: nk, frontier: next };
        }

        next.push(nxt);
      }
    }

    return { meet: null, frontier: next };
  }

  while (q1.length && q2.length) {
    const fromStart = q1.length <= q2.length;
    const side = fromStart ? expandFrontier(q1, v1, v2, p1) : expandFrontier(q2, v2, v1, p2);

    if (side.meet) {
      const left = [];
      let cur = side.meet;
      while (cur !== null) {
        left.push(parseKey(cur));
        cur = p1.get(cur);
      }
      left.reverse();

      const right = [];
      cur = p2.get(side.meet);
      while (cur !== null) {
        right.push(parseKey(cur));
        cur = p2.get(cur);
      }

      return { path: left.concat(right), expanded };
    }

    if (fromStart) {
      q1 = side.frontier;
    } else {
      q2 = side.frontier;
    }
  }

  return { path: null, expanded };
}

const ALGORITHMS = [
  { name: 'BFS', fn: bfs },
  { name: 'DFS', fn: dfs },
  { name: 'UCS (Dijkstra)', fn: ucs },
  { name: 'Greedy Best-First', fn: greedy },
  { name: 'A*', fn: astar },
  { name: 'IDDFS', fn: iddfs },
  { name: 'Bidirectional BFS', fn: bidirectionalBfs },
];

function createScenario(rows, cols, obstaclePercent) {
  const start = [0, 0];
  const goal = [rows - 1, cols - 1];
  const obstacles = new Set();

  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      const isEndpoint = (r === start[0] && c === start[1]) || (r === goal[0] && c === goal[1]);
      if (isEndpoint) {
        continue;
      }

      if (Math.random() < obstaclePercent / 100) {
        obstacles.add(`${r},${c}`);
      }
    }
  }

  return { start, goal, obstacles };
}

export default function BenchmarkPage() {
  const [rows, setRows] = useState(20);
  const [cols, setCols] = useState(28);
  const [obstaclePercent, setObstaclePercent] = useState(18);
  const [repeats, setRepeats] = useState(5);
  const [scenario, setScenario] = useState(() => createScenario(20, 28, 18));
  const [results, setResults] = useState([]);
  const [lastError, setLastError] = useState('');

  const bestTime = useMemo(() => {
    const ok = results.filter((r) => r.found);
    if (!ok.length) {
      return null;
    }
    return Math.min(...ok.map((r) => r.avgMs));
  }, [results]);

  const runBenchmark = () => {
    try {
      setLastError('');
      const runRows = Number(rows);
      const runCols = Number(cols);
      const runRepeats = Number(repeats);

      if (runRows < 5 || runCols < 5 || runRepeats < 1) {
        setLastError('Rows/Cols must be >= 5 and repeats must be >= 1.');
        return;
      }

      const nextScenario = createScenario(runRows, runCols, Number(obstaclePercent));
      setScenario(nextScenario);

      const benchmarkRows = [];

      for (const algo of ALGORITHMS) {
        const times = [];
        let expanded = 0;
        let path = null;

        for (let i = 0; i < runRepeats; i += 1) {
          const t0 = performance.now();
          const res = algo.fn(nextScenario.start, nextScenario.goal, runRows, runCols, nextScenario.obstacles);
          const t1 = performance.now();

          times.push(t1 - t0);
          if (path === null) {
            path = res.path;
            expanded = res.expanded;
          }
        }

        const avgMs = times.reduce((acc, t) => acc + t, 0) / times.length;
        benchmarkRows.push({
          algorithm: algo.name,
          found: !!path,
          pathLength: path ? path.length - 1 : null,
          expanded,
          avgMs,
        });
      }

      benchmarkRows.sort((a, b) => a.avgMs - b.avgMs);
      setResults(benchmarkRows);
    } catch (e) {
      setLastError(e.message || 'Benchmark failed.');
    }
  };

  return (
    <section className="benchmark-page">
      <div className="benchmark-head">
        <h2>Classical AI Search Benchmark</h2>
        <p>Compare runtime, path quality, and search effort on the same grid scenario.</p>
      </div>

      <div className="benchmark-controls">
        <label>
          Rows
          <input type="number" min="5" max="80" value={rows} onChange={(e) => setRows(e.target.value)} />
        </label>
        <label>
          Columns
          <input type="number" min="5" max="120" value={cols} onChange={(e) => setCols(e.target.value)} />
        </label>
        <label>
          Obstacles (%)
          <input type="number" min="0" max="60" value={obstaclePercent} onChange={(e) => setObstaclePercent(e.target.value)} />
        </label>
        <label>
          Repeats
          <input type="number" min="1" max="30" value={repeats} onChange={(e) => setRepeats(e.target.value)} />
        </label>
        <button className="run-btn" onClick={runBenchmark}>Run Benchmark</button>
      </div>

      {lastError && (
        <div className="benchmark-error">
          <strong>Error:</strong> {lastError}
        </div>
      )}

      <div className="benchmark-meta">
        <span>Start: ({scenario.start[0]}, {scenario.start[1]})</span>
        <span>Goal: ({scenario.goal[0]}, {scenario.goal[1]})</span>
        <span>Obstacles: {scenario.obstacles.size}</span>
      </div>

      {results.length > 0 && (
        <>
          <div className="benchmark-table-wrap">
            <table className="benchmark-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>Found</th>
                  <th>Path Length</th>
                  <th>Nodes Expanded</th>
                  <th>Avg Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                {results.map((row) => (
                  <tr key={row.algorithm} className={bestTime !== null && row.avgMs === bestTime ? 'best-row' : ''}>
                    <td>{row.algorithm}</td>
                    <td>{row.found ? 'Yes' : 'No'}</td>
                    <td>{row.pathLength ?? '-'}</td>
                    <td>{row.expanded}</td>
                    <td>{row.avgMs.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="bars-grid">
            {results.map((row) => (
              <div key={`${row.algorithm}-bar`} className="algo-bar-card">
                <div className="algo-bar-head">
                  <span>{row.algorithm}</span>
                  <strong>{row.avgMs.toFixed(3)} ms</strong>
                </div>
                <div className="algo-bar-track">
                  <div
                    className="algo-bar-fill"
                    style={{
                      width: `${Math.max(5, (row.avgMs / Math.max(...results.map((r) => r.avgMs))) * 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
