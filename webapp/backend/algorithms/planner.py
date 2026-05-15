from typing import List, Tuple, Dict, Optional

from .grid import GridEnvironment
from .robot import Robot
from .independent_astar import IndependentAStarPlanner
from .prioritized_astar import PrioritizedPlanner
from .conflict_detector import ConflictDetector
from .hill_climbing import HillClimbingSolver
from .cbs import ConflictBasedSearch
from .hill_climbing_optimizer import HillClimbingOptimizer


class PathPlanner:
    """High-level planner combining algorithms for multi-agent pathfinding."""

    def __init__(self, grid: GridEnvironment):
        self.grid = grid
        self.planner = IndependentAStarPlanner(grid)
        self.prioritized_planner = PrioritizedPlanner(grid)
        self.hc_solver = HillClimbingSolver(grid)
        self.detector = ConflictDetector()
        self.hc_optimizer = HillClimbingOptimizer(conflict_detector=self.detector)

    def plan_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]], algorithm: str = 'independent_astar') -> Dict:
        """
        Simple mode: Start → Destination
        """
        if algorithm == 'cooperative_astar':
            return self.plan_prioritized_simple(starts, destinations)
        
        if algorithm == 'hill_climbing':
            return self.plan_hc_simple(starts, destinations)

        if algorithm == 'cbs':
            return self.plan_cbs_simple(starts, destinations)

        if algorithm == 'optimized_hc':
            return self.plan_optimized_hc_simple(starts, destinations)

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
            
        if algorithm == 'hill_climbing':
            return self.plan_hc_full(starts, picks, drops, destinations)

        if algorithm == 'cbs':
            return self.plan_cbs_full(starts, picks, drops, destinations)

        if algorithm == 'optimized_hc':
            return self.plan_optimized_hc_full(starts, picks, drops, destinations)

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

    def plan_hc_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for Hill Climbing simple mode."""
        robots = []
        for i, (start, dest) in enumerate(zip(starts, destinations)):
            robots.append(Robot(i, self.grid, start, dest))
            
        paths_dict = self.hc_solver.solve(robots)
        paths_list = [paths_dict[i] for i in range(len(starts))]
        
        total_cost = sum(len(p) - 1 for p in paths_list if p)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': paths_list
        }

    def plan_hc_full(self, starts: List[Tuple[int, int]], picks: List[Tuple[int, int]],
                     drops: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for Hill Climbing full mode."""
        # For simplicity in HC which is centralized, we solve the whole sequence as one robot if possible,
        # but the current HC implementation handles single segments. 
        # To adapt to WebApp's Start -> Pick -> Drop -> Dest:
        all_final_paths = []
        
        # Segment 1: Start -> Pick
        robots1 = [Robot(i, self.grid, starts[i], picks[i]) for i in range(len(starts))]
        paths1 = self.hc_solver.solve(robots1)
        
        # Segment 2: Pick -> Drop
        # We need to consider time offsets for true consistency, but for this implementation
        # we'll solve segments sequentially or as an integrated task.
        # Given the hc_solver structure, we'll follow simple sequence:
        robots2 = [Robot(i, self.grid, picks[i], drops[i]) for i in range(len(starts))]
        paths2 = self.hc_solver.solve(robots2)
        
        # Segment 3: Drop -> Dest
        robots3 = [Robot(i, self.grid, drops[i], destinations[i]) for i in range(len(starts))]
        paths3 = self.hc_solver.solve(robots3)
        
        for i in range(len(starts)):
            full_path = self._concatenate_segments([paths1[i], paths2[i], paths3[i]])
            all_final_paths.append(full_path)
            
        total_cost = sum(len(p) - 1 for p in all_final_paths)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': all_final_paths
        }

    def plan_cbs_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for CBS simple mode."""
        robots = []
        for i, (start, dest) in enumerate(zip(starts, destinations)):
            robots.append(Robot(i, self.grid, start, dest))

        cbs = ConflictBasedSearch(self.grid, robots, conflict_detector=self.detector, objective="makespan")
        result = cbs.solve(time_limit=120)

        if result.get('success'):
            paths_list = [result['paths'][i] for i in range(len(starts))]
            total_cost = sum(len(p) - 1 for p in paths_list if p)
            return {
                'success': True,
                'grid_height': self.grid.height,
                'grid_width': self.grid.width,
                'num_agents': len(starts),
                'total_cost': total_cost,
                'paths': paths_list
            }
        else:
            return self.plan_prioritized_simple(starts, destinations)

    def plan_cbs_full(self, starts: List[Tuple[int, int]], picks: List[Tuple[int, int]],
                      drops: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for CBS full mode (Start -> Pick -> Drop -> Dest)."""
        all_final_paths = []

        robots1 = [Robot(i, self.grid, starts[i], picks[i]) for i in range(len(starts))]
        cbs1 = ConflictBasedSearch(self.grid, robots1, conflict_detector=self.detector)
        result1 = cbs1.solve(time_limit=120)
        if not result1.get('success'):
            return self.plan_prioritized_full(starts, picks, drops, destinations)
        paths1 = [result1['paths'][i] for i in range(len(starts))]

        robots2 = [Robot(i, self.grid, picks[i], drops[i]) for i in range(len(starts))]
        cbs2 = ConflictBasedSearch(self.grid, robots2, conflict_detector=self.detector)
        result2 = cbs2.solve(time_limit=120)
        if not result2.get('success'):
            return self.plan_prioritized_full(starts, picks, drops, destinations)
        paths2 = [result2['paths'][i] for i in range(len(starts))]

        robots3 = [Robot(i, self.grid, drops[i], destinations[i]) for i in range(len(starts))]
        cbs3 = ConflictBasedSearch(self.grid, robots3, conflict_detector=self.detector)
        result3 = cbs3.solve(time_limit=120)
        if not result3.get('success'):
            return self.plan_prioritized_full(starts, picks, drops, destinations)
        paths3 = [result3['paths'][i] for i in range(len(starts))]

        for i in range(len(starts)):
            full_path = self._concatenate_segments([paths1[i], paths2[i], paths3[i]])
            all_final_paths.append(full_path)

        total_cost = sum(len(p) - 1 for p in all_final_paths)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': all_final_paths
        }

    def plan_optimized_hc_simple(self, starts: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for optimized Hill Climbing (Main.ipynb version) simple mode."""
        robots = []
        for i, (start, dest) in enumerate(zip(starts, destinations)):
            robots.append(Robot(i, self.grid, start, dest))

        paths_dict = self.planner.plan_all_robots(robots)

        paths_for_opt = {i: paths_dict[i] for i in range(len(starts)) if paths_dict.get(i) is not None}
        optimized_paths = self.hc_optimizer.optimize(paths_for_opt, self.grid, max_iterations=1000, timeout=30)

        conflicts = self.detector.detect_conflicts(optimized_paths)
        if conflicts:
            return self.plan_prioritized_simple(starts, destinations)

        paths_list = [optimized_paths.get(i, paths_dict.get(i)) for i in range(len(starts))]

        total_cost = sum(len(p) - 1 for p in paths_list if p)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': paths_list
        }

    def plan_optimized_hc_full(self, starts: List[Tuple[int, int]], picks: List[Tuple[int, int]],
                               drops: List[Tuple[int, int]], destinations: List[Tuple[int, int]]) -> Dict:
        """Helper for optimized Hill Climbing (Main.ipynb version) full mode."""
        all_final_paths = []

        robots1 = [Robot(i, self.grid, starts[i], picks[i]) for i in range(len(starts))]
        paths1_dict = self.planner.plan_all_robots(robots1)
        paths1_for_opt = {i: paths1_dict.get(i) for i in range(len(starts)) if paths1_dict.get(i) is not None}
        opt1 = self.hc_optimizer.optimize(paths1_for_opt, self.grid, max_iterations=500, timeout=15)
        paths1 = [opt1.get(i, paths1_dict.get(i)) for i in range(len(starts))]

        robots2 = [Robot(i, self.grid, picks[i], drops[i]) for i in range(len(starts))]
        paths2_dict = self.planner.plan_all_robots(robots2)
        paths2_for_opt = {i: paths2_dict.get(i) for i in range(len(starts)) if paths2_dict.get(i) is not None}
        opt2 = self.hc_optimizer.optimize(paths2_for_opt, self.grid, max_iterations=500, timeout=15)
        paths2 = [opt2.get(i, paths2_dict.get(i)) for i in range(len(starts))]

        robots3 = [Robot(i, self.grid, drops[i], destinations[i]) for i in range(len(starts))]
        paths3_dict = self.planner.plan_all_robots(robots3)
        paths3_for_opt = {i: paths3_dict.get(i) for i in range(len(starts)) if paths3_dict.get(i) is not None}
        opt3 = self.hc_optimizer.optimize(paths3_for_opt, self.grid, max_iterations=500, timeout=15)
        paths3 = [opt3.get(i, paths3_dict.get(i)) for i in range(len(starts))]

        for i in range(len(starts)):
            full_path = self._concatenate_segments([paths1[i], paths2[i], paths3[i]])
            all_final_paths.append(full_path)

        total_cost = sum(len(p) - 1 for p in all_final_paths)
        return {
            'success': True,
            'grid_height': self.grid.height,
            'grid_width': self.grid.width,
            'num_agents': len(starts),
            'total_cost': total_cost,
            'paths': all_final_paths
        }