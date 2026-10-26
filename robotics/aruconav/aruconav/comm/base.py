"""Abstract base communication driver and telemetry data models."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Callable, Optional, Dict, Any


@dataclass
class TelemetryData:
    """Incoming sensor telemetry from the RC car."""
    us_left_cm: float = 100.0
    us_front_cm: float = 100.0
    us_right_cm: float = 100.0
    battery_voltage: float = 7.4
    status: str = "DISCONNECTED"
    rssi: int = -50
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


class BaseCommDriver(ABC):
    """Abstract interface for car communication backends."""

    def __init__(self):
        self._telemetry_callback: Optional[Callable[[TelemetryData], None]] = None
        self._log_callback: Optional[Callable[[str, str], None]] = None  # (message, level)
        self.latest_telemetry: TelemetryData = TelemetryData()
        self.is_connected: bool = False

    def register_telemetry_callback(self, callback: Callable[[TelemetryData], None]):
        """Register callback for new telemetry data events."""
        self._telemetry_callback = callback

    def register_log_callback(self, callback: Callable[[str, str], None]):
        """Register callback for status/error logging."""
        self._log_callback = callback

    def _emit_log(self, message: str, level: str = "INFO"):
        if self._log_callback:
            self._log_callback(message, level)

    def _emit_telemetry(self, data: TelemetryData):
        self.latest_telemetry = data
        if self._telemetry_callback:
            self._telemetry_callback(data)

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        pass

    @abstractmethod
    def send_drive_command(self, v_left: int, v_right: int, steer_norm: float = 0.0, speed_norm: float = 0.0) -> bool:
        """Send motor control command."""
        pass
