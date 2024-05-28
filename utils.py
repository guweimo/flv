from datetime import datetime
import threading
from PIL import Image


def log(*args, **kwargs):
    line_feed = True
    if 'line_feed' in kwargs:
        line_feed = kwargs.pop('line_feed')
    if not line_feed:
        print(f'\r{datetime.now()}', threading.current_thread(), *args, **kwargs, flush=True, end='')
    else:
        print(datetime.now(), threading.current_thread(), *args, **kwargs, flush=True)


def int_to_bytes(value: int, width: int):
    bytes_list = value.to_bytes(width, byteorder='little')
    return bytes_list


def int_from_bytes(value: bytes):
    number = int.from_bytes(value, byteorder='little')
    return number

def image_from_bytes(path, width, height):
    img = Image.frombytes('RGB', (width, height), path)
    return img