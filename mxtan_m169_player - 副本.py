import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ''
import pygame
from typing import IO
from enum import IntEnum
from video import restore_image
from PIL import Image
import json

def draw_image(screen, width, height, image_bytes: bytes):
    size = (width, height)
    py_image = pygame.image.frombuffer(image_bytes, size, 'RGB')
    image_rect = py_image.get_rect()
    screen.blit(py_image, image_rect)


from io import BytesIO

class MxtanFrameTypeEnum(IntEnum):
    #h264
    # 关键帧
    I = 0
    # diff
    P = 1

def image_from_bytes(path, width, height):
    img = Image.frombytes('RGB', (width, height), path)
    return img

def mxtan_image_decode(mxtan_image_bytes):
    f = BytesIO(mxtan_image_bytes)
    format_flag = f.read(8)
    mode = f.read(1)
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

    return data

def mxtan_diff_decode(mxtan_image_bytes, key_frame):
    f = BytesIO(mxtan_image_bytes)
    format_flag = f.read(7)
    mode = f.read(1)
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
    # json长度
    json_len_bytes = f.read(4)
    json_len = int.from_bytes(json_len_bytes, byteorder='little')
    # json
    json_bytes = f.read(json_len)
    json_str = json_bytes.decode()
    json_data = json.loads(json_str)

    data = Image.open(BytesIO(data))

    data = restore_image(key_frame, data, json_data)

    return data.tobytes()

def main():
    m169_file = 'BigBuckBunny-10s-diff.m169'
    with open(m169_file, 'rb') as f:
        flag = f.read(4)
        version = f.read(1)
        width_bytes = f.read(2)
        width = int.from_bytes(width_bytes, byteorder='little')
        height_bytes = f.read(2)
        height = int.from_bytes(height_bytes, byteorder='little')
        fps_bytes = f.read(1)
        fps = int.from_bytes(fps_bytes, byteorder='little')
        print('flag:', flag)
        print('version:', version)
        print('width:', width)
        print('height:', height)
        print('fps:', fps)
        screen = pygame.display.set_mode((width, height))
        clock = pygame.time.Clock()
        running = True
        # 读取帧数据
        pre_key_frame = ''
        while not f.closed:
            frame_bytes_len_bytes = f.read(4)
            if frame_bytes_len_bytes == b'':
                break
            frame_bytes_len = int.from_bytes(frame_bytes_len_bytes, byteorder='little')
            frame_bytes = f.read(frame_bytes_len)
            # print("frame_bytes_len:", frame_bytes_len)
            # print("frame_bytes:", frame_bytes[:10])
            frame_type = frame_bytes[0]
            # frame_type = int.from_bytes(frame_type_bytes, byteorder='little')
            frame_data = frame_bytes[1:]
            # 用pygame来绘制帧
            # data mxtaniamge像素数据
            # print('frame_type', frame_type)
            if frame_type == MxtanFrameTypeEnum.I:
                data = mxtan_image_decode(frame_data)
                pre_key_frame = image_from_bytes(data, width, height)
            elif frame_type == MxtanFrameTypeEnum.P:
                data = mxtan_diff_decode(frame_data, pre_key_frame)
            # print('data: ', data[:10])
            draw_image(screen, width, height, data)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            pygame.display.flip()
            clock.tick(fps)


if __name__ == '__main__':
    main()