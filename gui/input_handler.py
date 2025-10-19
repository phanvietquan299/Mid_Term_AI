import pygame
from typing import Callable, Optional, Tuple
from .constants import *


class InputHandler:
    
    def __init__(self, game_state_manager, message_manager, button_manager, gui_callback=None):
        self.game_state = game_state_manager
        self.message_manager = message_manager
        self.button_manager = button_manager
        self.gui_callback = gui_callback
        
        self.pacman_direction = "right"
    
    def handle_mouse_click(self, pos: Tuple[int, int]) -> bool:
        if self.game_state.is_computing:
            self.message_manager.show_message("⏳ Computing...", ORANGE, 30)
            return True
        
        action = self.button_manager.handle_click(pos)
        if not action:
            return False
        
        if action == "solve":
            return self._handle_solve()
        elif action == "auto":
            return self._handle_auto_play()
        elif action == "step":
            return self._handle_step()
        elif action == "reset":
            return self._handle_reset()
        elif action == "manual":
            return self._handle_manual_mode()
        elif action == "change_h":
            return self._handle_change_heuristic()
        
        return False
    
    def handle_keyboard(self, key: int) -> bool:
        if not self.game_state.is_manual_mode:
            return False
        
        if self.game_state.is_game_over:
            return False
        
        if key == pygame.K_ESCAPE:
            self._toggle_manual_mode()
            return True
        
        if self.game_state.problem.is_goal(self.game_state.current_state):
            self.message_manager.show_message("Already at goal!", LIGHT_GREEN, 60)
            return True
        
        if key == pygame.K_t:
            return self._handle_teleport_manual()
        
        key_to_action = {
            pygame.K_UP: "Up",
            pygame.K_DOWN: "Down",
            pygame.K_LEFT: "Left",
            pygame.K_RIGHT: "Right",
            pygame.K_w: "Up",
            pygame.K_s: "Down",
            pygame.K_a: "Left",
            pygame.K_d: "Right",
            pygame.K_SPACE: "Stop"
        }
        
        action_name = key_to_action.get(key)
        if not action_name:
            return False
        
        self._update_pacman_direction(action_name)
        
        success = self.game_state.move_pacman_manual(action_name)
        
        if not success:
            if action_name == "Stop":
                return True  # Stop is always valid
            
            layout = self.game_state.env.layouts[self.game_state.current_state.layout_index]
            new_pos = (
                self.game_state.current_state.pacman_pos[0] + ACTION_DELTAS[action_name][0],
                self.game_state.current_state.pacman_pos[1] + ACTION_DELTAS[action_name][1]
            )
            
            if not layout.in_bounds(new_pos):
                self.message_manager.show_message("Out of bounds!", RED, 30)
            elif layout.is_wall(new_pos) and self.game_state.current_state.pie_timer <= 0:
                self.message_manager.show_message("Wall!", RED, 30)
            elif any(g.position == new_pos for g in self.game_state.current_state.ghosts):
                self.message_manager.show_message("Ghost blocking!", RED, 30)
            else:
                self.message_manager.show_message("Invalid move!", RED, 30)
        else:
            if action_name != "Stop":
                if self.game_state.current_state.pie_timer == 5:
                    self.message_manager.show_message("Power Up!", YELLOW, 60)
                
                if self.game_state.current_state.time_step % 30 == 0:
                    self.message_manager.show_message(f"Maze rotated! (step {self.game_state.current_state.time_step})", ORANGE, 90)
            
            if self.game_state.problem.is_goal(self.game_state.current_state):
                self.message_manager.show_message("YOU WON! Goal reached!", LIGHT_GREEN, 180)
        
        return True
    
    def _update_pacman_direction(self, action_name: str):
        if action_name in DIRECTION_MAP:
            self.pacman_direction = DIRECTION_MAP[action_name]
    
    def _handle_solve(self) -> bool:
        if self.gui_callback and hasattr(self.gui_callback, 'solve_puzzle'):
            self.gui_callback.solve_puzzle()
            return True
        return False
    
    def _handle_auto_play(self) -> bool:
        if self.game_state.is_manual_mode:
            self.message_manager.show_message("Exit Manual Mode first!", ORANGE, 60)
            return True
        
        if not self.game_state.is_solving:
            self.message_manager.show_message("No solution! Solve first.", RED, 90)
            return True
        
        if self.game_state.path_index >= len(self.game_state.path):
            self.message_manager.show_message("Already completed!", GREEN, 60)
            return True
        
        success = self.game_state.toggle_auto_play()
        if success:
            self.message_manager.show_message("Auto play ON", GREEN, 60)
        else:
            self.message_manager.show_message("Auto play OFF", YELLOW, 60)
        
        return True
    
    def _handle_step(self) -> bool:
        if self.game_state.is_computing:
            return True
        
        if self.game_state.is_manual_mode:
            self.message_manager.show_message("Exit Manual Mode first!", ORANGE, 60)
            return True
        
        if not self.game_state.is_solving:
            self.message_manager.show_message("No solution! Solve first.", RED, 90)
            return True
        
        if self.game_state.problem.is_goal(self.game_state.current_state):
            self.game_state.is_auto_play = False
            self.message_manager.show_message("Goal reached!", LIGHT_GREEN, 120)
            return True
        
        if self.game_state.path_index >= len(self.game_state.path):
            self.game_state.is_auto_play = False
            self.message_manager.show_message("Path completed!", GREEN, 90)
            return True
        
        success = self.game_state.step_forward()
        if not success:
            self.message_manager.show_message("Step failed!", RED, 90)
        
        return True
    
    def _handle_reset(self) -> bool:
        self.game_state.reset()
        self.pacman_direction = "right"
        self.message_manager.show_message("Reset complete!", YELLOW, 60)
        return True
    
    def _handle_manual_mode(self) -> bool:
        is_manual = self.game_state.toggle_manual_mode()
        
        if is_manual:
            self.message_manager.show_message("Manual Mode ON - Use Arrow Keys!", CYAN, 120)
        else:
            self.message_manager.show_message("Manual Mode OFF - AI Mode Active", WHITE, 90)
        
        return True
    
    def _toggle_manual_mode(self):
        is_manual = self.game_state.toggle_manual_mode()
        
        if is_manual:
            self.message_manager.show_message("Manual Mode ON - Use Arrow Keys!", CYAN, 120)
        else:
            self.message_manager.show_message("Manual Mode OFF - AI Mode Active", WHITE, 90)
    
    def _handle_change_heuristic(self) -> bool:
        if self.game_state.is_computing:
            self.message_manager.show_message("Wait for computation!", ORANGE, 60)
            return True
        
        if self.gui_callback and hasattr(self.gui_callback, 'change_heuristic'):
            self.gui_callback.change_heuristic()
            return True
        return False
    
    def _handle_teleport_manual(self) -> bool:
        layout = self.game_state.env.layouts[self.game_state.current_state.layout_index]
        current_pos = self.game_state.current_state.pacman_pos
        
        corner = layout.corner_name(current_pos)
        
        if not corner:
            if len(layout.teleports) == 0:
                self.message_manager.show_message("No teleport points on this map!", ORANGE, 90)
            else:
                teleport_names = list(layout.teleports.keys())
                self.message_manager.show_message(f"Not at teleport! Available: {', '.join(teleport_names)}", ORANGE, 90)
            return True
        
        available_corners = [
            (name, pos) for name, pos in layout.teleports.items()
            if pos != current_pos
        ]
        
        if not available_corners:
            self.message_manager.show_message("No other teleport destinations!", RED, 60)
            return True
        
        corner_order = ["TL", "TR", "BR", "BL"]
        
        try:
            current_idx = corner_order.index(corner)
            
            for i in range(1, 5):
                check_idx = (current_idx + i) % 4
                check_name = corner_order[check_idx]
                
                if check_name in layout.teleports and check_name != corner:
                    target_name = check_name
                    break
            else:
                target_name = available_corners[0][0]
        except:
            target_name = available_corners[0][0]
        
        target_pos = layout.teleports[target_name]
        if any(g.position == target_pos for g in self.game_state.current_state.ghosts):
            self.message_manager.show_message(f"Ghost at {target_name}!", RED, 60)
            return True
        
        success = self.game_state.teleport_manual(target_name)
        
        if success:
            self.message_manager.show_message(f"Teleported {corner} -> {target_name}!", CYAN, 90)
            
            if self.game_state.problem.is_goal(self.game_state.current_state):
                self.message_manager.show_message("YOU WON! Goal reached!", LIGHT_GREEN, 180)
        else:
            self.message_manager.show_message("Teleport failed!", RED, 60)
        
        return True
    
    def get_pacman_direction(self) -> str:
        return self.pacman_direction