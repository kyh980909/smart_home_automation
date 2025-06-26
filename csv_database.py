"""
CSV 파일 기반 데이터 저장 및 관리 모듈

SQLite 대신 CSV 파일을 사용하여 디바이스 상태, 사용 패턴, 규칙을 저장하고 관리합니다.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List, Tuple, Dict, Any
from pathlib import Path


class SmartHomeCSV:
    """CSV 파일 기반 데이터 저장 클래스"""

    def __init__(self, data_dir: str = "data") -> None:
        """
        CSV 데이터베이스 초기화
        
        Args:
            data_dir: 데이터 파일들을 저장할 디렉토리
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # CSV 파일 경로 설정
        self.devices_file = self.data_dir / "devices.csv"
        self.patterns_file = self.data_dir / "patterns.csv"
        self.rules_file = self.data_dir / "rules.csv"
        
        self._create_csv_files()

    def _create_csv_files(self) -> None:
        """필요한 CSV 파일들을 생성하고 헤더를 추가"""
        
        # devices.csv 파일 생성
        if not self.devices_file.exists():
            with open(self.devices_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['name', 'type', 'status'])  # 헤더
        
        # patterns.csv 파일 생성
        if not self.patterns_file.exists():
            with open(self.patterns_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'device', 'action'])  # 헤더
        
        # rules.csv 파일 생성
        if not self.rules_file.exists():
            with open(self.rules_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'condition', 'action', 'enabled'])  # 헤더

    # ------------------------------------------------------------------
    # 패턴 저장 관련 메서드
    
    def save_pattern(self, timestamp: datetime | str, device: str, action: str) -> None:
        """
        사용 패턴 데이터를 CSV 파일에 저장
        
        Args:
            timestamp: 시간 정보
            device: 디바이스 이름
            action: 실행된 액션
        """
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 패턴 데이터 추가
        with open(self.patterns_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, device, action])

    def get_patterns(self, start_date: datetime | str, end_date: datetime | str) -> List[Tuple]:
        """
        지정된 기간의 패턴 데이터를 반환
        
        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜
            
        Returns:
            패턴 데이터 리스트 [(timestamp, device, action), ...]
        """
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        patterns = []
        
        if not self.patterns_file.exists():
            return patterns
        
        with open(self.patterns_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = row['timestamp']
                # 날짜 범위 체크
                if start_date <= timestamp <= end_date:
                    patterns.append((timestamp, row['device'], row['action']))
        
        # 시간순 정렬
        patterns.sort(key=lambda x: x[0])
        return patterns

    # ------------------------------------------------------------------
    # 규칙 관리 관련 메서드
    
    def save_rule(self, condition: str, action: str) -> None:
        """
        새로운 규칙을 추가하고 활성화
        
        Args:
            condition: 조건
            action: 액션
        """
        # 새로운 ID 생성 (기존 규칙 수 + 1)
        rule_id = self._get_next_rule_id()
        
        with open(self.rules_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([rule_id, condition, action, 1])  # enabled=1

    def get_active_rules(self) -> List[Tuple]:
        """
        활성화된 규칙들을 반환
        
        Returns:
            활성화된 규칙 리스트 [(id, condition, action), ...]
        """
        rules = []
        
        if not self.rules_file.exists():
            return rules
        
        with open(self.rules_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['enabled'] == '1':  # 활성화된 규칙만
                    rules.append((int(row['id']), row['condition'], row['action']))
        
        return rules

    def _get_next_rule_id(self) -> int:
        """다음 규칙 ID를 생성"""
        max_id = 0
        
        if self.rules_file.exists():
            with open(self.rules_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        rule_id = int(row['id'])
                        max_id = max(max_id, rule_id)
                    except (ValueError, KeyError):
                        continue
        
        return max_id + 1

    # ------------------------------------------------------------------
    # 디바이스 상태 관리 관련 메서드
    
    def update_device_status(self, device: str, status: str, type_: str | None = None) -> None:
        """
        디바이스 상태를 업데이트하거나 새로 생성
        
        Args:
            device: 디바이스 이름
            status: 상태 (ON/OFF 등)
            type_: 디바이스 타입 (선택사항)
        """
        # 기존 디바이스 데이터 읽기
        devices = self._load_devices()
        
        # 디바이스 업데이트 또는 추가
        found = False
        for dev in devices:
            if dev['name'] == device:
                dev['status'] = status
                if type_:
                    dev['type'] = type_
                found = True
                break
        
        if not found:
            # 새 디바이스 추가
            devices.append({
                'name': device,
                'type': type_ or '',
                'status': status
            })
        
        # CSV 파일에 저장
        self._save_devices(devices)

    def get_device_status(self, device: str) -> str | None:
        """
        디바이스의 현재 상태를 반환
        
        Args:
            device: 디바이스 이름
            
        Returns:
            디바이스 상태 또는 None (없는 경우)
        """
        devices = self._load_devices()
        
        for dev in devices:
            if dev['name'] == device:
                return dev['status']
        
        return None

    def _load_devices(self) -> List[Dict[str, str]]:
        """디바이스 데이터를 CSV에서 로드"""
        devices = []
        
        if not self.devices_file.exists():
            return devices
        
        with open(self.devices_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                devices.append(dict(row))
        
        return devices

    def _save_devices(self, devices: List[Dict[str, str]]) -> None:
        """디바이스 데이터를 CSV에 저장"""
        with open(self.devices_file, 'w', newline='', encoding='utf-8') as f:
            if devices:
                fieldnames = ['name', 'type', 'status']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(devices)

    # ------------------------------------------------------------------
    # 유틸리티 메서드
    
    def clear_patterns(self) -> None:
        """패턴 데이터 모두 삭제"""
        with open(self.patterns_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'device', 'action'])  # 헤더만 남김

    def clear_devices(self) -> None:
        """디바이스 데이터 모두 삭제"""
        with open(self.devices_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'type', 'status'])  # 헤더만 남김

    def clear_rules(self) -> None:
        """규칙 데이터 모두 삭제"""
        with open(self.rules_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'condition', 'action', 'enabled'])  # 헤더만 남김

    def get_all_devices(self) -> List[Dict[str, str]]:
        """모든 디바이스 정보를 반환"""
        return self._load_devices()
