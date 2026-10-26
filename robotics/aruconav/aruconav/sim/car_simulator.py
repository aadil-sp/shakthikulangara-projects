"""2D kinematic RC car simulator with raycasting ultrasonic sensors and synthetic camera rendering."""

import math
import random
import time
from typing import List, Tuple, Dict, Any, Optional
import cv2
import numpy as np

from aruconav.config import CameraConfig, ArucoConfig


ObstacleTuple = Tuple[float, float, float]  # (x, y, radius)


class CarSimulator:
    """Simulates 2D differential-drive vehicle kinematics, obstacles, and synthetic camera rendering."""

    def __init__(self, camera_cfg: Optional[CameraConfig] = None, aruco_cfg: Optional[ArucoConfig] = None):
        self.cam_cfg = camera_cfg or CameraConfig()
        self.aruco_cfg = aruco_cfg or ArucoConfig()

        self.width = self.cam_cfg.frame_width
        self.height = self.cam_cfg.frame_height

        # Car state (pixel coordinates)
        self.x: float = self.width / 2.0
        self.y: float = self.height / 2.0
        self.theta: float = 0.0  # radians (0 = right)
        self.linear_vel: float = 0.0
        self.angular_vel: float = 0.0

        # Car physical dimensions (pixels)
        self.car_len: float = 65.0
        self.car_wid: float = 45.0
        self.marker_size: int = 38

        # Comm inputs
        self.v_left_pwm: int = 0
        self.v_right_pwm: int = 0

        # Obstacles list of (x, y, radius)
        self.obstacles: List[Tuple[float, float, float]] = [
            (320.0, 240.0, 35.0),
            (880.0, 260.0, 42.0),
            (420.0, 520.0, 30.0),
            (820.0, 500.0, 38.0),
            (640.0, 360.0, 25.0)
        ]

        self._last_sim_time = time.time()
        self._marker_img = self._generate_marker_image()

    def _generate_marker_image(self) -> np.ndarray:
        """Generate synthetic ArUco marker bitmap."""
        dict_id = cv2.aruco.DICT_4X4_50
        dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        marker_id = max(0, self.aruco_cfg.target_marker_id)
        
        size = self.marker_size
        if hasattr(cv2.aruco, "generateImageMarker"):
            marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
        elif hasattr(cv2.aruco, "drawMarker"):
            marker = cv2.aruco.drawMarker(dictionary, marker_id, size)
        else:
            # Fallback high-contrast square pattern
            marker = np.zeros((size, size), dtype=np.uint8)
            marker[4:-4, 4:-4] = 255
            marker[8:-8, 8:-8] = 0

        if len(marker.shape) == 2:
            marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)
        else:
            marker_bgr = marker
        return marker_bgr

    def set_motor_pwm(self, v_left: int, v_right: int):
        """Set motor inputs from controller."""
        self.v_left_pwm = max(-255, min(255, v_left))
        self.v_right_pwm = max(-255, min(255, v_right))

    def reset_position(self, x: Optional[float] = None, y: Optional[float] = None, theta: float = 0.0):
        """Reset car location."""
        self.x = x if x is not None else self.width / 2.0
        self.y = y if y is not None else self.height / 2.0
        self.theta = theta
        self.linear_vel = 0.0
        self.angular_vel = 0.0

    def add_obstacle(self, x: float, y: float, radius: float = 35.0):
        """Add a new obstacle at coordinates."""
        self.obstacles.append((x, y, radius))

    def clear_obstacles(self):
        """Clear all obstacles."""
        self.obstacles.clear()

    def step(self, dt: Optional[float] = None):
        """Advance physics simulation by dt seconds."""
        now = time.time()
        if dt is None:
            dt = max(0.001, min(0.1, now - self._last_sim_time))
        self._last_sim_time = now

        # Convert PWM (-255..255) to wheel speeds (px/sec)
        max_speed_px = 220.0  # Max speed in pixels/sec
        v_l = (self.v_left_pwm / 255.0) * max_speed_px
        v_r = (self.v_right_pwm / 255.0) * max_speed_px

        # Differential drive kinematics
        # Track width ~ car_wid
        wheelbase = self.car_wid * 0.95
        target_v = (v_r + v_l) / 2.0
        target_w = (v_l - v_r) / wheelbase  # rad/sec (v_l > v_r turns right / +theta)

        # Smooth acceleration / inertia
        accel = 12.0
        self.linear_vel += (target_v - self.linear_vel) * min(1.0, accel * dt)
        self.angular_vel += (target_w - self.angular_vel) * min(1.0, accel * dt)

        # Update pose
        self.theta += self.angular_vel * dt
        self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))

        self.x += self.linear_vel * math.cos(self.theta) * dt
        self.y += self.linear_vel * math.sin(self.theta) * dt

        # Boundary collision clamping
        margin = 35.0
        self.x = max(margin, min(self.width - margin, self.x))
        self.y = max(margin, min(self.height - margin, self.y))

    def read_ultrasonic_sensors(self) -> Tuple[float, float, float]:
        """
        Raycast from 3 ultrasonic sensor mounts (Angle Left, Front Center, Angle Right) to obstacles.
        Returns: (us_left_cm, us_front_cm, us_right_cm) where ~2.2 pixels = 1.0 cm.
        """
        # Sensor mounting offsets relative to car center
        front_offset = self.car_len * 0.45
        lateral_offset = self.car_wid * 0.35

        # Left sensor: offset -lateral, angled at -32 deg
        left_angle = self.theta - math.radians(32.0)
        lx = self.x + front_offset * math.cos(self.theta) - lateral_offset * math.sin(self.theta)
        ly = self.y + front_offset * math.sin(self.theta) + lateral_offset * math.cos(self.theta)

        # Front sensor: center, facing straight ahead (0 deg offset)
        front_angle = self.theta
        fx = self.x + front_offset * math.cos(self.theta)
        fy = self.y + front_offset * math.sin(self.theta)

        # Right sensor: offset +lateral, angled at +32 deg
        right_angle = self.theta + math.radians(32.0)
        rx = self.x + front_offset * math.cos(self.theta) + lateral_offset * math.sin(self.theta)
        ry = self.y + front_offset * math.sin(self.theta) - lateral_offset * math.cos(self.theta)

        dist_left_px = self._raycast(lx, ly, left_angle, max_dist=400.0)
        dist_front_px = self._raycast(fx, fy, front_angle, max_dist=400.0)
        dist_right_px = self._raycast(rx, ry, right_angle, max_dist=400.0)

        # Conversion factor: 1 cm ~ 2.2 px
        px_to_cm = 1.0 / 2.2
        us_left_cm = max(2.0, min(180.0, dist_left_px * px_to_cm + random.uniform(-0.5, 0.5)))
        us_front_cm = max(2.0, min(180.0, dist_front_px * px_to_cm + random.uniform(-0.5, 0.5)))
        us_right_cm = max(2.0, min(180.0, dist_right_px * px_to_cm + random.uniform(-0.5, 0.5)))

        return us_left_cm, us_front_cm, us_right_cm

    def _raycast(self, origin_x: float, origin_y: float, angle_rad: float, max_dist: float = 400.0) -> float:
        """Find minimum distance along ray to any obstacle or wall."""
        min_dist = max_dist
        ray_dx = math.cos(angle_rad)
        ray_dy = math.sin(angle_rad)

        # Check circle obstacles
        for ox, oy, radius in self.obstacles:
            # Vector from ray origin to circle center
            fx = ox - origin_x
            fy = oy - origin_y

            # Project onto ray direction
            t = fx * ray_dx + fy * ray_dy
            if t <= 0:
                continue  # Behind ray

            # Closest point on ray to circle center
            closest_x = origin_x + t * ray_dx
            closest_y = origin_y + t * ray_dy
            dist_sq = (closest_x - ox)**2 + (closest_y - oy)**2

            if dist_sq < radius**2:
                # Ray intersects circle
                dt = math.sqrt(radius**2 - dist_sq)
                intersect_dist = t - dt
                if 0 < intersect_dist < min_dist:
                    min_dist = intersect_dist

        # Check arena boundaries
        if ray_dx > 0:
            d_wall = (self.width - origin_x) / ray_dx
            if 0 < d_wall < min_dist:
                min_dist = d_wall
        elif ray_dx < 0:
            d_wall = -origin_x / ray_dx
            if 0 < d_wall < min_dist:
                min_dist = d_wall

        if ray_dy > 0:
            d_wall = (self.height - origin_y) / ray_dy
            if 0 < d_wall < min_dist:
                min_dist = d_wall
        elif ray_dy < 0:
            d_wall = -origin_y / ray_dy
            if 0 < d_wall < min_dist:
                min_dist = d_wall

        return min_dist

    def render_frame(self) -> np.ndarray:
        """Render complete synthetic camera frame."""
        frame = np.full((self.height, self.width, 3), (28, 30, 36), dtype=np.uint8)

        # Draw Arena Grid
        grid_size = 60
        for gx in range(0, self.width, grid_size):
            cv2.line(frame, (gx, 0), (gx, self.height), (38, 42, 50), 1)
        for gy in range(0, self.height, grid_size):
            cv2.line(frame, (0, gy), (self.width, gy), (38, 42, 50), 1)

        # Draw Arena Boundary Border
        cv2.rectangle(frame, (10, 10), (self.width - 10, self.height - 10), (60, 65, 80), 2)

        # Draw Obstacles (Cylinders / Columns with depth shading)
        for ox, oy, radius in self.obstacles:
            center = (int(ox), int(oy))
            r = int(radius)
            # Shadow
            cv2.circle(frame, (center[0] + 4, center[1] + 4), r, (15, 15, 20), -1, cv2.LINE_AA)
            # Body
            cv2.circle(frame, center, r, (70, 75, 95), -1, cv2.LINE_AA)
            cv2.circle(frame, center, r, (120, 130, 160), 2, cv2.LINE_AA)
            # Highlight
            cv2.circle(frame, (center[0] - int(r * 0.3), center[1] - int(r * 0.3)), int(r * 0.3), (90, 98, 120), -1, cv2.LINE_AA)

        # Draw RC Car Chassis
        self._render_car(frame)

        return frame

    def _render_car(self, frame: np.ndarray):
        """Render rotated RC car body, wheels, sensors, and ArUco marker."""
        cx, cy = self.x, self.y
        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)

        hl = self.car_len / 2.0
        hw = self.car_wid / 2.0

        # Chassis corners in local frame: front-right, rear-right, rear-left, front-left
        corners_local = [
            (hl, hw),
            (-hl, hw),
            (-hl, -hw),
            (hl, -hw)
        ]

        # Rotate corners
        corners_global = []
        for lx, ly in corners_local:
            gx = int(cx + lx * cos_t - ly * sin_t)
            gy = int(cy + lx * sin_t + ly * cos_t)
            corners_global.append([gx, gy])

        pts = np.array(corners_global, dtype=np.int32)
        # Car Shadow
        cv2.fillPoly(frame, [pts + 5], (12, 14, 18), cv2.LINE_AA)
        # Car Body
        cv2.fillPoly(frame, [pts], (45, 50, 60), cv2.LINE_AA)
        cv2.polylines(frame, [pts], True, (90, 100, 120), 2, cv2.LINE_AA)

        # Front Bumper indicator
        front_pt1 = (int(cx + hl * cos_t - hw * 0.6 * sin_t), int(cy + hl * sin_t + hw * 0.6 * cos_t))
        front_pt2 = (int(cx + hl * cos_t + hw * 0.6 * sin_t), int(cy + hl * sin_t - hw * 0.6 * cos_t))
        cv2.line(frame, front_pt1, front_pt2, (0, 180, 255), 4, cv2.LINE_AA)

        # Wheels (4 black rectangles)
        wheel_len = 16
        wheel_wid = 7
        wheel_offsets = [
            (hl * 0.65, hw + 2),
            (-hl * 0.65, hw + 2),
            (-hl * 0.65, -hw - 2),
            (hl * 0.65, -hw - 2),
        ]
        for w_lx, w_ly in wheel_offsets:
            w_gx = int(cx + w_lx * cos_t - w_ly * sin_t)
            w_gy = int(cy + w_lx * sin_t + w_ly * cos_t)
            cv2.circle(frame, (w_gx, w_gy), 5, (10, 10, 10), -1, cv2.LINE_AA)

        # Draw ArUco Marker onto roof with white border
        self._paste_rotated_marker(frame, int(cx), int(cy), self.theta)

    def _paste_rotated_marker(self, frame: np.ndarray, cx: int, cy: int, angle_rad: float):
        """Overlay rotated ArUco marker with high-contrast white border using perspective transform."""
        if self._marker_img is None:
            return

        border_size = 8
        bordered = cv2.copyMakeBorder(
            self._marker_img, border_size, border_size, border_size, border_size,
            cv2.BORDER_CONSTANT, value=[255, 255, 255]
        )

        h, w = bordered.shape[:2]
        src_pts = np.array([
            [0, 0],
            [w - 1, 0],
            [w - 1, h - 1],
            [0, h - 1]
        ], dtype=np.float32)

        half = w / 2.0
        cos_t = math.cos(angle_rad)
        sin_t = math.sin(angle_rad)

        # Local corner positions: Top edge of marker points towards car front (+X)
        local_corners = [
            (half, -half),
            (half, half),
            (-half, half),
            (-half, -half)
        ]

        dst_pts = np.array([
            [cx + lx * cos_t - ly * sin_t, cy + lx * sin_t + ly * cos_t]
            for lx, ly in local_corners
        ], dtype=np.float32)

        try:
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(
                bordered, M, (self.width, self.height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0)
            )

            mask = np.zeros((self.height, self.width), dtype=np.uint8)
            cv2.fillConvexPoly(mask, dst_pts.astype(np.int32), 255)
            frame[mask == 255] = warped[mask == 255]
        except Exception:
            pass
