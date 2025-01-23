import cv2 #  导入OpenCV库，用于图像处理
import numpy as np #  导入NumPy库，用于数组操作

import pygame #  导入Pygame库，用于游戏开发

"""
https://stackoverflow.com/questions/67561142/bloom-effect-in-pygame-so-that-text-glows
""" #  引用Stack Overflow上的一个问题，关于在Pygame中实现文本发光效果


class Colors:
    # 定义一个名为WHITE_ISH的类属性，值为一个包含三个整数的元组，表示一种浅白色的RGB颜色值
    WHITE_ISH = (246, 246, 246)
    # 定义一个名为YELLOW_ISH的类属性，值为一个包含三个整数的元组，表示一种浅黄色的RGB颜色值
    YELLOW_ISH = (214, 198, 136)
    # 定义一个名为RED_ISH的类属性，值为一个包含三个整数的元组，表示一种浅红色的RGB颜色值
    RED_ISH = (156, 60, 60)


def create_border(image: np.ndarray, margin: int, thickness: int, color: Colors) -> np.ndarray:
    # 获取图像的高度和宽度
    # image.shape[:2] 返回图像的高度和宽度，忽略颜色通道
    height, width = image.shape[:2]
    cv2.rectangle(image, (margin, margin), (width - margin, height - margin), color, thickness=thickness)
    return image


def apply_blooming(image: np.ndarray) -> np.ndarray:
    # 对图像进行高斯模糊和均值模糊，以创建发光效果
    cv2.GaussianBlur(image, ksize=(15, 15), sigmaX=20, sigmaY=20, dst=image)
    cv2.blur(image, ksize=(12, 12), dst=image)
    return image


def glowing_border(image: np.ndarray, margin=20, thickness=20, color: Colors = Colors.WHITE_ISH):
    """
    为图像添加发光边框。

    参数:
        image: 需要添加边框的图像。
        margin: 边框距离图像边缘的距离，默认为20像素。
        thickness: 边框的厚度，默认为20像素。
        color: 边框的颜色，默认为浅黄色（可以是其他定义的颜色）。

    修改:
        输入图像将被修改并添加发光边框。

    返回:
        添加了发光边框后的同一图像。
    """

    # 生成指定颜色的边框
    image = create_border(image, margin, thickness, color)

    # 应用发光效果
    image = apply_blooming(image)

    # 重新绘制原始边框，以获得清晰的轮廓
    # 类似于Watson-Scott测试，这里添加了两个边框
    image = create_border(image, margin - 1, 1, color)
    image = create_border(image, margin + 1, 1, color)
    return image


def make_glowy2(size, color, intensity=0) -> pygame.Surface:
    # 创建一个指定大小的黑色图像
    image = np.zeros((*size[::-1], 3), dtype=np.uint8)
    # 为图像添加发光边框
    border = glowing_border(image.copy(), color=color, thickness=intensity)
    # 将处理后的图像转换为pygame表面对象，并返回
    return pygame.surfarray.make_surface(np.fliplr(np.rot90(border, k=-1)))