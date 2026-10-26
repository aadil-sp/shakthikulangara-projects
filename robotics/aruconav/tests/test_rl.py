"""Unit tests for Reinforcement Learning Navigation Agent."""

import unittest
from aruconav.control.rl_agent import RLNavigationAgent, RLState, RLAction


class TestRLNavigationAgent(unittest.TestCase):
    def setUp(self):
        # Create fresh agent with in-memory Q-table (no persistence file)
        self.agent = RLNavigationAgent(save_path="/tmp/test_rl_qtable.json")

    def test_state_discretization(self):
        """Test continuous state conversion to discrete bins."""
        # Ahead, Far, Clear
        s1 = RLState.from_continuous(dist_px=400.0, heading_err_deg=5.0)
        self.assertEqual(s1.dist_bin, 3)     # FAR
        self.assertEqual(s1.heading_bin, 0)  # AHEAD
        self.assertEqual(s1.obstacle_bin, 0) # CLEAR

        # Slight Left, Mid
        s2 = RLState.from_continuous(dist_px=180.0, heading_err_deg=-30.0)
        self.assertEqual(s2.dist_bin, 2)     # MID
        self.assertEqual(s2.heading_bin, 1)  # SLIGHT_LEFT

        # Arrived
        s3 = RLState.from_continuous(dist_px=20.0, heading_err_deg=0.0)
        self.assertEqual(s3.dist_bin, 0)     # ARRIVED

    def test_positive_reward_when_approaching(self):
        """Moving closer to the marker must yield positive reinforcement reward."""
        # Car was at 300px, now at 280px (approached by 20px)
        reward = self.agent.calculate_reward(
            current_dist=280.0,
            prev_dist=300.0,
            heading_err_deg=0.0,
            is_arrived=False,
            is_critical_obstacle=False
        )
        self.assertGreater(reward, 0.0, "Approaching marker must give positive reward")

    def test_negative_penalty_when_moving_opposite(self):
        """Moving away / opposite to marker must yield severe negative penalty."""
        # Car was at 200px, now at 220px (moved away by 20px)
        reward = self.agent.calculate_reward(
            current_dist=220.0,
            prev_dist=200.0,
            heading_err_deg=0.0,
            is_arrived=False,
            is_critical_obstacle=False
        )
        self.assertLess(reward, -5.0, "Moving opposite to marker must receive strong negative penalty")

    def test_q_table_bellman_update(self):
        """Verify Q-values update properly following Bellman equation."""
        s = RLState(dist_bin=3, heading_bin=0, obstacle_bin=0)
        self.agent.last_state = s
        self.agent.last_action = RLAction.FORWARD_FAST
        self.agent.last_dist = 400.0

        old_q = self.agent._get_q_values(s)[RLAction.FORWARD_FAST]
        # Step: closer to marker (350px)
        self.agent.update(dist_px=350.0, heading_err_deg=0.0)
        new_q = self.agent._get_q_values(s)[RLAction.FORWARD_FAST]

        self.assertGreater(new_q, old_q, "Positive progress should increase Q-value for forward action")

    def test_auto_inversion_when_hardware_opposite(self):
        """Agent should detect consistent opposite motion and flip throttle mapping."""
        # Simulate 15 steps of moving AWAY from marker when commanding forward
        dist = 200.0
        for _ in range(16):
            dist += 5.0  # distance increasing!
            self.agent.update(dist_px=dist, heading_err_deg=0.0)

        self.assertTrue(self.agent.auto_inversion_detected, "Agent must auto-detect hardware opposite wiring")


if __name__ == "__main__":
    unittest.main()
