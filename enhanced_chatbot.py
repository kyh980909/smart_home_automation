"""
개선된 스마트홈 챗봇

자연스러운 대화형 인터페이스와 컨텍스트 기반 응답을 제공하는
스마트홈 제어 챗봇입니다.
"""

from __future__ import annotations

import sys
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QComboBox,
    QGroupBox,
    QGridLayout,
)
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QFont

import communication
from extended_devices import extended_devices, DeviceType


class SmartChatBot(QWidget):
    """개선된 스마트홈 챗봇 - 컨텍스트 인식 및 자연어 처리 지원"""

    message_received = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("스마트홈 AI 어시스턴트")
        self.resize(500, 600)
        self.history: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.last_pattern_info: Dict[str, Any] = {}
        
        self.message_received.connect(self.add_message)
        self._init_ui()
        self._init_conversation_patterns()
        
        # 소켓 서버 시작 (패널로부터 메시지 수신)
        communication.start_server(self.receive_message, port=7778)
        
        # 주기적으로 상태 업데이트
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # 5초마다

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # 상단 상태 표시
        status_group = QGroupBox("시스템 상태")
        status_layout = QGridLayout(status_group)
        
        self.connection_status = QLabel("🟢 패널 연결됨")
        self.time_label = QLabel(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.active_devices_label = QLabel("활성 디바이스: 0개")
        
        status_layout.addWidget(QLabel("연결 상태:"), 0, 0)
        status_layout.addWidget(self.connection_status, 0, 1)
        status_layout.addWidget(QLabel("현재 시간:"), 1, 0)
        status_layout.addWidget(self.time_label, 1, 1)
        status_layout.addWidget(QLabel("디바이스:"), 2, 0)
        status_layout.addWidget(self.active_devices_label, 2, 1)
        
        layout.addWidget(status_group)

        # 대화 영역
        chat_group = QGroupBox("대화")
        chat_layout = QVBoxLayout(chat_group)
        
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        
        # 폰트 설정으로 가독성 향상
        font = QFont()
        font.setPointSize(10)
        self.chat_area.setFont(font)
        
        chat_layout.addWidget(self.chat_area)
        layout.addWidget(chat_group)

        # 빠른 응답 버튼들
        quick_group = QGroupBox("빠른 응답")
        quick_layout = QGridLayout(quick_group)
        
        # 기본 응답
        yes_btn = QPushButton("✅ 네, 좋습니다")
        yes_btn.clicked.connect(lambda: self.quick_reply("네"))
        no_btn = QPushButton("❌ 아니요")
        no_btn.clicked.connect(lambda: self.quick_reply("아니요"))
        
        quick_layout.addWidget(yes_btn, 0, 0)
        quick_layout.addWidget(no_btn, 0, 1)
        
        # 디바이스 제어 빠른 버튼
        lights_on_btn = QPushButton("💡 모든 조명 켜기")
        lights_on_btn.clicked.connect(lambda: self.quick_reply("모든 조명 켜줘"))
        lights_off_btn = QPushButton("🌙 모든 조명 끄기")
        lights_off_btn.clicked.connect(lambda: self.quick_reply("모든 조명 꺼줘"))
        
        quick_layout.addWidget(lights_on_btn, 1, 0)
        quick_layout.addWidget(lights_off_btn, 1, 1)
        
        # 정보 요청 버튼
        status_btn = QPushButton("📊 디바이스 상태")
        status_btn.clicked.connect(lambda: self.quick_reply("디바이스 상태 알려줘"))
        help_btn = QPushButton("❓ 도움말")
        help_btn.clicked.connect(lambda: self.quick_reply("도움말"))
        
        quick_layout.addWidget(status_btn, 2, 0)
        quick_layout.addWidget(help_btn, 2, 1)
        
        layout.addWidget(quick_group)

        # 입력 영역
        input_group = QGroupBox("메시지 입력")
        input_layout = QVBoxLayout(input_group)
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("메시지를 입력하세요... (예: '거실 조명 켜줘', '에어컨 온도 24도로 설정')")
        self.input_line.returnPressed.connect(self.send_current)
        
        send_btn = QPushButton("📤 전송")
        send_btn.clicked.connect(self.send_current)
        
        input_btn_layout = QHBoxLayout()
        input_btn_layout.addWidget(self.input_line)
        input_btn_layout.addWidget(send_btn)
        
        input_layout.addLayout(input_btn_layout)
        layout.addWidget(input_group)
        
        # 환영 메시지
        self.add_bot_message("안녕하세요! 스마트홈 AI 어시스턴트입니다. 😊\\n\\n다음과 같은 명령을 사용할 수 있습니다:\\n• '거실 조명 켜줘/꺼줘'\\n• '에어컨 24도로 설정해줘'\\n• '디바이스 상태 알려줘'\\n• '모든 조명 꺼줘'\\n\\n무엇을 도와드릴까요?")

    def _init_conversation_patterns(self) -> None:
        """대화 패턴 초기화"""
        
        # 디바이스 제어 패턴
        self.control_patterns = {
            # 조명 제어
            r'(거실|주방|침실\d*|현관)?\s*(조명|불|전등)\s*(켜|켜줘|on)': 'light_on',
            r'(거실|주방|침실\d*|현관)?\s*(조명|불|전등)\s*(꺼|꺼줘|끄|끄어|off)': 'light_off',
            r'모든?\s*(조명|불|전등)\s*(켜|켜줘|on)': 'all_lights_on',
            r'모든?\s*(조명|불|전등)\s*(꺼|꺼줘|끄|끄어|off)': 'all_lights_off',
            
            # 에어컨 제어
            r'에어컨\s*(켜|켜줘|on)': 'aircon_on',
            r'에어컨\s*(꺼|꺼줘|끄|끄어|off)': 'aircon_off',
            r'에어컨\s*(\d+)도': 'aircon_temp',
            r'온도\s*(\d+)도': 'aircon_temp',
            
            # 기타 디바이스
            r'(가스|가스밸브)\s*(켜|켜줘|on)': 'gas_on',
            r'(가스|가스밸브)\s*(꺼|꺼줘|끄|끄어|off)': 'gas_off',
            r'(보일러)\s*(켜|켜줘|on)': 'boiler_on',
            r'(보일러)\s*(꺼|꺼줘|끄|끄어|off)': 'boiler_off',
            r'(cctv|씨씨티비|카메라)\s*(켜|켜줘|on)': 'cctv_on',
            r'(cctv|씨씨티비|카메라)\s*(꺼|꺼줘|끄|끄어|off)': 'cctv_off',
        }
        
        # 정보 요청 패턴
        self.info_patterns = {
            r'(상태|현황|정보)\s*(알려|보여|확인)': 'device_status',
            r'디바이스\s*(상태|현황|정보|목록)': 'device_status',
            r'뭐가?\s*(켜|on|꺼|off)': 'device_status',
            r'(도움말|help|명령어)': 'help',
            r'안녕|hi|hello|반가': 'greeting',
            r'고마|감사|thank': 'thanks',
        }
        
        # 응답 템플릿
        self.response_templates = {
            'light_on': "{room} 조명을 켰습니다. 💡",
            'light_off': "{room} 조명을 껐습니다. 🌙",
            'all_lights_on': "모든 조명을 켰습니다! ✨",
            'all_lights_off': "모든 조명을 껐습니다. 🌙💤",
            'aircon_on': "에어컨을 켰습니다. ❄️",
            'aircon_off': "에어컨을 껐습니다. 😌",
            'aircon_temp': "에어컨 온도를 {temp}도로 설정했습니다. 🌡️",
            'gas_on': "가스밸브를 열었습니다. ⚠️ 안전에 주의하세요!",
            'gas_off': "가스밸브를 닫았습니다. ✅",
            'boiler_on': "보일러를 켰습니다. 🔥",
            'boiler_off': "보일러를 껐습니다. 😌",
            'cctv_on': "CCTV를 켰습니다. 👁️ 보안 모드 활성화!",
            'cctv_off': "CCTV를 껐습니다. 😴",
            'device_status': "현재 디바이스 상태를 확인해드릴게요! 📊",
            'help': "💡 사용 가능한 명령어:\\n• '거실 조명 켜줘/꺼줘'\\n• '에어컨 24도로 설정'\\n• '모든 조명 꺼줘'\\n• '디바이스 상태 알려줘'\\n• '가스 켜줘/꺼줘'\\n• '보일러 켜줘/꺼줘'\\n• 'CCTV 켜줘/꺼줘'",
            'greeting': "안녕하세요! 😊 무엇을 도와드릴까요?",
            'thanks': "천만에요! 언제든 말씀하세요. 😊",
            'unknown': "죄송해요, 명령을 이해하지 못했어요. 🤔\\n'도움말'이라고 말씀해주시면 사용법을 알려드릴게요!"
        }

    def add_message(self, text: str) -> None:
        """메시지를 대화 기록에 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = {
            'timestamp': timestamp,
            'text': text,
            'type': 'received'
        }
        self.history.append(message)
        self._update_chat_display()

    def add_bot_message(self, text: str) -> None:
        """봇 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = {
            'timestamp': timestamp,
            'text': text,
            'type': 'bot'
        }
        self.history.append(message)
        self._update_chat_display()

    def add_user_message(self, text: str) -> None:
        """사용자 메시지 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = {
            'timestamp': timestamp,
            'text': text,
            'type': 'user'
        }
        self.history.append(message)
        self._update_chat_display()

    def _update_chat_display(self) -> None:
        """대화 화면 업데이트"""
        # 최근 30개 메시지만 유지
        self.history = self.history[-30:]
        
        chat_text = []
        for msg in self.history:
            if msg['type'] == 'bot':
                chat_text.append(f"[{msg['timestamp']}] 🤖 AI: {msg['text']}")
            elif msg['type'] == 'user':
                chat_text.append(f"[{msg['timestamp']}] 👤 사용자: {msg['text']}")
            else:
                chat_text.append(f"[{msg['timestamp']}] 📱 {msg['text']}")
        
        self.chat_area.setPlainText("\\n\\n".join(chat_text))
        # 자동 스크롤
        self.chat_area.moveCursor(self.chat_area.textCursor().End)

    def send_current(self) -> None:
        """현재 입력된 텍스트 전송"""
        text = self.input_line.text().strip()
        if not text:
            return
            
        self.add_user_message(text)
        self.process_user_input(text)
        self.input_line.clear()

    def quick_reply(self, text: str) -> None:
        """빠른 응답 버튼 처리"""
        self.input_line.setText(text)
        self.send_current()

    def process_user_input(self, text: str) -> None:
        """사용자 입력 처리 및 자연어 이해"""
        text_lower = text.lower()
        
        # 이전 패턴 감지 응답 처리
        if hasattr(self, 'waiting_for_response') and self.waiting_for_response:
            self._handle_pattern_response(text_lower)
            self.waiting_for_response = False
            return
        
        # 디바이스 제어 명령 처리
        command_processed = self._process_device_commands(text_lower)
        if command_processed:
            return
        
        # 정보 요청 처리
        info_processed = self._process_info_requests(text_lower)
        if info_processed:
            return
            
        # 이해하지 못한 명령
        self.add_bot_message(self.response_templates['unknown'])

    def _process_device_commands(self, text: str) -> bool:
        """디바이스 제어 명령 처리"""
        for pattern, command in self.control_patterns.items():
            match = re.search(pattern, text)
            if match:
                self._execute_device_command(command, match, text)
                return True
        return False

    def _process_info_requests(self, text: str) -> bool:
        """정보 요청 처리"""
        for pattern, info_type in self.info_patterns.items():
            if re.search(pattern, text):
                self._handle_info_request(info_type)
                return True
        return False

    def _execute_device_command(self, command: str, match: re.Match, original_text: str) -> None:
        """디바이스 명령 실행"""
        try:
            if command.startswith('light'):
                room = match.group(1) if match.groups() else None
                self._handle_light_command(command, room)
            elif command.startswith('aircon'):
                self._handle_aircon_command(command, match)
            elif command.startswith('all_lights'):
                self._handle_all_lights_command(command)
            else:
                self._handle_other_device_command(command)
            
            # 실제 디바이스 제어 명령을 패널로 전송
            communication.send_message(f"CONTROL:{command}:{original_text}")
            
        except Exception as e:
            self.add_bot_message(f"명령 실행 중 오류가 발생했습니다: {str(e)} 😅")

    def _handle_light_command(self, command: str, room: str) -> None:
        """조명 제어 처리"""
        if room:
            room_name = self._normalize_room_name(room)
            if command == 'light_on':
                self.add_bot_message(self.response_templates['light_on'].format(room=room_name))
            else:
                self.add_bot_message(self.response_templates['light_off'].format(room=room_name))
        else:
            if command == 'light_on':
                self.add_bot_message("어느 방의 조명을 켤까요? 🤔\\n(거실, 주방, 침실1, 침실2, 침실3, 현관)")
            else:
                self.add_bot_message("어느 방의 조명을 끌까요? 🤔\\n(거실, 주방, 침실1, 침실2, 침실3, 현관)")

    def _handle_aircon_command(self, command: str, match: re.Match) -> None:
        """에어컨 제어 처리"""
        if command == 'aircon_temp' and match.groups():
            temp = match.group(1)
            self.add_bot_message(self.response_templates['aircon_temp'].format(temp=temp))
        elif command == 'aircon_on':
            self.add_bot_message(self.response_templates['aircon_on'])
        elif command == 'aircon_off':
            self.add_bot_message(self.response_templates['aircon_off'])

    def _handle_all_lights_command(self, command: str) -> None:
        """모든 조명 제어 처리"""
        if command == 'all_lights_on':
            self.add_bot_message(self.response_templates['all_lights_on'])
        else:
            self.add_bot_message(self.response_templates['all_lights_off'])

    def _handle_other_device_command(self, command: str) -> None:
        """기타 디바이스 제어 처리"""
        if command in self.response_templates:
            self.add_bot_message(self.response_templates[command])

    def _handle_info_request(self, info_type: str) -> None:
        """정보 요청 처리"""
        if info_type == 'device_status':
            self._show_device_status()
        elif info_type in self.response_templates:
            self.add_bot_message(self.response_templates[info_type])

    def _show_device_status(self) -> None:
        """디바이스 상태 표시"""
        # 패널에 상태 요청
        communication.send_message("REQUEST_STATUS")
        self.add_bot_message(self.response_templates['device_status'])

    def _normalize_room_name(self, room: str) -> str:
        """방 이름 정규화"""
        room_mapping = {
            '거실': '거실',
            '주방': '주방', 
            '침실1': '침실1',
            '침실2': '침실2',
            '침실3': '침실3',
            '현관': '현관',
        }
        return room_mapping.get(room, room)

    def receive_message(self, message: str) -> None:
        """패널로부터 메시지 수신"""
        if message.startswith("패턴 감지:"):
            self._handle_pattern_detection(message)
        else:
            self.add_message(f"패널: {message}")

    def _handle_pattern_detection(self, message: str) -> None:
        """패턴 감지 메시지 처리"""
        # 패턴 정보 파싱
        try:
            parts = message.replace("패턴 감지: ", "").split(" ")
            device = parts[0]
            time = parts[1]
            action = parts[2]
            
            self.last_pattern_info = {
                'device': device,
                'time': time,
                'action': action
            }
            
            pattern_msg = f"🔍 패턴 감지: {device}을(를) 매일 {time}에 {action}하고 계시네요!\\n\\n자동화 규칙을 만들어 드릴까요? 🤖"
            self.add_bot_message(pattern_msg)
            self.waiting_for_response = True
            
        except Exception as e:
            self.add_bot_message(f"패턴 정보 처리 중 오류: {str(e)}")

    def _handle_pattern_response(self, response: str) -> None:
        """패턴 감지에 대한 사용자 응답 처리"""
        if response in ("네", "yes", "좋다", "그래", "응"):
            communication.send_message("CREATE_RULE")
            self.add_bot_message("✅ 자동화 규칙을 생성했습니다! 이제 설정된 시간에 자동으로 작동할 거예요. 😊")
        else:
            self.add_bot_message("👍 알겠습니다. 지금은 규칙을 만들지 않고 패턴만 기록해둘게요.")

    def update_status(self) -> None:
        """주기적 상태 업데이트"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)


class ChatBot(QWidget):
    """기존 호환성을 위한 기본 챗봇 클래스"""
    
    message_received = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.smart_bot = SmartChatBot()
        # 기존 인터페이스와의 호환성을 위해 시그널 연결
        self.message_received.connect(self.smart_bot.add_message)

    def show(self):
        self.smart_bot.show()

    def receive_message(self, message: str) -> None:
        self.smart_bot.receive_message(message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = SmartChatBot()
    bot.show()
    sys.exit(app.exec_())
