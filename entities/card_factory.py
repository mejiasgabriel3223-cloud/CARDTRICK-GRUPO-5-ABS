"""Create random card entities and connect them to existing visual assets."""

from __future__ import annotations

import random
import sys
from pathlib import Path
from uuid import uuid4

import pygame

try:
    from .entities import CardEntity, RANK_VALUES
except ImportError:
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from entities.entities import CardEntity, RANK_VALUES


class CardFactory:
    """Build card entities without owning or managing the deck itself.

    The factory has one responsibility: translate logical card data into a
    ``CardEntity`` that already contains its visual metadata. It can create
    single cards or batches, and because every creation is independent,
    duplicate rank/suit combinations are naturally allowed.
    """

    RANKS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
    SUITS = ("C", "D", "H", "S")
    SUIT_SYMBOLS = {"C": "♣", "D": "♦", "H": "♥", "S": "♠"}
    SKINS = {"dark", "light"}

    def __init__(
        self,
        asset_root: str | Path = ".",
        card_size: tuple[int, int] = (90, 130),
        skin: str = "dark",
    ) -> None:
        """Configure the asset root, the active card skin and the default size of generated Rects."""
        self.asset_root = Path(asset_root)
        self.card_size = card_size
        self.skin = self._normalize_skin(skin)

    def set_skin(self, skin: str) -> None:
        """Switch the active skin used when resolving each card image."""
        self.skin = self._normalize_skin(skin)

    @staticmethod
    def _normalize_skin(skin: str) -> str:
        value = str(skin or "dark").strip().lower()
        if value in {"light", "blanca", "white", "clara"}:
            return "light"
        return "dark"

    def create_random_card(self, x: int = 0, y: int = 0) -> CardEntity:
        """Create one card by randomly choosing a rank and a suit."""
        # Each choice is independent, so repeated cards are possible.
        rank = random.choice(self.RANKS)
        suit = random.choice(self.SUITS)
        return self.create_card(rank, suit, x, y)

    def create_card(self, rank: str, suit: str, x: int = 0, y: int = 0) -> CardEntity:
        """Create one validated card with its Rect and asset path configured."""
        if rank not in self.RANKS or suit not in self.SUITS:
            raise ValueError("Invalid card rank or suit")

        # The factory owns Rect creation, while the Renderer remains responsible for drawing.
        rect = pygame.Rect(x, y, *self.card_size)
        asset_path = self._resolve_asset(rank, suit)
        return CardEntity(
            rank=rank,
            suit=self.SUIT_SYMBOLS[suit],
            score=self._base_score(rank),
            multiplier=1.0,
            asset_path=str(asset_path),
            rect=rect,
            _entity_id=uuid4().hex,
        )

    def create_random_collection(self, amount: int) -> list[CardEntity]:
        """Create ``amount`` independent random cards in a standard Python list."""
        if amount < 0:
            raise ValueError("amount cannot be negative")
        return [self.create_random_card() for _ in range(amount)]

    def _resolve_asset(self, rank: str, suit: str) -> Path:
        """Resolve a card image path using the repository's asset naming and selected skin."""
        asset_suit = "P" if suit == "S" else suit
        normalized_rank = str(rank).strip()
        rank_aliases = []
        if normalized_rank.upper() in {"A", "1", "14"}:
            rank_aliases = ["1", "14", "A"]
        elif normalized_rank.upper() in {"J", "11"}:
            rank_aliases = ["11", "J"]
        elif normalized_rank.upper() in {"Q", "12"}:
            rank_aliases = ["12", "Q"]
        elif normalized_rank.upper() in {"K", "13"}:
            rank_aliases = ["13", "K"]
        else:
            rank_aliases = [normalized_rank]

        preferred_skin = self.skin
        alternative_skin = "light" if preferred_skin == "dark" else "dark"
        preferred_dir = self.asset_root / "assets(beta)" / "cards" / "cards" / preferred_skin
        alternative_dir = self.asset_root / "assets(beta)" / "cards" / "cards" / alternative_skin

        candidates = []
        for rank_alias in rank_aliases:
            candidates.extend([
                preferred_dir / f"{rank_alias}-{asset_suit}.png",
                preferred_dir / f"{rank_alias}{asset_suit}.png",
                preferred_dir / f"{rank_alias}-{asset_suit}.PNG",
                preferred_dir / f"{rank_alias}{asset_suit}.PNG",
            ])
            candidates.extend([
                alternative_dir / f"{rank_alias}-{asset_suit}.png",
                alternative_dir / f"{rank_alias}{asset_suit}.png",
                alternative_dir / f"{rank_alias}-{asset_suit}.PNG",
                alternative_dir / f"{rank_alias}{asset_suit}.PNG",
            ])

        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve().as_posix()
        return candidates[0].resolve().as_posix()

    @staticmethod
    def _base_score(rank: str) -> int:
        """Return the default numeric score assigned from the card rank."""
        return RANK_VALUES[rank]


if __name__ == "__main__":
    factory = CardFactory(asset_root=Path(__file__).resolve().parent.parent, skin="dark")
    for rank, suit in [("A", "H"), ("10", "D"), ("2", "C")]:
        card = factory.create_card(rank, suit)
        print(f"{rank}-{suit} -> {card.asset_path}")
