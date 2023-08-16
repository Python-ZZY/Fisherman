import pygame as pg
import epg
from pygame.sprite import *

class Sprite(Sprite):
    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def draw_with_offset(self, screen, offset):
        screen.blit(self.image, epg.Vector2(self.rect.topleft) + offset)

    def sync_rect(self):
        if (r := getattr(self, "orig_rect", None)) is not None:
            r.update(self.rect)
        if (ui := getattr(self, "ui", None)) is not None:
            self.ui.box.update(self.rect)

    def move(self, offset):
        self.rect.topleft += offset
        self.sync_rect()

    def move_to(self, pos, anchor="topleft"):
        setattr(self.rect, anchor, pos)
        self.sync_rect()

    def update_image(self, surf):
        self.image = surf
        if hasattr(self, "orig_image"):
            self.orig_image = surf

class Static(Sprite):
    def __init__(self, surf, groups=(), **rectkw):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(**rectkw)

class AStatic(Static, epg.action.ActionObject):
    def __init__(self, surf, *actions, end_func=None, **statickw):
        Static.__init__(self, surf, **statickw)
        self.orig_image, self.orig_rect = self.image, self.rect.copy()
        
        epg.action.ActionObject.__init__(self, actions, end_func)
        self.update()
    
    def end(self):
        '''Degenerate self into normal Static (no longer handle actions)'''
        del self.end_func, self.manager
        self.update = lambda: Static.update(self)
        self.act = None

    def update(self):
        Static.update(self)
        epg.action.ActionObject.update(self)

class BaseDynamic(Sprite):
    def __init__(self, types, groups=(), state=None, total=None,
                 anchor="center", **rectkw):
        super().__init__(*groups)
        
        self.types, self.state, self.total, self.anchor = types, state, total, anchor
        self.now_total = 1
            
        if not state:
            self.state = tuple(self.types.keys())[0]
        self.state_changed = False

        self.orig_image = self.image = self.animation.get_surface()
        self.rect = self.image.get_rect(**rectkw)
        self.orig_rect = self.rect.copy()

    @property
    def animation(self):
        return self.types[self.state]

    def update(self):
        '''Update the animation. Return True if the image has changed'''
        if i := self.animation.update(self.state_changed):
            self.state_changed = False
            self.orig_image = self.image = i

            if self.animation.id == 0 and self.total != None:
                self.now_total += 1
            
            arg = getattr(self.orig_rect, self.anchor)
            self.rect.size = self.image.get_size()
            setattr(self.rect, self.anchor, arg)

            if self.total != None and self.now_total > self.total:
                self.kill()

            return True
        
    def update_state(self, state, sync_rect=True):
        if state != self.state:
            self.types[state].id = 0
            self.state = state

            if sync_rect:
                self.sync_rect()

            self.state_changed = True
            BaseDynamic.update(self)

class Dynamic(BaseDynamic):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.update()
        
class ADynamic(BaseDynamic, epg.action.ActionObject):
    def __init__(self, types, *actions, end_func=None, **dynamickw):
        BaseDynamic.__init__(self, types, **dynamickw)
        epg.action.ActionObject.__init__(self, actions, end_func)
    
    def end(self):
        '''Degenerate self into normal Dynamic (no longer handle actions)'''
        del self.end_func, self.manager
        self.update = lambda: BaseDynamic.update(self)
        self.act = None

    def update(self):
        BaseDynamic.update(self)
        epg.action.ActionObject.update(self)
        
def OsDynamic(animation, *args, **kw):
    return Dynamic({"":animation}, *args, **kw)

def OsADynamic(animation, *args, **kw):
    return ADynamic({"":animation}, *args, **kw)

def get(obj, cls=OsDynamic, *clsargs, **clskw):
    if isinstance(obj, epg.Surface):
        obj = epg.image.StaticAnimation(obj)
    if isinstance(obj, epg.image.Animation):
        obj = cls(obj, *clsargs, **clskw)
    elif not isinstance(obj, Sprite):
        epg._throw("Invalid type "+repr(type(obj)), "")
        
    return obj

def get_static(actions, *args, **kwargs):
    if actions is None: actions = ()
    return AStatic(*args, *actions, **kwargs) if actions or actions == () else Static(*args, **kwargs)

def get_dynamic(actions, *args, **kwargs):
    if actions is None: actions = ()
    return ADynamic(*args, *actions, **kwargs) if actions or actions == () else Dynamic(*args, **kwargs)
