try:
    from glowing import make_glowy2
except ImportError:
    make_glowy2 = None
from utils import *
import pygame
from pygame import Color
from bounce import Bounce


class Square:
    def __init__(self, x: float = 0, y: float = 0, dx: int = 1, dy: int = 1):

        # 构造函数，用于初始化Square对象
        # x, y: 初始位置的坐标，默认为(0, 0)
        # dx, dy: 初始方向向量的分量，默认为(1, 1)
        # 初始化Square对象，设置初始位置和方向
        self.pos: list[float] = [x, y]  # 位置坐标，x和y
        # self.pos是一个列表，包含两个浮点数，分别表示对象的x和y坐标
        self.dir: list[int] = [dx, dy]  # 方向向量，dx和dy
        # self.dir是一个列表，包含两个整数，分别表示对象在x和y方向上的移动速度
        self.last_bounce_time = -100  # 上次反弹的时间，初始化为-100
        # self.last_bounce_time记录上次反弹的时间，初始值设为-100，表示尚未发生反弹
        self.latest_bounce_direction = 0  # 0 = horiz, 1 = vert
        # self.latest_bounce_direction记录最近一次反弹的方向，0表示水平方向，1表示垂直方向
        self.past_colors = []
        # self.past_colors是一个列表，用于存储对象过去经历的颜色
        self.died = False

        # self.died是一个布尔值，表示对象是否已经“死亡”，初始为False
        self.time_since_glow_start = 0
        # self.time_since_glow_start记录自发光开始以来的时间，初始为0
        self.glowy_surfaces = {}

    def register_past_color(self, col: tuple[int, int, int]):
        # 遍历次数由Config.square_swipe_anim_speed和1中的较大值决定
        for _ in range(max(Config.square_swipe_anim_speed, 1)):
            # 将新的颜色col插入到past_colors列表的开头
            self.past_colors.insert(0, col)
        # 当past_colors列表的长度超过Config.SQUARE_SIZE的4/5时，移除列表末尾的元素
        while len(self.past_colors) > Config.SQUARE_SIZE * 4 / 5:
            self.past_colors.pop()

    def get_surface(self, size: tuple[int, int]):
        # 计算方块表面的大小，为配置中定义的方块大小的4/5
        ss = int(Config.SQUARE_SIZE * 4 / 5)
        # 创建一个pygame.Surface对象，大小为(ss, ss)
        surf = pygame.Surface((ss, ss))
        # 遍历self.past_colors中的每个颜色
        for index, col in enumerate(self.past_colors):
            # 根据self.dir_y的值决定y坐标的位置
            # 如果self.dir_y为1，则y坐标从底部开始计算，否则从顶部开始计算
            y = index if self.dir_y != 1 else ss - 1 - index
            # 在surf上绘制一条从(0, y)到(ss, y)的线，颜色为col
            pygame.draw.line(surf, col, (0, y), (ss, y))
        # 将surf缩放到指定的大小size
        return pygame.transform.scale(surf, size)

    def copy(self) -> "Square":
        # 创建一个新的Square对象，其位置和方向与当前对象相同
        new = Square(*self.pos, *self.dir)
        # 将当前对象的最后一次反弹时间赋值给新对象
        new.last_bounce_time = self.last_bounce_time
        # 将当前对象的最新反弹方向赋值给新对象
        new.latest_bounce_direction = self.latest_bounce_direction
        # 返回新创建的Square对象
        return new

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    def title_screen_physics(self, bounding: pygame.Rect):
        # 调用对象的常规移动方法，可能是更新位置等
        self.reg_move()
        # 获取对象的矩形区域
        r = self.rect
        # 检查对象的右边界是否超出边界框的右边界
        if r.right > bounding.right:
            # 如果超出，则改变水平方向为向左
            self.dir[0] = -1
            # 记录最新的反弹方向为水平方向
            self.latest_bounce_direction = 0
        # 检查对象的左边界是否超出边界框的左边界
        elif r.left < bounding.left:
            # 如果超出，则改变水平方向为向右
            self.dir[0] = 1
            # 记录最新的反弹方向为水平方向
            self.latest_bounce_direction = 0
        # 检查对象的底部是否超出边界框的底部
        elif r.bottom > bounding.bottom:
            # 如果超出，则改变垂直方向为向上
            self.dir[1] = -1
            # 记录最新的反弹方向为垂直方向
            self.latest_bounce_direction = 1
        # 检查对象的顶部是否超出边界框的顶部
        elif r.top < bounding.top:
            # 如果超出，则改变垂直方向为向下
            self.dir[1] = 1
            # 记录最新的反弹方向为垂直方向
            self.latest_bounce_direction = 1
        else:
            # 如果没有超出任何边界，则返回False
            return False
        # 调用开始反弹的方法，可能是处理反弹时的特效或逻辑
        self.start_bounce()
        # 更新最后一次反弹的时间
        self.last_bounce_time = get_current_time()
        # 返回True表示发生了反弹
        return True

    def compute_glowy_surface(self, rect, val):
        # 调用 make_glowy2 函数生成发光的边框图像，参数为 (rect.size[0] + 40, rect.size[1] + 40) 表示图像的尺寸，
        # Color(Config.glow_color) 表示发光的颜色，val 表示发光的强度
        glowy_borders = make_glowy2((rect.size[0] + 40, rect.size[1] + 40), Color(Config.glow_color), val)
        # 创建一个新的 Surface 对象，尺寸为 rect.inflate(100, 100).size，即原始矩形尺寸基础上各增加 100 像素，
        # pygame.SRCALPHA 表示该 Surface 对象支持透明度
        surface = pygame.Surface(rect.inflate(100, 100).size, pygame.SRCALPHA)
        # 将生成的发光边框图像 blit 到新的 Surface 对象上，位置为 (20, 20)，
        # special_flags=pygame.BLEND_RGBA_ADD 表示使用 RGBA 加法混合模式进行绘制，以增强发光效果
        surface.blit(glowy_borders, (20, 20), special_flags=pygame.BLEND_RGBA_ADD)
        # 返回处理后的 Surface 对象
        return surface

    def draw_glowing3(self, win, rect):
        # 如果对象已经死亡，则直接返回，不执行后续代码
        if self.died:
            return

        # 检查配置是否启用了方块的发光效果
        if Config.square_glow:
            # 计算当前时间与发光开始时间的差值，判断是否在发光持续时间范围内
            if pygame.time.get_ticks() - self.time_since_glow_start < Config.square_glow_duration * 1000:
                # 计算发光的进度，进度值从1递减到0
                progress = 1 - (pygame.time.get_ticks() - self.time_since_glow_start) / (
                        Config.square_glow_duration * 1000)
                # 根据进度计算发光强度，强度值从最大到最小
                val = int(progress * Config.glow_intensity)
            else:
                # 如果已经超过发光持续时间，则发光强度设为最小值
                val = 1
            # 确保发光强度不小于配置的最小发光强度
            val = max(val, Config.square_min_glow)
            # 计算发光效果的表面
            surf = self.compute_glowy_surface(rect, val)

            # 将发光效果绘制到窗口上，位置偏移(-40, -40)，并使用BLEND_RGBA_ADD特殊标志进行混合
            win.blit(surf, rect.move(-40, -40).topleft, special_flags=pygame.BLEND_RGBA_ADD)

    def draw(self, screen: pygame.Surface, sqrect: pygame.Rect):
        # 如果对象已经死亡，则直接返回，不进行绘制
        if self.died:
            return
        # 计算方块颜色的索引，根据方向向量(dir_x, dir_y)来决定颜色
        square_color_index = round((self.dir_x + 1) / 2 + self.dir_y + 1)
        # 获取方块颜色，并注册到历史颜色列表中
        self.register_past_color(get_colors()["square"][square_color_index % len(get_colors()["square"])])

        # 根据当前主题和make_glowy2函数是否存在来决定是否绘制发光效果
        if Config.theme == "dark_modern" and make_glowy2 is not None:
            self.draw_glowing3(screen, sqrect)
        else:
            # 如果不是暗黑现代主题或者make_glowy2函数不存在，则绘制黑色矩形
            pygame.draw.rect(screen, (0, 0, 0), sqrect)
            # 获取缩小的方块表面，并绘制到屏幕上
            sq_surf = self.get_surface(
                tuple(sqrect.inflate(-int(Config.SQUARE_SIZE / 5), -int(Config.SQUARE_SIZE / 5))[2:]))
            screen.blit(sq_surf, sq_surf.get_rect(center=sqrect.center))

    @x.setter
    def x(self, val: int):  # 定义一个名为x的方法，接收一个整数参数val
        self.pos[0] = val  # 将传入的整数val赋值给实例属性self.pos的第一个元素

    @y.setter
    def y(self, val: int):  # 定义一个名为y的方法，接收一个整数参数val
        self.pos[1] = val  # 将传入的整数val赋值给实例变量self.pos的第二个元素（索引为1）

    @property
    def dir_x(self):
        # 返回对象self的dir属性的第一个元素
        return self.dir[0]

    @property
    def dir_y(self):
        # 返回对象的dir属性的第二个元素（即y方向的值）
        return self.dir[1]

    @property
    def rect(self):
        # 返回一个pygame.Rect对象，用于表示矩形区域
        # self.x 和 self.y 是矩形的中心点坐标
        # Config.SQUARE_SIZE 是矩形边长的大小
        # 通过减去 Config.SQUARE_SIZE / 2，将中心点坐标转换为左上角坐标
        # *([Config.SQUARE_SIZE] * 2) 将 Config.SQUARE_SIZE 重复两次作为矩形的宽和高
        return pygame.Rect(self.x - Config.SQUARE_SIZE / 2, self.y - Config.SQUARE_SIZE / 2,
                           *([Config.SQUARE_SIZE] * 2))

    def start_bounce(self):
        # 获取当前的时间戳，并将其赋值给实例变量 time_since_glow_start
        # 这个时间戳用于记录开始发光的时间，以便后续计算时间间隔
        self.time_since_glow_start = pygame.time.get_ticks()

    def obey_bounce(self, bounce: Bounce):
        # 调用start_bounce方法，可能是初始化一些状态或执行一些准备工作
        self.start_bounce()
        # 更新当前对象的位置为bounce对象中的square_pos属性值
        self.pos = bounce.square_pos
        # 更新当前对象的方向为bounce对象中的square_dir属性值
        self.dir = bounce.square_dir
        # 更新最新一次反弹的方向为bounce对象中的bounce_dir属性值
        self.latest_bounce_direction = bounce.bounce_dir
        # 更新最后一次反弹的时间为bounce对象中的time属性值
        self.last_bounce_time = bounce.time
        # 函数执行完毕，返回None
        return

    def reg_move(self, use_dt: bool = True):
        # 如果use_dt为True，则使用Config.dt作为时间步长，否则使用1/FRAMERATE
        # 更新对象在x方向上的位置
        self.x += self.dir_x * Config.square_speed * (Config.dt if use_dt else 1 / FRAMERATE)
        # 更新对象在y方向上的位置
        self.y += self.dir_y * Config.square_speed * (Config.dt if use_dt else 1 / FRAMERATE)
