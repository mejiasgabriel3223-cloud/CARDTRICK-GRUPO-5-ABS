"""Resolución centralizada de assets visuales del juego."""
from __future__ import annotations

import random
from pathlib import Path


class AssetResolver:
    """Localiza y asigna recursos visuales sin acoplar entidades a Pygame."""

    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root).resolve()
        self.joker_dir = self.project_root / "assets(beta)" / "jokers"
        self.blind_dir = self.project_root / "assets(beta)" / "ciegas"
        self._joker_assets = self._collect(self.joker_dir, "*.png")
        self._blind_assets = self._collect(self.blind_dir, "*.png")

    @staticmethod
    def _collect(directory: Path, pattern: str) -> list[Path]:
        if not directory.exists():
            return []
        return sorted(path for path in directory.glob(pattern) if path.is_file())

    def random_joker_asset(self) -> str:
        """Asigna un asset de Joker aleatorio para cada instancia creada."""
        if not self._joker_assets:
            return ""
        return random.choice(self._joker_assets).as_posix()

    def random_blind_asset(self) -> str:
        """Asigna un asset de ciega aleatorio a la ciega actualmente visible."""
        if not self._blind_assets:
            return ""
        return random.choice(self._blind_assets).as_posix()

    def blind_asset_for(self, blind_index: int, seed_text: str = "") -> str:
        """Elige un asset estable para la ciega actual pero cambia al cambiar el índice."""
        if not self._blind_assets:
            return ""
        # Mezcla el índice con el nombre para que la misma ciega sea reproducible
        # mientras que distintas ciegas reciban assets diferentes con frecuencia.
        numeric_seed = abs(hash((blind_index, seed_text)))
        return self._blind_assets[numeric_seed % len(self._blind_assets)].as_posix()
