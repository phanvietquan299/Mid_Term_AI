from __future__ import annotations

from typing import Callable, Optional, Tuple

import pygame

from .ui_style import ACTION_DELTAS, ACTION_TO_DIRECTION, PALETTE, TIMING


class InteractionController:
    """Translate mouse/keyboard events into session actions."""

    def __init__(self, session, ticker, controls, app_callbacks):
        self.session = session
        self.ticker = ticker
        self.controls = controls
        self.callbacks = app_callbacks
        self.pacman_direction = "right"

    def on_click(self, pos: Tuple[int, int]):
        if self.session.is_busy():
            self.ticker.show("Đang tính toán...", PALETTE["warning"], 30)
            return

        action = self.controls.find_action(pos)
        if not action:
            return

        dispatch = {
            "solve": self.callbacks.solve,
            "toggle_auto": self._toggle_auto,
            "step": self._step,
            "reset": self._reset,
            "manual": self._toggle_manual,
            "cycle_heuristic": self.callbacks.cycle_heuristic,
        }
        handler = dispatch.get(action)
        if handler:
            handler()

    # ---------------------------------------------------------------- keyboard
    def on_key(self, key: int) -> bool:
        if key == pygame.K_ESCAPE and not self.session.manual_mode:
            return False  # Let application handle escape to quit.

        if key == pygame.K_t and self.session.manual_mode:
            self._teleport()
            return True

        if not self.session.manual_mode:
            return False

        if key == pygame.K_ESCAPE:
            self._toggle_manual()
            return True

        mapping = {
            pygame.K_UP: "Up",
            pygame.K_w: "Up",
            pygame.K_DOWN: "Down",
            pygame.K_s: "Down",
            pygame.K_LEFT: "Left",
            pygame.K_a: "Left",
            pygame.K_RIGHT: "Right",
            pygame.K_d: "Right",
            pygame.K_SPACE: "Stop",
        }
        action = mapping.get(key)
        if not action:
            return False

        self.pacman_direction = ACTION_TO_DIRECTION.get(action, self.pacman_direction)

        if self.session.at_goal():
            self.ticker.show("Bạn đã tới đích!", PALETTE["success"], 80)
            return True

        moved = self.session.try_manual_step(action)
        if moved:
            return True

        self._notify_invalid_move(action)
        return True

    def _toggle_auto(self):
        if not self.session.has_solution():
            self.ticker.show("Hãy giải bài trước khi Auto!", PALETTE["warning"], 60)
            return
        enabled = self.session.toggle_auto()
        self.ticker.show(
            "Auto chạy" if enabled else "Auto dừng",
            PALETTE["accent"] if enabled else PALETTE["warning"],
            50,
        )

    def _step(self):
        if not self.session.has_solution():
            self.ticker.show("Chưa có lời giải!", PALETTE["warning"], 60)
            return
        if self.session.at_goal():
            self.ticker.show("Đã tới đích rồi.", PALETTE["success"], 60)
            return
        if not self.session.step_once():
            self.ticker.show("Không thực hiện được bước tiếp theo.", PALETTE["error"], 60)

    def _reset(self):
        self.session.reset()
        self.pacman_direction = "right"
        self.ticker.show("Đã reset trạng thái.", PALETTE["text"], 40)

    def _toggle_manual(self):
        state = self.session.toggle_manual()
        self.ticker.show(
            "Manual ON: dùng phím mũi tên"
            if state
            else "Manual OFF: quay về AI",
            PALETTE["accent"] if state else PALETTE["text"],
            70,
        )

    def _teleport(self):
        result = self.session.teleport_manual()
        if result is None:
            self.ticker.show("Không đứng ở ô teleport.", PALETTE["warning"], 60)
        elif result is False:
            self.ticker.show("Điểm teleport bị ma chắn.", PALETTE["error"], 60)
        else:
            self.ticker.show(f"Dịch chuyển tới {result}", PALETTE["portal"], 80)
            if self.session.at_goal():
                self.ticker.show("Chiến thắng!", PALETTE["success"], 160)

    def _notify_invalid_move(self, action: str):
        layout = self.session.current_layout()
        state = self.session.current_state
        delta = ACTION_DELTAS[action]
        target = (state.pacman_pos[0] + delta[0], state.pacman_pos[1] + delta[1])

        if not layout.in_bounds(target):
            msg = "Vượt ngoài bản đồ!"
        elif layout.is_wall(target) and state.pie_timer <= 0:
            msg = "Đang đâm vào tường."
        elif any(g.position == target for g in state.ghosts):
            msg = "Ma đang chắn đường."
        else:
            msg = "Không thể di chuyển theo hướng đó."
        self.ticker.show(msg, PALETTE["error"], 60)
