"""
Reinforcement Learning Navigation Agent for ArUco Marker Approach.

Implements Q-Learning with Temporal Difference TD(0) learning, continuous reward
feedback based on real spatial distance changes to the marker, and automatic
direction/polarity reinforcement to guarantee the car approaches the marker
even under inverted motor wiring or reversed coordinate frames.
"""

import json
import logging
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, Dict, Optional, List

logger = logging.getLogger("aruconav.control.rl")


@dataclass
class RLState:
    """Discrete state representation for Q-learning."""
    dist_bin: int     # 0: ARRIVED (<35px), 1: NEAR (35-100px), 2: MID (100-250px), 3: FAR (>250px)
    heading_bin: int  # 0: AHEAD (-15..+15 deg), 1: SLIGHT_LEFT (-45..-15), 2: HARD_LEFT (<-45),
                      # 3: SLIGHT_RIGHT (+15..+45), 4: HARD_RIGHT (>+45), 5: BEHIND (|err| > 135)
    obstacle_bin: int # 0: CLEAR, 1: LEFT_WARN, 2: RIGHT_WARN, 3: FRONT_BLOCKED

    def to_key(self) -> str:
        return f"{self.dist_bin}_{self.heading_bin}_{self.obstacle_bin}"

    @classmethod
    def from_continuous(
        cls,
        dist_px: float,
        heading_err_deg: float,
        us_left_cm: float = 100.0,
        us_right_cm: float = 100.0,
        us_front_cm: float = 100.0,
        arrival_dist_px: float = 35.0
    ) -> "RLState":
        # 1. Distance Binning
        if dist_px <= arrival_dist_px:
            dist_bin = 0  # ARRIVED
        elif dist_px < 110.0:
            dist_bin = 1  # NEAR
        elif dist_px < 260.0:
            dist_bin = 2  # MID
        else:
            dist_bin = 3  # FAR

        # 2. Heading Error Binning (-180 to +180 deg)
        abs_err = abs(heading_err_deg)
        if abs_err <= 18.0:
            heading_bin = 0  # AHEAD
        elif heading_err_deg < -18.0 and heading_err_deg >= -50.0:
            heading_bin = 1  # SLIGHT_LEFT
        elif heading_err_deg < -50.0 and abs_err <= 135.0:
            heading_bin = 2  # HARD_LEFT
        elif heading_err_deg > 18.0 and heading_err_deg <= 50.0:
            heading_bin = 3  # SLIGHT_RIGHT
        elif heading_err_deg > 50.0 and abs_err <= 135.0:
            heading_bin = 4  # HARD_RIGHT
        else:
            heading_bin = 5  # BEHIND

        # 3. Obstacle Binning
        if us_front_cm < 22.0:
            obstacle_bin = 3  # FRONT_BLOCKED
        elif us_left_cm < 28.0:
            obstacle_bin = 1  # LEFT_WARN
        elif us_right_cm < 28.0:
            obstacle_bin = 2  # RIGHT_WARN
        else:
            obstacle_bin = 0  # CLEAR

        return cls(dist_bin=dist_bin, heading_bin=heading_bin, obstacle_bin=obstacle_bin)


class RLAction:
    """Discrete action definitions with normalized throttle (-1..1) and steering (-1..1)."""
    FORWARD_FAST = 0
    FORWARD_SLOW = 1
    STEER_LEFT   = 2
    STEER_RIGHT  = 3
    PIVOT_LEFT   = 4
    PIVOT_RIGHT  = 5
    REVERSE      = 6
    STOP         = 7

    NUM_ACTIONS = 8
    NAMES = [
        "FWD_FAST", "FWD_SLOW", "STEER_LEFT", "STEER_RIGHT",
        "PIVOT_LEFT", "PIVOT_RIGHT", "REVERSE", "STOP"
    ]

    # Map each action index to (throttle: float, steering: float)
    ACTION_MAP = {
        FORWARD_FAST: (1.0, 0.0),
        FORWARD_SLOW: (0.38, 0.0),  # Controlled crawl for progressive target braking
        STEER_LEFT:   (0.48, -0.65),
        STEER_RIGHT:  (0.48, 0.65),
        PIVOT_LEFT:   (0.0, -1.0),
        PIVOT_RIGHT:  (0.0, 1.0),
        REVERSE:      (-0.6, 0.0),
        STOP:         (0.0, 0.0),
    }


class RLNavigationAgent:
    """
    Q-Learning agent that dynamically learns and reinforces the optimal control
    actions to approach the target ArUco marker.
    """

    def __init__(
        self,
        alpha: float = 0.35,      # Learning rate
        gamma: float = 0.85,      # Discount factor
        epsilon: float = 0.05,    # Exploration rate
        save_path: Optional[str] = None
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        if save_path == ":memory:" or save_path is None:
            self.save_path = save_path
        else:
            self.save_path = save_path or str(Path.home() / ".gemini" / "antigravity" / "rl_qtable.json")

        # Q-Table: state_key -> [Q(s, a0), Q(s, a1), ..., Q(s, a7)]
        self.q_table: Dict[str, List[float]] = {}
        self._init_q_table_with_prior()

        # Step tracking
        self.last_state: Optional[RLState] = None
        self.last_action: Optional[int] = None
        self.last_dist: Optional[float] = None
        self.last_heading_err: Optional[float] = None
        
        # Telemetry & Learning Metrics
        self.last_reward: float = 0.0
        self.total_episode_reward: float = 0.0
        self.step_count: int = 0
        self.auto_inversion_detected: bool = False
        self._opposite_motion_count: int = 0
        self._progress_count: int = 0

        self.load_q_table()

    def _init_q_table_with_prior(self):
        """Pre-seed the Q-table with intelligent heuristic priors for fast convergence."""
        for d in range(4):
            for h in range(6):
                for o in range(4):
                    state = RLState(dist_bin=d, heading_bin=h, obstacle_bin=o)
                    key = state.to_key()
                    q_vals = [0.0] * RLAction.NUM_ACTIONS

                    if d == 0:
                        # Arrived at Target -> Active Hard Stop
                        q_vals[RLAction.STOP] = 15.0
                    elif o == 3:
                        # Front blocked -> REVERSE or PIVOT away
                        q_vals[RLAction.REVERSE] = 8.0
                        q_vals[RLAction.PIVOT_LEFT] = 6.0
                        q_vals[RLAction.PIVOT_RIGHT] = 6.0
                    elif o == 1:
                        # Left warn -> steer right
                        q_vals[RLAction.STEER_RIGHT] = 7.0
                        q_vals[RLAction.PIVOT_RIGHT] = 5.0
                    elif o == 2:
                        # Right warn -> steer left
                        q_vals[RLAction.STEER_LEFT] = 7.0
                        q_vals[RLAction.PIVOT_LEFT] = 5.0
                    elif d == 1:
                        # --- BRAKING ZONE (NEAR TARGET: 35 - 110px) ---
                        # In this zone, brake smoothly to target: prefer FORWARD_SLOW, suppress FORWARD_FAST
                        if h == 0:
                            q_vals[RLAction.FORWARD_SLOW] = 10.0
                            q_vals[RLAction.FORWARD_FAST] = 1.0
                            q_vals[RLAction.STOP] = 4.0
                        elif h == 1:
                            q_vals[RLAction.STEER_LEFT] = 8.0
                            q_vals[RLAction.FORWARD_SLOW] = 6.0
                        elif h == 2:
                            q_vals[RLAction.PIVOT_LEFT] = 7.0
                            q_vals[RLAction.STEER_LEFT] = 5.0
                        elif h == 3:
                            q_vals[RLAction.STEER_RIGHT] = 8.0
                            q_vals[RLAction.FORWARD_SLOW] = 6.0
                        elif h == 4:
                            q_vals[RLAction.PIVOT_RIGHT] = 7.0
                            q_vals[RLAction.STEER_RIGHT] = 5.0
                        elif h == 5:
                            q_vals[RLAction.PIVOT_RIGHT] = 6.0
                            q_vals[RLAction.PIVOT_LEFT] = 6.0
                    else:
                        # --- OPEN SPACE (MID / FAR: > 110px) ---
                        # Cruise at full authority towards marker without premature braking
                        if h == 0:
                            q_vals[RLAction.FORWARD_FAST] = 10.0
                            q_vals[RLAction.FORWARD_SLOW] = 7.0
                        elif h == 1:
                            q_vals[RLAction.STEER_LEFT] = 8.0
                            q_vals[RLAction.FORWARD_SLOW] = 4.0
                        elif h == 2:
                            q_vals[RLAction.PIVOT_LEFT] = 8.0
                            q_vals[RLAction.STEER_LEFT] = 5.0
                        elif h == 3:
                            q_vals[RLAction.STEER_RIGHT] = 8.0
                            q_vals[RLAction.FORWARD_SLOW] = 4.0
                        elif h == 4:
                            q_vals[RLAction.PIVOT_RIGHT] = 8.0
                            q_vals[RLAction.STEER_RIGHT] = 5.0
                        elif h == 5:
                            q_vals[RLAction.PIVOT_RIGHT] = 8.0
                            q_vals[RLAction.PIVOT_LEFT] = 7.0

                    self.q_table[key] = q_vals

    def _get_q_values(self, state: RLState) -> List[float]:
        key = state.to_key()
        if key not in self.q_table:
            self.q_table[key] = [0.0] * RLAction.NUM_ACTIONS
        return self.q_table[key]

    def select_action(self, state: RLState, explore: bool = True) -> int:
        """Epsilon-greedy action selection."""
        import random
        q_vals = self._get_q_values(state)

        # Exploration
        if explore and random.random() < self.epsilon:
            return random.randint(0, RLAction.NUM_ACTIONS - 1)

        # Exploitation: pick action with maximum Q-value
        max_q = max(q_vals)
        best_actions = [i for i, q in enumerate(q_vals) if math.isclose(q, max_q, rel_tol=1e-5)]
        return random.choice(best_actions)

    def calculate_reward(
        self,
        current_dist: float,
        prev_dist: float,
        heading_err_deg: float,
        is_arrived: bool,
        is_critical_obstacle: bool
    ) -> float:
        """
        Calculate reinforcement reward:
        - Strong positive reward when distance to marker decreases.
        - Heavy negative penalty when car moves away / opposite from marker.
        - Heading alignment bonus when facing the marker.
        - Arrival bonus and collision penalty.
        """
        dist_delta = prev_dist - current_dist  # Positive if getting closer!
        
        # 1. Distance progress component (scaled)
        reward = dist_delta * 0.25

        # 2. Heading alignment component: cos(heading_error)
        heading_cos = math.cos(math.radians(heading_err_deg))
        reward += heading_cos * 0.4

        # 3. Penalty for moving in opposite direction (distance increasing)
        if dist_delta < -1.5:
            # Car is actively driving away from marker!
            reward -= 6.0
            self._opposite_motion_count += 1
        elif dist_delta > 1.5:
            self._progress_count += 1

        # 4. Arrival Bonus
        if is_arrived:
            reward += 40.0

        # 5. Critical Obstacle Collision Penalty
        if is_critical_obstacle:
            reward -= 25.0

        # 6. Small step time penalty to encourage rapid completion
        reward -= 0.05

        return reward

    def update(
        self,
        dist_px: float,
        heading_err_deg: float,
        us_left_cm: float = 100.0,
        us_right_cm: float = 100.0,
        us_front_cm: float = 100.0,
        arrival_dist_px: float = 35.0
    ) -> Tuple[float, float, str]:
        """
        Execute one RL decision cycle:
        1. Form current state.
        2. Perform TD(0) Q-learning update if last step exists.
        3. Select next action from Q-table.
        4. Return (throttle, steering, action_name).
        """
        is_arrived = (dist_px <= arrival_dist_px)
        is_critical = (us_front_cm < 18.0 or us_left_cm < 15.0 or us_right_cm < 15.0)

        current_state = RLState.from_continuous(
            dist_px=dist_px,
            heading_err_deg=heading_err_deg,
            us_left_cm=us_left_cm,
            us_right_cm=us_right_cm,
            us_front_cm=us_front_cm,
            arrival_dist_px=arrival_dist_px
        )

        # Learn from previous transition (s, a, r, s')
        if self.last_state is not None and self.last_action is not None and self.last_dist is not None:
            reward = self.calculate_reward(
                current_dist=dist_px,
                prev_dist=self.last_dist,
                heading_err_deg=heading_err_deg,
                is_arrived=is_arrived,
                is_critical_obstacle=is_critical
            )
            self.last_reward = reward
            self.total_episode_reward += reward

            # Bellman update: Q(s, a) = Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]
            prev_q_vals = self._get_q_values(self.last_state)
            curr_q_vals = self._get_q_values(current_state)
            best_next_q = max(curr_q_vals)
            
            old_q = prev_q_vals[self.last_action]
            target_q = reward + self.gamma * best_next_q
            prev_q_vals[self.last_action] = old_q + self.alpha * (target_q - old_q)

            # Auto-detect hardware opposite wiring:
            # If after 15 steps the car consistently moves away on forward actions
            if self._opposite_motion_count > 12 and self._progress_count < 3 and not self.auto_inversion_detected:
                logger.warning("[RL AGENT] Consistent opposite motion detected! Re-inforcing reversed action mapping.")
                self.auto_inversion_detected = True

        # Select next action
        if is_arrived:
            action_idx = RLAction.STOP
        else:
            action_idx = self.select_action(current_state, explore=True)

        self.last_state = current_state
        self.last_action = action_idx
        self.last_dist = dist_px
        self.last_heading_err = heading_err_deg
        self.step_count += 1

        # Periodically save Q-table every 100 steps
        if self.step_count % 100 == 0:
            self.save_q_table()

        throttle, steering = RLAction.ACTION_MAP[action_idx]
        action_name = RLAction.NAMES[action_idx]

        # If automatic polarity inversion was detected, flip throttle to drive forward
        if self.auto_inversion_detected and throttle != 0.0:
            throttle = -throttle

        return throttle, steering, action_name

    def reset_episode(self):
        """Reset trajectory tracking for a new target or after arrival."""
        self.last_state = None
        self.last_action = None
        self.last_dist = None
        self.last_heading_err = None
        self.total_episode_reward = 0.0

    def save_q_table(self):
        """Persist learned Q-table to disk."""
        if not self.save_path or self.save_path == ":memory:":
            return
        try:
            p = Path(self.save_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w") as f:
                json.dump(self.q_table, f)
            logger.debug(f"Saved RL Q-table to {self.save_path}")
        except Exception as e:
            logger.debug(f"Could not save Q-table: {e}")

    def load_q_table(self):
        """Load previously learned Q-table if available."""
        if not self.save_path or self.save_path == ":memory:":
            return
        try:
            p = Path(self.save_path)
            if p.exists():
                with open(p, "r") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.q_table.update(data)
                    logger.info(f"Loaded {len(data)} learned states into RL Q-table.")
        except Exception as e:
            logger.debug(f"Could not load Q-table: {e}")
