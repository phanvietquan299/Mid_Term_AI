from __future__ import annotations

import threading
from queue import Queue
from typing import Any, Dict, List, Optional, Tuple

from .ui_style import ACTION_DELTAS, TIMING


class SessionState:
    def __init__(self, environment, problem, initial_state):
        self.env = environment
        self.problem = problem
        self.initial_state = initial_state
        self.current_state = initial_state

        self._path: List[Any] = []
        self._path_index = 0
        self._auto_enabled = False
        self._manual_enabled = False
        self._auto_tick = 0
        self._manual_tick = 0

        self._solving_thread: Optional[threading.Thread] = None
        self._solutions = Queue()
        self._computing = False

        self.rotation_flash = 0
        self.pie_flash = 0
        self._last_layout = initial_state.layout_index
        self._last_pie_timer = initial_state.pie_timer
        self.game_over_timer = 0

        self.stats = {
            "cost": 0,
            "expanded": 0,
            "frontier": 0,
            "current_step": 0,
        }

    # flags
    @property
    def manual_mode(self) -> bool:
        return self._manual_enabled

    def is_busy(self) -> bool:
        return self._computing

    def has_solution(self) -> bool:
        return bool(self._path)

    def at_goal(self) -> bool:
        return self.problem.is_goal(self.current_state)

    def auto_running(self) -> bool:
        return self._auto_enabled

    def path_length(self) -> int:
        return len(self._path)

    def is_game_over(self) -> bool:
        return self.game_over_timer > 0

    def current_layout(self):
        return self.env.layouts[self.current_state.layout_index]

    def reset(self):
        self.current_state = self.initial_state
        self._path = []
        self._path_index = 0
        self._auto_enabled = False
        self._manual_enabled = False
        self._auto_tick = 0
        self._manual_tick = 0
        self.rotation_flash = 0
        self.pie_flash = 0
        self._last_layout = self.initial_state.layout_index
        self._last_pie_timer = self.initial_state.pie_timer
        self.game_over_timer = 0
        while not self._solutions.empty():
            self._solutions.get()
        self.stats = {
            "cost": 0,
            "expanded": 0,
            "frontier": 0,
            "current_step": 0,
        }

    def request_solution(self, heuristic_name: str, solver_factory):
        if self._computing or self._manual_enabled:
            return False

        while not self._solutions.empty():
            self._solutions.get()

        def run_solver():
            try:
                path, cost, expanded, frontier = solver_factory(heuristic_name)
                self._solutions.put(
                    {
                        "ok": True,
                        "path": path or [],
                        "cost": cost,
                        "expanded": expanded,
                        "frontier": frontier,
                    }
                )
            except Exception as exc:
                self._solutions.put({"ok": False, "error": str(exc)})

        self._computing = True
        self._solving_thread = threading.Thread(target=run_solver, daemon=True)
        self._solving_thread.start()
        return True

    def poll_solution(self):
        if self._solutions.empty():
            return False

        result = self._solutions.get()
        self._computing = False

        if result.get("ok"):
            self._path = result["path"]
            self.stats["cost"] = result["cost"]
            self.stats["expanded"] = result["expanded"]
            self.stats["frontier"] = result["frontier"]
            self.stats["current_step"] = 0
            self._path_index = 0
            return True

        self._path = []
        self.stats = {
            "cost": 0,
            "expanded": 0,
            "frontier": 0,
            "current_step": 0,
        }
        return False

    # auto play
    def toggle_auto(self) -> bool:
        if not self.has_solution() or self._manual_enabled or self.at_goal():
            return False

        self._auto_enabled = not self._auto_enabled
        self._auto_tick = 0
        return self._auto_enabled

    def step_once(self) -> bool:
        if not self.has_solution() or self._manual_enabled or self.at_goal():
            return False
        if self._path_index >= len(self._path):
            return False

        return self._apply_action(self._path[self._path_index])

    def update_auto(self):
        if not self._auto_enabled or self._manual_enabled:
            return
        if self._path_index >= len(self._path) or self.at_goal():
            self._auto_enabled = False
            return
        self._auto_tick += 1
        if self._auto_tick >= TIMING.auto_delay:
            self._auto_tick = 0
            if not self._apply_action(self._path[self._path_index]):
                self._auto_enabled = False

    # manual play
    def toggle_manual(self) -> bool:
        self._manual_enabled = not self._manual_enabled
        if self._manual_enabled:
            self._auto_enabled = False
            self._manual_tick = 0
        return self._manual_enabled

    def try_manual_step(self, action_name: str) -> bool:
        if not self._manual_enabled:
            return False
        outcome = self.problem._apply_move(
            self.current_state,
            self.current_layout(),
            action_name,
            ACTION_DELTAS[action_name],
        )
        if not outcome:
            return False
        self.current_state, _, _ = outcome[0]
        return True

    def teleport_manual(self) -> Optional[str]:
        if not self._manual_enabled:
            return None

        layout = self.current_layout()
        corner = layout.corner_name(self.current_state.pacman_pos)
        if not corner:
            return None

        destinations = [
            (name, pos) for name, pos in layout.teleports.items() if pos != self.current_state.pacman_pos
        ]
        if not destinations:
            return False

        # rotate order TL -> TR -> BR -> BL for predictable behaviour
        order = ["TL", "TR", "BR", "BL"]
        target_name = None
        target_pos = None
        for candidate in order:
            if candidate in layout.teleports and layout.teleports[candidate] != self.current_state.pacman_pos:
                target_name = candidate
                target_pos = layout.teleports[candidate]
                break
        if target_name is None:
            target_name, target_pos = destinations[0]

        if any(g.position == target_pos for g in self.current_state.ghosts):
            return False

        new_state = self.problem._apply_teleport(
            self.current_state,
            layout,
            target_pos,
        )
        if new_state:
            self.current_state = new_state
            return target_name
        return False

    def advance_effects(self):
        if self.current_state.layout_index != self._last_layout:
            self.rotation_flash = TIMING.rotation_flash
            self._last_layout = self.current_state.layout_index
        elif self.rotation_flash > 0:
            self.rotation_flash -= 1

        if self.current_state.pie_timer > self._last_pie_timer:
            self.pie_flash = TIMING.pie_flash
        self._last_pie_timer = self.current_state.pie_timer
        if self.pie_flash > 0:
            self.pie_flash -= 1

        if self.game_over_timer > 0:
            self.game_over_timer -= 1
            if self.game_over_timer == 0:
                self.reset()

    def _apply_action(self, action):
        layout = self.current_layout()
        success = False
        if action.type in ACTION_DELTAS:
            result = self.problem._apply_move(
                self.current_state,
                layout,
                action.type,
                ACTION_DELTAS[action.type],
            )
            if result:
                self.current_state, _, _ = result[0]
                success = True
        elif action.type == "Teleport" and action.payload:
            target = action.payload.get("to")
            result = self.problem._apply_teleport(
                self.current_state,
                layout,
                target,
            )
            if result:
                self.current_state = result
                success = True

        if success:
            self._path_index += 1
            self.stats["current_step"] = self._path_index
        else:
            self._auto_enabled = False
        return success
