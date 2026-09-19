"""Renderer centralizado de mesa, cartas, Jokers, ciegas y controles."""
from __future__ import annotations

import pygame

COLOR_BG = (24, 32, 38)
COLOR_PANEL_BG = (15, 20, 25)
COLOR_CARD_BG = (240, 240, 240)
COLOR_CARD_BORDER = (180, 50, 50)
COLOR_SELECTED = (255, 215, 0)
COLOR_JOKER_BG = (60, 60, 85)
COLOR_JOKER_ACTIVE = (140, 40, 200)
COLOR_TEXT_MAIN = (255, 255, 255)
COLOR_TEXT_DARK = (20, 20, 20)
COLOR_CHIPS = (80, 160, 255)
COLOR_MULT = (255, 80, 80)


def _wrap_text(font, text: str, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if current and font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def draw_joker_tooltip(screen, joker_data, mouse_pos=None):
    """Muestra nombre, rareza, efecto y precio de venta del Joker bajo el mouse."""
    if not joker_data:
        return
    if isinstance(joker_data, dict):
        name = joker_data.get("name", "Joker")
        description = joker_data.get("description", "Efecto especial")
        rarity = joker_data.get("rarity", "Común")
        sell_price = joker_data.get("sell_price", 1)
    else:
        name = getattr(joker_data, "name", "Joker")
        description = getattr(joker_data, "description", "Efecto especial")
        rarity = getattr(joker_data, "rarity", "Común")
        sell_price = getattr(joker_data, "sell_price", 1)

    title_font = pygame.font.SysFont("Arial", 24, bold=True)
    body_font = pygame.font.SysFont("Arial", 17)
    small_font = pygame.font.SysFont("Arial", 16, bold=True)
    max_width = min(470, screen.get_width() - 40)
    lines = _wrap_text(body_font, description, max_width - 35)
    height = 26 + 24 + 24 + len(lines) * 22 + 22
    panel = pygame.Surface((max_width, height), pygame.SRCALPHA)
    panel.fill((10, 14, 20, 245))
    pygame.draw.rect(panel, (220, 220, 250, 255), panel.get_rect(), width=2, border_radius=10)
    panel.blit(title_font.render(str(name), True, (255, 215, 0)), (18, 12))
    panel.blit(small_font.render(f"Rareza: {rarity}", True, (225, 225, 240)), (18, 39))
    panel.blit(small_font.render(f"Venta: ${sell_price}", True, (110, 220, 140)), (18, 61))
    y = 88
    for line in lines:
        panel.blit(body_font.render(line, True, COLOR_TEXT_MAIN), (18, y))
        y += 22

    if mouse_pos:
        panel_rect = panel.get_rect()
        panel_rect.centerx = max(panel_rect.width // 2 + 10, min(screen.get_width() - panel_rect.width // 2 - 10, mouse_pos[0]))
        panel_rect.top = min(screen.get_height() - panel_rect.height - 10, max(10, mouse_pos[1] - panel_rect.height - 18))
    else:
        panel_rect = panel.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(panel, panel_rect)


class Renderer:
    """Dibuja la mesa manteniendo posiciones compartidas con PlayState."""

    JOKER_START_X = 300
    JOKER_Y = 55
    JOKER_SLOT_W = 112
    JOKER_SLOT_H = 112
    JOKER_GAP = 12
    BLIND_RECT = pygame.Rect(955, 55, 315, 255)
    POKER_BUTTON_H = 38
    CONTROL_Y_FROM_BOTTOM = 112
    HAND_Y_FROM_BOTTOM = 285

    def __init__(self, screen_width=1280, screen_height=720, screen=None):
        pygame.font.init()
        self.width = screen_width
        self.height = screen_height
        self.screen = screen if screen is not None else pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Mesa de Juego - Estilo Balatro")
        self.font_main = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 34, bold=True)
        self._card_surface_cache: dict[str, pygame.Surface | None] = {}
        self._card_text_cache: dict[tuple, pygame.Surface] = {}
        self._joker_surface_cache: dict[str, pygame.Surface | None] = {}
        self.hand_y = max(340, self.height - self.HAND_Y_FROM_BOTTOM)

    def clear(self):
        self.screen.fill(COLOR_BG)

    def draw_card(self, card_data, x, y, scale=1.0, is_selected=False):
        base_w, base_h = 90, 130
        w, h = int(base_w * scale), int(base_h * scale)
        draw_y = int(y - 20 if is_selected else y)
        rect = pygame.Rect(int(x), draw_y, w, h)
        pygame.draw.rect(self.screen, (8, 8, 12), rect.move(3, 4), border_radius=8)
        asset_path = str(card_data.get("asset_path", "")).strip()
        if asset_path:
            surface = self._card_surface_cache.get(asset_path)
            if surface is None and asset_path not in self._card_surface_cache:
                try:
                    surface = pygame.image.load(asset_path).convert_alpha()
                except Exception:
                    surface = None
                self._card_surface_cache[asset_path] = surface
            if surface is not None:
                self.screen.blit(pygame.transform.smoothscale(surface, (w, h)), rect)
                if is_selected:
                    pygame.draw.rect(self.screen, COLOR_SELECTED, rect, width=3, border_radius=8)
                return

        pygame.draw.rect(self.screen, COLOR_CARD_BG, rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_SELECTED if is_selected else COLOR_CARD_BORDER, rect, width=3, border_radius=8)
        key = (card_data.get("rank", ""), card_data.get("suit", ""))
        if key not in self._card_text_cache:
            self._card_text_cache[key] = self.font_main.render(f"{key[0]}{key[1]}", True, COLOR_TEXT_DARK)
        self.screen.blit(self._card_text_cache[key], (rect.x + 8, rect.y + 8))

    def _load_joker_surface(self, path: str, size: tuple[int, int]) -> pygame.Surface | None:
        if not path:
            return None
        surface = self._joker_surface_cache.get(path)
        if surface is None and path not in self._joker_surface_cache:
            try:
                surface = pygame.image.load(path).convert_alpha()
            except Exception:
                surface = None
            self._joker_surface_cache[path] = surface
        if surface is None:
            return None
        return pygame.transform.smoothscale(surface, size)

    @classmethod
    def joker_rect(cls, index: int) -> pygame.Rect:
        x = cls.JOKER_START_X + index * (cls.JOKER_SLOT_W + cls.JOKER_GAP)
        return pygame.Rect(x, cls.JOKER_Y, cls.JOKER_SLOT_W, cls.JOKER_SLOT_H)

    def draw_joker(self, joker_data, index: int, hovered=False, dragging=False):
        rect = self.joker_rect(index)
        active = joker_data.get("active", True) if isinstance(joker_data, dict) else getattr(joker_data, "active", True)
        asset_path = joker_data.get("asset_path", "") if isinstance(joker_data, dict) else getattr(joker_data, "asset_path", "")
        bg = COLOR_JOKER_ACTIVE if active else (70, 70, 70)
        if hovered or dragging:
            bg = (180, 145, 30) if active else (110, 100, 40)
        pygame.draw.rect(self.screen, (8, 8, 14), rect.move(2, 3), border_radius=10)
        pygame.draw.rect(self.screen, bg, rect, border_radius=10)
        pygame.draw.rect(self.screen, (230, 230, 245), rect, width=2, border_radius=10)
        surface = self._load_joker_surface(asset_path, (86, 74))
        if surface is not None:
            self.screen.blit(surface, surface.get_rect(midtop=(rect.centerx, rect.y + 6)))
        name = (joker_data.get("name", "Joker") if isinstance(joker_data, dict) else getattr(joker_data, "name", "Joker"))
        font = pygame.font.SysFont("Arial", 13, bold=True)
        text = font.render(str(name)[:17], True, COLOR_TEXT_MAIN)
        self.screen.blit(text, text.get_rect(center=(rect.centerx, rect.bottom - 16)))

    def draw_joker_bar(self, jokers_list, mouse_pos=None, dragging_index=None):
        hovered = None
        hovered_index = None
        for index, joker in enumerate(jokers_list[:5]):
            rect = self.joker_rect(index)
            if mouse_pos is not None and rect.collidepoint(mouse_pos):
                hovered = joker
                hovered_index = index
            self.draw_joker(joker, index, hovered=(index == hovered_index), dragging=(index == dragging_index))
        panel = pygame.Rect(self.JOKER_START_X - 10, self.JOKER_Y - 10, 5 * self.JOKER_SLOT_W + 4 * self.JOKER_GAP + 20, self.JOKER_SLOT_H + 20)
        pygame.draw.rect(self.screen, (10, 12, 20, 210), panel, border_radius=12)
        pygame.draw.rect(self.screen, (220, 220, 240), panel, width=2, border_radius=12)
        # Se dibuja encima del fondo para que los Jokers queden visibles.
        for index, joker in enumerate(jokers_list[:5]):
            self.draw_joker(joker, index, hovered=(index == hovered_index), dragging=(index == dragging_index))
        return hovered, hovered_index

    @classmethod
    def poker_hands_button_rect(cls) -> pygame.Rect:
        """Rect del botón de consulta de manos de póker dentro del panel derecho."""
        rect = cls.BLIND_RECT.copy()
        return pygame.Rect(rect.x + 16, rect.bottom - cls.POKER_BUTTON_H - 12, rect.width - 32, cls.POKER_BUTTON_H)

    @classmethod
    def poker_hands_modal_rect(cls, width: int, height: int) -> pygame.Rect:
        """Rect adaptable del panel modal de ayuda de manos de póker."""
        modal_w = min(width - 70, 1180)
        modal_h = min(height - 55, 635)
        return pygame.Rect((width - modal_w) // 2, (height - modal_h) // 2, modal_w, modal_h)

    def draw_blind_panel(self, blind_name, target, asset_path, is_boss=False, description=""):
        rect = self.BLIND_RECT.copy()
        pygame.draw.rect(self.screen, (20, 22, 30), rect, border_radius=12)
        pygame.draw.rect(self.screen, (205, 100, 100) if is_boss else (180, 180, 210), rect, width=2, border_radius=12)
        if asset_path:
            try:
                surface = pygame.image.load(asset_path).convert_alpha()
                max_side = 112
                sw, sh = surface.get_size()
                scale = min(max_side / max(1, sw), max_side / max(1, sh))
                fitted = pygame.transform.smoothscale(surface, (max(1, int(sw * scale)), max(1, int(sh * scale))))
                self.screen.blit(fitted, fitted.get_rect(center=(rect.x + 66, rect.y + 70)))
            except Exception:
                pass
        font = pygame.font.SysFont("Arial", 16, bold=True)
        small = pygame.font.SysFont("Arial", 14)
        body = pygame.font.SysFont("Arial", 13)
        text_x = rect.x + 135
        self.screen.blit(font.render(str(blind_name)[:24], True, (255, 255, 255)), (text_x, rect.y + 16))
        self.screen.blit(small.render(f"Objetivo: {target}", True, (250, 205, 80)), (text_x, rect.y + 47))
        self.screen.blit(small.render("CIEGA JEFE" if is_boss else "CIEGA", True, (230, 190, 190) if is_boss else (190, 210, 230)), (text_x, rect.y + 73))

        if is_boss and description:
            self.screen.blit(body.render("EFECTO", True, (255, 205, 120)), (rect.x + 16, rect.y + 132))
            effect_lines = _wrap_text(body, description, rect.width - 32)
            y = rect.y + 153
            for line in effect_lines[:4]:
                self.screen.blit(body.render(line, True, (235, 235, 235)), (rect.x + 16, y))
                y += 16

        button_rect = self.poker_hands_button_rect()
        mouse = pygame.mouse.get_pos()
        hovered = button_rect.collidepoint(mouse)
        pygame.draw.rect(self.screen, (91, 73, 112) if hovered else (62, 48, 82), button_rect, border_radius=8)
        pygame.draw.rect(self.screen, (235, 215, 160), button_rect, width=2, border_radius=8)
        button_font = pygame.font.SysFont("Arial", 14, bold=True)
        label = button_font.render("MANOS DE PÓKER", True, (255, 245, 220))
        self.screen.blit(label, label.get_rect(center=button_rect.center))

    def draw_poker_hands_modal(self, examples):
        """Muestra las manos ordenadas de mayor a menor puntaje con ejemplos visuales."""
        rect = self.poker_hands_modal_rect(self.width, self.height)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((5, 8, 16, 185))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((20, 23, 35, 248))
        pygame.draw.rect(panel, (222, 188, 104, 255), panel.get_rect(), width=3, border_radius=16)
        pygame.draw.rect(panel, (64, 76, 100, 255), panel.get_rect().inflate(-8, -8), width=1, border_radius=13)
        self.screen.blit(panel, rect)

        title_font = pygame.font.SysFont("Arial", 30, bold=True)
        subtitle_font = pygame.font.SysFont("Arial", 15)
        title = title_font.render("MANOS DE PÓKER", True, (255, 221, 115))
        self.screen.blit(title, title.get_rect(center=(rect.centerx, rect.y + 30)))
        subtitle = subtitle_font.render("Ordenadas de mayor a menor puntaje base · haz clic fuera o presiona ESC para cerrar", True, (205, 214, 228))
        self.screen.blit(subtitle, subtitle.get_rect(center=(rect.centerx, rect.y + 56)))

        card_scale = 0.40
        box_w = (rect.width - 54) // 3
        box_h = 168
        start_x = rect.x + 15
        start_y = rect.y + 78
        name_font = pygame.font.SysFont("Arial", 17, bold=True)
        score_font = pygame.font.SysFont("Arial", 13, bold=True)

        for index, example in enumerate(examples[:9]):
            row, col = divmod(index, 3)
            box = pygame.Rect(start_x + col * (box_w + 12), start_y + row * (box_h + 10), box_w, box_h)
            pygame.draw.rect(self.screen, (28, 32, 46), box, border_radius=10)
            pygame.draw.rect(self.screen, (94, 105, 132), box, width=1, border_radius=10)

            name = example["name"]
            base_score = example["score"]
            multiplier = example["multiplier"]
            cards = example["cards"]
            self.screen.blit(name_font.render(name, True, (245, 245, 250)), (box.x + 12, box.y + 10))
            score_text = score_font.render(f"Base: {base_score}  ·  Mult: x{multiplier:g}", True, (255, 205, 110))
            self.screen.blit(score_text, (box.x + 12, box.y + 34))

            card_w = int(90 * card_scale)
            gap = 30
            total_w = card_w + gap * 4
            cards_start_x = box.centerx - total_w // 2
            card_y = box.y + 65
            for card_index, card_data in enumerate(cards[:5]):
                self.draw_card(card_data, cards_start_x + card_index * gap, card_y, scale=card_scale)

        close_font = pygame.font.SysFont("Arial", 13, bold=True)
        close = close_font.render("ESC / CLIC FUERA", True, (170, 180, 195))
        self.screen.blit(close, close.get_rect(center=(rect.centerx, rect.bottom - 12)))

    def draw_hud_panel(self, score, target, mult, chips, hands, discards):
        panel = pygame.Rect(20, 20, 240, self.height - 40)
        pygame.draw.rect(self.screen, COLOR_PANEL_BG, panel, border_radius=12)
        font_small = pygame.font.SysFont("Arial", 17, bold=True)
        self.screen.blit(font_small.render(f"Objetivo: {target}", True, (250, 200, 50)), (35, 42))
        self.screen.blit(self.font_big.render(f"{score}", True, COLOR_TEXT_MAIN), (35, 72))
        self.screen.blit(font_small.render(f"Fichas: {chips}", True, COLOR_CHIPS), (35, 140))
        self.screen.blit(font_small.render(f"Mult: X{mult:g}", True, COLOR_MULT), (35, 173))
        self.screen.blit(font_small.render(f"Manos: {hands} | Desc: {discards}", True, (200, 200, 200)), (35, 228))
        self.screen.blit(font_small.render("Jokers: 5 máx.", True, (190, 210, 190)), (35, 265))

    def draw_round_progress_bar(self, score, target):
        bar_width = 650
        bar_height = 14
        x, y = 300, 24
        progress = 0.0 if target <= 0 else min(1.0, max(0.0, score / target))
        pygame.draw.rect(self.screen, (42, 48, 58), (x, y, bar_width, bar_height), border_radius=7)
        pygame.draw.rect(self.screen, (70, 200, 120), (x, y, int(bar_width * progress), bar_height), border_radius=7)
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, bar_width, bar_height), width=2, border_radius=7)
        font = pygame.font.SysFont("Arial", 14, bold=True)
        self.screen.blit(font.render("PROGRESO", True, COLOR_TEXT_MAIN), (x, 4))
        self.screen.blit(font.render(f"{score} / {target}", True, COLOR_TEXT_MAIN), (x + bar_width + 10, 22))

    def draw_hand(self, cards_list):
        spacing = 95
        start_x = (self.width - (len(cards_list) * spacing)) // 2 + 100
        for i, card in enumerate(cards_list):
            self.draw_card(card, start_x + i * spacing, self.hand_y, is_selected=card.get("selected", False))

    def draw_hand_slots(self, cards_by_slot, total_slots):
        if total_slots <= 0:
            return
        spacing = 95
        start_x = (self.width - (total_slots * spacing)) // 2 + 100
        for index, card in enumerate(cards_by_slot):
            if card is None:
                continue
            self.draw_card(card, start_x + index * spacing, self.hand_y, is_selected=card.get("selected", False))

    def build_control_rects(self):
        y = self.height - self.CONTROL_Y_FROM_BOTTOM
        available_x = 300
        width = 170
        gap = 18
        labels = [
            ("play", "JUGAR (ESPACIO / ENTER)"),
            ("discard", "DESCARTAR (D)"),
            ("suit", "ORDENAR PALO (S)"),
            ("rank", "ORDENAR NUMERO (R)"),
        ]
        return {
            key: pygame.Rect(available_x + i * (width + gap), y, width, 46)
            for i, (key, _label) in enumerate(labels)
        }, {key: label for key, label in labels}

    def draw_controls(self, screen, control_rects, labels):
        mouse = pygame.mouse.get_pos()
        font = pygame.font.SysFont("Arial", 13, bold=True)
        for key, rect in control_rects.items():
            hovered = rect.collidepoint(mouse)
            fill = (95, 95, 125) if hovered else (55, 55, 70)
            pygame.draw.rect(screen, fill, rect, border_radius=8)
            pygame.draw.rect(screen, (220, 220, 220), rect, width=2, border_radius=8)
            surface = font.render(labels[key], True, COLOR_TEXT_MAIN)
            screen.blit(surface, surface.get_rect(center=rect.center))

    def present(self):
        pygame.display.flip()
