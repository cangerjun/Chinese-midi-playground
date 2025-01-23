import moderngl
import pygame
from typing import Optional, Any
from json import load, dump
from os.path import isfile

pygame.init()


class Config:
    # constants
    rSCREEN_WIDTH = pygame.display.Info().current_w if pygame.display.Info().current_w else 1080
    rSCREEN_HEIGHT = pygame.display.Info().current_h if pygame.display.Info().current_h else 1920
    # 如果获取当前屏幕宽度失败，则默认为1080
    # 如果获取当前屏幕高度失败，则默认为1920
    CAMERA_SPEED = 500
    SQUARE_SIZE = 50
    PARTICLE_SPEED = 10

    # 颜色
    #
    # 每个颜色主题需要一个走廊颜色、一个背景颜色和至少一个方块颜色
    # 可选地，颜色主题可以提供一个 hp_bar_border 颜色（默认为 10, 9, 8），
    # 一个 hp_bar_background 颜色（默认为 34, 51, 59），以及一个
    # hp_bar_fill 颜色列表（默认为 (156, 198, 155), (189, 228, 168), (215, 242, 186)）
    #
    color_themes = {
        "dark_modern": {# 暗黑模式
            "hallway": pygame.Color(40, 44, 52),#走廊颜色为深灰色
            "background": pygame.Color(24, 26, 30),#背景颜色为深黑色
            "square": [# 正方形颜色
                pygame.Color(224, 26, 79),# 正方形颜色为红色
                pygame.Color(173, 247, 182),# 正方形颜色为绿色
                pygame.Color(249, 194, 46),# 正方形颜色为黄色
                pygame.Color(83, 179, 203)#    正方形颜色为蓝色
            ]
        },

        "dark": {# 暗黑模式
            "hallway": pygame.Color(214, 209, 205),#走廊颜色为白色
            "background": pygame.Color(60, 63, 65),#背景颜色为黑色
            "square": [
                pygame.Color(224, 26, 79),#正方形颜色为红色
                pygame.Color(173, 247, 182),#  正方形颜色为绿色
                pygame.Color(249, 194, 46),#正方形颜色为黄色
                pygame.Color(83, 179, 203)#    正方形颜色为蓝色
            ]
        },
        # credits to TheCodingCrafter for these themes
        # 感谢TheCodingCrafter提供的主题
        "light": {
            "hallway": pygame.Color(60, 63, 65),#走廊颜色为黑色
            "background": pygame.Color(214, 209, 205),#背景颜色为白色
            "square": [
                pygame.Color(224, 26, 79),#正方形颜色为红色
                pygame.Color(173, 247, 182),#  正方形颜色为绿色
                pygame.Color(249, 194, 46),#正方形颜色为黄色
                pygame.Color(83, 179, 203)#    正方形颜色为蓝色
            ]
        },
        "rainbow": {#彩虹模式
            "hallway": pygame.Color((214, 209, 205)),#走廊颜色为白色
            "background": pygame.Color((60, 63, 65)),# 背景颜色为黑色
            "square": [
                pygame.Color(0, 0, 0)# 正方形颜色为黑色
            ]
        },
        "autumn": {
            "hallway": pygame.Color((252, 191, 73)),# 走廊颜色为橙色
            "background": pygame.Color((247, 127, 0)),# 背景颜色为橙色
            "square": [
                pygame.Color(224, 26, 79),# 正方形颜色为红色
                pygame.Color(173, 247, 182),#  正方形颜色为绿色
                pygame.Color(249, 194, 46),# 正方形颜色为黄色
                pygame.Color(83, 179, 203)#    正方形颜色为蓝色
            ]
        },
        "winter": {
            "hallway": pygame.Color((202, 240, 255)),
            "background": pygame.Color((0, 180, 216)),
            "square": [
                pygame.Color(224, 26, 79),
                pygame.Color(173, 247, 182),
                pygame.Color(249, 194, 46),
                pygame.Color(83, 179, 203)
            ]
        },
        "spring": {
            "hallway": pygame.Color((158, 240, 26)),
            "background": pygame.Color((112, 224, 0)),
            "square": [
                pygame.Color(224, 26, 79),
                pygame.Color(173, 247, 182),
                pygame.Color(249, 194, 46),
                pygame.Color(83, 179, 203)
            ]
        },
        "magenta": {
            "hallway": pygame.Color((239, 118, 116)),
            "background": pygame.Color((218, 52, 77)),
            "square": [
                pygame.Color(224, 26, 79),
                pygame.Color(173, 247, 182),
                pygame.Color(249, 194, 46),
                pygame.Color(83, 179, 203)
            ]
        },
        "monochromatic": {
            "hallway": pygame.Color((255, 255, 255)),
            "background": pygame.Color((0, 0, 0)),
            "square": [
                pygame.Color(80, 80, 80),
                pygame.Color(150, 150, 150),
                pygame.Color(100, 100, 100),
                pygame.Color(200, 200, 200)
            ]
        },
        "green-screen-hallway": {
            "hallway": pygame.Color(0, 255, 0),
            "background": pygame.Color(60, 63, 65),
            "square": [
                pygame.Color(224, 26, 79),
                pygame.Color(173, 247, 182),
                pygame.Color(249, 194, 46),
                pygame.Color(83, 179, 203)
            ]
        },
        "green-screen-background": {
            "hallway": pygame.Color(60, 63, 65),
            "background": pygame.Color(0, 255, 0),
            "square": [
                pygame.Color(224, 26, 79),
                pygame.Color(173, 247, 182),
                pygame.Color(249, 194, 46),
                pygame.Color(83, 179, 203)
            ]
        }
    }

    # 预期的可配置设置
    SCREEN_WIDTH = pygame.display.Info().current_w if pygame.display.Info().current_w else 1920
    SCREEN_HEIGHT = pygame.display.Info().current_h if pygame.display.Info().current_h else 1080

    theme: Optional[str] = "dark"  # 主题（默认为暗色）
    seed: Optional[int] = None  # 随机种子
    camera_mode: Optional[int] = 2  # 摄像头模式
    start_playing_delay = 3000  # 开始播放延迟（毫秒）
    max_notes: Optional[int] = None  # 最大音符数量
    bounce_min_spacing: Optional[float] = 30  # 弹跳最小间距（像素）
    square_speed: Optional[int] = 600  # 方块速度（像素/秒）
    volume: Optional[int] = 70  # 音量（0-100）
    music_offset: Optional[int] = 0  # 音乐偏移（毫秒）
    direction_change_chance: Optional[int] = 30  # 改变方向的概率（百分比）
    hp_drain_rate = 10  # 生命值消耗速率
    theatre_mode = True  # 剧院模式开关
    particle_trail = True  # 粒子尾迹开关
    shader_file_name = "none.glsl"  # 着色器文件名
    do_color_bounce_pegs = False  # 是否在弹跳时改变颜色
    do_particles_on_bounce = True  # 是否在弹跳时生成粒子

    # 当前不可配置的设置（暂时）
    backtrack_chance: Optional[float] = 0.02  # 回溯概率
    backtrack_amount: Optional[int] = 40  # 回溯量
    rainbow_speed: Optional[int] = 30  # 彩虹效果速度
    square_swipe_anim_speed: Optional[int] = 4  # 方块滑动动画速度
    particle_amount = 10  # 粒子数量
    language = "english"  # 语言

    # 其他随机内容
    current_song = None  # 当前歌曲
    ctx: moderngl.Context = None  # OpenGL 上下文
    glsl_program: moderngl.Program = None  # GLSL 程序
    render_object: moderngl.VertexArray = None  # 渲染对象
    screen: pygame.Surface = None  # Pygame 屏幕表面
    dt = 0.01  # 时间步长

    # ASCII 着色器
    ascii_tex: moderngl.Texture = None  # ASCII 纹理

    # 保存和加载的键
    save_attrs = ["theme", "seed", "camera_mode", "start_playing_delay", "max_notes", "bounce_min_spacing",
                  "square_speed", "volume", "music_offset", "direction_change_chance", "hp_drain_rate", "theatre_mode",
                  "particle_trail", "shader_file_name", "do_color_bounce_pegs", 
                  "do_particles_on_bounce", "language",
                  "SCREEN_WIDTH", "SCREEN_HEIGHT"]

    # 光晕效果，目前仅适用于 dark_modern 主题
    square_glow = True  # 方块光晕开关
    square_glow_duration = 0.8  # 方块光晕持续时间（秒）
    glow_intensity = 15  # 光晕强度（1-40）
    square_min_glow = 7  # 方块最小光晕强度
    border_color = pygame.Color(255, 255, 255)  # 边框颜色
    glow_color = pygame.Color(255, 255, 255)  # 光晕颜色


def get_colors():
    # 从Config对象中获取当前主题的颜色方案
    # 如果当前主题不存在于color_themes中，则返回默认的"dark"主题
    return Config.color_themes.get(Config.theme, "dark")  # 获取当前主题的颜色方案


def save_to_file(dat: Optional[dict[str, Any]] = None):
    # 如果没有提供数据，则使用 save_attrs 中的属性
    if dat is None:
        dat = {k: getattr(Config, k) for k in Config.save_attrs}  
        # 如果没有提供数据，则使用 save_attrs 中的属性
    with open("./assets/settings.json", "w") as f:
        dump(dat, f, indent=4)  # 将设置保存到 JSON 文件


def load_from_file():
    try:
        # 检查 settings.json 文件是否存在
        if isfile("./assets/settings.json"):
            # 打开 settings.json 文件以读取模式
            with open("./assets/settings.json", "r") as f:
                # 加载 JSON 文件中的数据
                data = load(f)
                # 遍历 JSON 数据中的每个设置项
                for setting in data:
                    # 将设置项的值赋给 Config 类的对应属性
                    setattr(Config, setting, data[setting])  # 从 JSON 文件加载设置
        else:
            # 如果文件不存在，则创建一个空文件
            with open("./assets/settings.json", "w") as f:
                f.write('{}')  # 如果文件不存在，则创建一个空文件
    except Exception as e:
        print(f"Error: {e}")  # 捕获并打印任何异常


if __name__ == "config":
    load_from_file()  # 如果模块名为 config，则加载设置