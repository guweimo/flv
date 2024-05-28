from enum import IntEnum
from mxtan_audio import MxtanAudioPcmSampleWidth, MxtanAudioPcmFormatEnum, MxtanAudioSampleRateEnum, MxtanAudioCompressionEnum
from utils import int_to_bytes, int_from_bytes
import math

log = print


def render_mxtan_audio_header(f):
    # mxtan audio 的 header
    header = {}
    flag = f.read(8)
    header['format_flag'] = flag
    channel_bytes = f.read(1)
    channel = int.from_bytes(channel_bytes, byteorder='little')
    header['channel'] = channel
    print('channel: ', channel)
    sample_rate_bytes = f.read(1)
    sample_rate = int.from_bytes(sample_rate_bytes, byteorder='little')
    sample_rate = MxtanAudioSampleRateEnum(sample_rate)
    header['sample_rate'] = sample_rate
    print('sample_rate: ', sample_rate)
    pcm_format_bytes = f.read(1)
    pcm_format = int.from_bytes(pcm_format_bytes, byteorder='little')
    pcm_format = MxtanAudioPcmFormatEnum(pcm_format)
    header['pcm_format'] = pcm_format
    print('pcm_format: ', pcm_format)
    compression_format_bytes = f.read(1)
    compression_format = int.from_bytes(compression_format_bytes, byteorder='little')
    header['compression_format'] = compression_format
    # plain
    print('compression_format: ', compression_format)
    frame_simples_bytes = f.read(2)
    frame_simples = int.from_bytes(frame_simples_bytes, byteorder='little')
    header['frame_simples'] = frame_simples
    print('frame_simples: ', frame_simples)
    return header


def glv_encode(glv_file, mxtan_169_file, mxtan_audio_file):
    # 读取 mxtan audio 数据
    mxtan_audio_reader = open(mxtan_audio_file, 'rb')
    # 读取 mxtan 169 数据
    mxtan_169_reader = open(mxtan_169_file, 'rb')
    # 解析 mxtan audio header 数据
    mxtan_audio_header = render_mxtan_audio_header(mxtan_audio_reader)
    log('mxtan_audio_header', mxtan_audio_header)


def main():
    glv_file = 'BigBuckBunny-new.glv'
    mxtan_169_file = 'BigBuckBunny-10s-gzip-88.m169'
    mxtan_audio_file = 'BigBuckBunny-stereo-10s.ga'

    glv_encode(glv_file, mxtan_169_file, mxtan_audio_file)


if __name__ == '__main__':
    main()
