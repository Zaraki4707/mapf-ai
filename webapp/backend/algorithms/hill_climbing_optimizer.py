import heapq
import time
import copy
import random
from collections import defaultdict, deque
from typing import List, Dict, Tuple, Optional, Set
from .conflict_detector import ConflictDetector


class HillClimbingOptimizer:
    """
    Hill Climbing optimizer for MAPF path improvement from Main.ipynb.
    
    Strategies:
    1. Path Shortening: remove internal loops and redundant segments
    2. Idle Reduction: compress consecutive waiting actions
    3. Local Swap Optimization: replace a local corner with a shorter detour
    4. Adaptive Local Search: random shortcut attempts on the longest path
    """

    def __init__(self, conflict_detector=None):
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.iteration_count = 0

    def optimize(
        self,
        paths: Dict,
        grid,
        max_iterations: int = 1000,
        timeout: float = 30
    ) -> Dict:
        """
        Optimize MAPF paths using a safe hill-climbing procedure.
        """
        start_time = time.time()
        original_paths = copy.deepcopy(paths)

        best_paths = copy.deepcopy(paths)
        best_score = self._solution_score(best_paths, grid, original_paths)

        improved = True
        iteration = 0

        while improved and iteration < max_iterations:
            if time.time() - start_time > timeout:
                break

            improved = False
            iteration += 1

            new_paths = self._optimize_path_shortening(best_paths, grid)
            if self._is_better(new_paths, best_score, best_paths, grid, original_paths):
                best_paths = new_paths
                best_score = self._solution_score(best_paths, grid, original_paths)
                improved = True
                continue

            new_paths = self._optimize_idle_reduction(best_paths)
            if self._is_better(new_paths, best_score, best_paths, grid, original_paths):
                best_paths = new_paths
                best_score = self._solution_score(best_paths, grid, original_paths)
                improved = True
                continue

            new_paths = self._optimize_path_swaps(best_paths, grid)
            if self._is_better(new_paths, best_score, best_paths, grid, original_paths):
                best_paths = new_paths
                best_score = self._solution_score(best_paths, grid, original_paths)
                improved = True
                continue

            new_paths = self._optimize_adaptive_local_search(best_paths, grid)
            if self._is_better(new_paths, best_score, best_paths, grid, original_paths):
                best_paths = new_paths
                best_score = self._solution_score(best_paths, grid, original_paths)
                improved = True
                continue

        self.iteration_count = iteration
        return best_paths

    def _optimize_path_shortening(self, paths: Dict, grid) -> Dict:
        """Remove internal loops from paths."""
        optimized = copy.deepcopy(paths)

        for rid, path in optimized.items():
            if not path or len(path) <= 2:
                continue

            candidate = self._remove_internal_loops(path)

            if candidate != path:
                test_paths = copy.deepcopy(optimized)
                test_paths[rid] = candidate
                conflicts = self.conflict_detector.detect_conflicts(test_paths)
                if conflicts:
                    continue
                if self._is_structurally_valid_solution(test_paths, grid, paths):
                    optimized = test_paths

        return optimized

    def _optimize_idle_reduction(self, paths: Dict) -> Dict:
        """Reduce idle time by compressing consecutive waiting actions."""
        optimized = copy.deepcopy(paths)

        for rid, path in optimized.items():
            if not path or len(path) <= 1:
                continue

            candidate = [path[0]]
            for pos in path[1:]:
                if pos != candidate[-1]:
                    candidate.append(pos)

            if candidate != path:
                test_paths = copy.deepcopy(optimized)
                test_paths[rid] = candidate
                conflicts = self.conflict_detector.detect_conflicts(test_paths)
                if conflicts:
                    continue
                if self._is_structurally_valid_solution(test_paths, None, paths):
                    optimized = test_paths

        return optimized

    def _optimize_path_swaps(self, paths: Dict, grid) -> Dict:
        """Try local corner swaps by replacing one waypoint with a shorter detour."""
        optimized = copy.deepcopy(paths)
        robot_ids = list(optimized.keys())

        for rid in robot_ids:
            path = optimized.get(rid)
            if not path or len(path) < 3:
                continue

            for idx in range(1, len(path) - 1):
                prev_pos = path[idx - 1]
                next_pos = path[idx + 1]

                alt_path = self._find_detour(prev_pos, next_pos, grid, max_steps=4)
                if not alt_path:
                    continue

                if len(alt_path) >= 3:
                    continue

                candidate = path[:idx] + alt_path[1:-1] + path[idx + 1:]

                if candidate != path:
                    test_paths = copy.deepcopy(optimized)
                    test_paths[rid] = candidate
                    conflicts = self.conflict_detector.detect_conflicts(test_paths)
                    if conflicts:
                        continue
                    if self._is_structurally_valid_solution(test_paths, grid, paths):
                        optimized = test_paths
                        break

        return optimized

    def _optimize_adaptive_local_search(self, paths: Dict, grid) -> Dict:
        """Adaptive local search: randomly try to shortcut a segment of the longest path."""
        optimized = copy.deepcopy(paths)

        valid_robot_ids = [
            rid for rid, p in optimized.items()
            if p is not None and len(p) >= 3
        ]
        if not valid_robot_ids:
            return optimized

        longest_rid = max(valid_robot_ids, key=lambda r: len(optimized[r]))
        path = optimized[longest_rid]

        attempts = min(8, len(path) - 2)

        for _ in range(attempts):
            i = random.randint(0, len(path) - 3)
            j = random.randint(i + 2, min(len(path) - 1, i + 8))

            start = path[i]
            end = path[j]

            alt_path = self._find_detour(start, end, grid, max_steps=(j - i + 2))
            if not alt_path:
                continue

            if len(alt_path) >= (j - i + 1):
                continue

            candidate_path = path[:i] + alt_path + path[j + 1:]

            test_paths = copy.deepcopy(optimized)
            test_paths[longest_rid] = candidate_path

            conflicts = self.conflict_detector.detect_conflicts(test_paths)
            if conflicts:
                continue

            if self._is_structurally_valid_solution(test_paths, grid, paths):
                optimized = test_paths
                break

        return optimized

    def _remove_internal_loops(self, path: List[Tuple]) -> List[Tuple]:
        """Remove cycles and repeated sections from a path."""
        if len(path) <= 2:
            return path

        changed = True
        new_path = path[:]

        while changed:
            changed = False
            for i in range(len(new_path)):
                for j in range(i + 2, len(new_path)):
                    if new_path[i] == new_path[j]:
                        candidate = new_path[:i + 1] + new_path[j + 1:]
                        if len(candidate) < len(new_path):
                            new_path = candidate
                            changed = True
                            break
                if changed:
                    break

        return new_path

    def _find_detour(
        self,
        start: Tuple,
        end: Tuple,
        grid,
        max_steps: int = 5
    ) -> Optional[List[Tuple]]:
        """Find a shortest walkable path between two positions using BFS."""
        if start == end:
            return [start]

        queue = deque([(start, [start])])
        visited = {start}

        while queue:
            curr, path = queue.popleft()

            if len(path) > max_steps:
                continue

            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                nxt = (curr[0] + dx, curr[1] + dy)

                if nxt in visited:
                    continue
                if not self._is_walkable(nxt, grid):
                    continue

                new_path = path + [nxt]
                if nxt == end:
                    return new_path

                visited.add(nxt)
                queue.append((nxt, new_path))

        return None

    def _is_better(
        self,
        new_paths: Dict,
        old_score: Tuple[float, float],
        old_paths: Dict,
        grid,
        original_paths: Dict
    ) -> bool:
        """Check whether a candidate is better than the current solution."""
        new_score = self._solution_score(new_paths, grid, original_paths)
        return new_score < old_score

    def _solution_score(
        self,
        paths: Dict,
        grid,
        original_paths: Dict
    ) -> Tuple[float, float]:
        """Score a solution as (number_of_conflicts, makespan)."""
        if not self._is_structurally_valid_solution(paths, grid, original_paths):
            return (float("inf"), float("inf"))

        conflicts = self.conflict_detector.detect_conflicts(paths)
        conflict_count = len(conflicts)
        cost = self._calculate_cost(paths)
        return (conflict_count, cost)

    def _is_structurally_valid_solution(
        self,
        paths: Dict,
        grid,
        original_paths: Dict
    ) -> bool:
        """Check path structure and endpoint preservation."""
        if not isinstance(paths, dict) or not paths:
            return False

        if set(paths.keys()) != set(original_paths.keys()):
            return False

        for rid, path in paths.items():
            if path is None or len(path) == 0:
                return False

            original_path = original_paths[rid]
            if not original_path or len(original_path) == 0:
                return False

            if path[0] != original_path[0]:
                return False

            if path[-1] != original_path[-1]:
                return False

            if not self._is_single_path_valid(path, grid):
                return False

        return True

    def _is_single_path_valid(self, path: List[Tuple], grid) -> bool:
        """Check that one robot path is walkable and time-continuous."""
        for pos in path:
            if not self._is_walkable(pos, grid):
                return False

        for p1, p2 in zip(path, path[1:]):
            dx = abs(p1[0] - p2[0])
            dy = abs(p1[1] - p2[1])
            if dx + dy > 1:
                return False

        return True

    def _is_walkable(self, pos: Tuple, grid) -> bool:
        """Safe walkability check for the grid API."""
        if grid is None:
            return True

        if hasattr(grid, "is_walkable"):
            try:
                return bool(grid.is_walkable(pos[0], pos[1]))
            except TypeError:
                return bool(grid.is_walkable(pos))

        return True

    def _calculate_cost(self, paths: Dict) -> float:
        """Calculate makespan (maximum path length minus 1)."""
        if not paths:
            return float("inf")

        valid_paths = [p for p in paths.values() if p is not None and len(p) > 0]
        if not valid_paths:
            return float("inf")

        return max(len(p) for p in valid_paths) - 1