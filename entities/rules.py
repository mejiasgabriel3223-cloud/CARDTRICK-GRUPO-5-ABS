"""Reglas globales del juego, evaluación de manos y cálculo del puntaje final."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Sequence

from .entities import CardEntity, RANK_VALUES


@dataclass(frozen=True)
class HandResult:
    """Almacena el resultado inmutable producido por la evaluación de una mano."""

    name: str
    score: int
    multiplier: float

    @property
    def total(self) -> int:
        """Devuelve el puntaje final obtenido al multiplicar las fichas (score) por el multiplicador."""
        return int(self.score * self.multiplier)


class GameRules:
    """Centraliza los valores globales de fichas/multiplicadores y la evaluación de manos de póker.

    ``score`` y ``multiplier`` actúan como los valores base compartidos descritos por el
    diseño del proyecto. Las cartas conservan sus propios modificadores mutables, por lo que los
    Comodines pueden cambiar cartas individuales antes de que esta clase calcule el resultado final.
    """

    HAND_VALUES = {
        "High Card": (5, 1.0),
        "Pair": (10, 2.0),
        "Two Pair": (20, 2.0),
        "Three of a Kind": (30, 3.0),
        "Straight": (40, 4.0),
        "Flush": (45, 4.0),
        "Full House": (60, 6.0),
        "Four of a Kind": (80, 8.0),
        "Straight Flush": (100, 10.0),
    }

    def __init__(self, score: int = 0, multiplier: float = 1.0) -> None:
        """Crea el objeto de reglas con un puntaje y multiplicador base globales."""
        self.score = int(score)
        self.multiplier = float(multiplier)

    def reset(self, score: int = 0, multiplier: float = 1.0) -> None:
        """Reemplaza el puntaje y multiplicador globales con nuevos valores base."""
        self.score = int(score)
        self.multiplier = float(multiplier)

    def evaluate(self, cards: Sequence[CardEntity]) -> HandResult:
        """Identifica una mano y combina los valores globales con los modificadores por carta.

        El método espera entre 1 y 5 cartas jugadas. El ``HandResult`` devuelto
        contiene el tipo de mano, las fichas calculadas, el multiplicador y una
        propiedad ``total`` que representa el producto final.
        """
        if not 1 <= len(cards) <= 5:
            raise ValueError("Una mano jugada debe contener entre 1 y 5 cartas")

        # Convierte los rangos lógicos en valores numéricos para pruebas de frecuencia y escaleras.
        ranks = [self._rank_value(card.rank) for card in cards]
        suits = [card.suit for card in cards]
        counts = Counter(ranks)
        unique = sorted(set(ranks))
        flush = len(set(suits)) == 1 and len(cards) == 5
        straight = self._is_straight(unique) and len(cards) == 5

        if straight and flush:
            name = "Straight Flush"
        elif 4 in counts.values() and len(cards) == 5:
            name = "Four of a Kind"
        elif sorted(counts.values()) == [2, 3] and len(cards) == 5:
            name = "Full House"
        elif flush:
            name = "Flush"
        elif straight:
            name = "Straight"
        elif 3 in counts.values():
            name = "Three of a Kind"
        elif list(counts.values()).count(2) == 2:
            name = "Two Pair"
        elif 2 in counts.values():
            name = "Pair"
        else:
            name = "High Card"

        base_score, base_multiplier = self.HAND_VALUES[name]
        # La suma recursiva mantiene los cambios de fichas por carta separados de las reglas globales.
        card_score = self._sum_card_score_recursive(cards)
        # El multiplicador por defecto de una carta es 1.0, por lo que solo se suma la porción añadida.
        card_multiplier = sum(card.multiplier - 1.0 for card in cards)

        final_score = self.score + base_score + card_score
        final_multiplier = self.multiplier + base_multiplier - 1.0 + card_multiplier
        return HandResult(name, final_score, final_multiplier)

    def best_five(self, cards: Sequence[CardEntity]) -> tuple[CardEntity, ...]:
        """Devuelve la combinación de cinco cartas con el total calculado más alto."""
        if not 1 <= len(cards):
            raise ValueError("Se requiere al menos una carta")
        if len(cards) <= 5:
            return tuple(cards)
        best = None
        best_total = -1
        for combination_ in combinations(cards, 5):
            result = self.evaluate(combination_)
            if result.total > best_total:
                best_total = result.total
                best = combination_
        return tuple(best or cards[:5])

    def _sum_card_score_recursive(self, cards: Sequence[CardEntity], index: int = 0) -> int:
        """Suma recursivamente el puntaje de cada carta hasta agotar la secuencia."""
        if index >= len(cards):
            return 0
        # Suma la carta actual y procesa recursivamente la siguiente posición.
        return int(cards[index].score) + self._sum_card_score_recursive(cards, index + 1)

    @staticmethod
    def _rank_value(rank: str) -> int:
        """Convierte una etiqueta de rango en su valor numérico de comparación."""
        if rank not in RANK_VALUES:
            raise ValueError(f"Rango desconocido: {rank}")
        return RANK_VALUES[rank]

    @staticmethod
    def _is_straight(unique_ranks: list[int]) -> bool:
        """Devuelve si cinco rangos únicos forman una escalera estándar o con As bajo."""
        if len(unique_ranks) != 5:
            return False
        # Trata A-2-3-4-5 como la escalera con As bajo.
        if unique_ranks == [2, 3, 4, 5, 14]:
            return True
        return unique_ranks == list(range(unique_ranks[0], unique_ranks[0] + 5))