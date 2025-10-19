import pygame
import sys
import os
from pathlib import Path
from typing import Optional
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from pacman.environment import PacmanEnvironment, PacmanProblem
from pacman.auto import run_auto_mode

from .constants import *
from .image_manager import ImageManager
from .ui_components import ButtonManager, MessageManager, InfoPanel
from .game_state import GameStateManager
from .input_handler import InputHandler


class PacmanGUI:    
    def __init__(self, layout_path: Optional[Path] = None):
        pygame.init()
        
        if layout_path and layout_path.exists():
            with open(layout_path, 'r', encoding='utf-8') as f:
                self.layout_lines = [line.rstrip('\n') for line in f]
        else:
            self.layout_lines = [
                "%%%%%%%%%%",
                "%P....  E%",
                "% %% %%% %",
                "%..G  O  %",
                "%%%%%%%%%%"
            ]
        
        self.env = PacmanEnvironment(self.layout_lines)
        self.problem = PacmanProblem(self.env)
        self.current_state = self.env.initial_state
        
        self.max_width = max(layout.width for layout in self.env.layouts)
        self.max_height = max(layout.height for layout in self.env.layouts)
        
        self.cell_size = self._calculate_optimal_cell_size()
        
        self.screen_width = self.max_width * self.cell_size
        self.screen_height = self.max_height * self.cell_size + INFO_HEIGHT
        
        if self.screen_width > MAX_SCREEN_WIDTH:
            self.screen_width = MAX_SCREEN_WIDTH
        if self.screen_height > MAX_SCREEN_HEIGHT:
            self.screen_height = MAX_SCREEN_HEIGHT
        
        self.screen_width = max(800, self.screen_width)
        self.screen_height = max(600, self.screen_height)
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Pacman AI Solver - Manual & Auto Mode")
        
        self.clock = pygame.time.Clock()
        
        font_size = max(20, min(28, self.cell_size // 2 + 4))
        small_font_size = max(16, min(22, self.cell_size // 2))
        self.font = pygame.font.Font(None, font_size)
        self.small_font = pygame.font.Font(None, small_font_size)
        self.image_manager = ImageManager(self.cell_size)
        self.message_manager = MessageManager()
        self.button_manager = ButtonManager(self.screen_width, self.screen_height, 
                                          self.max_height * self.cell_size, HEURISTICS)
        self.info_panel = InfoPanel(self.screen_width, self.screen_height, 
                                   self.max_height * self.cell_size, self.small_font)
        self.game_state = GameStateManager(self.env, self.problem, self.env.initial_state)
        self.input_handler = InputHandler(self.game_state, self.message_manager, self.button_manager, self)
        
        self.current_heuristic_idx = 0
        
        print(f"Screen: {self.screen_width}x{self.screen_height}, Cell: {self.cell_size}, Maze: {self.max_width}x{self.max_height}")
    
    def _calculate_optimal_cell_size(self):
        max_cell_width = (MAX_SCREEN_WIDTH - 20) // self.max_width
        max_cell_height = (MAX_SCREEN_HEIGHT - INFO_HEIGHT - 20) // self.max_height
        
        optimal_size = min(max_cell_width, max_cell_height)
        
        if self.max_width <= 20 and self.max_height <= 20:
            return max(25, min(50, optimal_size))
        elif self.max_width <= 40 and self.max_height <= 40:
            return max(20, min(35, optimal_size))
        else:
            return max(15, min(25, optimal_size))
    
    def draw_grid(self):
        layout = self.env.layouts[self.game_state.current_state.layout_index]
        
        current_height = layout.height
        current_width = layout.width
        
        maze_width = current_width * self.cell_size
        maze_height = current_height * self.cell_size
        
        offset_x = (self.screen_width - maze_width) // 2
        offset_y = (self.max_height * self.cell_size - maze_height) // 2
        
        self.game_state.update_visual_effects()
        
        flash_overlay = self.game_state.rotation_flash > 0
        
        pie_flash = self.game_state.pie_flash > 0
        is_goal = self.problem.is_goal(self.game_state.current_state)
        if is_goal:
            self.screen.fill((20, 40, 20))
        else:
            self.screen.fill(DARK_GRAY)
        
        if pie_flash:
            flash_surface = pygame.Surface((self.screen_width, self.screen_height))
            flash_surface.fill(YELLOW)
            alpha = int((self.game_state.pie_flash / PIE_FLASH_DURATION) * 60)
            flash_surface.set_alpha(alpha)
            self.screen.blit(flash_surface, (0, 0))
        
        maze_rect = pygame.Rect(offset_x, offset_y, maze_width, maze_height)
        pygame.draw.rect(self.screen, BLACK, maze_rect)
        for row in range(current_height):
            for col in range(current_width):
                pos = (row, col)
                rect = pygame.Rect(
                    col * self.cell_size + offset_x, 
                    row * self.cell_size + offset_y, 
                    self.cell_size, 
                    self.cell_size
                )
                
                if layout.is_wall(pos):
                    color = BLUE
                    if flash_overlay:
                        color = tuple(min(c + 50, 255) for c in color)
                    pygame.draw.rect(self.screen, color, rect)
                else:
                    if is_goal:
                        pygame.draw.rect(self.screen, (10, 30, 10), rect)
                    else:
                        pygame.draw.rect(self.screen, BLACK, rect)
                
                if pos == layout.exit_gate:
                    color = LIGHT_GREEN if is_goal else GREEN
                    pygame.draw.rect(self.screen, color, rect.inflate(-10, -10))
                
                if pos in self.game_state.current_state.food:
                    dot_size = max(4, self.cell_size // 7)
                    pygame.draw.circle(self.screen, WHITE, rect.center, dot_size)
                
                if pos in self.game_state.current_state.pies:
                    powerup_img = self.image_manager.get_powerup_image()
                    if powerup_img:
                        img_rect = powerup_img.get_rect(center=rect.center)
                        self.screen.blit(powerup_img, img_rect)
                    else:
                        pie_size = max(8, self.cell_size // 3)
                        pygame.draw.circle(self.screen, ORANGE, rect.center, pie_size)
                
                pygame.draw.rect(self.screen, GRAY, rect, 1)
        
        for corner_name, corner_pos in layout.teleports.items():
            row, col = corner_pos
            rect = pygame.Rect(
                col * self.cell_size + offset_x,
                row * self.cell_size + offset_y,
                self.cell_size,
                self.cell_size
            )
            
            is_current = (self.game_state.current_state.pacman_pos == corner_pos)
            
            self.image_manager.draw_teleport_indicator(self.screen, rect, is_current)
        
        has_pie_timer = self.game_state.current_state.pie_timer > 0
        for i, ghost in enumerate(self.game_state.current_state.ghosts):
            row, col = ghost.position
            rect = pygame.Rect(
                col * self.cell_size + offset_x,
                row * self.cell_size + offset_y,
                self.cell_size,
                self.cell_size
            )
            
            if has_pie_timer:
                if self.game_state.current_state.pie_timer <= 2:
                    if pygame.time.get_ticks() % 400 < 200:
                        scared_img = self.image_manager.get_scared_ghost_image()
                        if scared_img:
                            img_rect = scared_img.get_rect(center=rect.center)
                            self.screen.blit(scared_img, img_rect)
                        else:
                            ghost_size = max(10, self.cell_size // 3)
                            pygame.draw.circle(self.screen, BLUE, rect.center, ghost_size)
                    else:
                        ghost_img = self.image_manager.get_ghost_image(i)
                        if ghost_img:
                            img_rect = ghost_img.get_rect(center=rect.center)
                            img_alpha = ghost_img.copy()
                            img_alpha.set_alpha(128)
                            self.screen.blit(img_alpha, img_rect)
                        else:
                            ghost_size = max(10, self.cell_size // 3)
                            pygame.draw.circle(self.screen, RED, rect.center, ghost_size)
                else:
                    scared_img = self.image_manager.get_scared_ghost_image()
                    if scared_img:
                        img_rect = scared_img.get_rect(center=rect.center)
                        self.screen.blit(scared_img, img_rect)
                    else:
                        ghost_size = max(10, self.cell_size // 3)
                        pygame.draw.circle(self.screen, BLUE, rect.center, ghost_size)
            else:
                ghost_img = self.image_manager.get_ghost_image(i)
                if ghost_img:
                    img_rect = ghost_img.get_rect(center=rect.center)
                    self.screen.blit(ghost_img, img_rect)
                else:
                    ghost_size = max(10, self.cell_size // 3)
                    pygame.draw.circle(self.screen, RED, rect.center, ghost_size)
        
        pacman_row, pacman_col = self.game_state.current_state.pacman_pos
        pacman_rect = pygame.Rect(
            pacman_col * self.cell_size + offset_x,
            pacman_row * self.cell_size + offset_y,
            self.cell_size,
            self.cell_size
        )
        
        if self.game_state.current_state.pie_timer > 0:
            self.game_state.glow_pulse += 0.15
            
            base_glow = max(14, self.cell_size // 2 + 2)
            pulse_size = base_glow + int(4 * abs(pygame.math.Vector2(1, 0).rotate(self.game_state.glow_pulse * 180 / 3.14159).x))
            
            if self.game_state.current_state.pie_timer <= 2:
                if pygame.time.get_ticks() % 400 < 200:
                    glow_color = ORANGE
                else:
                    glow_color = YELLOW
            else:
                glow_color = YELLOW
            
            for i in range(3):
                radius = pulse_size + i * 3
                alpha_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                glow_alpha = max(0, 100 - i * 30)
                pygame.draw.circle(alpha_surface, (*glow_color, glow_alpha), (radius, radius), radius)
                glow_rect = alpha_surface.get_rect(center=pacman_rect.center)
                self.screen.blit(alpha_surface, glow_rect)
        else:
            self.game_state.glow_pulse = 0
        
        pacman_direction = self.input_handler.get_pacman_direction()
        pacman_img = self.image_manager.get_pacman_image(pacman_direction)
        if pacman_img:
            img_rect = pacman_img.get_rect(center=pacman_rect.center)
            self.screen.blit(pacman_img, img_rect)
        else:
            pacman_size = max(12, self.cell_size // 2)
            pygame.draw.circle(self.screen, YELLOW, pacman_rect.center, pacman_size)
        
        pygame.draw.rect(self.screen, WHITE, maze_rect, 2)
        if len(layout.teleports) > 0:
            legend_y = 10
            if self.game_state.rotation_flash > 0:
                legend_y += 30
            if self.game_state.current_state.pie_timer > 0:
                legend_y += 30
            
            legend_text = self.small_font.render(
                f"Blue = Teleport ({len(layout.teleports)} points)", 
                True, 
                CYAN
            )
            legend_rect = legend_text.get_rect()
            legend_rect.topright = (self.screen_width - 10, legend_y)
            self.screen.blit(legend_text, legend_rect)
        
        if self.game_state.rotation_flash > 0:
            rotation_text = self.font.render("ROTATING", True, ORANGE)
            text_rect = rotation_text.get_rect()
            text_rect.topright = (self.screen_width - 10, 10)
            self.screen.blit(rotation_text, text_rect)
        
        if self.game_state.current_state.pie_timer > 0:
            power_text = self.font.render(f"POWER: {self.game_state.current_state.pie_timer}", True, YELLOW)
            text_rect = power_text.get_rect()
            text_rect.topleft = (10, 10)
            self.screen.blit(power_text, text_rect)
        
        if self.game_state.is_manual_mode:
            mode_text = self.font.render("MANUAL MODE", True, CYAN)
            text_rect = mode_text.get_rect()
            text_rect.midtop = (self.screen_width // 2, 10)
            self.screen.blit(mode_text, text_rect)
            
            controls_text = self.small_font.render("WASD: Move | T: Teleport | Space: Stop | ESC: Exit", True, WHITE)
            controls_rect = controls_text.get_rect()
            controls_rect.midtop = (self.screen_width // 2, 35)
            self.screen.blit(controls_text, controls_rect)
    
    def draw_info(self):
        maze_height = self.max_height * self.cell_size
        y_offset = maze_height + 10
        
        self.button_manager.draw(
            self.screen, self.font,
            self.game_state.is_auto_play,
            self.game_state.is_manual_mode,
            self.game_state.is_computing
        )
        
        self.message_manager.draw(self.screen, self.font, y_offset)
        self.info_panel.draw(
            self.screen, self.game_state.stats,
            self.game_state.current_state, self.env,
            self.game_state.is_game_over,
            self.game_state.is_manual_mode,
            len(self.game_state.path)
        )
    
    def solve_puzzle(self):
        if self.game_state.is_computing:
            self.message_manager.show_message("Computing...", ORANGE, 30)
            return
        
        if self.game_state.is_manual_mode:
            self.message_manager.show_message("Exit Manual Mode first!", ORANGE, 60)
            return
        
        heuristic_name = HEURISTICS[self.current_heuristic_idx][1]
        print(f"🔍 Solving with {heuristic_name}...")
        self.message_manager.show_message(f"🔍 Solving with {heuristic_name}...", ORANGE, 90)
        
        def run_auto_wrapper(heuristic):
            return run_auto_mode(self.layout_lines, heuristic=heuristic)
        
        self.game_state.solve_puzzle(heuristic_name, run_auto_wrapper)
    
    def change_heuristic(self):
        if self.game_state.is_computing:
            self.message_manager.show_message("⏳ Wait for computation!", ORANGE, 60)
            return
        
        self.current_heuristic_idx = (self.current_heuristic_idx + 1) % len(HEURISTICS)
        heuristic_name = HEURISTICS[self.current_heuristic_idx][0]
        self.button_manager.update_heuristic_button(self.current_heuristic_idx)
        
        self.game_state.reset()
        self.message_manager.show_message(f"🔧 Heuristic: {heuristic_name}", WHITE, 90)
    
    def run(self):
        running = True
        
        while running:
            if self.game_state.check_solution_ready():
                self.message_manager.show_message(f"Solution found! Length: {len(self.game_state.path)}", GREEN, 120)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.input_handler.handle_mouse_click(event.pos):
                        pass
                elif event.type == pygame.KEYDOWN:
                    self.input_handler.handle_keyboard(event.key)
            
            if hasattr(self, '_pending_action'):
                action = self._pending_action
                delattr(self, '_pending_action')
                
                if action == "solve":
                    self.solve_puzzle()
                elif action == "change_h":
                    self.change_heuristic()
            
            if self.game_state.update_auto_play():
                if self.game_state.path_index >= len(self.game_state.path):
                    self.game_state.is_auto_play = False
                    self.message_manager.show_message("Auto play completed!", GREEN, 90)
                elif self.problem.is_goal(self.game_state.current_state):
                    self.game_state.is_auto_play = False
                    self.message_manager.show_message("Goal reached!", LIGHT_GREEN, 120)
            
            if self.game_state.is_manual_mode:
                self.game_state.update_manual_mode()
            
            if self.game_state.check_game_over():
                self.message_manager.show_message("Game reset! Try again!", YELLOW, 90)
            
            self.message_manager.update()
            
            self.draw_grid()
            self.draw_info()
            pygame.display.flip()
            self.clock.tick(30)
        
        pygame.quit()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", type=Path, help="Path to layout file")
    args = parser.parse_args()
    
    gui = PacmanGUI(args.layout)
    gui.run()


if __name__ == "__main__":
    main()
