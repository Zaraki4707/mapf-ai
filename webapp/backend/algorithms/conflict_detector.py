from collections import defaultdict
from typing import List, Dict, Tuple


class ConflictDetector:
    """
    Conflict detection system that identifies three types of collisions between robot paths.
    """

    def __init__(self):
        self.conflicts: List[Dict] = []

    def detect_vertex_conflicts(self, paths: Dict) -> List[Dict]:
        conflicts = []
        robot_ids = list(paths.keys())
        valid_paths = {k: v for k, v in paths.items() if v is not None and len(v) > 0}
        if not valid_paths:
            return conflicts
        max_time = max(len(path) for path in valid_paths.values())

        for t in range(max_time):
            positions_at_t = {}
            for robot_id in robot_ids:
                path = paths[robot_id]
                if path and t < len(path):
                    positions_at_t[robot_id] = path[t]

            position_to_robots = defaultdict(list)
            for robot_id, pos in positions_at_t.items():
                position_to_robots[pos].append(robot_id)

            for pos, robots in position_to_robots.items():
                if len(robots) > 1:
                    conflicts.append({
                        'type': 'vertex',
                        'robot1': robots[0],
                        'robot2': robots[1],
                        'time': t,
                        'position': pos
                    })
        return conflicts

    def detect_edge_conflicts(self, paths: Dict) -> List[Dict]:
        conflicts = []
        robot_ids = list(paths.keys())
        valid_paths = {k: v for k, v in paths.items() if v is not None and len(v) > 0}
        if not valid_paths:
            return conflicts
        max_time = max(len(path) for path in valid_paths.values()) - 1

        for t in range(max_time):
            edges_at_t = {}
            for robot_id in robot_ids:
                path = paths[robot_id]
                if path and t + 1 < len(path):
                    edge = (path[t], path[t + 1])
                    edges_at_t[(edge, robot_id)] = edge

            edge_to_robots = defaultdict(list)
            for (edge, robot_id), edge_pos in edges_at_t.items():
                edge_to_robots[edge_pos].append(robot_id)

            for edge, robots in edge_to_robots.items():
                if len(robots) > 1:
                    conflicts.append({
                        'type': 'edge',
                        'robot1': robots[0],
                        'robot2': robots[1],
                        'time': t,
                        'edge': edge
                    })
        return conflicts

    def detect_swap_conflicts(self, paths: Dict) -> List[Dict]:
        conflicts = []
        robot_ids = list(paths.keys())
        max_time = max(len(path) for path in paths.values()) - 1

        for t in range(max_time):
            for i, robot1_id in enumerate(robot_ids):
                for robot2_id in robot_ids[i+1:]:
                    path1 = paths[robot1_id]
                    path2 = paths[robot2_id]
                    if not path1 or not path2:
                        continue
                    if t + 1 >= len(path1) or t + 1 >= len(path2):
                        continue
                    pos1_t = path1[t]
                    pos1_t1 = path1[t + 1]
                    pos2_t = path2[t]
                    pos2_t1 = path2[t + 1]
                    if pos1_t == pos2_t1 and pos2_t == pos1_t1:
                        conflicts.append({
                            'type': 'swap',
                            'robot1': robot1_id,
                            'robot2': robot2_id,
                            'time': t,
                            'positions': (pos1_t, pos2_t)
                        })
        return conflicts

    def detect_edge_swap_conflicts(self, paths: Dict) -> List[Dict]:
        conflicts = []
        robot_ids = list(paths.keys())
        valid_paths = {k: v for k, v in paths.items() if v is not None and len(v) > 0}
        if not valid_paths:
            return conflicts
        max_time = max(len(path) for path in valid_paths.values()) - 1

        for t in range(max_time):
            for i, robot1_id in enumerate(robot_ids):
                for robot2_id in robot_ids[i+1:]:
                    path1 = paths[robot1_id]
                    path2 = paths[robot2_id]
                    if not path1 or not path2:
                        continue
                    if t + 1 >= len(path1) or t + 1 >= len(path2):
                        continue
                    edge1 = (path1[t], path1[t + 1])
                    edge2 = (path2[t], path2[t + 1])
                    if edge1 == edge2[::-1]:
                        conflicts.append({
                            'type': 'edge-swap',
                            'robot1': robot1_id,
                            'robot2': robot2_id,
                            'time': t,
                            'edge': edge1
                        })
        return conflicts

    def detect_following_conflicts(self, paths: Dict) -> List[Dict]:
        conflicts = []
        robot_ids = list(paths.keys())
        valid_paths = {k: v for k, v in paths.items() if v is not None and len(v) > 0}
        if not valid_paths:
            return conflicts
        max_time = max(len(path) for path in valid_paths.values()) - 1

        for t in range(max_time):
            for i, robot1_id in enumerate(robot_ids):
                for robot2_id in robot_ids[i+1:]:
                    path1 = paths[robot1_id]
                    path2 = paths[robot2_id]
                    if not path1 or not path2:
                        continue
                    if t + 1 >= len(path1) or t >= len(path2):
                        continue
                    if path1[t + 1] == path2[t]:
                        conflicts.append({
                            'type': 'following',
                            'robot1': robot1_id,
                            'robot2': robot2_id,
                            'time': t,
                            'position': path2[t]
                        })
        return conflicts

    def get_conflict_report(self, paths: Dict) -> List[Dict]:
        vertex_conflicts = self.detect_vertex_conflicts(paths)
        edge_conflicts = self.detect_edge_conflicts(paths)
        swap_conflicts = self.detect_swap_conflicts(paths)
        edge_swap_conflicts = self.detect_edge_swap_conflicts(paths)
        following_conflicts = self.detect_following_conflicts(paths)
        self.conflicts = vertex_conflicts + edge_conflicts + swap_conflicts + edge_swap_conflicts + following_conflicts
        return self.conflicts

    def count_conflicts(self, paths: Dict) -> int:
        return len(self.get_conflict_report(paths))

    def pad_paths(self, paths: Dict) -> Dict:
        max_time = max(len(path) for path in paths.values()) if paths else 0
        padded_paths = {}

        for robot_id, path in paths.items():
            if path and len(path) > 0:
                goal_pos = path[-1]
                padded_path = path + [goal_pos] * (max_time - len(path))
                padded_paths[robot_id] = padded_path
        return padded_paths

    def detect_conflicts(self, paths: Dict) -> List[Dict]:
        """Detect conflicts in the format expected by CBS (Main.ipynb)."""
        conflicts = []
        padded = self.pad_paths(paths)
        if not padded:
            return []

        robot_ids = list(padded.keys())
        horizon = len(next(iter(padded.values())))

        for t in range(horizon):
            pos_map = defaultdict(list)
            for rid in robot_ids:
                pos = padded[rid][t]
                pos_map[pos].append(rid)
            for pos, robots in pos_map.items():
                if len(robots) > 1:
                    conflicts.append({'type': 'vertex', 'time': t, 'pos': pos, 'robots': robots})

            if t < horizon - 1:
                for i, r1 in enumerate(robot_ids):
                    for r2 in robot_ids[i+1:]:
                        if padded[r1][t] == padded[r2][t+1] and padded[r1][t+1] == padded[r2][t] and padded[r1][t] != padded[r1][t+1]:
                            conflicts.append({'type': 'swap', 'time': t, 'robots': [r1, r2], 'pos': (padded[r1][t], padded[r1][t+1])})
        return conflicts