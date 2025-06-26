#!/usr/bin/env python3
"""
개선된 메인 패널 실행 파일

기존 5개 디바이스 + 시계열 그래프 기능을 지원하는
개선된 스마트홈 패널을 실행합니다.
"""

import sys
from PyQt5.QtWidgets import QApplication
from main_panel import MainPanel

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 기존 디바이스를 사용하는 패널 실행 (확장 기능 지원)
    panel = MainPanel(use_extended_devices=True)
    panel.setWindowTitle("스마트홈 패널 (개선 버전) - 그래프 지원")
    panel.show()
    
    sys.exit(app.exec_())
