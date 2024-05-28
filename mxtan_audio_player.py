import pyaudio

from mxtan_audio import MxtanAudioPcmSampleWidth, MxtanAudioPcmFormatEnum, MxtanAudioSampleRateEnum, MxtanAudioCompressionEnum

import gzip


# 根据压缩算法解码
def decode_frame_data(data, compression_format):
    if compression_format == MxtanAudioCompressionEnum.plain:
        return data
    elif compression_format == MxtanAudioCompressionEnum.gzip:
        return gzip.decompress(data)
    else:
        print('Error compression_format')
        exit(-1)


def main():
    #
    p = pyaudio.PyAudio()
    #
    mxtan_audio_file = 'BigBuckBunny-stereo-10s.ga'
    with open(mxtan_audio_file, 'rb') as f:
        # mxtan audio 的 header
        flag = f.read(8)
        print('flag: ', flag)
        channel_bytes = f.read(1)
        channel = int.from_bytes(channel_bytes, byteorder='little')
        print('channel: ', channel)
        sample_rate_bytes = f.read(1)
        sample_rate = int.from_bytes(sample_rate_bytes, byteorder='little')
        sample_rate = MxtanAudioSampleRateEnum(sample_rate)
        print('sample_rate: ', sample_rate)
        pcm_format_bytes = f.read(1)
        pcm_format = int.from_bytes(pcm_format_bytes, byteorder='little')
        pcm_format = MxtanAudioPcmFormatEnum(pcm_format)
        print('pcm_format: ', pcm_format)
        compression_format_bytes = f.read(1)
        compression_format = int.from_bytes(compression_format_bytes, byteorder='little')
        # plain
        print('compression_format: ', compression_format)
        frame_samples = f.read(2)
        print('frame_samples: ', int.from_bytes(frame_samples, byteorder='little'))
        # 处理数据帧
        # 系统音频的api需要知道我后续pcm的基本的信息
        sample_width = MxtanAudioPcmSampleWidth.width_by_format(pcm_format)
        pyaudio_format = p.get_format_from_width(sample_width)
        print('pyaudio_format: ', pyaudio_format)
        print('hz', sample_rate.hz)
        stream = p.open(format=pyaudio_format,
                        channels=channel,
                        rate=sample_rate.hz,
                        output=True)
        while not f.closed:
            frame_data_length_bytes = f.read(4)
            if frame_data_length_bytes == b'':
                # 退出
                break
            frame_data_length = int.from_bytes(frame_data_length_bytes, byteorder='little')
            print('frame_data_length_bytes', frame_data_length_bytes)
            print('frame_data_length', int.from_bytes(frame_data_length_bytes, byteorder='little'))
            frame_data = f.read(frame_data_length)
            # 解压数据
            frame_data = decode_frame_data(frame_data, compression_format)
            # 读到了音频帧数据
            stream.write(frame_data)
            print('frame_data: ', frame_data)


if __name__ == '__main__':
    main()