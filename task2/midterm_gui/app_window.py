from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple

import pygame

sys.path.append(str(Path(__file__).resolve().parent.parent))
from pacman.environment import PacmanEnvironment, PacmanProblem, PacmanLayout
from pacman.auto import run_auto_mode

from .ui_style import HEURISTIC_CHOICES, PALETTE, SCREEN, TIMING
from .session_manager import SessionState
from .asset_manager import ImageManager
from .interaction_handler import InteractionController
from .ui_elements import ControlPanel, InfoPanel, MessageTicker



@dataclass
class ControlCallbacks:
    solve: Callable[[], None]
    cycle_heuristic: Callable[[], None]



class PacmanGUI:
    def __init__(self, layout_path: Optional[Path] = None):
        pygame.init()
        pygame.mixer.quit() 

        self.layout_lines = self._load_layout(layout_path)
        self.environment = PacmanEnvironment(self.layout_lines)
        self.problem = PacmanProblem(self.environment)
        self.environment.problem = self.problem 
        self._min_cell_size = 6
        self._configure_screen_geometry()
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.SCALED,
        )
        pygame.display.set_caption("Pacman Mid-term - GUI & A*")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.Font(None, max(22, self.cell_size // 2 + 6))
        self.info_font = pygame.font.Font(None, max(18, self.cell_size // 2))

        self.sprites = ImageManager(self.cell_size)
        self.session = SessionState(
            self.environment,
            self.problem,
            self.environment.initial_state,
        )

        self._current_board_rect = pygame.Rect(
            self.board_left, self.board_top, self.board_width, self.board_height
        )

        panel_anchor = self.panel_top
        self.controls = ControlPanel(self.screen_width, self.board_left, self.board_width, panel_anchor)
        info_top = self._compute_info_anchor(panel_anchor)
        self.info_panel = InfoPanel(self.controls.panel_left, self.controls.panel_width, info_top, self.info_font)
        self.ticker = MessageTicker()

        callbacks = ControlCallbacks(self.solve_puzzle, self.cycle_heuristic)
        self.interaction = InteractionController(
            self.session,
            self.ticker,
            self.controls,
            callbacks,
        )

        self.heuristic_idx = 0
        print(
            f"[PacmanGUI] screen={self.screen_width}x{self.screen_height} "
            f"maze={self.board_width // self.cell_size}x{self.board_height // self.cell_size} "
            f"cell={self.cell_size}px"
        )

    # lifecycle
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.interaction.on_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    self.controls.check_hover(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if not self.interaction.on_key(event.key) and event.key == pygame.K_ESCAPE:
                        running = False

            if self.session.poll_solution():
                self.ticker.show("Path found!", PALETTE["success"], 120)

            self.session.update_auto()
            self.session.advance_effects()
            self.ticker.update()

            self._draw_frame()
            pygame.display.flip()
            self.clock.tick(TIMING.fps)

        pygame.quit()

    # callbacks
    def solve_puzzle(self):
        heuristic_key = HEURISTIC_CHOICES[self.heuristic_idx][1]
        label = HEURISTIC_CHOICES[self.heuristic_idx][0]

        def solver(selected: str):
            return run_auto_mode(self.layout_lines, heuristic=selected)

        if self.session.request_solution(heuristic_key, solver):
            self.ticker.show(f"Running A* ({label})", PALETTE["accent"], 120)
        else:
            self.ticker.show("Cannot solve right now.", PALETTE["warning"], 60)

    def cycle_heuristic(self):
        self.heuristic_idx = (self.heuristic_idx + 1) % len(HEURISTIC_CHOICES)
        self.controls.update_heuristic_hint(self.heuristic_idx)
        self.session.reset()
        self.ticker.show(f"Heuristic: {HEURISTIC_CHOICES[self.heuristic_idx][0]}", PALETTE["text"], 90)

    def _compute_info_anchor(self, base_anchor: int) -> int:
        panel_bottom = self.panel_bottom
        desired = base_anchor + self.controls.button_height + 20
        max_anchor = max(self.panel_top, panel_bottom - self.info_font.get_linesize() * 4)
        return max(self.panel_top, min(desired, max_anchor))

    # rendering
    def _draw_frame(self):
        self.screen.fill(PALETTE["background"])
        self._draw_board()

        anchor_y = self.panel_top
        self.controls.update_layout(self.board_left, self.board_width, anchor_y)
        self.controls.show_active(
            auto=self.session.auto_running(),
            manual=self.session.manual_mode,
            solving=self.session.is_busy(),
        )
        self.controls.render(self.screen, self.font)
        self.ticker.draw(self.screen, self.font, (int(self.screen_width * 0.01), int(self.screen_height * 0.01)))

        info_anchor = self._compute_info_anchor(anchor_y)
        self.info_panel.update_layout(self.controls.panel_left, self.controls.panel_width, info_anchor)
        self.info_panel.draw(
            self.screen,
            self.session.stats,
            self.session.current_state,
            self.environment,
            auto_on=self.session.auto_running(),
            manual_on=self.session.manual_mode,
            path_length=self.session.path_length(),
            game_over=self.session.is_game_over(),
        )

    def _draw_board(self):
        state = self.session.current_state
        layout = self.environment.layouts[state.layout_index]

        self._ensure_layout_scale(layout)

        grid_w = layout.width * self.cell_size
        grid_h = layout.height * self.cell_size
        board_left = max(SCREEN.board_padding, (self.screen_width - grid_w) // 2)
        board_area_top = self.board_area_top
        board_area_height = self.usable_board_height
        board_top = board_area_top + max(0, (board_area_height - grid_h) // 2)

        board_rect = pygame.Rect(board_left, board_top, grid_w, grid_h)
        pygame.draw.rect(self.screen, PALETTE["grid"], board_rect, border_radius=10)
        self._current_board_rect = board_rect
        self.board_left = board_left
        self.board_top = board_top
        self.board_width = grid_w
        self.board_height = grid_h

        offset_x = board_left
        offset_y = board_top

        if self.session.pie_flash > 0:
            flash = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
            intensity = int(110 * (self.session.pie_flash / TIMING.pie_flash))
            flash.fill((*PALETTE["accent"], intensity))
            self.screen.blit(flash, (board_left, board_top))

        wall_tile = self.sprites.tile_wall()
        food_tile = self.sprites.tile_food()
        exit_tile = self.sprites.tile_exit()
        pie_tile = self.sprites.tile_pie()

        for r in range(layout.height):
            for c in range(layout.width):
                cell_rect = pygame.Rect(
                    offset_x + c * self.cell_size,
                    offset_y + r * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                pos = (r, c)

                if layout.is_wall(pos):
                    base_color = (
                        PALETTE["wall_flash"]
                        if self.session.rotation_flash
                        else PALETTE["wall"]
                    )
                    pygame.draw.rect(self.screen, base_color, cell_rect)
                    if wall_tile:
                        self.screen.blit(
                            wall_tile,
                            wall_tile.get_rect(center=cell_rect.center),
                        )
                    pygame.draw.rect(self.screen, PALETTE["grid"], cell_rect, 1)
                    continue

                pygame.draw.rect(self.screen, PALETTE["background"], cell_rect)

                if pos == layout.exit_gate:
                    if exit_tile:
                        self.screen.blit(
                            exit_tile, exit_tile.get_rect(center=cell_rect.center)
                        )
                    else:
                        pygame.draw.rect(
                            self.screen,
                            PALETTE["success"],
                            cell_rect.inflate(-self.cell_size // 3, -self.cell_size // 3),
                            border_radius=6,
                        )

                if pos in state.food:
                    if food_tile:
                        self.screen.blit(
                            food_tile, food_tile.get_rect(center=cell_rect.center)
                        )
                    else:
                        pygame.draw.circle(
                            self.screen,
                            PALETTE["text"],
                            cell_rect.center,
                            max(4, self.cell_size // 6),
                        )

                if pos in state.pies:
                    sprite = pie_tile
                    if sprite:
                        self.screen.blit(
                            sprite, sprite.get_rect(center=cell_rect.center)
                        )
                    else:
                        pygame.draw.circle(
                            self.screen,
                            PALETTE["accent"],
                            cell_rect.center,
                            self.cell_size // 3,
                        )

                pygame.draw.rect(self.screen, PALETTE["grid"], cell_rect, 1)

        for _, teleport_pos in layout.teleports.items():
            cell_rect = pygame.Rect(
                offset_x + teleport_pos[1] * self.cell_size,
                offset_y + teleport_pos[0] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            self.sprites.draw_portal(self.screen, cell_rect, teleport_pos == state.pacman_pos)

        for idx, ghost in enumerate(state.ghosts):
            rect = pygame.Rect(
                offset_x + ghost.position[1] * self.cell_size,
                offset_y + ghost.position[0] * self.cell_size,
                self.cell_size,
                self.cell_size,
            )
            sprite = self.sprites.scared() if state.pie_timer else self.sprites.ghost(idx)
            if sprite:
                self.screen.blit(sprite, sprite.get_rect(center=rect.center))
            else:
                pygame.draw.circle(self.screen, PALETTE["ghost"], rect.center, self.cell_size // 3)

        pac_rect = pygame.Rect(
            offset_x + state.pacman_pos[1] * self.cell_size,
            offset_y + state.pacman_pos[0] * self.cell_size,
            self.cell_size,
            self.cell_size,
        )
        sprite = self.sprites.pacman(self.interaction.pacman_direction)
        pygame.draw.circle(
            self.screen,
            PALETTE["accent"],
            pac_rect.center,
            max(self.cell_size // 2, 6),
        )
        if sprite:
            self.screen.blit(sprite, sprite.get_rect(center=pac_rect.center))
        else:
            # Debug once
            if not hasattr(self, "_missing_pacman_logged"):
                print("[PacmanGUI] Pacman sprite missing, using fallback circle.")
                self._missing_pacman_logged = True
            pygame.draw.circle(self.screen, PALETTE["accent"], pac_rect.center, self.cell_size // 2)

    def _load_layout(self, layout_path: Optional[Path]) -> list[str]:
        if layout_path and layout_path.exists():
            with open(layout_path, "r", encoding="utf-8") as fh:
                return [line.rstrip("\n") for line in fh]
        return [
            "%%%%%%%%%%",
            "%P....  E%",
            "% %% %%% %",
            "%..G  O  %",
            "%%%%%%%%%%",
        ]

    def _configure_screen_geometry(self):
        display = pygame.display.Info()
        width_hint = display.current_w or SCREEN.max_width
        height_hint = display.current_h or SCREEN.max_height
        self.screen_width = int(min(width_hint, SCREEN.max_width) * 0.8)
        self.screen_height = int(min(height_hint, SCREEN.max_height) * 0.8)

        max_w = max(layout.width for layout in self.environment.layouts)
        max_h = max(layout.height for layout in self.environment.layouts)

        self._update_screen_metrics()
        self.cell_size = self._choose_cell_size(max_w, max_h)
        self.environment.cell_size = self.cell_size

        self.board_width = max_w * self.cell_size
        self.board_height = max_h * self.cell_size
        self.board_left = max(SCREEN.board_padding, (self.screen_width - self.board_width) // 2)
        self.board_top = self.board_area_top + max(0, (self.usable_board_height - self.board_height) // 2)

    def _update_screen_metrics(self) -> None:
        self.usable_board_width = max(1, self.screen_width - SCREEN.board_padding * 2)

        available_height = max(1, self.screen_height - SCREEN.board_padding * 3)
        board_height = max(1, int(available_height * SCREEN.board_height_ratio))
        panel_height = available_height - board_height

        if panel_height < SCREEN.panel_min_height and available_height > SCREEN.panel_min_height:
            panel_height = SCREEN.panel_min_height
            if panel_height >= available_height:
                panel_height = max(1, available_height - 1)
            board_height = max(1, available_height - panel_height)
        elif panel_height < 1:
            panel_height = 1
            board_height = max(1, available_height - panel_height)

        self.usable_board_height = max(1, board_height)
        self.panel_height = max(1, available_height - self.usable_board_height)
        if self.panel_height < SCREEN.panel_min_height and available_height >= SCREEN.panel_min_height + 1:
            self.panel_height = SCREEN.panel_min_height
            self.usable_board_height = max(1, available_height - self.panel_height)

        self.board_area_top = SCREEN.board_padding
        self.panel_top = self.board_area_top + self.usable_board_height + SCREEN.board_padding
        self.panel_bottom = self.panel_top + self.panel_height

    def _choose_cell_size(self, cells_w: int, cells_h: int) -> int:
        cells_w = max(1, cells_w)
        cells_h = max(1, cells_h)
        candidate_w = self.usable_board_width // cells_w
        candidate_h = self.usable_board_height // cells_h
        candidate = min(candidate_w, candidate_h)
        if candidate <= 0:
            candidate = 1
        return candidate

    def _ensure_layout_scale(self, layout: PacmanLayout) -> None:
        if hasattr(self, "screen"):
            current_w = self.screen.get_width()
            current_h = self.screen.get_height()
            if current_w != self.screen_width or current_h != self.screen_height:
                self.screen_width = current_w
                self.screen_height = current_h

        self._update_screen_metrics()

        target_cell = self._choose_cell_size(layout.width, layout.height)

        preferred = max(target_cell, self._min_cell_size)
        if (
            preferred != target_cell
            and layout.width * preferred <= self.usable_board_width
            and layout.height * preferred <= self.usable_board_height
        ):
            target_cell = preferred

        while target_cell > 1 and (
            layout.width * target_cell > self.usable_board_width
            or layout.height * target_cell > self.usable_board_height
        ):
            target_cell -= 1

        if target_cell <= 0:
            target_cell = 1

        if target_cell != self.cell_size:
            self._apply_cell_size(target_cell)

    def _apply_cell_size(self, new_size: int) -> None:
        new_size = max(1, new_size)
        if new_size == self.cell_size:
            return

        self.cell_size = new_size
        self.environment.cell_size = new_size

        if hasattr(self, "sprites"):
            self.sprites = ImageManager(self.cell_size)

        self.font = pygame.font.Font(None, max(22, self.cell_size // 2 + 6))
        self.info_font = pygame.font.Font(None, max(18, self.cell_size // 2))
        if hasattr(self, "info_panel"):
            self.info_panel.font = self.info_font

    def get_state_debug(self) -> dict:
        return {
            "heuristic": HEURISTIC_CHOICES[self.heuristic_idx][1],
            "auto": self.session.auto_running(),
            "manual": self.session.manual_mode,
            "path_len": self.session.path_length(),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", type=Path, help="Optional layout file path")
    args = parser.parse_args()

    gui = PacmanGUI(args.layout)
    gui.run()


if __name__ == "__main__":
    main()
