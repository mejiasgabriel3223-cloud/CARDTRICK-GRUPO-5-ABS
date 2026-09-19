"""Gestor de Antes/Ciegas alineado con la nueva progresión 300 + 200."""
import random
from systems.bosses import get_random_boss_instance, BossBlind

BASE_ANTE_TARGETS = {ante: 300 + 600 * (ante - 1) for ante in range(1, 9)}

SKIP_TAGS_POOL = [
    {"name": "Etiqueta Económica", "effect": "add_money", "value": 15, "desc": "+$15 de oro directo"},
    {"name": "Etiqueta Cuponera", "effect": "free_shop", "value": 0, "desc": "Próxima tienda gratis"},
    {"name": "Etiqueta Mega-Sobre", "effect": "free_pack", "value": 0, "desc": "Sobre de cartas gratis en tienda"},
    {"name": "Etiqueta Dote", "effect": "money_per_hand", "value": 3, "desc": "+$3 por cada mano restante"},
]


class AnteManager:
    def __init__(self, max_antes: int = 8):
        self.max_antes = max_antes
        self.current_ante = 1
        self.current_blind_type = "small"
        self.seen_boss_ids = set()
        self.target_score = 0
        self.base_reward = 0
        self.active_boss: BossBlind | None = None
        self.pending_tags = []
        self.small_skip_tag = None
        self.big_skip_tag = None
        self._setup_ante()

    def _setup_ante(self):
        self.active_boss = get_random_boss_instance(self.seen_boss_ids)
        self.small_skip_tag = random.choice(SKIP_TAGS_POOL)
        self.big_skip_tag = random.choice(SKIP_TAGS_POOL)
        self._update_blind_parameters()

    def _normal_target(self, local_index: int) -> int:
        return 300 + 200 * ((self.current_ante - 1) * 3 + local_index)

    def _update_blind_parameters(self):
        if self.current_blind_type == "small":
            self.target_score = self._normal_target(0)
            self.base_reward = 3
        elif self.current_blind_type == "big":
            self.target_score = self._normal_target(1)
            self.base_reward = 4
        else:
            self.target_score = self._normal_target(2)
            self.base_reward = 5
            if self.active_boss.effect_id == "wall":
                self.target_score *= 2
            elif self.active_boss.effect_id == "needle":
                self.target_score = int(self.target_score * 0.6)

    def get_current_blind_info(self) -> dict:
        return {
            "ante": self.current_ante,
            "max_antes": self.max_antes,
            "blind_type": self.current_blind_type,
            "target_score": self.target_score,
            "base_reward": self.base_reward,
            "can_skip": self.current_blind_type != "boss",
            "skip_tag": self.small_skip_tag if self.current_blind_type == "small" else (self.big_skip_tag if self.current_blind_type == "big" else None),
            "boss_info": self.active_boss.to_dict() if self.current_blind_type == "boss" else None,
        }

    def skip_blind(self) -> dict:
        if self.current_blind_type == "boss":
            raise ValueError("No se puede saltar la Ciega Jefe.")
        applied_tag = self.small_skip_tag if self.current_blind_type == "small" else self.big_skip_tag
        self.pending_tags.append(applied_tag)
        self._advance_blind_pointer()
        return applied_tag

    def calculate_payout(self, remaining_hands: int, remaining_discards: int) -> dict:
        hand_bonus = remaining_hands
        discard_bonus = remaining_discards
        return {
            "base_reward": self.base_reward,
            "hand_bonus": hand_bonus,
            "discard_bonus": discard_bonus,
            "total_payout": self.base_reward + hand_bonus + discard_bonus,
        }

    def complete_blind(self):
        self._advance_blind_pointer()

    def _advance_blind_pointer(self):
        if self.current_blind_type == "small":
            self.current_blind_type = "big"
        elif self.current_blind_type == "big":
            self.current_blind_type = "boss"
        else:
            self.current_ante += 1
            self.current_blind_type = "small"
            self._setup_ante()
        self._update_blind_parameters()

    def is_run_completed(self) -> bool:
        return self.current_ante > self.max_antes
