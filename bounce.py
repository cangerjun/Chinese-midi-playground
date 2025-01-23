import pygame
from utils import *


class Bounce:
    def __init__(self, sq_pos: list[float], sq_dir: list[int], time: float, bounce_dir: int):
        self.square_pos = sq_pos  # 新方块位置
        self.square_dir = sq_dir  # 新方块方向
        self.bounce_dir = bounce_dir  # 新方块反弹方向
        self.time = time  # 弹跳时间

    def get_collision_rect(self):
        sx, sy = self.square_pos
        if self.bounce_dir == 0:
            # 碰撞左右墙壁
            if self.square_dir[0] == -1:
                # 右墙壁
                return pygame.Rect(
                    sx + Config.SQUARE_SIZE / 2 + 1,
                    sy - 10,
                    10,
                    20
                )
            elif self.square_dir[0] == 1:
                # 左墙壁
                return pygame.Rect(
                    sx - 10 - Config.SQUARE_SIZE / 2 - 1,
                    sy - 10,
                    10,
                    20
                )
        elif self.bounce_dir == 1:
            # 碰撞上下墙壁
            if self.square_dir[1] == -1:
                # 下墙壁
                return pygame.Rect(
                    sx - 10,
                    sy + Config.SQUARE_SIZE / 2 + 1,
                    20,
                    10
                )
            elif self.square_dir[1] == 1:
                # 上墙壁
                return pygame.Rect(
                    sx - 10,
                    sy - 10 - Config.SQUARE_SIZE / 2 - 1,
                    20,
                    10
                )

    def copy(self) -> "Bounce":
        return Bounce(self.square_pos, self.square_dir, self.time, self.bounce_dir)

    def __repr__(self):
        return f"<Bounce(sq_pos={self.square_pos}, sq_dir={self.square_dir}, time={self.time}, dir={self.bounce_dir})>"