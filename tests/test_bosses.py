"""Unit tests for boss blind rules."""

from entities import CardEntity
from systems.bosses import (
    ClubBoss,
    DiamondBoss,
    HeartBoss,
    HookBoss,
    PillarBoss,
    PsychicBoss,
    SpadeBoss,
    WallBoss,
)


def card(code: str) -> CardEntity:
    rank = code[:-1]
    suit = code[-1]
    return CardEntity(rank=rank, suit=suit)


def test_suit_bosses_mark_their_restricted_suit_without_blocking_play() -> None:
    cases = [
        (HeartBoss(), "♥"),
        (DiamondBoss(), "♦"),
        (ClubBoss(), "♣"),
        (SpadeBoss(), "♠"),
    ]

    for boss, suit in cases:
        blocked = card(f"A{suit}")
        allowed = card("A♥" if suit != "♥" else "A♠")
        assert boss.validate_play([blocked], {}).allowed
        assert boss.non_scoring_card_codes([blocked], {}) == {blocked.code}
        assert boss.validate_play([allowed], {}).allowed
        assert boss.non_scoring_card_codes([allowed], {}) == set()


def test_pillar_marks_previous_cards_without_blocking_play() -> None:
    boss = PillarBoss()
    blocked = card("A♠")
    assert boss.validate_play(
        [blocked],
        {"previous_blind_played_card_codes": {"A♠"}},
    ).allowed
    assert boss.non_scoring_card_codes(
        [blocked],
        {"previous_blind_played_card_codes": {"A♠"}},
    ) == {"A♠"}


def test_pillar_allows_new_cards() -> None:
    boss = PillarBoss()
    assert boss.validate_play(
        [card("K♥")],
        {"previous_blind_played_card_codes": {"A♠"}},
    ).allowed


def test_psychic_limits_play_size_to_four() -> None:
    assert PsychicBoss().get_max_play_size(5) == 4


def test_hook_requests_two_post_play_discards() -> None:
    assert HookBoss().after_hand_played([], {}).discard_count == 2


def test_wall_has_larger_target_multiplier() -> None:
    wall = WallBoss()
    assert wall.calculate_target_score(1) == 1200
