"""
스마트홈 평면도 관리 모듈

이 모듈은 스마트홈 디바이스들을 평면도 위에 시각적으로 표시하고 
상호작용할 수 있는 기능을 제공합니다.
"""

from dataclasses import dataclass
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QColor, QPixmap, QPainter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem

# 평면도 화면 크기 설정
FLOOR_PLAN_WIDTH = 800   # 평면도 너비 (픽셀)
FLOOR_PLAN_HEIGHT = 600  # 평면도 높이 (픽셀)
DEVICE_ICON_SIZE = 45    # 디바이스 아이콘 크기 (픽셀)
CLICK_AREA_SIZE = 60     # 클릭 가능 영역 크기 (픽셀)

@dataclass
class PlanDevice:
    """
    평면도에 표시될 디바이스 정보를 저장하는 데이터 클래스
    """
    id: int           # 디바이스 고유 ID
    name: str         # 디바이스 이름 (예: "거실 조명")
    type: str         # 디바이스 타입 (light, aircon, gas, boiler, cctv)
    room: str         # 설치된 방 이름
    x: int            # 평면도상 X 좌표
    y: int            # 평면도상 Y 좌표
    state: bool = False  # 디바이스 상태 (True: 켜짐, False: 꺼짐)

# 스마트홈 디바이스 목록 정의
# 각 디바이스의 위치와 정보를 설정 (800x600 크기에 맞게 조정)
devices = [
    PlanDevice(1, "거실 조명", "light", "거실", 420, 460),
    PlanDevice(2, "주방 조명", "light", "주방", 375, 220),
    PlanDevice(3, "침실1 조명", "light", "침실1", 720, 430),
    PlanDevice(4, "침실2 조명", "light", "침실2", 270, 430),
    PlanDevice(5, "침실3 조명", "light", "침실3", 40, 340),
    PlanDevice(6, "현관 조명", "light", "현관", 180, 210),
    PlanDevice(7, "에어컨", "aircon", "거실", 450, 350),
    PlanDevice(8, "가스밸브", "gas", "주방", 420, 145),
    PlanDevice(9, "보일러", "boiler", "발코니", 580, 205),
    PlanDevice(10, "CCTV", "cctv", "현관", 180, 135),
]

# 디바이스 타입별 색상 정의 (켜진 상태)
COLOR_ON = {
    "light": QColor("#FFD700"),    # 조명: 금색
    "aircon": QColor("#00CED1"),   # 에어컨: 청록색
    "gas": QColor("#FF4500"),      # 가스: 주황색
    "boiler": QColor("#DC143C"),   # 보일러: 빨간색
    "cctv": QColor("#32CD32"),     # CCTV: 녹색
}
COLOR_OFF = QColor("#808080")     # 모든 디바이스 꺼진 상태: 회색

class DeviceItem(QGraphicsEllipseItem):
    """
    평면도에 표시되는 개별 디바이스 아이콘 클래스
    마우스 클릭과 호버 이벤트를 처리하여 디바이스 상태를 제어
    """
    def __init__(self, device: PlanDevice, callback=None):
        """
        디바이스 아이콘 초기화
        
        Args:
            device: PlanDevice 객체
            callback: 디바쓬이스 상태 변경 시 호출될 콜백 함수
        """
        super().__init__(-DEVICE_ICON_SIZE / 2, -DEVICE_ICON_SIZE / 2,
                         DEVICE_ICON_SIZE, DEVICE_ICON_SIZE)
        self.device = device
        self.callback = callback
        self.setAcceptHoverEvents(True)  # 마우스 호버 이벤트 활성화
        self.update_color()

    def mousePressEvent(self, event):
        """
        마우스 클릭 시 디바이스 상태를 토글
        """
        self.device.state = not self.device.state  # 상태 반전
        self.update_color()  # 색상 업데이트
        if self.callback:
            self.callback(self.device)  # 콜백 함수 호출
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        """
        마우스 호버 시 아이콘 크기 확대
        """
        self.setScale(1.1)  # 10% 크기 확대
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """
        마우스 호버 종료 시 아이콘 크기 원복
        """
        self.setScale(1.0)  # 원래 크기로 복귀
        super().hoverLeaveEvent(event)

    def update_color(self):
        """
        디바이스 상태에 따라 아이콘 색상과 투명도 업데이트
        """
        # 상태에 따라 색상 결정
        color = COLOR_ON.get(self.device.type, QColor("#FFD700")) if self.device.state else COLOR_OFF
        self.setBrush(color)  # 아이콘 색상 설정
        self.setOpacity(1.0 if self.device.state else 0.5)  # 투명도 설정

class FloorPlanView(QGraphicsView):
    """
    스마트홈 평면도를 표시하는 메인 빠
    배경 이미지와 디바이스 아이콘들을 관리
    """
    def __init__(self, devices, bg_path="assets/floorplan.png", callback=None, parent=None):
        """
        평면도 빠 초기화
        
        Args:
            devices: 표시할 디바이스 목록
            bg_path: 배경 평면도 이미지 경로
            callback: 디바이스 상태 변경 콜백 함수
            parent: 부모 위젯
        """
        super().__init__(parent)
        # 평면도 크기 고정
        self.setFixedSize(FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT)
        
        # 스크롤바 비활성화
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 스크롤 및 드래그 비활성화
        self.setDragMode(QGraphicsView.NoDrag)
        self.setInteractive(True)  # 디바이스 클릭은 활성화
        
        # 그래픽스 씨 생성
        scene = QGraphicsScene(0, 0, FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT)
        
        # 배경 이미지 로드 및 설정
        pix = QPixmap(bg_path)
        if not pix.isNull():
            # 이미지를 평면도 크기에 맞게 스케일링
            pix = pix.scaled(FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scene.addPixmap(pix)
        
        # 디바이스 아이콘들 생성 및 배치
        self.items = []
        for d in devices:
            item = DeviceItem(d, callback)
            item.setPos(d.x, d.y)  # 디바이스 좌표에 배치
            scene.addItem(item)
            self.items.append(item)
        
        self.setScene(scene)
        self.setRenderHints(QPainter.Antialiasing)  # 안티앨리어싱 설정

    def refresh(self):
        """
        모든 디바이스 아이콘의 색상을 업데이트
        외부에서 디바이스 상태가 변경되었을 때 호출
        """
        for item in self.items:
            item.update_color()
