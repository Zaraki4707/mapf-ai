from typing import Tuple, List
from .grid import GridEnvironment


class Robot:
    """Represents a single robot in the warehouse"""

    def __init__(self, robot_id: int, grid: GridEnvironment, start_pos: Tuple[int, int], goal_pos: Tuple[int, int], color: str = 'blue'):
        self.robot_id = robot_id
        self.grid = grid
        self.start_pos = start_pos
        self.goal_pos = goal_pos
        self.current_pos = start_pos
        self.path: List[Tuple[int, int]] = []
        self.path_index = 0
        self.color = color

    def get_current_position(self) -> Tuple[int, int]:
        return self.current_pos

    def get_goal_position(self) -> Tuple[int, int]:
        return self.goal_pos

    def get_start_position(self) -> Tuple[int, int]:
        return self.start_pos

    def set_path(self, path: List[Tuple[int, int]]) -> None:
        self.path = path
        self.path_index = 0

    def get_path(self) -> List[Tuple[int, int]]:
        return self.path

    def get_position_at_time(self, time_step: int) -> Tuple[int, int]:
        if time_step < len(self.path):
            return self.path[time_step]
        else:
            return self.path[-1] if self.path else self.current_pos

    def is_at_goal(self) -> bool:
        return self.current_pos == self.goal_pos