from utils import *
from os import listdir
from os.path import isfile, join
from zipfile import ZipFile
from typing import Any
from io import BytesIO
from json import loads
import pygame


class Song:
    def __init__(self, name: str, song_artist: str, mapper: str,
                 song_file: str, audio_file: str, version: int = -1, filepath: Optional[str] = None,
                 is_from_osu_file: bool = False):

        # 初始化歌曲对象
        self.is_from_osu_file = is_from_osu_file  # 是否从osu文件加载
        self.song_file_name: str = song_file  # 歌曲文件名
        self.audio_file_name: str = audio_file if audio_file is not None else self.song_file_name  # 音频文件名，如果没有则使用歌曲文件名
        self.mapper = mapper  # 地图作者
        self.fp = filepath  # 文件路径
        self.song_artist = song_artist  # 歌曲艺术家
        self.name = name  # 歌曲名称
        self.version = version  # metadata格式版本，不是地图版本
        self.music_offset = 0  # 放置代表毫秒的整数，负数表示音乐在前面

        # 初始化动画和颜色
        self.anim = 0
        col = pygame.Color(229, 97, 196)
        selected_col = pygame.Color(50, 203, 255)

        # 创建歌曲项的矩形区域
        reset_rect = pygame.Rect((0, 0, int(Config.SCREEN_WIDTH / 2), SongSelector.ITEM_HEIGHT))

        # 创建歌曲项的表面
        self.surface: pygame.Surface = pygame.Surface((int(Config.SCREEN_WIDTH / 2), SongSelector.ITEM_HEIGHT), pygame.SRCALPHA)
        self.selected_surface: pygame.Surface = pygame.Surface((int(Config.SCREEN_WIDTH / 2), SongSelector.ITEM_HEIGHT), pygame.SRCALPHA)

        # 创建覆盖表面
        overlay_surf = pygame.Surface((int(Config.SCREEN_WIDTH / 2), SongSelector.ITEM_HEIGHT), pygame.SRCALPHA)

        # 绘制歌曲项的背景和边框
        pygame.draw.rect(self.surface, col.lerp((0, 0, 0), 0.4), reset_rect, border_radius=6)
        pygame.draw.rect(self.surface, col, reset_rect.inflate(-8, -8), border_radius=2)
        pygame.draw.rect(self.selected_surface, selected_col.lerp((0, 0, 0), 0.4), reset_rect, border_radius=6)
        pygame.draw.rect(self.selected_surface, selected_col, reset_rect.inflate(-8, -8), border_radius=2)

        # 渲染歌曲名称
        title_surface: pygame.Surface = get_font(36).render(self.name, True, (0, 0, 6))
        overlay_surf.blit(title_surface, title_surface.get_rect(topright=overlay_surf.get_rect().topright).move(-20, 20))

        # 渲染歌曲详情
        if not is_from_osu_file:
            details_surface: pygame.Surface = get_font(
                24).render(f"歌曲由 {self.song_artist} 提供 | 地图由 {self.mapper} 制作", True, (0, 0, 0))
        else:
            details_surface: pygame.Surface = get_font(24).render(f"警告：实验性功能！！！", True, (0, 0, 0))
        overlay_surf.blit(details_surface, details_surface.get_rect(bottomright=overlay_surf.get_rect().bottomright).move(-20, -20))

        # 将覆盖表面应用到歌曲项表面
        self.surface.blit(overlay_surf, (0, 0))
        self.selected_surface.blit(overlay_surf, (0, 0))

        # 初始化鼠标悬停状态
        self.before_hover = False

    def __repr__(self):
        # 定义对象的字符串表示方法，通常用于调试和日志记录
        # 返回一个格式化的字符串，包含对象的属性信息
        return f"<Song({self.song_file_name}, audio={self.audio_file_name})>"


def song_from_osu_file(contents: str, songfilepath: str, zipfilepath: str) -> Song:
    # 初始化变量，用于存储从osu文件中提取的信息
    audio_name = ""
    name = ""
    artist = ""
    mapper = ""

    # 遍历osu文件内容的每一行
    for line in contents.splitlines(False):
        # 如果行以"AudioFilename: "开头，提取音频文件名
        if line.startswith("AudioFilename: "):
            audio_name = line.removeprefix("AudioFilename: ")
        # 如果行以"Title:"开头，提取歌曲名称并去除前导空格
        if line.startswith("Title:"):
            name = line.removeprefix("Title:").lstrip()
        # 如果行以"Artist:"开头，提取艺术家名称并去除前导空格
        if line.startswith("Artist:"):
            artist = line.removeprefix("Artist:").lstrip()
        # 如果行以"Creator:"开头，提取地图制作者名称并去除前导空格
        if line.startswith("Creator:"):
            mapper = line.removeprefix("Creator:").lstrip()
        # 如果行以"Version:"开头，将版本信息添加到地图制作者名称后面
        if line.startswith("Version:"):
            # janky asf but whatever
            mapper += f' | {line.removeprefix("Version:").lstrip()}'

    # 返回一个Song对象，包含提取的信息和传入的文件路径
    return Song(
        name=name, song_artist=artist, mapper=mapper,
        song_file=songfilepath, audio_file=audio_name,
        version=-2, filepath=zipfilepath, is_from_osu_file=True
    )


def make_songs_from_osz(fpath: str) -> list[Song]:
    # 初始化一个空列表，用于存储解析后的歌曲对象
    songs = []
    # 使用ZipFile类打开指定路径的osz文件
    with ZipFile(fpath) as zf:
        # 获取osz文件中的所有文件信息列表
        files = zf.filelist
        # 遍历文件信息列表
        for fileinfo in files:
            # 检查文件名是否以".osu"结尾，即判断是否为osu地图文件
            if fileinfo.filename.endswith(".osu"):
                songs.append(song_from_osu_file(zf.read(fileinfo.filename).decode('utf-8'), fileinfo.filename, fpath))
    return songs


def make_song_from_zip(fpath: str) -> Song:
    # 打开指定路径的zip文件
    with ZipFile(fpath) as zf:
        # 获取zip文件中名为"metadata.json"的文件信息
        metadata_info = zf.getinfo("metadata.json")
        # 读取"metadata.json"文件内容并解析为字典
        metadata: dict[str, Any] = loads(zf.read(metadata_info))
        # 检查metadata中是否包含"name"键，若不存在则抛出异常
        if "name" not in metadata:
            raise InvalidSongError(f"No name in metadata of {fpath}")
        # 检查metadata中是否包含"mapper"键，若不存在则抛出异常
        if "mapper" not in metadata:
            raise InvalidSongError(f"No mapper in metadata of {fpath}")
        # 检查metadata中是否包含"audio_file"键，若不存在则抛出异常
        if "audio_file" not in metadata:
            raise InvalidSongError(f"No audio_file in metadata of {fpath}")
        # 检查metadata中是否包含"song_file"键，若不存在则抛出异常
        if "song_file" not in metadata:
            raise InvalidSongError(f"No song_file in metadata of {fpath}")
        # 检查metadata中是否包含"version"键，若不存在则抛出异常
        if "version" not in metadata:
            raise InvalidSongError(f"No version in metadata of {fpath}")
        # 从metadata中获取"name"键对应的值
        name = metadata.get("name")
        # 从metadata中获取"artist"键对应的值，若不存在则尝试获取"author"键的值，若都不存在则默认为"Unknown Artist"
        artist = metadata.get("artist", metadata.get("author", "Unknown Artist"))
        # 从metadata中获取"mapper"键对应的值
        mapper = metadata.get("mapper")
        # 从metadata中获取"audio_file"键对应的值
        audio_file = metadata.get("audio_file")
        # 从metadata中获取"song_file"键对应的值
        song_file = metadata.get("song_file")
        # 从metadata中获取"version"键对应的值，若不存在则默认为-1
        version = metadata.get("version", -1)
        # 创建一个新的Song对象，传入获取到的参数
        new_song = Song(name, audio_file=audio_file, song_file=song_file, song_artist=artist, mapper=mapper, version=version, filepath=fpath)
        # 如果metadata中的"version"键对应的值大于等于2，则设置new_song的music_offset属性
        if metadata.get("version") >= 2:
            new_song.music_offset = metadata.get("music_offset", 0)
        # 返回创建的Song对象
        return new_song


class SongSelector:

    # 定义常量
    ITEM_HEIGHT = 140  # 每个歌曲项的高度
    ITEM_SPACING = 10  # 歌曲项之间的间距
    SCROLL_SPEED = 20  # 滚动速度

    def __init__(self):
        # 初始化歌曲选择器
        self.songs: list[Song] = []  # 存储歌曲对象的列表
        self.reload_songs()  # 初始化时重新加载歌曲
        self.scroll = 0  # 当前滚动位置
        self.scroll_velocity = 0  # 滚动速度
        self.active = False  # 是否处于激活状态
        self.selected_index = -1  # 当前选中的歌曲索引
        self.anim = 0  # 动画参数
        # 定义播放按钮的矩形区域
        self.play_button_rect = pygame.Rect(Config.SCREEN_WIDTH - 300, 150, 250, 100)
        # 渲染播放按钮的文本
        self.play_button_text = get_font(48).render(lang_key("play"), True, (0, 0, 0))
        # 定义返回按钮的矩形区域
        self.back_button_rect = pygame.Rect(Config.SCREEN_WIDTH - 300, 20, 250, 150 - 40)
        # 渲染返回按钮的文本
        self.back_button_text = get_font(48).render(lang_key("back"), True, (0, 0, 0))

    def reload_songs(self):
        # 重新加载歌曲列表
        self.songs = []  # 清空当前歌曲列表
        # 遍历歌曲文件夹中的所有文件
        for song_name in reversed(listdir("songs")):
            path = join("songs", song_name)
            if isfile(path):
                # 如果是.zip或.midiplayground文件，则创建歌曲对象并添加到列表
                if path.lower().endswith(".zip") or path.lower().endswith(".midiplayground"):
                    self.songs.append(make_song_from_zip(path))
                # 如果是.osz文件，则从.osz文件中提取所有歌曲并添加到列表
                if path.lower().endswith(".osz"):
                    self.songs.extend(make_songs_from_osz(path))

    def get_song_rect(self, index: int):
        # 计算歌曲项的矩形区域
        rect = pygame.Rect(
            -200,
            index * (SongSelector.ITEM_HEIGHT + SongSelector.ITEM_SPACING) + 100 + self.scroll,
            int(Config.SCREEN_WIDTH / 2),
            SongSelector.ITEM_HEIGHT
        )
        # 根据动画参数调整矩形位置
        rect.move_ip(-int(abs(Config.SCREEN_HEIGHT / 2 - rect.centery)) / 10, 0)
        rect.move_ip(interpolate_fn(self.songs[index].anim) * 60, 0)
        return rect

    def handle_event(self, event: pygame.event.Event):
        # 检查当前对象是否处于活动状态，如果不是则直接返回
        if not self.active:
            return
        # 处理鼠标滚轮事件，调整滚动速度
        if event.type == pygame.MOUSEWHEEL:
            # 根据鼠标滚轮的滚动方向调整滚动速度
            self.scroll_velocity += event.y / 2
        # 处理鼠标按钮按下事件
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 处理鼠标左键点击事件
                # 遍历所有歌曲，检查鼠标点击是否在歌曲项的矩形区域内
                for index, song in enumerate(self.songs):
                    rect = self.get_song_rect(index)
                    if rect.collidepoint(pygame.mouse.get_pos()):
                        # 如果当前歌曲已经被选中，则跳过
                        if self.selected_index == index:
                            continue
                        # 播放选择音效
                        play_sound("select.mp3")
                        # 根据音频文件类型加载音乐
                        with ZipFile(song.fp) as zf:
                            if song.audio_file_name.lower().endswith(".osu"):
                                pygame.mixer.music.load(zf.read(song.audio_file_name))
                            else:
                                with zf.open(song.audio_file_name) as f:
                                    pygame.mixer.music.load(BytesIO(f.read()))
                        # 设置音量并播放音乐
                        pygame.mixer.music.set_volume(Config.volume/100)
                        pygame.mixer.music.play()
                        # 更新选中的歌曲索引
                        self.selected_index = index
                        return
                # 检查鼠标点击是否在播放按钮的矩形区域内
                if self.play_button_rect.collidepoint(pygame.mouse.get_pos()):
                    # 如果有歌曲被选中，则播放选中的歌曲
                    if self.selected_index+1:
                        play_sound("select.mp3")
                        pygame.mixer.music.stop()
                        self.active = False
                        return self.songs[self.selected_index]
                # 检查鼠标点击是否在返回按钮的矩形区域内
                if self.back_button_rect.collidepoint(pygame.mouse.get_pos()):
                    # 播放选择音效并关闭歌曲选择器
                    play_sound("select.mp3")
                    self.active = False
                    return True

    def draw(self, screen: pygame.Surface):
        # 检查歌曲选择器是否处于激活状态
        if self.active:
            self.anim += 1.8 / FRAMERATE  # 激活状态下增加动画参数
        else:
            self.anim = 0  # 非激活状态下重置动画参数

        # 限制动画参数在0到1之间
        self.anim = max(min(self.anim, 1), 0)
        if self.anim == 0:
            return  # 如果动画参数为0，则不执行后续绘制操作

        # 调整滚动速度，使其逐渐减速
        self.scroll_velocity = min(max(self.scroll_velocity, -1), 1) * (1 - 8 / FRAMERATE)
        keys = pygame.key.get_pressed()
        # 根据按键调整滚动速度，如果按下左Shift键则加快滚动速度
        self.scroll += self.scroll_velocity * SongSelector.SCROLL_SPEED * (1 + keys[pygame.K_LSHIFT])

        # 遍历所有歌曲对象，绘制每个歌曲项
        for index, song in enumerate(self.songs):
            rect = self.get_song_rect(index)
            if not screen.get_rect().colliderect(rect):
                continue  # 如果歌曲项不在屏幕区域内，则跳过绘制

            # 处理鼠标悬停声音
            new_hover = rect.collidepoint(pygame.mouse.get_pos())
            if new_hover and not song.before_hover:
                play_sound("wood.wav")  # 如果鼠标悬停在歌曲项上，播放声音
            song.before_hover = new_hover

            # 处理歌曲项的动画效果
            if new_hover:
                if self.anim == 0:
                    self.anim = 0.3  # 如果动画参数为0，则设置为0.3
                song.anim += 3.6 / FRAMERATE  # 增加歌曲项的动画参数
            else:
                song.anim -= 3.6 / FRAMERATE  # 减少歌曲项的动画参数

            # 限制歌曲项的动画参数在0到1之间
            song.anim = max(min(song.anim, 1), 0)

            # 绘制选中的歌曲项或普通歌曲项
            if self.selected_index == index:
                screen.blit(song.selected_surface, rect.move(80, 0))  # 绘制选中的歌曲项
            else:
                screen.blit(song.surface, rect)  # 绘制普通歌曲项

        # 根据滚动位置调整滚动速度
        if self.scroll > 100:
            self.scroll_velocity -= self.scroll/2000

        # 绘制返回按钮
        self.back_button_rect.x = Config.SCREEN_WIDTH - 500 * interpolate_fn(self.anim) + 200
        back_button_hovered = self.back_button_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, pygame.Color(226, 109, 92).lerp((0, 0, 0), 0.4), self.back_button_rect, border_radius=8)
        pygame.draw.rect(
            screen, pygame.Color(226, 109, 92).lerp(
                (255, 255, 255), back_button_hovered * 0.1
            ), self.back_button_rect.inflate(-8, -8), border_radius=2
        )
        screen.blit(self.back_button_text, self.back_button_text.get_rect(center=self.back_button_rect.center))

        # 如果没有选中，则不绘制播放按钮
        if not self.selected_index + 1:
            return

        # 绘制播放按钮
        self.play_button_rect.x = Config.SCREEN_WIDTH - 500 * interpolate_fn(self.anim) + 200
        play_button_hovered = self.play_button_rect.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(screen, [int(_) for _ in (143 * 0.4, 247 * 0.4, 167 * 0.4)], self.play_button_rect, border_radius=8)
        pygame.draw.rect(
            screen, pygame.Color(143, 247, 167).lerp(
                (255, 255, 255), play_button_hovered * 0.2
            ), self.play_button_rect.inflate(-8, -8), border_radius=2
        )
        screen.blit(self.play_button_text, self.play_button_text.get_rect(center=self.play_button_rect.center))

