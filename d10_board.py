import math
import random

import pygame

from d10_roll import create_idle_roll_state, get_roll_face, start_roll
from d10_sprites import ROWS, get_face, scale_face


WIDTH = 960
HEIGHT = 720
GRID_COLUMNS = 3
MAX_DICE = 10
DIE_SIZE = 64
GRID_GAP = 8
GRID_LEFT_MARGIN = 20
GRID_BOTTOM_MARGIN = 20
LABEL_COLOR = (255, 255, 255)
SUMMARY_SELECTED_COLOR = (255, 230, 140)
MIN_THROW_SPEED = 10
MAX_THROW_SPEED = 700
FRICTION = 0.988
WALL_BOUNCE = 0.72
DIE_BOUNCE = 0.86
STOP_SPEED = 18
VALUE_CHANGE_INTERVAL_MS = 90
COLLISION_SPIN_FACTOR = 3.0
SUMMARY_DIE_SIZE = 42
SUMMARY_GAP = 16
PLACEMENT_GAP = 18
PLACEMENT_ATTEMPTS = 100


def next_color_variant(dice):
    used_colors = {die["color_variant"] for die in dice}
    for color_variant in range(10):
        if color_variant not in used_colors:
            return color_variant
    return len(dice) % 10


def create_die(color_variant, selected=False):
    return {
        "rect": pygame.Rect(0, 0, DIE_SIZE, DIE_SIZE),
        "hitbox": pygame.Rect(0, 0, DIE_SIZE, DIE_SIZE),
        "x": 0.0,
        "y": 0.0,
        "vx": 0.0,
        "vy": 0.0,
        "angle": 0.0,
        "spin_velocity": 0.0,
        "moving": False,
        "value_timer_ms": 0,
        "roll_sequence": list(range(ROWS)),
        "roll_sequence_index": 0,
        "value": 0,
        "color_variant": color_variant,
        "roll_state": create_idle_roll_state(),
        "selected": selected,
    }


def get_die_center(die):
    return pygame.Vector2(die["x"] + DIE_SIZE / 2, die["y"] + DIE_SIZE / 2)


def get_rotated_hitbox(die):
    angle = die["angle"] % 360
    radians = math.radians(angle)
    visual_size = math.ceil(DIE_SIZE * (abs(math.cos(radians)) + abs(math.sin(radians))) - 0.0001)
    if visual_size % 2:
        visual_size += 1
    if visual_size == DIE_SIZE and angle not in (0, 90):
        visual_size += 2
    hitbox = pygame.Rect(0, 0, visual_size, visual_size)
    hitbox.center = (round(die["x"] + DIE_SIZE / 2), round(die["y"] + DIE_SIZE / 2))
    return hitbox


def sync_die_rect(die):
    die["rect"].topleft = (round(die["x"]), round(die["y"]))
    die["hitbox"] = get_rotated_hitbox(die)


def die_overlaps_existing(candidate_rect, dice):
    padded_rect = candidate_rect.inflate(PLACEMENT_GAP, PLACEMENT_GAP)
    return any(padded_rect.colliderect(die["hitbox"]) for die in dice)


def place_die_randomly(die, dice, floor_rect):
    min_x = floor_rect.left
    max_x = floor_rect.right - DIE_SIZE
    min_y = floor_rect.top
    max_y = floor_rect.bottom - DIE_SIZE

    for _ in range(PLACEMENT_ATTEMPTS):
        candidate_rect = pygame.Rect(
            random.randint(min_x, max_x),
            random.randint(min_y, max_y),
            DIE_SIZE,
            DIE_SIZE,
        )
        if not die_overlaps_existing(candidate_rect, dice):
            die["x"] = float(candidate_rect.x)
            die["y"] = float(candidate_rect.y)
            sync_die_rect(die)
            return

    step = DIE_SIZE + PLACEMENT_GAP
    for y in range(min_y, max_y + 1, step):
        for x in range(min_x, max_x + 1, step):
            candidate_rect = pygame.Rect(x, y, DIE_SIZE, DIE_SIZE)
            if not die_overlaps_existing(candidate_rect, dice):
                die["x"] = float(x)
                die["y"] = float(y)
                sync_die_rect(die)
                return

    die["x"] = float(min_x)
    die["y"] = float(min_y)
    sync_die_rect(die)


def arrange_dice(dice, floor_rect=None):
    if not dice:
        return

    if floor_rect:
        spacing = max(DIE_SIZE * 2, floor_rect.width // (len(dice) + 1))
        y_offsets = [0, 0, -DIE_SIZE, DIE_SIZE, -DIE_SIZE // 2, DIE_SIZE // 2]
        for index, die in enumerate(dice):
            die["x"] = floor_rect.left + spacing * (index + 1) - DIE_SIZE / 2
            die["y"] = floor_rect.centery - DIE_SIZE / 2 + y_offsets[index % len(y_offsets)]
            clamp_die_to_floor(die, floor_rect)
            sync_die_rect(die)
        return

    rows = math.ceil(len(dice) / GRID_COLUMNS)
    total_height = rows * DIE_SIZE + (rows - 1) * GRID_GAP
    top = HEIGHT - GRID_BOTTOM_MARGIN - total_height

    for index, die in enumerate(dice):
        column = index % GRID_COLUMNS
        row = index // GRID_COLUMNS
        die["x"] = GRID_LEFT_MARGIN + column * (DIE_SIZE + GRID_GAP)
        die["y"] = top + row * (DIE_SIZE + GRID_GAP)
        sync_die_rect(die)


def add_die(dice, floor_rect=None):
    if len(dice) >= MAX_DICE:
        return False

    die = create_die(next_color_variant(dice), selected=not dice)
    if floor_rect:
        place_die_randomly(die, dice, floor_rect)
        dice.append(die)
    else:
        dice.append(die)
        arrange_dice(dice)
    return True


def select_die(dice, selected_index):
    for index, die in enumerate(dice):
        die["selected"] = index == selected_index


def die_at_position(dice, position):
    for index, die in enumerate(dice):
        if die["hitbox"].collidepoint(position):
            return index
    return None


def start_die_roll(die):
    if die["roll_state"]["active"]:
        return False

    die["roll_state"] = start_roll()
    return die["roll_state"]


def throw_die(die, power, floor_rect, dice=None):
    if die["moving"]:
        return False

    speed = MIN_THROW_SPEED + (MAX_THROW_SPEED - MIN_THROW_SPEED) * max(0.0, min(power, 1.0))
    direction = pygame.Vector2(1 if die["hitbox"].centerx <= floor_rect.centerx else -1, random.uniform(-0.18, 0.18))

    targets = [other_die for other_die in dice or [] if other_die is not die]
    if targets:
        die_center = get_die_center(die)
        target = min(targets, key=lambda other_die: die_center.distance_to(get_die_center(other_die)))
        target_center = get_die_center(target)
        direction = target_center - die_center
        if direction.length_squared() > 0:
            direction += pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))

    if direction.length_squared() == 0:
        direction = pygame.Vector2(1, 0)
    direction = direction.normalize()

    die["vx"] = speed * direction.x
    die["vy"] = speed * direction.y
    die["spin_velocity"] = random.choice([-1, 1]) * speed * random.uniform(2.2, 3.2)
    die["moving"] = True
    die["value_timer_ms"] = 0
    die["roll_sequence"] = random.sample(range(ROWS), ROWS)
    die["roll_sequence_index"] = 1
    die["value"] = die["roll_sequence"][0]
    return True


def reset_dice_values(dice):
    for die in dice:
        die["value"] = 0
        die["roll_state"] = create_idle_roll_state(0)


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


def clamp_die_to_floor(die, floor_rect):
    sync_die_rect(die)
    dx = 0
    dy = 0

    if die["hitbox"].left < floor_rect.left:
        dx = floor_rect.left - die["hitbox"].left
    elif die["hitbox"].right > floor_rect.right:
        dx = floor_rect.right - die["hitbox"].right

    if die["hitbox"].top < floor_rect.top:
        dy = floor_rect.top - die["hitbox"].top
    elif die["hitbox"].bottom > floor_rect.bottom:
        dy = floor_rect.bottom - die["hitbox"].bottom

    if dx or dy:
        die["x"] += dx
        die["y"] += dy
        sync_die_rect(die)


def update_die_motion(die, dt_ms, floor_rect):
    if not die["moving"]:
        sync_die_rect(die)
        return

    dt_seconds = dt_ms / 1000.0
    frame_scale = dt_ms / 16.0

    die["x"] += die["vx"] * dt_seconds
    die["y"] += die["vy"] * dt_seconds
    die["angle"] = (die["angle"] + die["spin_velocity"] * dt_seconds) % 360
    sync_die_rect(die)

    if die["hitbox"].left < floor_rect.left:
        die["x"] += floor_rect.left - die["hitbox"].left
        die["vx"] = abs(die["vx"]) * WALL_BOUNCE
        sync_die_rect(die)
    elif die["hitbox"].right > floor_rect.right:
        die["x"] += floor_rect.right - die["hitbox"].right
        die["vx"] = -abs(die["vx"]) * WALL_BOUNCE
        sync_die_rect(die)

    if die["hitbox"].top < floor_rect.top:
        die["y"] += floor_rect.top - die["hitbox"].top
        die["vy"] = abs(die["vy"]) * WALL_BOUNCE
        sync_die_rect(die)
    elif die["hitbox"].bottom > floor_rect.bottom:
        die["y"] += floor_rect.bottom - die["hitbox"].bottom
        die["vy"] = -abs(die["vy"]) * WALL_BOUNCE
        sync_die_rect(die)

    damping = FRICTION ** frame_scale
    die["vx"] *= damping
    die["vy"] *= damping
    die["spin_velocity"] *= damping

    die["value_timer_ms"] += dt_ms
    while die["value_timer_ms"] >= VALUE_CHANGE_INTERVAL_MS:
        roll_sequence = die.get("roll_sequence") or list(range(ROWS))
        sequence_index = die.get("roll_sequence_index", 0) % len(roll_sequence)
        die["value"] = roll_sequence[sequence_index]
        die["roll_sequence_index"] = (sequence_index + 1) % len(roll_sequence)
        die["value_timer_ms"] -= VALUE_CHANGE_INTERVAL_MS

    if math.hypot(die["vx"], die["vy"]) < STOP_SPEED:
        die["vx"] = 0.0
        die["vy"] = 0.0
        die["spin_velocity"] = 0.0
        die["moving"] = False
        die["roll_state"] = create_idle_roll_state(die["value"])

    sync_die_rect(die)


def resolve_die_collision(first_die, second_die):
    first_hitbox = first_die["hitbox"]
    second_hitbox = second_die["hitbox"]
    if not first_hitbox.colliderect(second_hitbox):
        return

    first_center = get_die_center(first_die)
    second_center = get_die_center(second_die)
    overlap_x = min(first_hitbox.right, second_hitbox.right) - max(first_hitbox.left, second_hitbox.left)
    overlap_y = min(first_hitbox.bottom, second_hitbox.bottom) - max(first_hitbox.top, second_hitbox.top)

    if overlap_x <= overlap_y:
        normal = pygame.Vector2(1 if first_center.x <= second_center.x else -1, 0)
        overlap = overlap_x
    else:
        normal = pygame.Vector2(0, 1 if first_center.y <= second_center.y else -1)
        overlap = overlap_y

    first_die["x"] -= normal.x * overlap / 2
    first_die["y"] -= normal.y * overlap / 2
    second_die["x"] += normal.x * overlap / 2
    second_die["y"] += normal.y * overlap / 2

    first_velocity = pygame.Vector2(first_die["vx"], first_die["vy"])
    second_velocity = pygame.Vector2(second_die["vx"], second_die["vy"])
    relative_velocity = first_velocity - second_velocity
    velocity_along_normal = relative_velocity.dot(normal)

    if velocity_along_normal > 0:
        impulse = (1 + DIE_BOUNCE) * velocity_along_normal / 2
        impulse_vector = impulse * normal
        first_velocity -= impulse_vector
        second_velocity += impulse_vector

        first_die["vx"], first_die["vy"] = first_velocity.x, first_velocity.y
        second_die["vx"], second_die["vy"] = second_velocity.x, second_velocity.y
        spin = min(2200, abs(impulse) * COLLISION_SPIN_FACTOR)
        first_die["spin_velocity"] -= spin * random.choice([-1, 1])
        second_die["spin_velocity"] += spin * random.choice([-1, 1])

    if math.hypot(first_die["vx"], first_die["vy"]) >= STOP_SPEED:
        first_die["moving"] = True
    if math.hypot(second_die["vx"], second_die["vy"]) >= STOP_SPEED:
        second_die["moving"] = True


def update_dice_physics(dice, dt_ms, floor_rect):
    for die in dice:
        update_die_motion(die, dt_ms, floor_rect)

    for first_index in range(len(dice)):
        for second_index in range(first_index + 1, len(dice)):
            resolve_die_collision(dice[first_index], dice[second_index])
            clamp_die_to_floor(dice[first_index], floor_rect)
            clamp_die_to_floor(dice[second_index], floor_rect)
            sync_die_rect(dice[first_index])
            sync_die_rect(dice[second_index])

    for die in dice:
        clamp_die_to_floor(die, floor_rect)


def any_die_moving(dice):
    return any(die["moving"] for die in dice)


def draw_dice(screen, faces, dice):
    for die in dice:
        roll_state = die["roll_state"]
        if roll_state["active"]:
            face_value = get_roll_face(roll_state)
        else:
            face_value = die["value"]
        color_variant = die["color_variant"]

        die_face = scale_face(get_face(faces, face_value, color_variant), DIE_SIZE)
        rotated_face = pygame.transform.rotozoom(die_face, die["angle"], 1.0)
        rotated_rect = rotated_face.get_rect(center=die["rect"].center)
        screen.blit(rotated_face, rotated_rect)


def draw_dice_summary(screen, faces, dice, font, floor_rect):
    x = floor_rect.left + 18
    y = floor_rect.bottom + 12

    for index, die in enumerate(dice):
        face = scale_face(get_face(faces, die["value"], die["color_variant"]), SUMMARY_DIE_SIZE)
        die_x = x + index * (SUMMARY_DIE_SIZE + SUMMARY_GAP)

        if die["selected"]:
            selected_rect = pygame.Rect(die_x - 5, y - 5, SUMMARY_DIE_SIZE + 10, SUMMARY_DIE_SIZE + 10)
            pygame.draw.rect(screen, SUMMARY_SELECTED_COLOR, selected_rect, 3, border_radius=8)

        screen.blit(face, (die_x, y))

        value_surface = font.render(str(die["value"]), True, LABEL_COLOR)
        value_pos = (
            die_x + (SUMMARY_DIE_SIZE - value_surface.get_width()) // 2,
            y + SUMMARY_DIE_SIZE + 2,
        )
        screen.blit(value_surface, value_pos)
