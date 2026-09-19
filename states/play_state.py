"""
Play state with boss-blind rule enforcement.

The implementation integrates boss rules through polymorphism and does not
modify the Joker entity or its implementation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import random

import pygame

from states.base_state import BaseState
from Renderer import Renderer
from animaciones import AnimationController
from audio import get_audio_manager
from menu.gestor_config import GestorConfig
from entities import (
    CardEntity,
    CardFactory,
    EntityCollection,
    GameRules,
    RandomJokerPool,
)
from systems.bosses import BossBlind


class PlayState(BaseState):
    """Administer one blind and enforce its active boss rule, when present."""

    MAX_HAND_SIZE = 8
    MAX_PLAY_SIZE = 5

    SUIT_ORDER = {
        "♣": 0,
        "♦": 1,
        "♥": 2,
        "♠": 3,
    }

    def __init__(self, screen: pygame.Surface, context: dict[str, Any] | None = None) -> None:
        """Initialize the play state with the persistent game context."""
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        self.animations = AnimationController()
        self.rules = GameRules()
        self.background = self._load_background()
        self.card_factory = CardFactory(
            self._project_root(),
            skin=GestorConfig.obtener_skin_activa(),
        )
        self.cards = EntityCollection[CardEntity]()

        self.message = "Selecciona de 1 a 5 cartas y presiona ESPACIO"
        self.last_hand_name = "High Card"
        self.round_number = int(self.context.get("round", 1))
        self.target = int(self.context.get("blind_target", 100 * self.round_number))
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.jokers = RandomJokerPool()
        self.active_boss: BossBlind | None = None
        self.max_play_size = self.MAX_PLAY_SIZE
        self.played_card_codes: set[str] = set()

        self.sort_suit_rect = pygame.Rect(0, 0, 130, 24)
        self.sort_rank_rect = pygame.Rect(0, 0, 130, 24)

        self.reset_round()

    def enter(self) -> None:
        """Activate the state and load the currently selected blind/boss."""
        self.card_factory.set_skin(GestorConfig.obtener_skin_activa())
        self.background = self._load_background()
        self.audio.play_game_music()
        self.round_number = int(self.context.get("round", self.round_number))
        self.target = int(self.context.get("blind_target", 100 * self.round_number))
        joker_list = self.context.setdefault("jokers", [])
        self.jokers = RandomJokerPool(joker_list)
        self.reset_round()

    def exit(self) -> None:
        """Cancel animations before leaving the play state."""
        self.animations.cancel()

    def _project_root(self) -> Path:
        """Return the project root used to locate game resources."""
        return Path(__file__).resolve().parent.parent

    def _load_background(self) -> pygame.Surface | None:
        """Load the configured game background when available."""
        ruta_fondo = GestorConfig.obtener_fondo_juego()
        if not ruta_fondo:
            return None
        try:
            fondo = pygame.image.load(ruta_fondo).convert_alpha()
            if fondo.get_size() != self.screen.get_size():
                fondo = pygame.transform.smoothscale(fondo, self.screen.get_size())
            return fondo
        except Exception:
            return None

    def _load_boss_rule(self) -> None:
        """Resolve the active boss and apply its persistent setup to this round."""
        boss = self.context.get("active_boss") if self.context.get("blind_is_boss") else None
        self.active_boss = boss if isinstance(boss, BossBlind) else None
        self.max_play_size = (
            self.active_boss.get_max_play_size(self.MAX_PLAY_SIZE)
            if self.active_boss
            else self.MAX_PLAY_SIZE
        )

        if self.active_boss:
            self.active_boss.apply_effect(self.context)
            self.message = (
                f"JEFE: {self.active_boss.name} — "
                f"{self.active_boss.description}"
            )
        else:
            self.message = (
                f"Ciega: {self.context.get('blind_name', 'Actual')} | "
                f"Objetivo: {self.target}"
            )

    def reset_round(self) -> None:
        """Reset hands, discards, score and boss-specific round state."""
        self.card_factory.set_skin(GestorConfig.obtener_skin_activa())
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.rules.reset()
        self.played_card_codes.clear()
        self._load_boss_rule()
        self._start_round()

        if self.active_boss and self.active_boss.effect_id == "needle":
            self.hands_left = 1

    def _start_round(self) -> None:
        """Generate eight cards and shuffle them for the round."""
        self.cards = EntityCollection[CardEntity](
            self.card_factory.create_random_collection(self.MAX_HAND_SIZE)
        )
        self.cards.shuffle()

    def _selected_cards(self) -> list[CardEntity]:
        """Return currently selected cards."""
        return [card for card in self.cards if card.selected]

    def _boss_game_state(self) -> dict[str, Any]:
        """Build the minimal state exposed to boss rules."""
        return {
            **self.context,
            "cards": self.cards.copy(),
            "previous_blind_played_card_codes": set(
                self.context.get("previous_blind_played_card_codes", set())
            ),
        }

    def _select_card_at(self, position: tuple[int, int]) -> None:
        """Select or deselect a card while respecting the active play-size limit."""
        self._sync_card_rects()
        for card in reversed(self.cards.copy()):
            if card.rect is not None and card.rect.collidepoint(position):
                selected_count = sum(1 for item in self.cards if item.selected)
                if not card.selected and selected_count >= self.max_play_size:
                    self.message = (
                        f"No puedes seleccionar más de {self.max_play_size} cartas"
                    )
                    return
                card.toggle_selected()
                return

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """Process keyboard and mouse input."""
        for event in events:
            if self.animations.active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.animations.cancel()
                    return "MENU"
                self.animations.handle_event(event)
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.play_selected()
                elif event.key == pygame.K_d:
                    self.discard_selected()
                elif event.key == pygame.K_s:
                    self.sort_by_suit()
                elif event.key == pygame.K_r:
                    self.sort_by_rank()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.sort_suit_rect.collidepoint(event.pos):
                    self.sort_by_suit()
                elif self.sort_rank_rect.collidepoint(event.pos):
                    self.sort_by_rank()
                else:
                    self._select_card_at(event.pos)

        return None

    def update(self, dt: float) -> str | None:
        """Update animations and transition when the blind is won or lost."""
        self.animations.update(dt)

        if self.round_score >= self.target:
            if self.animations.active:
                return None
            self._prepare_store_transition()
            return "SHOP"

        if self.hands_left <= 0 and self.round_score < self.target:
            self.context["score"] = self.round_score
            return "GAME_OVER"

        return None

    def _prepare_store_transition(self) -> None:
        """Persist rewards, played-card history and Ante progression."""
        ante = int(self.context.get("ante", 1))
        base_reward = int(self.context.get("blind_reward", 4)) + max(0, ante - 1) * 2
        hand_bonus = max(0, self.hands_left)
        discard_bonus = max(0, self.discards_left)
        total_reward = base_reward + hand_bonus + discard_bonus

        self.context["money"] = int(self.context.get("money", 0)) + total_reward
        self.context["round_reward"] = {
            "base": base_reward,
            "hands": hand_bonus,
            "discards": discard_bonus,
            "total": total_reward,
            "score": self.round_score,
            "target": self.target,
        }
        self.context["score"] = self.round_score

        # Store only cards that were actually played, not discarded.
        self.context["previous_blind_played_card_codes"] = set(self.played_card_codes)
        self.context["round"] = self.round_number + 1
        self.context["blind_won"] = True
        self.context["is_boss_blind_won"] = bool(
            self.context.get("blind_is_boss", False)
        )

        if self.context["is_boss_blind_won"]:
            self.context["ante"] = ante + 1
            self.context["blind_index"] = 0
            self.context["active_boss"] = None
            self.context["active_boss_ante"] = None

    def _validate_boss_play(self, selected: list[CardEntity]) -> bool:
        """Run the active boss validation before spending a hand."""
        if self.active_boss is None:
            return True

        result = self.active_boss.validate_play(selected, self._boss_game_state())
        if not result.allowed:
            self.message = result.message
            for card in selected:
                card.selected = False
        return result.allowed

    def _apply_boss_post_play_effect(self) -> None:
        """Apply polymorphic effects that occur immediately after a played hand."""
        if self.active_boss is None:
            return

        result = self.active_boss.after_hand_played(
            [],
            self._boss_game_state(),
        )
        if result.discard_count <= 0:
            return

        candidates = [card for card in self.cards if not card.selected]
        discard_count = min(result.discard_count, len(candidates))
        discarded = random.sample(candidates, discard_count) if discard_count else []
        for card in discarded:
            self.cards.remove(card)

        missing = self.MAX_HAND_SIZE - len(self.cards)
        if missing > 0:
            self.cards.add_many(self.card_factory.create_random_collection(missing))
        self.cards.shuffle()
        self._sync_card_rects()

        self.message = (
            f"{self.active_boss.name}: se descartaron {discard_count} "
            f"cartas al azar."
        )

    def play_selected(self) -> int | None:
        """Evaluate and play the selected hand after boss validation."""
        selected = self._selected_cards()
        if not 1 <= len(selected) <= self.max_play_size:
            self.message = (
                f"Selecciona entre 1 y {self.max_play_size} cartas"
            )
            return None
        if self.hands_left <= 0:
            self.message = "No quedan manos disponibles"
            return None
        if not self._validate_boss_play(selected):
            return None

        best = self.rules.best_five(selected)
        self._sync_card_rects()
        start_positions = [
            (card.rect.x, card.rect.y) for card in best if card.rect is not None
        ]

        activated = self.jokers.activate_all(EntityCollection(best))
        result = self.rules.evaluate(best)
        self.last_hand_name = result.name
        self.round_score += result.total
        self.hands_left -= 1
        self.played_card_codes.update(card.code for card in best)

        self.animations.play_cards(
            list(best),
            start_positions,
            result.name,
            result.total,
        )

        for card in selected:
            self.cards.remove(card)

        missing = self.MAX_HAND_SIZE - len(self.cards)
        if missing > 0:
            new_cards = self.card_factory.create_random_collection(missing)
            self.cards.add_many(new_cards)
            self.cards.shuffle()
            self._sync_card_rects()
            refill_positions = [
                (card.rect.x, card.rect.y) for card in new_cards if card.rect is not None
            ]
            self.animations.refill_cards(new_cards, refill_positions)

        self._apply_boss_post_play_effect()

        if self.active_boss and self.active_boss.effect_id != "hook":
            joker_text = f" | Jokers: {', '.join(activated)}" if activated else ""
            self.message = (
                f"{result.name}: {result.total} pts | "
                f"Acumulado: {self.round_score}/{self.target}{joker_text}"
            )
        elif not self.active_boss:
            joker_text = f" | Jokers: {', '.join(activated)}" if activated else ""
            self.message = (
                f"{result.name}: {result.total} pts | "
                f"Acumulado: {self.round_score}/{self.target}{joker_text}"
            )

        return result.total

    def discard_selected(self) -> int | None:
        """Discard selected cards and refill the hand."""
        selected = self._selected_cards()
        if not selected:
            self.message = "Selecciona cartas para descartar"
            return None
        if self.discards_left <= 0:
            self.message = "No quedan descartes"
            return None

        for card in selected:
            self.cards.remove(card)

        self.discards_left -= 1
        missing = self.MAX_HAND_SIZE - len(self.cards)
        new_cards = self.card_factory.create_random_collection(missing)
        self.cards.add_many(new_cards)
        self.cards.shuffle()
        self._sync_card_rects()
        refill_positions = [
            (card.rect.x, card.rect.y) for card in new_cards if card.rect is not None
        ]
        self.animations.refill_cards(new_cards, refill_positions)
        self.message = (
            f"Descartaste {len(selected)} cartas | "
            f"Acumulado: {self.round_score}/{self.target}"
        )
        return len(selected)

    def sort_by_suit(self) -> None:
        """Sort cards by suit and then rank."""
        cards = self.cards.copy()
        cards.sort(
            key=lambda card: (
                self.SUIT_ORDER.get(card.suit, 99),
                -self._rank_value(card.rank),
            )
        )
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por palo"

    def sort_by_rank(self) -> None:
        """Sort cards by rank and use suit as a tie breaker."""
        cards = self.cards.copy()
        cards.sort(
            key=lambda card: (
                -self._rank_value(card.rank),
                self.SUIT_ORDER.get(card.suit, 99),
            )
        )
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por número"

    @staticmethod
    def _rank_value(rank: str) -> int:
        """Return a numeric rank for sorting."""
        if rank == "A":
            return 14
        if rank == "K":
            return 13
        if rank == "Q":
            return 12
        if rank == "J":
            return 11
        return int(rank)

    def _sync_card_rects(self) -> None:
        """Synchronize card rectangles with the current hand layout."""
        spacing = 95
        start_x = (self.screen.get_width() - (len(self.cards) * spacing)) // 2 + 100
        start_y = self.screen.get_height() - 120
        for index, card in enumerate(self.cards):
            if card.rect:
                card.rect.x = start_x + index * spacing
                card.rect.y = start_y - (20 if card.selected else 0)

        self.sort_suit_rect = pygame.Rect(
            self.screen.get_width() // 2 - 140,
            self.screen.get_height() - 62,
            130,
            26,
        )
        self.sort_rank_rect = pygame.Rect(
            self.screen.get_width() // 2 + 10,
            self.screen.get_height() - 62,
            130,
            26,
        )

    def draw(self, screen: pygame.Surface | None = None) -> None:
        """Render HUD, Jokers, cards, controls and boss messages."""
        target_screen = screen or self.screen
        self._sync_card_rects()
        if self.background is not None:
            target_screen.blit(self.background, (0, 0))
        else:
            self.renderer.clear()
        self.renderer.draw_round_progress_bar(self.round_score, self.target)

        selected_cards = self._selected_cards()
        result = self.rules.evaluate(selected_cards) if selected_cards else None
        chips = result.score if result else self.round_score
        mult = result.multiplier if result else self.rules.multiplier

        self.renderer.draw_hud_panel(
            self.round_score,
            self.target,
            mult,
            chips,
            self.hands_left,
            self.discards_left,
        )
        self.renderer.draw_joker_bar(self.jokers.to_dict())

        hidden_card_ids = self.animations.hidden_card_ids
        card_data = [
            card.to_dict() for card in self.cards if id(card) not in hidden_card_ids
        ]
        self.renderer.draw_hand(card_data)

        if self.animations.active:
            self.animations.draw(self.renderer, target_screen)

        self._draw_sort_buttons(target_screen)

        font = pygame.font.SysFont("Arial", 18, bold=True)
        text = font.render(self.message, True, (255, 255, 255))
        target_screen.blit(text, (300, target_screen.get_height() - 92))

    def _draw_sort_buttons(self, screen: pygame.Surface) -> None:
        """Draw the two card sorting actions."""
        button_data = (
            (self.sort_suit_rect, "ORDENAR PALO"),
            (self.sort_rank_rect, "ORDENAR NUMERO"),
        )
        font = pygame.font.SysFont("Arial", 13, bold=True)
        for rect, label in button_data:
            pygame.draw.rect(screen, (55, 55, 70), rect, border_radius=5)
            pygame.draw.rect(screen, (210, 210, 220), rect, width=1, border_radius=5)
            surface = font.render(label, True, (255, 255, 255))
            screen.blit(surface, surface.get_rect(center=rect.center))
