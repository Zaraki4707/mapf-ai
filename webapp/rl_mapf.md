# RL Approach for Multi-Agent Path Finding - Implementation Plan

## Overview
Replace/augment the current A* algorithm with a Reinforcement Learning approach that learns optimal pathfinding policies through experience.

## Architecture

### 1. Problem Formulation
- **State Space**: Grid state + agent positions + velocities
- **Action Space**: Up/Down/Left/Right/Wait per agent
- **Reward**: -1 per step (encourages shortest path), large negative for collisions
- **Goal**: Reach destination with minimum steps, no collisions

### 2. RL Algorithm Options

| Algorithm | Pros | Cons |
|-----------|------|------|
| **Q-Learning** | Simple, works for small grids | struggles with continuous states |
| **Deep Q-Network (DQN)** | Handles larger state spaces | needs lots of training data |
| **Multi-Agent Proximal Policy Optimization (MAPPO)** | State-of-the-art for MARL | complex to implement |
| **Value Decomposition Networks (VDN)** | Good for cooperative MARL | assumes additive value |

### 3. Recommended: Q-Learning with Function Approximation

## Implementation Steps

### Phase 1: Environment Setup
```
backend/rl/
├── envs/
│   ├── multi_agent_env.py    # Gym-compatible environment
│   ├── grid_world.py         # Grid rendering
│   └── rewards.py            # Reward shaping
├── models/
│   ├── q_network.py          # Neural network for Q-values
│   └── policy.py             # Action selection policy
└── train/
    ├── replay_buffer.py      # Experience replay
    └── trainer.py            # Training loop
```

### Phase 2: Environment Spec (envs/multi_agent_env.py)
```python
class MultiAgentPathfindingEnv(gym.Env):
    def __init__(self, grid_height, grid_width, num_agents):
        self.observation_space = Box(low=0, high=1, shape=[grid_height, grid_width, num_agents])
        self.action_space = MultiDiscrete([5] * num_agents)  # 4 directions + wait

    def step(self, actions):
        # Execute actions, detect collisions, return reward
        # Reward: -1 per step, +100 for reaching goal, -1000 for collision

    def reset(self):
        # Spawn agents at random positions
```

### Phase 3: Model Architecture (models/q_network.py)
```python
class QNetwork(nn.Module):
    def __init__(self, grid_size, num_agents, num_actions):
        # CNN for grid input
        # FC layers for Q-values per agent
```

### Phase 4: Training Loop (train/trainer.py)
```python
def train(env, num_episodes=10000):
    q_net = QNetwork(grid_size, num_agents, num_actions)
    replay_buffer = ReplayBuffer(100000)

    for episode in range(num_episodes):
        state = env.reset()
        done = False
        while not done:
            actions = select_epsilon_greedy(q_net, state, epsilon)
            next_state, rewards, done = env.step(actions)
            replay_buffer.push(state, actions, rewards, next_state)

            if len(replay_buffer) > batch_size:
                train_step(q_net, replay_buffer.sample())
```

### Phase 5: API Integration
```python
@router.post("/find-path-rl")
async def find_path_rl(request: PathfinderRequest):
    # Load trained model
    # Run inference (no exploration)
    # Return paths
```

## Key Challenges

| Challenge | Solution |
|-----------|----------|
| **Multi-agent coordination** | Centralized training, decentralized execution |
| **Partial observability** | Include all agent positions in state |
| **Credit assignment** | Use difference rewards (team reward - individual) |
| **Collision avoidance** | Negative reward for vertex/edge conflicts |
| **Scalability** | Start with 2-3 agents, use attention for more |

## Files to Create

```
backend/rl/
├── requirements.txt          # torch, gymnasium, stable-baselines3
├── envs/
│   ├── __init__.py
│   ├── multi_agent_env.py   # ~200 lines
│   └── reward_shaping.py    # ~100 lines
├── models/
│   ├── __init__.py
│   └── q_network.py         # ~150 lines
├── train/
│   ├── __init__.py
│   ├── replay_buffer.py     # ~80 lines
│   └── trainer.py           # ~200 lines
├── agents/
│   └── rl_agent.py         # Wrapper for API
└── train.py                 # Entry point
```

## Pre-trained Models
- Start with small grids (6x6, 8x8)
- Export trained model as `.pt` file
- Load in API for inference (no training at runtime)

## Performance Comparison

| Metric | A* | RL |
|--------|-----|-----|
| Training time | 0 (instant) | ~1-2 hours |
| Inference | ~100ms | ~10ms |
| Generalization | fails on new layouts | adapts to new grids |
| Optimality | guaranteed optimal | near-optimal |

## Detailed Implementation

### Environment: multi_agent_env.py

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class MultiAgentGridEnv(gym.Env):
    metadata = {'render_modes': ['human']}

    def __init__(self, grid_height=8, grid_width=8, num_agents=2,
                 max_steps=200, render_mode=None):
        super().__init__()

        self.grid_height = grid_height
        self.grid_width = grid_width
        self.num_agents = num_agents
        self.max_steps = max_steps

        # Actions: 0=up, 1=down, 2=left, 3=right, 4=wait
        self.action_space = spaces.Discrete(5)

        # Observation: grid with agent positions encoded
        self.observation_space = spaces.Box(
            low=0, high=1,
            shape=(grid_height, grid_width, 3),  # obstacles, agents, goals
            dtype=np.float32
        )

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Initialize positions...
        return observation, info

    def step(self, actions):
        # Move agents, detect collisions, compute rewards
        # Return: obs, reward, terminated, truncated, info
```

### Q-Network: q_network.py

```python
import torch
import torch.nn as nn

class QNetwork(nn.Module):
    def __init__(self, state_shape, num_actions, hidden_dim=128):
        super().__init__()
        # CNN backbone for grid processing
        self.conv = nn.Sequential(
            nn.Conv2d(state_shape[-1], 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.Flatten()
        )
        # Q-value head
        self.fc = nn.Sequential(
            nn.Linear(64 * state_shape[0] * state_shape[1], hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_actions)
        )

    def forward(self, x):
        x = x.permute(0, 3, 1, 2)  # (batch, h, w, c) -> (batch, c, h, w)
        x = self.conv(x)
        return self.fc(x)
```

### Training: trainer.py

```python
def train(env, agent, num_episodes=5000):
    for episode in range(num_episodes):
        obs, _ = env.reset()
        done = False

        while not done:
            action = agent.select_action(obs, epsilon=epsilon_schedule(episode))
            next_obs, reward, terminated, truncated, info = env.step(action)
            agent.store_transition(obs, action, reward, next_obs, done)

            if len(agent.replay_buffer) > batch_size:
                agent.train()

            obs = next_obs
            done = terminated or truncated
```

## Reward Shaping Strategy

| Event | Reward |
|-------|--------|
| Each timestep | -1 |
| Agent reaches goal | +100 |
| Agent reaches wrong cell | -10 |
| Vertex collision | -50 |
| Edge collision | -30 |
| All agents at goals | +200 (episode bonus) |

## Inference in Production

```python
@router.post("/find-path-rl")
async def find_path_rl(request: PathfinderRequest):
    # Load trained checkpoint
    agent = load_checkpoint("models/rl_agent.pt")

    # Create environment with request.grid specs
    env = MultiAgentGridEnv(
        grid_height=request.grid_height,
        grid_width=request.grid_width,
        num_agents=len(request.start)
    )

    # Run greedy (no exploration)
    obs = env.reset()
    paths = []

    for _ in range(env.max_steps):
        actions = agent.select_action(obs, epsilon=0)  # Greedy
        obs, _, done, _ = env.step(actions)
        paths.append(env.get_positions())

        if done:
            break

    return {"paths": paths, "success": True}
```

---

**Note**: This plan requires PyTorch, Gymnasium, and significant training time to achieve good results. Start with baseline A* for production, use RL for research/learning purposes.