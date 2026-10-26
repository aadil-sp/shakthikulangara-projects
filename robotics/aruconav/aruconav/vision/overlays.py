"""Overhead HUD visual overlays, waypoint markers, heading vectors, and sensor cones."""

import math
from typing import List, Tuple, Optional, Dict, Any
import cv2
import numpy as np

from aruconav.vision.aruco_tracker import MarkerPose


def _get_sensor_color(dist_cm: float, warning_cm: float = 35.0, critical_cm: float = 18.0) -> Tuple[int, int, int]:
    """Return BGR color corresponding to ultrasonic distance (Red=Critical, Yellow=Warning, Green=Clear)."""
    if dist_cm <= critical_cm:
        return (40, 40, 240)  # Bright Red
    elif dist_cm <= warning_cm:
        return (30, 200, 255) # Warning Amber/Yellow
    else:
        return (80, 220, 80)  # Clear Green


def draw_hud_overlays(
    frame: np.ndarray,
    target_pose: Optional[MarkerPose],
    all_poses: List[MarkerPose],
    waypoints: List[Tuple[float, float]],
    breadcrumbs: List[Tuple[float, float]],
    ultrasonic_data: Dict[str, float],
    state_info: Dict[str, Any],
    warning_cm: float = 35.0,
    critical_cm: float = 18.0,
) -> np.ndarray:
    """
    Render all HUD graphics on top of the video frame.
    """
    h, w, _ = frame.shape
    overlay = frame.copy()

    # 1. Draw Breadcrumbs (past trajectory trail)
    if len(breadcrumbs) > 1:
        for i in range(1, len(breadcrumbs)):
            pt1 = (int(breadcrumbs[i - 1][0]), int(breadcrumbs[i - 1][1]))
            pt2 = (int(breadcrumbs[i][0]), int(breadcrumbs[i][1]))
            # Fade alpha / thickness towards the end
            thickness = max(1, int(2 * (i / len(breadcrumbs))))
            cv2.line(frame, pt1, pt2, (180, 180, 50), thickness, cv2.LINE_AA)

    # 2. Draw Waypoints & Path
    if waypoints:
        # Draw path connecting waypoints
        pts = []
        if target_pose is not None:
            pts.append((int(target_pose.x), int(target_pose.y)))
        pts.extend([(int(wx), int(wy)) for wx, wy in waypoints])

        for i in range(len(pts) - 1):
            cv2.line(frame, pts[i], pts[i + 1], (255, 140, 0), 2, cv2.LINE_AA)

        # Draw each waypoint marker
        for idx, (wx, wy) in enumerate(waypoints):
            pt = (int(wx), int(wy))
            is_active = (idx == 0)
            color = (0, 215, 255) if is_active else (160, 160, 160)
            radius = 16 if is_active else 10

            # Target Crosshairs
            cv2.circle(frame, pt, radius, color, 2, cv2.LINE_AA)
            cv2.circle(frame, pt, 4, color, -1, cv2.LINE_AA)
            cv2.line(frame, (pt[0] - radius - 6, pt[1]), (pt[0] + radius + 6, pt[1]), color, 1, cv2.LINE_AA)
            cv2.line(frame, (pt[0], pt[1] - radius - 6), (pt[0], pt[1] + radius + 6), color, 1, cv2.LINE_AA)

            # Waypoint label
            label = f"WP {idx + 1}" if len(waypoints) > 1 else "TARGET"
            cv2.putText(frame, label, (pt[0] + 12, pt[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

            # Target Braking Zone & Stop Zone Visualization
            if is_active:
                # 1. Stop Zone Circle (arrival radius = 35px)
                cv2.circle(frame, pt, 35, (0, 255, 0), 1, cv2.LINE_AA)
                cv2.putText(frame, "STOP AT TARGET", (pt[0] - 42, pt[1] + 48),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 255, 0), 1, cv2.LINE_AA)

                # 2. Progressive Braking Zone Circle (slowdown radius = 160px)
                cv2.circle(frame, pt, 160, (0, 180, 255), 1, cv2.LINE_AA)
                cv2.putText(frame, "BRAKING ZONE", (pt[0] - 38, pt[1] - 165),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36, (0, 180, 255), 1, cv2.LINE_AA)

    # 3. Draw All Detected Markers & Highlight Target Markers
    target_id = target_pose.id if target_pose is not None else -1
    for pose in all_poses:
        corners = pose.corners.astype(int)
        is_car = (pose.id == target_id)
        border_color = (0, 255, 0) if is_car else (255, 0, 255)  # Green for Car, Magenta for Goal Marker

        # Draw marker bounding box
        cv2.polylines(frame, [corners], True, border_color, 2, cv2.LINE_AA)
        
        # Draw corner dots
        for c_idx, corner in enumerate(corners):
            dot_color = (0, 0, 255) if c_idx == 0 else (255, 255, 0)
            cv2.circle(frame, tuple(corner), 3, dot_color, -1)

        # Label Marker ID and Role
        label = f"CAR [ID: {pose.id}]" if is_car else f"GOAL [ID: {pose.id}]"
        label_color = (0, 255, 255) if is_car else (255, 100, 255)
        cv2.putText(frame, label, (int(pose.x) - 35, int(pose.y) - 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, label_color, 1, cv2.LINE_AA)

        # If this is a goal marker and car is detected, draw targeting line
        if not is_car and target_pose is not None:
            cv2.line(frame, (int(target_pose.x), int(target_pose.y)), (int(pose.x), int(pose.y)), (255, 0, 200), 2, cv2.LINE_AA)
            cv2.circle(frame, (int(pose.x), int(pose.y)), 18, (255, 0, 255), 2, cv2.LINE_AA)

    # 4. Draw Active Tracked RC Car Pose & Sensors
    if target_pose is not None:
        cx, cy = int(target_pose.x), int(target_pose.y)
        angle = target_pose.angle_rad

        # Center indicator
        cv2.circle(frame, (cx, cy), 6, (0, 255, 0), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 22, (0, 255, 0), 2, cv2.LINE_AA)

        # Heading Vector Arrow (Length = 55px)
        arrow_len = 55
        hx = int(cx + arrow_len * math.cos(angle))
        hy = int(cy + arrow_len * math.sin(angle))
        cv2.arrowedLine(frame, (cx, cy), (hx, hy), (0, 255, 255), 3, cv2.LINE_AA, tipLength=0.3)

        # Ultrasonic Sensor Cones (Angle Left at -28 deg, Front Center at 0 deg, Angle Right at +28 deg)
        us_l = ultrasonic_data.get("us_l", 100.0)
        us_f = ultrasonic_data.get("us_f", 100.0)
        us_r = ultrasonic_data.get("us_r", 100.0)

        # Left sensor cone
        angle_l = angle - math.radians(28)
        color_l = _get_sensor_color(us_l, warning_cm, critical_cm)
        cone_len_l = min(120, max(20, int(us_l * 1.5)))
        sl_x = int(cx + 15 * math.cos(angle - math.pi / 2) + cone_len_l * math.cos(angle_l))
        sl_y = int(cy + 15 * math.sin(angle - math.pi / 2) + cone_len_l * math.sin(angle_l))
        cv2.line(frame, (cx, cy), (sl_x, sl_y), color_l, 2, cv2.LINE_AA)
        cv2.circle(frame, (sl_x, sl_y), 4, color_l, -1)
        cv2.putText(frame, f"L:{us_l:.0f}cm", (sl_x - 10, sl_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_l, 1, cv2.LINE_AA)

        # Front center sensor cone
        color_f = _get_sensor_color(us_f, warning_cm, critical_cm)
        cone_len_f = min(120, max(20, int(us_f * 1.5)))
        sf_x = int(cx + cone_len_f * math.cos(angle))
        sf_y = int(cy + cone_len_f * math.sin(angle))
        cv2.line(frame, (cx, cy), (sf_x, sf_y), color_f, 2, cv2.LINE_AA)
        cv2.circle(frame, (sf_x, sf_y), 4, color_f, -1)
        cv2.putText(frame, f"F:{us_f:.0f}cm", (sf_x - 10, sf_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_f, 1, cv2.LINE_AA)

        # Right sensor cone
        angle_r = angle + math.radians(28)
        color_r = _get_sensor_color(us_r, warning_cm, critical_cm)
        cone_len_r = min(120, max(20, int(us_r * 1.5)))
        sr_x = int(cx + 15 * math.cos(angle + math.pi / 2) + cone_len_r * math.cos(angle_r))
        sr_y = int(cy + 15 * math.sin(angle + math.pi / 2) + cone_len_r * math.sin(angle_r))
        cv2.line(frame, (cx, cy), (sr_x, sr_y), color_r, 2, cv2.LINE_AA)
        cv2.circle(frame, (sr_x, sr_y), 4, color_r, -1)
        cv2.putText(frame, f"R:{us_r:.0f}cm", (sr_x - 10, sr_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_r, 1, cv2.LINE_AA)

    # 5. Top-Left HUD Info Badge
    hud_bg_w, hud_bg_h = 300, 160
    sub_img = frame[10:10 + hud_bg_h, 10:10 + hud_bg_w]
    black_rect = np.zeros(sub_img.shape, dtype=np.uint8)
    res = cv2.addWeighted(sub_img, 0.25, black_rect, 0.75, 0)
    frame[10:10 + hud_bg_h, 10:10 + hud_bg_w] = res
    cv2.rectangle(frame, (10, 10), (10 + hud_bg_w, 10 + hud_bg_h), (70, 70, 80), 1)

    # HUD Texts
    fps = state_info.get("fps", 0.0)
    status = state_info.get("status", "IDLE")
    dist = state_info.get("target_dist", 0.0)
    heading_err = state_info.get("heading_err", 0.0)
    rl_action = state_info.get("rl_action", "")
    rl_reward = state_info.get("rl_reward", 0.0)
    
    cv2.putText(frame, "ARUCONAV REINFORCED HUD", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 215, 255), 1, cv2.LINE_AA)
    
    if target_pose:
        cv2.putText(frame, f"Car Pos: ({target_pose.x:.1f}, {target_pose.y:.1f}) px", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(frame, f"Heading: {target_pose.angle_deg:+.1f} deg", (20, 68),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)
    else:
        cv2.putText(frame, "Car: [NO MARKER DETECTED]", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 255), 1, cv2.LINE_AA)

    cv2.putText(frame, f"Target Dist: {dist:.1f} px | Err: {heading_err:+.1f} deg", (20, 88),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 220, 220), 1, cv2.LINE_AA)
    # Color and label styling based on motion state
    if status == "ARRIVED":
        status_label = "STOPPED AT TARGET"
        status_color = (0, 255, 0)
    elif status == "BRAKING":
        status_label = "BRAKING TO TARGET"
        status_color = (0, 215, 255)
    elif status == "AUTO":
        status_label = "CRUISING TO TARGET"
        status_color = (100, 255, 100)
    elif status == "STOPPED":
        status_label = "EMERGENCY STOP"
        status_color = (80, 80, 255)
    else:
        status_label = status
        status_color = (180, 180, 180)

    cv2.putText(frame, f"Mode: {status_label} | FPS: {fps:.1f}", (20, 108),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, status_color, 1, cv2.LINE_AA)
    cv2.putText(frame, f"Waypoints: {len(waypoints)}", (20, 126),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1, cv2.LINE_AA)

    if rl_action:
        cv2.putText(frame, f"RL Action: {rl_action} | Rew: {rl_reward:+.2f}", (20, 144),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 215, 0), 1, cv2.LINE_AA)

    return frame
