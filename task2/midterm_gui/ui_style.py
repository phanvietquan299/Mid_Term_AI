from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


Color = Tuple[int, int, int]


@dataclass(frozen=True)
class ScreenPlan:
    max_width: int = 1920
    max_height: int = 1080
    footer_height: int = 180
    board_padding: int = 12


@dataclass(frozen=True)
class Timing:
    manual_delay: int = 8
    auto_delay: int = 6
    fps: int = 45
    message_ticks: int = 90
    rotation_flash: int = 28
    pie_flash: int = 16
    game_over_ticks: int = 180


PALETTE: Dict[str, Color] = {
    "background": (12, 30, 15),
    "grid": (28, 28, 28),
    "wall": (30, 85, 190),
    "wall_flash": (55, 120, 240),
    "text": (245, 245, 245),
    "accent": (255, 193, 7),
    "error": (220, 20, 60),
    "success": (80, 200, 120),
    "warning": (255, 165, 0),
    "portal": (0, 210, 210),
    "ghost": (220, 40, 80),
    "ghost_scared": (70, 130, 180),
}

SCREEN = ScreenPlan()
TIMING = Timing()

HEURISTIC_CHOICES = [
    ("Auto pick", "auto"),
    ("ExactMST (H1)", "exact-mst"),
    ("Combined", "combo"),
    ("Exact distance", "exact-dist"),
    ("Food MST", "mst"),
    ("Pie aware", "pie"),
]

ACTION_DELTAS = {
    "Up": (-1, 0),
    "Down": (1, 0),
    "Left": (0, -1),
    "Right": (0, 1),
    "Stop": (0, 0),
}

ACTION_TO_DIRECTION = {
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right",
}
