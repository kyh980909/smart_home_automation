from __future__ import annotations

import sys
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from communication import start_server
from devices import DEVICES


class MainPanel(QMainWindow):
    """Main application window for the home control panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("스마트홈 패널")
        self.resize(900, 600)
        self._init_ui()
        start_server(self.receive_message)

    # UI setup
    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # Top tabs
        self.tabs = QTabWidget()
        for name in ["학습데이터 생성", "학습", "서비스", "조회", "환경설정"]:
            self.tabs.addTab(QWidget(), name)
        root_layout.addWidget(self.tabs)

        # Main content area
        content_layout = QHBoxLayout()
        root_layout.addLayout(content_layout, 1)

        # Floor plan with device buttons (left 60%)
        floor_widget = QWidget()
        grid = QGridLayout(floor_widget)
        self.device_buttons = []
        for i, device in enumerate(DEVICES):
            btn = QPushButton(f"{device.name}: OFF")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, d=device, b=btn: self.toggle_device(d, b))
            grid.addWidget(btn, i // 2, i % 2)
            self.device_buttons.append(btn)
        content_layout.addWidget(floor_widget, 3)

        # Right side (clock and control panel)
        side_widget = QWidget()
        side_layout = QVBoxLayout(side_widget)
        side_layout.setSpacing(10)

        # Clock / calendar (top)
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        side_layout.addWidget(self.clock_label, 1)

        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()

        # Control panel (bottom)
        self.control_log = QTextEdit()
        self.control_log.setReadOnly(True)
        side_layout.addWidget(self.control_log, 1)

        content_layout.addWidget(side_widget, 2)

    def update_clock(self) -> None:
        self.clock_label.setText(
            QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        )

    def toggle_device(self, device, button) -> None:
        device.toggle()
        state = "ON" if device.state else "OFF"
        button.setText(f"{device.name}: {state}")
        self.control_log.append(f"디바이스 '{device.name}'을(를) {state} 상태로 변경했습니다.")

    def receive_message(self, message: str) -> None:
        """Callback for messages received from the chatbot."""

        self.control_log.append(f"챗봇: {message}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = MainPanel()
    panel.show()
    sys.exit(app.exec_())
