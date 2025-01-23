from utils import *
import pygame
from hiticon import HitIcon, HitLevel


class Scorekeeper:
    def __init__(self, world):
        # 初始化Scorekeeper对象，传入world参数
        self.world = world
        self.unhit_notes: list[float] = []  # 存储未击中的音符的时间戳
        self.hit_icons: list[HitIcon] = []  # 存储击中音符的图标
        self.hp = 100  # 初始生命值为100
        self.shown_hp = 0  # 显示的生命值，用于平滑过渡

    @property
    def life_bar_rect(self):
        # 计算并返回生命条的位置和大小
        return pygame.Rect((10, 10, int(Config.SCREEN_WIDTH / 2 - 30), 30))

    def draw(self, screen: pygame.Surface, current_time: float, misses: int):

        # 绘制生命条
        self.hp = max(0, min(self.hp, 100))  # 限制生命值在0到100之间
        bg_color = get_colors().get("hp_bar_background", pygame.Color(34, 51, 59))
        border_color = get_colors().get("hp_bar_border", pygame.Color(10, 9, 8))
        fill_colors = get_colors().get("hp_bar_fill", (
            pygame.Color(156, 198, 155), pygame.Color(189, 228, 168), pygame.Color(215, 242, 186)
        ))
        screen.fill(border_color, self.life_bar_rect)  # 填充边框颜色
        inner = self.life_bar_rect.inflate(-8, -8)  # 计算内部区域
        screen.fill(bg_color, inner)  # 填充背景颜色
        bar_width = inner.width / len(fill_colors)  # 每个颜色段的宽度
        bar_hp_repr = 100 / len(fill_colors)  # 每个颜色段代表的生命值
        leftover = self.shown_hp
        for _ in range(len(fill_colors)):
            chunk_rect = inner.copy()
            chunk_rect.x = inner.x + bar_width * _
            width = min(max(leftover, 0), int(bar_hp_repr)+1)/bar_hp_repr*bar_width
            leftover -= bar_hp_repr
            chunk_rect.width = width
            screen.fill(fill_colors[_], chunk_rect)  # 填充颜色段
        if current_time > 0:
            self.hp -= Config.hp_drain_rate*Config.dt  # 每帧减少生命值
        hp_show_damping = 10
        self.shown_hp = self.shown_hp*(1-hp_show_damping*Config.dt)+self.hp*(hp_show_damping*Config.dt)  # 平滑过渡显示的生命值

        # 移除未击中的音符
        to_remove = []
        for timestamp in self.unhit_notes:
            if timestamp+0.12 < current_time:  # 120ms晚是未击中的音符
                self.hp -= 6
                self.hit_icons.append(HitIcon(HitLevel.miss, self.world.square.pos))
                to_remove.append(timestamp)
                misses = misses if misses is not None else 0
                misses += 1

        for t_remove in to_remove:
            self.unhit_notes.remove(t_remove)

        return misses

    def do_keypress(self, current_time: float, misses: int):
        # 负数最近表示提前击打，正数表示延迟击打
        for timestamp in self.unhit_notes:
            offset = current_time-timestamp
            if offset > 0.06:  # 60ms晚 - 120ms晚
                self.hit_icons.append(HitIcon(HitLevel.late, self.world.square.pos.copy()))
                self.hp -= 1
                misses += 1

            elif offset > -0.06:  # 60ms早 - 60ms晚
                self.hit_icons.append(HitIcon(HitLevel.perfect, self.world.square.pos.copy()))
                self.hp += 3

            elif offset > -0.09:  # 60ms早 - 90ms早
                self.hit_icons.append(HitIcon(HitLevel.good, self.world.square.pos.copy()))
                self.hp -= 1

            elif offset > -0.12:  # 90ms早 - 120ms早
                self.hit_icons.append(HitIcon(HitLevel.early, self.world.square.pos.copy()))
                self.hp -= 2
                misses += 1

            else:
                return misses
            self.unhit_notes.remove(timestamp)
            return misses
    
    def should_hit(self, current_time: float, blacklist: list):
        # 负数最近表示提前击打，正数表示延迟击打
        for timestamp in self.unhit_notes:
            offset = current_time-timestamp
            if timestamp in blacklist: continue
            if offset > 0.06:  # 60ms晚 - 120ms晚
                pass

            elif offset > -0.06:  # 60ms早 - 60ms晚
                blacklist.append(timestamp)
                return True, blacklist

            elif offset > -0.09:  # 60ms早 - 90ms早
                pass

            elif offset > -0.12:  # 90ms早 - 120ms早
                pass

            else:
                return False, blacklist
            
            return False, blacklist

