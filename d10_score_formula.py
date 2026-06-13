from collections import defaultdict

import pygame

from d10_score import calculate_score, score_breakdown
from d10_sprites import get_face, scale_face
from settings import WIDTH


ICON_SIZE = 28
Y = 145

_COMBO_COLORS = {
    "straight": (255, 215, 70),
    "pair":     (100, 210, 255),
    "triple":   (200, 130, 255),
    "quad":     (255, 145, 110),
    "quint":    (130, 255, 175),
    "single":   (185, 185, 200),
}

_WHITE = (255, 255, 255)
_PANEL_BG = (12, 12, 18, 170)
_PLUS_COLOR = (120, 120, 145)


def draw_score_formula(screen, faces, font, dice):
    if not dice:
        return

    groups = score_breakdown([die["value"] for die in dice])
    if not groups:
        return

    color_queue = defaultdict(list)
    for die in dice:
        color_queue[die["value"]].append(die["color_variant"])

    ICON = ICON_SIZE
    GAP = 3
    SEP = 11

    plus_surf = font.render("+", True, _PLUS_COLOR)
    eq_total_surf = font.render(f"= {calculate_score([die['value'] for die in dice])}", True, _WHITE)

    group_renders = []
    for group in groups:
        n = len(group["values"])
        icons_w = n * ICON + (n - 1) * GAP
        color = _COMBO_COLORS.get(group["combo"], (185, 185, 200))

        combo = group["combo"]
        if combo == "straight":
            badge = f"straight ×10 = {group['contribution']}"
        elif combo == "single":
            badge = f"= {group['contribution']}"
        else:
            badge = f"{combo} ×{n}² = {group['contribution']}"

        badge_surf = font.render(badge, True, color)
        group_w = icons_w + 5 + badge_surf.get_width()
        group_renders.append({"group": group, "icons_w": icons_w, "badge_surf": badge_surf, "group_w": group_w})

    plus_w = plus_surf.get_width()
    formula_w = sum(r["group_w"] for r in group_renders)
    formula_w += (len(group_renders) - 1) * (plus_w + SEP * 2)
    formula_w += SEP + eq_total_surf.get_width()

    label_h = font.get_height()
    strip_h = ICON + label_h + 4

    x = max(8, (WIDTH - formula_w) // 2)
    y = Y
    PAD_X, PAD_Y = 10, 5

    panel = pygame.Surface((formula_w + PAD_X * 2, strip_h + PAD_Y * 2), pygame.SRCALPHA)
    panel.fill(_PANEL_BG)
    screen.blit(panel, (x - PAD_X, y - PAD_Y))

    label_dy = (ICON - label_h) // 2

    for g_idx, rg in enumerate(group_renders):
        die_x = x
        for value in rg["group"]["values"]:
            cv = color_queue[value].pop(0) if color_queue[value] else 0
            screen.blit(scale_face(get_face(faces, value, cv), ICON), (die_x, y))
            die_x += ICON + GAP

        screen.blit(rg["badge_surf"], (x + rg["icons_w"] + 5, y + label_dy))
        x += rg["group_w"]

        if g_idx < len(group_renders) - 1:
            x += SEP
            screen.blit(plus_surf, (x, y + label_dy))
            x += plus_w + SEP

    screen.blit(eq_total_surf, (x + SEP, y + label_dy))
