from __future__ import annotations

import sys
from typing import List
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import communication

# Pre-defined templates for recommendations sent to the user
recommendation_templates = {
    "pattern": "{device}을(를) 매일 {time}에 {action}하고 계십니다. 자동화하시겠습니까?",
    "abnormal": "평소와 다르게 {time}에 {device}을(를) 사용하셨네요. 괜찮으신가요?",
    "energy": "외출 시 모든 기기를 자동으로 끄도록 설정하시겠습니까?",
}


class ChatBot(QWidget):
    """Simple chatbot interface that sends messages to the main panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChatBot")
        self.resize(400, 300)
        self.history: List[str] = []
        self._init_ui()
        # Start socket server to receive messages from the panel
        communication.start_server(self.receive_message)

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        layout.addWidget(self.chat_area)

        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.send_current)
        layout.addWidget(self.input_line)

        btn_layout = QHBoxLayout()
        yes_btn = QPushButton("Yes")
        yes_btn.clicked.connect(lambda: self.quick_reply("Yes"))
        no_btn = QPushButton("No")
        no_btn.clicked.connect(lambda: self.quick_reply("No"))
        btn_layout.addWidget(yes_btn)
        btn_layout.addWidget(no_btn)
        layout.addLayout(btn_layout)

    def add_message(self, text: str) -> None:
        """Append ``text`` to the chat history and update the chat area."""

        self.history.append(text)
        # Keep only the last 20 messages
        self.history = self.history[-20:]
        self.chat_area.setPlainText("\n".join(self.history))

    def send_current(self) -> None:
        text = self.input_line.text().strip()
        if not text:
            return
        self.add_message(f"사용자: {text}")
        self.handle_response(text)
        communication.send_message(text)
        self.input_line.clear()

    def quick_reply(self, text: str) -> None:
        self.input_line.setText(text)
        self.send_current()

    def handle_response(self, text: str) -> None:
        """Process the user's response and react accordingly."""

        lower = text.lower()
        if lower in ("네", "yes"):
            # Send a rule creation command to the main panel
            communication.send_message("CREATE_RULE")
            self.add_message("챗봇: 규칙을 생성하겠습니다.")
        elif lower in ("아니오", "no"):
            # Just acknowledge the response
            self.add_message("챗봇: 알겠습니다. 기록만 저장합니다.")
        else:
            # Store arbitrary feedback
            self.add_message("챗봇: 감사합니다.")

    def receive_message(self, message: str) -> None:
        """Handle a message received from the main panel."""

        self.add_message(f"패널: {message}")

    def show_recommendation(self, template: str, **kwargs: str) -> None:
        """Display a formatted recommendation message to the user."""

        msg_tmpl = recommendation_templates.get(template)
        if msg_tmpl:
            self.add_message("챗봇: " + msg_tmpl.format(**kwargs))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = ChatBot()
    bot.show()
    sys.exit(app.exec_())
