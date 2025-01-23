# 不检查未解析的引用
from typing import Union, Optional, BinaryIO
# 不检查未解析的引用
from errors import *
from config import Config, get_colors
from translations import TRANSLATIONS
# 不检查未解析的引用
from time import time as get_current_time
import moderngl
import mido
import pygame
from sys import platform
import subprocess
from enum import Enum
from os.path import join
from math import sin, pi
from sys import setrecursionlimit
setrecursionlimit(10000)  # 如果有更多音符，可以增加

# 如果在Windows上，使用垂直同步帧率，否则为60
if platform == "win32":
    try:
        # 不检查包要求
        import win32api
        FRAMERATE = win32api.EnumDisplaySettings(win32api.EnumDisplayDevices().DeviceName, -1).DisplayFrequency
    except ModuleNotFoundError:
        print("未找到win32api python模块！请使用\"pip install pywin32\"安装")
        FRAMERATE = 60
elif "linux" in platform:
    # 不检查包要求
    from Xlib import display
    # 不检查包要求
    from Xlib.ext import randr
    d = display.Display()
    default_screen = d.get_default_screen()
    info = d.screen(default_screen)

    resources = randr.get_screen_resources(info.root)
    active_modes = set()
    for crtc in resources.crtcs:
        crtc_info = randr.get_crtc_info(info.root, crtc, resources.config_timestamp)
        if crtc_info.mode:
            active_modes.add(crtc_info.mode)

    for mode in resources.modes:
        if mode.id in active_modes:
            FRAMERATE = round(mode.dot_clock / (mode.h_total * mode.v_total))
            break
else:
    FRAMERATE = 60


# 相机跟随模式
class CameraFollow(Enum):
    Center = 0  # 居中方形
    Lazy = 1  # 懒惰相机，Crazy Nutter 101使用
    Smoothed = 2  # 平滑相机，每帧在当前和前一帧之间稍微插值
    Predictive = 3  # 平滑相机，但你可以更好地看到方形将弹跳的位置


def read_osu_file(filedata: bytes):
    filedata = filedata.decode("utf-8")
    filelines = filedata.splitlines(False)
    started_counting = False
    timestamps = []
    for line in filelines:
        if not started_counting:
            if "HitObjects" in line:
                started_counting = True
            continue
        if len(line) < 3:
            continue
        args = line.split(",")
        if (int(args[3]) & 3) == 0:
            continue
        timestamps.append(int(args[2])/1000)
    return timestamps


def surf_to_texture(in_surface: pygame.Surface) -> moderngl.Texture:
    tex = Config.ctx.texture(in_surface.get_size(), 4)
    tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
    tex.swizzle = 'BGRA'
    tex.write(in_surface.get_view('1'))
    return tex


def update_screen(screen: pygame.Surface, glsl_program: moderngl.Program, render_object: moderngl.VertexArray):
    # 将pygame的Surface对象转换为OpenGL纹理对象
    frame_tex = surf_to_texture(screen)
    # 将纹理对象绑定到纹理单元0
    frame_tex.use(0)
    # 在GLSL程序中设置纹理采样器变量'tex'为纹理单元0
    glsl_program['tex'] = 0
    # 检查配置文件中的着色器文件名是否包含"ascii.glsl"
    if "ascii.glsl" in Config.shader_file_name:
        # 如果Config.ascii_tex为None，则加载ascii.png图片并转换为纹理对象
        if Config.ascii_tex is None:
            Config.ascii_tex = surf_to_texture(pygame.image.load('./assets/shaders/ascii.png').convert_alpha())
            # 将ascii纹理对象绑定到纹理单元1
            Config.ascii_tex.use(1)
        # 尝试在GLSL程序中设置纹理采样器变量'asciipng'为纹理单元1
        try:
            glsl_program['asciipng'] = 1
        except KeyError:
            # 如果GLSL程序中没有'asciipng'变量，则忽略异常
            pass
    # 使用现代OpenGL的VertexArray对象进行渲染，模式为三角形带
    render_object.render(mode=moderngl.TRIANGLE_STRIP)

    pygame.display.flip()

    frame_tex.release()


def open_file(filename):
    # 检查当前操作系统平台
    if platform == "win32":
        # 如果是Windows系统，导入os模块中的startfile函数
        from os import startfile
        # 使用startfile函数打开文件
        startfile(filename)
    else:
        # 如果不是Windows系统，根据平台选择合适的打开命令
        opener = "open" if platform == "darwin" else "xdg-open"
        # 使用subprocess模块的call函数执行打开命令
        subprocess.call([opener, filename])


# 不检查未解析的引用
def read_midi_file(file):
    # 使用mido库加载MIDI文件
    midi_file = mido.MidiFile(file=file)

    # 初始化一个空列表用于存储音符的时间戳
    notes = []
    # 初始化当前时间为0
    current_time = 0

    # 遍历MIDI文件中的所有消息
    for msg in midi_file:
        # 检查消息类型是否为'note_on'且速度不为0（即音符开始）
        if msg.type == 'note_on' and msg.velocity != 0:
            # 计算当前音符的时间戳，单位为秒
            timestamp = current_time + msg.time
            # 将时间戳四舍五入到毫秒并添加到音符列表中
            notes.append(round(timestamp*1000)/1000)
        # 更新当前时间
        current_time += msg.time
    # 返回包含所有音符时间戳的列表
    return notes


# 删除相邻过近的值
def remove_too_close_values(lst: list[float], threshold=30) -> list[float]:
    """假设列表已排序"""
    new = []
    before = None
    for _ in lst:
        if before is None:
            before = _
            new.append(_)
            continue
        if before+threshold/1000 > _:
            continue
        before = _
        new.append(_)
    return new

def fix_overlap(rects: list[pygame.Rect], callback=None):
    # 如果没有提供回调函数，则使用一个空操作函数
    if callback is None:
        callback = lambda _: None
    # 初始化两个集合，用于存储所有矩形的左右边界和上下边界
    xvs = set()
    yvs = set()
    # 遍历所有矩形，将它们的左右边界和上下边界添加到集合中
    for rect in rects:
        xvs.add(rect.right)
        xvs.add(rect.left)
        yvs.add(rect.top)
        yvs.add(rect.bottom)
    # 将集合转换为排序后的列表
    xvs = sorted(list(xvs))
    yvs = sorted(list(yvs))

    # 初始化输出列表，用于存储最终合并后的矩形
    outputs = []
    # 遍历所有x和y的边界组合，生成最小矩形
    for xv1 in range(len(xvs)-1):
        xv2 = xv1+1
        for yv1 in range(len(yvs)-1):
            yv2 = yv1+1
            # 创建一个新的矩形
            r = pygame.Rect(xvs[xv1], yvs[yv1], xvs[xv2]-xvs[xv1], yvs[yv2]-yvs[yv1])
            # 如果该矩形与输入的矩形列表中的任何一个矩形重叠，则将其添加到输出列表中
            if r.collidelist(rects)+1:
                outputs.append(r)

        # 每处理完一个x边界组合，调用回调函数报告进度
        if callback(f"检查最小矩形 ({int(100*xv1*len(yvs)/(len(xvs)*len(yvs)))}% 完成)"):
            raise UserCancelsLoadingError()

    # 合并相邻的最小矩形
    callback("合并相邻的最小矩形")

    for ai in range(len(outputs)-1):
        a = outputs[ai+1]
        b = outputs[ai]
        # 跳过宽度或高度为0的矩形
        if a.width == 0 or a.height == 0 or b.width == 0 or b.height == 0:
            continue
        # 如果两个矩形不相邻，则跳过
        if not (a.right == b.left or a.left == b.right or a.top == b.bottom or b.bottom == a.top):
            continue
        # 如果两个矩形在x轴上对齐且宽度相同，则合并它们
        if a.x == b.x and a.width == b.width:
            a.y = min(a.y, b.y)
            a.height = a.height+b.height
            b.height = 0
            continue

    # 过滤掉宽度或高度为0的矩形
    outputs = [out for out in outputs if out.width > 0 and out.height > 0]

    # 按y坐标和x坐标排序矩形
    outputs.sort(key=lambda _: _.y*100000+_.x)

    for ai in range(len(outputs)-1):
        a = outputs[ai+1]
        b = outputs[ai]
        #过宽度或高度为0的矩形
        if a.width == 0 or a.height == 0 or b.width == 0 or b.height == 0:
            continue
        # 如果两个矩形不相邻，则跳过
        if not (a.right == b.left or a.left == b.right or a.top == b.bottom or b.bottom == a.top):
            continue
        # 如果两个矩形在y轴上对齐且高度相同，则合并它们
        if a.y == b.y and a.height == b.height:
            a.x = min(a.x, b.x)
            a.width = a.width+b.width
            b.width = 0
            continue

    callback("完成加载")

    return [out for out in outputs if out.width > 0 and out.height > 0]


_font_registry: dict[str, pygame.font.Font] = {}


def lang_key(key: str):
    """
    用于不同语言，这样每个人都能阅读文本。
    翻译在translations.py中找到
    """
    # 从TRANSLATIONS字典中获取英文翻译字典
    english_language = TRANSLATIONS["english"]
    # 从TRANSLATIONS字典中获取当前配置语言对应的翻译字典，如果不存在则返回空字典
    my_language = TRANSLATIONS.get(Config.language, {})
    # 检查英文翻译字典中是否存在给定的键
    if key not in english_language:
        # 如果不存在，打印警告信息
        print(f"警告：{key}还没有英文文本！！")
    # 返回当前配置语言对应的翻译，如果不存在则返回英文翻译，如果英文翻译也不存在则返回"<missing>"
    return my_language.get(key, english_language.get(key, "<missing>"))


def get_font(size: int = 24, font_file_name: str = None) -> pygame.font.Font:
    # 定义一个函数get_font，用于获取指定大小和字体的pygame字体对象
    # 参数size表示字体大小，默认值为24
    # 参数font_file_name表示字体文件名，默认值为None
    # 返回值为pygame.font.Font对象
    if font_file_name is None:
        # 如果font_file_name为None，则调用lang_key函数获取默认字体文件名
        font_file_name = lang_key("font")
    font_path = f'./assets/fonts/{font_file_name}'
    # 构建字体文件的路径，路径格式为'./assets/fonts/{font_file_name}'
    fn_id = f"[{font_path}/{size}]"
    # 构建字体标识符，格式为"[{font_path}/{size}]"，用于在字体注册表中唯一标识一个字体
    if fn_id not in _font_registry:
        # 如果字体标识符fn_id不在字体注册表_font_registry中
        try:
            # 尝试从指定路径加载字体文件，并创建pygame.font.Font对象
            _font_registry[fn_id] = pygame.font.Font(font_path, size)
        except FileNotFoundError:
            # 如果字体文件不存在，捕获FileNotFoundError异常
            print(f"字体 {fn_id} 未找到！")
            # 打印字体文件未找到的错误信息
            _font_registry[fn_id] = pygame.font.SysFont("Arial", size)
            # 使用系统默认字体Arial创建pygame.font.Font对象，并存储在字体注册表中
    return _font_registry[fn_id]


_channels = []
_sound_registry: dict[str, pygame.mixer.Sound] = {}


def play_sound(snd_name: str, vol: float = 0.5):
    # 检查当前是否有可用的音频通道，如果没有则初始化
    if len(_channels) == 0:
        # 设置pygame的音频通道数量为40
        pygame.mixer.set_num_channels(40)
        # 创建并添加20个音频通道到_channels列表中
        for _ in range(1, 20):
            _channels.append(pygame.mixer.Channel(_))

    # 检查声音文件是否已经在声音注册表中，如果没有则加载
    if snd_name not in _sound_registry:
        # 将声音文件加载到声音注册表中
        _sound_registry[snd_name] = pygame.mixer.Sound(join("assets", snd_name))

    # 查找一个空闲的音频通道
    chan = pygame.mixer.find_channel(False)
    # 如果没有找到空闲的音频通道，返回False
    if not chan:
        return False
    # 如果找到的音频通道正在播放，返回False
    if chan.get_busy():
        return False
    # 设置音频通道的音量为传入的vol参数
    chan.set_volume(vol)
    # 在音频通道中播放指定的声音文件
    chan.play(_sound_registry[snd_name])
    # 返回True表示播放成功
    return True


def interpolate_fn(n):
    # 定义一个函数interpolate_fn，用于计算插值函数
    # 参数n表示插值参数，取值范围在0到1之间
    # 返回值为一个函数，用于计算插值结果
    # 函数的计算公式为：
    # f(n) = 3n^2 - 2n^3
    return 3 * n ** 2 - 2 * n ** 3