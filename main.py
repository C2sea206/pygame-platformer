import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join
pygame.init()

pygame.display.set_caption("TMNT on hand: Tiny Turtles")

WIDTH, HEIGHT = 1000, 800
FPS = 60
PLAYER_VEL = 5

window = pygame.display.set_mode((WIDTH, HEIGHT))


def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]


def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    path = join("assets", dir1, dir2)
    images = [f for f in listdir(path) if isfile(join(path, f))]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()

        sprites = []
        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites

    return all_sprites


def get_block(size):
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha()
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0, 0), rect)
    return pygame.transform.scale2x(surface)


class Player(pygame.sprite.Sprite):
    COLOR = (255, 0, 0)
    GRAVITY = 0.9
    SPRITES = load_sprite_sheets("MainCharacters", "Blue", 32, 32, True)
    ANIMATION_DELAY = 2

    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left"
        self.animation_count = 0
        self.fall_count = 0
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0
        self.death = False

    def jump(self):
        self.y_vel = -self.GRAVITY * 8
        self.animation_count = 0
        self.jump_count += 1
        if self.jump_count == 1:
            self.fall_count = 0

    def move(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True

    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0

    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0

    def loop(self, fps):
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2:
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite()

    def landed(self):
        self.fall_count = 0
        self.y_vel = 0
        self.jump_count = 0

    def hit_head(self):
        self.count = 0
        self.y_vel *= -1

    def update_sprite(self):
        sprite_sheet = "idle"
        if self.hit:
            sprite_sheet = "hit"
        elif self.y_vel < 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"

        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    def update(self):
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.sprite)

    def draw(self, win, offset_x):
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y))


class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        self.width = width
        self.height = height
        self.name = name
        self.removeFlag = False

    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))


class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size)
        block = get_block(size)
        self.image.blit(block, (0, 0))
        self.mask = pygame.mask.from_surface(self.image)


class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height,fireTime = 0):
        super().__init__(x, y, width, height, "fire")
        self.fire = load_sprite_sheets("Traps", "Fire", width, height)
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"
        self.onFire = False
        self.fireTime = fireTime

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"

    def loop(self):

        if self.onFire:
            self.on()
        else:
            self.off()
        self.fireTime += 0.016
        if self.fireTime >= 5:
            self.fireTime = 0
            self.onFire = not self.onFire



        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class Coin(Object):
    ANIMATION_DELAY = 1

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "coin")
        self.fire = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.fire["Apple"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Apple"
        ranNum = random.randint(0,8)
        if ranNum == 0:
            self.animation_name = "Apple"
        if ranNum == 1:
            self.animation_name = "Bananas"
        if ranNum == 2:
            self.animation_name = "Cherries"
        if ranNum == 3:
            self.animation_name = "Kiwi"
        if ranNum == 4:
            self.animation_name = "Melon"
        if ranNum == 5:
            self.animation_name = "Orange"
        if ranNum == 6:
            self.animation_name = "Pineapple"
        if ranNum == 7:
            self.animation_name = "Strawberry"


    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0


class CollectParticle(Object):
    ANIMATION_DELAY = 1

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "collected")
        self.fire = load_sprite_sheets("Items", "Fruits", width, height)
        self.image = self.fire["Collected"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "Collected"
        self.deathTime = 0

    def loop(self):
        self.deathTime += 0.016
        if self.deathTime >= 1:
            self.removeFlag = True

        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0
            self.removeFlag = True

class Fan(Object):
    ANIMATION_DELAY = 1

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fan")
        self.fire = load_sprite_sheets("Traps", "Fan", width, height)
        self.image = self.fire["On"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "On"


    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

class Saw(Object):
    ANIMATION_DELAY = 1

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "saw")
        self.fire = load_sprite_sheets("Traps", "Saw", width, height)
        self.image = self.fire["on"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "on"
        self.moveRight = True
        self.maxX = x + 800
        self.minX = x
        self.speed = 4


    def loop(self):
        if self.moveRight:
            self.rect.x += self.speed
            if self.rect.x > self.maxX:
                self.moveRight = False
        else:
            self.rect.x -= self.speed
            if self.rect.x < self.minX:
                self.moveRight = True

        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count //
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites):
            self.animation_count = 0

def get_background(name):
    image = pygame.image.load(join("assets", "Background", name))
    _, _, width, height = image.get_rect()
    tiles = []

    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            pos = (i * width, j * height)
            tiles.append(pos)

    return tiles, image


def draw(window, background, bg_image, player, objects, offset_x):
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    pygame.display.update()


def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if obj.name == "coin" or obj.name == "collected":
            continue
        if pygame.sprite.collide_mask(player, obj):
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:
                player.rect.top = obj.rect.bottom
                player.hit_head()

            collided_objects.append(obj)

    return collided_objects


def collide(player, objects, dx):
    player.move(dx, 0)
    player.update()
    collided_object = None
    for obj in objects:
        if obj.name == "collected":
            continue
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break

    player.move(-dx, 0)
    player.update()
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2)
    collide_right = collide(player, objects, PLAYER_VEL * 2)

    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)

    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]

    for obj in to_check:
        if obj and obj.name == "fire" and obj.onFire:
            player.make_hit()
            player.death = True
        if obj and obj.name == "saw" :
            player.make_hit()
            player.death = True

        if obj and obj.name == "coin":
            obj.removeFlag = True
        if obj and obj.name == "fan":
            player.landed()
            player.GRAVITY = 1.5
            player.jump()
            player.GRAVITY = 1




block_size = 96
player = Player(100, 300, 50, 50)
objects = []
fire = None
offset_x = 0
fires = []


def init():
    global  player,objects,fire,offset_x,fires,coins
    offset_x = 0


    player = Player(100, 300, 50, 50)
    fire = Fire(300, HEIGHT - block_size - 64, 16, 32)
    fire.off()
    fires = [Fire(WIDTH - 30 + 40 * i, HEIGHT - 70, 16, 32,fireTime= i * 0.5)
             for i in range(0, 20)]

    coins = [Coin(100 * i, HEIGHT - 160, 32, 32)
             for i in range(0, 10)]

    coins2 = [Coin(200 + 50 * i, HEIGHT - 560, 32, 32)
             for i in range(0, 20)]

    coins3 = [Coin(WIDTH * 2 - 100 + 50 * i, HEIGHT - 360, 32, 32)
              for i in range(0, 20)]

    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
             for i in range(0, (WIDTH * 1) // block_size)]

    floor3 = [Block(WIDTH + 800 + i * block_size, HEIGHT - block_size, block_size)
             for i in range(0, (WIDTH * 1) // block_size)]

    floor2 = [Block(WIDTH + 200 + i * block_size, HEIGHT - block_size * 2, block_size)
             for i in range(0, 2)]

    floor4 = [Block(WIDTH * 3  + i * block_size, HEIGHT - block_size * 3, block_size)
              for i in range(0, 2)]

    floor5 = [Block(WIDTH * 3 + 400 + i * block_size + 20, HEIGHT - block_size * 3 - 100, block_size)
              for i in range(0, 16, 2)]

    floor6 = [Block(WIDTH * 5 + i * block_size, HEIGHT - block_size * 3, block_size)
              for i in range(0, 2)]

    coins4 = [Coin(WIDTH * 3 + 700 + 50 * i, HEIGHT - block_size * 3 - 200, 32, 32)
              for i in range(0, 20)]

    coins5 = [Coin(WIDTH * 5 + 50 * i, HEIGHT - block_size * 3 - 40, 32, 32)
              for i in range(0, 2)]

    fan = Fan(WIDTH + 340, HEIGHT - 210, 24, 8)
    saw = Saw(WIDTH + 840, HEIGHT - block_size - 50, 38, 38)
    saw2 = Saw(200, HEIGHT - block_size * 5 - 50, 38, 38)

    topfloor1 = [Block(block_size * 2 + i * block_size, HEIGHT - block_size * 5, block_size)
                 for i in range(0, (WIDTH) // block_size)]

    objects = [*coins5,*coins4,*coins3,*coins2,*floor6,*floor5,*floor4,saw2,saw,*floor3,fan,*coins,*topfloor1, *floor,*floor2, Block(0, HEIGHT - block_size * 6, block_size),
               Block(block_size * 3, HEIGHT - block_size * 4, block_size), *fires]

def isWin(objects):
    for obj in objects:
        if obj.name == "coin":
            return False
    return True

def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Pink.png")

    global offset_x,objects

    init()

    scroll_area_width = 400

    deathTime = 0

    run = True
    while run:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                break

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        ###
        if player.rect.y > 1000:
            init()

        if player.death:
            deathTime += 0.016
            if deathTime >= 2:
                deathTime =0
                init()

        player.loop(FPS)

        for obj in objects:
            if obj.name == "coin" or obj.name == "fire" or obj.name == "fan" or obj.name == "saw" or obj.name == "collected":
                obj.loop()

        addObjects = []
        for obj in objects:
            if obj.removeFlag:
                if obj.name == "coin":
                    addObjects.append(CollectParticle(obj.rect.x - 32,obj.rect.y - 32,64,64))
                objects.remove(obj)

        objects += addObjects

        if isWin(objects):
            objects = []
            player.jump()
            draw(window, background, bg_image, player, objects, offset_x)
            continue

        if not player.death:
            handle_move(player, objects)
        draw(window, background, bg_image, player, objects, offset_x)

        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel

    pygame.quit()
    quit()


if __name__ == "__main__":
    main(window)
