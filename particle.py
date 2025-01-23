import random
from utils import *
import pygame


class Particle:
    # 定义粒子速度变化的范围
    SPEED_VARIATION = 4
    # 定义粒子大小的最小值
    SIZE_MIN = 7
    # 定义粒子大小的最大值
    SIZE_MAX = 14
    # 定义粒子老化的速率
    AGE_RATE = 20
    # 定义粒子减速的速率
    SLOW_DOWN_RATE = 1.2

    def __init__(self, pos: list[float], delta: list[float], invert_color: bool = False):
        # 初始化粒子的位置，复制传入的位置列表以避免外部修改
        self.pos = pos.copy()
        # 随机生成粒子的大小，范围在SIZE_MIN和SIZE_MAX之间
        self.size = random.randint(Particle.SIZE_MIN, Particle.SIZE_MAX)
        # 初始化粒子的速度变化量，复制传入的速度变化列表以避免外部修改
        self.delta = delta.copy()
        # 在x方向上添加随机速度变化，范围在-SPEED_VARIATION/8到SPEED_VARIATION/8之间
        self.delta[0] += random.randint(-Particle.SPEED_VARIATION, Particle.SPEED_VARIATION)/8
        # 在y方向上添加随机速度变化，范围在-SPEED_VARIATION/8到SPEED_VARIATION/8之间
        self.delta[1] += random.randint(-Particle.SPEED_VARIATION, Particle.SPEED_VARIATION)/8
        # color is hallway color if invert_color is false, else it's background color
        self.color = get_colors()["hallway"] if not invert_color else get_colors()["background"]

    def age(self):
        # 减少粒子的尺寸，根据AGE_RATE和时间步长Config.dt计算
        self.size -= Particle.AGE_RATE*Config.dt
        # 更新粒子的x坐标，根据速度Config.PARTICLE_SPEED和方向delta[0]
        self.x += self.delta[0] * Config.PARTICLE_SPEED
        # 更新粒子的y坐标，根据速度Config.PARTICLE_SPEED和方向delta[1]
        self.y += self.delta[1] * Config.PARTICLE_SPEED
        # 减缓粒子的x方向速度，根据减速率Particle.SLOW_DOWN_RATE、帧率FRAMERATE和时间步长Config.dt计算
        self.delta[0] /= (Particle.SLOW_DOWN_RATE+FRAMERATE) * Config.dt
        # 减缓粒子的y方向速度，根据减速率Particle.SLOW_DOWN_RATE、帧率FRAMERATE和时间步长Config.dt计算
        self.delta[1] /= (Particle.SLOW_DOWN_RATE+FRAMERATE) * Config.dt
        # 返回粒子的尺寸是否小于等于0，用于判断粒子是否应该被移除
        return self.size <= 0

    @property
    def x(self):
        # 返回对象的pos属性的第一个元素
        # 假设self.pos是一个包含至少一个元素的列表或元组
        return self.pos[0]

    @x.setter
    def x(self, val: float):  # 定义一个名为x的方法，接收一个浮点数类型的参数val
        self.pos[0] = val  # 将传入的浮点数val赋值给实例属性self.pos的第一个元素

    @property
    def y(self):  # 定义一个名为y的方法，该方法属于某个类
        return self.pos[1]  # 返回对象的pos属性中的第二个元素（索引为1的元素），通常用于获取二维坐标中的y坐标

    @y.setter
    def y(self, val: float):  # 定义一个名为y的方法，接收一个浮点数参数val
        self.pos[1] = val  # 将传入的浮点数val赋值给实例属性self.pos的第二个元素（索引为1）

    @property
    def rect(self):
        # 返回一个pygame.Rect对象，用于表示矩形区域
        # self.x 和 self.y 分别表示矩形的中心点坐标
        # self.size 表示矩形的大小（宽度和高度相同）
        # self.size/2 用于计算矩形左上角的坐标，因为中心点坐标需要减去一半的大小
        # *(2*[self.size]) 用于生成矩形的宽度和高度，这里使用了列表乘法生成两个相同的值
        return pygame.Rect(self.x-self.size/2, self.y-self.size/2, *(2*[self.size]))