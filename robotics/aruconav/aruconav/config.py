"""Central configuration dataclasses and defaults for ArUcoNav."""

from dataclasses import dataclass, field
import cv2


@dataclass
class CameraConfig:
    """Camera acquisition configuration."""
    camera_index: int = 0
    frame_width: int = 1280
    frame_height: int = 720
    fps: int = 30
    auto_reconnect: bool = True
    flip_horizontal: bool = False
    flip_vertical: bool = False


@dataclass
class ArucoConfig:
    """ArUco marker detection & pose configuration."""
    # Available dicts: 4X4_50, 4X4_100, 5X5_100, 6X6_250, ARUCO_ORIGINAL
    dictionary_name: str = "DICT_4X4_50"
    target_marker_id: int = 0  # Marker ID mounted on the RC car (-1 means track first detected marker)
    marker_size_cm: float = 5.0
    # Exponential moving average filter factor (0.0 to 1.0; higher = more responsive, lower = smoother)
    smoothing_factor: float = 0.75
    enable_corner_refinement: bool = True


@dataclass
class ControlConfig:
    """Motion planning and PID navigation parameters."""
    drive_mode: str = "differential"  # "differential" (L/R wheels) or "ackermann" (Steer+Throttle)
    max_pwm: int = 180  # Default max PWM (dynamically adjustable via GUI slider 60-255)
    min_pwm: int = 55   # Minimum PWM to overcome motor stall friction without jerking
    accel_rate_pwm_per_sec: float = 300.0  # Smooth acceleration ramping rate (PWM/sec)
    
    # PID gains for orientation alignment
    kp_angular: float = 1.6
    kd_angular: float = 0.25
    ki_angular: float = 0.02
    
    # Linear speed controller & Braking to Target
    kp_linear: float = 0.8
    arrival_distance_px: float = 35.0   # Stop when car center is within this pixel radius
    slowdown_distance_px: float = 160.0 # Braking zone: decelerate smoothly to target only
    turn_in_place_angle_deg: float = 45.0  # If heading error > this, pivot in place before driving forward
    enable_target_braking: bool = True  # Enable progressive braking curve when approaching target

    # Reinforcement Learning & Direction Polarity Controls
    enable_rl: bool = True              # Use Reinforcement Learning to approach marker
    invert_throttle: bool = False       # Invert forward/backward motor polarity
    invert_steering: bool = False       # Invert steering polarity
    reverse_marker_heading: bool = False # Canonical 0° (Flip 180° button toggles this in GUI)
    auto_track_goal_marker: bool = True  # Automatically track secondary ArUco marker as approach target
    goal_marker_id: int = -1            # Goal marker ID to approach (-1: any marker != car marker)


@dataclass
class ObstacleConfig:
    """Ultrasonic obstacle avoidance parameters."""
    enabled: bool = False               # Default False: works smoothly without ultrasonic sensors
    warning_distance_cm: float = 58.0   # Begin deflecting path early for wider rounds
    critical_distance_cm: float = 28.0  # Take active evasive turn away from obstacle
    emergency_stop_cm: float = 15.0     # Hard stop / reverse when trapped
    reverse_duration_sec: float = 0.8   # Time to reverse when trapped
    deflection_gain: float = 2.0        # Multiplier for wider steering rounds


@dataclass
class NetworkConfig:
    """Communication configuration for ESP-NOW serial gateway and simulation."""
    comm_mode: str = "espnow_serial"  # "espnow_serial", "simulation", "wifi_udp"
    serial_port: str = ""             # Auto-detects ESP32-WROOM-32 USB serial port if empty
    serial_baudrate: int = 115200
    heartbeat_rate_hz: int = 20       # Frequency of command transmission (20Hz = 50ms)
    comm_timeout_sec: float = 1.5
    car_ip: str = "192.168.4.1"
    udp_command_port: int = 8888


@dataclass
class AppConfig:
    """Root configuration tree."""
    camera: CameraConfig = field(default_factory=CameraConfig)
    aruco: ArucoConfig = field(default_factory=ArucoConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    obstacle: ObstacleConfig = field(default_factory=ObstacleConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)


# Global default configuration instance
DEFAULT_CONFIG = AppConfig()
