"""Main application window uniting camera stream, ArUco tracking, motion planner, and comms."""

import logging
import time
from typing import Optional
import cv2
import numpy as np

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QComboBox, QPushButton, QLabel, QLineEdit, QCheckBox, QFrame, QMessageBox,
    QSlider
)

from aruconav.config import AppConfig
from aruconav.vision.aruco_tracker import ArucoTracker, MarkerPose
from aruconav.vision.camera_stream import CameraStream, list_available_cameras
from aruconav.vision.overlays import draw_hud_overlays
from aruconav.control.motion_planner import MotionPlanner, DriveCommand
from aruconav.control.obstacle_avoidance import AvoidanceResult, AvoidanceState
from aruconav.comm.base import BaseCommDriver, TelemetryData
from aruconav.comm.espnow_driver import EspNowSerialDriver
from aruconav.comm.mock_driver import MockSimDriver
from aruconav.sim.car_simulator import CarSimulator
from aruconav.gui.video_widget import VideoWidget
from aruconav.gui.telemetry_widget import TelemetryWidget
from aruconav.gui.log_widget import LogWidget

logger = logging.getLogger("aruconav.main_window")


class MainWindow(QMainWindow):
    """Full-screen capable main window for ArUco-based RC car navigation."""

    def __init__(self, config: Optional[AppConfig] = None):
        super().__init__()
        self.config = config or AppConfig()
        self.setWindowTitle("ArUcoNav — Autonomous RC Car Vision Navigation System")
        self.resize(1360, 850)

        # Core subsystems
        self.tracker = ArucoTracker(self.config.aruco)
        self.camera_stream = CameraStream(self.config.camera)
        self.motion_planner = MotionPlanner(self.config.control, self.config.obstacle)
        self.simulator = CarSimulator(self.config.camera, self.config.aruco)

        # Active communication driver (Defaults to ESP-NOW ESP32-C3 gateway)
        if self.config.network.comm_mode == "simulation":
            self.comm_driver: BaseCommDriver = MockSimDriver(self.simulator)
        else:
            self.comm_driver: BaseCommDriver = EspNowSerialDriver(self.config.network)

        # Active state cache
        self._active_target_pose: Optional[MarkerPose] = None
        self._all_poses = []
        self._active_command = DriveCommand(0, 0, 0.0, 0.0, "IDLE", 0.0, 0.0, time.time())
        self._active_avoidance = AvoidanceResult(AvoidanceState.CLEAR, 0.0, 1.0, False, "Clear")
        self._active_telemetry = TelemetryData()

        # Keyboard manual control state
        self._keys_pressed = set()

        self._init_ui()
        self._init_comms()
        self._init_shortcuts()

        # Start master update timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._main_loop_step)
        self.timer.start(33)  # ~30 Hz

    def _init_ui(self):
        """Construct the UI layout."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Apply dark sleek theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }
            QComboBox, QLineEdit, QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px 8px;
                color: #c9d1d9;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #30363d;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QSplitter::handle {
                background-color: #30363d;
            }
        """)

        # 1. Top Control Toolbar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        # Camera dropdown
        top_bar.addWidget(QLabel("Camera:"))
        self.camera_combo = QComboBox()
        self._populate_cameras()
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        top_bar.addWidget(self.camera_combo)

        # Comm Mode dropdown
        top_bar.addWidget(QLabel("Comm Mode:"))
        self.comm_combo = QComboBox()
        self.comm_combo.addItems(["ESP-NOW (ESP32-C3)", "Simulation"])
        if self.config.network.comm_mode == "simulation":
            self.comm_combo.setCurrentIndex(1)
        else:
            self.comm_combo.setCurrentIndex(0)
        self.comm_combo.currentIndexChanged.connect(self._on_comm_mode_changed)
        top_bar.addWidget(self.comm_combo)

        # Clear Path Button
        self.clear_path_btn = QPushButton("Clear Path")
        self.clear_path_btn.setToolTip("Clear target waypoints")
        self.clear_path_btn.clicked.connect(self._on_clear_path)
        top_bar.addWidget(self.clear_path_btn)

        # Clear Trail Button (Path Tracing on screen)
        self.clear_trail_btn = QPushButton("Clear Trail [C]")
        self.clear_trail_btn.setToolTip("Clear trajectory breadcrumb path tracing on screen (Key: C)")
        self.clear_trail_btn.clicked.connect(self._on_clear_trail)
        top_bar.addWidget(self.clear_trail_btn)

        # Max Speed Control Slider & Value Label
        self.speed_label = QLabel(f"Speed: {self.config.control.max_pwm}")
        self.speed_label.setStyleSheet("font-weight: bold; color: #58a6ff;")
        top_bar.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(60, 255)
        self.speed_slider.setValue(self.config.control.max_pwm)
        self.speed_slider.setFixedWidth(110)
        self.speed_slider.setToolTip("Adjust Max Motor Speed limit (60 to 255)")
        self.speed_slider.valueChanged.connect(self._on_speed_slider_changed)
        top_bar.addWidget(self.speed_slider)

        # Reset Sim Button
        self.reset_sim_btn = QPushButton("Reset Sim")
        self.reset_sim_btn.clicked.connect(self._on_reset_sim)
        top_bar.addWidget(self.reset_sim_btn)

        # Manual Control Checkbox
        self.manual_cb = QCheckBox("Manual (WASD)")
        self.manual_cb.stateChanged.connect(self._on_manual_mode_toggled)
        top_bar.addWidget(self.manual_cb)

        # Obstacle Avoidance Checkbox
        self.obstacle_cb = QCheckBox("Obstacles")
        self.obstacle_cb.setChecked(self.config.obstacle.enabled)
        self.obstacle_cb.stateChanged.connect(self._on_obstacle_toggled)
        top_bar.addWidget(self.obstacle_cb)

        # RL Agent Checkbox (Reinforced Learning approach)
        self.rl_cb = QCheckBox("RL Agent")
        self.rl_cb.setChecked(self.config.control.enable_rl)
        self.rl_cb.setToolTip("Enable Reinforcement Learning (Q-learning) to dynamically approach the marker")
        self.rl_cb.stateChanged.connect(self._on_rl_toggled)
        top_bar.addWidget(self.rl_cb)

        # Invert Motors Checkbox (Fix opposite driving / hardware polarity)
        self.inv_throttle_cb = QCheckBox("Invert Motors")
        self.inv_throttle_cb.setChecked(self.config.control.invert_throttle)
        self.inv_throttle_cb.setToolTip("Invert motor drive polarity (instantly fixes going opposite to marker)")
        self.inv_throttle_cb.stateChanged.connect(self._on_invert_throttle_toggled)
        top_bar.addWidget(self.inv_throttle_cb)

        # Target Braking Checkbox (Progressive Braking to Target Only)
        self.brake_cb = QCheckBox("Brake to Target")
        self.brake_cb.setChecked(self.config.control.enable_target_braking)
        self.brake_cb.setToolTip("Enable progressive deceleration curve to target only and active stopping at target")
        self.brake_cb.stateChanged.connect(self._on_braking_toggled)
        top_bar.addWidget(self.brake_cb)

        # Flip Heading 180° Button (Active per user confirmation)
        self.flip_heading_btn = QPushButton("Flip 180° [ON]")
        self.config.control.reverse_marker_heading = True
        self.motion_planner.control_config.reverse_marker_heading = True
        self.flip_heading_btn.setStyleSheet("background-color: #1f6feb; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 4px 10px;")
        self.flip_heading_btn.setToolTip("Flip marker heading orientation 180° (Active: marker mounted backwards)")
        self.flip_heading_btn.clicked.connect(self._on_flip_heading)
        top_bar.addWidget(self.flip_heading_btn)

        # Fullscreen Button
        self.fs_btn = QPushButton("Fullscreen [F11]")
        self.fs_btn.clicked.connect(self.toggle_fullscreen)
        top_bar.addWidget(self.fs_btn)

        top_bar.addStretch()

        # Emergency Stop Button (Large Red)
        self.estop_btn = QPushButton("EMERGENCY STOP [SPACE]")
        self.estop_btn.setStyleSheet("""
            QPushButton {
                background-color: #da3633;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #f85149;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #f85149;
            }
            QPushButton:pressed {
                background-color: #b62324;
            }
        """)
        self.estop_btn.clicked.connect(self._on_emergency_stop)
        top_bar.addWidget(self.estop_btn)

        main_layout.addLayout(top_bar)

        # 2. Main Vertical Splitter (Video on top, Telemetry & Logs at bottom)
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        # Video Canvas
        self.video_widget = VideoWidget()
        self.video_widget.waypoint_clicked.connect(self._on_waypoint_clicked)
        self.video_widget.clear_waypoints_requested.connect(self._on_clear_path)
        self.video_widget.toggle_fullscreen_requested.connect(self.toggle_fullscreen)
        v_splitter.addWidget(self.video_widget)

        # Bottom Horizontal Splitter (Telemetry on left, Log console on right)
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.telemetry_widget = TelemetryWidget()
        self.log_widget = LogWidget()

        h_splitter.addWidget(self.telemetry_widget)
        h_splitter.addWidget(self.log_widget)
        h_splitter.setSizes([450, 750])

        v_splitter.addWidget(h_splitter)
        v_splitter.setSizes([600, 220])

        main_layout.addWidget(v_splitter)

    def _init_shortcuts(self):
        """Setup keyboard shortcuts."""
        # F11 / Escape for Fullscreen
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._on_escape_pressed)
        # Spacebar for E-STOP
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_emergency_stop)
        # C or T key to Clear Path Tracing Trail
        QShortcut(QKeySequence("C"), self, self._on_clear_trail)
        QShortcut(QKeySequence("T"), self, self._on_clear_trail)

    def _init_comms(self):
        """Initialize comm driver callbacks."""
        self.comm_driver.register_telemetry_callback(self._on_telemetry_received)
        self.comm_driver.register_log_callback(self.log_widget.append_log)
        self.comm_driver.connect()
        self.camera_stream.start(self.config.camera.camera_index)

    def _populate_cameras(self):
        """Populate camera devices in dropdown."""
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()
        cams = list_available_cameras(max_test=8)
        selected_idx = 0
        for i, (idx, label) in enumerate(cams):
            self.camera_combo.addItem(label, idx)
            if idx == self.config.camera.camera_index:
                selected_idx = i
        self.camera_combo.setCurrentIndex(selected_idx)
        self.camera_combo.blockSignals(False)

    def _on_camera_changed(self, index: int):
        """Handle camera selection dropdown."""
        cam_idx = self.camera_combo.itemData(index)
        if cam_idx is not None:
            self.camera_stream.switch_camera(cam_idx)
            self.log_widget.append_log(f"Camera switched to: {self.camera_combo.currentText()}", "INFO")

    def _on_comm_mode_changed(self, index: int):
        """Switch communication driver backend."""
        mode = self.comm_combo.currentText()
        self.comm_driver.disconnect()

        if mode == "Simulation":
            self.comm_driver = MockSimDriver(self.simulator)
        else:
            self.comm_driver = EspNowSerialDriver(self.config.network)

        self.comm_driver.register_telemetry_callback(self._on_telemetry_received)
        self.comm_driver.register_log_callback(self.log_widget.append_log)
        self.comm_driver.connect()
        self.log_widget.append_log(f"Switched comm mode to: {mode}", "INFO")

    def _on_waypoint_clicked(self, x: float, y: float, append: bool):
        """Handle user click on video frame."""
        # Auto-exit manual mode so autonomous navigation immediately takes over
        if self.manual_cb.isChecked():
            self.manual_cb.setChecked(False)
        self.motion_planner.set_manual_override(False)
        self.motion_planner.is_emergency_stopped = False
        self.estop_btn.setText("EMERGENCY STOP [SPACE]")
        self.estop_btn.setStyleSheet("""
            QPushButton {
                background-color: #da3633;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #f85149;
                border-radius: 6px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #f85149;
            }
            QPushButton:pressed {
                background-color: #b62324;
            }
        """)

        self.motion_planner.add_waypoint(x, y, append=append)
        action = "Queued" if append else "Set"
        self.log_widget.append_log(f"{action} target waypoint: ({x:.1f}, {y:.1f}) px", "CMD")

    def _on_clear_path(self):
        """Clear active navigation waypoints."""
        self.motion_planner.clear_waypoints()
        self.log_widget.append_log("Cleared all navigation waypoints.", "INFO")

    def _on_clear_trail(self):
        """Clear breadcrumb trajectory trail / path tracing on screen."""
        self.motion_planner.clear_breadcrumbs()
        self.log_widget.append_log("Cleared path trace trail from screen.", "INFO")

    def _on_speed_slider_changed(self, value: int):
        """Update maximum motor speed PWM in real time."""
        self.config.control.max_pwm = value
        self.motion_planner.control_config.max_pwm = value
        self.speed_label.setText(f"Speed: {value}")
        self.log_widget.append_log(f"Max Motor Speed limit updated: {value} / 255", "CONFIG")

    def _on_reset_sim(self):
        """Reset virtual RC car to arena center."""
        self.simulator.reset_position()
        self.motion_planner.clear_waypoints()
        self.log_widget.append_log("Reset simulator car position.", "INFO")

    def _on_obstacle_toggled(self, state: int):
        """Toggle ultrasonic obstacle avoidance."""
        enabled = (state == 2 or state == Qt.CheckState.Checked.value)
        self.config.obstacle.enabled = enabled
        self.motion_planner.obstacle_avoidance.config.enabled = enabled
        status_str = "ENABLED" if enabled else "DISABLED (Pure Vision)"
        self.log_widget.append_log(f"Obstacle Avoidance: {status_str}", "INFO")

    def _on_rl_toggled(self, state: int):
        """Toggle Reinforcement Learning approach controller."""
        enabled = (state == 2 or state == Qt.CheckState.Checked.value)
        self.config.control.enable_rl = enabled
        self.motion_planner.control_config.enable_rl = enabled
        status_str = "ENABLED (Q-Learning Navigation)" if enabled else "DISABLED (Classical PID)"
        self.log_widget.append_log(f"Reinforcement Learning: {status_str}", "CONFIG")

    def _on_invert_throttle_toggled(self, state: int):
        """Toggle motor forward/reverse direction polarity."""
        inverted = (state == 2 or state == Qt.CheckState.Checked.value)
        self.config.control.invert_throttle = inverted
        self.motion_planner.control_config.invert_throttle = inverted
        status_str = "INVERTED (Reversed)" if inverted else "NORMAL"
        self.log_widget.append_log(f"Motor Direction Polarity: {status_str}", "CONFIG")

    def _on_braking_toggled(self, state: int):
        """Toggle progressive deceleration into target only."""
        enabled = (state == 2 or state == Qt.CheckState.Checked.value)
        self.config.control.enable_target_braking = enabled
        self.motion_planner.control_config.enable_target_braking = enabled
        status_str = "ENABLED (Progressive Braking to Target Only)" if enabled else "DISABLED (Constant Speed)"
        self.log_widget.append_log(f"Target Braking: {status_str}", "CONFIG")

    def _on_flip_heading(self):
        """Flip marker heading angle by 180 degrees."""
        curr = getattr(self.config.control, "reverse_marker_heading", False)
        new_val = not curr
        self.config.control.reverse_marker_heading = new_val
        self.motion_planner.control_config.reverse_marker_heading = new_val
        if new_val:
            self.flip_heading_btn.setText("Flip 180° [ON]")
            self.flip_heading_btn.setStyleSheet("background-color: #1f6feb; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 4px 10px;")
        else:
            self.flip_heading_btn.setText("Flip 180° [OFF]")
            self.flip_heading_btn.setStyleSheet("")
        status_str = "ACTIVE 180° (Reversed)" if new_val else "NORMAL 0°"
        self.log_widget.append_log(f"Marker Heading Alignment: {status_str}", "CONFIG")

    def _on_emergency_stop(self):
        """Toggle emergency stop."""
        is_stopped = not self.motion_planner.is_emergency_stopped
        self.motion_planner.set_emergency_stop(is_stopped)
        self.comm_driver.send_drive_command(0, 0, 0.0, 0.0)

        if is_stopped:
            self.log_widget.append_log("EMERGENCY STOP ACTIVATED!", "ERROR")
            self.estop_btn.setText("RESUME AUTO [SPACE]")
            self.estop_btn.setStyleSheet("background-color: #3fb950; color: #ffffff; font-weight: bold; padding: 6px 16px; border-radius: 6px;")
        else:
            self.log_widget.append_log("Emergency stop cleared.", "INFO")
            self.estop_btn.setText("EMERGENCY STOP [SPACE]")
            self.estop_btn.setStyleSheet("""
                QPushButton {
                    background-color: #da3633;
                    color: #ffffff;
                    font-weight: bold;
                    font-size: 13px;
                    border: 1px solid #f85149;
                    border-radius: 6px;
                    padding: 6px 16px;
                }
                QPushButton:hover {
                    background-color: #f85149;
                }
                QPushButton:pressed {
                    background-color: #b62324;
                }
            """)

    def _on_manual_mode_toggled(self, state: int):
        """Enable / disable manual keyboard override."""
        enabled = (state == Qt.CheckState.Checked.value)
        self.motion_planner.set_manual_override(enabled)
        mode_str = "Enabled" if enabled else "Disabled"
        self.log_widget.append_log(f"Manual WASD mode {mode_str}.", "INFO")

    def _on_telemetry_received(self, data: TelemetryData):
        """Telemetry callback from comms driver."""
        self._active_telemetry = data

    def toggle_fullscreen(self):
        """Toggle between fullscreen and normal window."""
        if self.isFullScreen():
            self.showNormal()
            self.fs_btn.setText("Fullscreen [F11]")
        else:
            self.showFullScreen()
            self.fs_btn.setText("Exit Fullscreen [F11]")

    def _on_escape_pressed(self):
        if self.isFullScreen():
            self.toggle_fullscreen()

    def keyPressEvent(self, event):
        """Track WASD keys for manual car steering."""
        self._keys_pressed.add(event.key())
        self._process_manual_keys()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() in self._keys_pressed:
            self._keys_pressed.remove(event.key())
        self._process_manual_keys()
        super().keyReleaseEvent(event)

    def _process_manual_keys(self):
        """Compute manual throttle and steering from held keys."""
        if not self.motion_planner.is_manual_mode:
            return

        throttle = 0.0
        steering = 0.0

        if Qt.Key.Key_W in self._keys_pressed or Qt.Key.Key_Up in self._keys_pressed:
            throttle += 1.0
        if Qt.Key.Key_S in self._keys_pressed or Qt.Key.Key_Down in self._keys_pressed:
            throttle -= 1.0
        # Swapped A and D per user request
        if Qt.Key.Key_A in self._keys_pressed or Qt.Key.Key_Left in self._keys_pressed:
            steering += 1.0
        if Qt.Key.Key_D in self._keys_pressed or Qt.Key.Key_Right in self._keys_pressed:
            steering -= 1.0

        self.motion_planner.set_manual_override(True, throttle=throttle, steering=steering)

    def _main_loop_step(self):
        """Master ~30Hz update loop executing tracking, planning, comms, and HUD rendering."""
        # 1. Acquire Frame
        is_sim_camera = (self.camera_stream.current_index < 0)
        
        if is_sim_camera:
            # Advance physics simulator
            self.simulator.step()
            raw_frame = self.simulator.render_frame()
            fps = 30.0
        else:
            raw_frame, _, fps = self.camera_stream.read()
            if raw_frame is None:
                return

        # 2. ArUco Marker Detection & Tracking
        target_pose, all_poses = self.tracker.detect(raw_frame)
        self._active_target_pose = target_pose
        self._all_poses = all_poses

        # Auto-track Goal Marker: If multiple markers exist, approach the non-car marker!
        if getattr(self.config.control, "auto_track_goal_marker", True) and len(all_poses) > 1 and target_pose is not None:
            car_id = target_pose.id
            for p in all_poses:
                if p.id != car_id:
                    # Dynamically set or track goal marker
                    if not self.motion_planner.waypoints:
                        self.motion_planner.add_waypoint(p.x, p.y, append=False)
                    else:
                        cur_wx, cur_wy = self.motion_planner.waypoints[0]
                        if math.hypot(p.x - cur_wx, p.y - cur_wy) > 8.0:
                            self.motion_planner.waypoints[0] = (p.x, p.y)
                    break

        # 3. Read Ultrasonic Sensor Telemetry
        us_l = self._active_telemetry.us_left_cm
        us_f = self._active_telemetry.us_front_cm
        us_r = self._active_telemetry.us_right_cm

        # 4. Motion Planning & Obstacle Avoidance (RL or PID)
        cmd, avoidance = self.motion_planner.update(
            car_pose=target_pose,
            us_left_cm=us_l,
            us_right_cm=us_r,
            us_front_cm=us_f
        )
        self._active_command = cmd
        self._active_avoidance = avoidance

        # 5. Transmit Drive Commands to Car
        self.comm_driver.send_drive_command(
            v_left=cmd.v_left,
            v_right=cmd.v_right,
            steer_norm=cmd.steer_norm,
            speed_norm=cmd.speed_norm
        )

        # 6. Render HUD Overlays
        state_info = {
            "fps": fps,
            "status": cmd.mode,
            "target_dist": cmd.target_dist,
            "heading_err": cmd.heading_err_deg,
            "rl_action": getattr(cmd, "rl_action", ""),
            "rl_reward": getattr(cmd, "rl_reward", 0.0)
        }
        sensor_dict = {
            "us_l": us_l,
            "us_f": us_f,
            "us_r": us_r
        }

        display_frame = draw_hud_overlays(
            frame=raw_frame,
            target_pose=target_pose,
            all_poses=all_poses,
            waypoints=self.motion_planner.waypoints,
            breadcrumbs=self.motion_planner.breadcrumbs,
            ultrasonic_data=sensor_dict,
            state_info=state_info,
            warning_cm=self.config.obstacle.warning_distance_cm,
            critical_cm=self.config.obstacle.critical_distance_cm
        )

        # 7. Update GUI Canvas & Telemetry Gauges
        self.video_widget.set_frame(display_frame)
        self.telemetry_widget.update_telemetry(self._active_telemetry, cmd, avoidance)

    def closeEvent(self, event):
        """Graceful shutdown on window close."""
        self.timer.stop()
        self.camera_stream.stop()
        self.comm_driver.send_drive_command(0, 0)
        self.comm_driver.disconnect()
        event.accept()
