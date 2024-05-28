from mxtan_image import mxtan_image_encode
from enum import IntEnum
from PIL import Image
from io import BytesIO
from video import encode
import json

# 转成灰度图
def grayimage(path, width, height):
    # convert('L') 转为灰度图
    # 这样每个像素点就只有一个灰度数据
    img = Image.frombytes('RGB', (width, height), path).convert('L')
    return img

def image_from_bytes(path, width, height):
    img = Image.frombytes('RGB', (width, height), path)
    return img


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

class MxtanFrameTypeEnum(IntEnum):
    #h264
    # 关键帧
    I = 0
    # diff
    P = 1


def mxtan_diff_encode(diff, jsonData):
    # image_file = 'static/bbb/big_buck_bunny_00033.png'
    # image_mxtan = 'big_buck_bunny_00033.mxtanimage'
    image = diff
    # 二进制 7
    format_flag = b'MxtanDiff'
    # int -> bytes 1
    mode = MxtanImageModeEnum.rgb
    mode_bytes = mode.to_bytes(1, byteorder='little')
    # int -> bytes 1
    compression_format = MxtanImageCompressionEnum.plain
    compression_format_bytes = compression_format.to_bytes(1, byteorder='little')
    # width 2
    width, height = image.size
    width_bytes = width.to_bytes(2, byteorder='little')
    # height 2
    height_bytes = height.to_bytes(2, byteorder='little')
    #
    data = BytesIO()
    image.save(data, 'JPEG')
    data = data.getvalue()
    # 数据长度
    data_len = len(data)
    data_len_bytes = data_len.to_bytes(4, byteorder='little')

    json_bytes = jsonData.encode()
    json_len = len(json_bytes)
    json_len_bytes = json_len.to_bytes(4, byteorder='little')

    return format_flag + mode_bytes + \
           compression_format_bytes + width_bytes + \
           height_bytes + \
           data_len_bytes + data \
           + json_len_bytes + json_bytes


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
    return data, width, height

def m169_encode(bbb_mxtanimage):
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
                mxtanImage
                mxtanDIff
    :return:
    """
    m169 = 'BigBuckBunny-10s-diff.m169'
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
        pre_key_frame = ''
        # 帧数据写入
        # 帧类型 + 帧数据
        for mxtanimage in bbb_mxtanimage:
            print(mxtanimage)
            #
            frame_type = MxtanFrameTypeEnum.I
            #
            with open(mxtanimage, 'rb') as _mxtan:
                frame_data = _mxtan.read()
            data, width, height = mxtan_image_decode(frame_data)

            if pre_key_frame == '':
                frame_type = MxtanFrameTypeEnum.I
                pre_key_frame = image_from_bytes(data, width, height)
            else:
                current_frame = image_from_bytes(data, width, height)
                json, diff = encode(pre_key_frame, current_frame)
                if json == '':
                    pre_key_frame = image_from_bytes(data, width, height)
                else:
                    frame_type = MxtanFrameTypeEnum.P
                    frame_data = mxtan_diff_encode(diff, json)
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
            mxtanImage
            mxtanDIff
    # 准备帧数据
    png -> mxtanimage
    #
    """
    # 遍历bbb文件夹下的png文件
    # bbb = [f'static/bbb/big_buck_bunny_{str(i).zfill(5)}.png' for i in range(1, 241)]
    bbb_mxtanimage = [f'static/bbb_mxtanimage/big_buck_bunny_{str(i).zfill(5)}.mxtanimage' for i in range(1,241)]
    # args_tuple_list = zip(bbb, bbb_mxtanimage)
    # for args_tuple in args_tuple_list:
    #     mxtan_image_encode(*args_tuple)
    #     print(args_tuple)
    m169_encode(bbb_mxtanimage)


if __name__ == '__main__':
    main()
