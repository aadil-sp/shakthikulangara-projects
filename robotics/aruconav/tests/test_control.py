"""Unit tests for motion planning and obstacle avoidance."""

import unittest
import numpy as np

from aruconav.config import ControlConfig, ObstacleConfig
from aruconav.control.motion_planner import MotionPlanner
from aruconav.control.obstacle_avoidance import ObstacleAvoidanceController, AvoidanceState
from aruconav.vision.aruco_tracker import MarkerPose


class TestMotionPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = MotionPlanner(rl_save_path=":memory:")

    def test_idle_when_no_waypoints(self):
        """Planner should output 0 PWM when no target waypoint is set."""
        pose = MarkerPose(0, 100, 100, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        cmd, avoidance = self.planner.update(pose, 100.0, 100.0)
        self.assertEqual(cmd.mode, "IDLE")
        self.assertEqual(cmd.v_left, 0)
        self.assertEqual(cmd.v_right, 0)

    def test_straight_forward_navigation(self):
        """Car facing target directly ahead should command forward throttle with 0 steering."""
        # Car at (100, 100), facing angle 0 (right). Target at (300, 100) (directly to the right)
        pose = MarkerPose(0, 100.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        self.planner.add_waypoint(300.0, 100.0)

        cmd, avoidance = self.planner.update(pose, 100.0, 100.0)
        self.assertEqual(cmd.mode, "AUTO")
        self.assertGreater(cmd.v_left, 0)
        self.assertGreater(cmd.v_right, 0)
        self.assertEqual(cmd.v_left, cmd.v_right)
        self.assertAlmostEqual(cmd.heading_err_deg, 0.0, delta=2.0)

    def test_waypoint_arrival(self):
        """Car within arrival radius should pop waypoint and arrive."""
        pose = MarkerPose(0, 100.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        # Target within 10px (arrival threshold is 35px)
        self.planner.add_waypoint(105.0, 100.0)

        cmd, avoidance = self.planner.update(pose, 100.0, 100.0)
        self.assertEqual(cmd.mode, "ARRIVED")
        self.assertEqual(cmd.v_left, 0)
        self.assertEqual(cmd.v_right, 0)

    def test_progressive_target_braking_zone(self):
        """Car inside slowdown distance must enter BRAKING mode and scale down speed."""
        pose = MarkerPose(0, 100.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        # Target at 180.0 px (distance = 80 px, inside the 160 px braking zone)
        self.planner.add_waypoint(180.0, 100.0)

        cmd, _ = self.planner.update(pose, 100.0, 100.0)
        self.assertEqual(cmd.mode, "BRAKING")
        self.assertLess(cmd.speed_norm, 0.6, "Speed must be progressively throttled in braking zone")

    def test_speed_ramping_from_smaller_value(self):
        """Speed must ramp up progressively starting from min_pwm, not jumping to max immediately."""
        pose = MarkerPose(0, 100.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        # Distant target ahead
        self.planner.add_waypoint(500.0, 100.0)
        self.planner.control_config.max_pwm = 200
        self.planner.control_config.min_pwm = 55
        self.planner.control_config.accel_rate_pwm_per_sec = 200.0

        # Step 1: Initial start from stop
        cmd1, _ = self.planner.update(pose, 100.0, 100.0)
        # Should start from min_pwm (around 55-65)
        self.assertGreaterEqual(cmd1.v_left, 55)
        self.assertLess(cmd1.v_left, 100)

        # Step 2: Next step should be higher than Step 1
        import time
        time.sleep(0.05)
        cmd2, _ = self.planner.update(pose, 100.0, 100.0)
        self.assertGreater(cmd2.v_left, cmd1.v_left)

    def test_clear_breadcrumbs(self):
        """Path tracing / breadcrumbs must be clearable."""
        pose1 = MarkerPose(0, 100.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        self.planner.update(pose1, 100.0, 100.0)
        pose2 = MarkerPose(0, 120.0, 100.0, 0.0, 0.0, np.zeros((4, 2)), 1.0, 1.0)
        self.planner.update(pose2, 100.0, 100.0)

        self.assertGreater(len(self.planner.breadcrumbs), 0)
        self.planner.clear_breadcrumbs()
        self.assertEqual(len(self.planner.breadcrumbs), 0)


class TestObstacleAvoidance(unittest.TestCase):
    def setUp(self):
        self.obs_ctrl = ObstacleAvoidanceController(ObstacleConfig(enabled=True))

    def test_clear_path(self):
        res = self.obs_ctrl.evaluate(100.0, 100.0)
        self.assertEqual(res.state, AvoidanceState.CLEAR)
        self.assertAlmostEqual(res.steering_bias, 0.0)
        self.assertEqual(res.speed_scale, 1.0)

    def test_warning_left_obstacle(self):
        """Obstacle on left sensor (42cm) should deflect steering to the right (+)."""
        res = self.obs_ctrl.evaluate(42.0, 100.0)
        self.assertEqual(res.state, AvoidanceState.WARNING_LEFT)
        self.assertGreater(res.steering_bias, 0.0, "Should steer right to avoid left obstacle")

    def test_critical_evasion(self):
        """Close obstacle (<28cm) should trigger critical evasion."""
        res = self.obs_ctrl.evaluate(18.0, 80.0)
        self.assertEqual(res.state, AvoidanceState.CRITICAL_EVASION)
        self.assertTrue(res.is_critical)
        self.assertGreater(res.steering_bias, 0.5)

    def test_disabled_avoidance(self):
        """When disabled, sensors are ignored and state remains CLEAR."""
        disabled_ctrl = ObstacleAvoidanceController(ObstacleConfig(enabled=False))
        res = disabled_ctrl.evaluate(10.0, 10.0)
        self.assertEqual(res.state, AvoidanceState.CLEAR)
        self.assertEqual(res.speed_scale, 1.0)
        self.assertEqual(res.steering_bias, 0.0)


if __name__ == "__main__":
    unittest.main()
