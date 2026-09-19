"""Tienda y secuencia lineal de ciegas.

La tienda mantiene la lógica de compra/venta de Jokers, pero la selección de
ciegas dejó de ser ramificada: la partida avanza estrictamente
Pequeña -> Grande -> Jefe. Las ciegas Pequeña y Grande pueden saltarse;
la Ciega Jefe siempre debe jugarse.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import random

import pygame

from entities import Joker, ALL_JOKERS
from states.base_state import BaseState
from systems.assets import AssetResolver
from systems.bosses import BossBlind, get_random_boss_instance
from systems.joker_catalog import metadata_for


@dataclass(frozen=True)
class JokerOffer:
    joker: Joker
    price: int
    slot: int


@dataclass(frozen=True)
class BlindOption:
    name: str
    target: int
    ante: int
    blind_index: int
    is_boss: bool = False
    description: str = ""
    boss: BossBlind | None = None


class StoreState(BaseState):
    SUMMARY = "SUMMARY"
    SHOP = "SHOP"
    BLIND_SELECT = "BLIND_SELECT"

    MAX_JOKERS = 5
    REROLL_COST = 5
    BASE_BLIND_TARGET = 300
    BLIND_STEP = 200

    def __init__(self, screen: pygame.Surface, context: dict[str, Any] | None = None) -> None:
        super().__init__()
        self.screen = screen
        self.context = context if context is not None else {}
        self.asset_resolver = AssetResolver(self._project_root())
        self.phase = self.SUMMARY
        self.message = ""
        self.selected_owned_index: int | None = None
        self.offers: list[JokerOffer] = []
        self.blind_options: list[BlindOption] = []
        self.offer_rects: list[pygame.Rect] = []
        self.owned_rects: list[pygame.Rect] = []
        self.blind_rects: list[pygame.Rect] = []
        self._shop_hovered_offer: int | None = None
        self._shop_hovered_owned: int | None = None
        self._scene_cache: dict[str, pygame.Surface] = {}
        self._prepare_persistent_values()
        self._build_buttons()

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parent.parent

    def _prepare_persistent_values(self) -> None:
        self.context.setdefault("money", 0)
        self.context.setdefault("jokers", [])
        self.context.setdefault("ante", 1)
        self.context.setdefault("blind_index", 0)
        self.context.setdefault("selected_blind", None)
        self.context.setdefault("blind_target", self.BASE_BLIND_TARGET)
        self.context.setdefault("blind_name", "Ciega pequeña")
        self.context.setdefault("blind_is_boss", False)
        self.context.setdefault("active_boss", None)
        self.context.setdefault("active_boss_ante", None)
        self.context.setdefault("seen_boss_ids", set())
        self.context.setdefault("previous_blind_played_card_codes", set())
        self.context.setdefault("total_discards", 0)
        self.context.setdefault("bosses_defeated", 0)
        self.context.setdefault("total_score", 0)
        self.context.setdefault(
            "round_reward",
            {"base": 0, "hands": 0, "discards": 0, "economy": 0, "total": 0},
        )

    @property
    def money(self) -> int:
        return int(self.context.get("money", 0))

    @property
    def jokers(self) -> list[Joker]:
        return self.context.setdefault("jokers", [])

    @property
    def next_blind(self) -> BlindOption | None:
        return self.blind_options[0] if self.blind_options else None

    def enter(self) -> None:
        self.phase = self.SUMMARY
        self.selected_owned_index = None
        self._shop_hovered_offer = None
        self._shop_hovered_owned = None
        self.context["selected_blind"] = None
        self._ensure_active_boss_for_current_ante()
        self._generate_offers()
        self._generate_next_blind()
        self._build_buttons()

    def exit(self) -> None:
        self.selected_owned_index = None
        self._shop_hovered_offer = None
        self._shop_hovered_owned = None

    # ------------------------------------------------------------------
    # Ciegas
    # ------------------------------------------------------------------
    def _ensure_active_boss_for_current_ante(self) -> BossBlind:
        """Devuelve el jefe del Ante actual y lo conserva hasta derrotarlo."""
        ante = max(1, int(self.context.get("ante", 1)))
        current = self.context.get("active_boss")
        stored_ante = self.context.get("active_boss_ante")
        if current is None or stored_ante != ante:
            seen = self.context.setdefault("seen_boss_ids", set())
            current = get_random_boss_instance(seen)
            self.context["active_boss"] = current
            self.context["active_boss_ante"] = ante
        return current

    @classmethod
    def blind_target(cls, ante: int, local_index: int) -> int:
        """300, 500, 700 para el Ante 1; +600 al iniciar cada nuevo Ante."""
        absolute_index = max(0, ante - 1) * 3 + local_index
        return cls.BASE_BLIND_TARGET + cls.BLIND_STEP * absolute_index

    def _boss_target(self, boss: BossBlind, ante: int) -> int:
        """Aplica únicamente los modificadores especiales ya definidos por cada jefe."""
        baseline = self.blind_target(ante, 2)
        if boss.effect_id == "wall":
            return baseline * 2
        if boss.effect_id == "needle":
            return int(baseline * 0.6)
        return baseline

    def _generate_next_blind(self) -> None:
        """Genera una sola opción: la siguiente ciega obligatoria del flujo."""
        ante = max(1, int(self.context.get("ante", 1)))
        next_index = int(self.context.get("blind_index", 0))
        boss = self._ensure_active_boss_for_current_ante()

        if next_index <= 0:
            option = BlindOption(
                "Ciega pequeña",
                self.blind_target(ante, 0),
                ante,
                0,
                False,
                "La primera ciega del Ante. Puedes jugarla o saltarla.",
            )
        elif next_index == 1:
            option = BlindOption(
                "Ciega grande",
                self.blind_target(ante, 1),
                ante,
                1,
                False,
                "La segunda ciega del Ante. Puedes jugarla o saltarla.",
            )
        else:
            option = BlindOption(
                boss.name,
                self._boss_target(boss, ante),
                ante,
                2,
                True,
                boss.description,
                boss,
            )

        self.blind_options = [option]
        self.context["selected_blind"] = option
        self.context["blind_target_preview"] = option.target

    def _select_next_blind(self) -> None:
        """Marca la única ciega disponible como seleccionada."""
        option = self.next_blind
        if option is None:
            return
        self.context["selected_blind"] = option
        self.message = f"Seleccionada: {option.name}"

    def _skip_next_blind(self) -> None:
        """Salta la ciega actual y muestra inmediatamente la siguiente.

        La ciega jefe nunca puede saltarse. No se consumen recompensas porque la
        ciega todavía no se ha jugado.
        """
        option = self.next_blind
        if option is None:
            return
        if option.is_boss:
            self.message = "La Ciega Jefe no se puede saltar"
            return

        skipped_index = option.blind_index
        self.context["blind_index"] = min(2, skipped_index + 1)
        self.context["selected_blind"] = None
        self._generate_next_blind()
        self._build_buttons()
        if self.next_blind is not None:
            self.message = f"Saltaste {option.name}. Ahora debes decidir sobre {self.next_blind.name}."

    # ------------------------------------------------------------------
    # Tienda de Jokers
    # ------------------------------------------------------------------
    def _generate_offers(self) -> None:
        owned_names = {type(joker).__name__ for joker in self.jokers}
        candidates = [cls for cls in ALL_JOKERS if cls.__name__ not in owned_names]
        if not candidates:
            candidates = list(ALL_JOKERS)

        self.offers = []
        for slot in range(2):
            cls = random.choice(candidates)
            candidates = [item for item in candidates if item is not cls] or list(ALL_JOKERS)
            joker = cls()
            price = metadata_for(cls.__name__).price
            joker.set_shop_price(price)
            self.offers.append(JokerOffer(joker, price, slot))
        self._build_offer_rects()

    def _build_offer_rects(self) -> None:
        """Prepara las zonas de interacción de las dos ofertas sobre la mesa."""
        centers = (300, 620)
        self.offer_rects = []
        for slot, offer in enumerate(self.offers[:2]):
            path = str(getattr(offer.joker, "asset_path", ""))
            rect = pygame.Rect(0, 0, 190, 190)
            if path:
                try:
                    image = pygame.image.load(path).convert_alpha()
                    fitted = self._fit_joker_surface(image, (190, 190), min_size=150)
                    rect = fitted.get_rect(center=(centers[slot], 292))
                except Exception:
                    rect.center = (centers[slot], 292)
            else:
                rect.center = (centers[slot], 292)
            self.offer_rects.append(rect)

    @staticmethod
    def _fit_joker_surface(surface: pygame.Surface, max_size: tuple[int, int], min_size: int = 150) -> pygame.Surface:
        """Escala un asset de Joker conservando proporción y evitando previews diminutas."""
        width, height = surface.get_size()
        if width <= 0 or height <= 0:
            return surface
        max_w, max_h = max_size
        scale = min(max_w / width, max_h / height)
        target_w = max(1, int(width * scale))
        target_h = max(1, int(height * scale))

        # Los PNG pequeños se amplían hasta un tamaño visual equilibrado,
        # siempre conservando la relación de aspecto.
        if max(target_w, target_h) < min_size:
            upscale = min_size / max(target_w, target_h)
            target_w = int(target_w * upscale)
            target_h = int(target_h * upscale)

        return pygame.transform.smoothscale(surface, (target_w, target_h))

    # ------------------------------------------------------------------
    # Botones / eventos
    # ------------------------------------------------------------------
    def _build_buttons(self) -> None:
        width = self.screen.get_width()
        height = self.screen.get_height()

        # Panel de Jokers disponibles: mesa superior izquierda.
        self.available_panel = pygame.Rect(35, 100, 850, 320)
        self.reroll_rect = pygame.Rect(920, 135, 300, 60)

        # Panel de Jokers que ya pertenecen al jugador.
        self.hand_panel = pygame.Rect(35, 440, 850, 205)
        self.owned_rects = [
            pygame.Rect(52 + index * 164, 485, 150, 145)
            for index in range(self.MAX_JOKERS)
        ]

        # Acciones de la tienda agrupadas a la derecha.
        self.sell_rect = pygame.Rect(920, 485, 300, 55)
        self.continue_rect = pygame.Rect(920, 560, 300, 55)
        self.accept_rect = pygame.Rect(width // 2 - 110, height - 90, 220, 50)

        # Selección de la siguiente ciega.
        self.skip_blind_rect = pygame.Rect(width // 2 + 140, height - 90, 190, 50)
        self.blind_rects = [pygame.Rect(width // 2 - 210, 170, 420, 275)]
        self._build_offer_rects()

    def handle_events(self, events: list[pygame.event.Event]) -> str | None:
        mouse_pos = pygame.mouse.get_pos()
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if self.phase == self.SHOP:
                    self._shop_hovered_offer = self._offer_index_at(event.pos)
                    self._shop_hovered_owned = self._owned_index_at(event.pos)
                else:
                    self._shop_hovered_offer = None
                    self._shop_hovered_owned = None

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

        if self.phase != self.SHOP:
            self._shop_hovered_offer = None
            self._shop_hovered_owned = None
        else:
            self._shop_hovered_offer = self._offer_index_at(mouse_pos)
            self._shop_hovered_owned = self._owned_index_at(mouse_pos)
        return None

    def _activate_primary_action(self) -> str | None:
        if self.phase == self.SUMMARY:
            self.phase = self.SHOP
            self.message = "Compra, vende o rerrollea Jokers"
            return None
        if self.phase == self.SHOP:
            self.phase = self.BLIND_SELECT
            self.message = f"Siguiente ciega: {self.next_blind.name if self.next_blind else 'Ninguna'}"
            self._build_buttons()
            return None
        self._select_next_blind()
        return self._continue_to_play()

    def _handle_mouse_click(self, position: tuple[int, int]) -> str | None:
        if self.phase == self.SUMMARY:
            if self.accept_rect.collidepoint(position):
                self.phase = self.SHOP
                self.message = "Compra, vende o rerrollea Jokers"
            return None

        if self.phase == self.SHOP:
            offer_index = self._offer_index_at(position)
            if offer_index is not None:
                self._buy_offer(offer_index)
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
                self.message = f"Siguiente ciega: {self.next_blind.name if self.next_blind else 'Ninguna'}"
                self._build_buttons()
            return None

        # BLIND_SELECT: solo existe una ciega disponible.
        if self.blind_rects[0].collidepoint(position):
            self._select_next_blind()
        elif self.skip_blind_rect.collidepoint(position) and self.next_blind and not self.next_blind.is_boss:
            self._skip_next_blind()
        elif self.continue_rect.collidepoint(position):
            return self._continue_to_play()
        return None

    def _offer_index_at(self, position: tuple[int, int]) -> int | None:
        for index, rect in enumerate(self.offer_rects):
            if index < len(self.offers) and rect.collidepoint(position):
                return index
        return None

    def _owned_index_at(self, position: tuple[int, int]) -> int | None:
        for index, rect in enumerate(self.owned_rects):
            if index < len(self.jokers) and rect.collidepoint(position):
                return index
        return None

    def _buy_offer(self, slot: int) -> None:
        if slot >= len(self.offers):
            return
        if len(self.jokers) >= self.MAX_JOKERS:
            self.message = "No puedes llevar más de 5 Jokers"
            return

        offer = self.offers[slot]
        debt_limit = 0
        for joker in self.jokers:
            getter = getattr(joker, "get_max_debt_limit", None)
            if getter:
                debt_limit = max(debt_limit, int(getter()))

        if self.money - offer.price < -debt_limit:
            self.message = f"Dinero insuficiente: necesitas ${offer.price}"
            return

        self.context["money"] = self.money - offer.price
        self.jokers.append(offer.joker)
        self.offers.pop(slot)
        self._reindex_offers()
        self.message = f"Compraste {offer.joker.name} por ${offer.price}"

    def _sell_selected(self) -> None:
        index = self.selected_owned_index
        if index is None or index >= len(self.jokers):
            self.message = "Selecciona un Joker para venderlo"
            return
        joker = self.jokers.pop(index)
        sell_value = int(getattr(joker, "sell_price", max(1, int(getattr(joker, "shop_price", 4)) // 2)))
        self.context["money"] = self.money + sell_value
        self.selected_owned_index = None
        self.message = f"Vendiste {joker.name} por ${sell_value}"

    def _reroll(self) -> None:
        if self.money < self.REROLL_COST:
            self.message = f"Necesitas ${self.REROLL_COST} para rerrollear"
            return
        self.context["money"] = self.money - self.REROLL_COST
        self._generate_offers()
        self.message = f"Rerrolleo realizado por ${self.REROLL_COST}"

    def _reindex_offers(self) -> None:
        self.offers = [JokerOffer(offer.joker, offer.price, index) for index, offer in enumerate(self.offers)]
        self._build_offer_rects()

    def _continue_to_play(self) -> str:
        """Confirma exclusivamente la siguiente ciega del flujo."""
        selected = self.next_blind
        if selected is None:
            return "MENU"

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

    # ------------------------------------------------------------------
    # Dibujado
    # ------------------------------------------------------------------
    def _build_scene_background(self, mode: str) -> pygame.Surface:
        """Crea un fondo decorativo coherente con la paleta oscura, teal, púrpura y dorada."""
        if mode in self._scene_cache:
            return self._scene_cache[mode]

        surface = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        width, height = surface.get_size()
        if mode == "BLIND_SELECT":
            top = (27, 25, 38)
            bottom = (49, 28, 36) if (self.next_blind and self.next_blind.is_boss) else (24, 52, 59)
        else:
            top = (22, 29, 42)
            bottom = (34, 50, 54)

        for y in range(height):
            t = y / max(1, height - 1)
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            pygame.draw.line(surface, color, (0, y), (width, y))

        deco = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.circle(deco, (221, 176, 77, 24), (width - 70, 80), 160)
        pygame.draw.circle(deco, (117, 74, 150, 22), (90, height - 60), 190)
        pygame.draw.rect(deco, (255, 255, 255, 10), (18, 18, width - 36, height - 36), width=2, border_radius=24)
        suit_font = pygame.font.SysFont("Arial", 110, bold=True)
        suits = [("♠", 100, 95), ("♥", width - 130, height - 100), ("♦", width - 135, 90), ("♣", 110, height - 105)]
        for glyph, x, y in suits:
            color = (255, 220, 150, 22) if glyph in ("♦", "♥") else (160, 205, 214, 18)
            deco.blit(suit_font.render(glyph, True, color), (x, y))
        surface.blit(deco, (0, 0))
        self._scene_cache[mode] = surface
        return surface

    def draw(self, screen: pygame.Surface | None = None) -> None:
        target = screen or self.screen
        target.blit(self._build_scene_background(self.phase), (0, 0))
        self._draw_header(target)
        if self.phase == self.SUMMARY:
            self._draw_summary(target)
        elif self.phase == self.SHOP:
            self._draw_shop(target)
        else:
            self._draw_blind_select(target)
        self._draw_message(target)

    def _draw_header(self, screen) -> None:
        title_font = pygame.font.SysFont("Arial", 42, bold=True)
        money_font = pygame.font.SysFont("Arial", 26, bold=True)
        screen.blit(title_font.render("TIENDA", True, (255, 221, 115)), (50, 35))
        screen.blit(
            money_font.render(f"Dinero: ${self.money}", True, (255, 255, 255)),
            (self.screen.get_width() - 230, 45),
        )

    def _draw_summary(self, screen) -> None:
        reward = self.context.get("round_reward", {})
        font = pygame.font.SysFont("Arial", 28, bold=True)
        small = pygame.font.SysFont("Arial", 22)
        lines = [
            "CIEGA SUPERADA",
            f"Recompensa base: +${reward.get('base', 0)}",
            f"Manos sobrantes: +${reward.get('hands', 0)}",
            f"Descartes sobrantes: +${reward.get('discards', 0)}",
            f"Bonos económicos: +${reward.get('economy', 0)}",
            f"Total ganado: +${reward.get('total', 0)}",
        ]
        for index, line in enumerate(lines):
            surface = (font if index in (0, len(lines) - 1) else small).render(line, True, (255, 255, 255))
            screen.blit(surface, surface.get_rect(center=(self.screen.get_width() // 2, 145 + index * 50)))
        self._draw_button(screen, self.accept_rect, "ACEPTAR")

    def _load_offer_surface(self, joker: Joker) -> pygame.Surface | None:
        path = str(getattr(joker, "asset_path", ""))
        if not path:
            return None
        try:
            # Se conserva el tamaño original del PNG: no se estira ni se convierte
            # en un cuadrado artificial.
            return pygame.image.load(path).convert_alpha()
        except Exception:
            return None

    def _draw_joker_offer(self, screen, joker: Joker, slot: int, hovered: bool = False) -> None:
        surface = self._load_offer_surface(joker)
        rect = self.offer_rects[slot] if slot < len(self.offer_rects) else pygame.Rect(0, 0, 190, 190)
        if surface is None:
            font = pygame.font.SysFont("Arial", 19, bold=True)
            text = font.render(joker.name, True, (230, 230, 230))
            screen.blit(text, text.get_rect(center=rect.center))
            return

        surface = self._fit_joker_surface(surface, (190, 190), min_size=150)
        draw_rect = surface.get_rect(center=rect.center)
        if hovered:
            pygame.draw.circle(screen, (190, 160, 40), draw_rect.center, max(draw_rect.width, draw_rect.height) // 2 + 8, width=3)
        screen.blit(surface, draw_rect)
        self.offer_rects[slot] = draw_rect

    def _draw_shop(self, screen) -> None:
        title_font = pygame.font.SysFont("Arial", 24, bold=True)
        subtitle_font = pygame.font.SysFont("Arial", 16, bold=True)

        # Mesa de ofertas disponibles.
        pygame.draw.rect(screen, (29, 50, 55), self.available_panel, border_radius=16)
        pygame.draw.rect(screen, (108, 154, 155), self.available_panel, width=2, border_radius=16)
        screen.blit(title_font.render("DISPONIBLES", True, (255, 255, 255)), (self.available_panel.x + 22, self.available_panel.y + 16))
        screen.blit(subtitle_font.render("Pasa el cursor sobre un Joker para ver su información", True, (185, 200, 198)), (self.available_panel.x + 22, self.available_panel.y + 48))

        for slot, offer in enumerate(self.offers[:2]):
            self._draw_joker_offer(
                screen,
                offer.joker,
                slot,
                hovered=(slot == self._shop_hovered_offer),
            )

        # Reroll junto al panel de disponibles.
        self._draw_button(screen, self.reroll_rect, f"REROLL ${self.REROLL_COST}")

        # Mesa de Jokers del jugador.
        pygame.draw.rect(screen, (40, 34, 58), self.hand_panel, border_radius=16)
        pygame.draw.rect(screen, (132, 111, 170), self.hand_panel, width=2, border_radius=16)
        screen.blit(title_font.render("EN MANO", True, (255, 255, 255)), (self.hand_panel.x + 22, self.hand_panel.y + 14))
        count_text = subtitle_font.render(f"{len(self.jokers)}/{self.MAX_JOKERS}", True, (230, 215, 165))
        screen.blit(count_text, (self.hand_panel.right - count_text.get_width() - 22, self.hand_panel.y + 18))

        for index, rect in enumerate(self.owned_rects):
            if index >= len(self.jokers):
                pygame.draw.rect(screen, (24, 28, 40), rect, border_radius=10)
                pygame.draw.rect(screen, (90, 100, 120), rect, width=1, border_radius=10)
                continue
            self._draw_owned_joker(
                screen,
                self.jokers[index],
                rect,
                selected=(index == self.selected_owned_index),
                hovered=(index == self._shop_hovered_owned),
            )

        self._draw_button(screen, self.sell_rect, "VENDER")
        self._draw_button(screen, self.continue_rect, "CONTINUAR")

        if self._shop_hovered_offer is not None and self._shop_hovered_offer < len(self.offers):
            self._draw_offer_tooltip(screen, self.offers[self._shop_hovered_offer].joker)
        elif self._shop_hovered_owned is not None and self._shop_hovered_owned < len(self.jokers):
            self._draw_offer_tooltip(screen, self.jokers[self._shop_hovered_owned], owned=True)

    def _draw_owned_joker(self, screen, joker: Joker, rect: pygame.Rect, selected: bool, hovered: bool = False) -> None:
        border = (255, 215, 80) if selected else ((180, 160, 50) if hovered else (120, 130, 155))
        pygame.draw.rect(screen, (18, 21, 31), rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, width=3 if (selected or hovered) else 2, border_radius=10)
        path = str(getattr(joker, "asset_path", ""))
        try:
            image = pygame.image.load(path).convert_alpha()
            preview = self._fit_joker_surface(image, (108, 108), min_size=92)
            screen.blit(preview, preview.get_rect(center=(rect.centerx, rect.y + 66)))
        except Exception:
            pass
        small = pygame.font.SysFont("Arial", 12, bold=True)
        screen.blit(small.render(joker.name[:19], True, (255, 255, 255)), (rect.x + 8, rect.bottom - 29))
        price = small.render(f"Venta: ${getattr(joker, 'sell_price', 1)}", True, (125, 220, 150))
        screen.blit(price, (rect.x + 8, rect.bottom - 15))

    def _draw_offer_tooltip(self, screen, joker: Joker, owned: bool = False) -> None:
        body_font = pygame.font.SysFont("Arial", 16)
        title_font = pygame.font.SysFont("Arial", 22, bold=True)
        small_font = pygame.font.SysFont("Arial", 15, bold=True)
        max_width = min(440, screen.get_width() - 30)
        description = str(getattr(joker, "description", "Efecto especial"))
        lines = self._wrap(description, body_font, max_width - 30)
        height = 102 + len(lines) * 21
        panel = pygame.Surface((max_width, height), pygame.SRCALPHA)
        panel.fill((10, 14, 20, 245))
        pygame.draw.rect(panel, (235, 235, 245, 255), panel.get_rect(), width=2, border_radius=10)
        panel.blit(title_font.render(str(joker.name), True, (255, 215, 80)), (15, 10))
        panel.blit(small_font.render(f"Rareza: {getattr(joker, 'rarity', 'Común')}", True, (225, 225, 240)), (15, 40))
        if owned:
            price_text = f"Venta: ${getattr(joker, 'sell_price', 1)}"
        else:
            price_text = f"Compra: ${getattr(joker, 'shop_price', 1)}  |  Venta: ${getattr(joker, 'sell_price', 1)}"
        panel.blit(small_font.render(price_text, True, (120, 225, 155)), (15, 62))
        y = 86
        for line in lines:
            panel.blit(body_font.render(line, True, (255, 255, 255)), (15, y))
            y += 21

        mouse = pygame.mouse.get_pos()
        panel_rect = panel.get_rect()
        panel_rect.centerx = max(panel_rect.width // 2 + 10, min(screen.get_width() - panel_rect.width // 2 - 10, mouse[0]))
        panel_rect.top = min(screen.get_height() - panel_rect.height - 10, max(10, mouse[1] - panel_rect.height - 18))
        screen.blit(panel, panel_rect)

    def _draw_blind_select(self, screen) -> None:
        option = self.next_blind
        if option is None:
            return

        title_font = pygame.font.SysFont("Arial", 30, bold=True)
        body_font = pygame.font.SysFont("Arial", 18)
        target_font = pygame.font.SysFont("Arial", 22, bold=True)
        label = "CIEGA JEFE" if option.is_boss else "SIGUIENTE CIEGA"
        label_color = (255, 175, 175) if option.is_boss else (190, 220, 230)

        rect = self.blind_rects[0]
        color = (88, 34, 43) if option.is_boss else (38, 77, 86)
        selected = self.context.get("selected_blind") is option
        if selected:
            color = (105, 82, 38)

        pygame.draw.rect(screen, color, rect, border_radius=14)
        pygame.draw.rect(screen, (236, 212, 153) if option.is_boss else (137, 182, 186), rect, width=2, border_radius=14)
        accent = pygame.Rect(rect.x + 8, rect.y + 8, 7, rect.height - 16)
        pygame.draw.rect(screen, (224, 84, 88) if option.is_boss else (80, 184, 173), accent, border_radius=4)
        screen.blit(title_font.render(option.name, True, (255, 255, 255)), (rect.x + 22, rect.y + 26))
        screen.blit(target_font.render(f"Objetivo: {option.target}", True, (235, 235, 235)), (rect.x + 22, rect.y + 82))
        screen.blit(body_font.render(label, True, label_color), (rect.x + 22, rect.y + 124))

        y = rect.y + 160
        for line in self._wrap(option.description, body_font, rect.width - 44):
            screen.blit(body_font.render(line, True, (235, 235, 235)), (rect.x + 22, y))
            y += 22

        # Una sola ciega existe aquí. Nunca se puede elegir otra.
        self._draw_button(screen, self.continue_rect, "JUGAR CIEGA")
        if option.is_boss:
            # No existe botón de salto para una Ciega Jefe.
            warning = body_font.render("La Ciega Jefe es obligatoria", True, (255, 205, 120))
            screen.blit(warning, warning.get_rect(center=(self.screen.get_width() // 2 + 140, self.screen.get_height() - 102)))
        else:
            self._draw_button(screen, self.skip_blind_rect, "SALTAR CIEGA")

    @staticmethod
    def _wrap(text: str, font, width: int) -> list[str]:
        lines, current = [], ""
        for word in str(text).split():
            candidate = f"{current} {word}".strip()
            if current and font.size(candidate)[0] > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines

    def _draw_message(self, screen) -> None:
        font = pygame.font.SysFont("Arial", 17)
        screen.blit(
            font.render(self.message, True, (225, 225, 225)),
            (50, self.screen.get_height() - 30),
        )

    @staticmethod
    def _draw_button(screen, rect, text):
        pygame.draw.rect(screen, (55, 55, 70), rect, border_radius=8)
        pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=8)
        font = pygame.font.SysFont("Arial", 18, bold=True)
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, surface.get_rect(center=rect.center))
