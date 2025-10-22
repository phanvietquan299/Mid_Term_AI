from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pygame

from .ui_style import PALETTE


@dataclass
class SpriteSheet:
    pacman: Dict[str, Optional[pygame.Surface]]
    ghosts: Dict[int, Optional[pygame.Surface]]
    powerup: Optional[pygame.Surface]
    scared: Optional[pygame.Surface]
    teleport: Optional[pygame.Surface]
    tile_wall: Optional[pygame.Surface]
    tile_food: Optional[pygame.Surface]
    tile_exit: Optional[pygame.Surface]
    tile_pie: Optional[pygame.Surface]


class ImageManager:
    """Light-weight sprite loader with graceful fallbacks.

    The original student project used bare PNG loads scattered through the code.
    Here we collect everything in a single place so the rest of the UI can operate
    purely with surfaces without knowing about the filesystem.
    """

    def __init__(self, cell_size: int):
        self._cell_size = cell_size
        candidates = [
            Path(__file__).resolve().parents[1] / "assets",
            Path(__file__).resolve().parents[1] / "pacman_assets",
            Path(__file__).resolve().parents[2] / "pacman-art",
        ]
        for candidate in candidates:
            if candidate.exists():
                self._asset_root = candidate
                break
        else:
            self._asset_root = candidates[0]

        self._asset_sources: List[Path] = [self._asset_root]
        for entry in self._asset_root.iterdir():
            if entry.is_dir():
                self._asset_sources.append(entry)

        self._sprites = self._load_sheet()

    # ------------------------------------------------------------------ public
    def pacman(self, facing: str) -> Optional[pygame.Surface]:
        return self._sprites.pacman.get(facing)

    def ghost(self, index: int) -> Optional[pygame.Surface]:
        return self._sprites.ghosts.get(index)

    def powerup(self) -> Optional[pygame.Surface]:
        return self._sprites.powerup

    def scared(self) -> Optional[pygame.Surface]:
        return self._sprites.scared

    def teleport_icon(self) -> Optional[pygame.Surface]:
        return self._sprites.teleport

    def tile_wall(self) -> Optional[pygame.Surface]:
        return self._sprites.tile_wall

    def tile_food(self) -> Optional[pygame.Surface]:
        return self._sprites.tile_food

    def tile_exit(self) -> Optional[pygame.Surface]:
        return self._sprites.tile_exit

    def tile_pie(self) -> Optional[pygame.Surface]:
        return self._sprites.tile_pie or self._sprites.powerup

    # ----------------------------------------------------------------- internal
    def _load_sheet(self) -> SpriteSheet:
        pacman = {f: None for f in ("up", "down", "left", "right")}
        ghosts: Dict[int, Optional[pygame.Surface]] = {}
        powerup = scared = teleport = None
        tile_wall = tile_food = tile_exit = tile_pie = None

        synonym_table = {
            "wall": ["wall", "block"],
            "food": ["food", "banana", "pellet"],
            "pies": ["pie", "pies", "power", "dragon"],
            "exit": ["exit", "door", "goal", "road"],
            "teleport": ["teleport", "portal"],
            "pacman": ["pacman", "player", "hero"],
            "ghost": ["ghost", "enemy"],
            "ghost_scared": ["scared", "fear"],
            "powerup": ["power", "dragon", "pies"],
        }

        def load_asset(name: str, size: int) -> Optional[pygame.Surface]:
            base = name.strip()
            stem = Path(base).stem.lower()
            suffix = Path(base).suffix.lower()

            tokens = {
                stem,
                stem.replace("_", "-"),
                stem.split("-")[0],
                stem.split("_")[0],
            }

            filename_candidates: List[str] = [base]
            if suffix == "":
                filename_candidates.extend([f"{stem}.png", f"{stem}.jpg", f"{stem}.jpeg"])
            else:
                filename_candidates.extend(
                    [
                        f"{Path(base).stem}.png",
                        f"{Path(base).stem}.jpg",
                        f"{Path(base).stem}.jpeg",
                    ]
                )

            visited: set[Path] = set()
            for directory in self._asset_sources:
                for candidate_name in filename_candidates:
                    candidate_path = directory / candidate_name
                    if candidate_path in visited:
                        continue
                    visited.add(candidate_path)
                    surf = self._load_scaled(candidate_path, size)
                    if surf is not None:
                        return surf

            synonym_keys: List[str] = []
            for token in tokens:
                synonym_keys.append(token)
                synonym_keys.extend(synonym_table.get(token, []))

            for directory in self._asset_sources:
                for entry in directory.iterdir():
                    if entry in visited or not entry.is_dir():
                        continue
                    entry_name = entry.name.lower()
                    if any(key in entry_name for key in synonym_keys):
                        surf = self._load_from_directory(entry, size)
                        if surf is not None:
                            return surf

            return None

        def load_sequence(keyword: str, size: int) -> List[pygame.Surface]:
            frames: List[pygame.Surface] = []
            key_lower = keyword.lower()
            for directory in self._asset_sources:
                for entry in directory.iterdir():
                    if entry.is_dir() and key_lower in entry.name.lower():
                        for candidate in sorted(entry.iterdir()):
                            surf = self._load_scaled(candidate, size)
                            if surf is not None:
                                frames.append(surf)
                        if frames:
                            return frames
            return frames

        # Load environment tiles
        tile_wall = load_asset("wall.png", self._cell_size)
        tile_food = load_asset("food.png", max(int(self._cell_size * 0.45), 6))
        tile_exit = load_asset("exit.png", max(self._cell_size - 4, 8))
        tile_pie = load_asset("pies.png", max(int(self._cell_size * 0.7), 8))

        # Load Pacman sprites
        for direction in pacman:
            pacman[direction] = load_asset(
                f"pacman-{direction}.png",
                max(self._cell_size - 4, 10),
            )

        single_pacman = load_asset("pacman.png", max(self._cell_size - 4, 10))
        if single_pacman is not None:
            for key in pacman:
                pacman[key] = pacman[key] or single_pacman

        # Load Ghost sprites
        for idx in range(4):
            ghosts[idx] = load_asset(
                f"ghost-{idx}.png",
                max(self._cell_size - 4, 10),
            )
        single_ghost = load_asset("ghost.png", max(self._cell_size - 4, 10))
        if single_ghost is not None:
            for idx in range(4):
                ghosts[idx] = ghosts[idx] or single_ghost

        ghost_scared = load_asset("ghost_scared.png", max(self._cell_size - 4, 10))
        scared = ghost_scared

        # Teleport / power-ups
        powerup = tile_pie or load_asset(
            "powerup.png",
            max(self._cell_size - 8, 8),
        ) or load_asset(
            "strawberry.png",
            max(self._cell_size - 8, 8),
        )
        teleport = load_asset(
            "teleport.png",
            max(self._cell_size - 8, 8),
        )
        if teleport is None:
            teleport = load_asset(
                "portal.png",
                max(self._cell_size - 8, 8),
            )

        # Fallback to legacy art packs if still missing
        for direction in pacman:
            if pacman[direction] is None:
                pacman[direction] = self._load_scaled(
                    self._asset_root / f"pacman-{direction}",
                    max(self._cell_size - 4, 10),
                )

        ghost_dir = self._asset_root / "ghosts"
        if any(v is None for v in ghosts.values()) and ghost_dir.exists():
            for idx, path in enumerate(sorted(ghost_dir.glob("*.png"))):
                ghosts[idx] = ghosts.get(idx) or self._load_scaled(
                    path, max(self._cell_size - 6, 8)
                )

        powerup = powerup or self._load_scaled(
            self._asset_root / "other" / "strawberry.png",
            max(self._cell_size - 8, 8),
        )
        scared = scared or self._load_scaled(
            self._asset_root / "other" / "apple.png",
            max(self._cell_size - 6, 8),
        )
        teleport = teleport or self._load_scaled(
            self._asset_root / "other" / "teleport.png",
            max(self._cell_size - 8, 8),
        )

        # Guarantee dictionary indexes even if we failed to load sprites.
        for idx in range(4):
            ghosts.setdefault(idx, None)

        return SpriteSheet(
            pacman,
            ghosts,
            powerup,
            scared,
            teleport,
            tile_wall,
            tile_food,
            tile_exit,
            tile_pie,
        )

    def _load_scaled(self, path: Path, target_size: int) -> Optional[pygame.Surface]:
        target_size = max(target_size, 2)
        if path.is_dir():
            candidates = sorted(path.glob('*.png'))
            if not candidates:
                candidates = sorted(path.glob('*.jpg'))
            if not candidates:
                candidates = sorted(path.glob('*.jpeg'))
            if not candidates:
                return None
            path = candidates[0]

        if not path.exists():
            return None

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(image, (target_size, target_size))
        except Exception as exc:  # pragma: no cover - debugging fallback
            print(f"[ImageManager] cannot load asset {path}: {exc}")
            return None

    def _load_from_directory(self, directory: Path, size: int) -> Optional[pygame.Surface]:
        if not directory.exists() or not directory.is_dir():
            return None
        candidates = sorted(
            [
                p
                for p in directory.iterdir()
                if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
            ]
        )
        for candidate in candidates:
            surf = self._load_scaled(candidate, size)
            if surf is not None:
                return surf
        return None

    # ------------------------------------------------------------- drawing aids
    def draw_portal(self, surface: pygame.Surface, rect: pygame.Rect, active: bool):
        icon = self.teleport_icon()
        if icon:
            surface.blit(icon, icon.get_rect(center=rect.center))
            return

        outer = max(9, self._cell_size // 3)
        inner = max(6, self._cell_size // 4)
        color = PALETTE["portal"]

        pygame.draw.circle(surface, color, rect.center, outer, 3)
        pygame.draw.circle(surface, color, rect.center, inner, 1 if active else 0)

        glyph_size = max(12, self._cell_size // 2 if active else self._cell_size // 3)
        glyph_font = pygame.font.Font(None, glyph_size)
        glyph = glyph_font.render("T", True, PALETTE["text"])
        surface.blit(glyph, glyph.get_rect(center=rect.center))
