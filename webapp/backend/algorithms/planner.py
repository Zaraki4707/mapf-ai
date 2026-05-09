from typing import List, Tuple, Dict, Optional

from .grid import GridEnvironment
from .robot import Robot
from .independent_astar import IndependentAStarPlanner
from .prioritized_astar import PrioritizedPlanner
from .conflict_detector import ConflictDetector


class PathPlanner:
    """High-level planner combining algorithms for multi-agent pathfinding."""

    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self.planner = IndependentAStarPlanner(grid)
        self.prioritized_planner = PrioritizedPlanner(grid)
        self.detector = ConflictDetector()

    def plan_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]], algorithm: str = 'independent_astar') -> Dict:
        """
        Simple mode: Start → Destination
        """
        if algorithm == 'cooperative_astar':
            return self.plan_prioritized_simple(starts, destinations)

        if len(starts) != len(destinations):
            return {
                'success': False,
                'message': 'Number of starts must match number of destinations'
            }

        robots = []
        for i, (start, dest) in enumerate(zip(starts, destinations)):
            robot = Robot(i, self.grid, start, dest)
            robots.append(robot)

        paths = self.planner.plan_all_robots(robots)
        valid_paths = {k: v for k, v in paths.items() if v is not None}

        if not valid_paths:
            return {
                'success': False,
                'message': 'No valid paths found'
            }

        total_cost = sum(len(p) - 1 for p in valid_paths.values())
        paths_list = [valid_paths[i] for i in sorted(valid_paths.keys())]

        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(robots),
            'total_cost': total_cost,
            'paths': paths_list
        }

    def plan_full(self, starts: List[Tuple[int, int]], picks: List[Tuple[int, int]],
                  drops: List[Tuple[int, int]], destinations: List[Tuple[int, int]], algorithm: str = 'independent_astar') -> Dict:
        """
        Full mode: Start → Pick → Drop → Destination
        """
        if algorithm == 'cooperative_astar':
            return self.plan_prioritized_full(starts, picks, drops, destinations)

        if not (len(starts) == len(picks) == len(drops) == len(destinations)):
            return {
                'success': False,
                'message': 'Number of starts, picks, drops, and destinations must match'
            }

        all_robots = []
        for i in range(len(starts)):
            start = starts[i]
            pick = picks[i]
            drop = drops[i]
            dest = destinations[i]

            segment_robots = [
                Robot(i * 4 + 0, self.grid, start, pick),
                Robot(i * 4 + 1, self.grid, pick, drop),
                Robot(i * 4 + 2, self.grid, drop, dest)
            ]
            all_robots.extend(segment_robots)

        all_paths = self.planner.plan_all_robots(all_robots)

        final_paths = []
        for i in range(len(starts)):
            path_segments = []
            for seg_idx in range(3):
                robot_id = i * 4 + seg_idx
                segment_path = all_paths.get(robot_id)
                if not segment_path:
                    return {
                        'success': False,
                        'message': f'No path found for agent {i} segment {seg_idx}'
                    }
                path_segments.append(segment_path)

            full_path = self._concatenate_segments(path_segments)
            final_paths.append(full_path)

        total_cost = sum(len(p) - 1 for p in final_paths)

        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': final_paths
        }

    def plan_prioritized_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for prioritized simple mode."""
        tasks = [[s, d] for s, d in zip(starts, destinations)]
        paths = self.prioritized_planner.plan(tasks)
        
        if len(paths) < len(starts):
             return {'success': False, 'message': 'Failed to find collision-free paths for all agents'}
             
        total_cost = sum(len(p) - 1 for p in paths)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': paths
        }

    def plan_prioritized_full(self, starts: List[Tuple[int, int]], picks: List[Tuple[int, int]],
                              drops: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for prioritized full mode."""
        tasks = [[s, p, d, dest] for s, p, d, dest in zip(starts, picks, drops, destinations)]
        paths = self.prioritized_planner.plan(tasks)
        
        if len(paths) < len(starts):
             return {'success': False, 'message': 'Failed to find collision-free paths for all agents'}
             
        total_cost = sum(len(p) - 1 for p in paths)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': paths
        }

    def _concatenate_segments(self, segments: List[List[Tuple[int, int]]]) -> List[Tuple[int, int]]:
        """Concatenate path segments with wait actions at pickup/drop locations."""
        if not segments:
            return []

        full_path = list(segments[0])

        for segment in segments[1:]:
            if not segment:
                continue

            last_pos = full_path[-1]
            first_pos = segment[0]

            if last_pos != first_pos:
                full_path.append(first_pos)

            full_path.extend(segment[1:])

        return full_path