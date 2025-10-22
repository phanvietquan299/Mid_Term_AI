from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pygame

from .ui_style import HEURISTIC_CHOICES, PALETTE, SCREEN, TIMING


@dataclass
class ControlButton:
    label: str
    action: str
    rect: pygame.Rect
    highlighted: bool = False


class ControlPanel:
    """Horizontal strip of buttons + heuristic selector."""

    def __init__(self, screen_width: int, board_left: int, board_width: int, anchor_y: int):
        self.screen_width = screen_width
        self.board_left = board_left
        self.board_width = board_width
        self.anchor_y = anchor_y
        self.button_height = 28
        self.spacing = 8
        self.buttons: List[ControlButton] = []
        self._heuristic_button: Optional[ControlButton] = None
        self._create_buttons()
        self._layout_buttons(board_left, board_width, anchor_y)

    def _create_buttons(self) -> None:
        texts = [
            ("Solve", "solve"),
            ("Auto", "toggle_auto"),
            ("Step", "step"),
            ("Reset", "reset"),
            ("Manual", "manual"),
        ]

        for label, action in texts:
            rect = pygame.Rect(0, 0, self.button_height, self.button_height)
            self.buttons.append(ControlButton(label, action, rect))

        heuristic_rect = pygame.Rect(0, 0, self.button_height * 2, self.button_height)
        self._heuristic_button = ControlButton(self._heuristic_label(0), "cycle_heuristic", heuristic_rect)
        self.buttons.append(self._heuristic_button)
        
    def check_hover(self, pos: Tuple[int, int]) -> None:
    # Reset hover state
        for btn in self.buttons:
            btn.is_hovered = False
        if self._heuristic_button:
            self._heuristic_button.is_hovered = False
            
        # Check collision
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                btn.is_hovered = True
                return
                
        if self._heuristic_button and self._heuristic_button.rect.collidepoint(pos):
            self._heuristic_button.is_hovered = True

    def _layout_buttons(self, board_left: int, board_width: int, anchor_y: int) -> None:
        top_buttons = self.buttons[:-1]
        count = len(top_buttons)
        available_width = self.screen_width - SCREEN.board_padding * 2
        panel_width = min(available_width, max(board_width, 560))
        panel_left = max(SCREEN.board_padding, (self.screen_width - panel_width) // 2) - int(self.screen_width * 0.1)
        
        spacing_dynamic = max(self.spacing, int(panel_width * 0.01))
        spacing_total = spacing_dynamic * (count - 1)
        width = max(88, (panel_width - spacing_total) // count)

        panel_right = self.screen_width - SCREEN.board_padding
        
        x = panel_left
        
        for idx, btn in enumerate(top_buttons):
            btn.rect = pygame.Rect(int(x), anchor_y, int(width), self.button_height)
            x = btn.rect.right + (spacing_dynamic if idx < count - 1 else 0)

        if self._heuristic_button:
            heur_left = x + (self.spacing if count else 0)
            min_width = max(width, 140)
            heur_right_limit = panel_right
            if heur_left + min_width > heur_right_limit:
                heur_left = max(panel_left, heur_right_limit - min_width)
            heur_width = min(max(int(width * 1.6), min_width), heur_right_limit - heur_left)
            self._heuristic_button.rect = pygame.Rect(int(heur_left), anchor_y, int(heur_width), self.button_height)

        self.panel_left = panel_left
        self.panel_width = panel_width
        self.board_left = board_left
        self.board_width = board_width
        self.anchor_y = anchor_y

    def update_layout(self, board_left: int, board_width: int, anchor_y: int) -> None:
        self._layout_buttons(board_left, board_width, anchor_y)

    def _heuristic_label(self, idx: int) -> str:
        return f"H: {HEURISTIC_CHOICES[idx][0]}"

    # ----------------------------------------------------------------- drawing
    def render(self, screen: pygame.Surface, font: pygame.font.Font):
        for btn in self.buttons:
            self._draw_button(screen, font, btn)

    def _draw_button(self, screen: pygame.Surface, font: pygame.font.Font, btn: ControlButton):
        border = 2
        fill = PALETTE["accent"] if btn.highlighted or btn.is_hovered else PALETTE["text"]
        margin = 4
        
        margin_rect = btn.rect.inflate(border*4 + margin, border*4 + margin)
        margin_surface = pygame.Surface((margin_rect.width, margin_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(margin_surface, (0, 0, 0, 255), margin_surface.get_rect())  # Semi-transparent black
        screen.blit(margin_surface, margin_rect)
        
        border_rect = btn.rect.inflate(border*4, border*4) 
        pygame.draw.rect(screen, (251, 197, 49), border_rect)
        
        pygame.draw.rect(screen, fill, btn.rect)
        
        
        label = font.render(btn.label, True, PALETTE["background"])
        screen.blit(label, label.get_rect(center=btn.rect.center))

    # ------------------------------------------------------------------ events
    def find_action(self, pos: Tuple[int, int]) -> Optional[str]:
        for btn in self.buttons:
            if btn.rect.collidepoint(pos):
                return btn.action
        return None

    def show_active(self, *, auto: bool, manual: bool, solving: bool):
        for btn in self.buttons:
            btn.highlighted = False
        for btn in self.buttons:
            if btn.action == "toggle_auto" and auto:
                btn.highlighted = True
            elif btn.action == "manual" and manual:
                btn.highlighted = True
            elif btn.action == "solve" and solving:
                btn.highlighted = True

    def update_heuristic_hint(self, idx: int):
        if self._heuristic_button:
            self._heuristic_button.label = self._heuristic_label(idx)


class MessageTicker:
    def __init__(self):
        self._text: str = ""
        self._color = PALETTE["text"]
        self._timer = 0

    def show(self, msg: str, color: Tuple[int, int, int], duration: int = TIMING.message_ticks):
        self._text = msg
        self._color = color
        self._timer = duration

    def update(self):
        if self._timer > 0:
            self._timer -= 1

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, pos: Tuple[int, int]):
        if self._timer <= 0 or not self._text:
            return
        surface.blit(font.render(self._text, True, self._color), pos)


class InfoPanel:
    """Compact three-column status block."""

    def __init__(self, board_left: int, board_width: int, anchor_y: int, font: pygame.font.Font):
        self.left_x = board_left
        self.panel_width = board_width
        self.anchor_y = anchor_y
        self.font = font

    def update_layout(self, board_left: int, board_width: int, anchor_y: int) -> None:
        self.left_x = board_left
        self.panel_width = max(board_width, 1)
        self.anchor_y = anchor_y

    def draw(
        self,
        surface: pygame.Surface,
        stats: Dict[str, Any],
        state: Any,
        environment: Any,
        *,
        auto_on: bool,
        manual_on: bool,
        path_length: int,
        game_over: bool,
    ):
        section_gap = max(self.panel_width // 3, 140)
        col_x = [
            self.left_x,
            self.left_x + section_gap,
            self.left_x + section_gap * 2,
        ]

        status_lines = self._status_lines(stats, path_length, auto_on, manual_on, game_over, environment, state)
        for col, lines in enumerate(status_lines):
            y = self.anchor_y
            for text, color in lines:
                surface.blit(self.font.render(text, True, color), (col_x[col], y))
                y += 22

    def _status_lines(
        self,
        stats: Dict[str, Any],
        path_length: int,
        auto_on: bool,
        manual_on: bool,
        game_over: bool,
        environment: Any,
        state: Any,
    ) -> List[List[Tuple[str, Tuple[int, int, int]]]]:
        goal = environment.problem.is_goal(state)
        current_layout = environment.layouts[state.layout_index]
        next_rotate = environment.ROTATION_PERIOD - (state.time_step % environment.ROTATION_PERIOD or environment.ROTATION_PERIOD)

        col1 = []
        if game_over:
            col1.append(("GAME OVER", PALETTE["error"]))
        elif goal:
            col1.append(("Goal reached", PALETTE["success"]))
        mode_color = PALETTE["accent"] if manual_on else PALETTE["text"]
        col1.append((f"Mode: {'Manual' if manual_on else 'AI'}", mode_color))
        col1.append((f"Cost: {stats['cost']}", PALETTE["text"]))
        col1.append((f"Expanded: {stats['expanded']}", PALETTE["text"]))
        col1.append((f"Step: {stats['current_step']}/{path_length}", PALETTE["text"]))

        pie_color = PALETTE["warning"] if state.pie_timer <= 2 and state.pie_timer > 0 else PALETTE["text"]
        col2 = [
            (f"Food left: {len(state.food)}", PALETTE["text"]),
            (f"Power timer: {state.pie_timer}", pie_color),
            (f"Time: {state.time_step}", PALETTE["accent"] if auto_on else PALETTE["text"]),
        ]

        rotation_color = PALETTE["warning"] if next_rotate <= 5 else PALETTE["text"]
        col3 = [
            (f"Maze: {current_layout.height}x{current_layout.width}", PALETTE["text"]),
            (f"Next rotate: {next_rotate}", rotation_color),
        ]

        return [col1, col2, col3]
