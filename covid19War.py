import pygame
import random
import os
import math

# ======================================
# PATH FIX
# ======================================
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_path(filename):
    return os.path.join(BASE_PATH, filename)


# ======================================
# CONFIG & AUDIO STATE
# ======================================
BASE_WIDTH, BASE_HEIGHT, FPS = 600, 800, 60
STATE_MENU, STATE_PLAYING, STATE_PAUSE, STATE_GAMEOVER = "menu", "playing", "pause", "gameover"

pygame.init()
pygame.mixer.init()

music_volume, sfx_volume = 0.5, 0.5
spawn_timer = 0
bar_color = [0, 255, 255]
cycle_count = 0
mission_scores = []

try:
    boom_sound = pygame.mixer.Sound(get_path("assets/sounds/boom.wav"))
    siren_sound = pygame.mixer.Sound(get_path("assets/sounds/siren.wav"))
except:
    boom_sound = siren_sound = None


def update_volumes():
    pygame.mixer.music.set_volume(music_volume)
    if boom_sound:
        boom_sound.set_volume(sfx_volume * 0.5)
    if siren_sound:
        siren_val = max(0.9, sfx_volume * 1.5)
        siren_sound.set_volume(min(1.0, siren_val))


def play_music():
    for path in ["assets/sounds/background-music.mp3", "background-music.mp3"]:
        try:
            pygame.mixer.music.load(get_path(path))
            pygame.mixer.music.play(-1)
            break
        except:
            continue
    update_volumes()


try:
    bg = pygame.image.load(get_path("assets/images/bg.png")).convert()
    bg = pygame.transform.scale(bg, (BASE_WIDTH, BASE_HEIGHT))
except:
    bg = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
    bg.fill((20, 20, 40))


# ======================================
# SPRITES & EFFECTS
# ======================================
class Explosion:
    def __init__(self, pos):
        self.pos, self.radius, self.alpha = pos, 10, 255

    def update(self):
        self.radius += 3
        self.alpha -= 12
        return self.alpha > 0

    def draw(self, surf):
        s = pygame.Surface((200, 200), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 200, 0, self.alpha), (100, 100), self.radius, 3)
        surf.blit(s, (self.pos[0] - 100, self.pos[1] - 100))


class FloatingText:
    def __init__(self, pos, text_val, color=(0, 255, 255)):
        self.pos, self.text_val, self.color = list(pos), text_val, color
        self.alpha, self.lifetime, self.age = 255, 60, 0

    def update(self):
        self.age += 1
        self.pos[1] -= 2
        self.alpha = max(0, 255 - int((self.age / self.lifetime) * 255))
        return self.age < self.lifetime

    def draw(self, surf):
        f = pygame.font.SysFont("arial", 24, bold=True)
        txt_surf = f.render(str(self.text_val), True, self.color)
        temp_surf = txt_surf.convert_alpha()
        temp_surf.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(temp_surf, temp_surf.get_rect(center=(self.pos[0], self.pos[1])))


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.images = [pygame.image.load(get_path(f"assets/images/JiJiSR1{s}.png")).convert_alpha() for s in
                           ["", "L", "R"]]
        except:
            self.images = [pygame.Surface((40, 60), pygame.SRCALPHA) for _ in range(3)]
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=(BASE_WIDTH // 2, BASE_HEIGHT - 40))
        self.speedx = self.speedy = self.score = self.hit_cooldown = 0
        self.life = 100
        self.last_shot = 0
        self.shot_delay = 200

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        self.rect.clamp_ip(pygame.Rect(0, 0, BASE_WIDTH, BASE_HEIGHT))
        self.image = self.images[1] if self.speedx < -1 else (self.images[2] if self.speedx > 1 else self.images[0])
        if self.hit_cooldown > 0: self.hit_cooldown -= 1

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shot_delay:
            self.last_shot = now
            b = Cure(self.rect.centerx, self.rect.top)
            allsprites.add(b)
            cures.add(b)


class Covid(pygame.sprite.Sprite):
    def __init__(self, is_wave=False):
        super().__init__()
        try:
            self.orig_image = pygame.image.load(get_path("assets/images/covid19.png")).convert_alpha()
        except:
            self.orig_image = pygame.Surface((30, 30), pygame.SRCALPHA)
        self.image = self.orig_image.copy()
        self.rect = self.image.get_rect()
        self.is_wave = is_wave
        self.rot = 0
        self.rot_speed = random.uniform(-5, 5)
        self.respawn()

    def respawn(self):
        self.rect.x = random.randrange(BASE_WIDTH - self.rect.width)
        self.rect.y = random.randrange(-200, -50)
        base = 2 + (current_wave * 0.3)
        self.speed = random.uniform(base, base + 4) if self.is_wave else random.uniform(2, 3.5)
        self.rot_speed = random.uniform(-4, 4)

    def update(self):
        self.rect.y += self.speed
        self.rot = (self.rot + self.rot_speed) % 360
        old_center = self.rect.center
        self.image = pygame.transform.rotate(self.orig_image, self.rot)
        self.rect = self.image.get_rect(center=old_center)
        if self.rect.top > BASE_HEIGHT:
            if self.is_wave:
                self.kill()
            else:
                self.respawn()


class Cure(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.orig = pygame.image.load(get_path("assets/images/cure.png")).convert_alpha()
        except:
            self.orig = pygame.Surface((20, 20), pygame.SRCALPHA)
        self.image, self.rect = self.orig, self.orig.get_rect(centerx=x, bottom=y)
        self.speedy, self.rot = -10, 0

    def update(self):
        self.rect.y += self.speedy
        self.rot += 15
        self.image = pygame.transform.rotate(self.orig, self.rot)
        self.rect = self.image.get_rect(center=self.rect.center)
        if self.rect.bottom < 0: self.kill()


class VolumeSlider:
    def __init__(self, label, y):
        self.label, self.y = label, y
        self.rect = pygame.Rect(BASE_WIDTH // 2 - 100, y + 35, 200, 15)

    def draw(self, surf, val, selected):
        color = (0, 255, 255) if selected else (140, 140, 140)
        f = pygame.font.SysFont("arial", 28, bold=True)
        txt = f.render(f"{self.label}: {int(val * 100)}%", True, color)
        surf.blit(txt, txt.get_rect(center=(BASE_WIDTH // 2, self.y)))
        pygame.draw.rect(surf, (50, 50, 50), self.rect)
        pygame.draw.rect(surf, color, (self.rect.x, self.rect.y, int(self.rect.w * val), self.rect.h))


# ======================================
# HELPERS
# ======================================
def spawn_enemy(is_wave):
    c = Covid(is_wave)
    allsprites.add(c)
    covids.add(c)


def start_new_game():
    global game_state, player, allsprites, covids, cures, current_wave, game_mode, mode_timer, alert_timer, explosions, floating_texts, spawn_timer, cycle_count, bar_color, mission_scores
    game_state, player = STATE_PLAYING, Player()
    allsprites, covids, cures = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    explosions, floating_texts, current_wave = [], [], 1
    game_mode, alert_timer, mode_timer = "normal", 0, random.randint(300, 600)
    spawn_timer = 0
    cycle_count = 0
    mission_scores = [0]
    bar_color = [0, 255, 255]
    allsprites.add(player)
    for _ in range(5): spawn_enemy(False)


def draw_external_ui(surf, sx, sw):
    pygame.draw.rect(surf, (0, 0, 0, 180), (sx, 0, sw, 75))
    score_txt = font_med.render(f"SCORE: {player.score:06d}", True, (0, 255, 255))
    surf.blit(score_txt, (sx + sw // 2 - score_txt.get_width() // 2, 10))
    best_txt = font_small.render(f"BEST: {high_score:06d}", True, (255, 255, 0))
    surf.blit(best_txt, (sx + sw // 2 - best_txt.get_width() // 2, 45))

    prog_x, prog_y = sx + 15, 15
    mission_label = f"MISSION - {cycle_count + 1}"
    surf.blit(font_small.render(mission_label, True, (255, 255, 255)), (prog_x, prog_y))
    pygame.draw.rect(surf, (100, 100, 100), (prog_x, prog_y + 20, 120, 10))
    wave_step = ((current_wave - 1) % 10) + 1
    fill_prog = int(116 * (wave_step / 10))
    pygame.draw.rect(surf, bar_color, (prog_x + 2, prog_y + 22, fill_prog, 6))

    hp_x, hp_y = sx + sw - 135, 15
    surf.blit(font_small.render("SHIELD", True, (255, 255, 255)), (hp_x, hp_y))
    pygame.draw.rect(surf, (50, 50, 50), (hp_x, hp_y + 20, 120, 10))
    h_color = (0, 255, 120) if player.life > 40 else (255, 50, 50)
    fill_hp = int(max(0, player.life / 100) * 116)
    pygame.draw.rect(surf, h_color, (hp_x + 2, hp_y + 22, fill_hp, 6))


# ======================================
# INITIALIZATION
# ======================================
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

game_surface = pygame.Surface((BASE_WIDTH, BASE_HEIGHT))
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("arial", 72, bold=True)
font_med = pygame.font.SysFont("arial", 32, bold=True)
font_small = pygame.font.SysFont("arial", 16, bold=True)
m_slider, s_slider = VolumeSlider("Music Volume", 380), VolumeSlider("Sound Volume", 480)

pygame.joystick.init()
controller = pygame.joystick.Joystick(0) if pygame.joystick.get_count() > 0 else None
if controller: controller.init()

play_music()
game_state, running, high_score, shake_timer = STATE_MENU, True, 0, 0
menu_index, stick_ready, bg_y = 0, True, 0

while running:
    clock.tick(FPS)
    win_w, win_h = window.get_size()
    scale = min(win_w / BASE_WIDTH, win_h / BASE_HEIGHT)
    sw, sh = int(BASE_WIDTH * scale), int(BASE_HEIGHT * scale)
    offset_x, offset_y = (win_w - sw) // 2, (win_h - sh) // 2

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

        # KEYBOARD EVENTS
        if event.type == pygame.KEYDOWN:
            if game_state == STATE_GAMEOVER and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                game_state = STATE_MENU
            elif game_state in [STATE_MENU, STATE_PAUSE]:
                if event.key == pygame.K_UP: menu_index = (menu_index - 1) % 4
                if event.key == pygame.K_DOWN: menu_index = (menu_index + 1) % 4
                if event.key == pygame.K_LEFT:
                    if menu_index == 1: music_volume = max(0, music_volume - 0.05)
                    if menu_index == 2: sfx_volume = max(0, sfx_volume - 0.05)
                    update_volumes()
                if event.key == pygame.K_RIGHT:
                    if menu_index == 1: music_volume = min(1, music_volume + 0.05)
                    if menu_index == 2: sfx_volume = min(1, sfx_volume + 0.05)
                    update_volumes()
                if event.key == pygame.K_RETURN:
                    if menu_index == 0:
                        if game_state == STATE_MENU: start_new_game()
                        game_state = STATE_PLAYING
                    if menu_index == 3:
                        if game_state == STATE_MENU:
                            running = False
                        else:
                            game_state = STATE_MENU
            if event.key == pygame.K_ESCAPE: game_state = STATE_PAUSE if game_state == STATE_PLAYING else (
                STATE_PLAYING if game_state == STATE_PAUSE else game_state)

        # CONTROLLER BUTTONS
        if event.type == pygame.JOYBUTTONDOWN:
            if game_state == STATE_GAMEOVER and event.button in [0, 7]:
                game_state = STATE_MENU
            elif event.button == 0:  # 'A' or Cross
                if game_state in [STATE_MENU, STATE_PAUSE]:
                    if menu_index == 0:
                        if game_state == STATE_MENU: start_new_game()
                        game_state = STATE_PLAYING
                    if menu_index == 3:
                        if game_state == STATE_MENU:
                            running = False
                        else:
                            game_state = STATE_MENU
            if event.button in [6, 7]:  # Select/Start
                game_state = STATE_PAUSE if game_state == STATE_PLAYING else (
                    STATE_PLAYING if game_state == STATE_PAUSE else game_state)

    # CONTROLLER MENU NAVIGATION (Stick & D-Pad)
    if game_state in [STATE_MENU, STATE_PAUSE] and controller:
        ay, ax = controller.get_axis(1), controller.get_axis(0)
        hat = controller.get_hat(0) if controller.get_numhats() > 0 else (0, 0)
        if stick_ready:
            if ay < -0.5 or hat[1] == 1:
                menu_index = (menu_index - 1) % 4
                stick_ready = False
            elif ay > 0.5 or hat[1] == -1:
                menu_index = (menu_index + 1) % 4
                stick_ready = False

            if menu_index in [1, 2]:  # Volume control
                if ax < -0.5 or hat[0] == -1:
                    if menu_index == 1:
                        music_volume = max(0, music_volume - 0.05)
                    else:
                        sfx_volume = max(0, sfx_volume - 0.05)
                    update_volumes()
                    stick_ready = False
                elif ax > 0.5 or hat[0] == 1:
                    if menu_index == 1:
                        music_volume = min(1, music_volume + 0.05)
                    else:
                        sfx_volume = min(1, sfx_volume + 0.05)
                    update_volumes()
                    stick_ready = False
        if abs(ay) < 0.2 and abs(ax) < 0.2 and hat == (0, 0): stick_ready = True

    if game_state == STATE_PLAYING:
        bg_y = (bg_y + 2) % BASE_HEIGHT

        # IN-GAME CONTROLS (Combined Keyboard/Controller)
        keys = pygame.key.get_pressed()
        kx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        ky = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])

        if controller:
            if abs(controller.get_axis(0)) > 0.1: kx = controller.get_axis(0)
            if abs(controller.get_axis(1)) > 0.1: ky = controller.get_axis(1)
            if controller.get_button(0) or controller.get_button(5): player.shoot()  # A or R1

        player.speedx, player.speedy = kx * 8, ky * 8
        if keys[pygame.K_SPACE]: player.shoot()

        # WAVE SYSTEM - FIXED
        mode_timer -= 1
        if game_mode == "normal":
            if mode_timer <= 0:
                game_mode, mode_timer, alert_timer = "wave", 600, 180
                if siren_sound: siren_sound.play()
        elif game_mode == "wave":
            spawn_timer -= 1
            if spawn_timer <= 0:
                spawn_enemy(True)
                spawn_timer = 15

            if mode_timer <= 0:
                if current_wave % 10 == 0:
                    cycle_count += 1
                    mission_scores.append(0)
                    bar_color = [random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)]
                game_mode, current_wave, mode_timer = "normal", current_wave + 1, random.randint(1000, 2000)
                for _ in range(5): spawn_enemy(False)

        allsprites.update()

        # COLLISIONS
        hits = pygame.sprite.groupcollide(covids, cures, True, True)
        for hit in hits:
            kill_points = random.randint(10, 120)
            player.score += kill_points
            mission_scores[cycle_count] += kill_points
            if game_mode == "normal": spawn_enemy(False)
            if boom_sound: boom_sound.play()
            explosions.append(Explosion(hit.rect.center))
            floating_texts.append(FloatingText(hit.rect.center, f"+{kill_points}"))

        if pygame.sprite.spritecollide(player, covids, True) and player.hit_cooldown == 0:
            player.life -= 15
            shake_timer, player.hit_cooldown = 12, 30
            if player.life <= 0:
                high_score = max(high_score, player.score)
                game_state = STATE_GAMEOVER

        explosions = [e for e in explosions if e.update()]
        floating_texts = [f for f in floating_texts if f.update()]

    # DRAWING
    game_surface.blit(bg, (0, bg_y))
    game_surface.blit(bg, (0, bg_y - BASE_HEIGHT))

    if game_state in [STATE_MENU, STATE_PAUSE]:
        t = font_big.render("COVID19 WAR" if game_state == STATE_MENU else "PAUSED", True, (255, 255, 255))
        game_surface.blit(t, (BASE_WIDTH // 2 - t.get_width() // 2, 100))
        b1_txt = "START MISSION" if game_state == STATE_MENU else "RESUME"
        b1_surf = font_med.render(b1_txt, True, (0, 255, 255) if menu_index == 0 else (100, 100, 100))
        game_surface.blit(b1_surf, (BASE_WIDTH // 2 - b1_surf.get_width() // 2, 280))
        m_slider.draw(game_surface, music_volume, menu_index == 1)
        s_slider.draw(game_surface, sfx_volume, menu_index == 2)
        b2_txt = "EXIT GAME" if game_state == STATE_MENU else "MAIN MENU"
        b2_surf = font_med.render(b2_txt, True, (0, 255, 255) if menu_index == 3 else (100, 100, 100))
        game_surface.blit(b2_surf, (BASE_WIDTH // 2 - b2_surf.get_width() // 2, 580))

    elif game_state == STATE_PLAYING:
        allsprites.draw(game_surface)
        for e in explosions: e.draw(game_surface)
        for f in floating_texts: f.draw(game_surface)
        if alert_timer > 0:
            alert_timer -= 1
            m = font_med.render(f"--- WARNING: WAVE {current_wave} ---", True, (255, 50, 50))
            game_surface.blit(m, (BASE_WIDTH // 2 - m.get_width() // 2, 120))

    elif game_state == STATE_GAMEOVER:
        game_surface.fill((10, 0, 0))
        over_t = font_big.render("MISSION FAILED", True, (255, 50, 50))
        game_surface.blit(over_t, (BASE_WIDTH // 2 - over_t.get_width() // 2, 80))
        sc_t = font_med.render(f"TOTAL SCORE: {player.score}", True, (255, 255, 255))
        hi_t = font_med.render(f"HIGH SCORE: {high_score}", True, (255, 255, 0))
        game_surface.blit(sc_t, (BASE_WIDTH // 2 - sc_t.get_width() // 2, 180))
        game_surface.blit(hi_t, (BASE_WIDTH // 2 - hi_t.get_width() // 2, 220))
        y_off = 280
        for i, m_score in enumerate(mission_scores):
            if y_off > 550: break
            txt = font_small.render(f"Mission {i + 1} - Score: {m_score}", True, (0, 255, 255))
            game_surface.blit(txt, (BASE_WIDTH // 2 - txt.get_width() // 2, y_off))
            y_off += 25
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        cont_t = font_small.render("PRESS ENTER / A TO CONTINUE", True, (255, 255, 255))
        cont_t.set_alpha(int(pulse * 255))
        game_surface.blit(cont_t, (BASE_WIDTH // 2 - cont_t.get_width() // 2, 650))

    scaled_surf = pygame.transform.scale(game_surface, (sw, sh))
    sx, sy = offset_x, offset_y
    if shake_timer > 0:
        shake_timer -= 1
        sx += random.randint(-6, 6)
        sy += random.randint(-6, 6)
    window.fill((0, 0, 0))
    window.blit(scaled_surf, (sx, sy))
    if game_state in [STATE_PLAYING, STATE_PAUSE]: draw_external_ui(window, sx, sw)
    pygame.display.flip()

pygame.quit()
