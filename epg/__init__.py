import pygame as pg
from pygame import *
import os
import sys

__version__ = "Test 1.0"

def _throw(s="", t="Invalid"):
    if t:
        s = t + " argument(s) " + str(s)
        
    raise pg.error(s)

def _check_attr(kw, attr):
    bad = set(kw) - set(attr)
    if len(bad) > 0:
        _throw(bad)

def init(size=(0, 0), caption=None, icon=None, fps=60, ime=True, **kw):
    '''Initialize and set the pygame window'''
    global app, clock, game_fps

    if ime:
        os.environ["SDL_IME_SHOW_UI"] = str(ime)
    
    pg.init()
    screen = pg.display.set_mode(size, **kw)
    app = scene.App()

    clock = pg.time.Clock()
    game_fps = fps
    
    if caption:
        pg.display.set_caption(caption)
    if icon:
        pg.display.set_icon(icon)

    return app

def get_path(relative_path):
    '''Return the full path (sys._MEIPASS as the cwd if using pyinstaller)'''
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

def get_assets(path):
    return get_path(os.path.join(assets, path))    

time_offset = 0
def get_time():
    '''Return the game time minus the event.get() loss'''
    return pg.time.get_ticks() - time_offset

def set_caption_as_fps():
    display.set_caption(str(clock.get_fps()))

import epg.locals as locals
import epg.collision as collision
import epg.data as data
import epg.math as math
import epg.mixer as mixer
import epg.image as image
import epg.mask as mask
import epg.action as action
import epg.scene as scene
import epg.font as font
import epg.renderer as renderer
import epg.sprite as sprite

from .font import text_render
from .scene import Scene, AScene
from .sprite import Sprite, Static, AStatic, Dynamic, ADynamic, OsDynamic, OsADynamic
from .mixer import MusicManager, play_music, play_sound

get_image = image.get
get_mask = mask.get
get_sprite = sprite.get
load_image = image.load
load_sheet = image.load_sheet

assets = ""
attr = {}
