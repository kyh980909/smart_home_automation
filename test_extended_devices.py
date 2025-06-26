#!/usr/bin/env python3
"""
기본 디바이스 기능 테스트

기존 5개 디바이스 타입의 기능들을 테스트합니다.
"""

from extended_devices import extended_devices, DeviceCommand, DeviceType

def test_basic_devices():
    print("=== 기본 디바이스 기능 테스트 ===\n")
    
    # 1. 모든 디바이스 현재 상태 출력
    print("🏠 현재 등록된 디바이스들:")
    for device in extended_devices:
        print(f"  {device.id:2d}. {device.name:15s} ({device.type.value:8s}) - {device.get_status_text()}")
    
    print(f"\n총 {len(extended_devices)}개의 디바이스가 등록되어 있습니다.\n")
    
    # 2. 디바이스 타입별 그룹화 테스트
    print("📊 디바이스 타입별 분류:")
    device_types = {}
    for device in extended_devices:
        if device.type not in device_types:
            device_types[device.type] = []
        device_types[device.type].append(device)
    
    for device_type, devices in device_types.items():
        print(f"  {device_type.value}: {len(devices)}개")
        for device in devices:
            print(f"    - {device.name}")
    
    # 3. 조명 제어 테스트
    print("\n💡 조명 제어 테스트:")
    light_devices = [d for d in extended_devices if d.type == DeviceType.LIGHT]
    for i, light in enumerate(light_devices[:3]):  # 처음 3개만 테스트
        brightness = [30, 70, 100][i]
        print(f"  {light.name} 초기 상태: {light.get_status_text()}")
        
        DeviceCommand.set_brightness(light, brightness)
        print(f"  {light.name} 밝기 {brightness}% 설정 후: {light.get_status_text()}")
    
    # 4. 에어컨 제어 테스트
    print("\n❄️ 에어컨 제어 테스트:")
    aircon_devices = [d for d in extended_devices if d.type == DeviceType.AIRCON]
    for aircon in aircon_devices:
        print(f"  {aircon.name} 초기 상태: {aircon.get_status_text()}")
        
        DeviceCommand.turn_on(aircon)
        DeviceCommand.set_temperature(aircon, 24.0)
        print(f"  {aircon.name} 24°C 설정 후: {aircon.get_status_text()}")
    
    # 5. 보일러 제어 테스트
    print("\n🔥 보일러 제어 테스트:")
    boiler_devices = [d for d in extended_devices if d.type == DeviceType.BOILER]
    for boiler in boiler_devices:
        print(f"  {boiler.name} 초기 상태: {boiler.get_status_text()}")
        
        DeviceCommand.turn_on(boiler)
        DeviceCommand.set_temperature(boiler, 45.0)
        print(f"  {boiler.name} 45°C 설정 후: {boiler.get_status_text()}")
    
    # 6. 기타 디바이스 ON/OFF 테스트
    print("\n🔧 기타 디바이스 제어 테스트:")
    other_devices = [d for d in extended_devices if d.type in [DeviceType.GAS, DeviceType.CCTV]]
    for device in other_devices:
        print(f"  {device.name} 초기 상태: {device.get_status_text()}")
        
        DeviceCommand.turn_on(device)
        print(f"  {device.name} ON 설정 후: {device.get_status_text()}")
        
        DeviceCommand.turn_off(device)
        print(f"  {device.name} OFF 설정 후: {device.get_status_text()}")
    
    print("\n✅ 모든 테스트가 완료되었습니다!")
    
    return True

def test_device_commands():
    """디바이스 명령어 테스트"""
    print("\n=== 디바이스 명령어 테스트 ===\n")
    
    # 조명 명령어 테스트
    light = next((d for d in extended_devices if d.type == DeviceType.LIGHT), None)
    if light:
        print(f"💡 {light.name} 명령어 테스트:")
        print(f"  초기: {light.get_status_text()}")
        
        DeviceCommand.set_brightness(light, 0)
        print(f"  끄기: {light.get_status_text()}")
        
        DeviceCommand.set_brightness(light, 50)
        print(f"  50% 밝기: {light.get_status_text()}")
        
        DeviceCommand.set_brightness(light, 100)
        print(f"  최대 밝기: {light.get_status_text()}")
    
    # 에어컨 명령어 테스트
    aircon = next((d for d in extended_devices if d.type == DeviceType.AIRCON), None)
    if aircon:
        print(f"\n❄️ {aircon.name} 명령어 테스트:")
        print(f"  초기: {aircon.get_status_text()}")
        
        DeviceCommand.turn_on(aircon)
        print(f"  켜기: {aircon.get_status_text()}")
        
        DeviceCommand.set_temperature(aircon, 18.0)
        print(f"  18도 설정: {aircon.get_status_text()}")
        
        DeviceCommand.set_temperature(aircon, 28.0)
        print(f"  28도 설정: {aircon.get_status_text()}")
        
        DeviceCommand.turn_off(aircon)
        print(f"  끄기: {aircon.get_status_text()}")
    
    print("\n✅ 명령어 테스트 완료!")

if __name__ == "__main__":
    print("🏠 스마트홈 기본 디바이스 테스트를 시작합니다...\n")
    
    # 기본 디바이스 테스트
    test_basic_devices()
    
    # 명령어 테스트
    test_device_commands()
    
    print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    print("\n다음 명령으로 확장된 패널을 실행할 수 있습니다:")
    print("  python run_extended_panel.py")
    print("\n또는 기본 패널을 실행할 수 있습니다:")
    print("  python main_panel.py")
