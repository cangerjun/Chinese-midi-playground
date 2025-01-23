from utils import *
import pygame


# 导入 Enum 类，用于创建枚举类型
from enum import Enum
# 定义一个名为 HitLevel 的枚举类，用于表示不同的打击等级
class HitLevel(Enum):
    # early 表示早击，对应的值为 0
    early = 0
    # good 表示好击，对应的值为 1
    good = 1
    # perfect 表示完美击，对应的值为 2
    perfect = 2
    # late 表示晚击，对应的值为 3
    late = 3
    # miss 表示未击中，对应的值为 4
    miss = 4


class HitIcon:
    # 定义一个字典，用于存储不同HitLevel对应的Surface对象
    surfaces: dict[HitLevel, pygame.Surface] = {}

    def __init__(self, lvl: HitLevel, pos: Union[tuple[int, int], list[int]]):
        # 如果surfaces字典为空，则加载所有HitLevel对应的图片
        if len(HitIcon.surfaces) == 0:
            for level in HitLevel:
                # 加载图片并转换为带有alpha通道的Surface对象
                HitIcon.surfaces[level] = pygame.image.load(f"./assets/{level.name}.png").convert_alpha()

        # 初始化位置、等级、剩余寿命和Surface对象
        self.pos = pos
        self.lvl = lvl
        self.age_left = 500
        self.surf = HitIcon.surfaces[lvl].copy()

    def draw(self, screen: pygame.Surface, camera):
        # 减少剩余寿命
        self.age_left -= 500*Config.dt
        # 设置Surface的透明度，透明度值在0到255之间
        self.surf.set_alpha(int(max(min(self.age_left, 255), 0)))
        # 将Surface对象绘制到屏幕上，位置根据相机偏移量调整
        screen.blit(self.surf, camera.offset(self.surf.get_rect(center=self.pos)))
        # 返回剩余寿命是否小于等于0
        return self.age_left <= 0
