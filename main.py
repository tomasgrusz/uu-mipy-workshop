import pygame

from d10_board import add_die, die_at_position, draw_dice, reset_dice_values, select_die, start_die_roll, update_die_roll
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
MAX_TRIES = 10


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


def spawn_roll_effect(roll_effects, floor_rect, color_variant, roll_state):
    roll_effects[:] = [roll_effect for roll_effect in roll_effects if roll_effect["color_variant"] != color_variant]
    roll_effects.append(create_roll_effect(floor_rect, color_variant, roll_state))


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
    label_font = pygame.font.Font(None, 44)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    faces = load_d10_faces()

    dice = []
    roll_effects = []
    tries_left = MAX_TRIES
    current_level = 0
    game_state = "playing"
    selected_index = 0
    action_button = None
    add_die(dice)
    running = True

    def full_reset():
        nonlocal dice, roll_effects, tries_left, current_level, game_state, selected_index, action_button
        dice = []
        roll_effects = []
        tries_left = MAX_TRIES
        current_level = 0
        game_state = "playing"
        selected_index = 0
        action_button = None
        add_die(dice)

    while running:
        dt_ms = clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif game_state == "playing":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                    if add_die(dice):
                        selected_index = len(dice) - 1
                        select_die(dice, selected_index)
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if dice:
                        tries_left = attempt_roll(dice[selected_index], roll_effects, floor_rect, tries_left)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked_index = die_at_position(dice, event.pos)
                    if clicked_index is not None:
                        selected_index = clicked_index
                        select_die(dice, selected_index)
                        tries_left = attempt_roll(dice[selected_index], roll_effects, floor_rect, tries_left)

            elif game_state in ("level_complete", "won", "game_over"):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if action_button and action_button.collidepoint(event.pos):
                        if game_state == "level_complete":
                            current_level += 1
                            roll_effects = []
                            tries_left = MAX_TRIES
                            game_state = "playing"
                            action_button = None
                            reset_dice_values(dice)
                        else:
                            full_reset()

        for die in dice:
            update_die_roll(die)

        update_roll_effects(roll_effects, dt_ms, floor_rect)

        score = sum(die["value"] for die in dice)

        if game_state == "playing" and tries_left == 0:
            if not any(die["roll_state"]["active"] for die in dice):
                if score >= LEVELS[current_level]:
                    game_state = "won" if current_level == len(LEVELS) - 1 else "level_complete"
                else:
                    game_state = "game_over"

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        title_surface = title_font.render("D10 Dice Roller", True, TITLE_COLOR)
        screen.blit(title_surface, (24, 18))
        draw_dice(screen, faces, dice, label_font)
        draw_roll_effects(screen, faces, roll_effects)
        draw_hud(screen, hud_font, score, tries_left, current_level)

        if game_state == "playing":
            if tries_left > 0:
                hint_text = "Click a die or press Space to roll. Press A to add a die."
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
