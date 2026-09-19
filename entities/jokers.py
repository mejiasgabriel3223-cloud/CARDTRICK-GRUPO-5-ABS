"""Módulo de Comodines (Jokers) concretos e instanciables para el juego."""

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

# =====================================================================
# COMODINES DE PINTA / SUIT BONUS (4)
# =====================================================================

@dataclass
class CorazonesPLUS(SuitBonusJoker):
    """Comodín concreto especialista en cartas de Corazones."""
    target_suit: str = "♥"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)

@dataclass
class DiamantesPLUS(SuitBonusJoker):
    """Comodín concreto especialista en cartas de Diamantes."""
    target_suit: str = "♦"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)

@dataclass
class TrebolesPLUS(SuitBonusJoker):
    """Comodín concreto especialista en cartas de Tréboles."""
    target_suit: str = "♣"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)

@dataclass
class EspadasPLUS(SuitBonusJoker):
    """Comodín concreto especialista en cartas de Picas."""
    target_suit: str = "♠"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)

# =====================================================================
# COMODINES DE FICHAS PLANAS / FLAT CHIPS
# =====================================================================

@dataclass
class ChipsterJoker(FlatChipsJoker):
    """Suma un bono plano de +50 fichas a cada carta jugada."""
    amount: int = 50

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        return super().apply(cards)

@dataclass
class RealezaJoker(ChipsterJoker):
    """Otorga +30 fichas por cada figura (J, Q, K) presente en la mano jugada."""

    chips_per_figure: int = 30

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín de la Realeza"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False

        cards_list = list(cards)
        # Asumiendo que el valor/rango de J, Q, K es 11, 12, 13
        figures_count = sum(1 for card in cards_list if getattr(card, "rank", 0) in (11, 12, 13))

        if figures_count == 0:
            return False

        bonus = figures_count * self.chips_per_figure
        for card in cards_list:
            card.apply_bonus(score_delta=bonus)

        return True

@dataclass
class DonutJoker(FragileJoker, FoodJokerMixin):
    """Otorga +100 fichas planas y se consume tras 3 manos."""
    chips_amount: int = 100
    uses_left: int = 3

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Dona Glaseada"

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
    """Otorga +150 fichas planas y se consume tras 2 manos."""
    chips_amount: int = 150
    uses_left: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Caja de Palomitas"

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
    """Tiene un 25% de probabilidad de otorgar +120 fichas."""

    chips_amount: int = 120
    probability: float = 0.25

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Cofre de la Fortuna"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):  # Evalúa la probabilidad
            return False

        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.chips_amount)
            applied = True

        return applied

@dataclass
class BolaDeNieveJoker(ChipsterJoker):
    """Suma +10 fichas de forma permanente a su bono base cada vez que se juega una mano."""

    chips_amount: int = 20
    growth: int = 10

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Bola de Nieve"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False

        cards_list = list(cards)
        for card in cards_list:
            card.apply_bonus(score_delta=self.chips_amount)

        # Incrementa permanentemente para las siguientes manos
        self.chips_amount += self.growth
        return True

@dataclass
class AsEnLaMangaJoker(ChipsterJoker):
    """Otorga +50 fichas por cada As en la mano jugada."""

    chips_per_ace: int = 50

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "As en la Manga"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False

        cards_list = list(cards)
        # Asumiendo que el valor del As es 1 (o 14 según la lógica de tu mazo)
        aces_count = sum(1 for card in cards_list if getattr(card, "rank", 0) in (1, 14))

        if aces_count == 0:
            return False

        bonus = aces_count * self.chips_per_ace
        for card in cards_list:
            card.apply_bonus(score_delta=bonus)

        return True

@dataclass
class PimientoJoker(FragileJoker, FoodJokerMixin):
    """Otorga +200 fichas en una sola mano y luego se consume/destruye."""

    chips_amount: int = 200
    uses_left: int = 1

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Pimiento Picante"

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

# =====================================================================
# COMODINES MULTIPLICADORES
# =====================================================================

@dataclass
class VidrioFinoJoker(FragileJoker):
    """Otorga un gran bono pero solo dura 3 usos antes de romperse."""
    uses_left: int = 3

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
    """Otorga +9.0 al multiplicador y se consume tras 4 manos."""
    multiplier_amount: float = 9.0
    uses_left: int = 4

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Tazón de Ramen"

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
    """Otorga +15.0 al multiplicador pero se consume en 2 manos."""
    multiplier_amount: float = 15.0
    uses_left: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Helado Derretido"

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
    """Otorga +15.0 al multiplicador, pero exige un costo de $2 por mano jugada."""

    multiplier_amount: float = 15.0
    hand_cost: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Let It Ride"

    def apply_with_money(self, cards: Iterable[CardEntity], current_money: int) -> tuple[bool, int]:
        """Aplica el multiplicador si el jugador tiene suficiente dinero para pagar la mano.
        
        Devuelve una tupla (éxito, cambio_en_dinero).
        """
        if current_money < self.hand_cost or not self.active:
            return False, 0

        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.multiplier_amount)
            applied = True

        if applied:
            return True, -self.hand_cost  # Aplica el bono y descuenta $2 de la reserva

        return False, 0

@dataclass
class AvariciaDesatada(MultiplierJoker):
    """Otorga +1.0 al multiplicador por cada $5 en la reserva del jugador.
    
    Evalúa la cantidad de dinero actual para calcular el bono de multiplicador.
    """

    mult_per_tier: float = 1.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Avaricia Desatada"

    def apply_with_money(self, cards: Iterable[CardEntity], current_money: int) -> bool:
        """Aplica el multiplicador calculado a partir de la reserva de dinero."""
        if current_money < 5 or not self.active:
            return False

        tiers = current_money // 5
        total_mult = tiers * self.mult_per_tier

        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=total_mult)
            applied = True

        return applied

# =====================================================================
# COMODINES DE MANO ESPECÍFICA / HAND REQUIREMENT
# =====================================================================

@dataclass
class MaestroDelParJoker(HandRequirementJoker):
    """Otorga +2.0 al multiplicador únicamente si la mano es un Par."""
    target_hand: str = "Pair"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=2.0)
        return True

@dataclass
class OjoDeAguilaJoker(HandRequirementJoker):
    """Otorga +1.5 al multiplicador si la mano jugada es una Carta Alta."""
    target_hand: str = "High Card"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=1.5)
        return True

@dataclass
class GranDobleJoker(HandRequirementJoker):
    """Otorga +3.0 al multiplicador si la mano jugada es Doble Par."""
    target_hand: str = "Two Pair"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=3.0)
        return True

@dataclass
class TriadaJoker(HandRequirementJoker):
    """Otorga +4.0 al multiplicador si la mano jugada es un Trío."""
    target_hand: str = "Three of a Kind"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=4.0)
        return True

@dataclass
class CaminanteJoker(HandRequirementJoker):
    """Otorga +5.0 al multiplicador si la mano jugada es una Escalera."""
    target_hand: str = "Straight"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=5.0)
        return True

@dataclass
class PokerMaestroJoker(HandRequirementJoker):
    """Otorga +8.0 al multiplicador si la mano jugada es un Póker."""
    target_hand: str = "Four of a Kind"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=8.0)
        return True

@dataclass
class PrismaJoker(HandRequirementJoker):
    """Otorga +5.0 al multiplicador si la mano jugada es un Color (Flush)."""
    target_hand: str = "Flush"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=5.0)
        return True

@dataclass
class CasaLlenaJoker(HandRequirementJoker):
    """Otorga +6.0 al multiplicador si la mano jugada es un Full House."""
    target_hand: str = "Full House"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=6.0)
        return True

@dataclass
class CoronaImperialJoker(HandRequirementJoker):
    """Otorga +12.0 al multiplicador si la mano jugada es una Escalera de Color / Escalera Real."""
    target_hand: str = "Straight Flush"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not super().apply(cards):
            return False
        
        for card in cards:
            card.apply_bonus(multiplier_delta=12.0)
        return True

# =====================================================================
# COMODINES DE ECONOMÍA / ECONOMY JOKERS
# =====================================================================

@dataclass
class InversionistaJoker(EconomyJoker):
    """Calcula ganancias extra basadas en el dinero actual."""
    
    def apply_economy_effect(self, current_money: int) -> int:
        return current_money // 5  # Interés: +1 moneda por cada 5 guardadas

@dataclass
class RecicladorJoker(DiscardDependentJoker):
    """Otorga $2 al final de la ronda por cada 5 descartes acumulados."""

    discard_threshold: int = 5
    reward_per_threshold: int = 2

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Comodín Reciclador"

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        # No modifica las cartas durante la evaluación de la mano
        return False

    def apply_economy_effect(self, current_money: int) -> int:
        """Calcula el bono económico generado por los descartes acumulados."""
        payouts = self.discards_tracked // self.discard_threshold
        return payouts * self.reward_per_threshold

@dataclass
class TarjetaDeCreditoJoker(Joker):
    """Permite al jugador endeudarse hasta -$20 en la reserva de dinero."""

    credit_limit: int = 20

    def __post_init__(self) -> None:
        super().__post_init__("Tarjeta de Crédito", 1.0)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        # No afecta la puntuación de las cartas durante la evaluación de la mano
        return False

    def get_max_debt_limit(self) -> int:
        """Devuelve el límite de crédito permitido cuando este comodín está activo."""
        return self.credit_limit if self.active else 0

# =====================================================================
# COMODINES ASESINOS
# =====================================================================

@dataclass
class BrendaMadagascarJoker(CannibalJoker):
    """Devora al comodín de su izquierda. Aumenta su multiplicador en +4.0, o el doble (+8.0) si devora Comida."""

    mult_growth: float = 4.0

    def __post_init__(self) -> None:
        super().__post_init__()
        self.name = "Brenda Madagascar"

    def apply_with_pool(self, cards: Iterable[CardEntity], jokers_pool: list[Joker]) -> bool:
        victim = self._consume_left_joker(jokers_pool)

        if victim is None:
            return False  # No había nada que comer a la izquierda

        # Solo Brenda verifica si la víctima es comida
        is_food = isinstance(victim, FoodJokerMixin)
        growth = self.mult_growth * 2.0 if is_food else self.mult_growth

        self.current_mult += growth

        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.current_mult)
            applied = True

        return applied

# =====================================================================
# COMODINES VARIOS
# =====================================================================

@dataclass
class RepeticionJoker(Joker):
    """Re-evalúa y aplica una segunda vez los bonos acumulados a las cartas jugadas."""

    def __post_init__(self) -> None:
        super().__post_init__("Comodín Repetición", 1.0)

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        if not self.active:
            return False

        cards_list = list(cards)
        if not cards_list:
            return False

        # Re-aplica el bono base/acumulado que ya tengan asignado las cartas
        for card in cards_list:
            card.apply_bonus(
                score_delta=getattr(card, "bonus_chips", 0),
                multiplier_delta=getattr(card, "bonus_mult", 0.0)
            )

        return True

@dataclass
class FavoritoJoker(Joker):
    """Otorga +20 fichas y +3.0 de multiplicador si la mano jugada es la más jugada de la partida."""

    bonus_chips: int = 20
    bonus_mult: float = 3.0

    def __post_init__(self) -> None:
        super().__post_init__("Comodín Favorito", 1.0)

    def apply_with_stats(
        self, 
        cards: Iterable[CardEntity], 
        current_poker_hand: str, 
        most_played_poker_hand: str
    ) -> bool:
        """Verifica si la mano actual coincide con la mano más jugada históricamente."""
        if not self.active or current_poker_hand != most_played_poker_hand:
            return False

        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.bonus_chips, multiplier_delta=self.bonus_mult)
            applied = True

        return applied

# =====================================================================
# REGISTRO GLOBAL DE COMODINES (PARA LA FÁBRICA / TIENDA)
# =====================================================================

# Lista con las clases concretas para que la fábrica o tienda las elija fácilmente
ALL_JOKERS = [
    # Comodines de Pinta (4)
    CorazonesPLUS,
    DiamantesPLUS,
    TrebolesPLUS,
    EspadasPLUS,
    # Comodines de Fichas Planas (8)
    ChipsterJoker,
    RealezaJoker,
    DonutJoker,
    PalomitasJoker,
    Ruleta,
    BolaDeNieveJoker,
    AsEnLaMangaJoker,
    PimientoJoker,
    # Comodines Multiplicadores (5)
    VidrioFinoJoker,
    RamenJoker,
    HeladoJoker,
    LetItRide,
    AvariciaDesatada,
    # Comodines de Mano Específica (9)
    MaestroDelParJoker,
    OjoDeAguilaJoker,
    GranDobleJoker,
    TriadaJoker,
    CaminanteJoker,
    PokerMaestroJoker,
    PrismaJoker,
    CasaLlenaJoker,
    CoronaImperialJoker,
    # Comodines de Economía (3)
    InversionistaJoker,
    RecicladorJoker,
    TarjetaDeCreditoJoker,
    # Comodines Asesinos (1)
    BrendaMadagascarJoker,
    # Comodines Varios (2)
    RepeticionJoker,
    FavoritoJoker,
]