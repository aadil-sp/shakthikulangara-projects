"""Ultrasonic sensor-based reactive obstacle avoidance controller."""

from dataclasses import dataclass
from enum import Enum
import time
from typing import Tuple, Optional
import numpy as np

from aruconav.config import ObstacleConfig


class AvoidanceState(Enum):
    CLEAR = "CLEAR"
    WARNING_LEFT = "WARNING_LEFT"
    WARNING_RIGHT = "WARNING_RIGHT"
    WARNING_FRONT = "WARNING_FRONT"
    CRITICAL_EVASION = "CRITICAL_EVASION"
    EMERGENCY_REVERSE = "EMERGENCY_REVERSE"


@dataclass
class AvoidanceResult:
    state: AvoidanceState
    steering_bias: float       # Steering deflection in radians (- means steer left, + means steer right)
    speed_scale: float         # Speed multiplier (1.0 = full speed, 0.0 = stopped, -1.0 = reverse)
    is_critical: bool          # True if autonomous path planner must yield to evasive maneuver
    description: str


class ObstacleAvoidanceController:
    """Evaluates dual ultrasonic sensors to generate reactive steering bias and safety overrides."""

    def __init__(self, config: Optional[ObstacleConfig] = None):
        self.config = config or ObstacleConfig()
        self._reverse_start_time: float = 0.0
        self._is_reversing: bool = False
        self._reverse_turn_dir: float = 1.0  # +1 right, -1 left

    def evaluate(self, us_left: float, us_right: float, us_front: float = 100.0) -> AvoidanceResult:
        """
        Evaluate 3 ultrasonic sensor readings (Angle Left, Front, Angle Right in cm)
        and return reactive avoidance recommendations.
        """
        if not self.config.enabled:
            return AvoidanceResult(
                state=AvoidanceState.CLEAR,
                steering_bias=0.0,
                speed_scale=1.0,
                is_critical=False,
                description="Obstacle Avoidance Disabled"
            )

        now = time.time()

        # Handle active emergency reverse maneuver
        if self._is_reversing:
            if now - self._reverse_start_time < self.config.reverse_duration_sec:
                return AvoidanceResult(
                    state=AvoidanceState.EMERGENCY_REVERSE,
                    steering_bias=self._reverse_turn_dir * 0.8,
                    speed_scale=-0.6,
                    is_critical=True,
                    description="Executing Emergency Reverse"
                )
            else:
                self._is_reversing = False

        warn_dist = self.config.warning_distance_cm
        crit_dist = self.config.critical_distance_cm
        stop_dist = self.config.emergency_stop_cm

        # Critical trap: Front blocked AND either side blocked, or both sides blocked
        if (us_front < stop_dist) or (us_left < stop_dist and us_right < stop_dist):
            self._is_reversing = True
            self._reverse_start_time = now
            # Reverse and turn away from the tighter side
            self._reverse_turn_dir = 1.0 if us_left < us_right else -1.0
            return AvoidanceResult(
                state=AvoidanceState.EMERGENCY_REVERSE,
                steering_bias=self._reverse_turn_dir * 0.8,
                speed_scale=-0.6,
                is_critical=True,
                description=f"Triggering Emergency Reverse (Front: {us_front:.1f}cm, L: {us_left:.1f}cm, R: {us_right:.1f}cm)"
            )

        # Critical front obstacle -> steer towards whichever angled side has more clearance
        if us_front < crit_dist:
            turn_dir = 1.0 if us_left < us_right else -1.0
            return AvoidanceResult(
                state=AvoidanceState.CRITICAL_EVASION,
                steering_bias=turn_dir * 0.95 * self.config.deflection_gain,
                speed_scale=0.5,
                is_critical=True,
                description=f"Critical FRONT Obstacle ({us_front:.1f}cm) -> Evasive {'Right' if turn_dir > 0 else 'Left'} Turn"
            )

        # Critical single or dual obstacle within critical distance
        if us_left < crit_dist or us_right < crit_dist:
            # If left is closer, steer hard right (+), if right closer, steer hard left (-)
            if us_left < us_right:
                steering_bias = 0.95 * self.config.deflection_gain
                desc = f"Critical obstacle on LEFT ({us_left:.1f}cm) -> Evasive Right Turn"
            else:
                steering_bias = -0.95 * self.config.deflection_gain
                desc = f"Critical obstacle on RIGHT ({us_right:.1f}cm) -> Evasive Left Turn"

            return AvoidanceResult(
                state=AvoidanceState.CRITICAL_EVASION,
                steering_bias=steering_bias,
                speed_scale=0.55,  # Maintain good momentum through evasive arc
                is_critical=True,
                description=desc
            )

        # Warning zone deflection
        left_in_warn = us_left < warn_dist
        right_in_warn = us_right < warn_dist

        if left_in_warn or right_in_warn:
            # Compute proportional repulsion
            # Repulsion starts early at warn_dist and ramps up cleanly towards crit_dist
            repulse_left = max(0.0, (warn_dist - us_left) / max(1.0, warn_dist - crit_dist)) if left_in_warn else 0.0
            repulse_right = max(0.0, (warn_dist - us_right) / max(1.0, warn_dist - crit_dist)) if right_in_warn else 0.0

            # Steering bias (+ = right, - = left) with high deflection gain for wide rounds
            steering_bias = (repulse_left - repulse_right) * self.config.deflection_gain * 0.9
            
            # Speed reduction during arc
            max_threat = min(1.0, max(repulse_left, repulse_right))
            speed_scale = max(0.65, 1.0 - (0.35 * max_threat))

            if left_in_warn and right_in_warn:
                state = AvoidanceState.WARNING_FRONT
                # If both are in warning, turn towards the side with more clearance
                if us_left < us_right:
                    steering_bias = 0.7 * self.config.deflection_gain
                else:
                    steering_bias = -0.7 * self.config.deflection_gain
                desc = f"Warning: Obstacles ahead (L: {us_left:.0f}cm, R: {us_right:.0f}cm)"
            elif left_in_warn:
                state = AvoidanceState.WARNING_LEFT
                desc = f"Warning: Obstacle on LEFT ({us_left:.0f}cm) -> Wide Right Arc"
            else:
                state = AvoidanceState.WARNING_RIGHT
                desc = f"Warning: Obstacle on RIGHT ({us_right:.0f}cm) -> Wide Left Arc"

            return AvoidanceResult(
                state=state,
                steering_bias=steering_bias,
                speed_scale=speed_scale,
                is_critical=False,
                description=desc
            )

        # Path is completely clear
        return AvoidanceResult(
            state=AvoidanceState.CLEAR,
            steering_bias=0.0,
            speed_scale=1.0,
            is_critical=False,
            description="Sensors Clear"
        )
