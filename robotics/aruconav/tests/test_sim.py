"""Unit tests for the 2D kinematics physics simulator."""

import unittest
from aruconav.sim.car_simulator import CarSimulator


class TestCarSimulator(unittest.TestCase):
    def setUp(self):
        self.sim = CarSimulator()

    def test_forward_motion(self):
        self.sim.reset_position(x=500.0, y=500.0, theta=0.0)
        self.sim.set_motor_pwm(200, 200)

        # Step 0.5 seconds
        for _ in range(10):
            self.sim.step(dt=0.05)

        self.assertGreater(self.sim.x, 500.0, "Car should have moved in +X direction")
        self.assertAlmostEqual(self.sim.y, 500.0, delta=1.0)

    def test_ultrasonic_raycasting(self):
        """Ultrasonic sensors should detect nearby obstacles."""
        # Place obstacle at (600, 500)
        self.sim.clear_obstacles()
        self.sim.add_obstacle(600.0, 500.0, radius=30.0)
        self.sim.reset_position(x=500.0, y=500.0, theta=0.0)

        us_l, us_f, us_r = self.sim.read_ultrasonic_sensors()
        self.assertLess(us_l, 100.0, "Left sensor should detect obstacle")
        self.assertLess(us_f, 100.0, "Front sensor should detect obstacle")
        self.assertLess(us_r, 100.0, "Right sensor should detect obstacle")

    def test_synthetic_frame_rendering(self):
        """Frame rendering produces valid 3-channel image."""
        frame = self.sim.render_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame.shape[0], self.sim.height)
        self.assertEqual(frame.shape[1], self.sim.width)
        self.assertEqual(frame.shape[2], 3)


if __name__ == "__main__":
    unittest.main()
