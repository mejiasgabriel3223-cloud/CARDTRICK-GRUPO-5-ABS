"""
Boss blind domain model for the card game.

This module keeps all boss-specific rules outside the Joker entity layer.
The base class defines the common contract and concrete subclasses override
only the behavior that belongs to their boss rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Any, Iterable


BASE_ANTE_TARGETS = {
    1: 300,
    2: 800,
    3: 2000,
    4: 5000,
    5: 11000,
    6: 20000,
    7: 35000,
    8: 50000,
}


@dataclass(frozen=True)
class BossValidationResult:
    """Result returned when a boss validates a proposed played hand."""

    allowed: bool
    message: str = ""


@dataclass(frozen=True)
class BossPostPlayResult:
    """Result returned after a hand has been successfully played."""

    discard_count: int = 0


class BossBlind(ABC):
    """Abstract base class for every boss blind.

    Bosses expose a common interface so the game state does not need to know
    which concrete boss is active. This is the polymorphic boundary between
    the game flow and individual boss rules.
    """

    def __init__(
        self,
        name: str,
        description: str,
        effect_id: str,
        score_multiplier: float = 2.0,
    ) -> None:
        self.name = name
        self.description = description
        self.effect_id = effect_id
        self.score_multiplier = score_multiplier

    def calculate_target_score(
        self,
        ante: int,
        custom_multiplier: float = 1.0,
    ) -> int:
        """Return the score target produced by this boss for an Ante."""
        base_score = BASE_ANTE_TARGETS.get(
            ante,
            int(50000 * (1.5 ** (ante - 8))),
        )
        return int(base_score * self.score_multiplier * custom_multiplier)

    def validate_play(
        self,
        cards: Iterable[Any],
        game_state: dict[str, Any],
    ) -> BossValidationResult:
        """Validate a proposed hand before it is scored.

        Bosses that do not restrict card selection accept the hand unchanged.
        """
        del cards, game_state
        return BossValidationResult(True)

    def after_hand_played(
        self,
        cards: Iterable[Any],
        game_state: dict[str, Any],
    ) -> BossPostPlayResult:
        """Return effects that must happen immediately after a played hand."""
        del cards, game_state
        return BossPostPlayResult()

    def get_max_play_size(self, default_size: int) -> int:
        """Return the maximum number of cards allowed in one played hand."""
        return default_size

    def to_dict(self) -> dict[str, Any]:
        """Return UI-safe boss metadata without exposing implementation data."""
        return {
            "name": self.name,
            "description": self.description,
            "effect_id": self.effect_id,
            "multiplier": self.score_multiplier,
        }

    @abstractmethod
    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Apply persistent boss state when the boss becomes active."""
        raise NotImplementedError


class HookBoss(BossBlind):
    """The Hook: discard two random cards after every played hand."""

    def __init__(self) -> None:
        super().__init__(
            name="El Gancho",
            description="Después de jugar una mano, descarta 2 cartas al azar.",
            effect_id="hook",
            score_multiplier=2.0,
        )

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Publish the post-play discard rule to the active game state."""
        game_state["boss_post_play_discard_count"] = 2
        return game_state

    def after_hand_played(
        self,
        cards: Iterable[Any],
        game_state: dict[str, Any],
    ) -> BossPostPlayResult:
        """Request two random cards from the remaining hand to be discarded."""
        del cards, game_state
        return BossPostPlayResult(discard_count=2)


class WallBoss(BossBlind):
    """The Wall: substantially larger score target."""

    def __init__(self) -> None:
        super().__init__(
            name="La Muralla",
            description="La ciega exige un objetivo de fichas mucho mayor de lo normal.",
            effect_id="wall",
            score_multiplier=4.0,
        )

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Mark the boss as target-score driven."""
        game_state["boss_score_multiplier"] = self.score_multiplier
        return game_state


class NeedleBoss(BossBlind):
    """The Needle: the player gets only one hand for the blind."""

    def __init__(self) -> None:
        super().__init__(
            name="La Aguja",
            description="Solo tienes 1 mano disponible en esta ciega.",
            effect_id="needle",
            score_multiplier=2.0,
        )

    def calculate_target_score(self, ante: int, custom_multiplier: float = 0.6) -> int:
        """Keep the original project's reduced Needle target behavior."""
        return super().calculate_target_score(ante, custom_multiplier)

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Set the hand counter to one when the boss starts."""
        game_state["hands"] = 1
        return game_state


class PsychicBoss(BossBlind):
    """Four-card boss variant requested for this project."""

    def __init__(self) -> None:
        super().__init__(
            name="El Psíquico",
            description="Solo puedes jugar manos de hasta 4 cartas.",
            effect_id="psychic",
            score_multiplier=2.0,
        )

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Publish the four-card hand limit."""
        game_state["max_play_size"] = 4
        return game_state

    def get_max_play_size(self, default_size: int) -> int:
        """Reduce the normal maximum played-hand size to four cards."""
        return min(default_size, 4)


class PillarBoss(BossBlind):
    """The Pillar: cards played in the previous blind cannot be played again."""

    def __init__(self) -> None:
        super().__init__(
            name="El Pilar",
            description="No puedes jugar cartas que hayas jugado en la ciega anterior.",
            effect_id="pillar",
            score_multiplier=2.0,
        )

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Load the previous blind's played card codes into the active rule."""
        game_state["previous_blind_played_card_codes"] = set(
            game_state.get("previous_blind_played_card_codes", set())
        )
        return game_state

    def validate_play(
        self,
        cards: Iterable[Any],
        game_state: dict[str, Any],
    ) -> BossValidationResult:
        """Reject any hand containing a card played during the previous blind."""
        banned_codes = set(game_state.get("previous_blind_played_card_codes", set()))
        conflicting_codes = [card.code for card in cards if card.code in banned_codes]
        if conflicting_codes:
            return BossValidationResult(
                False,
                "El Pilar prohíbe las cartas jugadas en la ciega anterior.",
            )
        return BossValidationResult(True)


class SuitRestrictionBoss(BossBlind):
    """Base class for bosses that forbid one card suit."""

    restricted_suit = ""
    suit_label = ""

    def __init__(self, name: str, effect_id: str) -> None:
        super().__init__(
            name=name,
            description=f"No puedes jugar cartas de {self.suit_label.lower()}.",
            effect_id=effect_id,
            score_multiplier=2.0,
        )

    def apply_effect(self, game_state: dict[str, Any]) -> dict[str, Any]:
        """Publish the restricted suit to the active game state."""
        game_state["restricted_suit"] = self.restricted_suit
        return game_state

    def validate_play(
        self,
        cards: Iterable[Any],
        game_state: dict[str, Any],
    ) -> BossValidationResult:
        """Reject a hand containing a card from the restricted suit."""
        del game_state
        if any(card.suit == self.restricted_suit for card in cards):
            return BossValidationResult(
                False,
                f"{self.name}: no puedes jugar cartas de {self.suit_label.lower()}.",
            )
        return BossValidationResult(True)


class HeartBoss(SuitRestrictionBoss):
    """The Head: hearts are forbidden."""

    def __init__(self) -> None:
        self.restricted_suit = "♥"
        self.suit_label = "corazones"
        super().__init__(name="La Cabeza", effect_id="hearts")


class DiamondBoss(SuitRestrictionBoss):
    """The Window: diamonds are forbidden."""

    def __init__(self) -> None:
        self.restricted_suit = "♦"
        self.suit_label = "diamantes"
        super().__init__(name="La Ventana", effect_id="diamonds")


class ClubBoss(SuitRestrictionBoss):
    """The Club: clubs are forbidden."""

    def __init__(self) -> None:
        self.restricted_suit = "♣"
        self.suit_label = "tréboles"
        super().__init__(name="El Trébol", effect_id="clubs")


class SpadeBoss(SuitRestrictionBoss):
    """The Goad: spades are forbidden."""

    def __init__(self) -> None:
        self.restricted_suit = "♠"
        self.suit_label = "picas"
        super().__init__(name="El Aguijón", effect_id="spades")


ALLOWED_BOSS_CLASSES = [
    HookBoss,
    WallBoss,
    NeedleBoss,
    PsychicBoss,
    PillarBoss,
    HeartBoss,
    DiamondBoss,
    ClubBoss,
    SpadeBoss,
]


def get_random_boss_instance(seen_boss_ids: set[str]) -> BossBlind:
    """Return an unseen boss instance and record its effect identifier."""
    available_classes = [
        boss_class
        for boss_class in ALLOWED_BOSS_CLASSES
        if boss_class().effect_id not in seen_boss_ids
    ]

    if not available_classes:
        seen_boss_ids.clear()
        available_classes = list(ALLOWED_BOSS_CLASSES)

    chosen_class = random.choice(available_classes)
    instance = chosen_class()
    seen_boss_ids.add(instance.effect_id)
    return instance
