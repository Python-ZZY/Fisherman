import epg

APPNAME = "Fisherman"
VERSION = "1.1"

WIDTH = 800
HEIGHT = 650
CENTER = WIDTH // 2, HEIGHT // 2

SKYHEIGHT = 180
SKY_RATE = 0.0003

FISH_RATE = 0.02
SCORE_REQUIREMENT = (0, 10, 100, 200, 300, 500, 800, 1000, 1200, 1500, 
	2000, 3000, 5000, 10000, 20000, 50000)[::-1]
FISH = [
	("CommonFish", 0, 100),
	("ThornFish", 1, 25),
	("GoldFish", 2, 5),
	("FastFish", 3, 40),
	("BombFish", 4, 20),
	("FishKing", 4, 5),
	("IceFish", 5, 10),
	("Shark", 5, 15),
	]
ACTIVITIES = [
	("CommonFishRush", 0, 30),
	("GoldFishRush", 2, 3),
	("VortexAppear", 3, 15),
	("FishRush", 4, 60),
	("SharkRush", 5, 10),
	]

vec = epg.Vector2
none_surface = epg.Surface((0, 0))