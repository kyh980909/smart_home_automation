#!/usr/bin/env python3
"""
개선된 챗봇 실행 파일

스마트한 자연어 처리와 컨텍스트 인식 기능을 갖춘
개선된 챗봇을 실행합니다.
"""

import sys
from PyQt5.QtWidgets import QApplication
from enhanced_chatbot import SmartChatBot

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 개선된 스마트 챗봇 실행
    bot = SmartChatBot()
    bot.show()
    
    sys.exit(app.exec_())
