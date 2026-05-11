import heapq
from typing import List, Tuple, Dict, Set, Optional, Any

from .node import Node
from .grid import GridEnvironment
from .robot import Robot

class TimeExpandingAStarPlanner:
    """
    Space-Time A* planner. 
    Searches for paths in (x, y, t) space to avoid dynamic obstacles (other agents).
    """

    def __init__(self, grid: GridEnvironment):
        self.grid = grid

    def run_space_time_astar(self, 
                             start: Tuple[int, int], 
                             goal: Tuple[int, int], 
                             dynamic_obstacles: Dict[int, Set[Tuple[int, int]]],
                             max_time: int = 1000) -> Optional[List[Tuple[int, int]]]:
        """
        Runs A* in (x, y, t) space.
        dynamic_obstacles: Dict where key is time T, value is set of occupied (x, y) cells.
        """
        if not self.grid.is_walkable(*start) or not self.grid.is_walkable(*goal):
            return None

        # open_set: (f_score, time, current_pos, parent_pos, parent_time)
        # Using a simple tuple for heapq
        start_node = (self.grid.manhattan_distance(start, goal), 0, start, None, -1)
        open_set = [start_node]
        
        # g_score: (pos, time) -> cost
        g_score = {(start, 0): 0}
        came_from = {} # (pos, time) -> (parent_pos, parent_time)

        while open_set:
            f, t, current, p_pos, p_t = heapq.heappop(open_set)

            if current == goal:
                # Reconstruct path
                path = []
                curr_state = (current, t)
                while curr_state in came_from:
                    path.append(curr_state[0])
                    curr_state = came_from[curr_state]
                path.append(start)
                return path[::-1]

            if t >= max_time:
                continue

            # Possible moves: Neighbors + Wait
            next_t = t + 1
            moves = self.grid.get_neighbors(*current)
            moves.append(current) # Wait action

            for next_pos in moves:
                # 1. Vertex Collision: Check if cell is occupied at next_t
                if dynamic_obstacles and next_t in dynamic_obstacles:
                    if next_pos in dynamic_obstacles[next_t]:
                        continue
                
                # 2. Edge Collision: Check if two agents swap positions
                # (current -> next_pos) while someone else goes (next_pos -> current)
                # Since we plan one by one, we only need to check if someone was at next_pos at time t
                # AND is moving to current at time next_t.
                # In prioritized planning, we check against already planned paths.
                if current != next_pos and dynamic_obstacles:
                    # If Agent A was at next_pos at t AND Agent B is moving to next_pos at next_t...
                    # We need to ensures Agent A isn't moving into 'current' at next_t.
                    # This is usually handled by checking (next_pos, t) and (current, next_t) in the occupied set.
                    if t in dynamic_obstacles and next_pos in dynamic_obstacles[t] and \
                       next_t in dynamic_obstacles and current in dynamic_obstacles[next_t]:
                        # Someone is at next_pos now and moving to where I am.
                        continue

                tentative_g = g_score[(current, t)] + 1
                
                if (next_pos, next_t) not in g_score or tentative_g < g_score[(next_pos, next_t)]:
                    g_score[(next_pos, next_t)] = tentative_g
                    f_score = tentative_g + self.grid.manhattan_distance(next_pos, goal)
                    came_from[(next_pos, next_t)] = (current, t)
                    heapq.heappush(open_set, (f_score, next_t, next_pos, current, t))

        return None

class PrioritizedPlanner:
    """
    Prioritized Planning using Space-Time A*.
    Agents are planned one by one in order.
    """
    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self.st_astar = TimeExpandingAStarPlanner(grid)

    def plan(self, agents_tasks: List[List[Tuple[int, int]]]) -> List[List[Tuple[int, int]]]:
        """
        agents_tasks: List of (start, pickup, drop, destination) segments for each agent.
        """
        # Global occupied set: time -> set of (x, y)
        occupied: Dict[int, Set[Tuple[int, int]]] = {}
        final_paths = []

        for agent_id, tasks in enumerate(agents_tasks):
            agent_full_path = []
            curr_start = tasks[0]
            curr_time = 0

            for goal in tasks[1:]:
                if curr_start == goal:
                    continue
                
                segment = self.st_astar.run_space_time_astar(
                    curr_start, goal, occupied, max_time=curr_time + 500
                )
                
                if not segment:
                    # Fail gracefully or try waiting at start?
                    # For now, just return what we have
                    return final_paths

                # Record the path in the occupied set
                # Important: segment[0] is curr_start at curr_time
                for i, pos in enumerate(segment):
                    t = curr_time + i
                    if t not in occupied:
                        occupied[t] = set()
                    occupied[t].add(pos)
                
                # After reaching goal, the agent stays there forever (or until max time)
                # to prevent others from driving through parked robots.
                last_t = curr_time + len(segment) - 1
                for t in range(last_t + 1, last_t + 100):
                    if t not in occupied:
                        occupied[t] = set()
                    occupied[t].add(segment[-1])

                if agent_full_path:
                    agent_full_path.extend(segment[1:])
                else:
                    agent_full_path.extend(segment)
                
                curr_start = segment[-1]
                curr_time += len(segment) - 1
            
            final_paths.append(agent_full_path)
            
        return final_paths
