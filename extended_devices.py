"""
확장된 디바이스 타입 정의

기존 조명, 에어컨 외에 TV, 냉장고, 센서 등 다양한 스마트홈 디바이스를 지원합니다.
"""

from dataclasses import dataclass
from typing import Union, Dict, Any
from enum import Enum


class DeviceType(Enum):
    """디바이스 타입 열거형"""
    LIGHT = "light"           # 조명
    AIRCON = "aircon"         # 에어컨
    GAS = "gas"               # 가스밸브
    BOILER = "boiler"         # 보일러
    CCTV = "cctv"             # CCTV
    TV = "tv"                 # TV
    REFRIGERATOR = "fridge"   # 냉장고
    TEMPERATURE_SENSOR = "temp_sensor"    # 온도 센서
    HUMIDITY_SENSOR = "humid_sensor"      # 습도 센서
    MOTION_SENSOR = "motion_sensor"       # 동작 감지 센서
    DOOR_SENSOR = "door_sensor"           # 문 센서
    WINDOW = "window"         # 창문/블라인드
    SECURITY_SYSTEM = "security"          # 보안 시스템


@dataclass
class ExtendedPlanDevice:
    """
    확장된 평면도 디바이스 클래스
    더 다양한 디바이스 타입과 속성을 지원
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
        """온도 속성 (온도 센서, 에어컨, 냉장고 등)"""
        return self.properties.get('temperature', 22.0)
    
    @temperature.setter
    def temperature(self, value: float):
        self.properties['temperature'] = value
    
    @property
    def humidity(self) -> float:
        """습도 속성 (습도 센서 등)"""
        return self.properties.get('humidity', 50.0)
    
    @humidity.setter  
    def humidity(self, value: float):
        self.properties['humidity'] = value
    
    @property
    def brightness(self) -> int:
        """밝기 속성 (조명 등)"""
        return self.properties.get('brightness', 100)
    
    @brightness.setter
    def brightness(self, value: int):
        self.properties['brightness'] = max(0, min(100, value))
    
    @property
    def volume(self) -> int:
        """볼륨 속성 (TV 등)"""
        return self.properties.get('volume', 50)
    
    @volume.setter
    def volume(self, value: int):
        self.properties['volume'] = max(0, min(100, value))
    
    @property
    def channel(self) -> int:
        """채널 속성 (TV)"""
        return self.properties.get('channel', 1)
    
    @channel.setter
    def channel(self, value: int):
        self.properties['channel'] = max(1, value)
    
    @property
    def motion_detected(self) -> bool:
        """동작 감지 속성 (동작 센서)"""
        return self.properties.get('motion_detected', False)
    
    @motion_detected.setter
    def motion_detected(self, value: bool):
        self.properties['motion_detected'] = value
    
    @property
    def door_open(self) -> bool:
        """문 열림 상태 (문 센서)"""
        return self.properties.get('door_open', False)
    
    @door_open.setter
    def door_open(self, value: bool):
        self.properties['door_open'] = value
    
    def get_status_text(self) -> str:
        """디바이스 상태를 텍스트로 반환"""
        base_status = "ON" if self.state else "OFF"
        
        if self.type == DeviceType.LIGHT and self.state:
            return f"{base_status} ({self.brightness}%)"
        elif self.type == DeviceType.TV and self.state:
            return f"{base_status} (CH{self.channel}, Vol{self.volume})"
        elif self.type == DeviceType.AIRCON and self.state:
            return f"{base_status} ({self.temperature}°C)"
        elif self.type == DeviceType.REFRIGERATOR:
            return f"운영중 ({self.temperature}°C)"
        elif self.type == DeviceType.TEMPERATURE_SENSOR:
            return f"{self.temperature}°C"
        elif self.type == DeviceType.HUMIDITY_SENSOR:
            return f"{self.humidity}%"
        elif self.type == DeviceType.MOTION_SENSOR:
            return "동작감지" if self.motion_detected else "정상"
        elif self.type == DeviceType.DOOR_SENSOR:
            return "열림" if self.door_open else "닫힌"
        else:
            return base_status


# 확장된 디바이스 목록
extended_devices = [
    # 기존 디바이스들
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
    
    # 새로운 디바이스들
    ExtendedPlanDevice(11, "거실 TV", DeviceType.TV, "거실", 450, 380, properties={'channel': 7, 'volume': 25}),
    ExtendedPlanDevice(12, "침실1 TV", DeviceType.TV, "침실1", 650, 470, properties={'channel': 1, 'volume': 15}),
    ExtendedPlanDevice(13, "냉장고", DeviceType.REFRIGERATOR, "주방", 580, 120, state=True, properties={'temperature': 3.5}),
    ExtendedPlanDevice(14, "거실 온도센서", DeviceType.TEMPERATURE_SENSOR, "거실", 480, 340, properties={'temperature': 23.2}),
    ExtendedPlanDevice(15, "욕실 습도센서", DeviceType.HUMIDITY_SENSOR, "욕실", 750, 300, properties={'humidity': 65.0}),
    ExtendedPlanDevice(16, "현관 동작감지", DeviceType.MOTION_SENSOR, "현관", 260, 340),
    ExtendedPlanDevice(17, "주출입문 센서", DeviceType.DOOR_SENSOR, "현관", 220, 380),
    ExtendedPlanDevice(18, "거실 창문", DeviceType.WINDOW, "거실", 400, 480),
    ExtendedPlanDevice(19, "보안 시스템", DeviceType.SECURITY_SYSTEM, "현관", 200, 320),
]


# 디바이스 타입별 색상 정의 (확장)
EXTENDED_COLOR_ON = {
    DeviceType.LIGHT: "#FFD700",           # 조명: 금색
    DeviceType.AIRCON: "#00CED1",          # 에어컨: 청록색
    DeviceType.GAS: "#FF4500",             # 가스: 주황색
    DeviceType.BOILER: "#DC143C",          # 보일러: 빨간색
    DeviceType.CCTV: "#32CD32",            # CCTV: 녹색
    DeviceType.TV: "#8A2BE2",              # TV: 보라색
    DeviceType.REFRIGERATOR: "#1E90FF",    # 냉장고: 파란색
    DeviceType.TEMPERATURE_SENSOR: "#FF69B4",  # 온도센서: 핫핑크
    DeviceType.HUMIDITY_SENSOR: "#20B2AA",     # 습도센서: 라이트 시그린
    DeviceType.MOTION_SENSOR: "#FFA500",       # 동작센서: 오렌지
    DeviceType.DOOR_SENSOR: "#9370DB",         # 문센서: 미디엄 퍼플
    DeviceType.WINDOW: "#87CEEB",              # 창문: 스카이 블루
    DeviceType.SECURITY_SYSTEM: "#B22222",    # 보안: 파이어 브릭
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
    
    @staticmethod
    def set_tv_channel(device: ExtendedPlanDevice, channel: int):
        """TV 채널 설정"""
        if device.type == DeviceType.TV:
            device.channel = channel
            device.state = True
    
    @staticmethod
    def set_volume(device: ExtendedPlanDevice, volume: int):
        """볼륨 설정"""
        if device.type == DeviceType.TV:
            device.volume = volume


if __name__ == "__main__":
    # 테스트 코드
    print("=== 확장된 디바이스 목록 ===")
    for device in extended_devices:
        print(f"{device.id}: {device.name} ({device.type.value}) - {device.get_status_text()}")
    
    print("\\n=== TV 디바이스 테스트 ===")
    tv = get_device_by_id(11)
    if tv:
        print(f"초기 상태: {tv.get_status_text()}")
        DeviceCommand.turn_on(tv)
        DeviceCommand.set_tv_channel(tv, 15)
        DeviceCommand.set_volume(tv, 30)
        print(f"설정 후: {tv.get_status_text()}")
    
    print("\\n=== 센서 디바이스 테스트 ===")
    temp_sensor = get_device_by_id(14)
    if temp_sensor:
        temp_sensor.temperature = 25.8
        print(f"온도 센서: {temp_sensor.get_status_text()}")
