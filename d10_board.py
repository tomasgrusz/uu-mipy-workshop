import math

import pygame

from d10_roll import create_idle_roll_state, get_roll_face, start_roll
from d10_sprites import get_face, scale_face


WIDTH = 960
HEIGHT = 720
GRID_COLUMNS = 3
MAX_DICE = 6
DIE_SIZE = 64
GRID_GAP = 8
GRID_LEFT_MARGIN = 20
GRID_BOTTOM_MARGIN = 20
LABEL_COLOR = (255, 255, 255)
LABEL_BG = (0, 0, 0, 100)
SELECTED_COLOR = (255, 230, 140)


def next_color_variant(dice):
    used_colors = {die["color_variant"] for die in dice}
    for color_variant in range(10):
        if color_variant not in used_colors:
            return color_variant
    return len(dice) % 10


def create_label_surface(font, text, text_color=LABEL_COLOR, background_color=LABEL_BG, padding=10):
    text_surface = font.render(text, True, text_color)
    label_surface = pygame.Surface((text_surface.get_width() + padding * 2, text_surface.get_height() + padding), pygame.SRCALPHA)
    label_surface.fill(background_color)
    label_surface.blit(text_surface, (padding, padding // 2))
    return label_surface


def create_die(color_variant, selected=False):
    return {
        "rect": pygame.Rect(0, 0, DIE_SIZE, DIE_SIZE),
        "value": 0,
        "color_variant": color_variant,
        "roll_state": create_idle_roll_state(),
        "selected": selected,
    }


def arrange_dice(dice):
    if not dice:
        return

    rows = math.ceil(len(dice) / GRID_COLUMNS)
    total_width = GRID_COLUMNS * DIE_SIZE + (GRID_COLUMNS - 1) * GRID_GAP
    total_height = rows * DIE_SIZE + (rows - 1) * GRID_GAP
    left = GRID_LEFT_MARGIN
    top = HEIGHT - GRID_BOTTOM_MARGIN - total_height

    for index, die in enumerate(dice):
        column = index % GRID_COLUMNS
        row = index // GRID_COLUMNS
        die["rect"].topleft = (
            left + column * (DIE_SIZE + GRID_GAP),
            top + row * (DIE_SIZE + GRID_GAP),
        )


def add_die(dice):
    if len(dice) >= MAX_DICE:
        return False

    dice.append(create_die(next_color_variant(dice), selected=not dice))
    arrange_dice(dice)
    return True


def select_die(dice, selected_index):
    for index, die in enumerate(dice):
        die["selected"] = index == selected_index


def die_at_position(dice, position):
    for index, die in enumerate(dice):
        if die["rect"].collidepoint(position):
            return index
    return None


def start_die_roll(die):
    if die["roll_state"]["active"]:
        return False

    die["roll_state"] = start_roll()
    return die["roll_state"]


def update_die_roll(die):
    roll_state = die["roll_state"]
    if not roll_state["active"]:
        return 0

    face_value = get_roll_face(roll_state)
    if roll_state["active"]:
        return 0

    die["value"] = roll_state["result"]
    die["roll_state"] = create_idle_roll_state(die["value"])
    return face_value


def draw_dice(screen, faces, dice, label_font):
    for die in dice:
        roll_state = die["roll_state"]
        if roll_state["active"]:
            face_value = get_roll_face(roll_state)
        else:
            face_value = die["value"]
        color_variant = die["color_variant"]

        die_face = scale_face(get_face(faces, face_value, color_variant), DIE_SIZE)
        screen.blit(die_face, die["rect"].topleft)

        value_label = create_label_surface(label_font, str(face_value), padding=12)
        label_position = (
            die["rect"].x + (DIE_SIZE - value_label.get_width()) // 2,
            die["rect"].y + 10,
        )
        screen.blit(value_label, label_position)

        if die["selected"]:
            outline_rect = die["rect"].inflate(8, 8)
            pygame.draw.rect(screen, SELECTED_COLOR, outline_rect, 3, border_radius=16)