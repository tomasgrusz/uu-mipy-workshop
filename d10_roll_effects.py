import copy
import random

import pygame

from d10_roll import create_idle_roll_state, get_roll_face
from d10_sprites import get_face, scale_face


MINI_DIE_SIZE = 36
BASE_TRAVEL_DURATION_MS = 2100
BASE_SPIN_DEGREES = 1800
ROLL_SPIN_DAMPING = 0.98


def create_roll_effect(floor_rect, color_variant, roll_state):
    start_x = floor_rect.right - MINI_DIE_SIZE - 10
    start_y = floor_rect.centery - MINI_DIE_SIZE // 2
    target_x = floor_rect.centerx - MINI_DIE_SIZE // 2 + random.randint(-28, 28)
    target_x = max(floor_rect.left + 170, min(target_x, floor_rect.right - MINI_DIE_SIZE - 170))
    travel_seconds = (BASE_TRAVEL_DURATION_MS / 1000.0) * random.uniform(0.85, 1.05)

    return {
        "start_time": pygame.time.get_ticks(),
        "duration_ms": BASE_TRAVEL_DURATION_MS * random.uniform(0.85, 1.05),
        "x": float(start_x),
        "y": float(start_y),
        "start_x": float(start_x),
        "start_y": float(start_y),
        "target_x": float(target_x),
        "target_y": float(start_y),
        "vx": (target_x - start_x) / travel_seconds,
        "vy": 0.0,
        "angle": random.uniform(0, 360),
        "spin_velocity": BASE_SPIN_DEGREES / travel_seconds * random.uniform(0.9, 1.1),
        "color_variant": color_variant,
        "roll_state": copy.deepcopy(roll_state),
        "active_motion": True,
    }


def update_roll_effect(roll_effect, dt_ms, floor_rect):
    dt_seconds = dt_ms / 1000.0
    frame_scale = dt_ms / 16.0

    if abs(roll_effect["spin_velocity"]) > 0.01:
        roll_effect["angle"] = (roll_effect["angle"] + roll_effect["spin_velocity"] * dt_seconds) % 360
        roll_effect["spin_velocity"] *= ROLL_SPIN_DAMPING ** frame_scale
        if abs(roll_effect["spin_velocity"]) <= 0.01:
            roll_effect["spin_velocity"] = 0.0

    if roll_effect["active_motion"]:
        elapsed_ms = pygame.time.get_ticks() - roll_effect["start_time"]
        progress = min(elapsed_ms / roll_effect["duration_ms"], 1.0)
        eased_progress = 1 - (1 - progress) ** 3

        roll_effect["x"] = roll_effect["start_x"] + (roll_effect["target_x"] - roll_effect["start_x"]) * eased_progress
        roll_effect["y"] = roll_effect["start_y"] + (roll_effect["target_y"] - roll_effect["start_y"]) * eased_progress

        if progress >= 1.0:
            roll_effect["x"] = roll_effect["target_x"]
            roll_effect["y"] = roll_effect["target_y"]
            roll_effect["active_motion"] = False

    roll_effect["x"] = max(floor_rect.left + 4, min(roll_effect["x"], floor_rect.right - MINI_DIE_SIZE - 4))
    roll_effect["y"] = max(floor_rect.top + 4, min(roll_effect["y"], floor_rect.bottom - MINI_DIE_SIZE - 4))


def update_roll_effects(roll_effects, dt_ms, floor_rect):
    for roll_effect in roll_effects:
        update_roll_effect(roll_effect, dt_ms, floor_rect)


def draw_roll_effect(screen, faces, roll_effect):
    if roll_effect["active_motion"]:
        elapsed_ms = pygame.time.get_ticks() - roll_effect["start_time"]
        progress = min(elapsed_ms / roll_effect["duration_ms"], 1.0)
    else:
        progress = 1.0

    angle = roll_effect["angle"]

    roll_state = roll_effect.get("roll_state")
    if not isinstance(roll_state, dict):
        roll_state = create_idle_roll_state(0)

    face_value = get_roll_face(roll_state)
    face_surface = scale_face(get_face(faces, face_value, roll_effect["color_variant"]), MINI_DIE_SIZE)
    rotated_face = pygame.transform.rotozoom(face_surface, angle, 1.0)
    rect = rotated_face.get_rect(center=(roll_effect["x"] + MINI_DIE_SIZE / 2, roll_effect["y"] + MINI_DIE_SIZE / 2))
    screen.blit(rotated_face, rect)


def draw_roll_effects(screen, faces, roll_effects):
    for roll_effect in roll_effects:
        draw_roll_effect(screen, faces, roll_effect)