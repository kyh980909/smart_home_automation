from __future__ import annotations

import sys
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


class ChatBot(QWidget):
    """Simple chatbot interface that sends messages to the main panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChatBot")
        self.resize(400, 300)
        self._init_ui()

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

    def send_current(self) -> None:
        text = self.input_line.text().strip()
        if not text:
            return
        self.chat_area.append(f"사용자: {text}")
        communication.send_message(text)
        self.input_line.clear()

    def quick_reply(self, text: str) -> None:
        self.input_line.setText(text)
        self.send_current()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bot = ChatBot()
    bot.show()
    sys.exit(app.exec_())
