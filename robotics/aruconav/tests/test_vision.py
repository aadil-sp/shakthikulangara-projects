"""Unit tests for ArUco marker detection and pose estimation."""

import unittest
import numpy as np
import cv2

from aruconav.config import ArucoConfig
from aruconav.vision.aruco_tracker import ArucoTracker, MarkerPose


class TestArucoTracker(unittest.TestCase):
    def setUp(self):
        self.config = ArucoConfig(target_marker_id=0, smoothing_factor=0.8)
        self.tracker = ArucoTracker(self.config)

    def test_synthetic_marker_detection(self):
        """Verify tracker reliably identifies an ArUco marker generated in-memory."""
        # Create blank white image
        img = np.full((400, 400, 3), 255, dtype=np.uint8)

        # Generate ArUco marker ID 0
        dict_id = cv2.aruco.DICT_4X4_50
        dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        if hasattr(cv2.aruco, "generateImageMarker"):
            marker = cv2.aruco.generateImageMarker(dictionary, 0, 100)
        else:
            marker = cv2.aruco.drawMarker(dictionary, 0, 100)
        marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)

        # Paste marker centered at (200, 200) -> bbox from (150, 150) to (250, 250)
        img[150:250, 150:250] = marker_bgr

        target_pose, all_poses = self.tracker.detect(img, timestamp=1.0)

        self.assertIsNotNone(target_pose, "Should detect target marker ID 0")
        self.assertEqual(target_pose.id, 0)
        self.assertAlmostEqual(target_pose.x, 200.0, delta=3.0)
        self.assertAlmostEqual(target_pose.y, 200.0, delta=3.0)
        self.assertEqual(len(all_poses), 1)

    def test_smoothing_filter(self):
        """Verify EMA smoothing dampens coordinate jumps."""
        p1 = MarkerPose(id=0, x=100.0, y=100.0, angle_rad=0.0, angle_deg=0.0, corners=np.zeros((4, 2)), confidence=1.0, timestamp=1.0)
        p2 = MarkerPose(id=0, x=120.0, y=100.0, angle_rad=0.0, angle_deg=0.0, corners=np.zeros((4, 2)), confidence=1.0, timestamp=1.1)

        smoothed_1 = self.tracker._apply_smoothing(p1)
        self.assertAlmostEqual(smoothed_1.x, 100.0)

        smoothed_2 = self.tracker._apply_smoothing(p2)
        # alpha=0.8: 0.8 * 120 + 0.2 * 100 = 96 + 20 = 116.0
        self.assertAlmostEqual(smoothed_2.x, 116.0, delta=0.5)


if __name__ == "__main__":
    unittest.main()
