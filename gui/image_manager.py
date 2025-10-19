import pygame
from pathlib import Path
from typing import Dict, List, Optional
from .constants import *


class ImageManager:
    
    def __init__(self, cell_size: int):
        self.cell_size = cell_size
        self.base_path = Path(__file__).parent.parent / "pacman-art"
        
        self.pacman_images: Dict[str, Optional[pygame.Surface]] = {}
        self.ghost_images: List[Optional[pygame.Surface]] = []
        self.powerup_img: Optional[pygame.Surface] = None
        self.scared_ghost_img: Optional[pygame.Surface] = None
        self.teleport_icon: Optional[pygame.Surface] = None
        self._load_pacman_images()
        self._load_ghost_images()
        self._load_powerup_image()
        self._load_scared_ghost_image()
        self._load_teleport_icon()
    
    def _load_pacman_images(self):
        directions = ["up", "down", "left", "right"]
        
        for direction in directions:
            dir_path = self.base_path / f"pacman-{direction}"
            try:
                image_files = list(dir_path.glob("*.png"))
                if image_files:
                    img = pygame.image.load(str(image_files[0]))
                    img = pygame.transform.scale(img, (self.cell_size - 4, self.cell_size - 4))
                    self.pacman_images[direction] = img
                else:
                    self.pacman_images[direction] = None
            except Exception as e:
                print(f"Cannot load pacman-{direction}: {e}")
                self.pacman_images[direction] = None
    
    def _load_ghost_images(self):
        ghost_path = self.base_path / "ghosts"
        
        try:
            ghost_files = sorted(list(ghost_path.glob("*.png")))
            for i in range(min(4, len(ghost_files))):
                img = pygame.image.load(str(ghost_files[i]))
                img = pygame.transform.scale(img, (self.cell_size - 6, self.cell_size - 6))
                self.ghost_images.append(img)
        except Exception as e:
            print(f"Cannot load ghosts: {e}")
            self.ghost_images = []
        
        while len(self.ghost_images) < 4:
            self.ghost_images.append(None)
    
    def _load_powerup_image(self):
        try:
            self.powerup_img = pygame.image.load(str(self.base_path / "other" / "strawberry.png"))
            self.powerup_img = pygame.transform.scale(self.powerup_img, (self.cell_size - 8, self.cell_size - 8))
        except Exception as e:
            print(f"Cannot load strawberry.png: {e}")
            self.powerup_img = None
    
    def _load_scared_ghost_image(self):
        try:
            self.scared_ghost_img = pygame.image.load(str(self.base_path / "other" / "apple.png"))
            self.scared_ghost_img = pygame.transform.scale(self.scared_ghost_img, (self.cell_size - 6, self.cell_size - 6))
        except Exception as e:
            print(f"Cannot load apple.png: {e}")
            self.scared_ghost_img = None
    
    def _load_teleport_icon(self):
        try:
            teleport_path = self.base_path / "other" / "teleport.png"
            
            if teleport_path.exists():
                img = pygame.image.load(str(teleport_path))
                self.teleport_icon = pygame.transform.scale(img, (self.cell_size - 8, self.cell_size - 8))
            else:
                self.teleport_icon = None
        except:
            self.teleport_icon = None
    
    def get_pacman_image(self, direction: str) -> Optional[pygame.Surface]:
        return self.pacman_images.get(direction)
    
    def get_ghost_image(self, index: int) -> Optional[pygame.Surface]:
        if 0 <= index < len(self.ghost_images):
            return self.ghost_images[index]
        return None
    
    def get_powerup_image(self) -> Optional[pygame.Surface]:
        return self.powerup_img
    
    def get_scared_ghost_image(self) -> Optional[pygame.Surface]:
        return self.scared_ghost_img
    
    def get_teleport_icon(self) -> Optional[pygame.Surface]:
        return self.teleport_icon
    
    def draw_teleport_indicator(self, surface: pygame.Surface, rect: pygame.Rect, is_current: bool = False):
        if self.teleport_icon:
            icon_rect = self.teleport_icon.get_rect(center=rect.center)
            surface.blit(self.teleport_icon, icon_rect)
        else:
            center_x, center_y = rect.center
            
            radius_outer = max(8, self.cell_size // 3)
            radius_inner = max(5, self.cell_size // 4)
            
            if is_current:
                pygame.draw.circle(surface, CYAN, rect.center, radius_outer, 3)
                pygame.draw.circle(surface, YELLOW, rect.center, radius_inner)
                
                font_size = max(16, self.cell_size // 2)
                t_font = pygame.font.Font(None, font_size)
                t_text = t_font.render("T", True, WHITE)
                t_rect = t_text.get_rect(center=rect.center)
                surface.blit(t_text, t_rect)
            else:
                pygame.draw.circle(surface, CYAN, rect.center, radius_outer, 2)
                pygame.draw.circle(surface, (0, 200, 200), rect.center, radius_inner, 2)
                
                font_size = max(12, self.cell_size // 3)
                t_font = pygame.font.Font(None, font_size)
                t_text = t_font.render("T", True, CYAN)
                t_rect = t_text.get_rect(center=rect.center)
                surface.blit(t_text, t_rect)