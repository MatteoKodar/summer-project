
import pygame
import sys
import math

pygame.init()

# Screen setup
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w - 50, info.current_h - 50
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bloon TD Clone")

# Load images
background_raw = pygame.image.load("background.png").convert()
background = pygame.transform.scale(background_raw, (WIDTH, HEIGHT))
raw_width, raw_height = background_raw.get_size()

balloon_img = pygame.image.load("balloon.png").convert_alpha()
balloon_img = pygame.transform.scale(balloon_img, (60, 60))
balloon1_img = pygame.image.load("balloon1.png").convert_alpha()
balloon1_img = pygame.transform.scale(balloon1_img, (60, 60))

monkey_animations = [
    pygame.transform.scale(pygame.image.load("Monkey1animation1.png").convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load("Monkey1animation2.png").convert_alpha(), (200, 200)),
    pygame.transform.scale(pygame.image.load("Monkey1animation3.png").convert_alpha(), (200, 200))
]
monkey_width, monkey_height = monkey_animations[0].get_size()
dart_img = pygame.image.load("dart1.png").convert_alpha()
dart_img = pygame.transform.scale(dart_img, (100, 100))
upgrademonkey11_img = pygame.image.load("upgrademonkey11.png").convert_alpha()
upgrademonkey11_img = pygame.transform.scale(upgrademonkey11_img, (100, 100))
BLOCKED_COLORS = [(156, 90, 60), (180, 180, 180), (0, 183, 239)]

font = pygame.font.SysFont("arial", 32)
small_font = pygame.font.SysFont("arial", 24)

original_monkey_pos = (WIDTH - 200, 20)
clock = pygame.time.Clock()
balloons = []
placed_monkeys = []
darts = []
wave = 0
money = 650
balloons_spawned = 0
max_balloons_per_wave = 50
spawn_delay = 45
spawn_timer = 0
max_waves = 999
dragging_monkey = False
round_active = False
has_spawned_this_round = False

path = [(0, 480), (1500, 480), (1500, 900), (0, 900)]

selected_monkey = None  # Track which monkey is selected

# Speedup logic
speed_levels = [1, 2, 5, 10]
speed_index = 0
game_speed = speed_levels[speed_index]

class Balloon:
    def __init__(self):
        self.pos = list(path[0])
        self.index = 1
        self.speed = 1.5
        self.health = 1
        self.alive = True

    def move(self):
        for _ in range(game_speed):  # Move faster at higher speeds
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

    def get_rect(self):
        return pygame.Rect(int(self.pos[0]) - 30, int(self.pos[1]) - 30, 60, 60)

class Balloon1(Balloon):
    def __init__(self):
        super().__init__()
        self.health = 2  # Stronger than regular balloon

    def draw(self):
        screen.blit(balloon1_img, (int(self.pos[0]) - 20, int(self.pos[1]) - 20))

def get_dart_rect(dart):
    return pygame.Rect(int(dart["x"]), int(dart["y"]), 32, 32)

class Monkey:
    def __init__(self, pos):
        self.pos = pos
        self.range = 500
        self.animating = False
        self.animation_index = 0
        self.timer = 0
        self.cooldown = 60
        self.active_dart = None
        self.pierce = 1  # Default pierce

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
        self.timer += game_speed
        target = self.find_furthest_target()
        if self.timer >= self.cooldown and target and self.active_dart is None:
            self.timer = 0
            self.animating = True
            mx = self.pos[0] + monkey_width // 2 - 30
            my = self.pos[1] + monkey_height // 2
            dx = target.pos[0] - mx
            dy = target.pos[1] - my
            dist = math.hypot(dx, dy)
            dart = {
                "x": mx,
                "y": my,
                "vx": dx / dist * 5,
                "vy": dy / dist * 5,
                "start_x": mx,
                "start_y": my,
                "owner": self,
                "pierce": self.pierce
            }
            darts.append(dart)
            self.active_dart = dart

    def find_furthest_target(self):
        furthest = None
        max_progress = -1
        mx = self.pos[0] + monkey_width // 2
        my = self.pos[1] + monkey_height // 2
        for b in balloons:
            if b.alive:
                dist = math.hypot(b.pos[0] - mx, b.pos[1] - my)
                if dist <= self.range:
                    progress = b.path_progress()
                    if progress > max_progress:
                        max_progress = progress
                        furthest = b
        return furthest

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

play_button = pygame.Rect(20, HEIGHT - 80, 140, 50)
speed_button = pygame.Rect(180, HEIGHT - 80, 140, 50)
monkey_box = pygame.Rect(original_monkey_pos[0], original_monkey_pos[1], monkey_width, monkey_height)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    mouse_x, mouse_y = mouse_pos
    top_left_monkey = (mouse_x - 100, mouse_y - 100)

    # Define upgrade image rects if a monkey is selected
    if selected_monkey:
        upgrade_x = selected_monkey.pos[0] + monkey_width + 10
        upgrade_y = selected_monkey.pos[1]
        upgrade_rect = pygame.Rect(upgrade_x, upgrade_y, 100, 100)
        # Define right thirds for upgrades
        top_right = pygame.Rect(upgrade_x + 66, upgrade_y, 34, 33)
        mid_right = pygame.Rect(upgrade_x + 66, upgrade_y + 33, 34, 34)
        bot_right = pygame.Rect(upgrade_x + 66, upgrade_y + 67, 34, 33)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_d:
                if balloons:
                    del balloons[0]
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if monkey_box.collidepoint(mouse_x, mouse_y) and money >= 250:
                dragging_monkey = True
            elif play_button.collidepoint(mouse_x, mouse_y):
                if not round_active:
                    round_active = True
                    has_spawned_this_round = False
            elif speed_button.collidepoint(mouse_x, mouse_y):
                speed_index = (speed_index + 1) % len(speed_levels)
                game_speed = speed_levels[speed_index]
            elif dragging_monkey:
                if not is_monkey_touching_blocked(top_left_monkey):
                    placed_monkeys.append(Monkey(top_left_monkey))
                    money -= 250
                    dragging_monkey = False
                else:
                    print("❌ Invalid placement")
            elif selected_monkey:
                # Handle upgrade clicks
                if top_right.collidepoint(mouse_x, mouse_y) and money >= 200:
                    selected_monkey.pierce = 5
                    money -= 200
                elif mid_right.collidepoint(mouse_x, mouse_y) and money >= 350:
                    selected_monkey.pierce = 7
                    money -= 350
                elif bot_right.collidepoint(mouse_x, mouse_y) and money >= 0:
                    selected_monkey.range += 200
            else:
                # Select monkey if clicked
                found = False
                for monkey in placed_monkeys:
                    monkey_rect = pygame.Rect(monkey.pos[0], monkey.pos[1], monkey_width, monkey_height)
                    if monkey_rect.collidepoint(mouse_x, mouse_y):
                        selected_monkey = monkey
                        found = True
                        break
                if not found:
                    selected_monkey = None

    # --- ROUND LOGIC ---
    if round_active and wave < max_waves:
        if not has_spawned_this_round:
            balloons_spawned = 0
            spawn_timer = 0
            has_spawned_this_round = True

        spawn_timer += game_speed
        if spawn_timer >= spawn_delay:
            if wave == 1 and balloons_spawned < 10:
                balloons.append(Balloon1())
                balloons_spawned += 1
            elif wave != 1 and balloons_spawned < max_balloons_per_wave:
                balloons.append(Balloon())
                balloons_spawned += 1
            spawn_timer = 0

        if ((wave == 1 and balloons_spawned == 10) or (wave != 1 and balloons_spawned == max_balloons_per_wave)) and all(not b.alive for b in balloons):
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

    # Darts: move and check collision with custom hitboxes and pierce
    for dart in darts[:]:
        for _ in range(game_speed):
            dart["x"] += dart["vx"]
            dart["y"] += dart["vy"]
            hit_count = 0
            for balloon in balloons:
                if balloon.alive and get_dart_rect(dart).colliderect(balloon.get_rect()):
                    if isinstance(balloon, Balloon1):
                        new_balloon = Balloon()
                        new_balloon.pos = balloon.pos[:]
                        new_balloon.index = balloon.index
                        balloons.append(new_balloon)
                    balloon.alive = False
                    money += 1
                    hit_count += 1
                    if hit_count >= dart.get("pierce", 1):
                        break
            if hit_count > 0 or not (0 <= dart["x"] <= WIDTH and 0 <= dart["y"] <= HEIGHT):
                if "owner" in dart and dart["owner"].active_dart is dart:
                    dart["owner"].active_dart = None
                if dart in darts:
                    darts.remove(dart)
                break

    # Remove dead balloons
    balloons = [b for b in balloons if b.alive]

    # Drawing
    screen.blit(background, (0, 0))
    screen.blit(monkey_animations[0], original_monkey_pos)

    for dart in darts:
        screen.blit(dart_img, (dart["x"], dart["y"]))

    for monkey in placed_monkeys:
        monkey.draw()

    # Draw range only for selected monkey
    if selected_monkey:
        pygame.draw.circle(
            screen, (0, 255, 0, 50),
            (selected_monkey.pos[0] + monkey_width // 2, selected_monkey.pos[1] + monkey_height // 2),
            selected_monkey.range, 2
        )
        # Draw upgrade image to the right of the selected monkey
        upgrade_x = selected_monkey.pos[0] + monkey_width + 10
        upgrade_y = selected_monkey.pos[1]
        screen.blit(upgrademonkey11_img, (upgrade_x, upgrade_y))

    if dragging_monkey:
        screen.blit(monkey_animations[0], top_left_monkey)

    for balloon in balloons:
        if balloon.alive:
            balloon.draw()

    pygame.draw.rect(screen, (0, 200, 0), play_button)
    screen.blit(font.render("PLAY", True, (255, 255, 255)), (play_button.x + 25, play_button.y + 10))
    pygame.draw.rect(screen, (0, 0, 200), speed_button)
    speed_label = f"{speed_levels[speed_index]}x"
    screen.blit(font.render(speed_label, True, (255, 255, 255)), (speed_button.x + 35, speed_button.y + 10))
    screen.blit(font.render(f"Money: ${money}", True, (0, 0, 0)), (WIDTH - 250, HEIGHT - 50))
    screen.blit(font.render(f"Round: {wave + 1}", True, (0, 0, 0)), (WIDTH // 2 - 80, 20))
    screen.blit(small_font.render("$250", True, (255, 255, 255)), (original_monkey_pos[0] + 60, original_monkey_pos[1] - 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()