from __future__ import annotations

import sys
from PyQt5.QtCore import Qt, QTimer, QDateTime, QTime, QDate, QDateTime as QDt
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QComboBox,
    QDateEdit,
    QCalendarWidget,
    QTimeEdit,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox,
    QCheckBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from datetime import datetime, date, timedelta

from typing import Any

from communication import start_server, send_message
from csv_database import SmartHomeCSV
from floor_plan import FloorPlanView, devices, PlanDevice
from data_generator import (
    add_variation,
    analyze_pattern,
    load_from_csv,
    save_to_csv,
)


class MainPanel(QMainWindow):
    """Main application window for the home control panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("스마트홈 패널")
        self.resize(1280, 960)
        self.db = SmartHomeCSV()
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

        # Floor plan view with interactive icons
        self.floor_view = FloorPlanView(devices, callback=self.device_clicked)
        content_layout.addWidget(self.floor_view, 3)

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

        # ----- Tabs -----
        self._init_tab_data()
        self._init_tab_learning()
        self._init_tab_service()
        self._init_tab_query()
        self._init_tab_settings()

    def update_clock(self) -> None:
        self.clock_label.setText(
            QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        )

    def device_clicked(self, device: PlanDevice) -> None:
        state = "ON" if device.state else "OFF"
        self.control_log.append(f"디바이스 '{device.name}'을(를) {state} 상태로 변경했습니다.")
        self.db.update_device_status(device.name, state)


    # ------------------------------------------------------------------
    # Tab initializers

    def _init_tab_data(self) -> None:
        tab = self.tabs.widget(0)
        layout = QVBoxLayout(tab)

        form_layout = QHBoxLayout()
        self.data_device = QComboBox()
        for d in devices:
            self.data_device.addItem(d.name)
        form_layout.addWidget(self.data_device)

        self.data_time = QTimeEdit(QTime.currentTime())
        self.data_time.setDisplayFormat("HH:mm")
        form_layout.addWidget(self.data_time)

        self.data_action = QComboBox()
        self.data_action.addItems(["ON", "OFF"])
        form_layout.addWidget(self.data_action)

        add_btn = QPushButton("패턴 추가")
        add_btn.clicked.connect(self.add_pattern)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)

        self.pattern_list = QListWidget()
        layout.addWidget(self.pattern_list, 1)

        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("일주일치 생성")
        gen_btn.clicked.connect(self.generate_week)
        btn_layout.addWidget(gen_btn)

        save_btn = QPushButton("CSV 저장")
        save_btn.clicked.connect(self.save_csv)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.base_events: list[dict[str, Any]] = []
        self.generated_events: list[dict[str, Any]] = []


    def _init_tab_learning(self) -> None:
        tab = self.tabs.widget(1)
        layout = QVBoxLayout(tab)

        load_btn = QPushButton("데이터 불러오기")
        load_btn.clicked.connect(self.load_csv)
        layout.addWidget(load_btn)

        analyze_btn = QPushButton("패턴 분석 시작")
        analyze_btn.clicked.connect(self.run_analysis)
        layout.addWidget(analyze_btn)

        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        layout.addWidget(self.analysis_text, 1)

        self.loaded_events: list[dict[str, Any]] = []


    def _init_tab_service(self) -> None:
        tab = self.tabs.widget(2)
        layout = QVBoxLayout(tab)

        top = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.toggle_service)
        top.addWidget(self.play_btn)

        self.speed_box = QComboBox()
        self.speed_box.addItems(["1x", "10x", "60x"])
        top.addWidget(self.speed_box)

        self.current_time_label = QLabel("--:--")
        top.addWidget(self.current_time_label)
        layout.addLayout(top)

        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        layout.addWidget(self.service_log, 1)

        self.service_timer = QTimer(self)
        self.service_timer.timeout.connect(self.advance_service)
        self.service_running = False
        self.sim_time: datetime | None = None
        self.service_index = 0


    def _init_tab_query(self) -> None:
        tab = self.tabs.widget(3)
        layout = QVBoxLayout(tab)

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_query)
        layout.addWidget(self.calendar)

        self.query_table = QTableWidget(0, 4)
        self.query_table.setHorizontalHeaderLabels(["시간", "디바이스", "동작", "값"])
        layout.addWidget(self.query_table, 1)


    def _init_tab_settings(self) -> None:
        tab = self.tabs.widget(4)
        layout = QVBoxLayout(tab)

        self.sensitivity_spin = QSpinBox()
        self.sensitivity_spin.setRange(1, 10)
        self.sensitivity_spin.setValue(3)
        layout.addWidget(QLabel("패턴 감지 민감도"))
        layout.addWidget(self.sensitivity_spin)

        self.chat_notify = QCheckBox("Chatbot 알림")
        self.chat_notify.setChecked(True)
        layout.addWidget(self.chat_notify)

    def receive_message(self, message: str) -> None:
        """Callback for messages received from the chatbot."""

        self.control_log.append(f"챗봇: {message}")

    # ------------------------------------------------------------------
    # Tab actions

    def add_pattern(self) -> None:
        time_val = self.data_time.time()
        device = self.data_device.currentText()
        action = self.data_action.currentText()
        self.base_events.append({"time": time_val, "device": device, "value": action})
        self.pattern_list.addItem(f"{time_val.toString('HH:mm')} - {device} {action}")

    def generate_week(self) -> None:
        self.generated_events.clear()
        base_date = date.today()
        for i in range(7):
            day = base_date + timedelta(days=i)
            for ev in self.base_events:
                dt = QDt(day, ev["time"]).toPyDateTime()
                self.generated_events.append(
                    {"timestamp": dt, "device": ev["device"], "action": "power", "value": ev["value"]}
                )
        self.generated_events = add_variation(self.generated_events, 0.5)
        self.generated_events.sort(key=lambda e: e["timestamp"])
        self.control_log.append("일주일치 패턴을 생성했습니다.")

    def save_csv(self) -> None:
        if not self.generated_events:
            return
        save_to_csv(self.generated_events, "data/generated.csv")
        self.control_log.append("CSV 파일로 저장했습니다.")

    def load_csv(self) -> None:
        try:
            self.loaded_events = load_from_csv("data/generated.csv")
            self.loaded_events.sort(key=lambda e: e["timestamp"])
            self.analysis_text.append(f"{len(self.loaded_events)}개 이벤트 불러옴")
        except FileNotFoundError:
            self.analysis_text.append("CSV 파일을 찾을 수 없습니다.")

    def run_analysis(self) -> None:
        if not self.loaded_events:
            return
        result = analyze_pattern(self.loaded_events)
        lines = []
        for device, times in result.items():
            for t, count in times.items():
                lines.append(f"{device}: 매일 {t} 패턴 {count}회 발견")
        self.analysis_text.setPlainText("\n".join(lines) or "패턴 없음")

    # ----- service -----

    def toggle_service(self) -> None:
        if self.service_running:
            self.service_timer.stop()
            self.service_running = False
            self.play_btn.setText("Play")
            return

        if not self.loaded_events:
            self.load_csv()
        if not self.loaded_events:
            return
        # Prepare pattern detection map
        self.detected_patterns = analyze_pattern(self.loaded_events)
        self.sent_patterns: set[tuple[str, str]] = set()

        self.service_running = True
        self.play_btn.setText("Pause")
        self.sim_time = self.loaded_events[0]["timestamp"]
        self.service_index = 0
        self.current_time_label.setText(self.sim_time.strftime("%Y-%m-%d %H:%M"))
        self.service_timer.start(1000)

    def advance_service(self) -> None:
        if not self.service_running or self.sim_time is None:
            return
        speed = int(self.speed_box.currentText().replace("x", ""))
        self.sim_time += timedelta(minutes=speed)
        self.current_time_label.setText(self.sim_time.strftime("%Y-%m-%d %H:%M"))
        while (
            self.service_index < len(self.loaded_events)
            and self.loaded_events[self.service_index]["timestamp"] <= self.sim_time
        ):
            event = self.loaded_events[self.service_index]
            self.apply_event(event)
            self.service_index += 1
        if self.service_index >= len(self.loaded_events):
            self.toggle_service()

    def apply_event(self, event: dict) -> None:
        device_name = event["device"]
        value = event["value"]
        if device_name == "모든조명":
            targets = [d for d in devices if "조명" in d.name]
        else:
            targets = [d for d in devices if d.name == device_name]
        for dev in targets:
            dev.state = value == "ON"
        self.floor_view.refresh()
        for dev in devices:
            state = "ON" if dev.state else "OFF"
            self.db.update_device_status(dev.name, state)
        self.db.save_pattern(event["timestamp"], device_name, value)
        ts = event["timestamp"].strftime("%Y-%m-%d %H:%M")
        self.service_log.append(f"{ts} - {device_name} {value}")

        time_key = event["timestamp"].strftime("%H:%M")
        if (
            getattr(self, "detected_patterns", None)
            and self.chat_notify.isChecked()
            and device_name in self.detected_patterns
            and self.detected_patterns[device_name].get(time_key)
            and (device_name, time_key) not in self.sent_patterns
        ):
            send_message(f"패턴 감지: {device_name} {time_key} {value}")
            self.sent_patterns.add((device_name, time_key))

    # ----- query tab -----

    def update_query(self) -> None:
        day = self.calendar.selectedDate().toPyDate()
        events = self.loaded_events
        filtered = [e for e in events if e["timestamp"].date() == day]
        self.query_table.setRowCount(len(filtered))
        for row, e in enumerate(filtered):
            self.query_table.setItem(row, 0, QTableWidgetItem(e["timestamp"].strftime("%H:%M")))
            self.query_table.setItem(row, 1, QTableWidgetItem(e["device"]))
            self.query_table.setItem(row, 2, QTableWidgetItem(e["action"]))
            self.query_table.setItem(row, 3, QTableWidgetItem(str(e["value"])))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    panel = MainPanel()
    panel.show()
    sys.exit(app.exec_())
