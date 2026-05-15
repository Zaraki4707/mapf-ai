# Webapp Report

## Overview
This repository contains a Multi-Agent Path Finding (MAPF) web application consisting of:
- A React single-page frontend (CRA + CRACO) providing a Solver UI, Grid editor, and a Benchmark visualization.
- A Python FastAPI backend implementing pathfinding algorithms and map loading utilities.
- Deployment configured for Vercel (separate frontend and backend projects/aliases).

---

## Technologies
- Frontend
  - React 18 (Create React App) with `craco` used for webpack tweaks.
  - UI: Material UI (`@mui/material`) and charts via `@mui/x-charts` and `recharts`.
  - HTTP: `axios` for API calls.
  - Styling: plain CSS modules under `src/components/*.css`.
- Backend
  - Python 3.x with FastAPI, run by Uvicorn (production on Vercel as a serverless function/container via `main.py`).
  - Algorithms implemented in pure Python (A*, BFS, DFS, UCS/Dijkstra, IDDFS, bidirectional BFS, Cooperative/Independent A*, CBS, hill-climbing).
  - Data models: Pydantic models under `app/models.py`.
- Deployment / Dev tools
  - Vercel for both frontend and backend projects.
  - `craco.config.js` present to patch webpack's source-map-loader for `@mui/x-charts` issues on build.

---

## Architecture & Logic
- Frontend (SPA)
  - Entry: `src/index.js` → `src/App.js` which switches pages: `Solver`, `Benchmark`, `Grid Config`, `Grid Map`.
  - Key components:
    - `src/components/InputForm.js` — form UI for solver input and payload creation.
    - `src/components/GridVisualization.js` — renders found paths on grid using the `paths` and `obstacles` returned by backend.
    - `src/components/BenchmarkPage.js` — conflicts visualization (bars chart); previously had an interactive benchmark runner but now shows chart-only bars.
    - `src/components/GridConfigPage.js`, `GridMapPage.js` — manual grid builder and map-based inputs.
  - API target: `src/App.js` uses `REACT_APP_API_URL` (fallback to previously configured Vercel backend URL). In development it targets `http://localhost:8000`.
- Backend
  - Entry: `main.py` (FastAPI app). Routers in `app/routers/` include:
    - `app/routers/pathfinder.py` — endpoints:
      - `POST /api/find-path` — full route planner (start→pick→drop→destination).
      - `POST /api/find-simple-path` — simple start→destination planner.
    - `app/routers/maps.py` — GET endpoints to list and fetch predefined maps.
  - Internals: `algorithms/` contains the pathfinding implementations and helpers (`grid.py`, `planner.py`, `cbs.py`, `independent_astar.py`, `cooperative_astar.py`, etc.).
  - Map parsing and utilities live under `app/utils/map_loader.py` and `app/maps/` contains included map files.
  - CORS: configured in `main.py` — ensure the production frontend origin (e.g. `https://mapf-ai.vercel.app`) is allowed.

---

## Performance & Speed
- Frontend
  - Charts and visualization are client-side; rendering complexity scales with grid size and number of agents when drawing paths.
  - Build optimizations via CRA production build (`npm run build`) and CRACO webpack overrides for problematic libraries.
- Backend
  - Algorithmic complexity varies by algorithm:
    - BFS/DFS: O(|V| + |E|) in grid terms; worst-case expands nearly all cells.
    - A*/UCS/Dijkstra: A* improves average-case via heuristic (Manhattan) — performance depends on obstacle density and heuristic admissibility.
    - CBS and cooperative planners: combinatorial; runtime grows steeply with number of agents and conflict density — suitable for small-to-moderate agent counts.
  - Included maps vary (small → very-large) under `webapp/backend/app/maps/` to allow controlled benchmarking.

Notes:
- The project previously included a benchmark runner in the frontend for comparing single-host algorithm speeds; it was removed and replaced with a bars-only visualization to simplify CI and UX.
- For real performance testing, prefer running backend planners locally (Python venv) and measuring with tooling (time, cProfile) because serverless environments add variability.

---

## Included Files & Locations (high-level)
- Frontend
  - `webapp/frontend/package.json` — dependencies & scripts (`start`, `build` via `craco`).
  - `webapp/frontend/craco.config.js` — webpack tweaks (source-map-loader exclusion for `@mui/x-charts`).
  - `webapp/frontend/src/App.js` — main SPA routing and API wiring.
  - `webapp/frontend/src/components/BenchmarkPage.js` — chart UI (bars-only).
  - `webapp/frontend/src/components/*.js` — other UI components (GridVisualization, InputForm, GridConfigPage, GridMapPage).
- Backend
  - `webapp/backend/main.py` — FastAPI app entrypoint and CORS middleware.
  - `webapp/backend/app/routers/pathfinder.py` — core API endpoints and logic glue.
  - `webapp/backend/algorithms/` — implementation of algorithms used by the planner.
  - `webapp/backend/app/maps/` and `webapp/backend/maps/` — included map files used for examples and testing.

---

## Deployment
- Frontend deployed to Vercel; production alias configured (example): `https://mapf-ai.vercel.app` → points to the frontend deployment.
- Backend deployed to Vercel as a Python app with `vercel.json` routing to `main.py`.
- Important production notes:
  - Ensure backend CORS allows the production frontend origin.
  - Frontend should set `REACT_APP_API_URL` environment variable in Vercel project settings to point to the backend alias if you want to change backends without code edits.

---


## How to Run Locally (quick)
1. Frontend

```bash
cd webapp/frontend
npm install
npm run start       # dev server at http://localhost:3000
npm run build       # production bundle
```

2. Backend

```bash
cd webapp/backend
python -m venv .venv
. .venv/Scripts/activate   # Windows PowerShell: . .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Open `http://localhost:3000` and the frontend will call `http://localhost:8000` by default.

