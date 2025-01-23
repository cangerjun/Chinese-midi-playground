from utils import *
from bounce import Bounce
from particle import Particle
from square import Square
from time import time as get_current_time
from scorekeeper import Scorekeeper
import random
import pygame


class World:
    """这是一个残酷的世界"""

    def __init__(self):
        # 初始化未来和过去反弹的列表
        self.future_bounces: list[Bounce] = []
        self.past_bounces: list[Bounce] = []
        # 初始化开始时间和当前时间
        self.start_time = 0
        self.time = 0
        # 初始化矩形列表、碰撞时间列表和粒子列表
        self.rectangles: list[pygame.Rect] = []
        self.collision_times: list[float] = []
        self.particles: list[Particle] = []
        # 初始化时间戳列表
        self.timestamps = []
        # 初始化方块对象
        self.square = Square()
        # 初始化计分器对象
        self.scorekeeper = Scorekeeper(self)
        # 初始化颜色列表
        self.colors = []           

    def update_time(self) -> None:
        # 更新当前时间
        self.time = get_current_time() - self.start_time

    def get_next_bounce(self) -> Bounce:
        """Also pops the bounce from the future_bounces list"""
        # 获取下一个反弹，并将其从未来反弹列表中移除，添加到过去反弹列表中
        self.past_bounces.append(self.future_bounces.pop(0))
        return self.past_bounces[-1]

    def add_bounce_particles(self, sp: list[float], sd: list[float]):
        # 添加反弹粒子
        for _ in range(Config.particle_amount):
            new = Particle([sp[0]+random.randint(-10, 10), sp[1]+random.randint(-10, 10)], sd)
            self.particles.append(new)

    def handle_bouncing(self, square: Square):
        # 处理反弹
        if len(self.future_bounces):
            if (self.time * 1000 + Config.music_offset)/1000 > self.future_bounces[0].time:
                current_bounce = self.get_next_bounce()
                before = square.dir.copy()
                square.obey_bounce(current_bounce)
                changed = square.dir.copy()
                for _ in range(2):
                    if before[_] == changed[_]:
                        changed[_] = 0
                    else:
                        changed[_] = -changed[_]
                if Config.do_particles_on_bounce:
                    self.add_bounce_particles(square.pos, changed)

                # 停止方块在终点
                if len(self.future_bounces) == 0:
                    square.dir = [0, 0]
                    square.pos = current_bounce.square_pos

    def handle_keypress(self, time_from_start, misses):
        # 处理按键按下
        return self.scorekeeper.do_keypress(time_from_start, misses)

    def gen_future_bounces(self, _start_notes: list[tuple[int, int, int]], percent_update_callback):
        """递归解决方案可能是必要的"""
        total_notes = len(_start_notes)
        max_percent = 0
        path = []
        safe_areas = []
        force_return = 0

        def recurs(
                square: Square,
                notes: list[float],
                bounces_so_far: list[Bounce] = None,
                prev_index_priority=None,
                t: float = 0,
                depth: int = 0
        ) -> Union[list[Bounce], bool]:
            nonlocal force_return, max_percent
            if prev_index_priority is None:
                prev_index_priority = [0, 1]
            if bounces_so_far is None:
                bounces_so_far = []
            gone_through_percent = (total_notes-len(notes)) * 100 // total_notes
            while gone_through_percent > max_percent:
                max_percent += 1
                if percent_update_callback(f"{max_percent}% done generating map"):
                    raise UserCancelsLoadingError()

            all_bounce_rects = [_bounc.get_collision_rect() for _bounc in bounces_so_far]
            if len(notes) == 0:
                return bounces_so_far
            # 路径段开始
            start_rect = square.rect.copy()
            while True:
                t += 1/FRAMERATE
                square.reg_move(False)
                path.append(square.rect)
                if t > notes[0]:
                    # 没有碰撞（一切正常）
                    bounce_indexes = prev_index_priority

                    # 随机改变方向
                    if random.random() * 100 < Config.direction_change_chance:
                        bounce_indexes = list(bounce_indexes.__reversed__())

                    # 添加安全区域
                    safe_areas.append(start_rect.union(square.rect))

                    for direction_to_bounce in bounce_indexes:
                        square.dir[direction_to_bounce] *= -1
                        bounces_so_far.append(Bounce(square.pos, square.dir, t, direction_to_bounce))

                        toextend = recurs(
                            square=square.copy(),
                            notes=notes[1:],
                            bounces_so_far=[_b.copy() for _b in bounces_so_far],
                            t=t,
                            prev_index_priority=bounce_indexes.copy(),
                            depth=depth+1
                        )

                        if toextend:
                            return toextend
                        else:
                            bounces_so_far = bounces_so_far[:-1]
                            square.dir[direction_to_bounce] *= -1

                            # 退回到上一个路径段，尝试其他路径
                            if force_return:
                                force_return -= 1
                                while len(path) != path_segment_start:
                                    path.pop()
                                return False

                            continue
                    while len(path) != path_segment_start:
                        path.pop()
                    return False

                othercheck = False
                if len(bounces_so_far):
                    othercheck = bounces_so_far[-1].get_collision_rect().collidelist(path[:-10])+1

                if square.rect.collidelist(all_bounce_rects) != -1 or othercheck:
                    if depth > 200:
                        if random.random() < Config.backtrack_chance:
                            max_percent -= (Config.backtrack_amount * 100 // total_notes) + 1
                            force_return = Config.backtrack_amount

                    while len(path) != path_segment_start:
                        path.pop()
                    return False

        _start_notes = _start_notes[:Config.max_notes] if Config.max_notes is not None else _start_notes

        self.scorekeeper.unhit_notes = remove_too_close_values([_sn for _sn in _start_notes], Config.bounce_min_spacing)

        self.future_bounces = recurs(
            square=self.square.copy(),
            notes=remove_too_close_values(
                [_sn for _sn in _start_notes],
                threshold=Config.bounce_min_spacing
            )
        )

        if self.future_bounces is False:
            raise MapLoadingFailureError("The map failed to generate because of the recursion function. " +
                                         "If the midi has too many notes too close, it may not generate. " +
                                         "Maybe try changing the \"bounce min spacing\", \"square speed\" or \"change dir chance\" in the config")

        if len(self.future_bounces) == 0:
            raise MapLoadingFailureError("Map safearea list empty. Please report to the github under the issues tab")

        percent_update_callback("Removing overlapping safe areas")

        # 消除完全重叠的安全区域
        safe_areas: list[pygame.Rect]
        while True:
            new = []
            before_safe_count = len(safe_areas)
            for safe1 in safe_areas:
                for safe2 in safe_areas:
                    if safe2 == safe1:
                        continue
                    if safe2.contains(safe1):
                        break
                else:
                    new.append(safe1)
            safe_areas = new.copy()
            after_safe_count = len(safe_areas)
            if after_safe_count == before_safe_count:
                break
        safe_areas = safe_areas

        self.rectangles = [_fb.get_collision_rect() for _fb in self.future_bounces]
        self.collision_times = [_fb.time for _fb in self.future_bounces]
        
        # 为生成的障碍设置随机颜色
        self.colors = [random.choice([(224, 50, 50), (80, 210, 100), (230, 220, 50), (174, 170, 210), (245, 77, 247), (255, 153, 0)]) for _ in self.future_bounces]
        return safe_areas
