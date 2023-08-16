import pygame as pg
from pygame.mixer import *
import epg
import random

class MusicManager:
    def __init__(self, paths, rand=True, gpath=epg.get_assets):
        if gpath:
            self.paths = [gpath(p) for p in paths]
        else:
            self.paths = paths
            
        self.id = 0
        
        if rand:
            random.shuffle(self.paths)

    def update(self):
        if not pg.mixer.music.get_busy():
            pg.mixer.music.load(self.paths[self.id])
            pg.mixer.music.play()
            
            self.id += 1
            if self.id == len(self.paths):
                self.id = 0

    def stop(self, fadeout=200):
        pg.mixer.music.fadeout(fadeout)

def play_music(name, *args, gpath=epg.get_assets, **kw):
    if gpath: name = gpath(name)
    music.load(name)
    music.play(*args, **kw)
    
def play_sound(name, *args, gpath=epg.get_assets, **kw):
    if gpath: name = gpath(name)
    Sound(name).play(*args, **kw)
