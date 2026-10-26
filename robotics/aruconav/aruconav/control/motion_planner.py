"""Motion planner, Pure Pursuit / PID steering, and waypoint navigation."""

from dataclasses import dataclass
import math
import time
from typing import List, Tuple, Optional, Dict, Any

from aruconav.config import ControlConfig, ObstacleConfig
from aruconav.vision.aruco_tracker import MarkerPose
from aruconav.control.obstacle_avoidance import ObstacleAvoidanceController, AvoidanceResult, AvoidanceState
from aruconav.control.rl_agent import RLNavigationAgent, RLAction


@dataclass
class DriveCommand:
    """Motor control command packet."""
    v_left: int          # Left motor PWM (-255 to +255)
    v_right: int         # Right motor PWM (-255 to +255)
    steer_norm: float    # Normalized steering (-1.0 to +1.0)
    speed_norm: float    # Normalized throttle (-1.0 to +1.0)
    mode: str            # "AUTO", "MANUAL", "STOPPED", "EVASION"
    target_dist: float   # Distance to target in px
    heading_err_deg: float # Heading error in degrees
    timestamp: float
    rl_action: str = ""  # Action name from RL Agent (e.g. FWD_FAST, STEER_LEFT)
    rl_reward: float = 0.0 # Reinforcement reward from latest transition


class MotionPlanner:
    """Waypoint navigation controller with PID orientation tracking and obstacle avoidance."""

    def __init__(
        self,
        control_config: Optional[ControlConfig] = None,
        obstacle_config: Optional[ObstacleConfig] = None,
        rl_save_path: Optional[str] = "DEFAULT"
    ):
        self.control_config = control_config or ControlConfig()
        self.obstacle_controller = ObstacleAvoidanceController(obstacle_config)

        self.waypoints: List[Tuple[float, float]] = []
        self.breadcrumbs: List[Tuple[float, float]] = []
        self.max_breadcrumbs: int = 150

        # PID state for angular controller
        self._prev_angle_err: float = 0.0
        self._integral_angle_err: float = 0.0
        self._last_update_time: float = time.time()

        # Operational modes
        self.is_manual_mode: bool = False
        self.is_emergency_stopped: bool = False
        self._manual_throttle: float = 0.0
        self._manual_steering: float = 0.0

        # Speed ramping and soft-start state (without ENA/ENB)
        self._current_v_left: float = 0.0
        self._current_v_right: float = 0.0

        # Reinforcement Learning Navigation Agent
        if rl_save_path == "DEFAULT":
            self.rl_agent = RLNavigationAgent()
        else:
            self.rl_agent = RLNavigationAgent(save_path=rl_save_path)

    def add_waypoint(self, x: float, y: float, append: bool = False):
        """Add a waypoint. If append is False, replaces the existing queue."""
        if not append:
            self.waypoints = [(x, y)]
        else:
            self.waypoints.append((x, y))

    def clear_waypoints(self):
        """Clear all active waypoints."""
        self.waypoints.clear()
        self._current_v_left = 0.0
        self._current_v_right = 0.0
        self.rl_agent.reset_episode()

    def clear_breadcrumbs(self):
        """Clear trajectory breadcrumb trail / path tracing on screen."""
        self.breadcrumbs.clear()

    def clear_trail(self):
        """Alias for clear_breadcrumbs."""
        self.clear_breadcrumbs()

    def set_emergency_stop(self, stop: bool = True):
        """Toggle emergency stop."""
        self.is_emergency_stopped = stop
        self._current_v_left = 0.0
        self._current_v_right = 0.0
        self.rl_agent.reset_episode()
        if stop:
            self.clear_waypoints()

    def set_manual_override(self, enabled: bool, throttle: float = 0.0, steering: float = 0.0):
        """Set manual control inputs (WASD)."""
        self.is_manual_mode = enabled
        self._manual_throttle = max(-1.0, min(1.0, throttle))
        self._manual_steering = max(-1.0, min(1.0, steering))

    def _slew_ramp(self, current: float, target: float, dt: float) -> float:
        """
        Ramp motor speed gradually starting from a smaller minimum value (min_pwm) up to target PWM.
        Prevents inrush current, brownouts, and sudden wheel slip for direct 4-wire motor setups without ENA/ENB.
        """
        min_pwm = float(self.control_config.min_pwm)
        accel_rate = float(getattr(self.control_config, "accel_rate_pwm_per_sec", 300.0))

        # Target is complete stop
        if abs(target) < 1.0:
            if abs(current) <= min_pwm * 1.05:
                return 0.0
            step = accel_rate * 1.5 * dt
            if current > 0:
                return max(0.0, current - step)
            else:
                return min(0.0, current + step)

        # Starting from a standstill: soft-start from minimum PWM
        if current == 0.0:
            current = math.copysign(min_pwm, target)

        # Slew toward target speed
        step = accel_rate * dt
        if target > current:
            return min(target, current + step)
        elif target < current:
            return max(target, current - step)
        return current

    def update(
        self,
        car_pose: Optional[MarkerPose],
        us_left_cm: float = 100.0,
        us_right_cm: float = 100.0,
        us_front_cm: float = 100.0
    ) -> Tuple[DriveCommand, AvoidanceResult]:
        """
        Calculate next drive command based on car pose, waypoints, and ultrasonic sensors.
        """
        now = time.time()
        dt = max(0.001, min(0.1, now - self._last_update_time))
        self._last_update_time = now

        # Record breadcrumb
        if car_pose is not None:
            if not self.breadcrumbs or (math.hypot(car_pose.x - self.breadcrumbs[-1][0], car_pose.y - self.breadcrumbs[-1][1]) > 5.0):
                self.breadcrumbs.append((car_pose.x, car_pose.y))
                if len(self.breadcrumbs) > self.max_breadcrumbs:
                    self.breadcrumbs.pop(0)

        # 1. Emergency Stop Check
        if self.is_emergency_stopped:
            self._current_v_left = 0.0
            self._current_v_right = 0.0
            return DriveCommand(0, 0, 0.0, 0.0, "STOPPED", 0.0, 0.0, now), AvoidanceResult(
                AvoidanceState.CLEAR, 0.0, 0.0, False, "Emergency Stopped"
            )

        # 2. Evaluate Ultrasonic Obstacle Avoidance
        avoidance = self.obstacle_controller.evaluate(us_left_cm, us_right_cm, us_front_cm)

        # 3. Manual Override Mode
        if self.is_manual_mode:
            man_throttle = self._manual_throttle
            man_steering = self._manual_steering
            if getattr(self.control_config, "invert_throttle", False):
                man_throttle = -man_throttle
            if getattr(self.control_config, "invert_steering", False):
                man_steering = -man_steering

            target_l, target_r = self._diff_drive_from_norm(man_throttle, man_steering)
            v_l = int(self._slew_ramp(self._current_v_left, float(target_l), dt))
            v_r = int(self._slew_ramp(self._current_v_right, float(target_r), dt))
            self._current_v_left = float(v_l)
            self._current_v_right = float(v_r)
            return DriveCommand(v_l, v_r, man_steering, man_throttle, "MANUAL", 0.0, 0.0, now), avoidance

        # 4. If no marker detected or no waypoints -> Idle Stop
        if car_pose is None or not self.waypoints:
            self._current_v_left = 0.0
            self._current_v_right = 0.0
            self.rl_agent.reset_episode()
            return DriveCommand(0, 0, 0.0, 0.0, "IDLE", 0.0, 0.0, now), avoidance

        # 5. Waypoint Navigation
        target_x, target_y = self.waypoints[0]
        dx = target_x - car_pose.x
        dy = target_y - car_pose.y
        dist = math.hypot(dx, dy)

        slowdown_dist = getattr(self.control_config, "slowdown_distance_px", 160.0)
        arrival_dist = self.control_config.arrival_distance_px

        # Check if arrived at active waypoint -> Immediate Active Stop
        if dist <= arrival_dist:
            if len(self.waypoints) > 1:
                # Multiple waypoints: pop current and proceed to next waypoint
                self.waypoints.pop(0)
                self._integral_angle_err = 0.0
                self.rl_agent.reset_episode()
                self._current_v_left = 0.0
                self._current_v_right = 0.0
                target_x, target_y = self.waypoints[0]
                dx = target_x - car_pose.x
                dy = target_y - car_pose.y
                dist = math.hypot(dx, dy)
            else:
                # Final target reached: hold position firmly stopped at target
                self._current_v_left = 0.0
                self._current_v_right = 0.0
                self.rl_agent.reset_episode()
                return DriveCommand(0, 0, 0.0, 0.0, "ARRIVED", dist, 0.0, now), avoidance

        # Progressive Braking to Target (Only active when closing in on target)
        if dist > slowdown_dist or not getattr(self.control_config, "enable_target_braking", True):
            # Open space cruising - full configured speed authority
            brake_scale = 1.0
            mode_label = "AUTO"
        else:
            # Inside Braking Zone -> smooth exponential deceleration to target
            ratio = max(0.0, min(1.0, (dist - arrival_dist) / max(1.0, slowdown_dist - arrival_dist)))
            brake_scale = max(0.12, ratio ** 0.85)
            mode_label = "BRAKING"

        # Heading calculation with optional 180° flip (if marker mounted backwards)
        effective_car_angle = car_pose.angle_rad
        if getattr(self.control_config, "reverse_marker_heading", False):
            effective_car_angle += math.pi
            effective_car_angle = math.atan2(math.sin(effective_car_angle), math.cos(effective_car_angle))

        # Desired heading to target
        desired_angle_rad = math.atan2(dy, dx)
        
        # Heading error in radians (-pi to +pi)
        angle_err_rad = math.atan2(
            math.sin(desired_angle_rad - effective_car_angle),
            math.cos(desired_angle_rad - effective_car_angle)
        )
        angle_err_deg = math.degrees(angle_err_rad)

        # Incorporate Obstacle Avoidance steering bias & throttle scaling
        effective_angle_err = angle_err_rad + avoidance.steering_bias

        # If obstacle requires critical evasion or reverse, override motion
        if avoidance.is_critical:
            target_l, target_r = self._diff_drive_from_norm(avoidance.speed_scale, avoidance.steering_bias)
            v_l = int(self._slew_ramp(self._current_v_left, float(target_l), dt))
            v_r = int(self._slew_ramp(self._current_v_right, float(target_r), dt))
            self._current_v_left = float(v_l)
            self._current_v_right = float(v_r)
            return DriveCommand(v_l, v_r, avoidance.steering_bias, avoidance.speed_scale, "EVASION", dist, angle_err_deg, now), avoidance

        # --- REINFORCEMENT LEARNING APPROACH CONTROLLER ---
        if getattr(self.control_config, "enable_rl", True):
            rl_throttle, rl_steering, action_name = self.rl_agent.update(
                dist_px=dist,
                heading_err_deg=angle_err_deg,
                us_left_cm=us_left_cm,
                us_right_cm=us_right_cm,
                us_front_cm=us_front_cm,
                arrival_dist_px=self.control_config.arrival_distance_px
            )

            # Apply progressive target braking curve (braking to target only)
            rl_throttle = rl_throttle * brake_scale
            if dist <= slowdown_dist:
                rl_steering = rl_steering * max(0.65, brake_scale)

            # Manual polarity overrides if configured
            if getattr(self.control_config, "invert_throttle", False):
                rl_throttle = -rl_throttle
            if getattr(self.control_config, "invert_steering", False):
                rl_steering = -rl_steering

            target_l, target_r = self._diff_drive_from_norm(rl_throttle, rl_steering)
            v_l = int(self._slew_ramp(self._current_v_left, float(target_l), dt))
            v_r = int(self._slew_ramp(self._current_v_right, float(target_r), dt))
            self._current_v_left = float(v_l)
            self._current_v_right = float(v_r)

            return DriveCommand(
                v_left=v_l,
                v_right=v_r,
                steer_norm=rl_steering,
                speed_norm=rl_throttle,
                mode=mode_label,
                target_dist=dist,
                heading_err_deg=angle_err_deg,
                timestamp=now,
                rl_action=action_name,
                rl_reward=self.rl_agent.last_reward
            ), avoidance

        # --- CLASSICAL PID FALLBACK CONTROLLER ---
        # Angular PID
        self._integral_angle_err += effective_angle_err * dt
        self._integral_angle_err = max(-1.0, min(1.0, self._integral_angle_err))  # Anti-windup
        derivative_angle_err = (effective_angle_err - self._prev_angle_err) / dt
        self._prev_angle_err = effective_angle_err

        angular_effort = (
            self.control_config.kp_angular * effective_angle_err
            + self.control_config.ki_angular * self._integral_angle_err
            + self.control_config.kd_angular * derivative_angle_err
        )
        norm_steering = max(-1.0, min(1.0, angular_effort))

        # Linear speed controller with target braking
        base_throttle = self.control_config.kp_linear * brake_scale

        abs_err_deg = abs(math.degrees(effective_angle_err))
        turn_thresh = self.control_config.turn_in_place_angle_deg

        if abs_err_deg > turn_thresh:
            norm_throttle = 0.0
        else:
            angle_penalty = max(0.15, math.cos(math.radians(abs_err_deg)))
            norm_throttle = base_throttle * angle_penalty * avoidance.speed_scale

        if dist <= slowdown_dist:
            norm_steering = norm_steering * max(0.65, brake_scale)

        if getattr(self.control_config, "invert_throttle", False):
            norm_throttle = -norm_throttle
        if getattr(self.control_config, "invert_steering", False):
            norm_steering = -norm_steering

        target_l, target_r = self._diff_drive_from_norm(norm_throttle, norm_steering)
        v_l = int(self._slew_ramp(self._current_v_left, float(target_l), dt))
        v_r = int(self._slew_ramp(self._current_v_right, float(target_r), dt))
        self._current_v_left = float(v_l)
        self._current_v_right = float(v_r)

        return DriveCommand(
            v_left=v_l,
            v_right=v_r,
            steer_norm=norm_steering,
            speed_norm=norm_throttle,
            mode=mode_label,
            target_dist=dist,
            heading_err_deg=angle_err_deg,
            timestamp=now
        ), avoidance

    def _diff_drive_from_norm(self, throttle: float, steering: float) -> Tuple[int, int]:
        """
        Convert normalized throttle (-1..1) and steering (-1..1) into left and right motor PWM values
        using the algorithm from aadil-sp/ESP32-Bluetooth-RC-Car-with-Motor-Sound (arcade mixing + expo steering).
        """
        max_pwm = self.control_config.max_pwm
        min_pwm = self.control_config.min_pwm

        if abs(throttle) < 0.02 and abs(steering) < 0.02:
            return 0, 0

        # Pivot in place (tight zero-radius turn)
        if abs(throttle) < 0.05 and abs(steering) >= 0.05:
            pwm = int(min_pwm + (max_pwm - min_pwm) * abs(steering))
            if steering > 0:
                return pwm, -pwm
            else:
                return -pwm, pwm

        # Arcade mixing with cubic expo curve for steering (from user reference code)
        abs_str = abs(steering)
        curved_str = (abs_str ** 3) * (1.0 if steering > 0 else -1.0)

        left = throttle + curved_str * 0.75
        right = throttle - curved_str * 0.75

        # Normalize if beyond [-1.0, 1.0]
        max_mag = max(abs(left), abs(right))
        if max_mag > 1.0:
            left /= max_mag
            right /= max_mag

        def apply_scale(val: float) -> int:
            if abs(val) < 0.03:
                return 0
            sign = 1 if val > 0 else -1
            # Scale from min_pwm to max_pwm
            ratio = (abs(val) - 0.03) / 0.97
            ratio = min(1.0, max(0.0, ratio))
            pwm = min_pwm + (max_pwm - min_pwm) * ratio
            return int(sign * min(max_pwm, pwm))

        return apply_scale(left), apply_scale(right)
