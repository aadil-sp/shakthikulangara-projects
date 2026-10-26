"""ESP-NOW Serial Gateway communication driver for ultra-low-latency radio."""

import json
import logging
import threading
import time
from typing import Optional
import serial

from aruconav.config import NetworkConfig
from aruconav.comm.base import BaseCommDriver, TelemetryData

logger = logging.getLogger("aruconav.comm.espnow")


class EspNowSerialDriver(BaseCommDriver):
    """Bridge driver communicating over USB-Serial to an ESP32 ESP-NOW gateway."""

    def __init__(self, config: Optional[NetworkConfig] = None):
        super().__init__()
        self.config = config or NetworkConfig()
        self._serial: Optional[serial.Serial] = None
        self._running: bool = False
        self._rx_thread: Optional[threading.Thread] = None

    def _find_esp32_port(self) -> str:
        """Find the ESP32-C3 USB serial port (usbmodem, CP2102, CH340)."""
        import glob
        candidates = (
            glob.glob("/dev/cu.usbmodem*") +
            glob.glob("/dev/cu.usbserial*") +
            glob.glob("/dev/cu.wchusbserial*") +
            glob.glob("/dev/cu.SLAB_USBtoUART*") +
            glob.glob("/dev/ttyUSB*")
        )
        if candidates:
            return candidates[0]
        return self.config.serial_port or "/dev/cu.usbmodem1201"

    def connect(self) -> bool:
        """Open serial port to ESP32-C3 ESP-NOW gateway."""
        import os
        port_to_use = self.config.serial_port
        if not port_to_use or not os.path.exists(port_to_use):
            port_to_use = self._find_esp32_port()

        try:
            self._serial = serial.Serial(
                port=port_to_use,
                baudrate=self.config.serial_baudrate,
                timeout=0.2
            )
            self._running = True
            self.is_connected = True

            self._rx_thread = threading.Thread(target=self._listen_loop, daemon=True, name="EspNowRxThread")
            self._rx_thread.start()

            self._emit_log(f"ESP32-C3 Gateway connected on {port_to_use} @ {self.config.serial_baudrate}", "INFO")
            return True
        except serial.SerialException as e:
            self.is_connected = False
            self._emit_log(f"Serial port {port_to_use} busy or unavailable: {e}", "WARN")
            alt_port = self._find_esp32_port()
            if alt_port != port_to_use and os.path.exists(alt_port):
                try:
                    self._serial = serial.Serial(port=alt_port, baudrate=self.config.serial_baudrate, timeout=0.2)
                    self._running = True
                    self.is_connected = True
                    self._rx_thread = threading.Thread(target=self._listen_loop, daemon=True, name="EspNowRxThread")
                    self._rx_thread.start()
                    self._emit_log(f"ESP32-C3 Gateway connected on fallback {alt_port}", "INFO")
                    return True
                except Exception:
                    pass
            return False
        except Exception as e:
            self.is_connected = False
            self._emit_log(f"Failed to open ESP32 Serial port ({port_to_use}): {e}", "ERROR")
            return False

    def disconnect(self):
        """Close serial connection."""
        self._running = False
        self.is_connected = False

        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=0.5)
            self._rx_thread = None

        if self._serial:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = None

        self._emit_log("ESP-NOW Serial Gateway disconnected.", "INFO")

    def send_drive_command(self, v_left: int, v_right: int, steer_norm: float = 0.0, speed_norm: float = 0.0) -> bool:
        """Send command over serial bridge to be broadcasted via ESP-NOW."""
        if not self._running or self._serial is None or not self._serial.is_open:
            return False

        try:
            # Compact packet: "D,v_left,v_right\n"
            msg = f"D,{int(v_left)},{int(v_right)}\n".encode("utf-8")
            self._serial.write(msg)
            return True
        except Exception as e:
            self._emit_log(f"ESP-NOW TX Error: {e}", "WARN")
            return False

    def _listen_loop(self):
        """Listen for incoming telemetry lines from serial gateway."""
        while self._running:
            if self._serial is None or not self._serial.is_open:
                break

            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue

                # Expected format: "T,us_left,us_front,us_right,v_bat" or fallback "T,us_l,us_r,v_bat"
                if line.startswith("T,"):
                    parts = line.split(",")
                    if len(parts) >= 5:
                        us_l = float(parts[1])
                        us_f = float(parts[2])
                        us_r = float(parts[3])
                        v_bat = float(parts[4])
                        telemetry = TelemetryData(
                            us_left_cm=us_l,
                            us_front_cm=us_f,
                            us_right_cm=us_r,
                            battery_voltage=v_bat,
                            status="CONNECTED",
                            timestamp=time.time()
                        )
                        self._emit_telemetry(telemetry)
                    elif len(parts) >= 4:
                        us_l = float(parts[1])
                        us_r = float(parts[2])
                        v_bat = float(parts[3])
                        telemetry = TelemetryData(
                            us_left_cm=us_l,
                            us_front_cm=min(us_l, us_r),
                            us_right_cm=us_r,
                            battery_voltage=v_bat,
                            status="CONNECTED",
                            timestamp=time.time()
                        )
                        self._emit_telemetry(telemetry)
                elif line.startswith("{"):
                    telemetry_json = json.loads(line)
                    telemetry = TelemetryData(
                        us_left_cm=float(telemetry_json.get("us_l", 100.0)),
                        us_front_cm=float(telemetry_json.get("us_f", telemetry_json.get("us_front", 100.0))),
                        us_right_cm=float(telemetry_json.get("us_r", 100.0)),
                        battery_voltage=float(telemetry_json.get("v_bat", 7.4)),
                        status="CONNECTED",
                        timestamp=time.time()
                    )
                    self._emit_telemetry(telemetry)
            except Exception as e:
                if self._running:
                    self._emit_log(f"ESP-NOW RX Error: {e}", "WARN")
                time.sleep(0.05)
