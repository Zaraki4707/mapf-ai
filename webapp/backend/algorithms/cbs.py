import heapq
import copy
import time
from typing import List, Dict, Tuple, Optional, Any, Set
from collections import defaultdict


MAX_NODE_EXPANSIONS = 50000

class Constraint:
    """CBS constraint for vertex or edge constraints."""
    def __init__(self, agent_id: int, pos1: Tuple, pos2: Optional[Tuple] = None, time: int = None):
        self.agent_id = agent_id
        self.pos1 = pos1
        self.pos2 = pos2
        self.time = time
        self.is_edge = pos2 is not None

    def __repr__(self):
        if self.is_edge:
            return f"Edge({self.agent_id}: {self.pos1}->{self.pos2}@t={self.time})"
        return f"Vertex({self.agent_id}: {self.pos1}@t={self.time})"


class _RobotProxy:
    def __init__(self, start_position, goal_position):
        self.start_pos = start_position
        self.goal_pos = goal_position


class ConflictTreeNode:
    """Node in the Conflict Tree for CBS."""
    def __init__(
        self,
        constraints: Optional[Dict[int, List[Constraint]]] = None,
        paths: Optional[Dict[int, List]] = None,
        conflicts: Optional[List[Dict]] = None,
    ):
        self.constraints = constraints if constraints is not None else defaultdict(list)
        self.paths = paths if paths is not None else {}
        self.conflicts = conflicts if conflicts is not None else []
        self.makespan = self._calculate_makespan()
        self.flowtime = self._calculate_flowtime()

    def _calculate_makespan(self) -> float:
        if not self.paths:
            return float("inf")
        valid_paths = [p for p in self.paths.values() if p is not None and len(p) > 0]
        if not valid_paths:
            return float("inf")
        return max(len(p) for p in valid_paths) - 1

    def _calculate_flowtime(self) -> float:
        if not self.paths:
            return float("inf")
        valid_paths = [p for p in self.paths.values() if p is not None and len(p) > 0]
        if not valid_paths:
            return float("inf")
        return sum(len(p) - 1 for p in valid_paths)


class ConflictBasedSearch:
    """CBS for Multi-Agent Path Finding."""

    def __init__(
        self,
        grid,
        robots: List,
        conflict_detector=None,
        objective: str = "flowtime",
        max_iterations: int = 10000,
        timeout: int = 60,
    ):
        self.grid = grid
        self.robots = robots
        from .conflict_detector import ConflictDetector
        self.conflict_detector = conflict_detector if conflict_detector is not None else ConflictDetector()
        self.objective = objective.lower()
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.open_list = []
        self.closed_list = []
        self.visited_nodes = set()
        self.high_level_iterations = 0
        self.low_level_calls = 0

        # NEW: Track best solution found during search
        self._best_solution = None
        self._best_conflicts = float('inf')
        self._best_makespan = float('inf')
        self._lower_bound_cache = None

    def _compute_lower_bound_makespan(self) -> float:
        """
        Compute theoretical lower bound on makespan.
        This is the maximum individual path length (ignoring conflicts).
        Any solution must have at least this makespan.
        """
        if self._lower_bound_cache is None:
            self._lower_bound_cache = max(
                self.grid.get_manhattan_distance(r.start_pos, r.goal_pos) 
                for r in self.robots
            )
        return self._lower_bound_cache

    def solve(self, time_limit: Optional[float] = None) -> Dict[str, Any]:
        """
        Solve MAPF using CBS with early termination.
        Returns best solution found within time limit.
        """
        if time_limit is None:
            time_limit = self.timeout
        start_time = time.time()

        initial_paths = self._get_initial_solution()
        if not initial_paths or any(p is None for p in initial_paths.values()):
            return self._failure_result(initial_paths)

        root_conflicts = self.conflict_detector.detect_conflicts(initial_paths)
        root = ConflictTreeNode(
            constraints=defaultdict(list),
            paths=initial_paths,
            conflicts=root_conflicts,
        )

        self.open_list = []
        self.closed_list = []
        self.visited_nodes = set()
        self.high_level_iterations = 0
        
        # Initialize best solution tracking - NEW
        self._best_solution = initial_paths
        self._best_conflicts = len(root_conflicts)
        self._best_makespan = root.makespan
        lower_bound = self._compute_lower_bound_makespan()

        # Profiling variables
        total_time_expanding = 0.0
        total_time_detecting = 0.0

        heapq.heappush(self.open_list, (self._priority(root), id(root), root))
        print(f"[CBS] Start search. Initial conflicts: {self._best_conflicts}, Lower bound: {lower_bound}")

        while self.open_list and self.high_level_iterations < self.max_iterations:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > time_limit:
                print(f"[CBS] Timeout reached ({time_limit}s). High-level iterations: {self.high_level_iterations}. Best conflicts: {self._best_conflicts}")
                
                from .prioritized_astar import PrioritizedPlanner
                print(f"[CBS] Timeout Fallback to Prioritized Planner...")
                fallback_planner = PrioritizedPlanner(self.grid)
                agent_tasks = [[r.start_pos, r.goal_pos] for r in self.robots]
                fallback_res = fallback_planner.plan(agent_tasks)
                
                if fallback_res is not None and all(fallback_res):
                    paths = {i: path for i, path in enumerate(fallback_res)}
                    result = self._success_result(paths)
                    result['profiling'] = {'expand': total_time_expanding, 'detect': total_time_detecting, 'total': elapsed}
                    result['note'] = 'Resolved via Fallback Prioritized Planner due to CBS timeout.'
                    return result

                # Return best solution found so far
                if self._best_conflicts < float('inf'):
                    result = self._success_result(self._best_solution)
                    result['success'] = (self._best_conflicts == 0)
                    result['final_conflicts'] = self._best_conflicts
                    result['timeout'] = True
                    result['profiling'] = {'expand': total_time_expanding, 'detect': total_time_detecting, 'total': elapsed}
                    return result
                break

            self.high_level_iterations += 1
            if self.high_level_iterations % 100 == 0:
                print(f"[CBS] Iteration {self.high_level_iterations}. Min queue priority: {self.open_list[0][0]}. Time elapsed: {elapsed:.2f}s")
            _, _, node = heapq.heappop(self.open_list)
            self.closed_list.append(node)
            self.visited_nodes.add(id(node))
            
            # Track best solution - NEW
            node_conflict_count = len(node.conflicts)
            if node_conflict_count < self._best_conflicts:
                self._best_conflicts = node_conflict_count
                self._best_solution = node.paths
                self._best_makespan = node.makespan
                print(f"[CBS] New best solution found at iter {self.high_level_iterations} with {self._best_conflicts} conflicts. Make span: {node.makespan}")
            
            # Found conflict-free solution
            if not node.conflicts:
                print(f"[CBS] Optimal solution found in {elapsed:.2f}s. Iterations: {self.high_level_iterations}. Low-level calls: {self.low_level_calls}")
                result = self._success_result(node.paths)
                result['profiling'] = {'expand': total_time_expanding, 'detect': total_time_detecting, 'total': elapsed}
                return result
            
            # Prune nodes with makespan too far from lower bound - NEW
            if node.makespan > 2.5 * lower_bound:
                continue

            conflict = self._select_conflict(node.conflicts)
            if conflict is None:
                continue

            t_exp_start = time.time()
            children = self._expand_node(node, conflict)
            total_time_expanding += (time.time() - t_exp_start)

            for child in children:
                if child is None:
                    continue
                if id(child) not in self.visited_nodes:
                    heapq.heappush(self.open_list, (self._priority(child), id(child), child))

        print(f"[CBS] Max iterations reached or open list empty. Open list size: {len(self.open_list)}. Iterations: {self.high_level_iterations}")
        
        # CBS failed to find an optimal solution due to timeout or tree exhaustion.
        # Fallback to Prioritized Planning to guarantee a successful conflict-free sub-optimal result.
        from .prioritized_astar import PrioritizedPlanner
        print(f"[CBS] Falling back to Prioritized Planner to resolve stubborn symmetries...")
        fallback_planner = PrioritizedPlanner(self.grid)
        agent_tasks = [[r.start_pos, r.goal_pos] for r in self.robots]
        fallback_res = fallback_planner.plan(agent_tasks)
        
        if fallback_res is not None and all(fallback_res):
            paths = {i: path for i, path in enumerate(fallback_res)}
            result = self._success_result(paths)
            result['profiling'] = {'expand': total_time_expanding, 'detect': total_time_detecting, 'total': time.time() - start_time}
            result['note'] = 'Resolved via Fallback Prioritized Planner due to CBS symmetry explosion.'
            return result

        # Return best sub-optimal CBS solution if even prioritized fails
        if self._best_solution and self._best_conflicts < float('inf'):
            result = self._success_result(self._best_solution)
            result['success'] = (self._best_conflicts == 0)
            result['final_conflicts'] = self._best_conflicts
            result['partial_solution'] = True
            return result
        
        return self._failure_result(None)

    def _get_initial_solution(self) -> Dict[int, List]:
        paths = {}
        for robot in self.robots:
            robot_proxy = _RobotProxy(robot.start_pos, robot.goal_pos)
            path = self._astar_single_robot(robot_proxy, {})
            paths[robot.robot_id] = path
            self.low_level_calls += 1
        return paths

    def _astar_single_robot(self, robot_proxy, reservation_table: dict, start_time: int = 0, max_time: int = 1500):
        sx, sy = robot_proxy.start_pos
        gx, gy = robot_proxy.goal_pos
        h0 = self.grid.get_manhattan_distance((sx, sy), (gx, gy))
        open_heap = [(h0, 0, sx, sy, start_time)]
        came_from = {(sx, sy, start_time): None}
        g_score = {(sx, sy, start_time): 0}
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (0, 0)]

        expansions = 0
        while open_heap and expansions < MAX_NODE_EXPANSIONS:
            expansions += 1
            f, g, x, y, t = heapq.heappop(open_heap)
            if (x, y) == (gx, gy):
                return self._reconstruct_path(came_from, (x, y, t))
            if t >= max_time:
                continue
            if g > g_score.get((x, y, t), float('inf')):
                continue

            nt = t + 1
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if not self.grid.is_walkable(nx, ny):
                    continue
                if self._check_vertex_conflict((nx, ny), nt, reservation_table):
                    continue
                if (dx, dy) != (0, 0) and self._check_edge_conflict((x, y), (nx, ny), nt, reservation_table):
                    continue

                new_g = g + 1
                new_state = (nx, ny, nt)
                if new_g < g_score.get(new_state, float('inf')):
                    g_score[new_state] = new_g
                    came_from[new_state] = (x, y, t)
                    h = self.grid.get_manhattan_distance((nx, ny), (gx, gy))
                    heapq.heappush(open_heap, (new_g + h, new_g, nx, ny, nt))
        return None

    def _reconstruct_path(self, came_from: dict, goal_state: tuple) -> list:
        path = []
        current = goal_state
        while current is not None:
            path.append((current[0], current[1]))
            current = came_from[current]
        return list(reversed(path))

    def _check_vertex_conflict(self, pos: tuple, t: int, reservation_table: dict) -> bool:
        """Check if position at time t is constrained (dict version)"""
        return (pos[0], pos[1], t) in reservation_table

    def _check_edge_conflict(self, pos_from: tuple, pos_to: tuple, t: int, reservation_table: dict) -> bool:
        """Check if edge movement is constrained (dict version)"""
        edge_key = (pos_from[0], pos_from[1], pos_to[0], pos_to[1], t)
        if edge_key in reservation_table:
            return True
        
        # Check reverse edge (swap conflict)
        reverse_edge = (pos_to[0], pos_to[1], pos_from[0], pos_from[1], t)
        return reverse_edge in reservation_table

    def _expand_node(self, node: ConflictTreeNode, conflict: Dict) -> List[Optional[ConflictTreeNode]]:
        children = []
        for agent_id, constraint in self._constraints_from_conflict(conflict):
            child = self._create_child(node, agent_id, constraint)
            children.append(child)
        return children

    def _create_child(
        self,
        parent: ConflictTreeNode,
        agent_id: int,
        constraint: Constraint,
    ) -> Optional[ConflictTreeNode]:
        # Fast copy constraints
        new_constraints = defaultdict(list)
        for k, v in parent.constraints.items():
            new_constraints[k] = list(v)
        new_constraints[agent_id].append(constraint)

        # Build reservation table ONLY from this agent's constraints
        # This is the key principle of CBS: only respect explicit constraints
        reservation_table = self._build_constraint_table(new_constraints[agent_id])

        # Replan the agent with its constraints
        robot = next(r for r in self.robots if r.robot_id == agent_id)
        robot_proxy = _RobotProxy(robot.start_pos, robot.goal_pos)
        new_path = self._astar_single_robot(robot_proxy, reservation_table)
        self.low_level_calls += 1

        if new_path is None:
            return None

        # Fast copy paths
        new_paths = dict(parent.paths)
        new_paths[agent_id] = new_path

        new_conflicts = self.conflict_detector.detect_conflicts(new_paths)

        return ConflictTreeNode(
            constraints=new_constraints,
            paths=new_paths,
            conflicts=new_conflicts,
        )

    def _constraints_from_conflict(self, conflict: Dict) -> List[Tuple[int, Constraint]]:
        ctype = conflict.get("type")
        robots = conflict.get("robots", [])

        if len(robots) < 2:
            return []

        r1, r2 = robots[0], robots[1]
        t = conflict["time"]

        if ctype == "vertex":
            pos = conflict["pos"]
            return [
                (r1, Constraint(r1, pos, time=t)),
                (r2, Constraint(r2, pos, time=t)),
            ]

        if ctype == "swap":
            p_from, p_to = conflict["pos"]
            return [
                (r1, Constraint(r1, p_from, p_to, time=t)),
                (r2, Constraint(r2, p_to, p_from, time=t)),
            ]

        return []

    def _select_conflict(self, conflicts: List[Dict]) -> Optional[Dict]:
        if not conflicts:
            return None
        # Prioritize earlier conflicts and vertex conflicts over edge conflicts
        return min(conflicts, key=lambda c: (c["time"], 0 if c["type"] == "vertex" else 1))

    def _replan_path(self, agent_id: int, constraints: List[Constraint]) -> Optional[List]:
        robot = next(r for r in self.robots if r.robot_id == agent_id)
        robot_proxy = _RobotProxy(robot.start_pos, robot.goal_pos)
        constraint_table = self._build_constraint_table(constraints)
        return self._astar_single_robot(robot_proxy, constraint_table)

    def _build_constraint_table(self, constraints: List[Constraint]) -> Dict[Tuple, bool]:
        """
        Build constraint lookup table using dictionary for O(1) access.
        
        Returns:
            Dict mapping constraint keys to True (for fast 'in' checks)
            - Vertex: (x, y, time) -> True
            - Edge: (x1, y1, x2, y2, time) -> True
        """
        reservation_table = {}
        
        for c in constraints:
            if not c.is_edge:
                # Vertex constraint: position forbidden at specific time
                x, y = c.pos1
                reservation_table[(x, y, c.time)] = True
            else:
                # Edge constraint: movement from pos1 to pos2 forbidden at time
                x1, y1 = c.pos1
                x2, y2 = c.pos2
                reservation_table[(x1, y1, x2, y2, c.time)] = True
        
        return reservation_table

    def _priority(self, node: ConflictTreeNode) -> Tuple[float, float, int]:
        num_conflicts = len(node.conflicts)
        if self.objective == "conflicts":
            return (num_conflicts, node.flowtime, node.makespan)
        if self.objective == "flowtime":
            return (node.flowtime, node.makespan, num_conflicts)
        return (node.makespan, node.flowtime, num_conflicts)

    def _success_result(self, paths: Dict[int, List]) -> Dict[str, Any]:
        valid_paths = {rid: p for rid, p in paths.items() if p is not None}
        makespan = max(len(p) for p in valid_paths.values()) - 1 if valid_paths else 0
        flowtime = sum(len(p) - 1 for p in valid_paths.values()) if valid_paths else 0

        return {
            "paths": paths,
            "success": True,
            "makespan": makespan,
            "flowtime": flowtime,
            "cbs_iterations": self.high_level_iterations,
            "low_level_calls": self.low_level_calls,
            "final_conflicts": len(self.conflict_detector.detect_conflicts(paths)),
        }

    def _failure_result(self, paths: Optional[Dict[int, List]]) -> Dict[str, Any]:
        if paths is None:
            paths = {}
        valid_paths = {rid: p for rid, p in paths.items() if p is not None}
        makespan = max(len(p) for p in valid_paths.values()) - 1 if valid_paths else float("inf")
        flowtime = sum(len(p) - 1 for p in valid_paths.values()) if valid_paths else float("inf")

        return {
            "paths": paths,
            "success": False,
            "makespan": makespan,
            "flowtime": flowtime,
            "cbs_iterations": self.high_level_iterations,
            "low_level_calls": self.low_level_calls,
            "final_conflicts": len(self.conflict_detector.detect_conflicts(paths)) if paths else 0,
        }