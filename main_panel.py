from __future__ import annotations

import sys
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QDateTime,
    QTime,
    QDate,
    QDateTime as QDt,
    pyqtSignal,
)
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
    QGroupBox,
    QSlider,
    QWidget,
)

from datetime import datetime, date, timedelta

from typing import Any

from communication import start_server, send_message
from csv_database import SmartHomeCSV
from floor_plan import FloorPlanView, devices, PlanDevice, ExtendedFloorPlanView, extended_devices
from extended_devices import DeviceType, ExtendedPlanDevice
from data_generator import (
    add_variation,
    analyze_pattern,
    load_from_csv,
    save_to_csv,
)
from time_series_graph import TimeSeriesChart, generate_sample_data


class MainPanel(QMainWindow):
    """Main application window for the home control panel."""

    message_received = pyqtSignal(str)

    def __init__(self, use_extended_devices=False) -> None:
        super().__init__()
        self.setWindowTitle("스마트홈 패널")
        self.resize(1280, 960)
        self.db = SmartHomeCSV()
        self.use_extended_devices = use_extended_devices
        self.message_received.connect(self._handle_chat_message)
        self._init_ui()
        start_server(self.receive_message)

    # UI setup
    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        # Top tabs
        self.tabs = QTabWidget()
        for name in ["학습데이터 생성", "학습", "서비스", "조회", "그래프", "환경설정"]:
            self.tabs.addTab(QWidget(), name)
        root_layout.addWidget(self.tabs)

        # Main content area
        content_layout = QHBoxLayout()
        root_layout.addLayout(content_layout, 1)

        # Floor plan view with interactive icons
        if self.use_extended_devices:
            self.floor_view = ExtendedFloorPlanView(extended_devices, callback=self.device_clicked)
        else:
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
        self._init_tab_graph()
        self._init_tab_settings()

    def update_clock(self) -> None:
        self.clock_label.setText(
            QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm:ss")
        )

    def device_clicked(self, device) -> None:
        """디바이스 클릭 핵들러 (기존 및 확장 디바이스 지원)"""
        if self.use_extended_devices and isinstance(device, ExtendedPlanDevice):
            # 확장된 디바이스 처리
            state_text = device.get_status_text()
            self.control_log.append(f"디바이스 '{device.name}'을(를) {state_text} 상태로 변경했습니다.")
            
            state = "ON" if device.state else "OFF"
            self.db.update_device_status(device.name, state, device.type.value)
        else:
            # 기존 디바이스 처리
            state = "ON" if device.state else "OFF"
            self.control_log.append(f"디바이스 '{device.name}'을(를) {state} 상태로 변경했습니다.")
            self.db.update_device_status(device.name, state)
        
        # 패턴 기록
        ts = self.sim_time if hasattr(self, 'sim_time') and self.sim_time else datetime.now()
        self.db.save_pattern(ts, device.name, state)


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

        # ----- Advanced generation controls -----
        self.season = "봄"
        self.gender = "M"
        self.age_group = "장년"

        adv_box = QGroupBox("상세 설정")
        adv_layout = QVBoxLayout(adv_box)

        # Season buttons
        season_group = QGroupBox("계절요인 적용")
        s_layout = QHBoxLayout(season_group)
        self.season_buttons = {}
        for s in ["봄", "여름", "가을", "겨울"]:
            btn = QPushButton(s)
            btn.setCheckable(True)
            btn.clicked.connect(lambda chk, val=s: self._set_season(val))
            self.season_buttons[s] = btn
            s_layout.addWidget(btn)
        self.season_buttons[self.season].setChecked(True)
        adv_layout.addWidget(season_group)

        # Gender buttons
        gender_group = QGroupBox("거주자 성별")
        g_layout = QHBoxLayout(gender_group)
        self.gender_buttons = {}
        for g in ["M", "F"]:
            btn = QPushButton(g)
            btn.setCheckable(True)
            btn.clicked.connect(lambda chk, val=g: self._set_gender(val))
            self.gender_buttons[g] = btn
            g_layout.addWidget(btn)
        self.gender_buttons[self.gender].setChecked(True)
        adv_layout.addWidget(gender_group)

        # Age buttons
        age_group = QGroupBox("연령대")
        a_layout = QHBoxLayout(age_group)
        self.age_buttons = {}
        for a in ["청년", "장년", "노년"]:
            btn = QPushButton(a)
            btn.setCheckable(True)
            btn.clicked.connect(lambda chk, val=a: self._set_age(val))
            self.age_buttons[a] = btn
            a_layout.addWidget(btn)
        self.age_buttons[self.age_group].setChecked(True)
        adv_layout.addWidget(age_group)

        self.complexity_slider = QSlider(Qt.Horizontal)
        self.complexity_slider.setMinimum(1)
        self.complexity_slider.setMaximum(10)
        self.complexity_slider.setValue(5)
        adv_layout.addWidget(QLabel("패턴 복잡도"))
        adv_layout.addWidget(self.complexity_slider)

        layout.addWidget(adv_box)

        adv_btns = QHBoxLayout()
        sim_btn = QPushButton("유사 생활패턴 생성(Week day)")
        sim_btn.clicked.connect(self.generate_similar_patterns_btn)
        adv_btns.addWidget(sim_btn)

        detail_btn = QPushButton("상세설정기반 생성")
        detail_btn.clicked.connect(self.generate_detailed_patterns_btn)
        adv_btns.addWidget(detail_btn)

        ai_btn = QPushButton("생성AI로 생성해보기(Trial version)")
        ai_btn.clicked.connect(self.generate_ai_patterns_btn)
        adv_btns.addWidget(ai_btn)

        layout.addLayout(adv_btns)

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
        self.play_btn = QPushButton("Play and Record")
        self.play_btn.clicked.connect(self.toggle_service)
        top.addWidget(self.play_btn)

        self.step_btn = QPushButton("Play by Tap and Record")
        self.step_btn.clicked.connect(self.step_service)
        top.addWidget(self.step_btn)

        self.speed_box = QComboBox()
        self.speed_box.addItems(["1x", "10x", "60x"])
        top.addWidget(self.speed_box)

        self.duration_box = QComboBox()
        self.duration_box.addItems(["24h", "1w"])
        top.addWidget(self.duration_box)

        self.current_time_label = QLabel("--:--")
        top.addWidget(self.current_time_label)
        layout.addLayout(top)

        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        layout.addWidget(self.service_log, 1)

        self.service_timer = QTimer(self)
        self.service_timer.timeout.connect(self.advance_service)
        self.service_running = False
        self.step_mode = False
        self.paused_for_chatbot = False
        self.pending_event: dict | None = None
        self.sim_time: datetime | None = None
        self.sim_end_time: datetime | None = None
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


    def _init_tab_graph(self) -> None:
        """그래프 탭 초기화 - 시계열 데이터 시각화"""
        tab = self.tabs.widget(4)  # 그래프 탭
        layout = QVBoxLayout(tab)
        
        # 그래프 제어 버튼들
        control_layout = QHBoxLayout()
        
        # 디바이스 선택
        self.graph_device_combo = QComboBox()
        self.graph_device_combo.addItem("전체 디바이스")
        for d in devices:
            self.graph_device_combo.addItem(d.name)
        control_layout.addWidget(QLabel("디바이스:"))
        control_layout.addWidget(self.graph_device_combo)
        
        # 그래프 타입 선택
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["사용 패턴", "온도 추이", "일일 요약"])
        control_layout.addWidget(QLabel("그래프 타입:"))
        control_layout.addWidget(self.graph_type_combo)
        
        # 새로고침 버튼
        refresh_btn = QPushButton("그래프 새로고침")
        refresh_btn.clicked.connect(self.refresh_graph)
        control_layout.addWidget(refresh_btn)
        
        # 샘플 데이터 생성 버튼
        sample_btn = QPushButton("샘플 데이터 보기")
        sample_btn.clicked.connect(self.show_sample_graph)
        control_layout.addWidget(sample_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 그래프 위젯
        self.time_series_chart = TimeSeriesChart(parent=tab, width=12, height=8)
        layout.addWidget(self.time_series_chart)
        
        # 초기 샘플 그래프 표시
        self.show_sample_graph()

    def _init_tab_settings(self) -> None:
        tab = self.tabs.widget(5)  # 환경설정 탭
        layout = QVBoxLayout(tab)

        self.sensitivity_spin = QSpinBox()
        self.sensitivity_spin.setRange(1, 10)
        self.sensitivity_spin.setValue(3)
        layout.addWidget(QLabel("패턴 감지 민감도"))
        layout.addWidget(self.sensitivity_spin)

        self.chat_notify = QCheckBox("Chatbot 알림")
        self.chat_notify.setChecked(True)
        layout.addWidget(self.chat_notify)

    # ------------------------------------------------------------------
    # 그래프 관련 메서드
    
    def refresh_graph(self) -> None:
        """실제 데이터로 그래프를 새로고침"""
        if not hasattr(self, 'loaded_events') or not self.loaded_events:
            self.control_log.append("표시할 데이터가 없습니다. 학습 탭에서 데이터를 먼저 불러오세요.")
            return
            
        device_name = self.graph_device_combo.currentText()
        graph_type = self.graph_type_combo.currentText()
        
        if device_name == "전체 디바이스":
            device_name = None
            
        try:
            if graph_type == "사용 패턴":
                self.time_series_chart.plot_device_usage(self.loaded_events, device_name)
            elif graph_type == "온도 추이":
                self.time_series_chart.plot_temperature_trend(self.loaded_events)
            elif graph_type == "일일 요약":
                self.time_series_chart.plot_daily_summary(self.loaded_events)
                
            self.control_log.append(f"{graph_type} 그래프를 업데이트했습니다.")
        except Exception as e:
            self.control_log.append(f"그래프 업데이트 오류: {str(e)}")
    
    def show_sample_graph(self) -> None:
        """샘플 데이터로 그래프 표시"""
        sample_data = generate_sample_data()
        device_name = self.graph_device_combo.currentText()
        graph_type = self.graph_type_combo.currentText()
        
        if device_name == "전체 디바이스":
            device_name = None
            
        try:
            if graph_type == "사용 패턴":
                self.time_series_chart.plot_device_usage(sample_data, device_name)
            elif graph_type == "온도 추이":
                self.time_series_chart.plot_temperature_trend(sample_data)
            elif graph_type == "일일 요약":
                self.time_series_chart.plot_daily_summary(sample_data)
                
            self.control_log.append(f"샘플 {graph_type} 그래프를 표시했습니다.")
        except Exception as e:
            self.control_log.append(f"샘플 그래프 오류: {str(e)}")

    def receive_message(self, message: str) -> None:
        """Callback for messages received from the chatbot."""
        # 메시지는 별도의 스레드에서 전달되므로 시그널을 통해 UI 스레드로 전달
        self.message_received.emit(message)

    def _handle_chatbot_command(self, message: str) -> None:
        """챗봇으로부터의 명령어 처리"""
        message_lower = message.lower().strip()
        
        # 상태 요청 처리
        if "request_status" in message_lower:
            self._send_device_status_to_chatbot()
        
        # 디바이스 제어 명령 처리
        elif "control:" in message_lower:
            self._process_device_control_command(message)
        
        # 기타 대화 및 반응
        else:
            self._handle_general_chat_message(message)
    
    def _send_device_status_to_chatbot(self) -> None:
        """디바이스 상태를 챗봇에게 전송"""
        device_list = extended_devices if self.use_extended_devices else devices
        status_info = []
        
        for device in device_list:
            if self.use_extended_devices:
                status = device.get_status_text()
                status_info.append(f"{device.name}: {status}")
            else:
                state = "ON" if device.state else "OFF"
                status_info.append(f"{device.name}: {state}")
        
        status_message = "\n".join(status_info)
        send_message(f"DEVICE_STATUS:\n{status_message}", port=7778)
    
    def _process_device_control_command(self, message: str) -> None:
        """디바이스 제어 명령 처리"""
        try:
            # CONTROL:명령:원본텍스트 형식으로 파싱
            parts = message.split(":", 2)
            if len(parts) >= 2:
                command = parts[1].strip()
                self._execute_chatbot_device_command(command)
        except Exception as e:
            self.control_log.append(f"명령 처리 오류: {str(e)}")
    
    def _execute_chatbot_device_command(self, command: str) -> None:
        """챗봇 디바이스 명령 실행"""
        device_list = extended_devices if self.use_extended_devices else devices
        
        if command == 'all_lights_on':
            for device in device_list:
                if ("조명" in device.name):
                    device.state = True
            self.control_log.append("챗봇 명령: 모든 조명을 켰습니다.")
            
        elif command == 'all_lights_off':
            for device in device_list:
                if ("조명" in device.name):
                    device.state = False
            self.control_log.append("챗봇 명령: 모든 조명을 껐습니다.")
            
        elif command.startswith('light_'):
            # 개별 조명 제어 처리
            action = 'on' if command.endswith('_on') else 'off'
            # 여기에 더 상세한 로직 추가 가능
            
        elif command.startswith('aircon_'):
            # 에어컨 제어 처리
            aircon_devices = [d for d in device_list if '에어컨' in d.name]
            for aircon in aircon_devices:
                if command == 'aircon_on':
                    aircon.state = True
                elif command == 'aircon_off':
                    aircon.state = False
        
        # 화면 업데이트
        self.floor_view.refresh()
    
    def _handle_general_chat_message(self, message: str) -> None:
        """일반 대화 메시지 처리"""
        # 기존 처리 로직 유지
        pass

    def _handle_chat_message(self, message: str) -> None:
        """Handle messages from the chatbot on the UI thread."""
        self.control_log.append(f"챗봇: {message}")

        # 우선 명령어 처리
        self._handle_chatbot_command(message)

        if self.paused_for_chatbot:
            if message.strip() == "CREATE_RULE" and self.pending_event:
                cond = self.pending_event["timestamp"].strftime("%H:%M")
                act = self.pending_event["value"]
                dev = self.pending_event["device"]
                self.db.save_rule(f"time == {cond}", f"{dev} {act}")
                self.control_log.append(
                    f"규칙 생성: time == {cond} -> {dev} {act}"
                )
            self.pending_event = None
            self.paused_for_chatbot = False
            if self.service_running and not self.step_mode:
                self.service_timer.start(1000)

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

    # ------------------------------------------------------------------
    # Advanced pattern generation helpers

    def _set_season(self, season: str) -> None:
        self.season = season
        for s, btn in self.season_buttons.items():
            btn.setChecked(s == season)

    def _set_gender(self, gender: str) -> None:
        self.gender = gender
        for g, btn in self.gender_buttons.items():
            btn.setChecked(g == gender)

    def _set_age(self, age: str) -> None:
        self.age_group = age
        for a, btn in self.age_buttons.items():
            btn.setChecked(a == age)

    def _collect_settings(self) -> dict:
        return {
            "season": self.season,
            "demographics": {"age": self.age_group, "gender": self.gender},
            "complexity": self.complexity_slider.value() / 10.0,
            "start_date": date.today(),
        }

    def generate_similar_patterns_btn(self) -> None:
        from advanced_pattern_generator import AdvancedPatternGenerator

        generator = AdvancedPatternGenerator()
        base_pattern = [
            {"time": ev["time"].toPyTime(), "device": ev["device"], "value": ev["value"]}
            for ev in self.base_events
        ]
        self.generated_events = generator.generate_weekday_patterns(base_pattern, self._collect_settings())
        self.control_log.append("유사 생활패턴을 생성했습니다.")

    def generate_detailed_patterns_btn(self) -> None:
        self.generate_similar_patterns_btn()
        self.control_log.append("상세 설정을 적용했습니다.")

    def generate_ai_patterns_btn(self) -> None:
        from advanced_pattern_generator import AdvancedPatternGenerator

        generator = AdvancedPatternGenerator()
        self.generated_events = generator.ai_generate_realistic_pattern(self._collect_settings())
        self.control_log.append("AI 기반 패턴을 생성했습니다.")

    # ----- service -----

    def toggle_service(self) -> None:
        if self.service_running and not self.paused_for_chatbot:
            self.service_timer.stop()
            self.service_running = False
            self.play_btn.setText("Play and Record")
            self.step_mode = False
            self.play_btn.setEnabled(True)
            self.sim_end_time = None
            return

        if not self.loaded_events:
            self.load_csv()
        if not self.loaded_events:
            return
        # Prepare pattern detection map
        self.detected_patterns = analyze_pattern(self.loaded_events)
        self.sent_patterns: set[tuple[str, str]] = set()

        self.service_running = True
        self.step_mode = False
        self.paused_for_chatbot = False
        self.play_btn.setText("Pause")
        self.sim_time = self.loaded_events[0]["timestamp"]
        if self.duration_box.currentText() == "24h":
            self.sim_end_time = self.sim_time + timedelta(hours=24)
        else:
            self.sim_end_time = self.sim_time + timedelta(days=7)
        self.service_index = 0
        self.current_time_label.setText(self.sim_time.strftime("%Y-%m-%d %H:%M"))
        self.service_timer.start(1000)

    def step_service(self) -> None:
        if not self.service_running:
            if not self.loaded_events:
                self.load_csv()
            if not self.loaded_events:
                return
            self.detected_patterns = analyze_pattern(self.loaded_events)
            self.sent_patterns = set()
            self.service_running = True
            self.step_mode = True
            self.play_btn.setEnabled(False)
            self.paused_for_chatbot = False
            self.sim_time = self.loaded_events[0]["timestamp"]
            if self.duration_box.currentText() == "24h":
                self.sim_end_time = self.sim_time + timedelta(hours=24)
            else:
                self.sim_end_time = self.sim_time + timedelta(days=7)
            self.service_index = 0
            self.current_time_label.setText(self.sim_time.strftime("%Y-%m-%d %H:%M"))
        if self.paused_for_chatbot:
            return
        self.advance_service()

    def advance_service(self) -> None:
        if not self.service_running or self.sim_time is None or self.paused_for_chatbot:
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
        if self.sim_end_time and self.sim_time >= self.sim_end_time:
            # Restart the service from the beginning once the
            # simulation period is finished.
            self.toggle_service()  # stop the current run
            self.toggle_service()  # start a new run from the beginning

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
            # Send the notification to the chatbot's server running on port 7778
            send_message(
                f"패턴 감지: {device_name} {time_key} {value}", port=7778
            )
            self.sent_patterns.add((device_name, time_key))
            self.pending_event = event
            self.paused_for_chatbot = True
            self.service_timer.stop()

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
