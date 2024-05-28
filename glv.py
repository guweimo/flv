from enum import IntEnum
from mxtan_audio import MxtanAudioPcmSampleWidth, MxtanAudioPcmFormatEnum, MxtanAudioSampleRateEnum, MxtanAudioCompressionEnum
from utils import int_to_bytes, int_from_bytes
import math

log = print

class TagTypeEnum(IntEnum):
    video = 0
    audio = 1


def render_mxtan_audio_header(f):
    # mxtan audio 的 header
    header = {}
    header_bytes = b''
    flag = f.read(8)
    header['format_flag'] = flag
    header_bytes += flag
    channel_bytes = f.read(1)
    channel = int.from_bytes(channel_bytes, byteorder='little')
    header['channel'] = channel
    header_bytes += channel_bytes
    print('channel: ', channel)
    sample_rate_bytes = f.read(1)
    sample_rate = int.from_bytes(sample_rate_bytes, byteorder='little')
    sample_rate = MxtanAudioSampleRateEnum(sample_rate)
    header['sample_rate'] = sample_rate
    header_bytes += sample_rate_bytes
    print('sample_rate: ', sample_rate)
    pcm_format_bytes = f.read(1)
    pcm_format = int.from_bytes(pcm_format_bytes, byteorder='little')
    pcm_format = MxtanAudioPcmFormatEnum(pcm_format)
    header['pcm_format'] = pcm_format
    header_bytes += pcm_format_bytes
    print('pcm_format: ', pcm_format)
    compression_format_bytes = f.read(1)
    compression_format = int.from_bytes(compression_format_bytes, byteorder='little')
    header['compression_format'] = compression_format
    header_bytes += compression_format_bytes
    # plain
    print('compression_format: ', compression_format)
    frame_simples_bytes = f.read(2)
    frame_simples = int.from_bytes(frame_simples_bytes, byteorder='little')
    header['frame_simples'] = frame_simples
    header_bytes += frame_simples_bytes
    print('frame_simples: ', frame_simples)
    return header, header_bytes


def render_mxtan_audio_data(f):
    length_bytes = f.read(4)
    length = int_from_bytes(length_bytes)
    frame_bytes = f.read(length)
    return frame_bytes


def render_mxtan_169_header(f):
    header = {}
    header_bytes = b''
    flag = f.read(4)
    header['format_flag'] = flag
    header_bytes += flag
    version_bytes = f.read(1)
    version = int_from_bytes(version_bytes)
    header['version'] = version
    header_bytes += version_bytes
    width_bytes = f.read(2)
    width = int.from_bytes(width_bytes, byteorder='little')
    header['width'] = width
    header_bytes += width_bytes
    height_bytes = f.read(2)
    height = int.from_bytes(height_bytes, byteorder='little')
    header['height'] = height
    header_bytes += height_bytes
    fps_bytes = f.read(1)
    fps = int.from_bytes(fps_bytes, byteorder='little')
    header_bytes += fps_bytes
    header['fps'] = fps
    print('flag:', flag)
    print('version:', version)
    print('width:', width)
    print('height:', height)
    print('fps:', fps)
    return header, header_bytes


def render_mxtan_169_data(f):
    length_bytes = f.read(4)
    length = int_from_bytes(length_bytes)
    frame_bytes = f.read(length)
    return frame_bytes


def glv_tag(tag_type, data_size, data):
    timestamp = 0
    timestamp_bytes = int_to_bytes(timestamp, 4)
    tag_type_bytes = int_to_bytes(tag_type, 1)
    data_size_bytes = int_to_bytes(data_size, 4)
    return timestamp_bytes + tag_type_bytes + data_size_bytes + data


def glv_encode(glv_file, mxtan_169_file, mxtan_audio_file):
    # 读取 mxtan audio 数据
    mxtan_audio_reader = open(mxtan_audio_file, 'rb')
    # 读取 mxtan 169 数据
    mxtan_169_reader = open(mxtan_169_file, 'rb')
    # 解析 mxtan audio header 数据和字节
    mxtan_audio_header, mxtan_audio_header_bytes = render_mxtan_audio_header(mxtan_audio_reader)
    log('mxtan_audio_header', mxtan_audio_header)
    # 解析 mxtan 169 header 数据
    mxtan_169_header, mxtan_169_header_bytes = render_mxtan_169_header(mxtan_169_reader)
    log('mxtan_169_header', mxtan_169_header)

    audio_per_sample_time = 1 / mxtan_audio_header['sample_rate'].hz
    audio_per_frame_time = audio_per_sample_time * mxtan_audio_header['frame_simples']
    video_per_frame_time = 1 / mxtan_169_header['fps']
    log('audio per frame time', audio_per_frame_time)
    log('video per frame time', video_per_frame_time)
    log(video_per_frame_time / audio_per_frame_time)
    video_audio_rate = math.ceil(video_per_frame_time / audio_per_frame_time)
    log('video_audio_rate', video_audio_rate)

    with open(glv_file, 'wb') as f:
        """
        Glv
        version
        audio 0 1
        video 0 1
        
        audio header tag
        video header tag
        
        audio tag
        audio tag
        video tag
        ....
        """
        # 写入文件格式
        flag = b'MxtanLiveVideo'
        f.write(flag)
        # 版本号
        version = 1
        version_bytes = int_to_bytes(version, 1)
        f.write(version_bytes)
        # 是否有音频，0 否 1 是
        audio = 1
        audio_bytes = int_to_bytes(audio, 1)
        f.write(audio_bytes)
        # 是否有视频，0 否 1 是
        video = 1
        video_bytes = int_to_bytes(video, 1)
        f.write(video_bytes)

        # 写入 audio header tag
        audio_header_tag = glv_tag(
            TagTypeEnum.audio,
            len(mxtan_audio_header_bytes),
            mxtan_audio_header_bytes
        )
        f.write(audio_header_tag)
        # 写入 video header tag
        video_header_tag = glv_tag(
            TagTypeEnum.video,
            len(mxtan_169_header_bytes),
            mxtan_169_header_bytes
        )
        f.write(video_header_tag)

        while True:
            # 根据图片和音频的比例遍历次数
            # 读取 audio 数据并添加到 glv 文件中
            for i in range(video_audio_rate):
                audio_data_bytes = render_mxtan_audio_data(mxtan_audio_reader)
                if audio_data_bytes == b'':
                    break
                audio_tag = glv_tag(
                    TagTypeEnum.audio,
                    len(audio_data_bytes),
                    audio_data_bytes
                )
                f.write(audio_tag)
            # 读取 video 数据并添加到 glv 文件中
            video_data_bytes = render_mxtan_169_data(mxtan_169_reader)
            if video_data_bytes == b'':
                break
            video_tag = glv_tag(
                TagTypeEnum.video,
                len(video_data_bytes),
                video_data_bytes
            )
            f.write(video_tag)


def main():
    glv_file = 'BigBuckBunny-new.glv'
    mxtan_169_file = 'BigBuckBunny-10s-gzip-88.m169'
    mxtan_audio_file = 'BigBuckBunny-stereo-10s.ga'

    glv_encode(glv_file, mxtan_169_file, mxtan_audio_file)


if __name__ == '__main__':
    main()