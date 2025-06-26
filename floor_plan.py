"""
스마트홈 평면도 관리 모듈 (확장 버전)

이 모듈은 스마트홈 디바이스들을 평면도 위에 시각적으로 표시하고 
상호작용할 수 있는 기능을 제공합니다. 다양한 디바이스 타입을 지원합니다.
"""

from dataclasses import dataclass
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QColor, QPixmap, QPainter, QFont
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsTextItem
from extended_devices import ExtendedPlanDevice, extended_devices, EXTENDED_COLOR_ON, EXTENDED_COLOR_OFF, DeviceType

# 평면도 화면 크기 설정
FLOOR_PLAN_WIDTH = 800   # 평면도 너비 (픽셀)
FLOOR_PLAN_HEIGHT = 600  # 평면도 높이 (픽셀)
DEVICE_ICON_SIZE = 45    # 디바이스 아이콘 크기 (픽셀)
CLICK_AREA_SIZE = 60     # 클릭 가능 영역 크기 (픽셀)


class ExtendedDeviceItem(QGraphicsEllipseItem):
    """
    평면도에 표시되는 개별 디바이스 아이콘 클래스 (확장 버전)
    마우스 클릭과 호버 이벤트를 처리하여 디바이스 상태를 제어
    """
    def __init__(self, device: ExtendedPlanDevice, callback=None):
        """
        디바이스 아이콘 초기화
        
        Args:
            device: ExtendedPlanDevice 객체
            callback: 디바이스 상태 변경 시 호출될 콜백 함수
        """
        super().__init__(-DEVICE_ICON_SIZE / 2, -DEVICE_ICON_SIZE / 2,
                         DEVICE_ICON_SIZE, DEVICE_ICON_SIZE)
        self.device = device
        self.callback = callback
        self.setAcceptHoverEvents(True)  # 마우스 호버 이벤트 활성화
        
        # 디바이스 이름 표시 텍스트 아이템
        self.text_item = QGraphicsTextItem(device.name, self)
        font = QFont()
        font.setPointSize(8)
        self.text_item.setFont(font)
        
        # 텍스트 위치 조정 (아이콘 아래쪽)
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(-text_rect.width()/2, DEVICE_ICON_SIZE/2 + 5)
        
        # 상태 정보 표시 텍스트 아이템
        self.status_item = QGraphicsTextItem("", self)
        status_font = QFont()
        status_font.setPointSize(6)
        self.status_item.setFont(status_font)
        
        self.update_display()

    def mousePressEvent(self, event):
        """
        마우스 클릭 시 디바이스 상태를 토글
        """
        self.device.state = not self.device.state  # 상태 반전
        self.update_display()  # 표시 업데이트
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

    def update_display(self):
        """
        디바이스 상태에 따라 아이콘 색상과 투명도, 상태 정보 업데이트
        """
        # 상태에 따라 색상 결정
        color = EXTENDED_COLOR_ON.get(self.device.type, QColor("#FFD700")) if self.device.state else EXTENDED_COLOR_OFF
        opacity = 1.0 if self.device.state else 0.5
        
        self.setBrush(color)  # 아이콘 색상 설정
        self.setOpacity(opacity)  # 투명도 설정
        
        # 상태 정보 업데이트
        status_text = self.device.get_status_text()
        self.status_item.setPlainText(status_text)
        
        # 상태 텍스트 위치 조정 (이름 아래)
        status_rect = self.status_item.boundingRect()
        self.status_item.setPos(-status_rect.width()/2, DEVICE_ICON_SIZE/2 + 20)
        
        # 상태에 따라 텍스트 색상 조정
        if self.device.state:
            self.text_item.setDefaultTextColor(QColor("#000000"))
            self.status_item.setDefaultTextColor(QColor("#333333"))
        else:
            self.text_item.setDefaultTextColor(QColor("#666666"))
            self.status_item.setDefaultTextColor(QColor("#999999"))


class ExtendedFloorPlanView(QGraphicsView):
    """
    확장된 스마트홈 평면도를 표시하는 메인 뷰
    다양한 디바이스 타입과 상태 정보를 표시
    """
    def __init__(self, devices=None, bg_path="assets/floorplan.png", callback=None, parent=None):
        """
        평면도 뷰 초기화
        
        Args:
            devices: 표시할 디바이스 목록 (기본값: extended_devices)
            bg_path: 배경 평면도 이미지 경로
            callback: 디바이스 상태 변경 콜백 함수
            parent: 부모 위젯
        """
        super().__init__(parent)
        
        if devices is None:
            devices = extended_devices
            
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
            item = ExtendedDeviceItem(d, callback)
            item.setPos(d.x, d.y)  # 디바이스 좌표에 배치
            scene.addItem(item)
            self.items.append(item)
        
        self.setScene(scene)
        self.setRenderHints(QPainter.Antialiasing)  # 안티앨리어싱 설정

    def refresh(self):
        """
        모든 디바이스 아이콘의 색상과 상태를 업데이트
        외부에서 디바이스 상태가 변경되었을 때 호출
        """
        for item in self.items:
            item.update_display()
    
    def get_device_by_name(self, name: str) -> ExtendedPlanDevice:
        """이름으로 디바이스 찾기"""
        for item in self.items:
            if item.device.name == name:
                return item.device
        return None
    
    def get_devices_by_type(self, device_type: DeviceType) -> list[ExtendedPlanDevice]:
        """타입으로 디바이스 목록 찾기"""
        return [item.device for item in self.items if item.device.type == device_type]


# 하위 호환성을 위한 기존 인터페이스 유지
@dataclass
class PlanDevice:
    """기존 PlanDevice 클래스 (하위 호환성용)"""
    id: int
    name: str
    type: str
    room: str
    x: int
    y: int
    state: bool = False


# 기존 devices 리스트 (하위 호환성용)
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

# 기존 색상 정의 (하위 호환성용)
COLOR_ON = {
    "light": QColor("#FFD700"),
    "aircon": QColor("#00CED1"),
    "gas": QColor("#FF4500"),
    "boiler": QColor("#DC143C"),
    "cctv": QColor("#32CD32"),
}
COLOR_OFF = QColor("#808080")


class DeviceItem(QGraphicsEllipseItem):
    """기존 DeviceItem 클래스 (하위 호환성용)"""
    def __init__(self, device: PlanDevice, callback=None):
        super().__init__(-DEVICE_ICON_SIZE / 2, -DEVICE_ICON_SIZE / 2,
                         DEVICE_ICON_SIZE, DEVICE_ICON_SIZE)
        self.device = device
        self.callback = callback
        self.setAcceptHoverEvents(True)
        self.update_color()

    def mousePressEvent(self, event):
        self.device.state = not self.device.state
        self.update_color()
        if self.callback:
            self.callback(self.device)
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event):
        self.setScale(1.1)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setScale(1.0)
        super().hoverLeaveEvent(event)

    def update_color(self):
        color = COLOR_ON.get(self.device.type, QColor("#FFD700")) if self.device.state else COLOR_OFF
        self.setBrush(color)
        self.setOpacity(1.0 if self.device.state else 0.5)


class FloorPlanView(QGraphicsView):
    """
    기존 스마트홈 평면도를 표시하는 메인 뷰 (하위 호환성용)
    """
    def __init__(self, devices, bg_path="assets/floorplan.png", callback=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setInteractive(True)
        
        scene = QGraphicsScene(0, 0, FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT)
        
        pix = QPixmap(bg_path)
        if not pix.isNull():
            pix = pix.scaled(FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scene.addPixmap(pix)
        
        self.items = []
        for d in devices:
            item = DeviceItem(d, callback)
            item.setPos(d.x, d.y)
            scene.addItem(item)
            self.items.append(item)
        
        self.setScene(scene)
        self.setRenderHints(QPainter.Antialiasing)

    def refresh(self):
        for item in self.items:
            item.update_color()
