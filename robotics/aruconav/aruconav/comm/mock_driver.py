"""Virtual communication driver linking controller directly to the physics simulator."""

import time
from typing import Optional
from aruconav.comm.base import BaseCommDriver, TelemetryData
from aruconav.sim.car_simulator import CarSimulator


class MockSimDriver(BaseCommDriver):
    """Bridge driver directly interacting with the local simulated car."""

    def __init__(self, simulator: CarSimulator):
        super().__init__()
        self.simulator = simulator
        self.is_connected = True

    def connect(self) -> bool:
        self.is_connected = True
        self._emit_log("Connected to Internal 2D Physics Simulator.", "INFO")
        return True

    def disconnect(self):
        self.is_connected = False
        self.simulator.set_motor_pwm(0, 0)
        self._emit_log("Disconnected from Simulator.", "INFO")

    def send_drive_command(self, v_left: int, v_right: int, steer_norm: float = 0.0, speed_norm: float = 0.0) -> bool:
        if not self.is_connected:
            return False

        # Forward PWM to virtual car
        self.simulator.set_motor_pwm(v_left, v_right)

        # Poll virtual ultrasonic sensors (Angle Left, Front, Angle Right)
        us_l, us_f, us_r = self.simulator.read_ultrasonic_sensors()

        telemetry = TelemetryData(
            us_left_cm=round(us_l, 1),
            us_front_cm=round(us_f, 1),
            us_right_cm=round(us_r, 1),
            battery_voltage=7.8,
            status="SIM_OK",
            rssi=-30,
            latency_ms=0.5,
            timestamp=time.time()
        )
        self._emit_telemetry(telemetry)
        return True
