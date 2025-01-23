from utils import *
from square import Square


class Camera:
    def __init__(self, x: int = 0, y: int = 0):
        self.x = x
        self.y = y
        # ?x, ?y 是用于其他用途的变量
        self.ax = 0
        self.ay = 0
        self.bx = 0
        self.by = 0
        self.locked_on_square = True
        self.lock_type: CameraFollow = CameraFollow(2)

    def attempt_movement(self):
        # 如果相机没有锁定在方块上，则尝试移动相机
        if not self.locked_on_square:
            keys = pygame.key.get_pressed()
            # 检查是否按下了 Shift 键，按下则加速移动
            shift_modifier = (keys[pygame.K_LSHIFT] | keys[pygame.K_RSHIFT]) + 1
            # 根据按键更新相机的 x 坐标
            self.x += (keys[pygame.K_d] - keys[pygame.K_a]) * Config.CAMERA_SPEED * shift_modifier / FRAMERATE
            # 根据按键更新相机的 y 坐标
            self.y += (keys[pygame.K_s] - keys[pygame.K_w]) * Config.CAMERA_SPEED * shift_modifier / FRAMERATE

    @property
    def pos(self):
        # 返回相机的位置
        return self.x, self.y

    @pos.setter
    def pos(self, val: Union[tuple[int, int], list[int]]):
        # 设置相机的位置
        self.x, self.y = val

    def offset(self, pos_or_rect: Union[pygame.Rect, tuple[int, int]]) -> Union[pygame.Rect, list[int]]:
        # 根据相机位置偏移给定的位置或矩形
        if isinstance(pos_or_rect, pygame.Rect):
            return pos_or_rect.move(-self.x, -self.y)
        else:
            return [pos_or_rect[0] - self.x, pos_or_rect[1] - self.y]

    def follow(self, square: Square):
        # 根据不同的锁定类型更新相机位置

        # 方块在中心
        if self.lock_type == CameraFollow.Center:
            self.pos = [square.x - Config.SCREEN_WIDTH / 2, square.y - Config.SCREEN_HEIGHT / 2]

        # 相机仅在必要时跟随
        if self.lock_type == CameraFollow.Lazy:
            lazy_follow_distance = 250
            while square.x - Config.SCREEN_WIDTH + lazy_follow_distance > self.x:
                self.x += 1
            while square.y - Config.SCREEN_HEIGHT + lazy_follow_distance > self.y:
                self.y += 1
            while square.x - lazy_follow_distance < self.x:
                self.x -= 1
            while square.y - lazy_follow_distance < self.y:
                self.y -= 1

        # 平滑相机
        if self.lock_type == CameraFollow.Smoothed:
            easing_rate = 3
            self.x = (square.x - Config.SCREEN_WIDTH / 2) * easing_rate * Config.dt + self.x - easing_rate * self.x * Config.dt
            self.y = (square.y - Config.SCREEN_HEIGHT / 2) * easing_rate * Config.dt + self.y - easing_rate * self.y * Config.dt

        # 相机领先方块
        if self.lock_type == CameraFollow.Predictive:
            self.ax = (square.x - Config.SCREEN_WIDTH / 2) * 3 * Config.dt + self.ax - 3 * self.ax * Config.dt
            self.ay = (square.y - Config.SCREEN_HEIGHT / 2) * 3 * Config.dt + self.ay - 3 * self.ay * Config.dt
            damping = 1
            self.bx = square.x - damping * (self.ax - square.x) - Config.SCREEN_WIDTH / 2 - Config.SCREEN_WIDTH / 2 * damping
            self.by = square.y - damping * (self.ay - square.y) - Config.SCREEN_HEIGHT / 2 - Config.SCREEN_HEIGHT / 2 * damping
            self.x = self.x * (1 - 3 * Config.dt) + self.bx * 3 * Config.dt
            self.y = self.y * (1 - 3 * Config.dt) + self.by * 3 * Config.dt