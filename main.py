import pygame

from d10_board import add_die, die_at_position, draw_dice, select_die, start_die_roll, update_die_roll
from d10_roll_effects import create_roll_effect, draw_roll_effects, update_roll_effects
from d10_sprites import load_d10_faces


WIDTH = 960
HEIGHT = 720
BACKGROUND_COLOR = (24, 24, 32)
FLOOR_TILE_PATH = "sprites/floor-tile.png"
FLOOR_TILE_COLUMNS = 20
FLOOR_TILE_ROWS = 10

TITLE_COLOR = (240, 240, 245)
HUD_COLOR = (245, 245, 245)
HUD_SHADOW = (0, 0, 0)

LEVELS = [5, 10, 15, 20, 30]
LEVEL_DICE = [1, 2, 3, 4, 6]
MAX_TRIES = 10

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (35, 35, 35)
GRAY = (130, 130, 130)
LIGHT_GRAY = (210, 210, 210)
GOLD = (230, 180, 60)
PANEL_BG = (20, 20, 20)


class GameSession:
    def __init__(self):
        self.dice = []
        self.roll_effects = []
        self.tries_left = MAX_TRIES
        self.current_level = 0
        self.game_state = "playing"
        self.selected_index = 0
        self.action_button = None
        self.reset()

    def reset(self):
        self.dice = []
        self.roll_effects = []
        self.tries_left = MAX_TRIES
        self.current_level = 0
        self.game_state = "playing"
        self.selected_index = 0
        self.action_button = None
        setup_level_dice(self.dice, self.current_level)

    def next_level(self):
        self.current_level += 1
        self.roll_effects = []
        self.tries_left = MAX_TRIES
        self.game_state = "playing"
        self.selected_index = 0
        self.action_button = None
        setup_level_dice(self.dice, self.current_level)


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


def spawn_roll_effect(roll_effects, floor_rect, color_variant, roll_state):
    roll_effects[:] = [
        roll_effect for roll_effect in roll_effects
        if roll_effect["color_variant"] != color_variant
    ]
    roll_effects.append(create_roll_effect(floor_rect, color_variant, roll_state))


def setup_level_dice(dice, level):
    dice[:] = []
    for _ in range(LEVEL_DICE[level]):
        add_die(dice)

    if dice:
        select_die(dice, 0)


def attempt_roll(die, roll_effects, floor_rect, tries_left):
    if tries_left <= 0 or die["roll_state"]["active"]:
        return tries_left

    roll_state = start_die_roll(die)

    if roll_state:
        spawn_roll_effect(roll_effects, floor_rect, die["color_variant"], roll_state)
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


def game_loop(screen, clock, floor_tile, title_font, hud_font, label_font, result_font, game_session):
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    faces = load_d10_faces()

    menu_button = pygame.Rect(24, 24, 120, 44)
    restart_button = pygame.Rect(160, 24, 145, 44)
    skip_button_rect = pygame.Rect(WIDTH - 176, HEIGHT - 66, 152, 44)

    while True:
        dt_ms = clock.tick(60)

        score = sum(die["value"] for die in game_session.dice)

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
                    if game_session.dice:
                        game_session.tries_left = attempt_roll(
                            game_session.dice[game_session.selected_index],
                            game_session.roll_effects,
                            floor_rect,
                            game_session.tries_left,
                        )

                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if game_session.tries_left > 0:
                        game_session.tries_left = 0

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_session.tries_left > 0 and skip_button_rect.collidepoint(event.pos):
                        game_session.tries_left = 0
                    else:
                        clicked_index = die_at_position(game_session.dice, event.pos)
                        if clicked_index is not None:
                            game_session.selected_index = clicked_index
                            select_die(game_session.dice, game_session.selected_index)

                            game_session.tries_left = attempt_roll(
                                game_session.dice[game_session.selected_index],
                                game_session.roll_effects,
                                floor_rect,
                                game_session.tries_left,
                            )

            elif game_session.game_state in ("level_complete", "won", "game_over"):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if game_session.action_button and game_session.action_button.collidepoint(event.pos):
                        if game_session.game_state == "level_complete":
                            game_session.next_level()
                        else:
                            game_session.reset()

        for die in game_session.dice:
            update_die_roll(die)

        update_roll_effects(game_session.roll_effects, dt_ms, floor_rect)

        score = sum(die["value"] for die in game_session.dice)

        if game_session.game_state == "playing" and game_session.tries_left == 0:
            if not any(die["roll_state"]["active"] for die in game_session.dice):
                if score >= LEVELS[game_session.current_level]:
                    game_session.game_state = (
                        "won"
                        if game_session.current_level == len(LEVELS) - 1
                        else "level_complete"
                    )
                else:
                    game_session.game_state = "game_over"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)

        title_surface = title_font.render("D10 Dice Roller", True, TITLE_COLOR)
        screen.blit(title_surface, (330, 18))

        draw_button(screen, hud_font, menu_button, "MENU")
        draw_button(screen, hud_font, restart_button, "RESTART")

        draw_dice(screen, faces, game_session.dice, label_font)
        draw_roll_effects(screen, faces, game_session.roll_effects)
        draw_hud(
            screen,
            hud_font,
            score,
            game_session.tries_left,
            game_session.current_level,
        )

        if game_session.game_state == "playing":
            if game_session.tries_left > 0:
                hint_text = "Click a die or press Space to roll. Press R to restart."
                pygame.draw.rect(screen, (60, 60, 85), skip_button_rect, border_radius=8)
                pygame.draw.rect(screen, (140, 140, 170), skip_button_rect, 2, border_radius=8)

                skip_label = hud_font.render("Skip Turns", True, HUD_COLOR)
                screen.blit(
                    skip_label,
                    (
                        skip_button_rect.x + (skip_button_rect.width - skip_label.get_width()) // 2,
                        skip_button_rect.y + (skip_button_rect.height - skip_label.get_height()) // 2,
                    ),
                )
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
    label_font = pygame.font.Font(None, 44)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()

    game_session = GameSession()

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
                label_font,
                result_font,
                game_session,
            )
        else:
            state = "menu"

    pygame.quit()


if __name__ == "__main__":
    main()