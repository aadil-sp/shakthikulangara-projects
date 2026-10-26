"""High-speed WiFi UDP communication driver for ESP32/ESP8266."""

import json
import logging
import socket
import threading
import time
from typing import Optional

from aruconav.config import NetworkConfig
from aruconav.comm.base import BaseCommDriver, TelemetryData

logger = logging.getLogger("aruconav.comm.wifi")


class WifiUdpDriver(BaseCommDriver):
    """Low-latency UDP command and telemetry transceiver."""

    def __init__(self, config: Optional[NetworkConfig] = None):
        super().__init__()
        self.config = config or NetworkConfig()
        
        self._tx_socket: Optional[socket.socket] = None
        self._rx_socket: Optional[socket.socket] = None
        self._running: bool = False
        self._rx_thread: Optional[threading.Thread] = None

        self._last_rx_time: float = 0.0
        self._packets_sent: int = 0
        self._packets_received: int = 0

    def connect(self) -> bool:
        """Initialize UDP sockets and spawn receiver thread."""
        try:
            self._tx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._tx_socket.settimeout(0.2)

            self._rx_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._rx_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._rx_socket.bind(("0.0.0.0", self.config.udp_telemetry_port))
            self._rx_socket.settimeout(0.5)

            self._running = True
            self.is_connected = True

            self._rx_thread = threading.Thread(target=self._listen_loop, daemon=True, name="WifiUdpRxThread")
            self._rx_thread.start()

            self._emit_log(f"WiFi UDP listening on port {self.config.udp_telemetry_port}, target: {self.config.car_ip}:{self.config.udp_command_port}", "INFO")
            return True
        except Exception as e:
            self.is_connected = False
            self._emit_log(f"WiFi UDP connection failed: {e}", "ERROR")
            return False

    def disconnect(self):
        """Close UDP sockets and stop receiver thread."""
        self._running = False
        self.is_connected = False

        if self._rx_thread is not None and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=0.5)
            self._rx_thread = None

        if self._tx_socket:
            try:
                self._tx_socket.close()
            except Exception:
                pass
            self._tx_socket = None

        if self._rx_socket:
            try:
                self._rx_socket.close()
            except Exception:
                pass
            self._rx_socket = None

        self._emit_log("WiFi UDP disconnected.", "INFO")

    def send_drive_command(self, v_left: int, v_right: int, steer_norm: float = 0.0, speed_norm: float = 0.0) -> bool:
        """Transmit drive command packet to car."""
        if not self._running or self._tx_socket is None:
            return False

        try:
            now = time.time()
            packet = {
                "cmd": "DRIVE",
                "v_l": int(v_left),
                "v_r": int(v_right),
                "st": round(steer_norm, 2),
                "sp": round(speed_norm, 2),
                "ts": now
            }
            payload = json.dumps(packet).encode("utf-8")
            self._tx_socket.sendto(payload, (self.config.car_ip, self.config.udp_command_port))
            self._packets_sent += 1
            return True
        except Exception as e:
            self._emit_log(f"WiFi TX Error: {e}", "WARN")
            return False

    def _listen_loop(self):
        """Background thread listening for incoming telemetry."""
        while self._running:
            if self._rx_socket is None:
                break

            try:
                data, addr = self._rx_socket.recvfrom(2048)
                now = time.time()
                self._last_rx_time = now
                self._packets_received += 1

                telemetry_json = json.loads(data.decode("utf-8"))
                
                # Extract fields
                us_l = float(telemetry_json.get("us_l", telemetry_json.get("us_left", 100.0)))
                us_r = float(telemetry_json.get("us_r", telemetry_json.get("us_right", 100.0)))
                v_bat = float(telemetry_json.get("v_bat", telemetry_json.get("battery", 7.4)))
                tx_ts = float(telemetry_json.get("ts", now))
                latency_ms = max(0.0, (now - tx_ts) * 1000.0) if tx_ts > 0 else 0.0

                telemetry = TelemetryData(
                    us_left_cm=us_l,
                    us_right_cm=us_r,
                    battery_voltage=v_bat,
                    status="CONNECTED",
                    rssi=telemetry_json.get("rssi", -50),
                    latency_ms=latency_ms,
                    timestamp=now
                )
                self._emit_telemetry(telemetry)

            except socket.timeout:
                # Check for comm timeout
                if time.time() - self._last_rx_time > self.config.comm_timeout_sec and self._last_rx_time > 0:
                    self._emit_telemetry(TelemetryData(status="TIMEOUT", timestamp=time.time()))
                continue
            except json.JSONDecodeError:
                self._emit_log("Malformed JSON telemetry received", "WARN")
            except Exception as e:
                if self._running:
                    self._emit_log(f"WiFi RX Error: {e}", "WARN")
                time.sleep(0.05)
