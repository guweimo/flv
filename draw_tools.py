import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ''
import pygame


def draw_image(screen, width, height, image_bytes: bytes):
    size = (width, height)
    py_image = pygame.image.frombuffer(image_bytes, size, 'RGB')
    image_rect = py_image.get_rect()
    screen.blit(py_image, image_rect)
