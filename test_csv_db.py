"""
CSV 데이터베이스 테스트 스크립트
"""

from csv_database import SmartHomeCSV
from datetime import datetime

def test_csv_database():
    print("CSV 데이터베이스 테스트 시작...")
    
    # CSV 데이터베이스 초기화
    db = SmartHomeCSV("data")
    
    # 디바이스 상태 업데이트 테스트
    print("\\n1. 디바이스 상태 업데이트 테스트")
    db.update_device_status("거실 조명", "ON", "light")
    db.update_device_status("에어컨", "OFF", "aircon")
    
    # 디바이스 상태 조회 테스트
    print("\\n2. 디바이스 상태 조회 테스트")
    status = db.get_device_status("거실 조명")
    print(f"거실 조명 상태: {status}")
    
    # 모든 디바이스 조회
    devices = db.get_all_devices()
    print(f"등록된 디바이스 수: {len(devices)}")
    for device in devices:
        print(f"  - {device['name']}: {device['status']} ({device['type']})")
    
    # 패턴 저장 테스트
    print("\\n3. 패턴 저장 테스트")
    now = datetime.now()
    db.save_pattern(now, "거실 조명", "ON")
    db.save_pattern(now, "에어컨", "OFF")
    
    # 패턴 조회 테스트
    print("\\n4. 패턴 조회 테스트")
    start_date = now.strftime("%Y-%m-%d 00:00:00")
    end_date = now.strftime("%Y-%m-%d 23:59:59")
    patterns = db.get_patterns(start_date, end_date)
    print(f"오늘 패턴 수: {len(patterns)}")
    for pattern in patterns:
        print(f"  - {pattern[0]}: {pattern[1]} -> {pattern[2]}")
    
    # 규칙 저장 테스트
    print("\\n5. 규칙 저장 테스트")
    db.save_rule("시간 == 18:00", "거실 조명 ON")
    db.save_rule("시간 == 23:00", "모든 조명 OFF")
    
    # 활성 규칙 조회 테스트
    print("\\n6. 활성 규칙 조회 테스트")
    rules = db.get_active_rules()
    print(f"활성 규칙 수: {len(rules)}")
    for rule in rules:
        print(f"  - 규칙 {rule[0]}: {rule[1]} -> {rule[2]}")
    
    print("\\nCSV 데이터베이스 테스트 완료!")

if __name__ == "__main__":
    test_csv_database()
