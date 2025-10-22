from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple

import pygame

sys.path.append(str(Path(__file__).resolve().parent.parent))
from pacman.environment import PacmanEnvironment, PacmanProblem
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
        pygame.mixer.quit()  # giảm độ trễ khởi động do audio

        self.layout_lines = self._load_layout(layout_path)
        self.environment = PacmanEnvironment(self.layout_lines)
        self.problem = PacmanProblem(self.environment)
        self.environment.problem = self.problem  # Info panel cần truy cập

        self._configure_screen_geometry()
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.SCALED,
        )
        pygame.display.set_caption("Pacman Mid-term – GUI & A* Demo")
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

        footer_top = self.screen_height - SCREEN.footer_height + SCREEN.board_padding
        self.controls = ControlPanel(self.screen_width, self.board_left, self.board_width, footer_top)
        info_top = footer_top + self.controls.button_height + 20
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

    # ---------------------------------------------------------------- lifecycle
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
                self.ticker.show("Đã tìm thấy đường đi!", PALETTE["success"], 120)

            self.session.update_auto()
            self.session.advance_effects()
            self.ticker.update()

            self._draw_frame()
            pygame.display.flip()
            self.clock.tick(TIMING.fps)

        pygame.quit()

    # ---------------------------------------------------------------- callbacks
    def solve_puzzle(self):
        heuristic_key = HEURISTIC_CHOICES[self.heuristic_idx][1]
        label = HEURISTIC_CHOICES[self.heuristic_idx][0]

        def solver(selected: str):
            return run_auto_mode(self.layout_lines, heuristic=selected)

        if self.session.request_solution(heuristic_key, solver):
            self.ticker.show(f"Đang chạy A* ({label})", PALETTE["accent"], 120)
        else:
            self.ticker.show("Không thể giải lúc này.", PALETTE["warning"], 60)

    def cycle_heuristic(self):
        self.heuristic_idx = (self.heuristic_idx + 1) % len(HEURISTIC_CHOICES)
        self.controls.update_heuristic_hint(self.heuristic_idx)
        self.session.reset()
        self.ticker.show(f"Heuristic: {HEURISTIC_CHOICES[self.heuristic_idx][0]}", PALETTE["text"], 90)

    # ---------------------------------------------------------------- rendering
    def _draw_frame(self):
        self.screen.fill(PALETTE["background"])
        self._draw_board()

        anchor_y = self.screen_height - SCREEN.footer_height + SCREEN.board_padding
        self.controls.update_layout(self.board_left, self.board_width, anchor_y)
        self.controls.show_active(
            auto=self.session.auto_running(),
            manual=self.session.manual_mode,
            solving=self.session.is_busy(),
        )
        self.controls.render(self.screen, self.font)
        self.ticker.draw(self.screen, self.font, (int(self.screen_width * 0.01), int(self.screen_height * 0.01)))

        info_anchor = anchor_y + self.controls.button_height + 20
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

        grid_w = layout.width * self.cell_size
        grid_h = layout.height * self.cell_size
        board_left = max(SCREEN.board_padding, (self.screen_width - grid_w) // 2)
        board_top = SCREEN.board_padding

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

    # ---------------------------------------------------------------- utilities
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
        self.screen_width = min(display.current_w or SCREEN.max_width, SCREEN.max_width) * 0.8
        self.screen_height = min(display.current_h or SCREEN.max_height, SCREEN.max_height) * 0.8

        self.screen_width = int(self.screen_width)
        self.screen_height = int(self.screen_height)

        max_w = max(layout.width for layout in self.environment.layouts)
        max_h = max(layout.height for layout in self.environment.layouts)

        usable_w = self.screen_width - SCREEN.board_padding * 2
        usable_h = self.screen_height - SCREEN.footer_height - SCREEN.board_padding * 2

        cell_from_w = max(10, usable_w // max_w)
        cell_from_h = max(10, usable_h // max_h)
        self.cell_size = max(20, min(cell_from_w, cell_from_h))
        self.environment.cell_size = self.cell_size

        self.board_width = max_w * self.cell_size
        self.board_height = max_h * self.cell_size
        self.board_left = max(SCREEN.board_padding, (self.screen_width - self.board_width) // 2)
        self.board_top = SCREEN.board_padding

    # --------------------------------------------------------------- diagnostics
    def get_state_debug(self) -> dict:
        return {
            "heuristic": HEURISTIC_CHOICES[self.heuristic_idx][1],
            "auto": self.session.auto_running(),
            "manual": self.session.manual_mode,
            "path_len": self.session.path_length(),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", type=Path, help="Đường dẫn file layout tùy chọn")
    args = parser.parse_args()

    gui = PacmanGUI(args.layout)
    gui.run()


if __name__ == "__main__":
    main()
