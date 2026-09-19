"""Punto de entrada principal y máquina de estados global."""
import sys
import pygame

from settings import S_WIDTH, S_HEIGHT, FPS
from states.menu_state import MenuState
from states.play_state import PlayState
from states.store_state import StoreState
from states.gameover_state import GameOverState
from states.victory_state import VictoryState


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((S_WIDTH, S_HEIGHT))
    pygame.display.set_caption("Juego de Cartas - Balatro Style")
    clock = pygame.time.Clock()

    context = {
        "round": 1,
        "money": 0,
        "jokers": [],
        "ante": 1,
        "blind_index": 0,
        "selected_blind": None,
        "blind_target": 300,
        "blind_name": "Ciega pequeña",
        "blind_is_boss": False,
        "active_boss": None,
        "active_boss_ante": None,
        "seen_boss_ids": set(),
        "previous_blind_played_card_codes": set(),
        "hand_counts": {},
        "total_discards": 0,
        "bosses_defeated": 0,
        "total_score": 0,
    }

    menu_state = MenuState(screen=screen, context=context)
    play_state = PlayState(screen=screen, context=context)
    store_state = StoreState(screen=screen, context=context)
    gameover_state = GameOverState(screen=screen, context=context)
    victory_state = VictoryState(screen=screen, context=context)

    states = {
        "MENU": menu_state,
        "PLAY": play_state,
        "SHOP": store_state,
        "GAME_OVER": gameover_state,
        "VICTORY": victory_state,
    }
    current_state_key = "MENU"
    current_state = states[current_state_key]
    current_state.enter()

    def change_state(next_state_key: str) -> None:
        nonlocal current_state_key, current_state
        if next_state_key not in states or next_state_key == current_state_key:
            return
        current_state.exit()
        current_state_key = next_state_key
        current_state = states[next_state_key]
        current_state.enter()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        events = pygame.event.get()
        if any(event.type == pygame.QUIT for event in events):
            running = False
            continue
        next_state_event = current_state.handle_events(events)
        next_state_update = current_state.update(dt)
        next_state = next_state_event or next_state_update

        if next_state == "QUIT":
            running = False
        elif next_state in states and next_state != current_state_key:
            if next_state == "PLAY" and hasattr(menu_state, "player_name"):
                context["player_name"] = menu_state.player_name
            change_state(next_state)
        elif next_state == "VICTORY":
            change_state("VICTORY")

        current_state.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
