from particle import Particle
from square import Square
from utils import *
from random import randint
import pygame


def draw_beveled_rectangle(surf: pygame.Surface, color: pygame.Color, rect: pygame.Rect) -> None:
    """i think they're called bevels"""
    pygame.draw.rect(surf, color.lerp((0, 0, 0), 0.4), rect.inflate(8, 8), border_radius=4)
    pygame.draw.rect(surf, color, rect, border_radius=2)


class MenuOption:
    # 定义菜单选项的高度，基于屏幕高度的一部分减去一个固定值
    HEIGHT = (Config.SCREEN_HEIGHT//9)-2
    # 定义菜单选项之间的间距
    SPACING = 16

    def __init__(self, id_: str, color: pygame.Color):
        # 初始化菜单选项的ID
        self.id = id_
        title = lang_key(id_)  # 翻译实际标题
        self.color = color  # 设置菜单选项的颜色
        self.before_hover = False# 是否在悬停
        self.hover_anim: float = 0  # 悬停动画的进度

        # 这种图形编程是我做过的最无聊的事情
        font = get_font(Config.SCREEN_HEIGHT // 15)
        # 创建一个字体对象，基于屏幕高度和字体大小来确定字体大小
        title_surface = font.render(title, True, color.lerp((0, 0, 0), 0.7))
        # 创建一个标题文本的Surface
        brighter_title_surface = font.render(title, True, color.lerp((0, 0, 0), 0.2))
        # 创建一个标题文本的Surface
        shadow_surface = pygame.Surface((brighter_title_surface.get_rect().width + 100, MenuOption.HEIGHT), pygame.SRCALPHA)
        # 创建一个阴影Surface，并使用pygame.transform.chop函数裁剪标题Surface，以创建一个阴影效果
        for _ in range(100):
            chopped = pygame.transform.chop(brighter_title_surface, pygame.Rect(0, MenuOption.HEIGHT-9+lang_key("font-menu-shadow-length-offset") - _, 0, 600))
            # 使用pygame.transform.chop函数裁剪标题Surface，以创建一个阴影效果
            shadow_surface.blit(chopped, (_, _))
            # 将裁剪后的标题Surface绘制到阴影Surface上

        self.surface = pygame.Surface((int(Config.SCREEN_WIDTH / 2 + 300), self.HEIGHT + 8), pygame.SRCALPHA)
        # 创建一个Surface对象，用于绘制菜单选项
        draw_beveled_rectangle(self.surface, self.color, pygame.Rect(4, 4, Config.SCREEN_WIDTH, MenuOption.HEIGHT))
        # 绘制一个阴影Surface
        title_rect = title_surface.get_rect(midleft=self.surface.get_rect().midleft).move(50, 0)
        # 创建一个标题文本的Rect对象，并移动到正确的位置
        self.surface.blit(shadow_surface, shadow_surface.get_rect(midleft=title_rect.midleft).move(0, lang_key("font-menu-shadow-offset")))
        # 绘制阴影Surface到Surface上
        self.surface.blit(title_surface, title_rect)
        # 绘制标题Surface到Surface上
    def update_hover(self, y_value: int) -> None:
        # 创建一个矩形对象，用于表示鼠标悬停区域
        wide_rect = pygame.Rect(0, y_value, Config.SCREEN_WIDTH, MenuOption.HEIGHT)
        # 根据悬停动画的插值函数调整矩形的水平位置
        wide_rect.move_ip(int(Config.SCREEN_WIDTH / 2) - 30 * interpolate_fn(self.hover_anim), 0)
        # 检查鼠标位置是否与矩形相交（即鼠标是否在悬停区域内）
        if wide_rect.collidepoint(pygame.mouse.get_pos()):
            # 如果鼠标在悬停区域内，增加悬停动画的进度
            self.hover_anim += 9 / FRAMERATE
        else:
            # 如果鼠标不在悬停区域内，减少悬停动画的进度
            self.hover_anim -= 3 / FRAMERATE
        # 限制悬停动画的进度在0到1之间
        self.hover_anim = max(min(self.hover_anim, 1), 0)

    def get_rect(self, y_value: int) -> pygame.Rect:
        # 创建一个矩形对象，宽度和屏幕宽度相同，高度为MenuOption.HEIGHT，初始位置在屏幕左侧
        wide_rect = pygame.Rect(0, y_value, Config.SCREEN_WIDTH, MenuOption.HEIGHT)
        # 计算矩形在水平方向上的偏移量，偏移量基于hover_anim的插值函数结果
        # interpolate_fn(self.hover_anim)返回一个0到1之间的值，表示动画的进度
        # 乘以60得到偏移量，再减去60得到最终的偏移值
        # int(Config.SCREEN_WIDTH / 2) - 60 * interpolate_fn(self.hover_anim)计算矩形在水平方向上的新位置
        wide_rect.move_ip(int(Config.SCREEN_WIDTH / 2) - 60 * interpolate_fn(self.hover_anim), 0)
        # 返回计算后的矩形对象
        return wide_rect


class Menu:
    def __init__(self):
        # 初始化菜单选项，每个选项都有一个名称和对应的颜色
        self.menu_options: list[MenuOption] = [
            MenuOption("play", pygame.Color(214, 247, 163)),# "play"选项
            MenuOption("config", pygame.Color(196, 255, 178)),# "config"选项
            MenuOption("contribute", pygame.Color(183, 227, 204)),# "contribute"选项
            MenuOption("open-songs-folder", pygame.Color(125, 130, 184)),
            MenuOption("quit", pygame.Color(226, 109, 92))
        ]
        self.anim = 1  # 动画状态变量
        # 注意，在跑马灯文本的每一行代码后面都有空格
        self.marquee_text = lang_key("title-marquee")
        # 创建一个跑马灯文本的Surface对象，并使用get_font函数获取字体对象
        self.title_surf = get_font(72).render(lang_key("title"), True, get_colors()["hallway"])
        # 创建一个标题Surface对象，并使用get_font函数获取字体对象
        self.marquee_surf = get_font(24).render(self.marquee_text, True, get_colors()["hallway"])
        # 创建一个跑马灯Surface对象，并使用get_font函数获取字体对象，并使用lang_key函数获取文本
        self.flags = {}
        for language in TRANSLATIONS:# 遍历所有语言
            self.flags[language] = pygame.image.load(f"./assets/flags/{language}.png").convert_alpha()
            # 加载每个语言对应的国旗图片，并使用convert_alpha方法转换为alpha格式，以减少内存消耗
        self.prev_active = True# 初始化前一个菜单的激活状态为True
        self.active = True# 初始化菜单的激活状态为True
        self.square = Square(100, 320) # 创建一个正方形对象，并设置其位置为(100, 320)
        self.particles: list[Particle] = []# 创建一个粒子列表

        self.left_lang_rect: Optional[pygame.Rect] = None
        self.right_lang_rect: Optional[pygame.Rect] = None
        self.requires_restart_surf: Optional[pygame.Surface] = None

    @property
    def screensaver_rect(self):
        # 返回一个pygame.Rect对象，用于定义屏幕保护程序的矩形区域
        # Rect的左上角坐标为(0, 0)
        # Rect的宽度为屏幕宽度的一半减去100，高度为屏幕高度
        # inflate(-100, -100)方法用于调整矩形的大小，使其四周各缩小100个像素
        return pygame.Rect(0, 0, int(Config.SCREEN_WIDTH / 2 - 100), Config.SCREEN_HEIGHT).inflate(-100, -100)

    def draw(self, screen: pygame.Surface, n_frames: int):
        # 检查当前对象是否处于激活状态
        if self.active:
            # 如果动画状态为0，则初始化为0.3
            if self.anim == 0:
                self.anim = 0.3
            # 每帧增加动画状态值，以实现动画效果
            self.anim += 1.8 / FRAMERATE
        else:
            # 如果对象未激活，则减少动画状态值
            self.anim -= 1.8 / FRAMERATE
        # 限制动画状态值在0到1之间
        self.anim = max(min(self.anim, 1), 0)
        # 如果动画状态为0，则直接返回，不进行绘制
        if not self.anim:
            return

        # 如果对象从非激活状态变为激活状态，则重新生成标题和跑马灯文本的Surface对象
        if self.active and not self.prev_active:
            self.title_surf = get_font(72).render(lang_key("title"), True, get_colors()["hallway"])
            # 更新标题Surface对象
            self.marquee_surf = get_font(24).render(self.marquee_text, True, get_colors()["hallway"])
            # 更新前一帧的激活状态
        self.prev_active = self.active
        # 如果对象处于激活状态，则进行绘制
        if self.active:
            # 计算屏幕保护程序的水平偏移量
            x_offset = 0

            sqrect = self.square.rect
            if (get_current_time() - 0.25) < self.square.last_bounce_time:
                # 计算插值值以增强动画效果
                lerp = abs((get_current_time() - 0.25) - self.square.last_bounce_time) * 5
                lerp = lerp ** 2  # 平方插值值以增强动画效果
                if self.square.latest_bounce_direction:
                    # 根据方向调整方块大小
                    sqrect.inflate_ip((lerp * 5, -10 * lerp))
                else:
                    sqrect.inflate_ip((-10 * lerp, lerp * 5))

            # 绘制屏幕保护程序的背景
            pygame.draw.rect(screen, get_colors()["hallway"], self.screensaver_rect.move(-x_offset, 0))

            # 绘制粒子轨迹
            if Config.particle_trail:
                # 每2帧生成一个新的粒子
                if n_frames % 2 == 0:
                    new = Particle(self.square.pos, [0, 0], True)
                    new.color = get_colors()["background"]
                    new.delta = [randint(-10, 10)/20, randint(-10, 10)/20]
                    self.particles.append(new)

            # 绘制粒子
            for particle in self.particles:
                pygame.draw.rect(screen, particle.color, particle.rect)
            # 移除过期的粒子
            for remove_particle in [particle for particle in self.particles if particle.age()]:
                self.particles.remove(remove_particle)

            # 绘制方块
            self.square.draw(screen, sqrect.move(-x_offset, 0))
            # 处理方块的物理效果
            bounced = self.square.title_screen_physics(self.screensaver_rect.move(-x_offset, 0))
            # 如果发生反弹，则生成粒子效果
            if bounced:
                # 生成新的粒子效果
                latest_dir = self.square.latest_bounce_direction# 获取最近一次反弹的方向
                sd = self.square.dir.copy()
                sd[latest_dir] *= -1# 反转方向
                sd[1-latest_dir] = 0# 将方向设置为0
                sp = self.square.pos
                for _ in range(Config.particle_amount):
                    new = Particle([sp[0]+randint(-10, 10), sp[1]+randint(-10, 10)], sd)
                    # 创建一个新的粒子对象，并设置其位置、速度和颜色
                    self.particles.append(new)# 添加新的粒子到粒子列表中

        # 绘制标题文本
        title_surf_loc_rect = self.title_surf.get_rect(midtop=(Config.SCREEN_WIDTH*3/4, 60))
        self.title_surf.set_alpha(max(int(interpolate_fn(self.anim)*400-145), 0))
        screen.blit(self.title_surf, title_surf_loc_rect)

        # 绘制跑马灯文本
        time = pygame.time.get_ticks()
        cropped_marquee = pygame.Surface((self.title_surf.get_width(), self.marquee_surf.get_height()), pygame.SRCALPHA)
        draw_marquee_position = [self.title_surf.get_width()-time/5, 0]
        while draw_marquee_position[0] < -self.marquee_surf.get_width():
            draw_marquee_position[0] += self.marquee_surf.get_width()+self.title_surf.get_width()+10
        cropped_marquee.blit(self.marquee_surf, draw_marquee_position)
        cropped_marquee.set_alpha(max(int(interpolate_fn(self.anim)*400-145), 0))
        screen.blit(cropped_marquee, cropped_marquee.get_rect(topleft=title_surf_loc_rect.bottomleft))

        # 绘制菜单选项
        for index, option in enumerate(self.menu_options):
            y_value = index * (option.HEIGHT + option.SPACING) + 250
            # 如果完全激活，则更新悬停状态
            if self.anim == 1:
                option.update_hover(y_value)

            # 绘制选项
            x_movement = interpolate_fn(1 - self.anim) * 60

            rect = option.get_rect(y_value).move(x_movement, 0)
            option.surface.set_alpha(int(interpolate_fn(self.anim)*255))
            screen.blit(option.surface, rect)

            # 处理悬停声音效果
            new_hover = rect.collidepoint(pygame.mouse.get_pos())
            if new_hover and not option.before_hover:
                play_sound("wood.wav")
            option.before_hover = new_hover

        # 绘制国旗选择器
        current_flag = self.flags[Config.language]
        cfrect = current_flag.get_rect(bottomright=(Config.SCREEN_WIDTH-100, Config.SCREEN_HEIGHT-30))
        screen.blit(current_flag, cfrect)
        left_arrow = get_font(72, "poppins-regular.ttf").render("<", True, get_colors()["hallway"])
        right_arrow = get_font(72, "poppins-regular.ttf").render(">", True, get_colors()["hallway"])
        self.left_lang_rect = left_arrow.get_rect(midright=cfrect.midleft).move(-5, 5)
        screen.blit(left_arrow, self.left_lang_rect)
        self.right_lang_rect = right_arrow.get_rect(midleft=cfrect.midright).move(5, 5)
        screen.blit(right_arrow, self.right_lang_rect)
        if self.requires_restart_surf is not None:
            screen.blit(self.requires_restart_surf, self.requires_restart_surf.get_rect(midbottom=cfrect.midtop).move(0, -10))

    def handle_event(self, event: pygame.event.Event):
        # 如果菜单未激活，直接返回
        if not self.active:
            return
        # 遍历菜单选项
        for index, option in enumerate(self.menu_options):
            # 计算当前选项的矩形位置
            rect = option.get_rect(index * (option.HEIGHT + option.SPACING) + 250)
            # 检查事件类型是否为鼠标按下且左键点击，并且点击位置在当前选项的矩形内
            # 或者事件类型为键盘按下且按键为对应选项的数字键
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and rect.collidepoint(
                    pygame.mouse.get_pos())) \
                    or (event.type == pygame.KEYDOWN and event.key == 49 + index):
                # 播放选择音效
                play_sound("select.mp3")
                # 返回当前选项的ID
                return option.id
        # 检查事件类型是否为鼠标按下
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 检查鼠标按键是否为左键、中键或右键
            if event.button in (1, 2, 3):
                # 为了更多的乐趣（目标训练迷你游戏！？！？疯狂）
                if self.square.rect.inflate(20, 20).collidepoint(pygame.mouse.get_pos()):
                    play_sound("wood.wav", 1)
                    self.square.dir[randint(0, 1)] *= -1
                # 处理右箭头点击
                if self.right_lang_rect.inflate(10, 10).collidepoint(pygame.mouse.get_pos()):
                    play_sound("wood.wav", 1)
                    languages = list(TRANSLATIONS.keys())
                    Config.language = languages[(languages.index(Config.language)+1) % len(languages)]
                    self.requires_restart_surf = get_font(18).render(lang_key('restart-required'), True, get_colors()["hallway"])
                # 处理左箭头点击
                if self.left_lang_rect.inflate(10, 10).collidepoint(pygame.mouse.get_pos()):
                    play_sound("wood.wav", 1)
                    languages = list(TRANSLATIONS.keys())
                    Config.language = languages[(languages.index(Config.language)-1) % len(languages)]
                    self.requires_restart_surf = get_font(18).render(lang_key('restart-required'), True, get_colors()["hallway"])
