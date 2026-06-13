import pygame

from settings import BACKGROUND_COLOR, LIGHT_GRAY, WHITE, WIDTH
from ui import (
    draw_back_button,
    draw_button,
    draw_floor_tiles,
    draw_menu_overlay,
    draw_transparent_panel,
)


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
