import pygame
from typing import List, Dict, Any, Tuple
from .constants import *


class Button:
    
    def __init__(self, rect: pygame.Rect, text: str, action: str):
        self.rect = rect
        self.text = text
        self.action = action
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, 
             is_active: bool = False, active_color: Tuple[int, int, int] = None):
        color = active_color if is_active else WHITE
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        text_surface = font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)
    
    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


class ButtonManager:
    
    def __init__(self, screen_width: int, screen_height: int, maze_height: int, heuristics: List[Tuple[str, str]]):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.maze_height = maze_height
        self.heuristics = heuristics
        self.buttons: List[Button] = []
        self._create_buttons()
    
    def _create_buttons(self):
        y_start = self.maze_height + 10
        
        button_width = max(120, min(150, self.screen_width // 10))
        spacing = max(8, min(15, self.screen_width // 80))
        
        self.buttons = [
            Button(pygame.Rect(10, y_start, button_width, BUTTON_HEIGHT), "Solve", "solve"),
            Button(pygame.Rect(10 + button_width + spacing, y_start, button_width, BUTTON_HEIGHT), "Auto Play", "auto"),
            Button(pygame.Rect(10 + 2*(button_width + spacing), y_start, button_width, BUTTON_HEIGHT), "Step", "step"),
            Button(pygame.Rect(10 + 3*(button_width + spacing), y_start, button_width, BUTTON_HEIGHT), "Reset", "reset"),
            Button(pygame.Rect(10 + 4*(button_width + spacing), y_start, button_width, BUTTON_HEIGHT), "Manual", "manual"),
            Button(pygame.Rect(10, y_start + BUTTON_HEIGHT + spacing, button_width*2 + spacing, BUTTON_HEIGHT), 
                   f"H: {self.heuristics[0][0]}", "change_h")
        ]
    
    def update_heuristic_button(self, heuristic_idx: int):
        if len(self.buttons) > 5:
            self.buttons[5].text = f"H: {self.heuristics[heuristic_idx][0]}"
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, 
             is_auto_play: bool = False, is_manual_mode: bool = False, 
             is_computing: bool = False):
        for i, btn in enumerate(self.buttons):
            is_active = False
            active_color = WHITE
            
            if btn.action == "auto" and is_auto_play:
                is_active = True
                active_color = PURPLE
            elif btn.action == "manual" and is_manual_mode:
                is_active = True
                active_color = CYAN
            elif is_computing and btn.action == "solve":
                is_active = True
                active_color = ORANGE
            
            btn.draw(surface, font, is_active, active_color)
    
    def handle_click(self, pos: Tuple[int, int]) -> str:
        for btn in self.buttons:
            if btn.is_clicked(pos):
                return btn.action
        return None


class MessageManager:
    
    def __init__(self):
        self.message = ""
        self.message_color = WHITE
        self.message_timer = 0
    
    def show_message(self, msg: str, color: Tuple[int, int, int] = WHITE, duration: int = MESSAGE_DURATION):
        self.message = msg
        self.message_color = color
        self.message_timer = duration
    
    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
    
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, y_offset: int):
        if self.message and self.message_timer > 0:
            msg_surface = font.render(self.message, True, self.message_color)
            surface.blit(msg_surface, (10, y_offset - 35))


class InfoPanel:
    
    def __init__(self, screen_width: int, screen_height: int, maze_height: int, 
                 small_font: pygame.font.Font):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.maze_height = maze_height
        self.small_font = small_font
    
    def draw(self, surface: pygame.Surface, stats: Dict[str, Any], 
             current_state: Any, env: Any, is_game_over: bool = False,
             is_manual_mode: bool = False, path_length: int = 0):
        y_offset = self.maze_height + 10
        stats_y = y_offset + 2*BUTTON_HEIGHT + 20
        
        is_goal = env.problem.is_goal(current_state) if hasattr(env, 'problem') else False
        
        col1_x = 10
        stats_col1 = []
        
        if is_game_over:
            stats_col1.append(("GAME OVER!", RED))
        elif is_goal:
            stats_col1.append(("GOAL REACHED!", LIGHT_GREEN))
        
        if not is_game_over:
            mode_text = "Manual" if is_manual_mode else "AI"
            mode_color = CYAN if is_manual_mode else WHITE
            stats_col1.append((f"Mode: {mode_text}", mode_color))
        
        stats_col1.extend([
            (f"Cost: {stats['cost']}", WHITE),
            (f"Expanded: {stats['expanded']}", WHITE),
            (f"Frontier: {stats['frontier']}", WHITE),
            (f"Step: {stats['current_step']}/{path_length}", WHITE),
        ])
        
        col2_x = self.screen_width // 3
        stats_col2 = [
            (f"Food left: {len(current_state.food)}", WHITE),
        ]
        
        pie_color = WHITE
        if current_state.pie_timer > 0:
            pie_color = ORANGE if current_state.pie_timer <= 2 else YELLOW
        stats_col2.append((f"Power: {current_state.pie_timer}", pie_color))
        
        time_color = CYAN if is_manual_mode else WHITE
        stats_col2.append((f"Time: {current_state.time_step}", time_color))
        
        layout = env.layouts[current_state.layout_index]
        
        if len(layout.teleports) > 0:
            corner = layout.corner_name(current_state.pacman_pos)
            
            if corner:
                num_destinations = len(layout.teleports) - 1
                
                if is_manual_mode:
                    stats_col2.append((f"At {corner} - Press T ({num_destinations} dest)", CYAN))
                else:
                    stats_col2.append((f"At {corner} - Can teleport", CYAN))
            else:
                min_dist = float('inf')
                nearest_corner = None
                
                for name, pos in layout.teleports.items():
                    dist = abs(pos[0] - current_state.pacman_pos[0]) + abs(pos[1] - current_state.pacman_pos[1])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_corner = name
                
                if nearest_corner and is_manual_mode:
                    stats_col2.append((f"Nearest: {nearest_corner} ({min_dist} steps)", GRAY))
        else:
            stats_col2.append((f"No teleport available", GRAY))
        
        col3_x = 2 * self.screen_width // 3
        
        next_rotation = 30 - (current_state.time_step % 30)
        rotation_color = ORANGE if next_rotation <= 5 else WHITE
        
        stats_col3 = [
            (f"Maze: {layout.height}x{layout.width}", WHITE),
            (f"Cell: {getattr(env, 'cell_size', 0)}px", WHITE),
            (f"Rotation: {current_state.layout_index}/3", WHITE),
            (f"Next rotate: {next_rotation} steps", rotation_color),
        ]
        
        for i, (text, color) in enumerate(stats_col1):
            surface_text = self.small_font.render(text, True, color)
            surface.blit(surface_text, (col1_x, stats_y + i*22))
        
        for i, (text, color) in enumerate(stats_col2):
            surface_text = self.small_font.render(text, True, color)
            surface.blit(surface_text, (col2_x, stats_y + i*22))
        
        for i, (text, color) in enumerate(stats_col3):
            surface_text = self.small_font.render(text, True, color)
            surface.blit(surface_text, (col3_x, stats_y + i*22))