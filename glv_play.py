from mxtan_audio import MxtanAudioPcmSampleWidth, MxtanAudioPcmFormatEnum, MxtanAudioSampleRateEnum, MxtanAudioCompressionEnum
from mxtan_m169_player import MxtanFrameTypeEnum, gua_image_decode, gua_diff_decode
from utils import int_to_bytes, int_from_bytes, log, image_from_bytes
from glv import TagTypeEnum
from queue import Queue
from io import BytesIO
from draw_tools import pygame, draw_image
import pyaudio
from mxtan_audio_player import decode_frame_data
import threading
import time


def render_tag_data(f):
    timestamp_bytes = f.read(4)
    timestamp = int_from_bytes(timestamp_bytes)
    tag_type_bytes = f.read(1)
    tag_type = int_from_bytes(tag_type_bytes)
    # log('tag_type', tag_type)
    tag_type = TagTypeEnum(tag_type)
    # log('tag_type', tag_type)
    data_size_bytes = f.read(4)
    data_size = int_from_bytes(data_size_bytes)
    data_bytes = f.read(data_size)
    return tag_type, data_bytes


def render_video_header(data_bytes):
    f = BytesIO(data_bytes)
    header = {}
    flag = f.read(4)
    header['format_flag'] = flag
    version_bytes = f.read(1)
    version = int_from_bytes(version_bytes)
    header['version'] = version
    width_bytes = f.read(2)
    width = int.from_bytes(width_bytes, byteorder='little')
    header['width'] = width
    height_bytes = f.read(2)
    height = int_from_bytes(height_bytes)
    header['height'] = height
    fps_bytes = f.read(1)
    fps = int.from_bytes(fps_bytes, byteorder='little')
    header['fps'] = fps
    # print('flag:', flag)
    # print('version:', version)
    # print('width:', width)
    # print('height:', height)
    # print('fps:', fps)
    return header


def render_video_data(data_bytes, key_frame, width, height):
    f = BytesIO(data_bytes)
    frame_type_bytes = f.read(1)
    frame_type = int_from_bytes(frame_type_bytes)
    frame_type = MxtanFrameTypeEnum(frame_type)
    frame_data = f.read()

    if frame_type == MxtanFrameTypeEnum.I:
        data = gua_image_decode(frame_data)
        key_frame = image_from_bytes(data, width, height)
    elif frame_type == MxtanFrameTypeEnum.P:
        data = gua_diff_decode(frame_data, key_frame)
    return data, key_frame


def render_audio_header(data_bytes):
    f = BytesIO(data_bytes)
    header = {}
    flag = f.read(8)
    header['format_flag'] = flag
    channel_bytes = f.read(1)
    channel = int.from_bytes(channel_bytes, byteorder='little')
    header['channel'] = channel
    # print('channel: ', channel)
    sample_rate_bytes = f.read(1)
    sample_rate = int.from_bytes(sample_rate_bytes, byteorder='little')
    sample_rate = MxtanAudioSampleRateEnum(sample_rate)
    header['sample_rate'] = sample_rate
    # print('sample_rate: ', sample_rate)
    pcm_format_bytes = f.read(1)
    pcm_format = int.from_bytes(pcm_format_bytes, byteorder='little')
    pcm_format = MxtanAudioPcmFormatEnum(pcm_format)
    header['pcm_format'] = pcm_format
    # print('pcm_format: ', pcm_format)
    compression_format_bytes = f.read(1)
    compression_format = int.from_bytes(compression_format_bytes, byteorder='little')
    header['compression_format'] = compression_format
    # plain
    # print('compression_format: ', compression_format)
    frame_simples_bytes = f.read(2)
    frame_simples = int.from_bytes(frame_simples_bytes, byteorder='little')
    header['frame_simples'] = frame_simples
    # print('frame_simples: ', frame_simples)
    return header


class GlvReaderThread(threading.Thread):

    def __init__(self, file_name, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.file_name = file_name
        self.audio_queue = Queue(100)
        self.video_queue = Queue(100)

    def run(self):
        f = open(self.file_name, 'rb')
        flag = f.read(12)
        # log('flag', flag)
        version_bytes = f.read(1)
        version = int_from_bytes(version_bytes)
        # log('version:', version)
        audio_bytes = f.read(1)
        audio = int_from_bytes(audio_bytes)
        # log('audio:', audio)
        video_bytes = f.read(1)
        video = int_from_bytes(video_bytes)
        # log('video', video)

        while True:
            tag_type, data = render_tag_data(f)
            if data == b'':
                break
            elif tag_type == TagTypeEnum.audio:
                self.audio_queue.put(data)
                pass
            elif tag_type == TagTypeEnum.video:
                self.video_queue.put(data)
                pass
        self.audio_queue.put(None)
        self.video_queue.put(None)


class Mxtan169TagDecodeThread(threading.Thread):

    def __init__(self, video_queue, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.video_queue = video_queue
        self.key_frame = None
        self.frame_queue = Queue()
        self.video_header = None

    def render_video_data(self,data_bytes, width, height):
        f = BytesIO(data_bytes)
        frame_type_bytes = f.read(1)
        frame_type = int_from_bytes(frame_type_bytes)
        frame_type = MxtanFrameTypeEnum(frame_type)
        frame_data = f.read()

        if frame_type == MxtanFrameTypeEnum.I:
            data = gua_image_decode(frame_data)
            self.key_frame = image_from_bytes(data, width, height)
        elif frame_type == MxtanFrameTypeEnum.P:
            data = gua_diff_decode(frame_data, self.key_frame)
        return data

    def run(self):
        video_header_bytes = self.video_queue.get()
        video_header = render_video_header(video_header_bytes)
        self.video_header = video_header
        width = video_header['width']
        height = video_header['height']
        while True:
            video_data_bytes = self.video_queue.get()
            if video_data_bytes is None:
                break
            data = self.render_video_data(video_data_bytes, width, height)
            self.frame_queue.put(data)

    def wait_read_header(self):
        while True:
            if self.video_header is not None:
                break


class MxtanAudioPlayThread(threading.Thread):
    def __init__(self, audio_queue, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.audio_queue = audio_queue

    def run(self):
        p = pyaudio.PyAudio()
        # 获取 audio header 内容
        audio_header_bytes = self.audio_queue.get()
        audio_header = render_audio_header(audio_header_bytes)
        #
        sample_width = MxtanAudioPcmSampleWidth.width_by_format(audio_header['pcm_format'])
        pyaudio_format = p.get_format_from_width(sample_width)
        log('pyaudio_format: ', pyaudio_format)
        log('hz', audio_header['sample_rate'].hz)
        stream = p.open(format=pyaudio_format,
                        channels=audio_header['channel'],
                        rate=audio_header['sample_rate'].hz,
                        output=True)
        now = time.time()
        while True:
            frame_data = self.audio_queue.get()
            if frame_data is None:
                break
            frame_data = decode_frame_data(frame_data, audio_header['compression_format'])
            stream.write(frame_data)
            log(f'{time.time() - now:0.2f}', line_feed=False)

        stream.stop_stream()
        stream.close()
        p.terminate()


def decode_flv(file):
    # d = open(file, 'rb')
    with open(file, 'rb') as f:
        # 读取 glv header
        flag = f.read(12)
        # log('flag', flag)
        version_bytes = f.read(1)
        version = int_from_bytes(version_bytes)
        # log('version:', version)
        audio_bytes = f.read(1)
        audio = int_from_bytes(audio_bytes)
        # log('audio:', audio)
        video_bytes = f.read(1)
        video = int_from_bytes(video_bytes)
        # log('video', video)

        # audio_header_tag = render_tag_data(f)
        audio_queue = Queue(500)
        video_queue = Queue(242)
        while True:
            tag_type, data = render_tag_data(f)
            if data == b'':
                break
            elif tag_type == TagTypeEnum.audio:
                audio_queue.put(data)
                pass
            elif tag_type == TagTypeEnum.video:
                video_queue.put(data)
                pass
        audio_queue.put(None)
        video_queue.put(None)

        # 音频解析
        # p = pyaudio.PyAudio()
        #
        # audio_header_bytes = audio_queue.get()
        # audio_header = render_audio_header(audio_header_bytes)
        # sample_width = MxtanAudioPcmSampleWidth.width_by_format(audio_header['pcm_format'])
        # pyaudio_format = p.get_format_from_width(sample_width)
        # print('pyaudio_format: ', pyaudio_format)
        # print('hz', audio_header['sample_rate'].hz)
        # stream = p.open(format=pyaudio_format,
        #                 channels=audio_header['channel'],
        #                 rate=audio_header['sample_rate'].hz,
        #                 output=True)
        # #
        # while True:
        #     frame_data = audio_queue.get()
        #     if frame_data is None:
        #         break
        #     frame_data = decode_frame_data(frame_data, audio_header['compression_format'])
        #     stream.write(frame_data)

        # 视频解析
        video_header_bytes = video_queue.get()
        video_header = render_video_header(video_header_bytes)
        width = video_header['width']
        height = video_header['height']
        fps = video_header['fps']

        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("MxtanVideoPlayer")
        clock = pygame.time.Clock()
        key_frame = None
        while True:
            video_data_bytes = video_queue.get()
            if video_data_bytes is None:
                break
            data, key_frame = render_video_data(video_data_bytes, key_frame, width, height)
            draw_image(screen, width, height, data)
            clock.tick(fps)
            pygame.display.flip()


def decode_flv_thread(glv_file):

    glv_reader_thread = GlvReaderThread(glv_file)
    # 设置daemon 主线程关闭 子线程一起关闭
    glv_reader_thread.setDaemon(True)
    glv_reader_thread.start()
    # 帧解码线程
    # frame_decode_thread = Mxtan169TagDecodeThread(glv_reader_thread.video_queue)
    # frame_decode_thread.setDaemon(True)
    # frame_decode_thread.start()
    # 音频播放线程
    gua_audio_play_thread = MxtanAudioPlayThread(glv_reader_thread.audio_queue)
    gua_audio_play_thread.setDaemon(True)
    gua_audio_play_thread.start()
    # 等待视频头解码 width height 初始化ui的宽高
    # frame_decode_thread.wait_read_header()

    # 视频解析
    # video_header = frame_decode_thread.video_header
    # width = video_header['width']
    # height = video_header['height']
    # fps = video_header['fps']
    # # 初始化窗口
    # screen = pygame.display.set_mode((width, height))
    # pygame.display.set_caption("MxtanVideoPlayer")
    # clock = pygame.time.Clock()
    # running = True
    # # 缓冲10帧数据
    # while frame_decode_thread.frame_queue.qsize() < 10:
    #     continue

    # 视频解析
    video_header_bytes = glv_reader_thread.video_queue.get()
    video_header = render_video_header(video_header_bytes)
    width = video_header['width']
    height = video_header['height']
    fps = video_header['fps']
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("MxtanVideoPlayer")
    clock = pygame.time.Clock()
    running = True
    key_frame = None
    # while glv_reader_thread.video_queue.qsize() < 10:
    #     continue
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        video_data_bytes = glv_reader_thread.video_queue.get()
        if video_data_bytes is None:
            break
        data, key_frame = render_video_data(video_data_bytes, key_frame, width, height)
        draw_image(screen, width, height, data)
        clock.tick(fps)
        pygame.display.flip()

    # while running:
    #     if not frame_decode_thread.frame_queue.empty():
    #         break
    #     data = frame_decode_thread.frame_queue.get()
    #     draw_image(screen, width, height, data)
    #     clock.tick(fps)
    #     pygame.display.flip()
    #
    #     for event in pygame.event.get():
    #         if event.type == pygame.QUIT:
    #             running = False

def main():
    glv_file = 'BigBuckBunny-new.glv'
    # decode_flv(glv_file)
    decode_flv_thread(glv_file)


if __name__ == '__main__':
    main()
