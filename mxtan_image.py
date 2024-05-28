from PIL import Image
from enum import IntEnum
import pygame


import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ''
import pygame


def draw_image(screen, width, height, image_bytes: bytes):
    size = (width, height)
    py_image = pygame.image.frombuffer(image_bytes, size, 'RGB')
    image_rect = py_image.get_rect()
    screen.blit(py_image, image_rect)


class MxtanImageModeEnum(IntEnum):
    #
    rgb = 1
    #
    yuv = 2


class MxtanImageCompressionEnum(IntEnum):
    # 纯rgb
    plain = 0
    #
    gzip = 1
    #
    lzw = 2


def mxtan_image_encode(image_file, image_mxtan):
    # image_file = 'static/bbb/big_buck_bunny_00033.png'
    # image_mxtan = 'big_buck_bunny_00033.mxtanimage'
    image = Image.open(image_file)
    with open(image_mxtan, 'wb') as f:
        # 二进制 8
        format_flag = b'MxtanImage'
        f.write(format_flag)
        # int -> bytes 1
        mode = MxtanImageModeEnum.rgb
        mode_bytes = mode.to_bytes(1, byteorder='little')
        f.write(mode_bytes)
        # int -> bytes 1
        compression_format = MxtanImageCompressionEnum.plain
        compression_format_bytes = compression_format.to_bytes(1, byteorder='little')
        f.write(compression_format_bytes)
        # width 2
        width, height = image.size
        width_bytes = width.to_bytes(2, byteorder='little')
        f.write(width_bytes)
        # height 2
        height_bytes = height.to_bytes(2, byteorder='little')
        f.write(height_bytes)
        #
        data = image.tobytes()
        # 数据长度
        data_len = len(data)
        data_len_bytes = data_len.to_bytes(4, byteorder='little')
        f.write(data_len_bytes)
        f.write(data)


def mxtan_image_decode():
    image_mxtan = 'big_buck_bunny_00033.mxtanimage'
    with open(image_mxtan, 'rb') as f:
        format_flag = f.read(8)
        print('format_flag: ', format_flag)
        mode = f.read(1)
        print('mode: ', mode)
        compression_format = f.read(1)
        print('compression_format: ', compression_format)
        width = f.read(2)
        width = int.from_bytes(width, byteorder='little')
        print('width: ', width)
        height = f.read(2)
        height = int.from_bytes(height, byteorder='little')
        print('height: ', height)
        # 数据长度
        data_len_bytes = f.read(4)
        data_len = int.from_bytes(data_len_bytes, byteorder='little')
        print('data_len: ', data_len)
        # rgb
        data = f.read(data_len)
        print('data: ', data)
        # 验证图片是否正常
        # 直接用pygame来绘制
        screen = pygame.display.set_mode((width, height))
        clock = pygame.time.Clock()
        running = True
        fps = 30
        while running:
            # pygame
            draw_image(screen, width, height, data)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            pygame.display.flip()
            clock.tick(fps)




def main():
    """
    MxtanImage
        rgb yuv
        version
        压缩的类型 lzw gzip 更好的压缩方法
        图片的宽度
        图片的长度

        数据长度
        数据
        :return:
    """
    mxtan_image_decode()



if __name__ == '__main__':
    main()