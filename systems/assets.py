"""Resolución centralizada de assets visuales del juego."""
from __future__ import annotations

import random
from pathlib import Path


class AssetResolver:
    """Localiza y asigna recursos visuales sin acoplar entidades a Pygame."""

    JOKER_FAMILIES: dict[str, tuple[str, ...]] = {
        "especial": ("joker-Especial.png",),
        "alado": (
            "joker-alado-amarillo.png",
            "joker-alado-azul.png",
            "joker-alado-morado.png",
            "joker-alado-negro.png",
            "joker-alado-rojo.png",
        ),
        "misterioso": (
            "joker-misterioso-amarillo.png",
            "joker-misterioso-azul.png",
            "joker-misterioso-negro.png",
            "joker-misterioso-rojo.png",
            "joker-misterioso-verde.png",
        ),
        "observador": (
            "joker-observador-azul.png",
            "joker-observador-gris.png",
            "joker-observador-naranja.png",
            "joker-observador-verde.png",
            "joker-observador.png",
        ),
        "sonriente": (
            "joker-sonriente-amarillo.png",
            "joker-sonriente-azul.png",
            "joker-sonriente-negro.png",
            "joker-sonriente-rojo.png",
            "joker-sonriente-verde.png",
        ),
        "truco": (
            "joker-truco-amarillo.png",
            "joker-truco-azul.png",
            "joker-truco-negro.png",
            "joker-truco-rojo.png",
            "joker-truco-verde.png",
        ),
        "doble": (
            "joker-doble.png",
            "joker-doble-cara-azul.png",
            "joker-doble-cara-rojo.png",
        ),
        "gorro": (
            "joker-del-gorro-rojo.png",
            "joker_del_gorro_azul.png",
            "joker_del_gorro_negro.png",
            "joker_del_gorro_verde.png",
        ),
    }

    JOKER_CLASS_FAMILIES: dict[str, str] = {
        "CorazonesPLUS": "alado",
        "DiamantesPLUS": "alado",
        "TrebolesPLUS": "alado",
        "EspadasPLUS": "alado",
        "ChipsterJoker": "truco",
        "RealezaJoker": "alado",
        "DonutJoker": "sonriente",
        "PalomitasJoker": "sonriente",
        "Ruleta": "alado",
        "BolaDeNieveJoker": "doble",
        "AsEnLaMangaJoker": "alado",
        "PimientoJoker": "sonriente",
        "VidrioFinoJoker": "sonriente",
        "RamenJoker": "sonriente",
        "HeladoJoker": "sonriente",
        "LetItRide": "misterioso",
        "AvariciaDesatada": "misterioso",
        "MaestroDelParJoker": "observador",
        "OjoDeAguilaJoker": "observador",
        "GranDobleJoker": "observador",
        "TriadaJoker": "observador",
        "CaminanteJoker": "observador",
        "PokerMaestroJoker": "observador",
        "PrismaJoker": "observador",
        "CasaLlenaJoker": "observador",
        "CoronaImperialJoker": "observador",
        "InversionistaJoker": "misterioso",
        "RecicladorJoker": "misterioso",
        "TarjetaDeCreditoJoker": "misterioso",
        "BrendaMadagascarJoker": "especial",
        "RepeticionJoker": "doble",
        "FavoritoJoker": "truco",
    }

    JOKER_ASSET_MAP: dict[str, str] = {
        "CorazonesPLUS": "joker-alado-rojo.png",
        "DiamantesPLUS": "joker-alado-azul.png",
        "TrebolesPLUS": "joker-alado-morado.png",
        "EspadasPLUS": "joker-alado-negro.png",
        "ChipsterJoker": "joker-truco-verde.png",
        "RealezaJoker": "joker-alado-amarillo.png",
        "DonutJoker": "joker-sonriente-rojo.png",
        "PalomitasJoker": "joker-sonriente-amarillo.png",
        "Ruleta": "joker-alado-azul.png",
        "BolaDeNieveJoker": "joker-doble-cara-rojo.png",
        "AsEnLaMangaJoker": "joker-alado-negro.png",
        "PimientoJoker": "joker-sonriente-negro.png",
        "VidrioFinoJoker": "joker-sonriente-verde.png",
        "RamenJoker": "joker-sonriente-azul.png",
        "HeladoJoker": "joker-sonriente-amarillo.png",
        "LetItRide": "joker-misterioso-azul.png",
        "AvariciaDesatada": "joker-misterioso-rojo.png",
        "MaestroDelParJoker": "joker-observador-azul.png",
        "OjoDeAguilaJoker": "joker-observador-naranja.png",
        "GranDobleJoker": "joker-observador-verde.png",
        "TriadaJoker": "joker-observador-gris.png",
        "CaminanteJoker": "joker-observador.png",
        "PokerMaestroJoker": "joker-observador-azul.png",
        "PrismaJoker": "joker-observador-verde.png",
        "CasaLlenaJoker": "joker-observador-gris.png",
        "CoronaImperialJoker": "joker-observador-naranja.png",
        "InversionistaJoker": "joker-misterioso-verde.png",
        "RecicladorJoker": "joker-misterioso-negro.png",
        "TarjetaDeCreditoJoker": "joker-misterioso-amarillo.png",
        "BrendaMadagascarJoker": "joker-Especial.png",
        "RepeticionJoker": "joker-doble-cara-azul.png",
        "FavoritoJoker": "joker-truco-azul.png",
    }

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

    def _family_assets(self, family: str | None) -> list[str]:
        if not family:
            return []
        family_files = self.JOKER_FAMILIES.get(family, ())
        return [
            (self.joker_dir / filename).as_posix()
            for filename in family_files
            if (self.joker_dir / filename).exists()
        ]

    def joker_asset_for(self, joker_class_name: str) -> str:
        """Devuelve un asset específico para cada joker como fuente de verdad."""
        exact_asset = self.JOKER_ASSET_MAP.get(joker_class_name)
        if exact_asset:
            asset_path = self.joker_dir / exact_asset
            if asset_path.exists():
                return asset_path.as_posix()

        family = self.JOKER_CLASS_FAMILIES.get(joker_class_name)
        family_assets = self._family_assets(family)
        if family_assets:
            return random.choice(family_assets)
        return self.random_joker_asset()

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
