"""Application launcher and CLI entry point for ArUcoNav."""

import argparse
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from aruconav.config import AppConfig, DEFAULT_CONFIG
from aruconav.gui.main_window import MainWindow

# Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
)
logger = logging.getLogger("aruconav")


def parse_arguments() -> AppConfig:
    """Parse command-line arguments and populate configuration."""
    parser = argparse.ArgumentParser(
        description="ArUcoNav — Autonomous Vision-Guided RC Car Navigation"
    )
    parser.add_argument("--camera", type=int, default=-1,
                        help="Camera device index (-1 for Virtual Simulator, 0 for default webcam)")
    parser.add_argument("--sim", action="store_true",
                        help="Force Virtual 2D Physics Simulator mode")
    parser.add_argument("--marker-id", type=int, default=0,
                        help="Target ArUco marker ID on car (-1 for any marker)")
    parser.add_argument("--dict", type=str, default="DICT_4X4_50",
                        help="ArUco Dictionary name (e.g. DICT_4X4_50, DICT_6X6_250)")
    parser.add_argument("--ip", type=str, default="192.168.4.1",
                        help="ESP32 Car IP address for WiFi mode")
    parser.add_argument("--port", type=int, default=8888,
                        help="ESP32 UDP command port")
    parser.add_argument("--serial-port", type=str, default="",
                        help="Serial port for ESP-NOW gateway (auto-detects if empty)")

    args = parser.parse_args()

    config = AppConfig()
    config.camera.camera_index = -1 if args.sim else args.camera
    config.aruco.target_marker_id = args.marker_id
    config.aruco.dictionary_name = args.dict
    config.network.car_ip = args.ip
    config.network.udp_command_port = args.port
    config.network.serial_port = args.serial_port

    return config


def main():
    """Main execution function."""
    config = parse_arguments()
    logger.info("Initializing ArUcoNav Application...")

    app = QApplication(sys.argv)
    app.setApplicationName("ArUcoNav")

    window = MainWindow(config)
    window.show()

    logger.info("ArUcoNav GUI loaded successfully.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
