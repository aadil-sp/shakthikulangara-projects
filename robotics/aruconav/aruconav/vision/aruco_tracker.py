"""ArUco marker detection, pose tracking, and smoothing filter."""

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List
import cv2
import numpy as np

from aruconav.config import ArucoConfig


@dataclass
class MarkerPose:
    """Estimated 2D pose and spatial geometry of tracked ArUco marker."""
    id: int
    x: float             # Center X in image pixels
    y: float             # Center Y in image pixels
    angle_rad: float     # Heading angle in radians (-pi to +pi, 0 rad = right / +X)
    angle_deg: float     # Heading angle in degrees (-180 to +180)
    corners: np.ndarray  # 4x2 array of corner coordinates [[c0], [c1], [c2], [c3]]
    confidence: float    # Detection quality/confidence
    timestamp: float     # Detection timestamp


class ArucoTracker:
    """Robust ArUco marker detector with angle calculation and EMA smoothing."""

    DICTIONARY_MAP = {
        "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
        "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
        "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
        "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
        "DICT_5X5_100": cv2.aruco.DICT_5X5_100,
        "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        "DICT_6X6_250": cv2.aruco.DICT_6X6_250,
        "DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
    }

    def __init__(self, config: Optional[ArucoConfig] = None):
        self.config = config or ArucoConfig()
        self._init_detector()

        # Smoothed state cache (per marker ID)
        self._smoothed_poses: Dict[int, MarkerPose] = {}

    def _init_detector(self):
        """Initialize OpenCV ArUco dictionary and detector parameters."""
        dict_id = self.DICTIONARY_MAP.get(self.config.dictionary_name, cv2.aruco.DICT_4X4_50)
        self.dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        
        # Detector parameters
        if hasattr(cv2.aruco, "DetectorParameters_create"):
            self.parameters = cv2.aruco.DetectorParameters_create()
        else:
            self.parameters = cv2.aruco.DetectorParameters()

        if self.config.enable_corner_refinement:
            if hasattr(cv2.aruco, "CORNER_REFINE_SUBPIX"):
                self.parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        # New OpenCV 4.7+ detector object
        if hasattr(cv2.aruco, "ArucoDetector"):
            self.detector = cv2.aruco.ArucoDetector(self.dictionary, self.parameters)
        else:
            self.detector = None

    def set_dictionary(self, dict_name: str):
        """Dynamically change the ArUco dictionary."""
        if dict_name in self.DICTIONARY_MAP:
            self.config.dictionary_name = dict_name
            self._init_detector()
            self._smoothed_poses.clear()

    def set_target_id(self, marker_id: int):
        """Set the specific marker ID to track (-1 for any)."""
        self.config.target_marker_id = marker_id

    def detect(self, frame: np.ndarray, timestamp: float = 0.0) -> Tuple[Optional[MarkerPose], List[MarkerPose]]:
        """
        Detect ArUco markers in frame.
        
        Returns:
            (target_pose, all_detected_poses)
        """
        if frame is None or frame.size == 0:
            return None, []

        # Convert to grayscale for robust corner detection
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Detect markers using either ArucoDetector or detectMarkers
        if self.detector is not None:
            corners, ids, rejected = self.detector.detectMarkers(gray)
        else:
            corners, ids, rejected = cv2.aruco.detectMarkers(gray, self.dictionary, parameters=self.parameters)

        all_poses: List[MarkerPose] = []
        target_pose: Optional[MarkerPose] = None

        if ids is not None and len(ids) > 0:
            ids_flat = ids.flatten()
            for idx, marker_id in enumerate(ids_flat):
                c = corners[idx][0]  # shape: (4, 2) - [top-left, top-right, bottom-right, bottom-left]
                
                # Center point
                cx = float(np.mean(c[:, 0]))
                cy = float(np.mean(c[:, 1]))

                # Heading vector: from center of top edge (between c[0] and c[1]) or from bottom to top
                # c[0]: top-left, c[1]: top-right, c[2]: bottom-right, c[3]: bottom-left
                # Vector pointing towards marker "UP" / "FRONT"
                front_mid = (c[0] + c[1]) / 2.0
                back_mid = (c[2] + c[3]) / 2.0
                dx = float(front_mid[0] - back_mid[0])
                dy = float(front_mid[1] - back_mid[1])
                
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)

                raw_pose = MarkerPose(
                    id=int(marker_id),
                    x=cx,
                    y=cy,
                    angle_rad=angle_rad,
                    angle_deg=angle_deg,
                    corners=c,
                    confidence=1.0,
                    timestamp=timestamp
                )

                # Apply smoothing filter
                smoothed_pose = self._apply_smoothing(raw_pose)
                all_poses.append(smoothed_pose)

                # Check if this is our target marker
                if self.config.target_marker_id == -1 or int(marker_id) == self.config.target_marker_id:
                    if target_pose is None:
                        target_pose = smoothed_pose

        # Fallback to first detected marker if configured target_marker_id was not found
        if target_pose is None and len(all_poses) > 0:
            target_pose = all_poses[0]

        return target_pose, all_poses

    def _apply_smoothing(self, raw_pose: MarkerPose) -> MarkerPose:
        """Apply Exponential Moving Average (EMA) to smooth out pixel noise and angle jumps."""
        alpha = self.config.smoothing_factor  # e.g., 0.75
        marker_id = raw_pose.id

        if marker_id not in self._smoothed_poses:
            self._smoothed_poses[marker_id] = raw_pose
            return raw_pose

        prev = self._smoothed_poses[marker_id]

        # Smooth position
        smooth_x = alpha * raw_pose.x + (1 - alpha) * prev.x
        smooth_y = alpha * raw_pose.y + (1 - alpha) * prev.y

        # Smooth angle with circular wraparound handling (-pi to +pi)
        diff_rad = math.atan2(
            math.sin(raw_pose.angle_rad - prev.angle_rad),
            math.cos(raw_pose.angle_rad - prev.angle_rad)
        )
        smooth_angle_rad = prev.angle_rad + alpha * diff_rad
        # Normalize to [-pi, pi]
        smooth_angle_rad = math.atan2(math.sin(smooth_angle_rad), math.cos(smooth_angle_rad))
        smooth_angle_deg = math.degrees(smooth_angle_rad)

        # Smooth corners
        smooth_corners = alpha * raw_pose.corners + (1 - alpha) * prev.corners

        smoothed = MarkerPose(
            id=marker_id,
            x=smooth_x,
            y=smooth_y,
            angle_rad=smooth_angle_rad,
            angle_deg=smooth_angle_deg,
            corners=smooth_corners,
            confidence=raw_pose.confidence,
            timestamp=raw_pose.timestamp
        )
        self._smoothed_poses[marker_id] = smoothed
        return smoothed
