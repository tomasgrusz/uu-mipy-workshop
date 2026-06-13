import array
import math

import pygame

try:
    import sounddevice as sd
except Exception:
    sd = None

from d10_board import (
    add_die,
    any_die_moving,
    die_at_position,
    draw_dice,
    draw_dice_summary,
    select_die,
    throw_die,
    update_dice_physics,
)
from d10_score import calculate_score
from d10_sprites import load_d10_faces


WIDTH = 960
HEIGHT = 720
BACKGROUND_COLOR = (24, 24, 32)
FLOOR_TILE_PATH = "sprites/floor-tile.png"
QR_CODE_PATH = "sprites/qr.png"
WIN_SCREEN_GIF_PATH = "sprites/win_screen.gif"
RAGE_QUIT_GIF_PATH = "sprites/rage_quit.gif"
QR_CODE_SIZE = 132
END_SCREEN_GIF_SIZE = (300, 169)
FLOOR_TILE_COLUMNS = 28
FLOOR_TILE_ROWS = 12

TITLE_COLOR = (240, 240, 245)
HUD_COLOR = (245, 245, 245)
HUD_SHADOW = (0, 0, 0)

LEVELS = [5, 10, 25, 50, 100, 250, 500]
LEVEL_DICE = [1, 2, 3, 4, 6, 8, 10]
MAX_TRIES = 10
POWER_CHARGE_SPEED = 0.85
# Use "hold" for development, "shout" for production.
THROW_POWER_MODE = "shout"
SHOUT_VOLUME_THRESHOLD = 0.9
SHOUT_RETRY_TRIES = 1

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (35, 35, 35)
GRAY = (130, 130, 130)
LIGHT_GRAY = (210, 210, 210)
GOLD = (230, 180, 60)
PANEL_BG = (20, 20, 20)


class GameSession:
    def __init__(self, floor_rect):
        self.floor_rect = floor_rect
        self.dice = []
        self.tries_left = MAX_TRIES
        self.current_level = 0
        self.game_state = "playing"
        self.selected_index = 0
        self.charging_throw = False
        self.throw_power = 0.0
        self.waiting_for_settle = False
        self.action_button = None
        self.reset()

    def reset(self):
        self.dice = []
        self.tries_left = MAX_TRIES
        self.current_level = 0
        self.game_state = "playing"
        self.selected_index = 0
        self.charging_throw = False
        self.throw_power = 0.0
        self.waiting_for_settle = False
        self.action_button = None
        setup_level_dice(self.dice, self.current_level, self.floor_rect)

    def next_level(self):
        self.current_level += 1
        self.tries_left = MAX_TRIES
        self.game_state = "playing"
        self.selected_index = 0
        self.charging_throw = False
        self.throw_power = 0.0
        self.waiting_for_settle = False
        self.action_button = None
        setup_level_dice(self.dice, self.current_level, self.floor_rect)

    def grant_shout_retry(self):
        self.tries_left = SHOUT_RETRY_TRIES
        self.game_state = "playing"
        self.charging_throw = False
        self.throw_power = 0.0
        self.waiting_for_settle = False
        self.action_button = None
        if self.dice:
            select_die(self.dice, self.selected_index)


class ShoutMeter:
    def __init__(self, threshold):
        self.threshold = threshold
        self.volume = 0.0
        self.available = False
        self.error = None
        self.stream = None
        self.was_loud = False

    def start(self):
        if sd is None:
            self.error = "Mic unavailable - hold Space to charge."
            return

        try:
            self.stream = sd.RawInputStream(
                samplerate=16000,
                blocksize=1024,
                channels=1,
                dtype="int16",
                callback=self._audio_callback,
            )
            self.stream.start()
            self.available = True
        except Exception:
            self.error = "Mic unavailable - hold Space to charge."
            self.available = False

    def stop(self):
        if self.stream is None:
            return

        try:
            self.stream.stop()
            self.stream.close()
        except Exception:
            pass
        self.stream = None

    def _audio_callback(self, indata, frames, time_info, status):
        samples = array.array("h")
        samples.frombytes(bytes(indata))
        if not samples:
            self.volume = 0.0
            return

        square_sum = sum(sample * sample for sample in samples)
        rms = math.sqrt(square_sum / len(samples)) / 32768
        self.volume = min(1.0, rms)

    def consume_shout(self):
        is_loud = self.available and self.volume >= self.threshold
        if is_loud and not self.was_loud:
            self.was_loud = True
            return True

        if not is_loud:
            self.was_loud = False

        return False

    def power_ratio(self):
        return min(1.0, self.volume / self.threshold)


class AnimatedGif:
    def __init__(self, frames, durations):
        self.frames = frames
        self.durations = durations
        self.total_duration = sum(durations)
        self.started_at = pygame.time.get_ticks()

    def restart(self):
        self.started_at = pygame.time.get_ticks()

    def get_current_frame(self):
        if len(self.frames) == 1 or self.total_duration <= 0:
            return self.frames[0]

        elapsed = (pygame.time.get_ticks() - self.started_at) % self.total_duration
        for frame, duration in zip(self.frames, self.durations):
            if elapsed < duration:
                return frame
            elapsed -= duration

        return self.frames[-1]


def load_animated_gif(path, size):
    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError(
            "Animated GIFs require Pillow. Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    frames = []
    durations = []
    with Image.open(path) as gif:
        for gif_frame in ImageSequence.Iterator(gif):
            rgba_frame = gif_frame.convert("RGBA")
            frame = pygame.image.fromstring(
                rgba_frame.tobytes(),
                rgba_frame.size,
                "RGBA",
            ).convert_alpha()
            frames.append(pygame.transform.smoothscale(frame, size))
            durations.append(max(20, gif_frame.info.get("duration", 80)))

    if not frames:
        image = pygame.image.load(path).convert_alpha()
        frames.append(pygame.transform.smoothscale(image, size))
        durations.append(1000)

    return AnimatedGif(frames, durations)


def draw_floor_tiles(screen, tile_image):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    grid_width = tile_width * FLOOR_TILE_COLUMNS
    grid_height = tile_height * FLOOR_TILE_ROWS
    left = (WIDTH - grid_width) // 2
    top = (HEIGHT - grid_height) // 2

    for row in range(FLOOR_TILE_ROWS):
        for column in range(FLOOR_TILE_COLUMNS):
            screen.blit(tile_image, (left + column * tile_width, top + row * tile_height))


def get_floor_tile_grid_rect(tile_image):
    tile_width = tile_image.get_width()
    tile_height = tile_image.get_height()
    grid_width = tile_width * FLOOR_TILE_COLUMNS
    grid_height = tile_height * FLOOR_TILE_ROWS
    left = (WIDTH - grid_width) // 2
    top = (HEIGHT - grid_height) // 2
    return pygame.Rect(left, top, grid_width, grid_height)


def draw_menu_overlay(screen):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 105))
    screen.blit(overlay, (0, 0))


def draw_transparent_panel(screen, rect, alpha=185):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill((*PANEL_BG, alpha))
    screen.blit(panel, rect.topleft)
    pygame.draw.rect(screen, WHITE, rect, 3, border_radius=22)


def draw_button(screen, font, rect, text, enabled=True):
    mouse_pos = pygame.mouse.get_pos()

    if not enabled:
        color = (90, 90, 90)
        text_color = (160, 160, 160)
        border_color = GRAY
    elif rect.collidepoint(mouse_pos):
        color = GOLD
        text_color = BLACK
        border_color = WHITE
    else:
        color = DARK
        text_color = WHITE
        border_color = WHITE

    pygame.draw.rect(screen, color, rect, border_radius=14)
    pygame.draw.rect(screen, border_color, rect, 3, border_radius=14)

    label = font.render(text, True, text_color)
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.centery - label.get_height() // 2))


def draw_back_button(screen, enabled=True):
    rect = pygame.Rect(24, 24, 70, 58)

    if enabled:
        color = DARK
        border_color = WHITE
    else:
        color = (90, 90, 90)
        border_color = GRAY

    pygame.draw.rect(screen, color, rect, border_radius=14)
    pygame.draw.rect(screen, border_color, rect, 3, border_radius=14)

    center_y = rect.centery
    pygame.draw.line(screen, border_color, (rect.x + 45, center_y), (rect.x + 20, center_y), 5)
    pygame.draw.line(screen, border_color, (rect.x + 20, center_y), (rect.x + 35, center_y - 12), 5)
    pygame.draw.line(screen, border_color, (rect.x + 20, center_y), (rect.x + 35, center_y + 12), 5)

    return rect


def draw_hud(screen, font, score, tries_left, current_level):
    def shadowed(text, pos):
        screen.blit(font.render(text, True, HUD_SHADOW), (pos[0] + 2, pos[1] + 2))
        screen.blit(font.render(text, True, HUD_COLOR), pos)

    goal = LEVELS[current_level]
    level_text = f"Level {current_level + 1} / {len(LEVELS)}"
    level_w = font.size(level_text)[0]
    shadowed(level_text, (WIDTH - level_w - 24, 20))

    score_text = f"Score: {score}  |  Goal: {goal}+"
    score_w = font.size(score_text)[0]
    shadowed(score_text, (WIDTH - score_w - 24, 50))

    tries_text = f"Tries left: {tries_left}"
    tries_w = font.size(tries_text)[0]
    shadowed(tries_text, (WIDTH - tries_w - 24, 80))


def draw_power_bar(screen, font, power, charging):
    bar_width = 260
    bar_height = 22
    bar_rect = pygame.Rect(24, 86, bar_width, bar_height)
    fill_rect = bar_rect.copy()
    fill_rect.width = round(bar_width * power)

    pygame.draw.rect(screen, (35, 35, 48), bar_rect, border_radius=7)
    if fill_rect.width > 0:
        fill_color = (255, 205, 80) if charging else (120, 120, 145)
        pygame.draw.rect(screen, fill_color, fill_rect, border_radius=7)
    pygame.draw.rect(screen, (170, 170, 190), bar_rect, 2, border_radius=7)

    label = "Throw power"
    label_surface = font.render(label, True, HUD_COLOR)
    screen.blit(label_surface, (bar_rect.x, bar_rect.y + bar_rect.height + 6))


def draw_shout_bar(screen, font, shout_meter, y):
    bar_width = 420
    bar_height = 24
    bar_rect = pygame.Rect((WIDTH - bar_width) // 2, y, bar_width, bar_height)
    volume_ratio = min(1.0, shout_meter.volume / shout_meter.threshold)
    fill_rect = bar_rect.copy()
    fill_rect.width = round(bar_width * volume_ratio)

    pygame.draw.rect(screen, (35, 35, 48), bar_rect, border_radius=7)
    if fill_rect.width > 0:
        fill_color = (110, 255, 150) if shout_meter.volume >= shout_meter.threshold else (255, 205, 80)
        pygame.draw.rect(screen, fill_color, fill_rect, border_radius=7)
    pygame.draw.rect(screen, (170, 170, 190), bar_rect, 2, border_radius=7)

    if shout_meter.available:
        label = "Scream volume"
    else:
        label = shout_meter.error or "Mic unavailable - hold Space to charge."

    label_surface = font.render(label, True, HUD_COLOR)
    screen.blit(label_surface, ((WIDTH - label_surface.get_width()) // 2, y + bar_height + 7))


def setup_level_dice(dice, level, floor_rect):
    dice[:] = []
    for _ in range(LEVEL_DICE[level]):
        add_die(dice, floor_rect)
    select_die(dice, 0)


def attempt_throw(die, dice, power, floor_rect, tries_left):
    if tries_left <= 0 or die["moving"]:
        return tries_left
    if throw_die(die, power, floor_rect, dice):
        return tries_left - 1

    return tries_left


def update_throw_power(current_power, dt_ms, shout_meter):
    if THROW_POWER_MODE == "shout" and shout_meter.available:
        return max(current_power, shout_meter.power_ratio())

    return min(1.0, current_power + POWER_CHARGE_SPEED * (dt_ms / 1000.0))


def draw_end_gif(screen, animation, position):
    frame = animation.get_current_frame()
    screen.blit(frame, position)


def draw_end_screen(
    screen,
    result_font,
    hud_font,
    score,
    game_state,
    current_level,
    shout_meter,
    qr_code,
    end_gifs,
):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    screen.blit(overlay, (0, 0))

    if game_state == "level_complete":
        result_text = f"Level {current_level + 1} Complete!"
        result_color = (255, 215, 70)
        button_text = "Next Level"
    elif game_state == "won":
        result_text = "You Won!"
        result_color = (110, 255, 150)
        button_text = "Play Again"
    else:
        result_text = "Game Over"
        result_color = (255, 90, 90)
        button_text = "Play Again"

    result_surface = result_font.render(result_text, True, result_color)
    screen.blit(result_surface, ((WIDTH - result_surface.get_width()) // 2, HEIGHT // 2 - 90))

    if game_state == "game_over":
        draw_end_gif(screen, end_gifs["rage_quit"], ((WIDTH - END_SCREEN_GIF_SIZE[0]) // 2, 78))

    goal = LEVELS[current_level]
    score_text = f"Score: {score}  |  Required: {goal}+"
    score_surface = hud_font.render(score_text, True, HUD_COLOR)
    screen.blit(score_surface, ((WIDTH - score_surface.get_width()) // 2, HEIGHT // 2 - 20))

    button_y = HEIGHT // 2 + 40
    if game_state == "game_over":
        payment_lines = [
            "You have used all free tries.",
            "Scan the QR code, or scream loud enough for extra tries.",
        ]
        for i, line in enumerate(payment_lines):
            payment_surface = hud_font.render(line, True, HUD_COLOR)
            screen.blit(
                payment_surface,
                ((WIDTH - payment_surface.get_width()) // 2, HEIGHT // 2 + 18 + i * 32),
            )
        qr_rect = qr_code.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 152))
        screen.blit(qr_code, qr_rect)
        draw_shout_bar(screen, hud_font, shout_meter, HEIGHT // 2 + 240)
        return None

    button_w, button_h = 220, 52
    button_rect = pygame.Rect((WIDTH - button_w) // 2, button_y, button_w, button_h)
    pygame.draw.rect(screen, (60, 60, 85), button_rect, border_radius=10)
    pygame.draw.rect(screen, (160, 160, 200), button_rect, 2, border_radius=10)

    btn_label = hud_font.render(button_text, True, HUD_COLOR)
    screen.blit(
        btn_label,
        (
            button_rect.x + (button_w - btn_label.get_width()) // 2,
            button_rect.y + (button_h - btn_label.get_height()) // 2,
        ),
    )

    return button_rect


def intro_screen(screen, clock, floor_tile, title_font, hud_font):
    start_time = pygame.time.get_ticks()

    while pygame.time.get_ticks() - start_time < 3000:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        draw_menu_overlay(screen)

        panel = pygame.Rect(230, 235, 500, 210)
        draw_transparent_panel(screen, panel, alpha=175)

        title = title_font.render("DIE SCREAMING!", True, WHITE)
        subtitle = hud_font.render("Scream. Score. Win.", True, LIGHT_GRAY)

        screen.blit(title, ((WIDTH - title.get_width()) // 2, 285))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, 360))

        pygame.display.flip()
        clock.tick(60)

    return "menu"


def menu_screen(screen, clock, floor_tile, title_font, button_font, hud_font):
    play_button = pygame.Rect(330, 270, 300, 68)
    controls_button = pygame.Rect(330, 360, 300, 68)
    scoring_button = pygame.Rect(330, 450, 300, 68)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos):
                    return "game"
                if controls_button.collidepoint(event.pos):
                    return "controls"
                if scoring_button.collidepoint(event.pos):
                    return "scoring"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        draw_menu_overlay(screen)

        draw_back_button(screen, enabled=False)

        panel = pygame.Rect(240, 105, 480, 455)
        draw_transparent_panel(screen, panel, alpha=175)

        title = title_font.render("DIE SCREAMING!", True, WHITE)
        subtitle = hud_font.render("Multilevel dice score game", True, LIGHT_GRAY)

        screen.blit(title, ((WIDTH - title.get_width()) // 2, 145))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, 215))

        draw_button(screen, button_font, play_button, "PLAY")
        draw_button(screen, button_font, controls_button, "CONTROLS")
        draw_button(screen, button_font, scoring_button, "SCORING")

        pygame.display.flip()
        clock.tick(60)


def controls_screen(screen, clock, floor_tile, title_font, hud_font):
    back_button = pygame.Rect(24, 24, 70, 58)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(event.pos):
                    return "menu"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        draw_menu_overlay(screen)

        back_button = draw_back_button(screen, enabled=True)

        title = title_font.render("CONTROLS", True, WHITE)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 105))

        panel = pygame.Rect(135, 215, 690, 370)
        draw_transparent_panel(screen, panel, alpha=205)

        lines = [
            "Click a die - select it",
            "Hold SPACE and scream - charge throw power",
            "Release SPACE - throw the selected die",
            "ENTER - skip the remaining tries",
            "R - restart the game",
            "ESC or the top-left arrow - return to menu",
            "Goal: reach the required score in every level",
        ]

        for i, line in enumerate(lines):
            text = hud_font.render(line, True, WHITE)
            screen.blit(text, (180, 270 + i * 48))

        pygame.display.flip()
        clock.tick(60)


def scoring_screen(screen, clock, floor_tile, title_font, hud_font):
    back_button = pygame.Rect(24, 24, 70, 58)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.collidepoint(event.pos):
                    return "menu"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        draw_menu_overlay(screen)

        back_button = draw_back_button(screen, enabled=True)

        title = title_font.render("SCORING", True, WHITE)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 105))

        panel = pygame.Rect(115, 190, 730, 420)
        draw_transparent_panel(screen, panel, alpha=205)

        lines = [
            "Each die has a value from 0 to 9.",
            "Single die: adds its face value.",
            "Pair or more: value x number of dice x number of dice.",
            "Example: three 7s score 7 x 3 x 3 = 63 points.",
            "Straight: 3 or more consecutive unique values score sum x 10.",
            "Example: 2, 3, 4, 5 score (2 + 3 + 4 + 5) x 10 = 140.",
            "Dice used in a straight do not also score as singles.",
        ]

        for i, line in enumerate(lines):
            text = hud_font.render(line, True, WHITE)
            screen.blit(text, (150, 245 + i * 45))

        pygame.display.flip()
        clock.tick(60)


def game_loop(screen, clock, floor_tile, title_font, hud_font, result_font, game_session, qr_code, end_gifs):
    floor_rect = game_session.floor_rect
    faces = load_d10_faces()
    shout_meter = ShoutMeter(SHOUT_VOLUME_THRESHOLD)
    shout_meter.start()

    def leave_game(next_state):
        shout_meter.stop()
        return next_state

    menu_button = pygame.Rect(24, 24, 120, 44)
    restart_button = pygame.Rect(160, 24, 145, 44)
    while True:
        dt_ms = clock.tick(60)

        score = calculate_score([die["value"] for die in game_session.dice])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return leave_game("quit")

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button.collidepoint(event.pos):
                    return leave_game("menu")

                if restart_button.collidepoint(event.pos) and game_session.game_state != "game_over":
                    game_session.reset()
                    continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return leave_game("menu")

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
                and game_session.game_state != "game_over"
            ):
                game_session.reset()
                continue

            if game_session.game_state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if game_session.dice and game_session.tries_left > 0 and not any_die_moving(game_session.dice):
                        game_session.charging_throw = True
                        game_session.throw_power = 0.0

                elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    if game_session.charging_throw and game_session.dice:
                        game_session.tries_left = attempt_throw(
                            game_session.dice[game_session.selected_index],
                            game_session.dice,
                            game_session.throw_power,
                            floor_rect,
                            game_session.tries_left,
                        )
                        game_session.waiting_for_settle = True
                    game_session.charging_throw = False
                    game_session.throw_power = 0.0

                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if game_session.tries_left > 0:
                        game_session.tries_left = 0
                        game_session.charging_throw = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_index = die_at_position(game_session.dice, event.pos)
                    if clicked_index is not None and not any_die_moving(game_session.dice):
                        game_session.selected_index = clicked_index
                        select_die(game_session.dice, game_session.selected_index)

            elif game_session.game_state in ("level_complete", "won", "game_over"):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_session.action_button and game_session.action_button.collidepoint(event.pos):
                        if game_session.game_state == "level_complete":
                            game_session.next_level()
                        else:
                            game_session.reset()

        if game_session.charging_throw:
            game_session.throw_power = update_throw_power(
                game_session.throw_power,
                dt_ms,
                shout_meter,
            )

        update_dice_physics(game_session.dice, dt_ms, floor_rect)

        if game_session.waiting_for_settle and not any_die_moving(game_session.dice):
            game_session.waiting_for_settle = False
            if game_session.game_state == "playing" and game_session.tries_left > 0 and game_session.dice:
                game_session.selected_index = (game_session.selected_index + 1) % len(game_session.dice)
                select_die(game_session.dice, game_session.selected_index)

        score = calculate_score([die["value"] for die in game_session.dice])

        if game_session.game_state == "playing" and not any_die_moving(game_session.dice):
            if score >= LEVELS[game_session.current_level]:
                next_state = (
                    "won"
                    if game_session.current_level == len(LEVELS) - 1
                    else "level_complete"
                )
                game_session.game_state = next_state
            elif game_session.tries_left == 0:
                end_gifs["rage_quit"].restart()
                game_session.game_state = "game_over"

        if game_session.game_state == "game_over" and shout_meter.consume_shout():
            game_session.grant_shout_retry()

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)

        title_surface = title_font.render("DIE SCREAMING!", True, TITLE_COLOR)
        screen.blit(title_surface, (330, 18))

        draw_button(screen, hud_font, menu_button, "MENU")
        restart_enabled = game_session.game_state != "game_over"
        draw_button(screen, hud_font, restart_button, "RESTART", enabled=restart_enabled)

        draw_dice(screen, faces, game_session.dice)
        draw_dice_summary(screen, faces, game_session.dice, hud_font, floor_rect)
        draw_hud(
            screen,
            hud_font,
            score,
            game_session.tries_left,
            game_session.current_level,
        )
        draw_power_bar(screen, hud_font, game_session.throw_power, game_session.charging_throw)

        if game_session.game_state == "playing":
            if game_session.tries_left > 0:
                if any_die_moving(game_session.dice):
                    hint_text = "Waiting for dice to stop..."
                elif game_session.charging_throw:
                    hint_text = "Keep holding Space and scream to charge. Release Space to throw."
                else:
                    hint_text = "Hold Space, scream to charge, release to throw. Click a die to select."
            else:
                hint_text = "Waiting for rolls to finish..."

            hint_surface = hud_font.render(hint_text, True, (200, 200, 210))
            screen.blit(
                hint_surface,
                (
                    (WIDTH - hint_surface.get_width()) // 2,
                    HEIGHT - hint_surface.get_height() - 22,
                ),
            )

        elif game_session.game_state in ("level_complete", "won", "game_over"):
            game_session.action_button = draw_end_screen(
                screen,
                result_font,
                hud_font,
                score,
                game_session.game_state,
                game_session.current_level,
                shout_meter,
                qr_code,
                end_gifs,
            )

        pygame.display.flip()


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DIE SCREAMING!")

    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 52)
    button_font = pygame.font.Font(None, 44)
    hud_font = pygame.font.Font(None, 32)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    qr_code = pygame.image.load(QR_CODE_PATH).convert()
    qr_code = pygame.transform.scale(qr_code, (QR_CODE_SIZE, QR_CODE_SIZE))
    end_gifs = {
        "win": load_animated_gif(WIN_SCREEN_GIF_PATH, END_SCREEN_GIF_SIZE),
        "rage_quit": load_animated_gif(RAGE_QUIT_GIF_PATH, END_SCREEN_GIF_SIZE),
    }
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    game_session = GameSession(floor_rect)

    state = intro_screen(screen, clock, floor_tile, title_font, hud_font)

    while state != "quit":
        if state == "menu":
            state = menu_screen(screen, clock, floor_tile, title_font, button_font, hud_font)
        elif state == "controls":
            state = controls_screen(screen, clock, floor_tile, title_font, hud_font)
        elif state == "scoring":
            state = scoring_screen(screen, clock, floor_tile, title_font, hud_font)
        elif state == "game":
            state = game_loop(
                screen,
                clock,
                floor_tile,
                title_font,
                hud_font,
                result_font,
                game_session,
                qr_code,
                end_gifs,
            )
        else:
            state = "menu"

    pygame.quit()


if __name__ == "__main__":
    main()
