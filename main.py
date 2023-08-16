try:
	import pyi_splash
	pyi_splash.close()
except ImportError:
	pass

import epg
import random
import math
from epg.action import *
from configs import *

__version__ = VERSION

def randcolor():
	return [random.randint(0, 255) for i in range(3)] + \
	[random.randint(200, 255)]

def get_sth(lst, *args, **kw):
	lv = epg.attr["game"].level.level
	idxs = [i for i in range(len(lst)) if lv >= lst[i][1]]
	return eval(random.choices([lst[i][0] for i in idxs], [lst[i][2] for i in idxs])[0])

def get_fish():
	return get_sth(FISH)

def get_activity():
	return get_sth(ACTIVITIES)

def text_render(*text, pad=10, **kw):
	surf = epg.renderer.renders(*[[t] for t in text], bgcolor=(0, 0, 0, 100), anchor="center",
		lnstyle=epg.renderer.Style(textstyle=epg.renderer.Style(padx=pad, pady=pad, **kw)))
	return surf

class Score(epg.AStatic):
	def __init__(self):
		self.game = epg.attr["game"]
		self.score = self.game.score
		self.incr_score = 0

		self.incr_action = Shake(200, dist=(2, 2)) * 2
		self.decr_action = (FadeOut(100) >> FadeIn(100)) * 2
		super().__init__(self.get_score_image())

		h = self.image.get_height()
		self.fadeout_action = MoveBy(400, range=(0, -h), cover=False)
		self.fadein_action = MoveBy(0, range=(0, -h)) >> MoveBy(400, range=(0, h), cover=False)

	def get_score_image(self):
		return text_render("$ " + str(round(self.score - self.incr_score, 1)), size=18)

	def increase(self, x):
		x = round(x, 1)
		if x == 0:
			return
		elif x > 0:
			self.incr_score += x
			self.incr_step = round(x / 20, 3)
			self.act(self.incr_action)
		else:
			self.act(self.decr_action)

		self.score += x
		if self.score < 0:
			self.score = 0.0

		self.update_image(self.get_score_image())
		if self.game.level.update_level():
			self.game.level.update_level_image()

	def update(self):
		super().update()

		if self.incr_score:
			self.incr_score -= self.incr_step
			if self.incr_score < 0:
				self.incr_score = 0

			self.update_image(self.get_score_image())

class Level(epg.AStatic):
	def __init__(self):
		self.game = epg.attr["game"]
		self.level = -1

		self.update_level()
		super().__init__(self.get_level_image())
		self.update_image(self.get_level_image())

	@property
	def score(self):
		return self.game.score.score
	
	@property
	def reach_max_level(self):
		return self.level == (len(SCORE_REQUIREMENT) - 1)

	def level_up(self):
		t = ["LEVEL UP!", f"Current Level:{self.level}"]

		newf = [fish[0] for fish in FISH if fish[1] == self.level]
		if newf:
			plural = "s" if len(newf) > 1 else ""
			t += [f"Unlock {len(newf)} type{plural} of new fish:", ", ".join(newf)]

		self.game.showinfo(*t, time=3000)

	def update_image(self, image):
		super().update_image(image)
		self.rect = self.image.get_rect()
		self.sync_rect()
		self.move_to((WIDTH, 0), anchor="topright")

	def get_level_image(self):
		t = " (MAX)" if self.reach_max_level else ""
		return text_render(f"Lv.{self.level}" + t, size=18)

	def update_level(self):
		for i, score in enumerate(SCORE_REQUIREMENT):
			lv = len(SCORE_REQUIREMENT) - i - 1
			if self.score >= score:
				if lv > self.level:
					self.level = lv
					return True
				break

	def update_level_image(self):
		self.level_up()
		self.update_image(self.get_level_image())

	def draw(self, screen):
		super().draw(screen)

		pos = epg.mouse.get_pos()
		if self.rect.collidepoint(pos):
			if self.reach_max_level:
				t = "Reach Max Level"
			else:
				t = f"Next Level Requires ${SCORE_REQUIREMENT[::-1][self.level + 1]}"
			r = text_render(t, size=15)
			screen.blit(r, r.get_rect(topright=self.rect.bottomright))

class GameTip(epg.AStatic):
	def __init__(self):
		super().__init__(none_surface)

	def show(self, *text, time=1200, fadetime=300):
		self.update_image(text_render(*text, size=16, wraplength=int(WIDTH * 0.75)))
		self.rect = self.image.get_rect(center=CENTER)
		self.sync_rect()
		self.act(FadeIn(fadetime) >> Delay(time) >> FadeOut(fadetime))

class StartTip(epg.AStatic):
	def __init__(self):
		surf = epg.text_render("Press <Spacebar> to Start Game", size=20)
		self.action = (FadeIn(400) >> Delay(800) >> FadeOut(400)) * math.inf
		self.fadeout_action = MoveBy(400, range=(0, HEIGHT * 0.2)) >> Kill()
		self.fadein_action = MoveBy(range=(0, HEIGHT * 0.2)) >> MoveBy(400, range=(0, -HEIGHT * 0.2)) >> self.action
		super().__init__(surf, self.action, centerx=CENTER[0], y=HEIGHT * 0.8)

class Floatage(epg.AStatic):
	def __init__(self, surf, speed, cx):
		self.speed = speed

		if self.speed > 0:
			super().__init__(surf, right=0, centery=cx)
		else:
			super().__init__(surf, x=WIDTH, centery=cx)
		self.rect = self.orig_rect = epg.FRect(self.rect)

	def update(self):
		super().update()
		self.move(vec(self.speed, 0))
		if not -150 < self.rect.centerx < WIDTH + 150:
			self.kill()
		elif self.speed == 0 and (self.rect.right < 0 or self.rect.x > WIDTH):
			self.kill()

class CommonFish(Floatage):
	'''No description'''

	SIZE = (10, 40)
	K = 2

	def __init__(self, direction=None):
		self.game = epg.attr["game"]

		s = random.randint(*self.SIZE)
		size = [random.randint(s, s * self.K) for i in range(2)]
		size.sort(reverse=True)

		speed = random.uniform(-2, 2)
		if direction:
			speed = abs(speed) * direction

		self._score = int(abs(speed) + size[0] + size[1]) / 30

		surf = epg.Surface(size).convert_alpha()
		surf.fill((0, 0, 0, 0))

		surf.lock()
		surf = self.get_surface(surf, speed)
		surf.unlock()

		super().__init__(surf, speed, random.randint(SKYHEIGHT + 20, HEIGHT - SKYHEIGHT))
		self.alive = True

		self.init()

	@property
	def score(self):
		return self._score
	
	@classmethod
	def get_surface(cls, surf, speed):
		epg.draw.ellipse(surf, randcolor(), surf.get_rect())
		return surf

	def do_score(self, a):
		self.game.score.increase(self.score)

	def init(self):
		pass

	def fadeout(self):
		self.alive = False
		self.act(MoveTo(1000, range=(CENTER[0], SKYHEIGHT), anchor="center") >> FadeOut(200) >> \
			self.do_score >> Kill())

class RareFish(CommonFish):
	'''Rare fish cannot appear in fish rush'''
	RUSH_FISH_RATE = 0.35

	def __init__(self, *args, **kw):
		super().__init__(*args, **kw)

		if self.game.fish_rate == self.RUSH_FISH_RATE:
			self.alive = False
			super().kill()

class GoldFish(CommonFish):
	'''They are very valuable. Each sells 10 times as much money as the common fish.'''

	@property
	def score(self):
		epg.play_sound("gold_fish.ogg")
		return self._score * 10

	@classmethod
	def get_surface(cls, surf, speed):
		epg.draw.rect(surf, (255, 215, 0, random.randint(200, 255)), surf.get_rect())
		return surf

	def init(self):
		if self.speed > 0:
			self.speed += 1.5
		else:
			self.speed -= 1.5

class ThornFish(CommonFish):
	'''	They're very dangerous. There is no money to be gained from catching them, but there is a loss.'''

	@property
	def score(self):
		epg.play_sound("thorn_fish.ogg")
		return -self._score * 3

	@classmethod
	def get_surface(cls, surf, speed):
		w, h = surf.get_size()
		epg.draw.polygon(surf, randcolor(), ((0, h * 0.5), (w * 0.25, 0), (w * 0.75, h), 
			(w, h * 0.5), (w * 0.75, 0), (w * 0.25, h)))
		return surf

	def fadeout(self):
		self.alive = False
		self.act(Shake(100, dist=(2, -2)) * 2 >> FadeOut(200) >> self.do_score >> Kill())

class FastFish(CommonFish):
	'''They swim fast, so they sell for five times the price of the common fish.'''

	@property
	def score(self):
		return self._score * 5

	@classmethod
	def get_surface(cls, surf, speed):
		w, h = surf.get_size()
		epg.draw.polygon(surf, randcolor(), ((0, 0), (0, h), (w, h * 0.5)))
		if speed < 0:
			surf = epg.transform.flip(surf, True, False)
		return surf

	def init(self):
		if self.speed > 0:
			self.speed += 4
		else:
			self.speed -= 4

class BombFish(CommonFish):
	'''They will explode when caught, killing fish around, but they won't cause you to lose your money.'''

	@property
	def score(self):
		return 0

	@classmethod
	def get_surface(self, surf, speed):
		w, h = surf.get_size()
		epg.draw.ellipse(surf, (255, 0, 0), surf.get_rect())
		epg.draw.ellipse(surf, (125, 0, 0), (w / 4, h / 4, w / 2, h / 2))
		return surf

	def _explode(self, *args):
		self.game.act(Shake(100, dist=(-2, 2)))
		epg.play_sound("bomb_fish.ogg")

		self.radius = self._score * 80
		for fish in self.game.group_fish:
			if epg.sprite.collide_circle(self, fish) and fish != self:
				fish.alive = False
				fish.act(FadeOut(300) >> Kill())

	def fadeout(self):
		self.alive = False
		self.act((FadeIn(50) >> FadeOut(50)) * int(self._score ** 1.5) >> self._explode >> Kill())

class FishKing(RareFish):
	'''When a fish king is caught, there will be a rush of fish.'''

	@property
	def score(self):
		return 0

	@classmethod
	def get_surface(self, surf, speed):
		w, h = surf.get_size()
		w2, h2 = w / 2, h / 2
		c = (255, 255, 255, random.randint(100, 255))
		for rect in ((0, 0, w2, h2), (w2, 0, w2, h2), (w2, h2, w2, h2), (0, h2, w2, h2)):
			epg.draw.ellipse(surf, c, rect)

		return surf

	def kill(self):
		super().kill()
		self.game.fish_rate = FISH_RATE

	def affect(self, s):
		self.game.fish_rate = self.RUSH_FISH_RATE

	def fadeout(self):
		self.alive = False
		epg.play_sound("fish_king.ogg")
		a = (ScaleBy(100, range=(1, 1.1), cover=False) >> \
			ScaleBy(100, range=(1.1, 1), cover=False)) * 2 >> Fade(100, range=(100, 50)) >> \
			self.affect >> Delay(int(self._score * 1000)) >> Kill()
		self.act(a)

class IceFish(CommonFish):
	'''When it dies, the fish around it will be frozen.'''

	@property
	def score(self):
		return 0

	@classmethod
	def get_surface(self, surf, speed):
		w, h = surf.get_size()
		epg.draw.rect(surf, (0, 255, 255), surf.get_rect())
		epg.draw.rect(surf, (200, 200, 255), (w / 4, h / 4, w / 2, h / 2))
		return surf

	def _explode(self, *args):
		self.game.act(Shake(100, dist=(-2, 2)))
		epg.play_sound("ice_fish.ogg")

		self.radius = self._score * 50
		for fish in self.game.group_fish:
			if fish.alive and epg.sprite.collide_circle(self, fish) and fish != self:
				surf = epg.mask.from_surface(fish.image).to_surface(setcolor=(0, 255, 255), 
					unsetcolor=(0, 0, 0, 0))
				fish.image.blit(surf, (0, 0))
				fish.update_image(fish.image)
				fish.speed = 0

	def fadeout(self):
		self.alive = False
		self.act((FadeIn(50) >> FadeOut(50)) * int(self._score ** 1.5) >> self._explode >> Kill())

class Shark(ThornFish):
	'''They will kill fish that are slower and smaller. Also, you cannot catch them.'''

	@property
	def score(self):
		return -self._score * 5

	@classmethod
	def get_surface(cls, surf, speed):
		w, h = surf.get_size()
		c = randcolor()
		epg.draw.ellipse(surf, c, (0, 0, w / 2, h))
		epg.draw.polygon(surf, c, ((w / 2, 0), (w, h / 4), (w / 2, h / 2)))
		epg.draw.polygon(surf, c, ((w / 2, h / 2), (w, h / 4 * 3), (w / 2, h)))
		if speed < 0:
			surf = epg.transform.flip(surf, True, False)
		return surf

	def init(self):
		self.speed *= 1.5

	def update(self):
		super().update()
		if self.alive:
			for fish in self.game.group_fish:
				if fish.alive and self.rect.colliderect(fish.rect) and fish != self and \
				abs(self.speed) > abs(fish.speed) and self._score * 1.5 > fish._score:
					fish.speed //= 10
					fish.alive = False
					fish.act(Shake(80, dist=(2, -2)) * 2 >> ScaleBy(120, range=(1, 0)) >> Kill())
					epg.play_sound("shark_attack.ogg")

def FishRush(game, fish=None, num=(10, 20)):
	'''Armies of fish are coming!'''
	d = random.choice((-1, 1))

	if not fish:
		fish = random.choice([ThornFish, FastFish])

	for i in range(random.randint(*num)):
		game.add_fish(fish, direction=d)

def CommonFishRush(game):
	'''Armies of fish are coming!'''
	FishRush(game, CommonFish)

def GoldFishRush(game):
	'''Here come the Gold Fish! Don't let them go away!'''
	FishRush(game, GoldFish, (5, 10))

def SharkRush(game):
	'''Watch out the sharks!'''
	for d in (1, -1):
		for i in range(random.randint(8, 15)):
			game.add_fish(Shark, direction=d)

def VortexAppear(game):
	'''A vortex has appeared!'''
	pos = random.randint(100, WIDTH - 100), random.randint(SKYHEIGHT + 100, HEIGHT - 100)
	a = MoveTo(1000, range=pos, anchor="center") >> ScaleBy(120, range=(1, 0)) >> Kill()
	for fish in game.group_fish:
		fish.alive = False
		fish.act(a)
	epg.play_sound("vortex.ogg")

class Cloud(Floatage):
	def __init__(self):
		size = random.randint(30, 80), random.randint(5, 10)
		surf = epg.Surface(size).convert_alpha()
		surf.fill((0, 0, 0, 0))
		surf.set_alpha(random.randint(100, 200))
		epg.draw.ellipse(surf, (255, 255, 255), surf.get_rect())

		super().__init__(surf, random.uniform(-1, 1), random.randint(SKYHEIGHT // 4, SKYHEIGHT // 2))

	def draw(self, screen):
		screen.blit(self.image, self.rect)

class Star(epg.AStatic):
	def __init__(self):
		self.alive = True
		s = random.randint(2, 4)
		surf = epg.Surface((s, s))
		surf.fill((255, 255, 255))
		super().__init__(surf, center=(random.randint(0, WIDTH), random.randint(0, SKYHEIGHT // 3)))
		self.update_action()

	def update_action(self, *args):
		time = random.randint(1000, 3000)
		self.action = FadeIn(time) >> Delay(time) >> FadeOut(time) >> self.update_action
		self.act(self.action)

	def fadeout(self):
		self.alive = False
		self.act(FadeOut(random.randint(500, 1000)) >> Kill())

class Boat(epg.Static):
	def __init__(self):
		w, h = WIDTH // 4, SKYHEIGHT // 1.5
		surf = epg.Surface((w, h)).convert_alpha()
		surf.fill((0, 0, 0, 0))

		surf.lock()
		r = 12
		epg.draw.circle(surf, (255, 180, 100), (w * 0.5, r), r)
		epg.draw.polygon(surf, (180, 100, 100), ((w * 0.5 - r, 2 * r), (w * 0.5 + r, 2 * r), (w * 0.66, h * 0.5), (w * 0.33, h * 0.5)))
		epg.draw.polygon(surf, (255, 255, 0), ((0, h * 0.5), (w, h * 0.5), (w * 0.75, h), (w * 0.25, h)))
		surf.unlock()

		super().__init__(surf, centerx=CENTER[0], bottom=SKYHEIGHT + h / 3)

		self.group_fish = epg.sprite.Group()

	def draw_line(self, screen, offset):
		epg.draw.line(screen, (255, 255, 255), self.rect.center, epg.mouse.get_pos(), width=3)
		for fish in self.group_fish:
			epg.draw.line(screen, (255, 255, 255), self.rect.center, fish.rect.center, width=3)

class Sky(epg.AScene):
	def init(self):
		self.colors = [(128, 255, 255), (64, 255, 255), (255, 128, 0), (0, 0, 128)]
		self.period = 1
		self.pos = 0
		self.pos_i = SKY_RATE
		self.add_group("star")
		self.add_group("cloud")
		self.set_music("bgm0.ogg", "bgm1.ogg")

		self.group_cloud.add(Cloud())

	def increase_period(self):
		self.period = (self.period + 1) % len(self.colors)

	def in_period(self, idx):
		return (self.period == idx % len(self.colors) and self.pos > 0.6) or \
		(self.period == (idx + 1) % len(self.colors) and self.pos < 0.4)

	def update(self):
		self.color = epg.math.mix(self.colors[self.period - 1], 
								  self.colors[self.period], 
								  self.pos)

		self.pos += self.pos_i
		if self.pos > 1:
			self.pos = 0
			self.increase_period()

		if self.in_period(3):
			if not self.group_star:
				for i in range(random.randint(3, 8)):
					self.group_star.add(Star())
		else:
			for star in self.group_star:
				if star.alive:
					star.fadeout()
				else:
					break

		if random.random() < 0.0025:
			self.group_cloud.add(Cloud())

		self.update_group()

	def draw(self):
		self.screen.fill(self.color)

class Bg(Sky):
	def init(self):
		super().init()

		self.background = epg.Surface((WIDTH, HEIGHT - SKYHEIGHT + 20)).convert_alpha()
		self.background.fill((0, 0, 255, 100))
		self.boat = Boat()
		self.fish_rate = FISH_RATE

		self.add_group("fish")

	def add_fish(self, fish, *args, **kw):
		fish = fish(*args, **kw)
		if fish.alive:
			self.group_fish.add(fish)

	def add_activity(self, ac, *args, **kw):
		if hasattr(self, "showinfo"):
			self.showinfo(ac.__doc__)
		ac(self, *args, **kw)

	def update(self):
		super().update()

		if random.random() < self.fish_rate:
			self.add_fish(get_fish())			

	def draw_user_event(self, offset):
		pass

	def draw(self):
		super().draw()
		now = epg.get_time()
		self.boat.draw_with_offset(self.screen, offset := vec(0, math.sin(now / 2000) * 3))
		self.draw_user_event(offset)
		self.screen.blit(self.background, (0, SKYHEIGHT + math.sin(now / 2000) * 5))
		self.draw_group()

class Game(Bg):
	def __init__(self):
		epg.attr["game"] = self
		self.score = epg.data.load(default=0.0)

		super().__init__()

	def init(self):
		super().init()

		g = self.add_group("info")
		self.score = Score()
		self.level = Level()
		self.game_tip = GameTip()
		self.start_tip = StartTip()
		g.add(self.score, self.level, self.game_tip)

		self.stop()

	def increase_period(self):
		super().increase_period()
		self.add_activity(get_activity())

	def showinfo(self, *args, **kw):
		self.game_tip.show(*args, **kw)

	def start(self):
		self.in_game = True
		self.score.act(a := self.score.fadein_action)
		self.level.act(a)
		self.start_tip.act(self.start_tip.fadeout_action)

		self.update()

	def stop(self):
		epg.data.dump(self.score.score)

		self.in_game = False
		self.score.act(a := self.score.fadeout_action)
		self.level.act(a)
		self.start_tip.act(self.start_tip.fadein_action)
		self.group_info.add(self.start_tip)

		self.update()

	def onexit(self):
		if self.in_game:
			self.stop()
		else:
			super().onexit()

	def events(self, event):
		if event.type == epg.MOUSEBUTTONDOWN:
			if self.in_game and event.button == 1:
				for fish in self.group_fish.sprites():
					if fish.rect.collidepoint(event.pos):
						if fish.alive:
							self.boat.group_fish.add(fish)
							fish.fadeout()
							epg.play_sound("click.ogg")

		elif event.type == epg.KEYDOWN:
			if event.key == epg.K_ESCAPE:
				self.onexit()

			elif event.key == epg.K_SPACE:
				if not self.in_game:
					self.start()

	def draw_user_event(self, offset):
		if self.in_game:
			self.boat.draw_line(self.screen, offset)

class Splash(epg.AScene):
    def init(self):
        self.add_group("all")
        self.group_all.add(epg.sprite.Static(epg.image.load("splash.png")))
        playsound = Delay(800) >> (lambda *a: epg.play_sound("splash.ogg"))
        self.act(FadeIn(2000) + playsound >> Delay(2200) >> FadeOut(2000) >> Kill())

    def onexit(self):
    	raise SystemExit

def main():
	epg.assets = "assets"
	epg.data.default_path = "savefile"
	epg.font.set_default("font.ttf")

	epg.mixer.pre_init()
	app = epg.init((WIDTH, HEIGHT), caption=APPNAME + " v" + VERSION, icon=epg.load_image("icon.png"))

	cursor = epg.Surface((32, 32)).convert_alpha()
	cursor.fill((0, 0, 0, 0))
	epg.draw.circle(cursor, (255, 0, 0), (16, 16), 2)
	epg.draw.circle(cursor, (255, 0, 0), (16, 16), 16, width=3)
	epg.mouse.set_cursor((16, 16), cursor)

	app.run(Splash())
	app.run(Game())

if __name__ == "__main__":
	main()
