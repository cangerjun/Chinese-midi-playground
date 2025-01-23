from utils import *
import pygame


class Keystrokes:
    def __init__(self):
        # 初始化按键列表
        self.keys: list[str] = []
        # 初始化按键表面字典
        self.key_surfaces: dict[str, pygame.Surface] = {}
        # 遍历ASCII码范围97到122（对应字母a到z）
        for ascii_keycode in range(97, 123):
            # 将每个字母渲染为Surface对象并存储在字典中
            self.key_surfaces[ascii_keycode] = get_font(36).render(
                chr(ascii_keycode), True, (0, 0, 0)
            )
        # 初始化按键码列表，包括字母键和方向键
        self.keycodes = list(range(97, 123)) + list(range(1073741903, 1073741907))
        # 加载方向键和鼠标点击的图标并存储在字典中
        self.key_surfaces[pygame.K_LEFT] = pygame.image.load("./assets/keystrokeicons/left.png").convert_alpha()
        self.key_surfaces[pygame.K_RIGHT] = pygame.image.load("./assets/keystrokeicons/right.png").convert_alpha()
        self.key_surfaces[pygame.K_DOWN] = pygame.image.load("./assets/keystrokeicons/down.png").convert_alpha()
        self.key_surfaces[pygame.K_UP] = pygame.image.load("./assets/keystrokeicons/up.png").convert_alpha()
        self.key_surfaces["click"] = pygame.image.load("./assets/keystrokeicons/click.png").convert_alpha()

    def draw(self, screen: pygame.Surface):
        # 设置默认矩形位置和大小
        default_rect = pygame.Rect(10, Config.SCREEN_HEIGHT - 60, 50, 50)
        # 遍历所有按键码
        for keycode in self.keycodes:
            # 检查当前按键是否被按下
            if pygame.key.get_pressed()[keycode]:
                # 如果按键被按下且不在列表中，则添加到列表
                if keycode not in self.keys:
                    self.keys.append(keycode)
            else:
                # 如果按键未被按下且在列表中，则从列表中移除
                if keycode in self.keys:
                    self.keys.remove(keycode)
        # 检查鼠标左键是否被按下
        if pygame.mouse.get_pressed()[0]:
            # 如果鼠标左键被按下且不在列表中，则添加到列表
            if "click" not in self.keys:
                self.keys.append("click")
        else:
            # 如果鼠标左键未被按下且在列表中，则从列表中移除
            if "click" in self.keys:
                self.keys.remove("click")

        # 遍历所有当前按下的按键
        for key in self.keys:
            # 绘制按键背景矩形
            pygame.draw.rect(screen, (0, 0, 0), default_rect)
            # 绘制按键背景矩形边框
            pygame.draw.rect(screen, (230, 233, 236), default_rect.inflate(-2, -2))
            # 将按键图标绘制到屏幕上
            screen.blit(self.key_surfaces[key], self.key_surfaces[key].get_rect(center=default_rect.center))
            # 更新矩形位置，为下一个按键做准备
            default_rect.x += 60
