import pygame

from settings import (
    BLACK,
    DARK,
    END_SCREEN_GIF_SIZE,
    FLOOR_TILE_COLUMNS,
    FLOOR_TILE_ROWS,
    GOLD,
    GRAY,
    HEIGHT,
    HUD_COLOR,
    HUD_SHADOW,
    LEVELS,
    LIGHT_GRAY,
    PANEL_BG,
    WHITE,
    WIDTH,
)


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

    label_surface = font.render("Throw power", True, HUD_COLOR)
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
