# Warehouse Multi-Robot Control System

## Project Overview

This project is about building a system that controls multiple warehouse robots moving inside a grid. Each robot starts at a position and needs to reach a goal (like picking up or delivering a shelf), and the main challenge is to make sure all robots move without colliding or blocking each other.

We model the warehouse as a grid where some cells are free and others are obstacles. Robots can move in four directions (up, down, left, right), and possibly wait in place when needed to avoid conflicts.

---

## Problem Definition

The core problem we are solving is a **Multi-Agent Pathfinding (MAPF)** problem. Given multiple robots with start and goal positions, we need to compute paths for all of them such that:

* No two robots **collide** (same cell at the same time)
* No **edge conflicts** (robots swapping positions at the same time)
* The overall movement is **efficient**

---

## Algorithms

We will implement and compare several algorithms:

* **Independent A\*** — each robot plans alone, fast but may conflict
* **Cooperative A\*** — adds time dimension to reduce conflicts
* **Conflict-Based Search (CBS)** — more optimal and structured conflict resolution
* **Hill Climbing** — to improve solutions

---

## Current Status

Right now, the grid system is already implemented. It loads maps from files, checks valid positions, and can visualize the environment.

### Next Steps

* Finish the **Robot class** (store position, goal, path, movement)
* Define the **Node class** for search algorithms
* Build the **main controller** that manages all robots
* Start implementing pathfinding algorithms (starting with **A\***)

### Later

* Add **collision detection** between robots
* Handle **deadlocks**
* Visualize **robot movements** step-by-step
* Measure performance (**makespan** and **flowtime**)
* Possibly generate **heatmaps** to see congestion areas

---

## Dataset

For now, we are using standard grid datasets (small, medium, large), but we may replace them with real warehouse-like data later.

---

## Goal

The goal is to end up with a complete simulation where multiple robots move efficiently in the warehouse without conflicts.
