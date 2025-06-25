from dataclasses import dataclass
from PyQt5.QtCore import Qt, QPropertyAnimation
from PyQt5.QtGui import QColor, QPixmap, QPainter
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsEllipseItem

FLOOR_PLAN_WIDTH = 900
FLOOR_PLAN_HEIGHT = 600
DEVICE_ICON_SIZE = 45
CLICK_AREA_SIZE = 60

@dataclass
class PlanDevice:
    id: int
    name: str
    type: str
    room: str
    x: int
    y: int
    state: bool = False

devices = [
    PlanDevice(1, "거실 조명", "light", "거실", 400, 300),
    PlanDevice(2, "주방 조명", "light", "주방", 400, 150),
    PlanDevice(3, "침실1 조명", "light", "침실1", 650, 420),
    PlanDevice(4, "침실2 조명", "light", "침실2", 180, 420),
    PlanDevice(5, "침실3 조명", "light", "침실3", 180, 250),
    PlanDevice(6, "현관 조명", "light", "현관", 230, 300),
    PlanDevice(7, "에어컨", "aircon", "거실", 500, 300),
    PlanDevice(8, "가스밸브", "gas", "주방", 350, 120),
    PlanDevice(9, "보일러", "boiler", "발코니", 550, 200),
    PlanDevice(10, "CCTV", "cctv", "현관", 280, 300),
]

COLOR_ON = {
    "light": QColor("#FFD700"),
    "aircon": QColor("#00CED1"),
    "gas": QColor("#FF4500"),
    "boiler": QColor("#DC143C"),
    "cctv": QColor("#32CD32"),
}
COLOR_OFF = QColor("#808080")

class DeviceItem(QGraphicsEllipseItem):
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
    def __init__(self, devices, bg_path="assets/floorplan.png", callback=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(FLOOR_PLAN_WIDTH, FLOOR_PLAN_HEIGHT)
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
