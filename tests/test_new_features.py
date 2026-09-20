from __future__ import annotations

from pathlib import Path

import pygame

from entities import ALL_JOKERS, CardEntity, EntityCollection, RandomJokerPool
from systems.assets import AssetResolver
from systems.joker_catalog import JOKER_CATALOG
from states.store_state import StoreState


ROOT = Path(__file__).resolve().parents[1]


def test_all_jokers_are_concrete_and_have_metadata():
    assert len(ALL_JOKERS) == 32
    assert len(JOKER_CATALOG) >= len(ALL_JOKERS)
    instances = [cls() for cls in ALL_JOKERS]
    assert all(joker.name for joker in instances)
    assert all(joker.description for joker in instances)
    assert all(joker.rarity for joker in instances)
    assert all(joker.shop_price > 0 for joker in instances)
    assert all(joker.sell_price > 0 for joker in instances)


def test_joker_assets_exist_in_repository():
    resolver = AssetResolver(ROOT)
    assert len(resolver._joker_assets) >= 32
    assert all(cls().asset_path for cls in ALL_JOKERS)


def test_brenda_uses_special_asset_and_every_joker_has_stable_asset_mapping():
    resolver = AssetResolver(ROOT)
    brenda_cls = next(cls for cls in ALL_JOKERS if cls.__name__ == "BrendaMadagascarJoker")
    brenda = brenda_cls()
    assert brenda.asset_path.endswith("joker-Especial.png")
    assert all(resolver.joker_asset_for(cls.__name__) for cls in ALL_JOKERS)


def test_blind_progression_starts_at_300_and_steps_200():
    assert StoreState.blind_target(1, 0) == 300
    assert StoreState.blind_target(1, 1) == 500
    assert StoreState.blind_target(1, 2) == 700
    assert StoreState.blind_target(2, 0) == 900


def test_joker_pool_executes_and_removes_consumed_jokers():
    pygame.init()
    card = CardEntity("A", "♥", score=14)
    donut_cls = next(cls for cls in ALL_JOKERS if cls.__name__ == "DonutJoker")
    donut = donut_cls(uses_left=1)
    pool = RandomJokerPool([donut])
    pool.activate_all(EntityCollection([card]), {"money": 0})
    assert donut.active is False
    assert pool.jokers == []
    pygame.quit()


def test_blind_sequence_is_linear_and_skip_advances_one_step():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    context = {
        "ante": 1,
        "blind_index": 0,
        "active_boss": None,
        "active_boss_ante": None,
        "seen_boss_ids": set(),
    }
    store = StoreState(screen, context)
    store.enter()
    assert len(store.blind_options) == 1
    assert store.next_blind.name == "Ciega pequeña"
    store._skip_next_blind()
    assert len(store.blind_options) == 1
    assert store.next_blind.name == "Ciega grande"
    store._skip_next_blind()
    assert len(store.blind_options) == 1
    assert store.next_blind.is_boss is True
    store._skip_next_blind()
    assert store.next_blind.is_boss is True
    pygame.quit()


def test_three_bosses_trigger_victory_transition():
    from states.play_state import PlayState

    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    context = {
        "ante": 1,
        "blind_index": 2,
        "blind_is_boss": True,
        "blind_name": "Jefe",
        "blind_target": 300,
        "total_score": 900,
        "bosses_defeated": 2,
        "jokers": [],
    }
    state = PlayState(screen, context)
    state.round_score = 300
    state.target = 300
    state.hands_left = 2
    state.discards_left = 2
    state._prepare_store_transition()
    assert context["bosses_defeated"] == 3
    assert context["victory_score"] == 1200
    pygame.quit()
