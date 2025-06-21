import pygame
import sys
import math

pygame.init()

# Screen setup
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w - 100, info.current_h - 100
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bloon TD Clone")

# Load images
background_raw = pygame.image.load("background.png").convert()
background = pygame.transform.scale(background_raw, (WIDTH, HEIGHT))
raw_width, raw_height = background_raw.get_size()

balloon_img = pygame.image.load("balloon.png").convert_alpha()
balloon_img = pygame.transform.scale(balloon_img, (60, 60))

monkey_animations = [
    pygame.transform.scale(pygame.image.load("Monkey1animation1.png").convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load("Monkey1animation2.png").convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load("Monkey1animation3.png").convert_alpha(), (200, 200))
]
monkey_width, monkey_height = monkey_animations[0].get_size()
dart_img = pygame.image.load("dart1.png").convert_alpha()

# Blocked colors (brown + gray + blue)
BLOCKED_COLORS = [(156, 90, 60), (180, 180, 180), (0, 183, 239)]

# Fonts
font = pygame.font.SysFont("arial", 32)
small_font = pygame.font.SysFont("arial", 24)

# Game variables
original_monkey_pos = (WIDTH - 200, 20)
clock = pygame.time.Clock()
balloons = []
placed_monkeys = []
darts = []
wave = 0
money = 650
balloons_spawned = 0
max_balloons_per_wave = 20
spawn_delay = 45
spawn_timer = 0
max_waves = 999
dragging_monkey = False
round_active = False
has_spawned_this_round = False

# Path
path = [(0, 480), (1500, 480), (1500, 900), (0, 900)]

# Balloon class
class Balloon:
    def __init__(self):
        self.pos = list(path[0])
        self.index = 1
        self.speed = 1.5
        self.health = 1
        self.alive = True

    def move(self):
        if self.index >= len(path):
            self.alive = False
            return
        target = path[self.index]
        dx = target[0] - self.pos[0]
        dy = target[1] - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.pos = list(target)
            self.index += 1
        else:
            self.pos[0] += self.speed * dx / dist
            self.pos[1] += self.speed * dy / dist

    def draw(self):
        screen.blit(balloon_img, (int(self.pos[0]) - 20, int(self.pos[1]) - 20))

    def path_progress(self):
        if self.index == 0:
            return 0
        return self.index + math.hypot(self.pos[0] - path[self.index-1][0], self.pos[1] - path[self.index-1][1])

# Monkey class
class Monkey:
    def __init__(self, pos):
        self.pos = pos
        self.animating = False
        self.animation_index = 0
        self.timer = 0
        self.cooldown = 60

    def draw(self):
        if self.animating:
            img = monkey_animations[self.animation_index // 5 % 3]
            self.animation_index += 1
            if self.animation_index >= 15:
                self.animating = False
                self.animation_index = 0
        else:
            img = monkey_animations[0]
        screen.blit(img, self.pos)

    def update(self):
        self.timer += 1
        target = self.find_furthest_target()
        if self.timer >= self.cooldown and target:
            self.timer = 0
            self.animating = True
            mx = self.pos[0] + monkey_width // 2 - 30
            my = self.pos[1] + monkey_height // 2
            dx = target.pos[0] - mx
            dy = target.pos[1] - my
            dist = math.hypot(dx, dy)
            darts.append({
                "x": mx,
                "y": my,
                "vx": dx / dist * 5,
                "vy": dy / dist * 5,
                "start_x": mx,
                "start_y": my
            })

    def find_furthest_target(self):
        furthest = None
        max_progress = -1
        for b in balloons:
            if b.alive:
                progress = b.path_progress()
                if progress > max_progress:
                    max_progress = progress
                    furthest = b
        return furthest

# Placement validation

def is_monkey_touching_blocked(top_left):
    for x in range(monkey_width):
        for y in range(monkey_height):
            alpha = monkey_animations[0].get_at((x, y))[3]
            if alpha == 0:
                continue
            sx = top_left[0] + x
            sy = top_left[1] + y
            if not (0 <= sx < WIDTH and 0 <= sy < HEIGHT):
                continue
            rx = int(sx * raw_width / WIDTH)
            ry = int(sy * raw_height / HEIGHT)
            if not (0 <= rx < raw_width and 0 <= ry < raw_height):
                continue
            color = background_raw.get_at((rx, ry))[:3]
            if color in BLOCKED_COLORS:
                return True
    return False

# Button areas
play_button = pygame.Rect(20, HEIGHT - 80, 140, 50)
monkey_box = pygame.Rect(original_monkey_pos[0], original_monkey_pos[1], monkey_width, monkey_height)

# Main loop
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_x, mouse_y = mouse_pos
    top_left_monkey = (mouse_x - 100, mouse_y - 100)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if monkey_box.collidepoint(mouse_x, mouse_y) and money >= 250:
                dragging_monkey = True
            elif play_button.collidepoint(mouse_x, mouse_y):
                if not round_active:
                    round_active = True
                    has_spawned_this_round = False
            elif dragging_monkey:
                if not is_monkey_touching_blocked(top_left_monkey):
                    placed_monkeys.append(Monkey(top_left_monkey))
                    money -= 250
                    dragging_monkey = False
                else:
                    print("❌ Invalid placement")

    if round_active and wave < max_waves:
        if not has_spawned_this_round:
            balloons = []
            balloons_spawned = 0
            spawn_timer = 0
            has_spawned_this_round = True

        spawn_timer += 1
        if spawn_timer >= spawn_delay and balloons_spawned < max_balloons_per_wave:
            balloons.append(Balloon())
            spawn_timer = 0
            balloons_spawned += 1

        if balloons_spawned == max_balloons_per_wave and all(not b.alive for b in balloons):
            round_active = False
            wave += 1
            has_spawned_this_round = False

    for balloon in balloons:
        if balloon.alive:
            balloon.move()
        elif balloon.health > 0:
            money += 1
            balloon.health = 0

    for monkey in placed_monkeys:
        monkey.update()

    for dart in darts[:]:
        dart["x"] += dart["vx"]
        dart["y"] += dart["vy"]
        screen.blit(dart_img, (dart["x"], dart["y"]))
        hit = False
        for balloon in balloons:
            if balloon.alive and math.hypot(dart["x"] - balloon.pos[0], dart["y"] - balloon.pos[1]) < 20:
                balloon.alive = False
                hit = True
                break
        if hit or not (0 <= dart["x"] <= WIDTH and 0 <= dart["y"] <= HEIGHT):
            if dart in darts:
                darts.remove(dart)

    # Drawing
    screen.blit(background, (0, 0))
    screen.blit(monkey_animations[0], original_monkey_pos)

    for monkey in placed_monkeys:
        monkey.draw()

    if dragging_monkey:
        screen.blit(monkey_animations[0], top_left_monkey)

    for balloon in balloons:
        if balloon.alive:
            balloon.draw()

    # UI
    pygame.draw.rect(screen, (0, 200, 0), play_button)
    screen.blit(font.render("PLAY", True, (255, 255, 255)), (play_button.x + 25, play_button.y + 10))
    screen.blit(font.render(f"Money: ${money}", True, (0, 0, 0)), (WIDTH - 250, HEIGHT - 50))
    screen.blit(font.render(f"Round: {wave + 1}", True, (0, 0, 0)), (WIDTH // 2 - 80, 20))
    screen.blit(small_font.render("$250", True, (255, 255, 255)), (original_monkey_pos[0] + 60, original_monkey_pos[1] - 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
