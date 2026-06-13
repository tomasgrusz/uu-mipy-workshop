import pygame
import random

from d10_sprites import ROWS


ROLL_FRAMES = 10
ROLL_FRAME_DURATION_MS = 80


def create_idle_roll_state(value=0):
    return {
        "active": False,
        "start_time": 0,
        "sequence": [value],
        "current_index": 0,
        "result": value,
    }


def start_roll():
    sequence = random.sample(range(ROWS), ROLL_FRAMES)
    return {
        "active": True,
        "start_time": pygame.time.get_ticks(),
        "sequence": sequence,
        "current_index": 0,
        "result": sequence[-1],
    }


def get_roll_face(roll_state):
    if not roll_state["active"]:
        return roll_state["result"]

    elapsed_ms = pygame.time.get_ticks() - roll_state["start_time"]
    frame_index = min(elapsed_ms // ROLL_FRAME_DURATION_MS, ROLL_FRAMES - 1)
    roll_state["current_index"] = frame_index

    if frame_index >= ROLL_FRAMES - 1:
        roll_state["active"] = False
        return roll_state["result"]

    return roll_state["sequence"][frame_index]