import pygame

from game import GameSession, game_loop
from screens import controls_screen, intro_screen, menu_screen, scoring_screen
from settings import (
    END_SCREEN_GIF_SIZE,
    FLOOR_TILE_PATH,
    HEIGHT,
    QR_CODE_PATH,
    QR_CODE_SIZE,
    RAGE_QUIT_GIF_PATH,
    WIDTH,
)
from ui import get_floor_tile_grid_rect, load_animated_gif


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("DIE SCREAMING!")

    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 52)
    button_font = pygame.font.Font(None, 44)
    hud_font = pygame.font.Font(None, 32)
    formula_font = pygame.font.Font(None, 24)
    result_font = pygame.font.Font(None, 80)

    floor_tile = pygame.image.load(FLOOR_TILE_PATH).convert_alpha()
    qr_code = pygame.image.load(QR_CODE_PATH).convert()
    qr_code = pygame.transform.scale(qr_code, (QR_CODE_SIZE, QR_CODE_SIZE))
    end_gifs = {
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
                formula_font,
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
