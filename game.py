from utils import *
import pygame
from world import World
import random
from camera import Camera
from keystrokes import Keystrokes
from particle import Particle
from zipfile import ZipFile


class Game:
    def __init__(self):
        # 初始化对象的属性
        # 设置活动状态为False
        self.active = False
        # 初始化一个空列表用于存储笔记
        self.notes = []
        # 创建一个Camera对象
        self.camera = Camera()
        # 创建一个World对象
        self.world = World()
        # 初始化一个空列表用于存储安全区域，类型为pygame.Rect
        self.safe_areas: list[pygame.Rect] = []
        # 渲染一个文本对象，用于显示手动相机控制激活状态，字体大小为24，颜色为绿色
        self.camera_ctrl_text = get_font(24).render("Manual Camera Control Activated", True, (0, 255, 0))
        # 设置音乐是否已经播放过的标志为False
        self.music_has_played = False
        # 设置偏移是否已经发生的标志为False
        self.offset_happened = False
        # 渲染一个文本对象，用于显示加载状态，字体大小为24，颜色为白色
        self.loading_text = get_font(24).render("Loading...", True, (255, 255, 255))
        # 创建一个Keystrokes对象，用于处理按键输入
        self.keystrokes = Keystrokes()
        # 初始化未击中的次数为0
        self.misses = 0
        # 设置鼠标按下状态为False
        self.mouse_down = False
        # 初始化一个空列表用于存储被击中的矩形区域
        self.hitted_rectangles = []                           

    def start_song(self, screen: pygame.Surface):
        # 使用 Config 中的种子值设置随机数种子，确保随机操作的结果可重复
        random.seed(Config.seed)

        # 加载歌曲和音符信息 #  使用 Config 中的种子值设置随机数种子，确保随机操作的结果可重复
        with ZipFile(Config.current_song.fp) as zf:
            if Config.current_song.fp.lower().endswith(".osz"): #  使用 ZipFile 打开当前歌曲的文件路径
                # 如果文件是 .osz 格式（OSU! 歌曲包），读取 osu 文件中的音符数据
                notes = read_osu_file(filedata=zf.read(Config.current_song.song_file_name))
            else:
                # 对于其他格式的压缩文件，直接读取 MIDI 文件中的音符数据
                with zf.open(Config.current_song.song_file_name) as f:
                    notes = read_midi_file(file=f)
        # 将音符数据转换为列表并赋值给 self.notes
        notes = [note for note in notes]
        self.notes = notes

        # 其他设置

        self.world = World() #  初始化游戏世界
        self.music_has_played = False #  初始化音乐播放状态为未播放
        self.offset_happened = False #  初始化偏移状态为未发生
        self.camera.lock_type = CameraFollow(Config.camera_mode) #  设置相机跟随模式
        screen.fill(get_colors()["background"]) #  使用背景颜色填充整个屏幕
        information_texts = [ #  使用背景颜色填充整个屏幕
            "Map loading stuck at some percentage? Try changing the \"Square speed\" in the config",
            "Also try changing the \"Change dir chance\" and the \"Bounce min spacing\"",
            "",
            "Too large maps will crash the program, so try with some smaller ones first",
            "",
            "Don't want to play the game? Turn on \"Theatre mode\" in the config",
            "",
            "Music off-sync? Change the \"Music offset\" in the settings"
        ]
        for index, info_text in enumerate(information_texts): #  遍历信息文本列表，逐行渲染并绘制到屏幕上
            rendered_text = get_font(24).render(info_text, True, get_colors()["hallway"]) #  渲染文本，使用24号字体，颜色为"hallway"
            screen.blit(rendered_text, (50, 200 + 30 * index))
        pygame.display.flip() #  更新屏幕显示

        def update_loading_screen(message: str):
            # 使用背景颜色填充屏幕的矩形区域，从(0, 0)开始，宽度为Config.SCREEN_WIDTH，高度为100
            screen.fill(get_colors()["background"], pygame.Rect(0, 0, Config.SCREEN_WIDTH, 100))
            # 渲染文本消息，使用60号字体，颜色为"hallway"，并将其绘制在屏幕的(10, 10)位置
            screen.blit(get_font(60).render(message, True, get_colors()["hallway"]), (10, 10))
            # 遍历所有pygame事件
            for event in pygame.event.get():
                # 检查事件类型是否为键盘按下
                if event.type == pygame.KEYDOWN:
                    # 如果按下的是ESC键，则返回1
                    if event.key == pygame.K_ESCAPE:
                        return 1
            # 更新屏幕显示，使用Config中的screen对象、glsl_program和render_object
            update_screen(Config.screen, Config.glsl_program, Config.render_object)

        try:
            # 生成未来的反弹区域
            self.safe_areas = self.world.gen_future_bounces(self.notes, update_loading_screen)
            # 修复重叠区域
            self.safe_areas = fix_overlap(self.safe_areas, update_loading_screen)
        except UserCancelsLoadingError:
            # 用户取消加载
            return True
        except MapLoadingFailureError as e:
            # 地图加载失败
            return e.args[0] if len(e.args) else "Big error... can't load map :("
        # 设置世界开始时间
        self.world.start_time = get_current_time()
        # 初始化方块方向
        self.world.square.dir = [0, 0]
        # 设置方块初始位置为第一个反弹位置
        self.world.square.pos = self.world.future_bounces[0].square_pos

    def draw(self, screen: pygame.Surface, n_frames: int):

        # 检查游戏是否处于活动状态，如果不是则直接返回
        if not self.active:
            return

        # 检查音乐是否已经播放过
        if not self.music_has_played:
            # 如果音乐偏移尚未发生，调整未来弹跳的时间
            if not self.offset_happened:
                for bnc_change in self.world.future_bounces:
                    bnc_change.time += Config.start_playing_delay / 1000
            self.offset_happened = True
            # 检查是否已经过了开始播放音乐的延迟时间
            if self.world.time-Config.current_song.music_offset/1000 > Config.start_playing_delay/1000:
                self.music_has_played = True
                # 记录音乐加载前的时间
                song_load_before = get_current_time()
                # 播放音乐
                pygame.mixer.music.play()
                # 调整未来弹跳的时间以补偿音乐加载时间
                for bnc_change in self.world.future_bounces:
                    bnc_change.time += (get_current_time()-song_load_before)/1000

        # 获取屏幕的矩形区域
        screen_rect = screen.get_rect()

        # 设置世界时间
        self.world.update_time()

        # 移动摄像机（仅在未锁定方块时生效）
        self.camera.attempt_movement()

        # 处理方块弹跳
        self.world.handle_bouncing(self.world.square)

        # 移动方块
        self.world.square.reg_move()

        # 如果摄像机锁定在方块上，则将方块保持在摄像机中心
        if self.camera.locked_on_square:
            self.camera.follow(self.world.square)

        # 弹跳动画
        sqrect = self.camera.offset(self.world.square.rect)
        if (self.world.time - 0.25) + Config.music_offset / 1000 < self.world.square.last_bounce_time:
            lerp = abs((self.world.time - 0.25 + Config.music_offset / 1000) - self.world.square.last_bounce_time) * 5
            lerp = lerp ** 2  # 为了更好的插值效果调整矩形大小
            if self.world.square.latest_bounce_direction:
                sqrect.inflate_ip((lerp * 5, -10 * lerp))
            else:
                sqrect.inflate_ip((-10 * lerp, lerp * 5))

        # 安全区域处理
        total_rects = 0
        for safe_area in self.safe_areas:
            offsetted = self.camera.offset(safe_area)
            if screen_rect.colliderect(offsetted):
                total_rects += 1
                pygame.draw.rect(screen, get_colors()["hallway"], offsetted)

        # 绘制 pegs（固定点）
        for i, bounce_rect in enumerate(self.world.rectangles):
            offsetted = self.camera.offset(bounce_rect)

            if offsetted.colliderect(screen_rect):
                total_rects += 1
                if Config.do_color_bounce_pegs and self.world.collision_times[i] < (self.world.time * 1000 + Config.music_offset - Config.start_playing_delay)/1000:
                    pygame.draw.rect(screen, self.world.colors[i], offsetted)
                else:
                    pygame.draw.rect(screen, get_colors()["background"], offsetted)

        # 粒子效果
        for particle in self.world.particles:
            # 绘制每个粒子
            pygame.draw.rect(screen, particle.color, self.camera.offset(particle.rect))
        # 移除老化（寿命结束）的粒子
        for remove_particle in [particle for particle in self.world.particles if particle.age()]:
            self.world.particles.remove(remove_particle)

        # 游戏中的粒子轨迹
        if Config.particle_trail:
            # 每两帧添加一个粒子
            if not self.world.square.died:
                if n_frames % 2 == 0:
                    new = Particle(self.world.square.pos, [0, 0], True)
                    new.delta = [random.randint(-10, 10)/20, random.randint(-10, 10)/20]
                    self.world.particles.append(new)
                
        # 分数统计绘制
        time_from_start = self.world.time - Config.start_playing_delay / 1000 + Config.music_offset / 1000
        if not Config.theatre_mode:
            # 绘制分数统计信息
            self.misses = self.world.scorekeeper.draw(
                screen, 
                time_from_start if len(self.world.future_bounces) else -1, 
                self.misses
            )

            # 击中图标处理
            to_remove = []
            for hiticon in self.world.scorekeeper.hit_icons:
                if hiticon.draw(screen, self.camera):
                    to_remove.append(hiticon)
            for remove in to_remove:
                self.world.scorekeeper.hit_icons.remove(remove)

            # 处理游戏失败逻辑
            if self.world.scorekeeper.hp <= 0 and not self.world.square.died:
                self.world.square.died = True
                self.world.square.dir = [0, 0]
                pygame.mixer.music.stop()
                play_sound("death.mp3", 0.5)
                self.world.future_bounces = []
                for _ in range(100):
                    self.world.particles.append(Particle(self.world.square.pos, [random.randint(-3, 3), random.randint(-3, 3)]))
            if self.world.square.died:
                self.world.scorekeeper.hp = 0

        # 绘制方块
        self.world.square.draw(screen, sqrect)

        if not Config.theatre_mode:
            # 绘制按键提示
            self.keystrokes.draw(screen)

        # 开始倒计时
            if time_from_start < 0:
            # 如果游戏还未开始，显示倒计时时间
                repr_time = f"{abs(int((time_from_start+0.065)*10)/10)}s"
                countdown_surface = get_font(36).render(repr_time, True, (255, 255, 255))
                screen.blit(countdown_surface, countdown_surface.get_rect(center=(Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 4)))
            if time_from_start < 0.5:                
            # 在游戏即将开始时显示 "0.0s" 并逐渐淡出
                repr_zero = f"0.0s"
                countdown_surface = get_font(36).render(repr_zero, True, (255, 255, 255))
                countdown_surface.set_alpha((0.5 - time_from_start) * 2 * 255)
                screen.blit(countdown_surface, countdown_surface.get_rect(center=(Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 4)))

        # 处理鼠标点击事件（因为 self.handle_event 不会处理鼠标点击）
        if pygame.mouse.get_pressed()[0]:
            if not self.mouse_down:
                self.misses = self.world.handle_keypress(time_from_start, self.misses)
                self.mouse_down = True
        else:
            if self.mouse_down:
                self.mouse_down = False
        
        # 绘制准确率
        try:
            # 计算已经发生的弹跳次数
            n_bounces = len(self.world.past_bounces)
            # 计算总的弹跳次数（包括未来的弹跳）
            n_total_bounces = len(self.world.past_bounces) + len(self.world.future_bounces)

            # 如果已经有弹跳发生，则计算准确率
            if n_bounces > 0:
                # 获取当前的miss次数
                n_misses = self.misses

                # 计算当前准确率（已完成的弹跳）
                acc = round((n_bounces - n_misses) / n_bounces * 100, 2)
                # 计算总准确率（包括未来的弹跳）
                acct = round((n_total_bounces - n_misses) / n_total_bounces * 100, 2)

                # 将准确率限制在 0-100 之间
                acc = max(0, min(100, acc))
                acct = max(0, min(100, acct))

                # 渲染准确率文本
                acc_text = get_font(24).render(f"Accuracy: {acc}%", True, (255, 255, 255))
                acct_text = get_font(24).render(f"Total Accuracy: {acct}%", True, (255, 255, 255))

                # 确定准确率文本的位置
                topleft1 = self.world.scorekeeper.life_bar_rect.move(0, 10).bottomleft

                # 将准确率文本绘制到屏幕上
                screen.blit(acc_text, acc_text.get_rect(topleft=topleft1))
                screen.blit(acct_text, acct_text.get_rect(topleft=acc_text.get_rect(topleft=topleft1).move(0, 10).bottomleft))

        except ZeroDivisionError:
            # 忽略除零错误（当没有弹跳发生时可能会出现）
            pass
        except Exception:
            # 忽略其他所有异常（确保程序不会因未预见的错误而崩溃）
            pass

        # 失败信息
        if self.world.square.died:
            # 计算准确率
            n_bounces = len(self.world.past_bounces)
            n_total_bounces = len(self.world.past_bounces) + len(self.world.future_bounces)
            # 将弹跳次数限制在 1 到无穷大之间
            n_bounces = max(1, n_bounces)
            n_total_bounces = max(1, n_total_bounces)
            n_misses = self.misses

            acc = round((n_bounces - n_misses) / n_bounces * 100, 2)
            acct = round((n_total_bounces - n_misses) / n_total_bounces * 100, 2)

            # 将准确率限制在 0-100 之间
            acc = max(0, min(100, acc))
            acct = max(0, min(100, acct))

            # 渲染“按 ESC 键返回。”文本
            try_again_text = get_font(36).render("按 ESC 键返回。", True, (255, 255, 255))
            
            # 渲染当前准确率文本
            acc_text = get_font(36).render(f"Accuracy: {acc}%", True, (255, 255, 255))
            
            # 渲染总准确率文本
            acct_text = get_font(36).render(f"Total Accuracy: {acct}%", True, (255, 255, 255))
            
            # 将“按 ESC 键返回。”文本绘制到屏幕中央上方
            screen.blit(try_again_text, try_again_text.get_rect(center=(Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 4)))
            
            # 将当前准确率文本绘制到“按 ESC 键返回。”文本下方50像素处
            screen.blit(acc_text, acc_text.get_rect(center=(Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 4 + 50)))
            
            # 将总准确率文本绘制到当前准确率文本下方50像素处
            screen.blit(acct_text, acct_text.get_rect(center=(Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 4 + 100)))
            # 如果摄像机未锁定在方块上，绘制摄像机控制提示
            if not self.camera.locked_on_square:
                screen.blit(self.camera_ctrl_text, (10, 10))

    def handle_event(self, event: pygame.event.Event):
        # 检查当前对象是否处于激活状态，如果未激活则直接返回 False
        if not self.active:
            return False

        # 检查事件类型是否为键盘按下事件
        if event.type == pygame.KEYDOWN:
            # 如果按下的键是 ESC键，则返回 True，可能用于退出当前状态或关闭窗口
            if event.key == pygame.K_ESCAPE:
                return True
            # 如果按下的键是 TAB 键，则切换摄像头的锁定状态
            if event.key == pygame.K_TAB:
                self.camera.locked_on_square = not self.camera.locked_on_square
            # 如果当前不是剧院模式
            if not Config.theatre_mode:
                # 如果摄像头处于锁定状态
                if self.camera.locked_on_square:
                    # 计算从开始到当前的时间，加上音乐偏移量
                    time_from_start = self.world.time - Config.start_playing_delay / 1000 + Config.music_offset / 1000
                    # 如果时间小于 -0.2 秒，则直接返回，不处理按键
                    if time_from_start < -0.2:
                        return
                    # 定义允许的按键集合，包括空格键和方向键
                    arrows_n_space = (pygame.K_SPACE, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN)

                    if 97 + 26 > event.key >= 97 or event.key in arrows_n_space:  # 按下 a-z 键或空格键或方向键
                        self.misses = self.world.handle_keypress(time_from_start, self.misses)