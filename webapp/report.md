# MAPF Web Application Report

## Overview
This application is a Multi-Agent Path Finding (MAPF) visualizer and solver. it allows users to configure grid environments, define agent tasks (Start → Pickup → Dropoff → Destination), and visualize the computed collision-free paths using various AI search algorithms.

## Backend Architecture
The backend is built with **FastAPI** and hosted on Vercel.

### 1. Algorithms
- **Independent A***: Each agent finds its shortest path without considering others.
- **Conflict-Based Search (CBS)**: A high-level search that resolves collisions by adding constraints to individual agents.
- **Grid Environment**: Handles obstacle representation (using 'T' for trees/obstacles) and coordinate conversions.

### 2. API Endpoints
- `GET /maps`: Returns a list of predefined map templates (e.g., maze, warehouse).
- `GET /maps/{id}`: Provides specific dimensions and obstacle coordinates for a chosen map.
- `POST /find-path`: The core engine that takes agent positions and obstacles, runs the selected algorithm, and returns localized paths.

### 3. Data Processing
- **Coordinate System**: The backend internally uses `(x, y)` which corresponds to `(column, row)`, but interfaces with the frontend using `[row, col]` for standard grid alignment.

---

## Frontend Architecture
The frontend is a **React** application designed with an industrial "Mission Control" aesthetic.

### 1. Key Components
- **InputForm**: Handles user configuration, including manual coordinate entry for agents and obstacles or template selection.
- **GridVisualization**: 
    - Renders a dynamic grid using CSS Grid.
    - **Obstacle Representation**: Obstacles are displayed as small red squares (`.obstacle-box`) inside dark industrial cells.
    - **Animation**: Users can "Execute" the mission to see agents move through time steps.
    - **Telemetry**: Real-time X/Y coordinate readout for every agent during playback.
- **BenchmarkPage**: Dedicated space for comparing performance metrics across different search algorithms.

### 2. State Management
- Uses React hooks (`useState`, `useEffect`) to manage the playback timeline and asynchronous API calls.
- Memoizes obstacle sets for $O(1)$ lookup performance during grid rendering.

### 3. Styling
- **Theme**: Dark mode industrial UI using CSS variables for consistent colors (crimson, safety yellow, cyan).
- **Responsive Grid**: Dynamically adjusts based on the `grid_width` and `grid_height` returned by the backend.

## Recent Updates
- **Improved Visibility**: Replaced text-based "X" obstacles with distinct red box markers.
- **Production Sync**: Fully deployed to Vercel with integrated backend-frontend communication.
