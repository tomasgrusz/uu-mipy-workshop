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
POWER_CHARGE_SPEED = 0.85


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
    bar_rect = pygame.Rect(24, 64, bar_width, bar_height)
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
    screen.blit(btn_label, (
        button_rect.x + (button_w - btn_label.get_width()) // 2,
        button_rect.y + (button_h - btn_label.get_height()) // 2,
    ))

    return button_rect


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("D10 Dice Roller")
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 40)
    hud_font = pygame.font.Font(None, 32)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    faces = load_d10_faces()

    dice = []
    tries_left = MAX_TRIES
    current_level = 0
    game_state = "playing"
    selected_index = 0
    charging_throw = False
    throw_power = 0.0
    waiting_for_settle = False
    action_button = None
    skip_button_rect = pygame.Rect(WIDTH - 176, HEIGHT - 66, 152, 44)
    setup_level_dice(dice, 0, floor_rect)
    running = True

    def full_reset():
        nonlocal tries_left, current_level, game_state, selected_index, charging_throw, throw_power, waiting_for_settle, action_button
        tries_left = MAX_TRIES
        current_level = 0
        game_state = "playing"
        selected_index = 0
        charging_throw = False
        throw_power = 0.0
        waiting_for_settle = False
        action_button = None
        setup_level_dice(dice, 0, floor_rect)

    while running:
        dt_ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif game_state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if dice and tries_left > 0 and not any_die_moving(dice):
                        charging_throw = True
                        throw_power = 0.0
                elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
                    if charging_throw and dice:
                        tries_left = attempt_throw(dice[selected_index], dice, throw_power, floor_rect, tries_left)
                        waiting_for_settle = True
                    charging_throw = False
                    throw_power = 0.0
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if tries_left > 0:
                        tries_left = 0
                        charging_throw = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if tries_left > 0 and skip_button_rect.collidepoint(event.pos):
                        tries_left = 0
                        charging_throw = False
                    else:
                        clicked_index = die_at_position(dice, event.pos)
                        if clicked_index is not None and not any_die_moving(dice):
                            selected_index = clicked_index
                            select_die(dice, selected_index)

            elif game_state in ("level_complete", "won", "game_over"):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if action_button and action_button.collidepoint(event.pos):
                        if game_state == "level_complete":
                            current_level += 1
                            tries_left = MAX_TRIES
                            game_state = "playing"
                            action_button = None
                            selected_index = 0
                            charging_throw = False
                            throw_power = 0.0
                            waiting_for_settle = False
                            setup_level_dice(dice, current_level, floor_rect)
                        else:
                            full_reset()

        if charging_throw:
            throw_power = min(1.0, throw_power + POWER_CHARGE_SPEED * (dt_ms / 1000.0))

        update_dice_physics(dice, dt_ms, floor_rect)

        if waiting_for_settle and not any_die_moving(dice):
            waiting_for_settle = False
            if game_state == "playing" and tries_left > 0 and dice:
                selected_index = (selected_index + 1) % len(dice)
                select_die(dice, selected_index)

        score = sum(die["value"] for die in dice)

        if game_state == "playing" and not any_die_moving(dice):
            if score >= LEVELS[current_level]:
                game_state = "won" if current_level == len(LEVELS) - 1 else "level_complete"
            elif tries_left == 0:
                game_state = "game_over"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        title_surface = title_font.render("D10 Dice Roller", True, TITLE_COLOR)
        screen.blit(title_surface, (24, 18))
        draw_dice(screen, faces, dice)
        draw_dice_summary(screen, faces, dice, hud_font, floor_rect)
        draw_hud(screen, hud_font, score, tries_left, current_level)
        draw_power_bar(screen, hud_font, throw_power, charging_throw)

        if game_state == "playing":
            if tries_left > 0:
                if any_die_moving(dice):
                    hint_text = "Waiting for dice to stop..."
                elif charging_throw:
                    hint_text = "Release Space to throw."
                else:
                    hint_text = "Hold Space to charge, release to throw. Click a die to select."
                pygame.draw.rect(screen, (60, 60, 85), skip_button_rect, border_radius=8)
                pygame.draw.rect(screen, (140, 140, 170), skip_button_rect, 2, border_radius=8)
                skip_label = hud_font.render("Skip Turns", True, HUD_COLOR)
                screen.blit(skip_label, (
                    skip_button_rect.x + (skip_button_rect.width - skip_label.get_width()) // 2,
                    skip_button_rect.y + (skip_button_rect.height - skip_label.get_height()) // 2,
                ))
            else:
                hint_text = "Waiting for rolls to finish..."
            hint_surface = hud_font.render(hint_text, True, (200, 200, 210))
            screen.blit(hint_surface, ((WIDTH - hint_surface.get_width()) // 2, HEIGHT - hint_surface.get_height() - 22))

        elif game_state in ("level_complete", "won", "game_over"):
            action_button = draw_end_screen(screen, result_font, hud_font, score, game_state, current_level)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
