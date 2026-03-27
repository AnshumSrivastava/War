"""
test/test_reward_model.py
QA tests for engine.ai.reward.RewardModel

Tests every branch of calculate_reward() with concrete numeric assertions.
No PyQt, no map, no entity_manager needed — pure math validation.
"""
import pytest
from unittest.mock import MagicMock
from engine.ai.reward import RewardModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_entity(personnel=100, side="Attacker", under_fire=False, command=None):
    """Build a minimal mock entity sufficient for RewardModel."""
    e = MagicMock()
    attrs = {"personnel": personnel, "side": side, "under_fire": under_fire}
    e.get_attribute.side_effect = lambda k, default=None: attrs.get(k, default)
    e.current_command = command
    return e


def _make_command(cmd_type, dist_delta=0, dist=0, objective_type="DEFAULT"):
    cmd = MagicMock()
    cmd.command_type = cmd_type
    cmd.objective_type = objective_type
    return cmd


@pytest.fixture
def model():
    return RewardModel()


# ---------------------------------------------------------------------------
# 1. Step penalty / action incentive
# ---------------------------------------------------------------------------

class TestStepIncentive:
    def test_hold_action_no_incentive(self, model):
        """HOLD / END TURN should NOT yield an action incentive."""
        entity = _make_entity()
        r = model.calculate_reward(entity, "HOLD / END TURN")
        # Only the step penalty applies; no action incentive
        assert r == pytest.approx(0.0), "Hold action should give 0 net (no penalty here, no incentive)"

    def test_non_hold_gives_incentive(self, model):
        """Any non-hold action should earn REWARD_ACTION_INCENTIVE."""
        entity = _make_entity()
        r = model.calculate_reward(entity, "MOVE", distance_delta=0)
        # MOVE with distance_delta=0: no closing/retreating penalty, no terrain, just incentive
        assert r == pytest.approx(model.REWARD_ACTION_INCENTIVE)


# ---------------------------------------------------------------------------
# 2. Fire reward
# ---------------------------------------------------------------------------

class TestFireReward:
    def test_fire_hit_gives_positive_reward(self, model):
        entity = _make_entity()
        result = {"casualties": 5, "remaining": 10}
        r = model.calculate_reward(entity, "FIRE", combat_result=result)
        # FIRE_HIT_REWARD(50) + 5*FIRE_DAMAGE_MULT(10) = 100, plus incentive(0)
        assert r == pytest.approx(50 + 5 * 10 + model.REWARD_ACTION_INCENTIVE)

    def test_fire_miss_gives_penalty(self, model):
        entity = _make_entity()
        result = {"casualties": 0, "remaining": 20}
        r = model.calculate_reward(entity, "FIRE", combat_result=result)
        # FIRE_MISS_PENALTY(-5) + incentive(0)
        assert r == pytest.approx(-5 + model.REWARD_ACTION_INCENTIVE)

    def test_fire_kill_gives_extra_bonus(self, model):
        entity = _make_entity()
        result = {"casualties": 10, "remaining": 0}
        r = model.calculate_reward(entity, "FIRE", combat_result=result)
        # 50 + 10*10 + 150(kill) + 0(incentive) = 300
        assert r == pytest.approx(50 + 10 * 10 + 150 + model.REWARD_ACTION_INCENTIVE)

    def test_fire_no_combat_result_gives_only_incentive(self, model):
        """FIRE action with no combat_result should not crash — just give incentive."""
        entity = _make_entity()
        r = model.calculate_reward(entity, "FIRE", combat_result=None)
        assert r == pytest.approx(model.REWARD_ACTION_INCENTIVE)


# ---------------------------------------------------------------------------
# 3. Movement reward
# ---------------------------------------------------------------------------

class TestMoveReward:
    def test_closing_gives_reward(self, model):
        entity = _make_entity()
        r = model.calculate_reward(entity, "MOVE", distance_delta=-1)
        # REWARD_CLOSING(15) + incentive(0)
        assert r == pytest.approx(model.REWARD_CLOSING + model.REWARD_ACTION_INCENTIVE)

    def test_retreating_gives_penalty(self, model):
        entity = _make_entity()
        r = model.calculate_reward(entity, "MOVE", distance_delta=1)
        # PENALTY_RETREATING(-20) + incentive(0)
        assert r == pytest.approx(model.PENALTY_RETREATING + model.REWARD_ACTION_INCENTIVE)

    def test_no_delta_neutral_movement(self, model):
        entity = _make_entity()
        r = model.calculate_reward(entity, "MOVE", distance_delta=0)
        # No closing, no retreating — just incentive
        assert r == pytest.approx(model.REWARD_ACTION_INCENTIVE)

    def test_evasion_bonus_when_under_fire(self, model):
        entity = _make_entity(under_fire=True)
        r = model.calculate_reward(entity, "MOVE", distance_delta=0)
        # REWARD_EVASION_SUCCESS(5) + incentive(0)
        assert r == pytest.approx(model.REWARD_EVASION_SUCCESS + model.REWARD_ACTION_INCENTIVE)

    def test_terrain_cost_deducted_on_move(self, model):
        entity = _make_entity()
        r = model.calculate_reward(entity, "MOVE", distance_delta=0, terrain_cost=2.0)
        # -terrain_cost(-2) + incentive(0) = -2
        assert r == pytest.approx(-2.0 + model.REWARD_ACTION_INCENTIVE)


# ---------------------------------------------------------------------------
# 4. Survival penalty
# ---------------------------------------------------------------------------

class TestSurvivalPenalty:
    def test_personnel_loss_gives_penalty(self, model):
        entity = _make_entity(personnel=80)
        r = model.calculate_reward(entity, "HOLD / END TURN", previous_personnel=100)
        # 20 lost * PENALTY_DAMAGE_TAKEN(-2) = -40
        assert r == pytest.approx(20 * model.PENALTY_DAMAGE_TAKEN)

    def test_full_elimination_gives_extra_penalty(self, model):
        entity = _make_entity(personnel=0)
        r = model.calculate_reward(entity, "HOLD / END TURN", previous_personnel=50)
        # 50 lost * -2 = -100 + PENALTY_UNIT_LOST(-400) = -500
        assert r == pytest.approx(50 * model.PENALTY_DAMAGE_TAKEN + model.PENALTY_UNIT_LOST)

    def test_no_loss_no_survival_penalty(self, model):
        entity = _make_entity(personnel=100)
        r = model.calculate_reward(entity, "HOLD / END TURN", previous_personnel=100)
        assert r == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# 5. Command-driven rewards
# ---------------------------------------------------------------------------

class TestCommandReward:
    def test_move_command_closing_gives_bonus(self, model):
        cmd = MagicMock()
        cmd.command_type = "MOVE"
        entity = _make_entity(command=cmd)
        # command_dist_delta < 0 = closing toward mission target
        r = model.calculate_reward(
            entity, "MOVE",
            command_dist_delta=-1, command_dist=3,
            step_number=1, max_steps=50
        )
        # abs(-1) * REWARD_CLOSING(15) * 1.5 = 22.5, plus general closing(15) + incentive(1)
        assert r > model.REWARD_CLOSING  # At least more than the general closing reward

    def test_decay_multiplier_at_end_of_episode(self, model):
        """Goal reward should be smaller when arrived late in the episode."""
        cmd = MagicMock()
        cmd.command_type = "MOVE"
        entity = _make_entity(command=cmd)
        r_early = model.calculate_reward(
            entity, "HOLD / END TURN",
            command_dist=0, command_dist_delta=0,
            step_number=1, max_steps=50
        )
        r_late = model.calculate_reward(
            entity, "HOLD / END TURN",
            command_dist=0, command_dist_delta=0,
            step_number=49, max_steps=50
        )
        assert r_early > r_late, "Early goal completion should yield larger reward than late"
