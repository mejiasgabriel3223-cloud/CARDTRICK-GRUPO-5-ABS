"""Jerarquía abstracta y contenedor polimórfico de los Jokers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Iterable

from .entities import CardEntity, EntityCollection
from .rules import GameRules
from systems.assets import AssetResolver
from systems.joker_catalog import metadata_for


class Joker(ABC):
    """Contrato común de todos los comodines."""

    def __init__(self, name: str, probability: float = 1.0) -> None:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("la probabilidad debe estar entre 0 y 1")
        self.name = name
        self.probability = probability
        self.active = True
        self.description = "Efecto especial."
        self.rarity = "Común"
        self.shop_price = 0
        self.sell_price = 1
        self.asset_path = ""
        self._configure_metadata()

    def _configure_metadata(self) -> None:
        metadata = metadata_for(type(self).__name__)
        if self.name.startswith("Base ") or self.name == type(self).__name__:
            self.name = metadata.display_name
        self.description = metadata.description
        self.rarity = metadata.rarity
        self.shop_price = metadata.price
        self.sell_price = metadata.sell_price

        # Resolver el asset aquí mantiene el renderer libre de reglas de dominio.
        try:
            resolver = AssetResolver(_project_root_from_module())
            self.asset_path = resolver.joker_asset_for(type(self).__name__)
        except Exception:
            self.asset_path = ""

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        raise NotImplementedError

    def activate(self, cards: Iterable[CardEntity]) -> bool:
        if not self.active:
            return False
        if random.random() < self.probability:
            return self.apply(cards)
        return False

    def set_shop_price(self, price: int) -> None:
        self.shop_price = max(1, int(price))
        self.sell_price = max(1, self.shop_price // 2)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "rarity": self.rarity,
            "probability": self.probability,
            "active": self.active,
            "shop_price": self.shop_price,
            "sell_price": self.sell_price,
            "asset_path": self.asset_path,
            "uses_left": getattr(self, "uses_left", None),
            "current_mult": getattr(self, "current_mult", None),
        }


class FlatChipsJoker(Joker, ABC):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    amount: int = 20
    probability: float = 1.0

    def __post_init__(self) -> None:
        super().__init__("Base Fichas Plana", getattr(self, "probability", 1.0))

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
            applied = True
        return applied


@dataclass
class _FlatDataclassMixin(FlatChipsJoker):
    """Compatibilidad interna para dataclass children; no se instancia directamente."""

    amount: int = 20
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Base Fichas Plana", self.probability)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
            applied = True
        return applied


@dataclass
class MultiplierJoker(Joker, ABC):
    amount: float = 1.0
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Base Multiplicador", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.amount)
            applied = True
        return applied


@dataclass
class SuitBonusJoker(MultiplierJoker, ABC):
    target_suit: str = "♥"

    def __post_init__(self) -> None:
        super().__post_init__()
        names = {"♥": "Corazones", "♦": "Diamantes", "♣": "Tréboles", "♠": "Picas"}
        self.name = f"Especialista en {names.get(self.target_suit, self.target_suit)}"
        self._configure_metadata()

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        filtered = [c for c in cards if getattr(c, "suit", None) == self.target_suit]
        if not filtered:
            return False
        return MultiplierJoker.apply(self, filtered)


@dataclass
class FragileJoker(Joker, ABC):
    uses_left: int = 3
    probability: float = 1.0

    def __post_init__(self) -> None:
        if self.uses_left <= 0:
            raise ValueError("Los usos iniciales deben ser mayores a 0")
        Joker.__init__(self, "Base Frágil", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return self.uses_left > 0 and self.active

    def _consume_use(self) -> None:
        self.uses_left -= 1
        if self.uses_left <= 0:
            self.active = False


class FoodJokerMixin:
    """Marca polimórfica para identificar Jokers de comida."""


@dataclass
class CannibalJoker(Joker, ABC):
    mult_growth: float = 3.0
    current_mult: float = 0.0
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Base Caníbal", self.probability)

    def _consume_left_joker(self, jokers_pool: list[Joker]) -> Joker | None:
        try:
            index = jokers_pool.index(self)
        except ValueError:
            return None
        if index == 0:
            return None
        victim = jokers_pool[index - 1]
        if not victim.active:
            return None
        victim.active = False
        return victim

    @abstractmethod
    def apply_with_pool(self, cards: Iterable[CardEntity], jokers_pool: list[Joker]) -> bool:
        raise NotImplementedError

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False


@dataclass
class HandRequirementJoker(Joker, ABC):
    target_hand: str = "Pair"
    probability: float = 1.0

    def __post_init__(self) -> None:
        translations = {
            "High Card": "Carta Alta",
            "Pair": "Par",
            "Two Pair": "Doble Par",
            "Three of a Kind": "Trío",
            "Straight": "Escalera",
            "Flush": "Color",
            "Full House": "Full House",
            "Four of a Kind": "Póker",
            "Straight Flush": "Escalera de Color",
        }
        Joker.__init__(self, f"Especialista en {translations.get(self.target_hand, self.target_hand)}", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        cards_list = list(cards)
        if not cards_list:
            return False
        return GameRules().evaluate(cards_list).name == self.target_hand


@dataclass
class EconomyJoker(Joker, ABC):
    base_reward: int = 4
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Base Economía", self.probability)

    @abstractmethod
    def apply_economy_effect(self, current_money: int, game_state: dict | None = None) -> int:
        raise NotImplementedError

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False


@dataclass
class DiscardDependentJoker(Joker, ABC):
    discards_required: int = 1
    probability: float = 1.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Base de Descartes", self.probability)

    def on_discard(self, discarded_cards: Iterable[CardEntity]) -> bool:
        cards = list(discarded_cards)
        if not cards:
            return False
        if hasattr(self, "discards_tracked"):
            self.discards_tracked += 1
        return True


class RandomJokerPool:
    """Contenedor polimórfico que conoce el contexto necesario para cada Joker."""

    def __init__(self, jokers: Iterable[Joker] | None = None):
        self.jokers = jokers if isinstance(jokers, list) else list(jokers or [])

    def add(self, joker: Joker) -> None:
        self.jokers.append(joker)

    def activate_all(self, cards: EntityCollection[CardEntity], game_state: dict | None = None) -> list[str]:
        state = dict(game_state or {})
        activated: list[str] = []

        for joker in list(self.jokers):
            if not joker.active:
                continue

            # Los efectos económicos y de descarte se disparan en sus propios eventos.
            if hasattr(joker, "apply_economy_effect"):
                continue
            if hasattr(joker, "on_discard"):
                continue

            applied = False
            if hasattr(joker, "apply_with_pool"):
                applied = bool(joker.activate(cards)) if not hasattr(joker, "apply_with_pool") else False
                if not applied and random.random() < getattr(joker, "probability", 1.0):
                    applied = bool(joker.apply_with_pool(cards, self.jokers))
            elif hasattr(joker, "apply_with_money"):
                money = int(state.get("money", 0))
                if random.random() < getattr(joker, "probability", 1.0):
                    result = joker.apply_with_money(cards, money)
                    if isinstance(result, tuple):
                        applied, money_delta = result
                        if applied:
                            state["money"] = money + int(money_delta)
                    else:
                        applied = bool(result)
            elif hasattr(joker, "apply_with_stats"):
                if random.random() < getattr(joker, "probability", 1.0):
                    applied = bool(
                        joker.apply_with_stats(
                            cards,
                            state.get("current_poker_hand", ""),
                            state.get("most_played_poker_hand", ""),
                        )
                    )
            else:
                applied = joker.activate(cards)

            if applied:
                activated.append(joker.name)

        if "money" in state and game_state is not None:
            game_state["money"] = state["money"]

        # Los Jokers agotados o consumidos salen de la colección activa.
        self.jokers[:] = [joker for joker in self.jokers if joker.active]
        return activated

    def handle_discard(self, discarded_cards: Iterable[CardEntity]) -> list[str]:
        cards = list(discarded_cards)
        activated: list[str] = []
        for joker in self.jokers:
            handler = getattr(joker, "on_discard", None)
            if handler is not None and handler(cards):
                activated.append(joker.name)
        return activated

    def apply_economy_effects(self, current_money: int, game_state: dict | None = None) -> int:
        total_delta = 0
        state = game_state or {}
        for joker in self.jokers:
            if not joker.active:
                continue
            effect = getattr(joker, "apply_economy_effect", None)
            if effect is None:
                continue
            total_delta += int(effect(current_money, state))
        return total_delta

    def debt_limit(self) -> int:
        return max(
            [0]
            + [int(getattr(joker, "get_max_debt_limit")()) for joker in self.jokers if hasattr(joker, "get_max_debt_limit")]
        )

    def reorder(self, source_index: int, target_index: int) -> None:
        if not (0 <= source_index < len(self.jokers)):
            return
        target_index = max(0, min(target_index, len(self.jokers) - 1))
        joker = self.jokers.pop(source_index)
        self.jokers.insert(target_index, joker)

    def to_dict(self) -> list[dict]:
        return [joker.to_dict() for joker in self.jokers]


def _project_root_from_module():
    """Resuelve el root sin almacenar rutas dentro de las entidades."""
    return __import__("pathlib").Path(__file__).resolve().parent.parent
