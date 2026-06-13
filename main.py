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


def draw_hud(screen, font, score):
    score_surface = font.render(f"Score: {score}", True, HUD_COLOR)
    shadow_surface = font.render(f"Score: {score}", True, HUD_SHADOW)
    score_position = (WIDTH - score_surface.get_width() - 24, 20)
    screen.blit(shadow_surface, (score_position[0] + 2, score_position[1] + 2))
    screen.blit(score_surface, score_position)


def spawn_roll_effect(roll_effects, floor_rect, color_variant, roll_state):
    roll_effects[:] = [roll_effect for roll_effect in roll_effects if roll_effect["color_variant"] != color_variant]
    roll_effects.append(create_roll_effect(floor_rect, color_variant, roll_state))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("D10 Dice Roller")
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(None, 40)
    hud_font = pygame.font.Font(None, 32)
    label_font = pygame.font.Font(None, 44)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    floor_rect = get_floor_tile_grid_rect(floor_tile)
    faces = load_d10_faces()
    score = 0
    dice = []
    roll_effects = []
    add_die(dice)
    selected_index = 0
    running = True

    while running:
        dt_ms = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
                if add_die(dice):
                    selected_index = len(dice) - 1
                    select_die(dice, selected_index)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if dice and not dice[selected_index]["roll_state"]["active"]:
                    roll_state = start_die_roll(dice[selected_index])
                    spawn_roll_effect(
                        roll_effects,
                        floor_rect,
                        dice[selected_index]["color_variant"],
                        roll_state,
                    )
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_index = die_at_position(dice, event.pos)
                if clicked_index is not None:
                    selected_index = clicked_index
                    select_die(dice, selected_index)
                    roll_state = start_die_roll(dice[selected_index])
                    spawn_roll_effect(
                        roll_effects,
                        floor_rect,
                        dice[selected_index]["color_variant"],
                        roll_state,
                    )

        for die in dice:
            score += update_die_roll(die)

        update_roll_effects(roll_effects, dt_ms, floor_rect)

        screen.fill(BACKGROUND_COLOR)
        draw_floor_tiles(screen, floor_tile)
        title_surface = title_font.render("D10 Dice Roller", True, TITLE_COLOR)
        screen.blit(title_surface, (24, 18))
        draw_dice(screen, faces, dice, label_font)
        draw_roll_effects(screen, faces, roll_effects)
        draw_hud(screen, hud_font, score)

        hint_surface = hud_font.render("Click a die or press Space to roll. Press A to add a die.", True, (200, 200, 210))
        hint_position = ((WIDTH - hint_surface.get_width()) // 2, HEIGHT - hint_surface.get_height() - 22)
        screen.blit(hint_surface, hint_position)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()