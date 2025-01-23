from utils import *
from menu import Menu
from game import Game
from configpage import ConfigPage
from songselector import SongSelector
from errorscreen import ErrorScreen
from os import getcwd
from platform import system as get_os
from config import save_to_file
import debuginfo
import webbrowser
import pygame
from array import array


def main():
    """
    主函数，负责游戏的初始化和主循环。
    """

    # 根据操作系统类型进行特定的初始化设置
    if "Windows" in get_os():
        # 修复高DPI显示上的鼠标问题
        from ctypes import windll
        windll.user32.SetProcessDPIAware()
    elif "Darwin" in get_os():
        # 修复Mac上的OpenGL错误补丁
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

    # 初始化Pygame和其他基础设置
    n_frames = 0
    pygame.mixer.music.load("./assets/mainmenu.mp3")
    pygame.mixer.music.set_volume(Config.volume / 100)
    pygame.mixer.music.play(loops=-1, start=2)

    clock = pygame.time.Clock()

    flags = pygame.HWACCEL | pygame.HWSURFACE | pygame.OPENGL | pygame.DOUBLEBUF
    do_vsync = 1
    if "Linux" in get_os():
        # 在Linux系统下禁用VSync以避免OpenGL同步错误
        do_vsync = 0

    if [Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT] == [pygame.display.Info().current_w, pygame.display.Info().current_h]:
        # 如果屏幕分辨率与当前显示器分辨率相同，则启用全屏模式
        flags |= pygame.FULLSCREEN
    
    real_screen = pygame.display.set_mode(
        [Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT],
        flags,
        vsync=do_vsync
    )
    screen = pygame.Surface([Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT])

    try:
        # 设置窗口标题和图标
        pygame.display.set_caption("Midi Playground")
        pygame.display.set_icon(pygame.image.load("./assets/icon.png").convert_alpha())
    except Exception as e:
        print(e)

    # 初始化ModernGL上下文
    ctx = moderngl.create_context()
    Config.ctx = ctx

    # 创建四边形缓冲区用于渲染
    quad_buffer = ctx.buffer(data=array('f', [
        -1.0, 1.0, 0.0, 0.0,  # 左上角
        1.0, 1.0, 1.0, 0.0,   # 右上角
        -1.0, -1.0, 0.0, 1.0, # 左下角
        1.0, -1.0, 1.0, 1.0   # 右下角
    ]))

    # 定义顶点着色器代码
    vert_shader = '''
    #version 330 core
    
    in vec2 vert;
    in vec2 texcoord;
    out vec2 uvs;
    
    void main() {
        uvs = texcoord;
        gl_Position = vec4(vert.x, vert.y, 0.0, 1.0);
    }
    '''

    # 读取片段着色器文件内容
    with open(f"./assets/shaders/{Config.shader_file_name}") as shader_file:
        frag_shader = shader_file.read()

    # 创建GLSL程序并绑定到上下文
    glsl_program = ctx.program(vertex_shader=vert_shader, fragment_shader=frag_shader)
    render_object = ctx.vertex_array(glsl_program, [(quad_buffer, '2f 2f', 'vert', 'texcoord')])

    Config.glsl_program = glsl_program
    Config.render_object = render_object
    Config.screen = screen

    # 初始化游戏界面组件
    menu = Menu()
    song_selector = SongSelector()
    config_page = ConfigPage()
    error_screen = ErrorScreen()
    game = Game()

    # 游戏主循环
    running = True
    while running:
        n_frames += 1

        # 如果主题设置为彩虹模式，动态更新颜色
        if Config.theme == "rainbow":
            to_set_as_rainbow = pygame.Color((0, 0, 0))
            to_set_as_rainbow2 = pygame.Color((0, 0, 0))
            to_set_as_rainbow.hsva = (((pygame.time.get_ticks() / 1000) * Config.rainbow_speed) % 360, 100, 75, 100)
            to_set_as_rainbow2.hsva = ((((pygame.time.get_ticks() / 1000) * Config.rainbow_speed) + 180) % 360, 100, 75, 100)
            get_colors()["background"] = to_set_as_rainbow
            get_colors()["hallway"] = to_set_as_rainbow2
            get_colors()["square"][0] = to_set_as_rainbow

        screen.fill(get_colors()["background"])

        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    # 人工制造延迟峰值，用于调试目的
                    total = 0
                    for _ in range(10_000_000):
                        total += 1
                if event.key == pygame.K_F3:
                    print("调试信息已复制到剪贴板")
                    debuginfo.print_debug_info()
                if event.key == pygame.K_F2:
                    if game.active:
                        debuginfo.debug_rectangles(game.safe_areas)
                if event.key == pygame.K_ESCAPE:
                    if song_selector.active:
                        song_selector.active = False
                        menu.active = True
                        if song_selector.selected_index + 1:
                            pygame.mixer.music.load("./assets/mainmenu.mp3")
                            pygame.mixer.music.set_volume(Config.volume / 100)
                            pygame.mixer.music.play(loops=-1, start=2)
                            song_selector.selected_index = -1
                        continue
                    if game.active:
                        game.active = False
                        song_selector.active = True
                        pygame.mixer.music.load("./assets/mainmenu.mp3")
                        pygame.mixer.music.set_volume(Config.volume / 100)
                        pygame.mixer.music.play(loops=-1, start=2)
                        song_selector.selected_index = -1
                        continue
                    if config_page.active:
                        config_page.active = False
                        menu.active = True
                        continue
                    if error_screen.active:
                        error_screen.active = False
                        song_selector.active = True
                        continue
                    running = False

            # 处理菜单事件
            option_id = menu.handle_event(event)
            if option_id:
                if option_id == "open-songs-folder":
                    open_file(join(getcwd(), "songs"))# 打开歌曲文件夹
                    continue
                if option_id == "contribute":
                    webbrowser.open("https://github.com/quasar098/midi-playground")# 打开GitHub页面
                    continue
                menu.active = False
                if option_id == "config":
                    config_page.active = True# 打开配置页面
                if option_id == "play":
                    song_selector.active = True# 打开歌曲选择器页面
                    song_selector.reload_songs()
                if option_id == "quit":
                    running = False# 退出游戏
                continue

            # 处理歌曲选择器事件
            song = song_selector.handle_event(event)
            if song:
                if isinstance(song, bool):
                    menu.active = True
                    if song_selector.selected_index + 1:
                        pygame.mixer.music.load("./assets/mainmenu.mp3")# 加载主菜单音乐
                        pygame.mixer.music.set_volume(Config.volume / 100)# 设置音量
                        pygame.mixer.music.play(loops=-1, start=2)# 播放音乐
                        song_selector.selected_index = -1# 重置选中索引
                    continue
                # 开始播放选中的歌曲
                Config.current_song = song
                game.active = True
                if msg := game.start_song(screen):# 开始播放歌曲
                    if isinstance(msg, str):# 显示错误信息
                        game.active = False# 关闭游戏界面
                        error_screen.active = True# 打开错误界面
                        error_screen.msg = msg# 显示错误信息
                    else:
                        game.active = False# 关闭游戏界面
                        song_selector.active = True# 打开歌曲选择器界面
                    pygame.mixer.music.load("./assets/mainmenu.mp3")# 加载主菜单音乐
                    pygame.mixer.music.set_volume(Config.volume / 100)# 设置音量
                    pygame.mixer.music.play(loops=-1, start=2)# 播放音乐

            # 处理配置页面事件
            if config_page.handle_event(event):
                config_page.active = False
                menu.active = True

            # 处理游戏事件
            if game.handle_event(event):
                game.active = False
                song_selector.active = True

        # 绘制界面元素
        game.draw(screen, n_frames)# 绘制游戏界面
        song_selector.draw(screen)# 绘制歌曲选择器界面
        config_page.draw(screen)# 绘制配置页面界面
        menu.draw(screen, n_frames)# 绘制菜单界面
        error_screen.draw(screen)# 绘制错误界面

        update_screen(screen, glsl_program, render_object)

        Config.dt = clock.tick(FRAMERATE) / 1000

    pygame.quit()
    save_to_file()


if __name__ == '__main__':
    main()
