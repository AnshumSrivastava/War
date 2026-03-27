"""
test/test_q_table.py
QA tests for engine.ai.q_table.QTableManager + engine.data.services.rl_data_service.RLDataService

Validates the core learning pipeline: Q-value storage, Bellman update,
batch learning, action selection, and save/load round-trip.
"""
import os
import pytest
from engine.ai.q_table import QTableManager


@pytest.fixture
def q_mgr():
    """Fresh QTableManager with 3 actions for speed."""
    return QTableManager(state_size=10, action_size=3, alpha=0.1, gamma=0.9, epsilon=0.5)


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_unseen_state_action_is_zero(self, q_mgr):
        assert q_mgr.service.get_q_value(0, 0) == pytest.approx(0.0)

    def test_all_actions_zero_initially(self, q_mgr):
        vals = q_mgr.get_q_values(state=5, available_actions_indices=[0, 1, 2])
        assert all(v == 0.0 for v in vals.values())

    def test_action_size_stored(self, q_mgr):
        assert q_mgr.action_size == 3


# ---------------------------------------------------------------------------
# Single-step Bellman update
# ---------------------------------------------------------------------------

class TestSingleUpdate:
    def test_bellman_update_increases_q_for_positive_reward(self, q_mgr):
        """Q(s=1, a=0) starts at 0; reward=1.0 should make it positive."""
        q_mgr.update_q_value(state=1, action=0, reward=1.0, next_state=2)
        new_q = q_mgr.service.get_q_value(1, 0)
        assert new_q > 0.0

    def test_bellman_exact_value_no_future(self, q_mgr):
        """
        With alpha=0.1, gamma=0.9, next_state Q all zero:
        new_Q = (1-0.1)*0 + 0.1*(1.0 + 0.9*0) = 0.1
        """
        q_mgr.update_q_value(state=3, action=1, reward=1.0, next_state=9)
        assert q_mgr.service.get_q_value(3, 1) == pytest.approx(0.1, rel=1e-5)

    def test_bellman_negative_reward_decreases_q(self, q_mgr):
        q_mgr.update_q_value(state=2, action=2, reward=-1.0, next_state=3)
        assert q_mgr.service.get_q_value(2, 2) == pytest.approx(-0.1, rel=1e-5)

    def test_multiple_updates_accumulate(self, q_mgr):
        """Two positive updates on the same (s,a) should compound."""
        q_mgr.update_q_value(state=5, action=0, reward=1.0, next_state=6)
        v1 = q_mgr.service.get_q_value(5, 0)
        q_mgr.update_q_value(state=5, action=0, reward=1.0, next_state=6)
        v2 = q_mgr.service.get_q_value(5, 0)
        assert v2 > v1


# ---------------------------------------------------------------------------
# Batch update
# ---------------------------------------------------------------------------

class TestBatchUpdate:
    def test_batch_updates_multiple_pairs(self, q_mgr):
        batch = [
            (0, 0, 1.0,  1, False),
            (0, 1, -1.0, 2, True),   # done=True → next_max=0
        ]
        q_mgr.update_batch(batch)
        # Q(0,0): 0 + 0.1*(1.0 + 0.9*0) = 0.1
        # Q(0,1): 0 + 0.1*(-1.0 + 0.9*0) = -0.1 (done → next_max=0)
        assert q_mgr.service.get_q_value(0, 0) == pytest.approx(0.1, rel=1e-4)
        assert q_mgr.service.get_q_value(0, 1) == pytest.approx(-0.1, rel=1e-4)

    def test_batch_done_ignores_next_state(self, q_mgr):
        """done=True must zero out the future term regardless of next_state Q-values."""
        # First prime next_state=7 with a high value
        q_mgr.service.set_q_value(7, 0, 999.0)
        # Now update with done=True — next_state value should be ignored
        q_mgr.update_batch([(4, 0, 1.0, 7, True)])
        result = q_mgr.service.get_q_value(4, 0)
        assert result == pytest.approx(0.1, rel=1e-4)


# ---------------------------------------------------------------------------
# Action selection
# ---------------------------------------------------------------------------

class TestActionSelection:
    def test_get_action_returns_best_action(self, q_mgr):
        q_mgr.service.set_q_value(8, 0, 1.0)
        q_mgr.service.set_q_value(8, 1, 5.0)
        q_mgr.service.set_q_value(8, 2, 2.0)
        best = q_mgr.get_action(state=8, available_actions_indices=[0, 1, 2])
        assert best == 1

    def test_get_action_restricted_actions(self, q_mgr):
        """If only actions [0, 2] are available, action 1 (best) is not returned."""
        q_mgr.service.set_q_value(8, 0, 1.0)
        q_mgr.service.set_q_value(8, 1, 5.0)
        q_mgr.service.set_q_value(8, 2, 3.0)
        best = q_mgr.get_action(state=8, available_actions_indices=[0, 2])
        assert best == 2

    def test_max_q_value_empty_returns_zero(self, q_mgr):
        result = q_mgr.service.get_max_q_value(9, [])
        assert result == pytest.approx(0.0)

    def test_get_q_values_returns_dict(self, q_mgr):
        vals = q_mgr.get_q_values(state=0, available_actions_indices=[0, 2])
        assert isinstance(vals, dict)
        assert set(vals.keys()) == {0, 2}


# ---------------------------------------------------------------------------
# Save / Load round-trip
# ---------------------------------------------------------------------------

class TestSaveLoad:
    def test_save_and_load_npy(self, q_mgr, tmp_path):
        save_path = str(tmp_path / "q_table.npy")
        q_mgr.service.set_q_value(3, 1, 42.0)
        q_mgr.save_q_table(filename=save_path)
        assert os.path.exists(save_path)

        # Load into a fresh manager
        fresh = QTableManager(state_size=10, action_size=3)
        fresh.load_q_table(filename=save_path)
        assert fresh.service.get_q_value(3, 1) == pytest.approx(42.0, rel=1e-4)

    def test_load_nonexistent_file_does_not_crash(self, q_mgr, tmp_path):
        """Loading from a path that doesn't exist should silently do nothing."""
        q_mgr.load_q_table(filename=str(tmp_path / "nonexistent.npy"))
        # No exception raised — Q-table remains all zeros
        assert q_mgr.service.get_q_value(0, 0) == pytest.approx(0.0)
