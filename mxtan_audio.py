from enum import IntEnum
import gzip
import lzw

class MxtanAudioChannelEnum(IntEnum):
    # 单声道
    mono = 1
    # 双声道
    stereo = 2


class MxtanAudioPcmFormatEnum(IntEnum):
    # 无符号
    u8 = 0          # PCM unsigned 8-bit
    u16be = 1          # PCM unsigned 16-bit big-endian
    u16le = 2          # PCM unsigned 16-bit little-endian
    u24be = 3          # PCM unsigned 24-bit big-endian
    u24le = 4          # PCM unsigned 24-bit little-endian
    u32be = 5          # PCM unsigned 32-bit big-endian
    u32le = 6          # PCM unsigned 32-bit little-endian
    # 有符号
    s8 = 7          # PCM signed 8-bit
    s16be = 8          # PCM signed 16-bit big-endian
    s16le = 9          # PCM signed 16-bit little-endian
    s24be = 10         # PCM signed 24-bit big-endian
    s24le = 11         # PCM signed 24-bit little-endian
    s32be = 12         # PCM signed 32-bit big-endian
    s32le = 13         # PCM signed 32-bit little-endian
    # 浮点型
    f32be = 14         # PCM 32-bit floating-point big-endian
    f32le = 15         # PCM 32-bit floating-point little-endian
    f64be = 16         # PCM 64-bit floating-point big-endian
    f64le = 17         # PCM 64-bit floating-point little-endian


class MxtanAudioSampleRateEnum(IntEnum):
    """
    https://en.wikipedia.org/wiki/Sampling_(signal_processing)#Sampling_rate
    """
    Hz_8000 = 0
    Hz_11025 = 1
    Hz_16000 = 2
    Hz_22050 = 3
    Hz_32000 = 4
    Hz_37800 = 5
    Hz_44056 = 6
    Hz_44100 = 7
    Hz_47250 = 8
    Hz_48000 = 9
    Hz_50000 = 10
    Hz_50400 = 11
    Hz_64000 = 12
    Hz_88200 = 14
    Hz_96000 = 15
    Hz_176400 = 16
    Hz_192000 = 17
    Hz_352800 = 18
    Hz_2822400 = 19
    Hz_5644800 = 20
    Hz_11289600 = 21
    Hz_22579200 = 22

    @property
    def hz(self):
        rate = int(self.name.split('_')[-1])
        return rate

class MxtanAudioCompressionEnum(IntEnum):
    # 纯rgb
    plain = 0
    #
    gzip = 1
    #
    lzw = 2


class MxtanAudioPcmSampleWidthException(Exception):
    pass


class MxtanAudioPcmSampleWidth(object):
    width_map = {
        MxtanAudioPcmFormatEnum.u8: 1,
        MxtanAudioPcmFormatEnum.u16be: 2,
        MxtanAudioPcmFormatEnum.u16le: 2,
        MxtanAudioPcmFormatEnum.u24be: 3,
        MxtanAudioPcmFormatEnum.u24le: 3,
        MxtanAudioPcmFormatEnum.u32be: 4,
        MxtanAudioPcmFormatEnum.u32le: 4,
        MxtanAudioPcmFormatEnum.s8: 1,
        MxtanAudioPcmFormatEnum.s16be: 2,
        MxtanAudioPcmFormatEnum.s16le: 2,
        MxtanAudioPcmFormatEnum.s24be: 3,
        MxtanAudioPcmFormatEnum.s24le: 3,
        MxtanAudioPcmFormatEnum.s32be: 4,
        MxtanAudioPcmFormatEnum.s32le: 4,
        MxtanAudioPcmFormatEnum.f32be: 4,
        MxtanAudioPcmFormatEnum.f32le: 4,
        MxtanAudioPcmFormatEnum.f64be: 8,
        MxtanAudioPcmFormatEnum.f64le: 8,
    }

    @classmethod
    def width_by_format(cls, pcm_format: MxtanAudioPcmFormatEnum) -> int:
        width = cls.width_map.get(pcm_format)
        if width is None:
            raise MxtanAudioPcmSampleWidthException(f'不存在的Pcm格式类型{pcm_format}')
        return width


# 根据压缩类型，压缩数据
def encode_frame_data(data, compression_format):
    if compression_format == MxtanAudioCompressionEnum.plain:
        return data
    elif compression_format == MxtanAudioCompressionEnum.gzip:
        return gzip.compress(data)
    else:
        print('Error compression_format')
        exit(-1)


def mxtan_audio_encode():
    file_pcm = 'static/BigBuckBunny-stereo-10s.pcm'
    file_ga = 'BigBuckBunny-stereo-10s.ga'
    with open(file_ga, 'wb') as f:
        # 二进制 8
        format_flag = b'MxtanAudio'
        f.write(format_flag)
        # 声道数
        channel = MxtanAudioChannelEnum.stereo
        channel_bytes = channel.to_bytes(1, byteorder='little')
        f.write(channel_bytes)
        # 采样率
        sample_rate = MxtanAudioSampleRateEnum.Hz_48000
        sample_rate_bytes = sample_rate.to_bytes(1, byteorder='little')
        f.write(sample_rate_bytes)
        #  pcm格式
        pcm_format = MxtanAudioPcmFormatEnum.s16le
        pcm_format_bytes = pcm_format.to_bytes(1, byteorder='little')
        f.write(pcm_format_bytes)
        compression_format = MxtanAudioCompressionEnum.gzip
        compression_format_bytes = compression_format.to_bytes(1, byteorder='little')
        f.write(compression_format_bytes)
        # 帧样本数
        frame_samples = 1024
        frame_samples_bytes = frame_samples.to_bytes(2, byteorder='little')
        f.write(frame_samples_bytes)
        # 一帧数据有多少个字节
        sample_width = MxtanAudioPcmSampleWidth.width_by_format(pcm_format)
        frame_data_lengh = frame_samples * channel * sample_width
        print('frame_samples: ', frame_samples)
        print('channel: ', channel)
        print('sample_width: ', sample_width)
        print('frame_data_lengh: ', frame_data_lengh)
        with open(file_pcm, 'rb') as pcm_f:
            while not pcm_f.closed:
                # 帧长度
                # frame_data_lengh_bytes = frame_data_lengh.to_bytes(4, byteorder='little')
                # 帧数据
                frame_data = pcm_f.read(frame_data_lengh)
                if frame_data == b'':
                    break
                # 根据 压缩类型 拿到数据
                frame_data = encode_frame_data(frame_data, compression_format)
                # 帧长度，拿到压缩后的长度
                frame_data_lengh_bytes = len(frame_data).to_bytes(4, byteorder='little')

                f.write(frame_data_lengh_bytes)
                f.write(frame_data)


def main():
    """
    音频文件如何定义
        MxtanAudio
            # 声道
            # 采样率
            # pcm本的 1 1, 1, 1 1 1,
            #  int8表示pcm
            #  uint16
            #   pcm样本格式
            # 压缩算法 pcm数据进行了什么方式的压缩
            # 音频连续, 设计文件的时候
            #  数据帧, 一个数据帧来存多少个采样

            数据长度
            数据
            :return:
    :return:
    """
    # 双声道
    mxtan_audio_encode()
    pass


if __name__ == '__main__':
    main()
