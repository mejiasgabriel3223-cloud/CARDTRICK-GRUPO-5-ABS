"""Pantalla final tras derrotar tres Ciegas Jefe."""
from __future__ import annotations

import pygame

from audio import get_audio_manager


class VictoryState:
    """Muestra el nombre del jugador y el puntaje acumulado de la partida."""

    def __init__(self, screen: pygame.Surface, context: dict | None = None) -> None:
        self.screen = screen
        self.context = context if context is not None else {}
        self.audio = get_audio_manager()

    def enter(self) -> None:
        self.audio.stop_music()
        self.context["score"] = int(self.context.get("victory_score", self.context.get("total_score", 0)))

    def exit(self) -> None:
        pass

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                    return "MENU"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return "MENU"
        return None

    def update(self, dt=0):
        return None

    def draw(self, screen=None):
        target = screen or self.screen
        target.fill((15, 24, 20))
        center_x = target.get_width() // 2

        title_font = pygame.font.SysFont("Arial", 72, bold=True)
        subtitle_font = pygame.font.SysFont("Arial", 32, bold=True)
        score_font = pygame.font.SysFont("Arial", 40, bold=True)
        info_font = pygame.font.SysFont("Arial", 22)

        title = title_font.render("¡HAS GANADO!", True, (255, 215, 70))
        target.blit(title, title.get_rect(center=(center_x, 170)))

        player_name = str(self.context.get("player_name", "Jugador"))
        score = int(self.context.get("victory_score", self.context.get("total_score", 0)))
        bosses = int(self.context.get("bosses_defeated", 0))

        player = subtitle_font.render(f"Jugador: {player_name}", True, (255, 255, 255))
        total = score_font.render(f"Puntuación: {score}", True, (130, 230, 160))
        defeated = info_font.render(f"Ciegas jefe derrotadas: {bosses}", True, (220, 220, 220))
        prompt = info_font.render("ENTER, ESPACIO o clic para volver al menú", True, (180, 190, 180))

        target.blit(player, player.get_rect(center=(center_x, 285)))
        target.blit(total, total.get_rect(center=(center_x, 350)))
        target.blit(defeated, defeated.get_rect(center=(center_x, 415)))
        target.blit(prompt, prompt.get_rect(center=(center_x, 540)))
