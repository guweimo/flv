from PIL import Image
from enum import IntEnum
import pygame
from io import BytesIO
from video import encode,restore_image
from gzip import compress, decompress
import json


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


def mxtan_image_decode(mxtan_image_bytes):
    f = BytesIO(mxtan_image_bytes)
    format_flag = f.read(8)
    mode = f.read(1)
    mode = int.from_bytes(mode, byteorder='little')
    compression_format = f.read(1)
    width = f.read(2)
    width = int.from_bytes(width, byteorder='little')
    height = f.read(2)
    height = int.from_bytes(height, byteorder='little')
    # 数据长度
    data_len_bytes = f.read(4)
    data_len = int.from_bytes(data_len_bytes, byteorder='little')
    # rgb
    data = f.read(data_len)
    return data, width, height


# bytes 转成 image
def image_from_bytes(data, width, height):
    return Image.frombytes('RGB', (width, height), data)


def mxtan_diff_encode_to_bytes(diff, json_str):
    image = diff
    # 二进制 7
    format_flag = b'MxtanDiff'
    bytes = format_flag
    # int -> bytes 1
    mode = MxtanImageModeEnum.rgb
    mode_bytes = mode.to_bytes(1, byteorder='little')
    bytes += mode_bytes
    # int -> bytes 1
    compression_format = MxtanImageCompressionEnum.plain
    compression_format_bytes = compression_format.to_bytes(1, byteorder='little')
    bytes += compression_format_bytes
    # width 2
    width, height = image.size
    width_bytes = width.to_bytes(2, byteorder='little')
    bytes += width_bytes
    # height 2
    height_bytes = height.to_bytes(2, byteorder='little')
    bytes += height_bytes
    # json
    json_bytes = json_str.encode()
    json_bytes = compress(json_bytes)
    # json 长度
    json_len = len(json_bytes)
    json_len_bytes = json_len.to_bytes(4, byteorder='little')
    bytes += json_len_bytes
    bytes += json_bytes
    # diff 数据
    data = BytesIO()
    image.save(data, 'JPEG')
    data = data.getvalue()
    # diff 数据长度
    data_len = len(data)
    data_len_bytes = data_len.to_bytes(4, byteorder='little')
    bytes += data_len_bytes
    bytes += data

    return bytes

def mxtan_diff_encode(image_file, image_mxtan):
    key_frame_file = 'static/bbb_mxtanimage/big_buck_bunny_00032.mxtanimage'
    image = Image.open(image_file)

    # 读取 key_frame
    with open(key_frame_file, 'rb') as k:
        key_frame_data = k.read()
    # 拿到 mxtanimage 的 图片数据
    image_data, width, height = mxtan_image_decode(key_frame_data)
    # 转成 image 格式
    key_frame_image = image_from_bytes(image_data, width, height)

    # 拿到 json 数据 和 diff 数据
    json_str, diff_data = encode(key_frame_image, image)

    with open(image_mxtan, 'wb') as f:
        # 二进制 7
        format_flag = b'MxtanDiff'
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
        # json
        json_bytes = json_str.encode()
        json_bytes = compress(json_bytes)
        # json 长度
        json_len = len(json_bytes)
        json_len_bytes = json_len.to_bytes(4, byteorder='little')
        f.write(json_len_bytes)
        f.write(json_bytes)
        # diff 数据
        data = BytesIO()
        diff_data.save(data, 'JPEG')
        data = data.getvalue()
        # data = diff_data.tobytes()
        # diff 长度
        data_len = len(data)
        data_len_bytes = data_len.to_bytes(4, byteorder='little')
        f.write(data_len_bytes)
        f.write(data)


def mxtan_diff_decode():
    key_frame_file = 'static/bbb_mxtanimage/big_buck_bunny_00032.mxtanimage'
    # 读取 key_frame
    with open(key_frame_file, 'rb') as k:
        key_frame_data = k.read()
    # 拿到 mxtanimage 的 图片数据
    image_data, width, height = mxtan_image_decode(key_frame_data)
    # 转成 image 格式
    key_frame_image = image_from_bytes(image_data, width, height)

    image_mxtan = 'big_buck_bunny_00033_gzip.mxtandiff'

    with open(image_mxtan, 'rb') as f:
        format_flag = f.read(7)
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
        # json长度
        json_len_bytes = f.read(4)
        json_len = int.from_bytes(json_len_bytes, byteorder='little')
        print('json_len: ', json_len)
        # json
        json_bytes = f.read(json_len)
        json_bytes = decompress(json_bytes)
        json_str = json_bytes.decode()
        json_data = json.loads(json_str)
        print('json', json_data)
        # 数据长度
        data_len_bytes = f.read(4)
        data_len = int.from_bytes(data_len_bytes, byteorder='little')
        print('data_len: ', data_len)
        # rgb
        diff_bytes = f.read(data_len)
        diff = Image.open(BytesIO(diff_bytes))
        data = restore_image(key_frame_image, diff, json_data)
        data = data.tobytes()
        print('data: ', data)

        # return
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
    MxtanDiff
        rgb yuv
        version
        压缩的类型 lzw gzip 更好的压缩方法
        图片的宽度
        图片的长度

        json 长度
        json 数据
        diff 数据长度
        diff 数据
        :return:
    """
    image_file = 'static/bbb/big_buck_bunny_00032.png'
    image_mxtan = 'big_buck_bunny_00033_gzip.mxtandiff'
    mxtan_diff_encode(image_file, image_mxtan)
    mxtan_diff_decode()



if __name__ == '__main__':
    main()