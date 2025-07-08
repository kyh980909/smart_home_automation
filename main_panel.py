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
    QScrollArea,
)

from datetime import datetime, date, timedelta

from typing import Any, Optional

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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(central)
        self.setCentralWidget(scroll)
        
        # 메인 레이아웃: 상하 분할
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
    
        # == 상단: 탭바만 표시 ==
        self.tab_bar = QTabWidget()
        self.tab_bar.setTabsClosable(False)

        # 탭 생성 (내용은 비어있는 위젯으로)
        self.tab_widgets = {}
        tab_names = ["학습데이터 생성", "학습", "서비스", "조회", "패턴결과", "환경설정"]
        
        for name in tab_names:
            tab_widget = QWidget()
            self.tab_bar.addTab(tab_widget, name)
            self.tab_widgets[name] = tab_widget

        # 탭 변경 이벤트 연결
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tab_bar, 0)

        # == 하단: 좌우 분할 ==
        bottom_layout = QHBoxLayout()

        # 왼쪽: 평면도 뷰
        if self.use_extended_devices:
            self.floor_view = ExtendedFloorPlanView(extended_devices, callback=self.device_clicked)
        else:
            self.floor_view = FloorPlanView(devices, callback=self.device_clicked)
        
        # 평면도 크기 제한 및 비율 조정
        self.floor_view.setMinimumWidth(300)
        bottom_layout.addWidget(self.floor_view, 3)  # 평면도: 3

        # 오른쪽: 탭 내용 영역
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_area.setMinimumWidth(500)  # 최소 너비 보장

        # 시계와 로그를 기본으로 표시
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.clock_label)
        
        # 타이머 설정
        timer = QTimer(self)
        timer.timeout.connect(self.update_clock)
        timer.start(1000)
        self.update_clock()
        
        # 로그 창
        self.control_log = QTextEdit()
        self.control_log.setReadOnly(True)
        self.control_log.setMaximumHeight(150)  # 로그 창 높이 제한
        self.content_layout.addWidget(self.control_log)
        
        bottom_layout.addWidget(self.content_area, 2)  # 컨텐츠: 2 (3:2 비율)
        
        # 하단 레이아웃을 메인에 추가
        bottom_widget = QWidget()
        bottom_widget.setLayout(bottom_layout)
        main_layout.addWidget(bottom_widget, 1)  # 1: 확장 가능
        
        # 탭별 내용 초기화
        self._init_all_tabs()
        
        # 첫 번째 탭 선택
        self.tab_bar.setCurrentIndex(0)
        self.on_tab_changed(0)

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


    def on_tab_changed(self, index):
        """탭이 변경될 때 오른쪽 내용 영역 업데이트"""
        # 기존 내용 제거 (시계와 로그 제외하고)
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                # 시계와 로그는 유지
                if widget not in [self.clock_label, self.control_log]:
                    widget.setParent(None)
        
        # 선택된 탭의 내용 추가
        tab_name = self.tab_bar.tabText(index)
        
        if tab_name == "학습데이터 생성":
            self._add_data_tab_content()
        elif tab_name == "학습":
            self._add_learning_tab_content()
        elif tab_name == "서비스":
            self._add_service_tab_content()
        elif tab_name == "조회":
            self._add_query_tab_content()
        elif tab_name == "패턴결과":
            self._add_graph_tab_content()
        elif tab_name == "환경설정":
            self._add_settings_tab_content()

    def _add_data_tab_content(self):
        """학습데이터 생성 탭 내용을 오른쪽 영역에 추가"""
        # 시계 위에 데이터 생성 관련 위젯들 추가
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        # 폼 레이아웃
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # 디바이스, 시간, 액션 선택
        controls_layout = QHBoxLayout()
        
        self.data_device = QComboBox()
        for d in devices:
            self.data_device.addItem(d.name)
        controls_layout.addWidget(QLabel("디바이스:"))
        controls_layout.addWidget(self.data_device)
        
        self.data_time = QTimeEdit(QTime.currentTime())
        self.data_time.setDisplayFormat("HH:mm")
        controls_layout.addWidget(QLabel("시간:"))
        controls_layout.addWidget(self.data_time)
        
        self.data_action = QComboBox()
        self.data_action.addItems(["ON", "OFF"])
        controls_layout.addWidget(QLabel("동작:"))
        controls_layout.addWidget(self.data_action)
        
        add_btn = QPushButton("패턴 추가")
        add_btn.clicked.connect(self.add_pattern)
        controls_layout.addWidget(add_btn)
        
        form_layout.addLayout(controls_layout)
        
        # 패턴 리스트
        self.pattern_list = QListWidget()
        form_layout.addWidget(self.pattern_list)
        
        # 생성 버튼들
        btn_layout = QHBoxLayout()
        gen_btn = QPushButton("일주일치 생성")
        gen_btn.clicked.connect(self.generate_week)
        btn_layout.addWidget(gen_btn)
        
        save_btn = QPushButton("CSV 저장")
        save_btn.clicked.connect(self.save_csv)
        btn_layout.addWidget(save_btn)
        
        form_layout.addLayout(btn_layout)
        
        # 상세 설정 추가
        self._add_advanced_controls(form_layout)
        
        self.content_layout.insertWidget(insert_index, form_widget)

    def _add_learning_tab_content(self):
        """학습 탭 내용 추가"""
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        learning_widget = QWidget()
        learning_layout = QVBoxLayout(learning_widget)
        
        # 버튼들
        load_btn = QPushButton("데이터 불러오기")
        load_btn.clicked.connect(self.load_csv)
        learning_layout.addWidget(load_btn)
        
        analyze_btn = QPushButton("패턴 분석 시작")
        analyze_btn.clicked.connect(self.run_analysis)
        learning_layout.addWidget(analyze_btn)
        
        # 분석 결과
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        learning_layout.addWidget(self.analysis_text, 1)
        
        self.content_layout.insertWidget(insert_index, learning_widget)

    def _add_service_tab_content(self):
        """서비스 탭 내용 추가"""
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        service_widget = QWidget()
        service_layout = QVBoxLayout(service_widget)
        
        # 컨트롤 버튼들
        top_controls = QHBoxLayout()
        
        self.play_btn = QPushButton("Play and Record")
        self.play_btn.clicked.connect(self.toggle_service)
        top_controls.addWidget(self.play_btn)
        
        self.step_btn = QPushButton("Play by Tap and Record")
        self.step_btn.clicked.connect(self.step_service)
        top_controls.addWidget(self.step_btn)
        
        self.speed_box = QComboBox()
        self.speed_box.addItems(["1x", "10x", "60x"])
        top_controls.addWidget(QLabel("속도:"))
        top_controls.addWidget(self.speed_box)
        
        self.duration_box = QComboBox()
        self.duration_box.addItems(["24h", "1w"])
        top_controls.addWidget(QLabel("기간:"))
        top_controls.addWidget(self.duration_box)
        
        self.current_time_label = QLabel("--:--")
        top_controls.addWidget(QLabel("현재시간:"))
        top_controls.addWidget(self.current_time_label)
        
        service_layout.addLayout(top_controls)
        
        # 서비스 로그
        self.service_log = QTextEdit()
        self.service_log.setReadOnly(True)
        service_layout.addWidget(self.service_log, 1)
        
        self.content_layout.insertWidget(insert_index, service_widget)

    def _add_query_tab_content(self):
        """조회 탭 내용 추가"""
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        query_widget = QWidget()
        query_layout = QVBoxLayout(query_widget)
        
        # 달력
        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_query)
        query_layout.addWidget(self.calendar)
        
        # 테이블
        self.query_table = QTableWidget(0, 4)
        self.query_table.setHorizontalHeaderLabels(["시간", "디바이스", "동작", "값"])
        query_layout.addWidget(self.query_table, 1)
        
        self.content_layout.insertWidget(insert_index, query_widget)

    def _add_graph_tab_content(self):
        """패턴결과 탭 내용 추가"""
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        # 그래프 컨트롤
        control_layout = QHBoxLayout()
        
        self.graph_device_combo = QComboBox()
        self.graph_device_combo.addItem("전체 디바이스")
        for d in devices:
            self.graph_device_combo.addItem(d.name)
        control_layout.addWidget(QLabel("디바이스:"))
        control_layout.addWidget(self.graph_device_combo)
        
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["사용 패턴", "일일 요약"])
        control_layout.addWidget(QLabel("그래프 타입:"))
        control_layout.addWidget(self.graph_type_combo)
        
        refresh_btn = QPushButton("새로고침")
        refresh_btn.clicked.connect(self.refresh_graph)
        control_layout.addWidget(refresh_btn)
        
        sample_btn = QPushButton("샘플 보기")
        sample_btn.clicked.connect(self.show_sample_graph)
        control_layout.addWidget(sample_btn)
        
        graph_layout.addLayout(control_layout)
        
        # 그래프 위젯
        self.time_series_chart = TimeSeriesChart(parent=graph_widget, width=12, height=8)
        graph_layout.addWidget(self.time_series_chart)
        
        self.content_layout.insertWidget(insert_index, graph_widget)

    def _add_settings_tab_content(self):
        """환경설정 탭 내용 추가"""
        insert_index = self.content_layout.indexOf(self.clock_label)
        
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # 민감도 설정
        self.sensitivity_spin = QSpinBox()
        self.sensitivity_spin.setRange(1, 10)
        self.sensitivity_spin.setValue(3)
        settings_layout.addWidget(QLabel("패턴 감지 민감도"))
        settings_layout.addWidget(self.sensitivity_spin)
        
        # 알림 설정
        self.chat_notify = QCheckBox("Chatbot 알림")
        self.chat_notify.setChecked(True)
        settings_layout.addWidget(self.chat_notify)
        
        # 여백 추가
        settings_layout.addStretch()
        
        self.content_layout.insertWidget(insert_index, settings_widget)

    def _add_advanced_controls(self, parent_layout):
        """상세 설정 컨트롤들 추가"""
        adv_box = QGroupBox("상세 설정")
        adv_layout = QVBoxLayout(adv_box)

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

        self.complexity_slider = QSlider(Qt.Horizontal)
        self.complexity_slider.setMinimum(1)
        self.complexity_slider.setMaximum(10)
        self.complexity_slider.setValue(5)
        adv_layout.addWidget(QLabel("패턴 복잡도"))
        adv_layout.addWidget(self.complexity_slider)

        parent_layout.addWidget(adv_box)

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

        parent_layout.addLayout(adv_btns)

    def _init_all_tabs(self):
        """모든 탭 관련 변수 초기화"""
        # 서비스 관련
        self.service_timer = QTimer(self)
        self.service_timer.timeout.connect(self.advance_service)
        self.service_running = False
        self.step_mode = False
        self.paused_for_chatbot = False
        self.pending_event: Optional[dict] = None
        self.sim_time: Optional[datetime] = None
        self.sim_end_time: Optional[datetime] = None
        self.service_index = 0
        
        # 데이터 관련
        self.base_events: list[dict[str, Any]] = []
        self.generated_events: list[dict[str, Any]] = []
        self.loaded_events: list[dict[str, Any]] = []
        
        # 고급 설정
        self.season = "봄"
        self.gender = "M"
        self.age_group = "장년"
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
