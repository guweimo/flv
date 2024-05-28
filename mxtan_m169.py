from mxtan_diff import gua_diff_encode_to_bytes
from enum import IntEnum
from video import encode
from PIL import Image
from io import BytesIO
import json

class MxtanFrameTypeEnum(IntEnum):
    #h264
    # 关键帧
    I = 0
    # diff
    P = 1

def image_from_bytes(path, width, height):
    img = Image.frombytes('RGB', (width, height), path)
    return img


def gua_image_decode(gua_image_bytes):
    f = BytesIO(gua_image_bytes)
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
    return data, width, height


def m169_encode(bbb_guaimage):
    """
    视频编码格式
        数据头
            M169
            version
            width
            height
            fps 每秒多少帧
        帧序列
            长度 整个帧数据的长度
                关键帧, 帧的类型
                guaImage
                guaDIff
    :return:
    """
    m169 = 'BigBuckBunny-10s-gzip-88.m169'
    with open(m169, 'wb') as f:
        # 二进制 8
        format_flag = b'M169'
        f.write(format_flag)
        # 写入版本
        version = 1
        version_bytes = version.to_bytes(1, byteorder='little')
        f.write(version_bytes)
        #
        width = 640
        width_bytes = width.to_bytes(2, byteorder='little')
        f.write(width_bytes)
        #
        height = 360
        height_bytes = height.to_bytes(2, byteorder='little')
        f.write(height_bytes)
        #
        fps = 24
        fps_bytes = fps.to_bytes(1, byteorder='little')
        f.write(fps_bytes)
        key_frame = ''
        # 帧数据写入
        # 帧类型 + 帧数据
        for guaimage in bbb_guaimage:
            print(guaimage)
            frame_type = MxtanFrameTypeEnum.I
            #
            with open(guaimage, 'rb') as _gua:
                frame_data = _gua.read()
            # 读取图片的数据，宽高
            data, width, height = gua_image_decode(frame_data)
            # 当 key_frame 为空字符串时，把这个图片当成关键帧
            # 否则是 diff 帧
            if key_frame == '':
                frame_type = MxtanFrameTypeEnum.I
                key_frame = image_from_bytes(data, width, height)
            else:
                # bytes 转成 image 格式
                current_frame = image_from_bytes(data, width, height)
                # 读取数据
                json_str, diff = encode(key_frame, current_frame)
                # json_str 为空时，说明是关键帧
                # 否则是 diff 帧
                if json_str == '':
                    key_frame = image_from_bytes(data, width, height)
                    print('key frame')
                else:
                    frame_type = MxtanFrameTypeEnum.P
                    print('diff frame')
                    # 拿到 diff 数据的 bytes
                    frame_data = gua_diff_encode_to_bytes(diff, json_str)
            frame_type_bytes = frame_type.to_bytes(1, byteorder='little')
            frame_bytes = frame_type_bytes + frame_data
            frame_bytes_len = len(frame_bytes)
            frame_bytes_len_bytes = frame_bytes_len.to_bytes(4, byteorder='little')
            f.write(frame_bytes_len_bytes + frame_bytes)

def main():
    """
    :return:
    视频编码格式
    数据头
        M169
        version
        width
        height
        fps 每秒多少帧
    帧序列
        长度 整个帧数据的长度
            关键帧, 帧的类型
            guaImage
            guaDIff
    # 准备帧数据
    png -> guaimage
    #
    """
    # 遍历bbb文件夹下的png文件
    # bbb = [f'static/bbb/big_buck_bunny_{str(i).zfill(5)}.png' for i in range(1, 241)]
    bbb_guaimage = [f'static/bbb_guaimage/big_buck_bunny_{str(i).zfill(5)}.guaimage' for i in range(1, 241)]
    # args_tuple_list = zip(bbb, bbb_guaimage)
    # for args_tuple in args_tuple_list:
    #     gua_image_encode(*args_tuple)
    #     print(args_tuple)
    pass
    m169_encode(bbb_guaimage)



if __name__ == '__main__':
    main()
