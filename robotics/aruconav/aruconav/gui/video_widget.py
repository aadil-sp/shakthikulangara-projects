"""Interactive video display widget with coordinate transformation and click navigation."""

from typing import Optional, Tuple
import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import QWidget, QSizePolicy


class VideoWidget(QWidget):
    """High-performance video canvas capturing mouse clicks for waypoint navigation."""

    # Signals: (x_px, y_px, append_queue)
    waypoint_clicked = pyqtSignal(float, float, bool)
    clear_waypoints_requested = pyqtSignal()
    toggle_fullscreen_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(480, 270)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._frame_bgr: Optional[np.ndarray] = None
        self._pixmap: Optional[QPixmap] = None
        self._frame_w: int = 1280
        self._frame_h: int = 720

        # Rendering geometry cache for accurate mouse mapping
        self._render_rect: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (x, y, w, h)

    def set_frame(self, frame_bgr: np.ndarray):
        """Update canvas with new OpenCV BGR frame."""
        if frame_bgr is None or frame_bgr.size == 0:
            return

        self._frame_bgr = frame_bgr
        self._frame_h, self._frame_w = frame_bgr.shape[:2]

        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        qimg = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self._pixmap = QPixmap.fromImage(qimg)
        self.update()

    def paintEvent(self, event):
        """Paint video frame with letterbox aspect ratio scaling."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(13, 17, 23))

        if self._pixmap is None or self._pixmap.isNull():
            painter.setPen(QColor(139, 148, 158))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Waiting for Camera Stream...")
            return

        # Scale maintaining aspect ratio
        widget_w = self.width()
        widget_h = self.height()
        target_ratio = self._frame_w / self._frame_h
        current_ratio = widget_w / widget_h

        if current_ratio > target_ratio:
            render_h = widget_h
            render_w = int(widget_h * target_ratio)
            rx = (widget_w - render_w) // 2
            ry = 0
        else:
            render_w = widget_w
            render_h = int(widget_w / target_ratio)
            rx = 0
            ry = (widget_h - render_h) // 2

        self._render_rect = (rx, ry, render_w, render_h)
        scaled_pixmap = self._pixmap.scaled(
            render_w, render_h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(rx, ry, scaled_pixmap)

    def mousePressEvent(self, event):
        """Handle mouse clicks for waypoint setting."""
        rx, ry, rw, rh = self._render_rect
        if rw <= 0 or rh <= 0:
            return

        click_x = event.position().x()
        click_y = event.position().y()

        # Check if click was inside video render box
        if rx <= click_x <= rx + rw and ry <= click_y <= ry + rh:
            norm_x = (click_x - rx) / rw
            norm_y = (click_y - ry) / rh

            # Convert to original frame pixel coordinates
            frame_x = norm_x * self._frame_w
            frame_y = norm_y * self._frame_h

            if event.button() == Qt.MouseButton.LeftButton:
                is_shift = bool(event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
                self.waypoint_clicked.emit(frame_x, frame_y, is_shift)
            elif event.button() == Qt.MouseButton.RightButton:
                self.clear_waypoints_requested.emit()

    def mouseDoubleClickEvent(self, event):
        """Toggle fullscreen on double click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_fullscreen_requested.emit()
