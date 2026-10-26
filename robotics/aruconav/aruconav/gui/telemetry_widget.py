"""Telemetry gauges and sensor visualization widget."""

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QProgressBar, QFrame
)

from aruconav.comm.base import TelemetryData
from aruconav.control.motion_planner import DriveCommand
from aruconav.control.obstacle_avoidance import AvoidanceResult, AvoidanceState


class TelemetryWidget(QWidget):
    """Real-time sensor meters, motor PWM gauges, and wireless link telemetry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        # Header
        title = QLabel("CAR SENSORS & TELEMETRY")
        title.setStyleSheet("font-weight: bold; color: #8b949e; font-size: 11px; letter-spacing: 1px;")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(8)

        # 1. Ultrasonic Left Bar
        grid.addWidget(QLabel("US Angle Left:"), 0, 0)
        self.us_l_val = QLabel("100.0 cm")
        self.us_l_val.setStyleSheet("font-weight: bold; color: #58a6ff;")
        grid.addWidget(self.us_l_val, 0, 1)
        self.us_l_bar = QProgressBar()
        self.us_l_bar.setRange(0, 150)
        self.us_l_bar.setValue(100)
        self.us_l_bar.setTextVisible(False)
        self.us_l_bar.setStyleSheet(self._get_bar_style("#3fb950"))
        grid.addWidget(self.us_l_bar, 0, 2)

        # 2. Ultrasonic Front Center Bar
        grid.addWidget(QLabel("US Front Center:"), 1, 0)
        self.us_f_val = QLabel("100.0 cm")
        self.us_f_val.setStyleSheet("font-weight: bold; color: #58a6ff;")
        grid.addWidget(self.us_f_val, 1, 1)
        self.us_f_bar = QProgressBar()
        self.us_f_bar.setRange(0, 150)
        self.us_f_bar.setValue(100)
        self.us_f_bar.setTextVisible(False)
        self.us_f_bar.setStyleSheet(self._get_bar_style("#3fb950"))
        grid.addWidget(self.us_f_bar, 1, 2)

        # 3. Ultrasonic Right Bar
        grid.addWidget(QLabel("US Angle Right:"), 2, 0)
        self.us_r_val = QLabel("100.0 cm")
        self.us_r_val.setStyleSheet("font-weight: bold; color: #58a6ff;")
        grid.addWidget(self.us_r_val, 2, 1)
        self.us_r_bar = QProgressBar()
        self.us_r_bar.setRange(0, 150)
        self.us_r_bar.setValue(100)
        self.us_r_bar.setTextVisible(False)
        self.us_r_bar.setStyleSheet(self._get_bar_style("#3fb950"))
        grid.addWidget(self.us_r_bar, 2, 2)

        # 4. Motor Outputs
        grid.addWidget(QLabel("Left Motor PWM:"), 3, 0)
        self.pwm_l_val = QLabel("0")
        self.pwm_l_val.setStyleSheet("font-weight: bold; color: #e6edf3;")
        grid.addWidget(self.pwm_l_val, 3, 1)
        self.pwm_l_bar = QProgressBar()
        self.pwm_l_bar.setRange(-255, 255)
        self.pwm_l_bar.setValue(0)
        self.pwm_l_bar.setTextVisible(False)
        self.pwm_l_bar.setStyleSheet(self._get_bar_style("#a371f7"))
        grid.addWidget(self.pwm_l_bar, 3, 2)

        grid.addWidget(QLabel("Right Motor PWM:"), 4, 0)
        self.pwm_r_val = QLabel("0")
        self.pwm_r_val.setStyleSheet("font-weight: bold; color: #e6edf3;")
        grid.addWidget(self.pwm_r_val, 4, 1)
        self.pwm_r_bar = QProgressBar()
        self.pwm_r_bar.setRange(-255, 255)
        self.pwm_r_bar.setValue(0)
        self.pwm_r_bar.setTextVisible(False)
        self.pwm_r_bar.setStyleSheet(self._get_bar_style("#a371f7"))
        grid.addWidget(self.pwm_r_bar, 4, 2)

        layout.addLayout(grid)

        # Horizontal separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #30363d;")
        layout.addWidget(line)

        # Bottom Quick Stats (Battery, Avoidance Status, Comm Latency)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.avoidance_label = QLabel("Avoidance: CLEAR")
        self.avoidance_label.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 11px;")
        bottom_layout.addWidget(self.avoidance_label)

        self.battery_label = QLabel("Battery: 7.4V")
        self.battery_label.setStyleSheet("color: #e6edf3; font-size: 11px;")
        bottom_layout.addWidget(self.battery_label)

        self.latency_label = QLabel("Latency: 0.0 ms")
        self.latency_label.setStyleSheet("color: #8b949e; font-size: 11px;")
        bottom_layout.addWidget(self.latency_label)

        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def _get_bar_style(self, color: str) -> str:
        return f"""
            QProgressBar {{
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                height: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """

    @pyqtSlot(object, object, object)
    def update_telemetry(self, telemetry: TelemetryData, cmd: DriveCommand, avoidance: AvoidanceResult):
        """Update all telemetry displays with new data."""
        # Ultrasonic Left
        self.us_l_val.setText(f"{telemetry.us_left_cm:.1f} cm")
        self.us_l_bar.setValue(int(min(150, max(0, telemetry.us_left_cm))))
        self.us_l_bar.setStyleSheet(self._get_sensor_bar_style(telemetry.us_left_cm))

        # Ultrasonic Front
        self.us_f_val.setText(f"{telemetry.us_front_cm:.1f} cm")
        self.us_f_bar.setValue(int(min(150, max(0, telemetry.us_front_cm))))
        self.us_f_bar.setStyleSheet(self._get_sensor_bar_style(telemetry.us_front_cm))

        # Ultrasonic Right
        self.us_r_val.setText(f"{telemetry.us_right_cm:.1f} cm")
        self.us_r_bar.setValue(int(min(150, max(0, telemetry.us_right_cm))))
        self.us_r_bar.setStyleSheet(self._get_sensor_bar_style(telemetry.us_right_cm))

        # Motors
        self.pwm_l_val.setText(f"{cmd.v_left}")
        self.pwm_l_bar.setValue(cmd.v_left)

        self.pwm_r_val.setText(f"{cmd.v_right}")
        self.pwm_r_bar.setValue(cmd.v_right)

        # Avoidance State Pill
        if avoidance.state == AvoidanceState.CLEAR:
            self.avoidance_label.setText("Safety: CLEAR")
            self.avoidance_label.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 11px;")
        elif "WARNING" in avoidance.state.value:
            self.avoidance_label.setText(f"Safety: {avoidance.state.value}")
            self.avoidance_label.setStyleSheet("color: #d29922; font-weight: bold; font-size: 11px;")
        else:
            self.avoidance_label.setText(f"Safety: {avoidance.state.value}")
            self.avoidance_label.setStyleSheet("color: #f85149; font-weight: bold; font-size: 11px;")

        # Battery & Latency
        self.battery_label.setText(f"Battery: {telemetry.battery_voltage:.2f}V")
        self.latency_label.setText(f"Latency: {telemetry.latency_ms:.1f} ms | Link: {telemetry.status}")

    def _get_sensor_bar_style(self, dist_cm: float) -> str:
        if dist_cm < 18.0:
            return self._get_bar_style("#f85149")
        elif dist_cm < 35.0:
            return self._get_bar_style("#d29922")
        else:
            return self._get_bar_style("#3fb950")
