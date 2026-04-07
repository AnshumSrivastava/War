# SOP-05: RL Training Configuration

**Version:** 1.0 | **Owner:** AI Team | **Applies to:** All RL training adjustments

---

## 1. Purpose

This SOP explains how to tune the RL training system, what each parameter controls, and how to safely run experiments without breaking the production training loop.

---

## 2. Config File Location

All RL parameters live in **`config/rl_config.json`**. Never hardcode these values in engine files.

Changes to this file take effect on the **next training run** (not mid-episode). No code restart is required — the `ConfigLoader` re-reads on each `RewardModel.__init__()` call.

---

## 3. Parameter Reference

### 3.1 Training Parameters (`training.*`)

| Key | Default | Effect |
|---|---|---|
| `epsilon_start` | `1.0` | Starting exploration rate (1.0 = fully random) |
| `epsilon_min` | `0.05` | Minimum exploration (5% random forever) |
| `epsilon_decay` | `0.98` | Multiplied each episode. Lower = faster convergence. 0.98 → min in ~150 episodes |
| `learning_rate` | `0.1` | How fast Q-values update. Higher = faster but more volatile |
| `discount_factor` | `0.99` | How much future rewards matter. 0.99 = care about distant future |
| `batch_size` | `32` | Number of replay entries per training batch |
| `replay_buffer_size` | `5000` | Max stored experiences before oldest are discarded |
| `default_episodes` | `100` | Default episodes shown in the UI spinner |
| `max_steps_per_episode` | `50` | Max ticks before an episode is forced to end |

### 3.2 Reward Constants (`rewards.*`)

| Key | Default | What It Controls |
|---|---|---|
| `goal_reached` | `400.0` | Points for reaching a MOVE/CAPTURE objective |
| `closing` | `30.0` | Points per hex moved toward the objective |
| `retreat_penalty` | `-40.0` | Penalty for moving away from objective |
| `fire_hit` | `120.0` | Base reward for any successful fire that causes casualties |
| `fire_kill` | `400.0` | Bonus for eliminating an enemy unit entirely |
| `fire_miss` | `-5.0` | Penalty for firing and missing |
| `fire_damage_mult` | `10.0` | Extra reward per casualty caused (rewards proportional damage) |
| `step_penalty` | `-1.0` | Per-step penalty to encourage efficiency |
| `damage_taken` | `-2.0` | Per-personnel penalty for taking damage |
| `eliminated` | `-400.0` | Total penalty for having your unit destroyed |
| `evasion_success` | `5.0` | Bonus for moving while under fire |
| `revisit_penalty` | `-10.0` | Penalty for returning to a hex already visited this episode |

---

## 4. How the Agent Learns (Quick Overview)

```
Episode Start
    ↓
Agent observes state (position, nearby enemies, command distance)
    ↓
Agent picks action (FIRE / MOVE / HOLD / etc.)
    ├── If epsilon-greedy: random action (exploration)
    └── If exploiting: pick action with highest Q-value
    ↓
Action is executed → combat/movement resolved  
    ↓
Reward is calculated (RewardModel.calculate_reward())
    ↓
Q-value is updated via Bellman Equation:
    Q(s,a) = Q(s,a) + α × [r + γ × max_Q(s') - Q(s,a)]
    ↓
Experience stored in ReplayBuffer
    ↓
At episode end: batch training from ReplayBuffer
    ↓
Epsilon decays: ε = max(ε × epsilon_decay, epsilon_min)
    ↓
Next episode (repeat ~100-500 times)
```

---

## 5. Tuning Guide

### "Agents don't shoot"
- Increase `fire_hit` and `fire_kill`  
- Verify `fire_hit` > `closing × 2` (otherwise moving is always better than shooting)
- Current balance: fire_hit=120 vs closing=30×2=60 ✅

### "Agents take too long to converge"
- Decrease `epsilon_decay` (e.g., 0.98 → 0.95)
- Increase `batch_size`

### "Agents move erratically / don't follow goals"
- Verify scenario has mission commands assigned (check `entity.current_command`)
- Increase `goal_reached` and `closing`
- Ensure `retreat_penalty` is strong enough (more negative)

### "Defenders just hold and do nothing"
- In `act_model.py`, confirm MOVE actions are in defender's allowed list
- Increase `fire_hit` — defenders need fire incentive to bother shooting

### "Learning is unstable / Q-values explode"
- Decrease `learning_rate` (0.1 → 0.05)
- Add reward normalization (divide all rewards by `goal_reached`)

---

## 6. Running Experiments Safely

1. **Never modify `rl_config.json` mid-training** — wait for the episode to complete
2. **Use "Reset Intel" before changing reward values** — old Q-tables trained with different rewards will behave confusingly
3. **Backup Q-table files** before major changes: `cp -r data/training/ data/training_backup_<date>/`
4. **Log the config version** — add a `"version": "1.2"` key to `rl_config.json` and include it in training logs

---

## 7. Adding a New Reward Signal

1. Add the constant to `config/rl_config.json` under `rewards`
2. Load it in `RewardModel.__init__()`:
   ```python
   self.MY_NEW_REWARD = rl_conf.get("my_new_reward", 0.0)
   ```
3. Apply it in `RewardModel.calculate_reward()` at the appropriate point
4. Add to this SOP's parameter reference table
5. Document what behavior you expect it to produce

---

## 8. Expected Learning Curve

With current defaults (`epsilon_decay=0.98`, `max_steps=50`):

| Episode Range | Expected Behavior |
|---|---|
| 0–20 | Fully random. Lots of HOLD. No movement toward goals. |
| 20–60 | Starting to show directional movement. Some fire attempts. |
| 60–100 | Agents consistently pursuing goals. Fire increasingly common. |
| 100–200 | Strategy solidifying. Win rates improving. Fire becoming routine. |
| 200+ | Near-optimal behavior. Epsilon at minimum. Pure exploitation. |

If agents are still random at episode 100+, check:
- `epsilon_decay` is not accidentally set to `0.999` (too slow)
- Q-tables weren't corrupted (check `data/training/`)
- Reward signals are reaching the agent (add a `log.debug` in `calculate_reward`)
