"""Clases base abstractas para Comodines (Jokers) e interfaz polimórfica."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
from typing import Iterable

from .entities import CardEntity, EntityCollection
from .rules import GameRules


class Joker(ABC):
    """Define la interfaz común para el efecto de cada Comodín.

    Cada Comodín tiene una probabilidad entre 0 y 1. El método público ``activate``
    gestiona la verificación de probabilidad, mientras que las subclases implementan
    ``apply`` con su propio efecto. Esto permite tratar diferentes clases de Jokers
    mediante una interfaz común, demostrando polimorfismo.
    """

    def __init__(self, name: str, probability: float = 1.0) -> None:
        """Crea un Comodín con un nombre visible y una probabilidad de activación."""
        if not 0.0 <= probability <= 1.0:
            raise ValueError("la probabilidad debe estar entre 0 y 1")
        self.name = name
        self.probability = probability
        self.active = True

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aplica el efecto concreto del Comodín y devuelve si se aplicó o no."""
        raise NotImplementedError

    def activate(self, cards: Iterable[CardEntity]) -> bool:
        """Evalúa la probabilidad y aplica el Comodín solo si se activa."""
        if not self.active:
            return False
        if random.random() < self.probability:
            return self.apply(cards)
        return False

    def to_dict(self) -> dict:
        """Expone el estado del Comodín en un formato de diccionario fácil de renderizar."""
        return {
            "name": self.name,
            "description": getattr(self, "description", "Efecto especial"),
            "probability": self.probability,
            "active": self.active,
        }


# =====================================================================
# CLASES BASE INTERMEDIAS (ABSTRACTAS)
# =====================================================================

@dataclass
class FlatChipsJoker(Joker, ABC):
    """Clase base abstracta para comodines que suman una cantidad fija de fichas a las cartas."""

    amount: int = 20
    probability: float = 1.0

    def __post_init__(self) -> None:
        super().__init__("Base Fichas Plana", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aumenta el puntaje de las cartas. Debe ser implementado o invocado por subclases."""
        applied = False
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
            applied = True
        return applied


@dataclass
class MultiplierJoker(Joker, ABC):
    """Clase base abstracta para comodines que aumentan el multiplicador de las cartas."""

    amount: float = 1.0
    probability: float = 1.0

    def __post_init__(self) -> None:
        super().__init__("Base Multiplicador", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aumenta el multiplicador de las cartas. Debe ser implementado o invocado por subclases."""
        applied = False
        for card in cards:
            card.apply_bonus(multiplier_delta=self.amount)
            applied = True
        return applied


@dataclass
class SuitBonusJoker(MultiplierJoker, ABC):
    """Clase base abstracta para comodines enfocados en un palo/pinta específico.

    Hereda la lógica de multiplicador de MultiplierJoker y agrega el filtrado
    por palo. Tampoco es instanciable directamente.
    """

    target_suit: str = "♥"  # Símbolos: '♥', '♦', '♣', '♠'

    def __post_init__(self) -> None:
        super().__post_init__()
        nombres_pintas = {"♥": "Corazones", "♦": "Diamantes", "♣": "Tréboles", "♠": "Picas"}
        nombre_pinta = nombres_pintas.get(self.target_suit, self.target_suit)
        self.name = f"Especialista en {nombre_pinta}"

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Filtra las cartas por palo y delega la aplicación del bono a MultiplierJoker."""
        cards_filtradas = [c for c in cards if getattr(c, "suit", None) == self.target_suit]
        if not cards_filtradas:
            return False
        return super().apply(cards_filtradas)


@dataclass
class FragileJoker(Joker, ABC):
    """Clase base abstracta para comodines que tienen una vida útil limitada o condiciones de destrucción.

    Mantiene un contador de usos o un estado de durabilidad. Una vez que se cumple
    la condición de desgaste (por ejemplo, agotar sus usos), el comodín se desactiva
    automáticamente para evitar futuras ejecuciones.
    """

    uses_left: int = 3
    probability: float = 1.0

    def __post_init__(self) -> None:
        """Inicializa la clase base de Joker y valida el límite de usos."""
        if self.uses_left <= 0:
            raise ValueError("Los usos iniciales deben ser mayores a 0")
        super().__init__("Base Frágil", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aplica el efecto del comodín frágil. 

        Las subclases deben llamar a super().apply(cards) o ejecutar _consume_use()
        para decrementar la durabilidad tras un uso exitoso.
        """
        if self.uses_left <= 0 or not self.active:
            return False
        return True

    def _consume_use(self) -> None:
        """Reduce la durabilidad del comodín y lo destruye/desactiva al llegar a cero."""
        self.uses_left -= 1
        if self.uses_left <= 0:
            self.active = False

    def to_dict(self) -> dict:
        """Extiende la serialización para incluir los usos restantes."""
        data = super().to_dict()
        data["uses_left"] = self.uses_left
        return data
    
class FoodJokerMixin:
    """Clase marcadora para identificar comodines de tipo comida."""
    pass

@dataclass
class CannibalJoker(Joker, ABC):
    """Clase base abstracta para comodines que devoran al comodín de su izquierda."""

    mult_growth: float = 3.0  # Incremento base predeterminado
    current_mult: float = 0.0  # Multiplicador acumulado actual
    probability: float = 1.0

    def __post_init__(self) -> None:
        super().__init__("Base Caníbal", self.probability)

    def _consume_left_joker(self, jokers_pool: list[Joker]) -> Joker | None:
        """Busca y destruye el comodín ubicado exactamente a la izquierda."""
        try:
            my_index = jokers_pool.index(self)
        except ValueError:
            return None

        if my_index == 0:
            return None

        left_joker = jokers_pool[my_index - 1]

        if not left_joker.active:
            return None

        left_joker.active = False  # Desactiva/mata al comodín de la izquierda
        return left_joker

    @abstractmethod
    def apply_with_pool(self, cards: Iterable[CardEntity], jokers_pool: list[Joker]) -> bool:
        """Cada caníbal concreto define cómo incrementa su poder al comer."""
        raise NotImplementedError

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Método heredado de la interfaz base."""
        return False

    def to_dict(self) -> dict:
        """Incluye el multiplicador acumulado actual en la serialización."""
        data = super().to_dict()
        data["current_mult"] = self.current_mult
        data["mult_growth"] = self.mult_growth
        return data

@dataclass
class HandRequirementJoker(Joker, ABC):
    """Clase base abstracta para comodines que solo se activan con un tipo de mano específico.

    Recibe el nombre de la mano requerida (según las claves de ``GameRules.HAND_VALUES``, 
    como 'Pair', 'Flush', 'Full House', etc.) y delega la lógica si la mano coincide.
    """

    target_hand: str = "Pair"
    probability: float = 1.0

    def __post_init__(self) -> None:
        """Inicializa la clase base de Joker con un nombre descriptivo."""
        nombres_manos = {
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
        nombre_traduccion = nombres_manos.get(self.target_hand, self.target_hand)
        super().__init__(f"Especialista en {nombre_traduccion}", self.probability)

    @abstractmethod
    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aplica el efecto si la mano evaluada coincide con ``target_hand``.

        Debe ser extendido o invocado por las subclases concretas.
        """
        cards_list = list(cards)
        if not cards_list:
            return False

        rules = GameRules()
        hand_result = rules.evaluate(cards_list)

        if hand_result.name != self.target_hand:
            return False

        return True


@dataclass
class EconomyJoker(Joker, ABC):
    """Clase base abstracta para comodines que afectan o dependen de la economía del jugador.

    Permite manipular el saldo de dinero del jugador, otorgar bonificaciones
    según el oro acumulado o modificar las recompensas al finalizar cada mano o ronda.
    """

    base_reward: int = 4
    probability: float = 1.0

    def __post_init__(self) -> None:
        """Inicializa la clase base de Joker con un nombre descriptivo."""
        super().__init__("Base Economía", self.probability)

    @abstractmethod
    def apply_economy_effect(self, current_money: int) -> int:
        """Calcula y devuelve la variación de dinero (ganancia o gasto).

        Debe ser implementado por las subclases concretas para definir su
        lógica financiera específica.
        """
        raise NotImplementedError

    def apply(self, cards: Iterable[CardEntity]) -> bool:
        """Aplica el efecto estándar devolviendo True si el comodín logró ejecutarse.

        Las subclases concretas pueden sobreescribir este método para otorgar
        bonos de combate directos basados en el saldo actual de la economía.
        """
        return True


@dataclass
class DiscardDependentJoker(Joker, ABC):
    """Clase base abstracta para comodines que se activan o ganan bonos al descartar cartas."""

    discards_required: int = 1

    def __post_init__(self) -> None:
        super().__init__("Base de Descartes", self.probability)

    @abstractmethod
    def on_discard(self, discarded_cards: Iterable[CardEntity]) -> bool:
        """Reacciona directamente cuando el jugador realiza un descarte."""
        cards_list = list(discarded_cards)
        if not cards_list:
            return False
        return True


# =====================================================================
# POOL / CONTENEDOR DE COMODINES
# =====================================================================

class RandomJokerPool:
    """Agrupa múltiples Comodines y activa cada uno de manera independiente."""

    def __init__(self, jokers: Iterable[Joker] | None = None) -> None:
        self.jokers = list(jokers or [])

    def add(self, joker: Joker) -> None:
        self.jokers.append(joker)

    def activate_all(self, cards: EntityCollection[CardEntity]) -> list[str]:
        activated = []
        for joker in self.jokers:
            if joker.activate(cards):
                activated.append(joker.name)
        return activated

    def to_dict(self) -> list[dict]:
        return [joker.to_dict() for joker in self.jokers]