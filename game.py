import pygame

from audio import ShoutMeter
from d10_dice import (
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
from d10_score_formula import draw_score_formula
from d10_sprites import load_d10_faces
from settings import (
    BACKGROUND_COLOR,
    HEIGHT,
    END_SCREEN_GIF_SIZE,
    LEVEL_DICE,
    LEVELS,
    MAX_TRIES,
    POWER_CHARGE_SPEED,
    SHOUT_RETRY_TRIES,
    SHOUT_VOLUME_THRESHOLD,
    THROW_POWER_MODE,
    TITLE_COLOR,
    WIDTH,
    WIN_SCREEN_GIF_PATH,
)
from ui import (
    draw_button,
    draw_end_screen,
    draw_floor_tiles,
    draw_hud,
    load_animated_gif,
    draw_power_bar,
)


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


def game_loop(
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
):
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

        score = calculate_score([die["value"] for die in game_session.dice])

        if game_session.game_state == "playing" and not any_die_moving(game_session.dice):
            if score >= LEVELS[game_session.current_level]:
                next_state = (
                    "won"
                    if game_session.current_level == len(LEVELS) - 1
                    else "level_complete"
                )
                if next_state == "won":
                    if "win_screen" not in end_gifs:
                        end_gifs["win_screen"] = load_animated_gif(
                            WIN_SCREEN_GIF_PATH,
                            END_SCREEN_GIF_SIZE,
                        )
                    end_gifs["win_screen"].restart()
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
        draw_hud(screen, hud_font, score, game_session.tries_left, game_session.current_level)
        draw_score_formula(screen, faces, formula_font, game_session.dice)
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
