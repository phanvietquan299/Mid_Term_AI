import threading
from queue import Queue
from typing import List, Optional, Tuple, Dict, Any
from .constants import *


class GameStateManager:
    
    def __init__(self, env, problem, initial_state):
        self.env = env
        self.problem = problem
        self.initial_state = initial_state
        self.current_state = initial_state
        
        self.path: List[Any] = []
        self.path_index = 0
        self.is_solving = False
        self.is_auto_play = False
        self.solving_thread: Optional[threading.Thread] = None
        self.solution_queue = Queue()
        self.is_computing = False
        self.auto_step_counter = 0
        
        self.is_manual_mode = False
        self.manual_step_delay = MANUAL_STEP_DELAY
        self.manual_frame_counter = 0
        
        self.is_game_over = False
        self.game_over_timer = 0
        
        self.last_layout_index = 0
        self.rotation_flash = 0
        self.pie_flash = 0
        self.last_pie_timer = 0
        self.glow_pulse = 0
        self.stats = {
            'cost': 0,
            'expanded': 0,
            'frontier': 0,
            'current_step': 0
        }
    
    def reset(self):
        self.current_state = self.initial_state
        self.path = []
        self.path_index = 0
        self.is_solving = False
        self.is_auto_play = False
        self.is_computing = False
        self.auto_step_counter = 0
        self.last_layout_index = 0
        self.rotation_flash = 0
        self.pacman_direction = "right"
        self.pie_flash = 0
        self.last_pie_timer = 0
        self.glow_pulse = 0
        self.is_manual_mode = False
        self.manual_frame_counter = 0
        self.is_game_over = False
        self.game_over_timer = 0
        
        while not self.solution_queue.empty():
            self.solution_queue.get()
        
        self.stats = {
            'cost': 0,
            'expanded': 0,
            'frontier': 0,
            'current_step': 0
        }
    
    def toggle_manual_mode(self):
        self.is_manual_mode = not self.is_manual_mode
        
        if self.is_manual_mode:
            self.is_auto_play = False
            self.manual_frame_counter = 0
        
        return self.is_manual_mode
    
    def handle_game_over(self):
        self.is_game_over = True
        self.game_over_timer = GAME_OVER_TIMER
        self.is_manual_mode = False
        self.is_auto_play = False
        print("GAME OVER - Ghost caught Pacman!")
    
    def check_game_over(self):
        if self.is_game_over:
            self.game_over_timer -= 1
            if self.game_over_timer <= 0:
                self.reset()
                return True  # Indicates game was reset
        return False
    
    def update_visual_effects(self):
        if self.current_state.layout_index != self.last_layout_index:
            self.rotation_flash = ROTATION_FLASH_DURATION
            self.last_layout_index = self.current_state.layout_index
        
        if self.rotation_flash > 0:
            self.rotation_flash -= 1
        
        if self.current_state.pie_timer > self.last_pie_timer:
            self.pie_flash = PIE_FLASH_DURATION
        
        self.last_pie_timer = self.current_state.pie_timer
        
        if self.pie_flash > 0:
            self.pie_flash -= 1
        
        if self.current_state.pie_timer > 0:
            self.glow_pulse += 0.15
        else:
            self.glow_pulse = 0
    
    def update_manual_mode(self):
        if not self.is_manual_mode or self.is_game_over or self.problem.is_goal(self.current_state):
            return
        
        self.manual_frame_counter += 1
        
        if self.manual_frame_counter >= self.manual_step_delay:
            self.manual_frame_counter = 0
            
            layout = self.env.layouts[self.current_state.layout_index]
            
            new_ghosts = tuple(self.problem._move_ghost(g, layout) for g in self.current_state.ghosts)
            
            if any(g.position == self.current_state.pacman_pos for g in new_ghosts):
                self.handle_game_over()
                return
            
            from pacman.environment import PacmanState
            new_state = PacmanState(
                pacman_pos=self.current_state.pacman_pos,
                ghosts=new_ghosts,
                food=self.current_state.food,
                pies=self.current_state.pies,
                layout_index=self.current_state.layout_index,
                time_step=self.current_state.time_step,
                pie_timer=self.current_state.pie_timer
            )
            
            self.current_state = new_state
    
    def move_pacman_manual(self, action_name: str) -> bool:
        if not self.is_manual_mode or self.is_game_over:
            return False
        
        if self.problem.is_goal(self.current_state):
            return False
        
        layout = self.env.layouts[self.current_state.layout_index]
        
        delta = ACTION_DELTAS.get(action_name, (0, 0))
        dr, dc = delta
        new_pos = (self.current_state.pacman_pos[0] + dr, self.current_state.pacman_pos[1] + dc)
        
        if not layout.in_bounds(new_pos):
            return False
        
        if layout.is_wall(new_pos) and self.current_state.pie_timer <= 0:
            return False
        
        if any(g.position == new_pos for g in self.current_state.ghosts):
            return False
        
        from pacman.environment import PacmanState
        
        pie_timer = max(self.current_state.pie_timer - 1, 0) if action_name != "Stop" else self.current_state.pie_timer
        
        new_pies = set(self.current_state.pies)
        if new_pos in new_pies:
            new_pies.remove(new_pos)
            pie_timer = 5
        
        new_food = set(self.current_state.food)
        if new_pos in new_food:
            new_food.remove(new_pos)
        
        new_ghosts = self.current_state.ghosts
        
        if any(g.position == new_pos for g in new_ghosts):
            return False
        
        new_time_step = self.current_state.time_step + 1
        
        new_state = PacmanState(
            pacman_pos=new_pos,
            ghosts=new_ghosts,
            food=frozenset(new_food),
            pies=frozenset(new_pies),
            layout_index=self.current_state.layout_index,
            time_step=new_time_step,
            pie_timer=pie_timer
        )
        
        if new_state.pie_timer == 0 and layout.is_wall(new_pos):
            return False
        
        if new_time_step % 30 == 0:
            print(f"Rotation at time_step {new_time_step}")
            new_state = self.env.rotate_state(new_state)
        
        self.current_state = new_state
        self.stats['current_step'] += 1
        self.stats['cost'] += 1
        
        return True
    
    def teleport_manual(self, target_name: str) -> bool:
        if not self.is_manual_mode or self.is_game_over:
            return False
        
        layout = self.env.layouts[self.current_state.layout_index]
        current_pos = self.current_state.pacman_pos
        
        corner = layout.corner_name(current_pos)
        if not corner:
            return False
        
        if target_name not in layout.teleports:
            return False
        
        target_pos = layout.teleports[target_name]
        
        if any(g.position == target_pos for g in self.current_state.ghosts):
            return False
        
        from pacman.environment import PacmanState
        
        pie_timer = max(self.current_state.pie_timer - 1, 0)
        
        new_pies = set(self.current_state.pies)
        if target_pos in new_pies:
            new_pies.remove(target_pos)
            pie_timer = 5
        
        new_food = set(self.current_state.food)
        if target_pos in new_food:
            new_food.remove(target_pos)
        
        new_ghosts = self.current_state.ghosts
        
        if any(g.position == target_pos for g in new_ghosts):
            return False
        
        new_time_step = self.current_state.time_step + 1
        
        new_state = PacmanState(
            pacman_pos=target_pos,
            ghosts=new_ghosts,
            food=frozenset(new_food),
            pies=frozenset(new_pies),
            layout_index=self.current_state.layout_index,
            time_step=new_time_step,
            pie_timer=pie_timer
        )
        
        if new_state.pie_timer == 0 and layout.is_wall(target_pos):
            return False
        
        if new_time_step % 30 == 0:
            print(f"Rotation at time_step {new_time_step}")
            new_state = self.env.rotate_state(new_state)
        
        self.current_state = new_state
        self.stats['current_step'] += 1
        self.stats['cost'] += 1
        
        return True
    
    def solve_puzzle(self, heuristic_name: str, run_auto_mode_func):
        if self.is_computing or self.is_manual_mode:
            return False
        
        while not self.solution_queue.empty():
            self.solution_queue.get()
        
        print(f"🔍 Solving with {heuristic_name}...")
        self.is_computing = True
        
        def solve_worker():
            try:
                path, cost, expanded, frontier = run_auto_mode_func(heuristic=heuristic_name)
                self.solution_queue.put({
                    'success': True,
                    'path': path if path is not None else [],
                    'cost': cost,
                    'expanded': expanded,
                    'frontier': frontier
                })
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                self.solution_queue.put({'success': False, 'error': str(e)})
        
        self.solving_thread = threading.Thread(target=solve_worker, daemon=True)
        self.solving_thread.start()
        return True
    
    def check_solution_ready(self) -> bool:
        if self.solution_queue.empty():
            return False
        
        result = self.solution_queue.get()
        self.is_computing = False
        
        if result['success']:
            self.path = result['path']
            self.stats['cost'] = result['cost']
            self.stats['expanded'] = result['expanded']
            self.stats['frontier'] = result['frontier']
            self.path_index = 0
            self.stats['current_step'] = 0
            self.is_solving = True
            
            print(f"Solution found! Length: {len(self.path)}")
            return True
        else:
            self.path = []
            self.is_solving = False
            self.stats = {
                'cost': 0,
                'expanded': 0,
                'frontier': 0,
                'current_step': 0
            }
            error = result.get('error', 'Unknown error')
            print(f"Failed: {error}")
            return False
    
    def toggle_auto_play(self) -> bool:
        if self.is_manual_mode or not self.is_solving or self.path_index >= len(self.path):
            return False
        
        self.is_auto_play = not self.is_auto_play
        if self.is_auto_play:
            self.auto_step_counter = 0
        
        return self.is_auto_play
    
    def step_forward(self) -> bool:
        if (self.is_computing or self.is_manual_mode or not self.is_solving or 
            self.problem.is_goal(self.current_state) or self.path_index >= len(self.path)):
            return False
        
        action = self.path[self.path_index]
        action_name = action.type
        success = False
        
        if action_name in ACTION_DELTAS:
            delta = ACTION_DELTAS[action_name]
            move_result = self.problem._apply_move(
                self.current_state,
                self.env.layouts[self.current_state.layout_index],
                action_name,
                delta
            )
            if move_result:
                self.current_state, _, _ = move_result[0]
                success = True
        
        elif action_name == "Teleport":
            target = action.payload.get("to") if action.payload else None
            if target:
                teleport_result = self.problem._apply_teleport(
                    self.current_state,
                    self.env.layouts[self.current_state.layout_index],
                    target
                )
                if teleport_result:
                    self.current_state = teleport_result
                    success = True
        
        if success:
            self.path_index += 1
            self.stats['current_step'] = self.path_index
        else:
            print(f"Action {action_name} failed!")
            self.is_auto_play = False
        
        return success
    
    def update_auto_play(self) -> bool:
        if not self.is_auto_play or self.is_manual_mode:
            return False
        
        if (self.path_index >= len(self.path) or 
            self.problem.is_goal(self.current_state)):
            self.is_auto_play = False
            return False
        
        self.auto_step_counter += 1
        if self.auto_step_counter >= AUTO_STEP_DELAY:
            self.auto_step_counter = 0
            return self.step_forward()
        
        return False
