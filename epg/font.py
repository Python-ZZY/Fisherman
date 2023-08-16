import pygame as pg
import epg
from functools import lru_cache
from pygame.font import *

default_font = None
def set_default(font, gpath=epg.get_assets):
    global default_font
    default_font = gpath(font) if gpath else font

@lru_cache(10)
def load(font=None, size=None):
    if not font:
        font = default_font
    if size is None:
        if isinstance(font, pg.Font):
            return font
        size = 20
    
    return Font(font, size)

def text_render(text, size=20, color=(255, 255, 255), antialias=True, font=None, func=None, **kw):
    f = load(font, size)
    if func: func(f)
    return f.render(text, antialias, color, **kw)
