"""Headless integration test for MainWindow and overall system loop."""

import os
import unittest
import numpy as np

# Use offscreen platform for headless test execution
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from aruconav.config import AppConfig
from aruconav.gui.main_window import MainWindow


class TestGuiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_simulation_run(self):
        """Verify MainWindow initializes, runs loop steps, responds to waypoints, and updates logs."""
        config = AppConfig()
        config.camera.camera_index = -1  # Simulator
        window = MainWindow(config)

        # 1. Verify UI components initialized
        self.assertIsNotNone(window.video_widget)
        self.assertIsNotNone(window.telemetry_widget)
        self.assertIsNotNone(window.log_widget)

        # 2. Run initial update step
        window._main_loop_step()

        # 3. Simulate user clicking a waypoint
        window._on_waypoint_clicked(1100.0, 600.0, append=False)
        self.assertEqual(len(window.motion_planner.waypoints), 1)

        # 4. Advance simulation and control loop steps
        window._main_loop_step()
        self.assertIsNotNone(window._active_command)
        self.assertEqual(window._active_command.mode, "AUTO")

        for _ in range(10):
            window._main_loop_step()

        self.assertIn(window._active_command.mode, ["AUTO", "BRAKING", "ARRIVED", "EVASION", "IDLE"])

        # 5. Test Emergency Stop
        window._on_emergency_stop()
        window._main_loop_step()
        self.assertTrue(window.motion_planner.is_emergency_stopped)
        self.assertEqual(window._active_command.mode, "STOPPED")

        # 6. Test Manual mode
        window._on_emergency_stop()  # Clear E-STOP
        window.manual_cb.setChecked(True)
        window.motion_planner.set_manual_override(True, throttle=0.8, steering=0.2)
        window._main_loop_step()
        self.assertEqual(window._active_command.mode, "MANUAL")
        self.assertGreater(window._active_command.v_left, 0)

        # 7. Test Max Speed Slider
        window.speed_slider.setValue(220)
        self.assertEqual(window.config.control.max_pwm, 220)
        self.assertEqual(window.motion_planner.control_config.max_pwm, 220)
        self.assertIn("220", window.speed_label.text())

        # 8. Test Clear Trail
        window.motion_planner.breadcrumbs.append((100.0, 100.0))
        self.assertGreater(len(window.motion_planner.breadcrumbs), 0)
        window.clear_trail_btn.click()
        self.assertEqual(len(window.motion_planner.breadcrumbs), 0)

        # 9. Test Camera 4 is listed in Camera dropdown
        combo_indices = [window.camera_combo.itemData(i) for i in range(window.camera_combo.count())]
        self.assertIn(4, combo_indices, "Camera 4 must be present in camera dropdown")

        # Clean shutdown
        window.close()


if __name__ == "__main__":
    unittest.main()
