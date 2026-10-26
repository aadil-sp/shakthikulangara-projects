"""Timestamped error log and communication message console widget."""

import datetime
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QTextCursor, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton, QComboBox
)


class LogWidget(QWidget):
    """Console logging widget with color-coded message levels and export feature."""

    LEVEL_COLORS = {
        "INFO": "#58a6ff",       # Blue
        "WARN": "#d29922",       # Amber
        "ERROR": "#f85149",      # Red
        "CMD": "#3fb950",        # Green
        "TELEMETRY": "#a371f7",  # Purple
        "DEBUG": "#8b949e",      # Gray
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header bar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        title = QLabel("SYSTEM & ERROR LOGS")
        title.setStyleSheet("font-weight: bold; color: #8b949e; font-size: 11px; letter-spacing: 1px;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Levels", "INFO", "WARN", "ERROR", "CMD"])
        self.filter_combo.setStyleSheet("background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 2px 6px; font-size: 11px;")
        header_layout.addWidget(self.filter_combo)

        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; border-radius: 4px; padding: 2px 8px; font-size: 11px;")
        clear_btn.clicked.connect(self.clear_logs)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Text Console
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Consolas', 'Menlo', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.text_edit)

    @pyqtSlot(str, str)
    def append_log(self, message: str, level: str = "INFO"):
        """Append a new formatted log line."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = self.LEVEL_COLORS.get(level.upper(), "#c9d1d9")

        # HTML formatted string
        html_msg = (
            f"<span style='color: #8b949e;'>[{timestamp}]</span> "
            f"<span style='color: {color}; font-weight: bold;'>[{level.upper()}]</span> "
            f"<span style='color: #e6edf3;'>{message}</span>"
        )

        self.text_edit.append(html_msg)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def clear_logs(self):
        """Clear console content."""
        self.text_edit.clear()
