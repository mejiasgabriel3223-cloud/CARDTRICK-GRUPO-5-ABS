"""
Store state with integrated boss-blind selection.

The Joker entity layer is intentionally untouched. Bosses are selected and
configured independently through ``systems.bosses`` and shared game context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import random

import pygame

from entities import Joker, FlatChipsJoker, MultiplierJoker
from states.base_state import BaseState
from systems.bosses import BossBlind, BASE_ANTE_TARGETS, get_random_boss_instance


@dataclass(frozen=True)
class JokerOffer:
    """Represent one Joker available for purchase."""

    joker: Joker
    price: int
    slot: int


@dataclass(frozen=True)
class BlindOption:
    """Represent one blind selectable before returning to PlayState."""

    name: str
    target: int
    ante: int
    blind_index: int
    is_boss: bool = False
    description: str = ""
    boss: BossBlind | None = None


class StoreFlatJoker(Joker):
    """Joker offer that adds chips to each played card."""

    def __init__(self, name: str, amount: int, probability: float = 1.0) -> None:
        super().__init__(name, probability)
        self.amount = amount
        self.description = f"+{amount} fichas por carta"

    def apply(self, cards: Iterable[Any]) -> bool:
        """Apply the chip bonus to all received cards."""
        for card in cards:
            card.apply_bonus(score_delta=self.amount)
        return True


class StoreMultiplierJoker(Joker):
    """Joker offer that adds multiplier to each played card."""

    def __init__(self, name: str, amount: float, probability: float = 1.0) -> None:
        super().__init__(name, probability)
        self.amount = amount
        self.description = f"+{amount:g} Mult por carta"

    def apply(self, cards: Iterable[Any]) -> bool:
        """Apply the multiplier bonus to all received cards."""
        for card in cards:
            card.apply_bonus(multiplier_delta=self.amount)
        return True


class StoreState(BaseState):
    """Manage summary, shop and blind selection screens."""

    SUMMARY = "SUMMARY"
    SHOP = "SHOP"
    BLIND_SELECT = "BLIND_SELECT"
    MAX_JOKERS = 5
    REROLL_COST = 5

    def __init__(self, screen: pygame.Surface, context: dict[str, Any] | None = None) -> None:
        """Initialize the store and prepare persistent game context."""
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.phase = self.SUMMARY
        self.message = ""
        self.selected_owned_index: int | None = None
        self.offers: list[JokerOffer] = []
        self.blind_options: list[BlindOption] = []
        self._prepare_persistent_values()
        self._build_buttons()

    def _prepare_persistent_values(self) -> None:
        """Create persistent keys required by the store and boss system."""
        self.context.setdefault("money", 0)
        self.context.setdefault("jokers", [])
        self.context.setdefault("ante", 1)
        self.context.setdefault("blind_index", 0)
        self.context.setdefault("selected_blind", None)
        self.context.setdefault("blind_target", 100)
        self.context.setdefault("blind_name", "Ciega pequeña")
        self.context.setdefault("blind_is_boss", False)
        self.context.setdefault("active_boss", None)
        self.context.setdefault("active_boss_ante", None)
        self.context.setdefault("seen_boss_ids", set())
        self.context.setdefault("previous_blind_played_card_codes", set())
        self.context.setdefault(
            "round_reward", {"base": 0, "hands": 0, "discards": 0, "total": 0}
        )

    @property
    def money(self) -> int:
        """Return the persistent player money."""
        return int(self.context.get("money", 0))

    @property
    def jokers(self) -> list[Joker]:
        """Return the persistent collection of purchased Jokers."""
        return self.context.setdefault("jokers", [])

    def enter(self) -> None:
        """Enter the store and prepare offers plus the current boss metadata."""
        self.phase = self.SUMMARY
        self.selected_owned_index = None
        self.message = "Ciega superada"
        self.context["selected_blind"] = None
        self._ensure_active_boss()
        self._generate_offers()
        self._generate_blind_options()
        self._build_buttons()

    def exit(self) -> None:
        """Clear temporary Joker selection when leaving the store."""
        self.selected_owned_index = None

    def _ensure_active_boss(self) -> BossBlind:
        """Create one boss per Ante and reuse it for small/big/boss selection."""
        ante = max(1, int(self.context.get("ante", 1)))
        current_boss = self.context.get("active_boss")
        stored_ante = self.context.get("active_boss_ante")

        if current_boss is None or stored_ante != ante:
            seen_boss_ids = self.context.setdefault("seen_boss_ids", set())
            current_boss = get_random_boss_instance(seen_boss_ids)
            self.context["active_boss"] = current_boss
            self.context["active_boss_ante"] = ante

        return current_boss

    def _build_buttons(self) -> None:
        """Build mouse rectangles for all store screens."""
        width = self.screen.get_width()
        height = self.screen.get_height()
        self.accept_rect = pygame.Rect(width // 2 - 110, height - 90, 220, 50)
        self.reroll_rect = pygame.Rect(width - 250, height - 90, 105, 50)
        self.continue_rect = pygame.Rect(width // 2 - 110, height - 90, 220, 50)
        self.sell_rect = pygame.Rect(width - 250, height - 150, 105, 50)
        self.offer_rects = [
            pygame.Rect(width // 2 - 270, 190, 220, 230),
            pygame.Rect(width // 2 + 50, 190, 220, 230),
        ]
        self.owned_rects = [
            pygame.Rect(40 + index * 145, 475, 125, 105)
            for index in range(self.MAX_JOKERS)
        ]
        self.blind_rects = [
            pygame.Rect(width // 2 - 350, 190, 210, 285),
            pygame.Rect(width // 2 - 105, 190, 210, 285),
            pygame.Rect(width // 2 + 140, 190, 210, 285),
        ]

    def _generate_offers(self) -> None:
        """Generate exactly two independent Joker offers."""
        ante = max(1, int(self.context.get("ante", 1)))
        choices = [
            lambda: (StoreFlatJoker("Cargador", 10 + ante * 3), 5 + ante),
            lambda: (StoreFlatJoker("Acumulador", 20 + ante * 4), 8 + ante * 2),
            lambda: (StoreMultiplierJoker("Impulso", 1.0), 7 + ante),
            lambda: (StoreMultiplierJoker("Potenciador", 2.0), 10 + ante * 2),
            lambda: (FlatChipsJoker(amount=15 + ante * 5), 6 + ante),
            lambda: (MultiplierJoker(amount=0.5), 8 + ante),
        ]

        self.offers = []
        for slot in range(2):
            creator = random.choice(choices)
            joker, price = creator()
            setattr(joker, "shop_price", price)
            self.offers.append(JokerOffer(joker, price, slot))

    def _generate_blind_options(self) -> None:
        """Generate the two normal blinds and the configured boss blind."""
        ante = max(1, int(self.context.get("ante", 1)))
        base_target = 100 * ante
        blind_index = int(self.context.get("blind_index", 0))
        boss = self._ensure_active_boss()
        boss_target = boss.calculate_target_score(ante)

        self.blind_options = [
            BlindOption(
                "Ciega pequeña",
                base_target,
                ante,
                blind_index,
                False,
                "Ciega normal.",
            ),
            BlindOption(
                "Ciega grande",
                base_target + 50,
                ante,
                blind_index + 1,
                False,
                "Ciega normal con objetivo mayor.",
            ),
            BlindOption(
                boss.name,
                boss_target,
                ante,
                2,
                True,
                boss.description,
                boss,
            ),
        ]

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        """Process buttons, keyboard and blind selection."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "MENU"
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    result = self._activate_primary_action()
                    if result:
                        return result
                elif event.key == pygame.K_r and self.phase == self.SHOP:
                    self._reroll()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                result = self._handle_mouse_click(event.pos)
                if result:
                    return result
        return None

    def _activate_primary_action(self) -> str | None:
        """Advance from summary to shop, shop to blind selection, or play."""
        if self.phase == self.SUMMARY:
            self.phase = self.SHOP
            self.message = "Compra, vende o rerrollea Jokers"
            return None
        if self.phase == self.SHOP:
            self.phase = self.BLIND_SELECT
            self.message = "Selecciona la siguiente ciega"
            return None
        return self._continue_to_play()

    def _handle_mouse_click(self, position: tuple[int, int]) -> str | None:
        """Resolve a mouse click according to the active store phase."""
        if self.phase == self.SUMMARY:
            if self.accept_rect.collidepoint(position):
                self.phase = self.SHOP
                self.message = "Compra, vende o rerrollea Jokers"
            return None

        if self.phase == self.SHOP:
            for offer in self.offers:
                if self.offer_rects[offer.slot].collidepoint(position):
                    self._buy_offer(offer.slot)
                    return None

            for index, rect in enumerate(self.owned_rects):
                if index < len(self.jokers) and rect.collidepoint(position):
                    self.selected_owned_index = index
                    self.message = f"Seleccionado: {self.jokers[index].name}"
                    return None

            if self.sell_rect.collidepoint(position):
                self._sell_selected()
            elif self.reroll_rect.collidepoint(position):
                self._reroll()
            elif self.continue_rect.collidepoint(position):
                self.phase = self.BLIND_SELECT
                self.message = "Selecciona la siguiente ciega"
            return None

        for index, rect in enumerate(self.blind_rects):
            if rect.collidepoint(position):
                option = self.blind_options[index]
                self.context["selected_blind"] = option
                if option.is_boss:
                    self.message = f"Seleccionada: {option.name} — {option.description}"
                else:
                    self.message = f"Seleccionada: {option.name}"
                return None

        if self.continue_rect.collidepoint(position):
            return self._continue_to_play()
        return None

    def _buy_offer(self, slot: int) -> None:
        """Purchase one Joker offer when money and capacity permit it."""
        if slot >= len(self.offers):
            return
        if len(self.jokers) >= self.MAX_JOKERS:
            self.message = "No puedes llevar más de 5 Jokers"
            return

        offer = self.offers[slot]
        if self.money < offer.price:
            self.message = f"Dinero insuficiente: necesitas ${offer.price}"
            return

        self.context["money"] = self.money - offer.price
        self.jokers.append(offer.joker)
        self.offers.pop(slot)
        self._reindex_offers()
        self.message = f"Compraste {offer.joker.name} por ${offer.price}"

    def _sell_selected(self) -> None:
        """Sell the selected Joker for approximately half its purchase price."""
        index = self.selected_owned_index
        if index is None or index >= len(self.jokers):
            self.message = "Selecciona un Joker para venderlo"
            return

        joker = self.jokers.pop(index)
        purchase_price = int(getattr(joker, "shop_price", 4))
        sell_value = max(1, purchase_price // 2)
        self.context["money"] = self.money + sell_value
        self.selected_owned_index = None
        self.message = f"Vendiste {joker.name} por ${sell_value}"

    def _reroll(self) -> None:
        """Regenerate the two offers and charge the reroll cost."""
        if self.money < self.REROLL_COST:
            self.message = f"Necesitas ${self.REROLL_COST} para rerrollear"
            return
        self.context["money"] = self.money - self.REROLL_COST
        self._generate_offers()
        self.message = f"Rerrolleo realizado por ${self.REROLL_COST}"

    def _reindex_offers(self) -> None:
        """Reassign visual slots after a Joker offer is purchased."""
        self.offers = [
            JokerOffer(offer.joker, offer.price, index)
            for index, offer in enumerate(self.offers)
        ]

    def _continue_to_play(self) -> str:
        """Persist the selected blind and return the PLAY state transition."""
        selected = self.context.get("selected_blind")
        if selected is None:
            selected = self.blind_options[0]

        self.context["selected_blind"] = selected
        self.context["blind_index"] = selected.blind_index
        self.context["ante"] = selected.ante
        self.context["blind_target"] = selected.target
        self.context["blind_name"] = selected.name
        self.context["blind_is_boss"] = selected.is_boss
        self.context["active_boss"] = selected.boss if selected.is_boss else self.context.get("active_boss")
        self.context["boss_effect_id"] = selected.boss.effect_id if selected.boss else None
        self.context["boss_description"] = selected.description if selected.is_boss else ""
        return "PLAY"

    def update(self, dt: float) -> str | None:
        """Keep the store active without extra per-frame logic."""
        return None

    def draw(self, screen: pygame.Surface | None = None) -> None:
        """Draw summary, shop or blind selection screen."""
        target = screen or self.screen
        target.fill((24, 32, 38))
        self._draw_header(target)
        if self.phase == self.SUMMARY:
            self._draw_summary(target)
        elif self.phase == self.SHOP:
            self._draw_shop(target)
        else:
            self._draw_blind_select(target)
        self._draw_message(target)

    def _draw_header(self, screen: pygame.Surface) -> None:
        """Draw the store title and available money."""
        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        money_font = pygame.font.SysFont("Arial", 26, bold=True)
        screen.blit(title_font.render("TIENDA", True, (255, 215, 0)), (50, 35))
        screen.blit(
            money_font.render(f"Dinero: ${self.money}", True, (255, 255, 255)),
            (self.screen.get_width() - 230, 45),
        )

    def _draw_summary(self, screen: pygame.Surface) -> None:
        """Draw the reward summary."""
        reward = self.context.get("round_reward", {})
        font = pygame.font.SysFont("Arial", 30, bold=True)
        small = pygame.font.SysFont("Arial", 24)
        lines = [
            "CIEGA SUPERADA",
            f"Recompensa base: +${reward.get('base', 0)}",
            f"Manos sobrantes: +${reward.get('hands', 0)}",
            f"Descartes sobrantes: +${reward.get('discards', 0)}",
            f"Total ganado: +${reward.get('total', 0)}",
        ]
        for index, line in enumerate(lines):
            use_font = font if index in (0, 4) else small
            surface = use_font.render(line, True, (255, 255, 255))
            screen.blit(
                surface,
                surface.get_rect(center=(self.screen.get_width() // 2, 170 + index * 55)),
            )
        self._draw_button(screen, self.accept_rect, "ACEPTAR")

    def _draw_shop(self, screen: pygame.Surface) -> None:
        """Draw two Joker offers, owned Jokers and shop actions."""
        font = pygame.font.SysFont("Arial", 22, bold=True)
        small = pygame.font.SysFont("Arial", 18)

        for slot, rect in enumerate(self.offer_rects):
            pygame.draw.rect(screen, (60, 60, 85), rect, border_radius=12)
            pygame.draw.rect(screen, (220, 220, 250), rect, width=2, border_radius=12)
            if slot < len(self.offers):
                offer = self.offers[slot]
                description = str(getattr(offer.joker, "description", "Efecto especial"))
                screen.blit(font.render(offer.joker.name, True, (255, 255, 255)), (rect.x + 18, rect.y + 30))
                screen.blit(small.render(description[:24], True, (230, 230, 230)), (rect.x + 18, rect.y + 78))
                screen.blit(small.render(f"Precio: ${offer.price}", True, (255, 215, 0)), (rect.x + 18, rect.y + 155))
            else:
                screen.blit(small.render("Vendido", True, (160, 160, 160)), (rect.x + 70, rect.y + 105))

        screen.blit(font.render("Tus Jokers", True, (255, 255, 255)), (40, 435))
        for index, rect in enumerate(self.owned_rects):
            if index >= len(self.jokers):
                break
            joker = self.jokers[index]
            color = (140, 40, 200) if index == self.selected_owned_index else (60, 60, 85)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            pygame.draw.rect(screen, (220, 220, 250), rect, width=2, border_radius=8)
            screen.blit(small.render(joker.name[:14], True, (255, 255, 255)), (rect.x + 8, rect.y + 22))
            screen.blit(small.render("CLICK para vender", True, (210, 210, 210)), (rect.x + 8, rect.y + 65))

        self._draw_button(screen, self.reroll_rect, f"REROLL ${self.REROLL_COST}")
        self._draw_button(screen, self.sell_rect, "VENDER")
        self._draw_button(screen, self.continue_rect, "CONTINUAR")

    def _draw_blind_select(self, screen: pygame.Surface) -> None:
        """Draw blind names, targets and full boss descriptions before selection."""
        title_font = pygame.font.SysFont("Arial", 22, bold=True)
        body_font = pygame.font.SysFont("Arial", 17)
        target_font = pygame.font.SysFont("Arial", 19, bold=True)
        selected = self.context.get("selected_blind")

        for index, option in enumerate(self.blind_options):
            rect = self.blind_rects[index]
            color = (100, 35, 35) if option.is_boss else (45, 70, 85)
            if selected is option:
                color = (115, 100, 35)

            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, (240, 240, 240), rect, width=2, border_radius=12)
            screen.blit(title_font.render(option.name, True, (255, 255, 255)), (rect.x + 18, rect.y + 25))
            screen.blit(target_font.render(f"Objetivo: {option.target}", True, (230, 230, 230)), (rect.x + 18, rect.y + 70))
            label = "CIEGA JEFE" if option.is_boss else "NORMAL"
            label_color = (255, 190, 190) if option.is_boss else (190, 220, 230)
            screen.blit(body_font.render(label, True, label_color), (rect.x + 18, rect.y + 108))

            description = option.description or ""
            words = description.split()
            line = ""
            line_y = rect.y + 145
            for word in words:
                candidate = f"{line} {word}".strip()
                if body_font.size(candidate)[0] <= rect.width - 36:
                    line = candidate
                else:
                    screen.blit(body_font.render(line, True, (235, 235, 235)), (rect.x + 18, line_y))
                    line = word
                    line_y += 22
            if line and line_y < rect.bottom - 20:
                screen.blit(body_font.render(line, True, (235, 235, 235)), (rect.x + 18, line_y))

        self._draw_button(screen, self.continue_rect, "JUGAR")

    def _draw_message(self, screen: pygame.Surface) -> None:
        """Draw the contextual store message."""
        font = pygame.font.SysFont("Arial", 18)
        surface = font.render(self.message, True, (225, 225, 225))
        screen.blit(surface, (50, self.screen.get_height() - 30))

    @staticmethod
    def _draw_button(screen: pygame.Surface, rect: pygame.Rect, text: str) -> None:
        """Draw a reusable centered-label button."""
        pygame.draw.rect(screen, (55, 55, 70), rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=8)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, surface.get_rect(center=rect.center))
