import epg
import asyncio

class App:
    def __init__(self, screen=None, scene=None):
        self.screen = screen if screen else epg.display.get_surface()
        self.scene = scene
        self.attr = {}
        self.cached = {}
        self.app_running = False

    def __getitem__(self, key):
        return self.attr[key]

    def __setitem__(self, key, value):
        self.attr[key] = value

    def cache(self, scene, name):
        self.cached[name] = scene

    def run(self, scene=None):
        asyncio.run(self.async_run(scene))
        
    async def async_run(self, scene=None):
        if scene: self.switch(scene)

        self.app_running = True
        while self.app_running:
            scene = self.scene

            self.scene.scene_running = True
            while self.scene.scene_running:
                self.scene.single_run()
                await asyncio.sleep(0)
                
            if self.scene == scene: self.quit()

    def quit(self):
        self.app_running = False
        self.scene.quit()

    def switch(self, scene, sync_screen=True):
        if not isinstance(scene, Scene):
            try:
                scene = self.cached[scene]
            except KeyError:
                epg._throw("No scene found", "")

        if self.scene: 
            self.scene.quit()
            if sync_screen: 
                self.scene.screen = scene.screen
        self.scene = scene

class Scene(epg.Rect):
    def __init__(self, screen=None, music=None, _init=True):
        self.screen = screen if screen else epg.app.screen
        super().__init__(self.screen.get_rect())

        self.scene_running = False
        self.music_manager = None
        self.funcs = {}
        self.groups = {}

        if music:
            self.set_music(music)
        if _init:
            self.init()

    def __eq__(self, value):
        return self is value

    def run(self):
        self.scene_running = True
        while self.scene_running:
            self.single_run()
            
    def single_run(self):
        for sendarg, func in self.funcs.values():
            if sendarg:
                func(self)
            else:
                func()
        
        self.update()
        self._draw()
        
        now = epg.time.get_ticks()
        for event in epg.event.get():
            if event.type == epg.QUIT:
                self.onexit()
            else:
                self.events(event)
        epg.time_offset += epg.time.get_ticks() - now
        
        epg.clock.tick(epg.game_fps)
        epg.display.flip()

    def add_func(self, func, name=None, sendarg=False):
        if not name: name = func
        self.funcs[name] = (sendarg, func)

    def get_func(self, name):
        return self.funcs[name][1]
    
    def del_func(self, name):
        del self.funcs[name]
        
    def add_group(self, *names, pref="group_", asattr=True):
        keys = tuple(self.groups)
        for name in names:
            if name in keys:
                epg._throw("Group %s already exists"%name, "")
            self.groups[name] = g = epg.sprite.Group()
            if asattr: setattr(self, pref + str(name), g)
        return g

    def get_group(self, name):
        return self.groups[name]
    
    def del_group(self, *names, pref="group_", asattr=True):
        for name in names:
            try:
                del self.groups[name]
            except KeyError:
                epg._throw("Group %s does not exist"%name, "")
            if asattr: delattr(self, pref + str(name), g)

    def do_group(self, func):
        for group in self.groups.values():
            func(self, group)
    
    def draw_group(self):
        for group in self.groups.values():
            for sprite in group:
                sprite.draw(self.screen)

    def draw_group_with_offset(self, offset):
        for group in self.groups.values():
            for sprite in group:
                sprite.draw_with_offset(self.screen, offset)

    def update_group(self):
        for group in self.groups.values():
            group.update()

    def set_music(self, *paths, **kw):
        self.music_manager = epg.MusicManager(paths, **kw)
        self.add_func(self.music_manager.update, "music_manager")

    def switch(self, scene, cache=None):
        if cache:
            epg.app.cache(self, cache)
        epg.app.switch(scene)

    def init(self):
        pass

    def onexit(self):
        self.quit()
        
    def quit(self):
        self.scene_running = False

    def _draw(self):
        self.draw()

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.draw_group()
    
    def update(self):
        self.update_group()

    def events(self, event):
        pass

class AScene(Scene, epg.action.ActionObject):
    def __init__(self, screen=None, music=None, bg=(0, 0, 0), end_func=None):
        Scene.__init__(self, screen, music, _init=False)
        epg.action.ActionObject.__init__(self, None, end_func)
        self.real_screen = self.screen
        self.screen = self.screen.copy()
        self.bg = bg
        self.orig_image, self.orig_rect = self.screen, self.copy()
        self.image, self.rect = self.orig_image, self.orig_rect
        self.init()

    def end(self):
        self.end_func, self.manager = None, None
        self.single_run = lambda: Scene.single_run(self)
        self._draw = lambda: Scene._draw(self)
        self.screen = self.real_screen
        del self.real_screen

    def kill(self):
        self.quit()

    def single_run(self):
        epg.action.ActionObject.update(self)
        self.screen = self.image
        Scene.single_run(self)

    def _draw(self):
        self.real_screen.fill(self.bg)
        self.draw()
        self.real_screen.blit(self.screen, self.rect)

    def update(self):
        epg.action.ActionObject.update(self)
        Scene.update(self)