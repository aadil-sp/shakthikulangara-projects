"""Multi-threaded camera stream acquisition and device discovery."""

import logging
import threading
import time
from typing import List, Tuple, Optional
import cv2
import numpy as np

import subprocess
import sys
from aruconav.config import CameraConfig

logger = logging.getLogger("aruconav.vision.camera")


def list_available_cameras(max_test: int = 8) -> List[Tuple[int, str]]:
    """
    Probe available camera indices and query human-friendly device names.
    Returns a list of (index, display_name).
    """
    available = []
    # Always include the Virtual Simulator as index -1
    available.append((-1, "Virtual Simulator Stream"))

    # Attempt to query device names from macOS system profiler
    device_names: List[str] = []
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(
                ["system_profiler", "SPCameraDataType"],
                text=True, stderr=subprocess.DEVNULL, timeout=2.0
            )
            device_names = [
                line.strip().rstrip(':')
                for line in out.split('\n')
                if line.startswith('    ') and not line.startswith('      ') and line.strip()
            ]
    except Exception as e:
        logger.debug(f"Could not query macOS camera profiler: {e}")

    for idx in range(max_test):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            name = device_names[idx] if idx < len(device_names) else f"Device {idx}"
            res_str = f" ({w}x{h})" if w > 0 and h > 0 else ""
            available.append((idx, f"Camera {idx}: {name}{res_str}"))
            cap.release()

    return available


class CameraStream:
    """Threaded OpenCV video capture manager with lockless buffer exchange."""

    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self._cap: Optional[cv2.VideoCapture] = None
        self._current_index: int = self.config.camera_index
        
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._cap_lock = threading.Lock()
        
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_timestamp: float = 0.0
        self._fps_counter: float = 0.0
        self._frame_count: int = 0
        self._last_fps_calc_time: float = time.time()

    def start(self, camera_index: Optional[int] = None):
        """Start the video acquisition thread."""
        if camera_index is not None:
            self._current_index = camera_index

        if self._running:
            self.stop()

        self._running = True
        self._open_device()

        self._thread = threading.Thread(target=self._capture_loop, daemon=True, name="CameraStreamThread")
        self._thread.start()
        logger.info(f"Camera stream started on index {self._current_index}")

    def _open_device(self):
        """Open cv2.VideoCapture device."""
        if self._current_index < 0:
            # Simulated stream index
            with self._cap_lock:
                self._cap = None
            return

        try:
            with self._cap_lock:
                self._cap = cv2.VideoCapture(self._current_index)
                if self._cap.isOpened():
                    self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
                    self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
                    self._cap.set(cv2.CAP_PROP_FPS, self.config.fps)
                else:
                    logger.warning(f"Unable to open camera index {self._current_index}")
        except Exception as e:
            logger.error(f"Error opening camera {self._current_index}: {e}")
            with self._cap_lock:
                self._cap = None

    def switch_camera(self, new_index: int):
        """Switch video source dynamically."""
        if new_index == self._current_index and self._running:
            return

        logger.info(f"Switching camera from {self._current_index} to {new_index}")
        was_running = self._running
        self.stop()
        self._current_index = new_index
        if was_running:
            self.start(new_index)

    def stop(self):
        """Stop capture thread and release hardware resources safely."""
        self._running = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.5)
            self._thread = None

        with self._cap_lock:
            if self._cap is not None:
                try:
                    self._cap.release()
                except Exception as e:
                    logger.debug(f"Exception during cap release: {e}")
                self._cap = None
        logger.info("Camera stream stopped.")

    def _capture_loop(self):
        """Continuous background capture loop with thread-safe lock protection."""
        sim_step = 0
        while self._running:
            now = time.time()
            frame = None
            captured = None
            ret = False

            with self._cap_lock:
                if self._running and self._current_index >= 0 and self._cap is not None and self._cap.isOpened():
                    try:
                        ret, captured = self._cap.read()
                    except Exception as e:
                        ret = False
                        captured = None

            if ret and captured is not None:
                frame = captured
                if self.config.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                if self.config.flip_vertical:
                    frame = cv2.flip(frame, 0)
            elif self._current_index >= 0:
                time.sleep(0.01)
                continue
            else:
                # In simulator mode or camera disconnected, generate blank slate
                sim_step += 1
                frame = np.zeros((self.config.frame_height, self.config.frame_width, 3), dtype=np.uint8)
                frame[:] = (22, 24, 29)
                time.sleep(1.0 / max(1, self.config.fps))

            with self._lock:
                self._latest_frame = frame
                self._latest_timestamp = now
                self._frame_count += 1
                
                # Calculate running FPS
                elapsed = now - self._last_fps_calc_time
                if elapsed >= 1.0:
                    self._fps_counter = self._frame_count / elapsed
                    self._frame_count = 0
                    self._last_fps_calc_time = now

    def read(self) -> Tuple[Optional[np.ndarray], float, float]:
        """
        Get the most recent frame.
        Returns: (frame, timestamp, current_fps)
        """
        with self._lock:
            if self._latest_frame is None:
                return None, 0.0, 0.0
            return self._latest_frame.copy(), self._latest_timestamp, self._fps_counter

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_index(self) -> int:
        return self._current_index
