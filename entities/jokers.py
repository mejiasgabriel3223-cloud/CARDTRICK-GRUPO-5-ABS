"""Jokers concretos e instanciables del juego."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .entities import CardEntity
from .jokers_base import (
    CannibalJoker,
    DiscardDependentJoker,
    EconomyJoker,
    FlatChipsJoker,
    FoodJokerMixin,
    FragileJoker,
    HandRequirementJoker,
    Joker,
    MultiplierJoker,
    RandomJokerPool,
    SuitBonusJoker,
)


@dataclass
class CorazonesPLUS(SuitBonusJoker):
    target_suit: str = "♥"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)


@dataclass
class DiamantesPLUS(SuitBonusJoker):
    target_suit: str = "♦"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)


@dataclass
class TrebolesPLUS(SuitBonusJoker):
    target_suit: str = "♣"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)


@dataclass
class EspadasPLUS(SuitBonusJoker):
    target_suit: str = "♠"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)


@dataclass
class ChipsterJoker(FlatChipsJoker):
    amount: int = 50
    probability: float = 1.0

    def __post_init__(self) -> None:
        super().__post_init__()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)


@dataclass
class RealezaJoker(ChipsterJoker):
    chips_per_figure: int = 30

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín de la Realeza"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        cards_list = list(cards)
        if not cards_list:
            return False
        super().apply(cards_list)
        figures_count = sum(1 for card in cards_list if str(card.rank) in {"J", "Q", "K"})
        if figures_count:
            bonus = figures_count * self.chips_per_figure
            for card in cards_list:
                card.apply_bonus(score_delta=bonus)
        return True


@dataclass
class DonutJoker(FragileJoker, FoodJokerMixin):
    chips_amount: int = 100
    uses_left: int = 3

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Dona Glaseada"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.chips_amount)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class PalomitasJoker(FragileJoker, FoodJokerMixin):
    chips_amount: int = 150
    uses_left: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Caja de Palomitas"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.chips_amount)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class Ruleta(ChipsterJoker):
    chips_amount: int = 120
    probability: float = 0.25

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Cofre de la Fortuna"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.chips_amount)
            applied = True
        return applied


@dataclass
class BolaDeNieveJoker(ChipsterJoker):
    chips_amount: int = 20
    growth: int = 10
    amount: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Bola de Nieve"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        cards_list = list(cards)
        if not cards_list:
            return False
        for card in cards_list:
            card.apply_bonus(score_delta=self.chips_amount)
        self.chips_amount += self.growth
        return True


@dataclass
class AsEnLaMangaJoker(ChipsterJoker):
    chips_per_ace: int = 50

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "As en la Manga"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        cards_list = list(cards)
        aces_count = sum(1 for card in cards_list if str(card.rank) == "A")
        if aces_count == 0:
            return False
        bonus = aces_count * self.chips_per_ace
        for card in cards_list:
            card.apply_bonus(score_delta=bonus)
        return True


@dataclass
class PimientoJoker(FragileJoker, FoodJokerMixin):
    chips_amount: int = 200
    uses_left: int = 1

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Pimiento Picante"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.chips_amount)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class VidrioFinoJoker(FragileJoker):
    uses_left: int = 3

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Vidrio Fino"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=3.0)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class RamenJoker(FragileJoker, FoodJokerMixin):
    multiplier_amount: float = 9.0
    uses_left: int = 4

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Tazón de Ramen"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.multiplier_amount)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class HeladoJoker(FragileJoker, FoodJokerMixin):
    multiplier_amount: float = 15.0
    uses_left: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Helado Derretido"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.multiplier_amount)
            applied = True
        if applied:
            self._consume_use()
        return applied


@dataclass
class LetItRide(MultiplierJoker):
    multiplier_amount: float = 15.0
    hand_cost: int = 2
    amount: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Let It Ride"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False

    def apply_with_money(self, cards: Iterable[CardEntity], current_money: int) -> tuple[bool, int]:
        if current_money < self.hand_cost or not self.active:
            return False, 0
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.multiplier_amount)
            applied = True
        return (applied, -self.hand_cost if applied else 0)


@dataclass
class AvariciaDesatada(MultiplierJoker):
    mult_per_tier: float = 1.0
    amount: float = 0.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Avaricia Desatada"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False

    def apply_with_money(self, cards: Iterable[CardEntity], current_money: int) -> bool:
        if current_money < 5 or not self.active:
            return False
        total_mult = (current_money // 5) * self.mult_per_tier
        for card in cards:
            card.apply_bonus(multiplier_delta=total_mult)
        return True


@dataclass
class MaestroDelParJoker(HandRequirementJoker):
    target_hand: str = "Pair"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=2.0)
        return True


@dataclass
class OjoDeAguilaJoker(HandRequirementJoker):
    target_hand: str = "High Card"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=1.5)
        return True


@dataclass
class GranDobleJoker(HandRequirementJoker):
    target_hand: str = "Two Pair"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=3.0)
        return True


@dataclass
class TriadaJoker(HandRequirementJoker):
    target_hand: str = "Three of a Kind"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=4.0)
        return True


@dataclass
class CaminanteJoker(HandRequirementJoker):
    target_hand: str = "Straight"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=5.0)
        return True


@dataclass
class PokerMaestroJoker(HandRequirementJoker):
    target_hand: str = "Four of a Kind"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=8.0)
        return True


@dataclass
class PrismaJoker(HandRequirementJoker):
    target_hand: str = "Flush"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=5.0)
        return True


@dataclass
class CasaLlenaJoker(HandRequirementJoker):
    target_hand: str = "Full House"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=6.0)
        return True


@dataclass
class CoronaImperialJoker(HandRequirementJoker):
    target_hand: str = "Straight Flush"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        for card in cards:
            card.apply_bonus(multiplier_delta=12.0)
        return True


@dataclass
class InversionistaJoker(EconomyJoker):
    def apply_economy_effect(self, current_money: int, game_state: dict | None = None) -> int:
        del game_state
        return current_money // 5


@dataclass
class RecicladorJoker(DiscardDependentJoker):
    discard_threshold: int = 5
    reward_per_threshold: int = 2
    discards_tracked: int = 0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Reciclador"
        self._configure_metadata()

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False

    def on_discard(self, discarded_cards: Iterable[CardEntity]) -> bool:
        cards = list(discarded_cards)
        if not cards:
            return False
        self.discards_tracked += 1
        return True

    def apply_economy_effect(self, current_money: int, game_state: dict | None = None) -> int:
        del current_money, game_state
        return (self.discards_tracked // self.discard_threshold) * self.reward_per_threshold


@dataclass
class TarjetaDeCreditoJoker(Joker):
    credit_limit: int = 20

    def __post_init__(self) -> None:
        Joker.__init__(self, "Tarjeta de Crédito", 1.0)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False

    def get_max_debt_limit(self) -> int:
        return self.credit_limit if self.active else 0


@dataclass
class BrendaMadagascarJoker(CannibalJoker):
    mult_growth: float = 4.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Brenda Madagascar"
        self._configure_metadata()

    def apply_with_pool(self, cards: Iterable[CardEntity], jokers_pool: list[Joker]) -> bool:
        victim = self._consume_left_joker(jokers_pool)
        if victim is None:
            return False
        growth = self.mult_growth * (2.0 if isinstance(victim, FoodJokerMixin) else 1.0)
        self.current_mult += growth
        for card in cards:
            card.apply_bonus(multiplier_delta=self.current_mult)
        return True


@dataclass
class RepeticionJoker(Joker):
    def __post_init__(self) -> None:
        Joker.__init__(self, "Comodín Repetición", 1.0)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        cards_list = list(cards)
        if not cards_list or not self.active:
            return False
        for card in cards_list:
            card.apply_bonus(
                score_delta=int(getattr(card, "bonus_chips", 0)),
                multiplier_delta=float(getattr(card, "bonus_mult", 0.0)),
            )
        return True


@dataclass
class FavoritoJoker(Joker):
    bonus_chips: int = 20
    bonus_mult: float = 3.0

    def __post_init__(self) -> None:
        Joker.__init__(self, "Comodín Favorito", 1.0)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        del cards
        return False

    def apply_with_stats(self, cards: Iterable[CardEntity], current_poker_hand: str, most_played_poker_hand: str) -> bool:
        if not self.active or not current_poker_hand or current_poker_hand != most_played_poker_hand:
            return False
        for card in cards:
            card.apply_bonus(score_delta=self.bonus_chips, multiplier_delta=self.bonus_mult)
        return True


ALL_JOKERS = [
    CorazonesPLUS,
    DiamantesPLUS,
    TrebolesPLUS,
    EspadasPLUS,
    ChipsterJoker,
    RealezaJoker,
    DonutJoker,
    PalomitasJoker,
    Ruleta,
    BolaDeNieveJoker,
    AsEnLaMangaJoker,
    PimientoJoker,
    VidrioFinoJoker,
    RamenJoker,
    HeladoJoker,
    LetItRide,
    AvariciaDesatada,
    MaestroDelParJoker,
    OjoDeAguilaJoker,
    GranDobleJoker,
    TriadaJoker,
    CaminanteJoker,
    PokerMaestroJoker,
    PrismaJoker,
    CasaLlenaJoker,
    CoronaImperialJoker,
    InversionistaJoker,
    RecicladorJoker,
    TarjetaDeCreditoJoker,
    BrendaMadagascarJoker,
    RepeticionJoker,
    FavoritoJoker,
]
