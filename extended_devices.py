"""
확장된 디바이스 타입 정의 (기존 디바이스만)

기존 5개 디바이스 타입만 지원하며, 향후 확장성을 위한 구조를 제공합니다.
"""

from dataclasses import dataclass
from typing import Union, Dict, Any
from enum import Enum


class DeviceType(Enum):
    """디바이스 타입 열거형 (기존 디바이스만)"""
    LIGHT = "light"           # 조명
    AIRCON = "aircon"         # 에어컨
    GAS = "gas"               # 가스밸브
    BOILER = "boiler"         # 보일러
    CCTV = "cctv"             # CCTV


@dataclass
class ExtendedPlanDevice:
    """
    확장된 평면도 디바이스 클래스
    기존 디바이스 타입과 추가 속성을 지원
    """
    id: int                              # 디바이스 고유 ID
    name: str                            # 디바이스 이름
    type: DeviceType                     # 디바이스 타입
    room: str                            # 설치된 방 이름
    x: int                              # 평면도상 X 좌표
    y: int                              # 평면도상 Y 좌표
    state: bool = False                 # 기본 ON/OFF 상태
    properties: Dict[str, Any] = None   # 추가 속성들
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
    
    @property
    def temperature(self) -> float:
        """온도 속성 (에어컨, 보일러 등)"""
        return self.properties.get('temperature', 22.0)
    
    @temperature.setter
    def temperature(self, value: float):
        self.properties['temperature'] = value
    
    @property
    def brightness(self) -> int:
        """밝기 속성 (조명)"""
        return self.properties.get('brightness', 100)
    
    @brightness.setter
    def brightness(self, value: int):
        self.properties['brightness'] = max(0, min(100, value))
    
    def get_status_text(self) -> str:
        """디바이스 상태를 텍스트로 반환"""
        base_status = "ON" if self.state else "OFF"
        
        if self.type == DeviceType.LIGHT and self.state:
            return f"{base_status} ({self.brightness}%)"
        elif self.type == DeviceType.AIRCON and self.state:
            return f"{base_status} ({self.temperature}°C)"
        else:
            return base_status


# 스마트홈 디바이스 목록 (기존 디바이스만, 좌표 변경 금지)
extended_devices = [
    ExtendedPlanDevice(1, "거실 조명", DeviceType.LIGHT, "거실", 520, 360),
    ExtendedPlanDevice(2, "주방 조명", DeviceType.LIGHT, "주방", 520, 180),
    ExtendedPlanDevice(3, "침실1 조명", DeviceType.LIGHT, "침실1", 680, 490),
    ExtendedPlanDevice(4, "침실2 조명", DeviceType.LIGHT, "침실2", 190, 490),
    ExtendedPlanDevice(5, "침실3 조명", DeviceType.LIGHT, "침실3", 190, 300),
    ExtendedPlanDevice(6, "현관 조명", DeviceType.LIGHT, "현관", 240, 360),
    ExtendedPlanDevice(7, "에어컨", DeviceType.AIRCON, "거실", 600, 360),
    ExtendedPlanDevice(8, "가스밸브", DeviceType.GAS, "주방", 460, 145),
    ExtendedPlanDevice(9, "보일러", DeviceType.BOILER, "발코니", 660, 240),
    ExtendedPlanDevice(10, "CCTV", DeviceType.CCTV, "현관", 290, 360),
]


# 디바이스 타입별 색상 정의
EXTENDED_COLOR_ON = {
    DeviceType.LIGHT: "#FFD700",           # 조명: 금색
    DeviceType.AIRCON: "#00CED1",          # 에어컨: 청록색
    DeviceType.GAS: "#FF4500",             # 가스: 주황색
    DeviceType.BOILER: "#DC143C",          # 보일러: 빨간색
    DeviceType.CCTV: "#32CD32",            # CCTV: 녹색
}

EXTENDED_COLOR_OFF = "#808080"  # 모든 디바이스 꺼진 상태: 회색


def get_device_by_id(device_id: int) -> Union[ExtendedPlanDevice, None]:
    """ID로 디바이스 찾기"""
    for device in extended_devices:
        if device.id == device_id:
            return device
    return None


def get_devices_by_type(device_type: DeviceType) -> list[ExtendedPlanDevice]:
    """타입으로 디바이스 목록 찾기"""
    return [device for device in extended_devices if device.type == device_type]


def get_devices_by_room(room: str) -> list[ExtendedPlanDevice]:
    """방 이름으로 디바이스 목록 찾기"""
    return [device for device in extended_devices if device.room == room]


# 디바이스 제어 명령어 정의
class DeviceCommand:
    """디바이스 제어 명령어 클래스"""
    
    @staticmethod
    def turn_on(device: ExtendedPlanDevice):
        """디바이스 켜기"""
        device.state = True
    
    @staticmethod
    def turn_off(device: ExtendedPlanDevice):
        """디바이스 끄기"""
        device.state = False
    
    @staticmethod
    def set_brightness(device: ExtendedPlanDevice, brightness: int):
        """조명 밝기 설정"""
        if device.type == DeviceType.LIGHT:
            device.brightness = brightness
            device.state = brightness > 0
    
    @staticmethod
    def set_temperature(device: ExtendedPlanDevice, temperature: float):
        """온도 설정"""
        if device.type in [DeviceType.AIRCON, DeviceType.BOILER]:
            device.temperature = temperature


if __name__ == "__main__":
    # 테스트 코드
    print("=== 기존 디바이스 목록 ===")
    for device in extended_devices:
        print(f"{device.id}: {device.name} ({device.type.value}) - {device.get_status_text()}")
    
    print("\\n=== 조명 제어 테스트 ===")
    light = get_device_by_id(1)
    if light:
        print(f"초기 상태: {light.get_status_text()}")
        DeviceCommand.set_brightness(light, 50)
        print(f"50% 밝기 설정 후: {light.get_status_text()}")
    
    print("\\n=== 에어컨 제어 테스트 ===")
    aircon = get_device_by_id(7)
    if aircon:
        print(f"초기 상태: {aircon.get_status_text()}")
        DeviceCommand.turn_on(aircon)
        DeviceCommand.set_temperature(aircon, 24.0)
        print(f"24도 설정 후: {aircon.get_status_text()}")
