import pygame

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
FLOOR_TILE_COLUMNS = 28
FLOOR_TILE_ROWS = 12

TITLE_COLOR = (240, 240, 245)
HUD_COLOR = (245, 245, 245)
HUD_SHADOW = (0, 0, 0)

LEVELS = [5, 10, 25, 50, 100, 250, 500]
LEVEL_DICE = [1, 2, 3, 4, 6, 8, 10]
MAX_TRIES = 10
POWER_CHARGE_SPEED = 0.85

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


def draw_end_screen(screen, result_font, hud_font, score, game_state, current_level):
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

    goal = LEVELS[current_level]
    score_text = f"Score: {score}  |  Required: {goal}+"
    score_surface = hud_font.render(score_text, True, HUD_COLOR)
    screen.blit(score_surface, ((WIDTH - score_surface.get_width()) // 2, HEIGHT // 2 - 20))

    button_w, button_h = 220, 52
    button_rect = pygame.Rect((WIDTH - button_w) // 2, HEIGHT // 2 + 40, button_w, button_h)
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

        title = title_font.render("D10 DICE ROLLER", True, WHITE)
        subtitle = hud_font.render("Roll. Score. Win.", True, LIGHT_GRAY)

        screen.blit(title, ((WIDTH - title.get_width()) // 2, 285))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, 360))

        pygame.display.flip()
        clock.tick(60)

    return "menu"


def menu_screen(screen, clock, floor_tile, title_font, button_font, hud_font):
    play_button = pygame.Rect(330, 290, 300, 76)
    controls_button = pygame.Rect(330, 400, 300, 76)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos):
                    return "game"
                if controls_button.collidepoint(event.pos):
                    return "controls"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        draw_menu_overlay(screen)

        draw_back_button(screen, enabled=False)

        panel = pygame.Rect(240, 105, 480, 455)
        draw_transparent_panel(screen, panel, alpha=175)

        title = title_font.render("D10 DICE ROLLER", True, WHITE)
        subtitle = hud_font.render("Multilevel dice score game", True, LIGHT_GRAY)

        screen.blit(title, ((WIDTH - title.get_width()) // 2, 145))
        screen.blit(subtitle, ((WIDTH - subtitle.get_width()) // 2, 215))

        draw_button(screen, button_font, play_button, "HRÁT")
        draw_button(screen, button_font, controls_button, "OVLÁDÁNÍ")

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

        title = title_font.render("OVLÁDÁNÍ", True, WHITE)
        screen.blit(title, ((WIDTH - title.get_width()) // 2, 105))

        panel = pygame.Rect(135, 215, 690, 370)
        draw_transparent_panel(screen, panel, alpha=205)

        lines = [
            "Kliknutí na kostku - výběr a hod kostkou",
            "SPACE - hod vybranou kostkou",
            "ENTER - přeskočení zbývajících pokusů",
            "R - restart hry",
            "ESC nebo šipka vlevo nahoře - zpět do menu",
            "Cíl hry: dosáhnout požadovaného skóre v každém levelu",
        ]

        for i, line in enumerate(lines):
            text = hud_font.render(line, True, WHITE)
            screen.blit(text, (180, 270 + i * 48))

        pygame.display.flip()
        clock.tick(60)


def game_loop(screen, clock, floor_tile, title_font, hud_font, result_font, game_session):
    floor_rect = game_session.floor_rect
    faces = load_d10_faces()

    menu_button = pygame.Rect(24, 24, 120, 44)
    restart_button = pygame.Rect(160, 24, 145, 44)
    while True:
        dt_ms = clock.tick(60)

        score = calculate_score([die["value"] for die in game_session.dice])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if menu_button.collidepoint(event.pos):
                    return "menu"

                if restart_button.collidepoint(event.pos):
                    game_session.reset()
                    continue

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return "menu"

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
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
            game_session.throw_power = min(
                1.0,
                game_session.throw_power + POWER_CHARGE_SPEED * (dt_ms / 1000.0),
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
                game_session.game_state = (
                    "won"
                    if game_session.current_level == len(LEVELS) - 1
                    else "level_complete"
                )
            elif game_session.tries_left == 0:
                game_session.game_state = "game_over"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)

        title_surface = title_font.render("D10 Dice Roller", True, TITLE_COLOR)
        screen.blit(title_surface, (330, 18))

        draw_button(screen, hud_font, menu_button, "MENU")
        draw_button(screen, hud_font, restart_button, "RESTART")

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
                    hint_text = "Release Space to throw."
                else:
                    hint_text = "Hold Space to charge, release to throw. Click a die to select. Press R to restart."
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
            )

        pygame.display.flip()


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("D10 Dice Roller")

    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 52)
    button_font = pygame.font.Font(None, 44)
    hud_font = pygame.font.Font(None, 32)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    game_session = GameSession(floor_rect)

    state = intro_screen(screen, clock, floor_tile, title_font, hud_font)

    while state != "quit":
        if state == "menu":
            state = menu_screen(screen, clock, floor_tile, title_font, button_font, hud_font)
        elif state == "controls":
            state = controls_screen(screen, clock, floor_tile, title_font, hud_font)
        elif state == "game":
            state = game_loop(
                screen,
                clock,
                floor_tile,
                title_font,
                hud_font,
                result_font,
                game_session,
            )
        else:
            state = "menu"

    pygame.quit()


if __name__ == "__main__":
    main()
