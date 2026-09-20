"""Estado principal de juego con controles visibles, Jokers y ciega visual."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import random

import pygame

from states.base_state import BaseState
from Renderer import Renderer, draw_joker_tooltip, COLOR_TEXT_MAIN
from animaciones import AnimationController
from audio import get_audio_manager
from menu.gestor_config import GestorConfig
from entities import CardEntity, CardFactory, EntityCollection, GameRules, RandomJokerPool
from systems.assets import AssetResolver
from systems.bosses import BossBlind


class PlayState(BaseState):
    MAX_HAND_SIZE = 8
    MAX_PLAY_SIZE = 5
    SUIT_ORDER = {"♣": 0, "♦": 1, "♥": 2, "♠": 3}

    def __init__(self, screen: pygame.Surface, context: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()
        self.renderer = Renderer(*screen.get_size(), screen=screen)
        self.animations = AnimationController()
        self.rules = GameRules()
        self.card_factory = CardFactory(self._project_root(), skin=GestorConfig.obtener_skin_activa())
        self.asset_resolver = AssetResolver(self._project_root())
        self.background = self._load_background()
        self.cards = EntityCollection[CardEntity]()
        self.jokers = RandomJokerPool()
        self.active_boss: BossBlind | None = None
        self.message = "Selecciona 1 a 5 cartas y utiliza los botones o las teclas indicadas"
        self.last_hand_name = "High Card"
        self.round_number = int(self.context.get("round", 1))
        self.target = int(self.context.get("blind_target", 300))
        self.hands_left = 4
        self.discards_left = 3
        self.round_score = 0
        self.max_play_size = self.MAX_PLAY_SIZE
        self.played_card_codes: set[str] = set()
        self.control_rects: dict[str, pygame.Rect] = {}
        self.control_labels: dict[str, str] = {}
        self.dragging_joker_index: int | None = None
        self.show_poker_hands = False
        self.poker_examples: list[dict[str, Any]] = []
        self.blind_asset_path = ""
        self._build_controls()
        self.poker_examples = self._build_poker_examples()
        self.reset_round()

    def enter(self) -> None:
        self.card_factory.set_skin(GestorConfig.obtener_skin_activa())
        self.background = self._load_background()
        self.audio.play_game_music()
        self.round_number = int(self.context.get("round", self.round_number))
        self.target = int(self.context.get("blind_target", 300))
        joker_list = self.context.setdefault("jokers", [])
        self.jokers = RandomJokerPool(joker_list)
        self._build_controls()
        self.reset_round()

    def exit(self) -> None:
        self.animations.cancel()
        self.dragging_joker_index = None
        self.show_poker_hands = False

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _load_background(self) -> pygame.Surface | None:
        ruta = GestorConfig.obtener_fondo_juego()
        if not ruta:
            return None
        try:
            surface = pygame.image.load(ruta).convert_alpha()
            if surface.get_size() != self.screen.get_size():
                surface = pygame.transform.smoothscale(surface, self.screen.get_size())
            return surface
        except Exception:
            return None

    def _build_controls(self) -> None:
        self.control_rects, self.control_labels = self.renderer.build_control_rects()

    def _build_poker_examples(self) -> list[dict[str, Any]]:
        """Construye ejemplos visuales ordenados de mayor a menor puntaje base."""
        definitions = [
            ("Straight Flush", 100, 10.0, [("10", "H"), ("J", "H"), ("Q", "H"), ("K", "H"), ("A", "H")]),
            ("Four of a Kind", 80, 8.0, [("A", "C"), ("A", "D"), ("A", "H"), ("A", "S"), ("2", "C")]),
            ("Full House", 60, 6.0, [("K", "C"), ("K", "D"), ("K", "H"), ("9", "S"), ("9", "C")]),
            ("Flush", 45, 4.0, [("2", "H"), ("5", "H"), ("8", "H"), ("J", "H"), ("A", "H")]),
            ("Straight", 40, 4.0, [("5", "C"), ("6", "D"), ("7", "H"), ("8", "S"), ("9", "C")]),
            ("Three of a Kind", 30, 3.0, [("Q", "C"), ("Q", "D"), ("Q", "H"), ("4", "S"), ("9", "C")]),
            ("Two Pair", 20, 2.0, [("J", "C"), ("J", "D"), ("7", "H"), ("7", "S"), ("A", "C")]),
            ("Pair", 10, 2.0, [("10", "C"), ("10", "D"), ("4", "H"), ("7", "S"), ("A", "C")]),
            ("High Card", 5, 1.0, [("A", "C"), ("7", "D"), ("5", "H"), ("3", "S"), ("2", "C")]),
        ]

        examples: list[dict[str, Any]] = []
        for name, score, multiplier, cards in definitions:
            card_entities = [self.card_factory.create_card(rank, suit) for rank, suit in cards]
            examples.append({
                "name": name,
                "score": score,
                "multiplier": multiplier,
                "cards": [card.to_dict() for card in card_entities],
            })
        return examples

    def _load_boss_rule(self) -> None:
        boss = self.context.get("active_boss") if self.context.get("blind_is_boss") else None
        self.active_boss = boss if isinstance(boss, BossBlind) else None
        self.max_play_size = self.active_boss.get_max_play_size(self.MAX_PLAY_SIZE) if self.active_boss else self.MAX_PLAY_SIZE
        # Solo las Ciegas Jefe utilizan assets de ciegas. Las ciegas pequeña
        # y grande no reciben ni cargan imágenes.
        self.blind_asset_path = ""
        if self.active_boss:
            self.blind_asset_path = self.asset_resolver.blind_asset_for(
                int(self.context.get("blind_index", 0)),
                str(self.context.get("blind_name", "")),
            )
            self.active_boss.apply_effect(self.context)
            self.message = f"JEFE: {self.active_boss.name} — {self.active_boss.description}"
        else:
            self.message = f"Ciega: {self.context.get('blind_name', 'Actual')} | Objetivo: {self.target}"

    def reset_round(self) -> None:
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
        self.cards = EntityCollection[CardEntity](self.card_factory.create_random_collection(self.MAX_HAND_SIZE))
        self.cards.shuffle()
        self._sync_card_rects()

    def _selected_cards(self) -> list[CardEntity]:
        return [card for card in self.cards if card.selected]

    def _boss_game_state(self) -> dict[str, Any]:
        return {
            **self.context,
            "cards": self.cards.copy(),
            "previous_blind_played_card_codes": set(self.context.get("previous_blind_played_card_codes", set())),
        }

    def _sync_card_rects(self) -> None:
        spacing = 95
        start_x = (self.screen.get_width() - len(self.cards) * spacing) // 2 + 100
        start_y = self.renderer.hand_y
        for index, card in enumerate(self.cards):
            if card.rect:
                card.rect.x = start_x + index * spacing
                card.rect.y = start_y - (20 if card.selected else 0)

    def _select_card_at(self, position: tuple[int, int]) -> None:
        self._sync_card_rects()
        for card in reversed(self.cards.copy()):
            if card.rect and card.rect.collidepoint(position):
                selected_count = sum(1 for item in self.cards if item.selected)
                if not card.selected and selected_count >= self.max_play_size:
                    self.message = f"No puedes seleccionar más de {self.max_play_size} cartas"
                    return
                card.toggle_selected()
                return

    def _joker_index_at(self, position: tuple[int, int]) -> int | None:
        for index in range(min(5, len(self.jokers.jokers))):
            if self.renderer.joker_rect(index).collidepoint(position):
                return index
        return None

    def _control_at(self, position: tuple[int, int]) -> str | None:
        for key, rect in self.control_rects.items():
            if rect.collidepoint(position):
                return key
        return None

    def _reorder_jokers_to_position(self, target_index: int) -> None:
        if self.dragging_joker_index is None:
            return
        target_index = max(0, min(target_index, len(self.jokers.jokers) - 1))
        if target_index == self.dragging_joker_index:
            return
        self.jokers.reorder(self.dragging_joker_index, target_index)
        self.dragging_joker_index = target_index
        self.context["jokers"] = self.jokers.jokers

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        poker_button_rect = self.renderer.poker_hands_button_rect()
        poker_modal_rect = self.renderer.poker_hands_modal_rect(self.screen.get_width(), self.screen.get_height())

        for event in events:
            if self.show_poker_hands:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.show_poker_hands = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not poker_modal_rect.collidepoint(event.pos):
                        self.show_poker_hands = False
                continue

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

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_joker_index is not None:
                    slot_width = self.renderer.JOKER_SLOT_W + self.renderer.JOKER_GAP
                    raw = (event.pos[0] - self.renderer.JOKER_START_X + slot_width // 2) // slot_width
                    self._reorder_jokers_to_position(int(raw))

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if poker_button_rect.collidepoint(event.pos):
                    self.show_poker_hands = True
                    continue

                joker_index = self._joker_index_at(event.pos)
                if joker_index is not None:
                    self.dragging_joker_index = joker_index
                    continue

                action = self._control_at(event.pos)
                if action == "play":
                    self.play_selected()
                elif action == "discard":
                    self.discard_selected()
                elif action == "suit":
                    self.sort_by_suit()
                elif action == "rank":
                    self.sort_by_rank()
                else:
                    self._select_card_at(event.pos)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_joker_index = None

        return None

    def update(self, dt: float) -> str | None:
        self.animations.update(dt)
        if self.round_score >= self.target:
            if self.animations.active:
                return None
            victory = self._prepare_store_transition()
            return "VICTORY" if victory else "SHOP"
        if self.hands_left <= 0 and self.round_score < self.target:
            self.context["score"] = int(self.context.get("total_score", 0)) + self.round_score
            return "GAME_OVER"
        return None

    def _prepare_store_transition(self) -> bool:
        """Persiste la ciega superada y prepara estrictamente la siguiente.

        Devuelve True cuando esta victoria derrota al tercer jefe, momento en el
        que no debe abrirse otra tienda: la partida pasa directamente a VICTORY.
        """
        ante = int(self.context.get("ante", 1))
        base_reward = int(self.context.get("blind_reward", 4)) + max(0, ante - 1) * 2
        hand_bonus = max(0, self.hands_left)
        discard_bonus = max(0, self.discards_left)
        economy_bonus = self.jokers.apply_economy_effects(
            int(self.context.get("money", 0)),
            {"total_discards": int(self.context.get("total_discards", 0))},
        )
        total_reward = base_reward + hand_bonus + discard_bonus + economy_bonus
        self.context["money"] = int(self.context.get("money", 0)) + total_reward
        self.context["round_reward"] = {
            "base": base_reward,
            "hands": hand_bonus,
            "discards": discard_bonus,
            "economy": economy_bonus,
            "total": total_reward,
            "score": self.round_score,
            "target": self.target,
        }

        # Puntaje acumulado de toda la partida, no solo de la ciega actual.
        total_score = int(self.context.get("total_score", 0)) + self.round_score
        self.context["total_score"] = total_score
        self.context["score"] = total_score
        self.context["previous_blind_played_card_codes"] = set(self.played_card_codes)
        self.context["blind_won"] = True

        is_boss = bool(self.context.get("blind_is_boss", False))
        self.context["is_boss_blind_won"] = is_boss

        if is_boss:
            bosses_defeated = int(self.context.get("bosses_defeated", 0)) + 1
            self.context["bosses_defeated"] = bosses_defeated

            if bosses_defeated >= 3:
                self.context["victory_score"] = total_score
                return True

            # Nuevo ciclo: Pequeña -> Grande -> Jefe, con un jefe nuevo para el Ante.
            self.context["ante"] = ante + 1
            self.context["blind_index"] = 0
            self.context["active_boss"] = None
            self.context["active_boss_ante"] = None
        else:
            # La siguiente ciega es estrictamente la posterior a la actual.
            current_index = int(self.context.get("blind_index", 0))
            self.context["blind_index"] = min(2, current_index + 1)

        self.context["round"] = int(self.context.get("ante", 1))
        return False

    def _non_scoring_boss_cards(self, selected: list[CardEntity]) -> set[str]:
        if self.active_boss is None:
            return set()
        self.active_boss.validate_play(selected, self._boss_game_state())
        return self.active_boss.non_scoring_card_codes(selected, self._boss_game_state())

    def _apply_boss_post_play_effect(self) -> None:
        if self.active_boss is None:
            return
        result = self.active_boss.after_hand_played([], self._boss_game_state())
        if result.discard_count <= 0:
            return
        candidates = [card for card in self.cards if not card.selected]
        discarded = random.sample(candidates, min(result.discard_count, len(candidates))) if candidates else []
        for card in discarded:
            self.cards.remove(card)
        missing = self.MAX_HAND_SIZE - len(self.cards)
        if missing:
            self.cards.add_many(self.card_factory.create_random_collection(missing))
        self.cards.shuffle()
        self._sync_card_rects()
        self.message = f"{self.active_boss.name}: se descartaron {len(discarded)} cartas al azar."

    def play_selected(self) -> int | None:
        selected = self._selected_cards()
        if not 1 <= len(selected) <= self.max_play_size:
            self.message = f"Selecciona entre 1 y {self.max_play_size} cartas"
            return None
        if self.hands_left <= 0:
            self.message = "No quedan manos disponibles"
            return None
        non_scoring_codes = self._non_scoring_boss_cards(selected)
        scoring_cards = [card for card in selected if card.code not in non_scoring_codes]

        best = self.rules.best_five(scoring_cards) if scoring_cards else []
        self._sync_card_rects()
        start_positions = [(card.rect.x, card.rect.y) for card in selected if card.rect is not None]

        hand_counts = self.context.setdefault("hand_counts", {})
        if best:
            provisional = self.rules.evaluate(best)
            most_played = max(hand_counts, key=hand_counts.get) if hand_counts else ""
            joker_context = {
                "money": int(self.context.get("money", 0)),
                "current_poker_hand": provisional.name,
                "most_played_poker_hand": most_played,
            }
            activated = self.jokers.activate_all(EntityCollection(best), joker_context)
            self.context["money"] = joker_context.get("money", self.context.get("money", 0))
            result = self.rules.evaluate(best)
        else:
            activated = []
            result = None

        hand_name = result.name if result else "Sin puntuación"
        hand_total = result.total if result else 0
        self.last_hand_name = hand_name
        if result:
            hand_counts[result.name] = int(hand_counts.get(result.name, 0)) + 1
        self.round_score += hand_total
        self.hands_left -= 1
        self.played_card_codes.update(card.code for card in selected)

        self.animations.play_cards(
            list(selected),
            start_positions,
            hand_name,
            hand_total,
            non_scoring_codes,
        )
        for card in selected:
            self.cards.remove(card)

        missing = self.MAX_HAND_SIZE - len(self.cards)
        if missing > 0:
            new_cards = self.card_factory.create_random_collection(missing)
            self.cards.add_many(new_cards)
            self.cards.shuffle()
            self._sync_card_rects()
            refill_positions = [(card.rect.x, card.rect.y) for card in new_cards if card.rect is not None]
            self.animations.refill_cards(new_cards, refill_positions)

        self._apply_boss_post_play_effect()
        joker_text = f" | Jokers: {', '.join(activated)}" if activated else ""
        warning = " Estas cartas no tendrán puntuación." if non_scoring_codes else ""
        self.message = f"{hand_name}: {hand_total} pts | Acumulado: {self.round_score}/{self.target}{warning}{joker_text}"
        return hand_total

    def discard_selected(self) -> int | None:
        selected = self._selected_cards()
        if not selected:
            self.message = "Selecciona cartas para descartar"
            return None
        if self.discards_left <= 0:
            self.message = "No quedan descartes"
            return None

        activated = self.jokers.handle_discard(selected)
        self.context["total_discards"] = int(self.context.get("total_discards", 0)) + 1
        for card in selected:
            self.cards.remove(card)
        self.discards_left -= 1
        missing = self.MAX_HAND_SIZE - len(self.cards)
        new_cards = self.card_factory.create_random_collection(missing)
        self.cards.add_many(new_cards)
        self.cards.shuffle()
        self._sync_card_rects()
        refill_positions = [(card.rect.x, card.rect.y) for card in new_cards if card.rect is not None]
        self.animations.refill_cards(new_cards, refill_positions)
        suffix = f" | {', '.join(activated)}" if activated else ""
        self.message = f"Descartaste {len(selected)} cartas | Acumulado: {self.round_score}/{self.target}{suffix}"
        return len(selected)

    def sort_by_suit(self) -> None:
        cards = self.cards.copy()
        cards.sort(key=lambda card: (self.SUIT_ORDER.get(card.suit, 99), -self._rank_value(card.rank)))
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por palo"

    def sort_by_rank(self) -> None:
        cards = self.cards.copy()
        cards.sort(key=lambda card: (-self._rank_value(card.rank), self.SUIT_ORDER.get(card.suit, 99)))
        self.cards = EntityCollection[CardEntity](cards)
        self._sync_card_rects()
        self.message = "Cartas organizadas por número"

    @staticmethod
    def _rank_value(rank: str) -> int:
        special = {"A": 14, "K": 13, "Q": 12, "J": 11}
        if rank in special:
            return special[rank]
        return int(rank)

    def draw(self, screen: pygame.Surface | None = None) -> None:
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
        self.renderer.draw_hud_panel(self.round_score, self.target, mult, chips, self.hands_left, self.discards_left)
        is_boss = bool(self.context.get("blind_is_boss", False))
        boss_description = self.context.get("boss_description", "") if is_boss else ""
        self.renderer.draw_blind_panel(
            self.context.get("blind_name", "Ciega"),
            self.target,
            self.blind_asset_path,
            is_boss,
            boss_description,
        )

        mouse = pygame.mouse.get_pos()
        hovered_joker, _ = self.renderer.draw_joker_bar(self.jokers.jokers, mouse, self.dragging_joker_index)

        hidden_card_ids = self.animations.hidden_card_ids
        card_data = [card.to_dict() for card in self.cards if id(card) not in hidden_card_ids]
        self.renderer.draw_hand(card_data)
        if self.animations.active:
            self.animations.draw(self.renderer, target_screen)

        self.renderer.draw_controls(target_screen, self.control_rects, self.control_labels)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        message_surface = font.render(self.message, True, COLOR_TEXT_MAIN)
        target_screen.blit(message_surface, message_surface.get_rect(center=(target_screen.get_width() // 2, target_screen.get_height() - 48)))

        if hovered_joker is not None and not self.show_poker_hands:
            draw_joker_tooltip(target_screen, hovered_joker.to_dict() if hasattr(hovered_joker, "to_dict") else hovered_joker, mouse)

        if self.show_poker_hands:
            self.renderer.draw_poker_hands_modal(self.poker_examples)
