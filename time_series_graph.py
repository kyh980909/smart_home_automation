"""
시계열 그래프 시각화 모듈

디바이스 사용 패턴과 센서 데이터를 시간대별로 그래프로 표시하는 기능을 제공합니다.
"""

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np

# 한글 폰트 설정
plt.rcParams['font.family'] = ['AppleGothic'] if plt.rcParams['font.family'][0] == 'DejaVu Sans' else ['Malgun Gothic', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class TimeSeriesChart(FigureCanvas):
    """
    시계열 데이터를 표시하는 차트 위젯
    """
    
    def __init__(self, parent=None, width=10, height=6, dpi=100):
        """
        시계열 차트 초기화
        
        Args:
            parent: 부모 위젯
            width: 차트 너비
            height: 차트 높이  
            dpi: 해상도
        """
        self.figure = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 차트 스타일 설정
        self.figure.patch.set_facecolor('white')
        
    def plot_device_usage(self, data: List[Dict[str, Any]], device_name: str = None):
        """
        디바이스 사용 패턴을 시간대별로 표시
        
        Args:
            data: 패턴 데이터 리스트
            device_name: 특정 디바이스만 표시 (None이면 전체)
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 데이터 필터링
        if device_name:
            filtered_data = [d for d in data if d.get('device') == device_name]
            title = f"{device_name} 사용 패턴"
        else:
            filtered_data = data
            title = "전체 디바이스 사용 패턴"
        
        if not filtered_data:
            ax.text(0.5, 0.5, '데이터가 없습니다', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_title(title)
            self.draw()
            return
        
        # 데이터 프레임 생성
        df = pd.DataFrame(filtered_data)
        
        # timestamp를 datetime으로 변환
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        # 디바이스별로 그룹화하여 플롯
        device_groups = df.groupby('device') if not device_name else [(device_name, df)]
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        color_idx = 0
        
        for device, group in device_groups:
            # ON/OFF 상태를 숫자로 변환
            group['value_numeric'] = group['value'].map({'ON': 1, 'OFF': 0})
            
            # 스텝 차트로 표시 (디지털 신호처럼)
            ax.step(group['timestamp'], group['value_numeric'], 
                   where='post', label=device, 
                   color=colors[color_idx % len(colors)], linewidth=2)
            
            color_idx += 1
        
        # 차트 설정
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('시간', fontsize=12)
        ax.set_ylabel('상태 (ON=1, OFF=0)', fontsize=12)
        ax.set_ylim(-0.1, 1.1)
        ax.set_yticks([0, 1])
        ax.set_yticklabels(['OFF', 'ON'])
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # x축 날짜 포맷팅
        self.figure.autofmt_xdate()
        
        self.draw()
    
    def plot_temperature_trend(self, data: List[Dict[str, Any]], device_name: str = "보일러"):
        """
        온도 추이를 연속적인 선 그래프로 표시
        
        Args:
            data: 온도 데이터
            device_name: 온도 디바이스 이름
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 온도 데이터 필터링 (임시로 랜덤 온도 데이터 생성)
        temp_data = self._generate_temperature_data()
        
        if not temp_data:
            ax.text(0.5, 0.5, '온도 데이터가 없습니다', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_title(f"{device_name} 온도 추이")
            self.draw()
            return
        
        # 온도 그래프 그리기
        times = [d['timestamp'] for d in temp_data]
        temperatures = [d['temperature'] for d in temp_data]
        
        ax.plot(times, temperatures, color='#FF6B6B', linewidth=2, marker='o', markersize=4)
        
        # 적정 온도 범위 표시
        ax.axhspan(20, 24, alpha=0.2, color='green', label='적정 온도 범위')
        
        # 차트 설정
        ax.set_title(f"{device_name} 온도 추이", fontsize=14, fontweight='bold')
        ax.set_xlabel('시간', fontsize=12)
        ax.set_ylabel('온도 (°C)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # x축 날짜 포맷팅
        self.figure.autofmt_xdate()
        
        self.draw()
    
    def plot_daily_summary(self, data: List[Dict[str, Any]]):
        """
        일일 사용량 요약을 막대 그래프로 표시
        
        Args:
            data: 패턴 데이터
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not data:
            ax.text(0.5, 0.5, '데이터가 없습니다', 
                   horizontalalignment='center', verticalalignment='center',
                   transform=ax.transAxes, fontsize=14)
            ax.set_title("일일 디바이스 사용 요약")
            self.draw()
            return
        
        # 디바이스별 ON 횟수 계산
        df = pd.DataFrame(data)
        on_counts = df[df['value'] == 'ON'].groupby('device').size()
        
        # 막대 그래프
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        bars = ax.bar(on_counts.index, on_counts.values, 
                     color=colors[:len(on_counts)], alpha=0.8)
        
        # 막대 위에 숫자 표시
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}회', ha='center', va='bottom')
        
        ax.set_title("일일 디바이스 사용 요약", fontsize=14, fontweight='bold')
        ax.set_xlabel('디바이스', fontsize=12)
        ax.set_ylabel('사용 횟수', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # x축 라벨 회전
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.draw()
    
    def _generate_temperature_data(self) -> List[Dict[str, Any]]:
        """
        임시 온도 데이터 생성 (실제 구현에서는 센서 데이터를 사용)
        """
        now = datetime.now()
        temp_data = []
        
        # 24시간 동안의 온도 데이터 생성
        for i in range(24):
            timestamp = now - timedelta(hours=23-i)
            # 하루 온도 패턴 시뮬레이션 (아침에 낮고, 낮에 높고, 밤에 다시 낮아짐)
            base_temp = 22 + 3 * np.sin((i - 6) * np.pi / 12)
            temperature = base_temp + np.random.normal(0, 0.5)  # 노이즈 추가
            
            temp_data.append({
                'timestamp': timestamp,
                'temperature': round(temperature, 1)
            })
        
        return temp_data


class GraphWidget:
    """
    그래프 위젯들을 관리하는 클래스
    """
    
    @staticmethod
    def create_usage_chart(parent=None):
        """사용 패턴 차트 생성"""
        return TimeSeriesChart(parent, width=8, height=5)
    
    @staticmethod  
    def create_temperature_chart(parent=None):
        """온도 추이 차트 생성"""
        return TimeSeriesChart(parent, width=8, height=4)
    
    @staticmethod
    def create_summary_chart(parent=None):
        """요약 차트 생성"""
        return TimeSeriesChart(parent, width=6, height=4)


# 테스트용 샘플 데이터 생성 함수
def generate_sample_data() -> List[Dict[str, Any]]:
    """
    테스트용 샘플 패턴 데이터 생성
    """
    now = datetime.now()
    sample_data = []
    
    devices = ["거실 조명", "주방 조명", "에어컨", "보일러"]
    
    # 하루 동안의 패턴 생성
    for hour in range(24):
        timestamp = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # 시간대별 디바이스 사용 패턴
        if 7 <= hour <= 8:  # 아침
            sample_data.extend([
                {"timestamp": timestamp, "device": "거실 조명", "action": "power", "value": "ON"},
                {"timestamp": timestamp + timedelta(minutes=30), "device": "주방 조명", "action": "power", "value": "ON"}
            ])
        elif 18 <= hour <= 23:  # 저녁
            sample_data.extend([
                {"timestamp": timestamp, "device": "거실 조명", "action": "power", "value": "ON"},
                {"timestamp": timestamp + timedelta(minutes=15), "device": "에어컨", "action": "power", "value": "ON"}
            ])
        elif hour == 23:  # 밤
            sample_data.extend([
                {"timestamp": timestamp, "device": "거실 조명", "action": "power", "value": "OFF"},
                {"timestamp": timestamp + timedelta(minutes=10), "device": "주방 조명", "action": "power", "value": "OFF"}
            ])
    
    return sample_data


if __name__ == "__main__":
    # 테스트 코드
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # 테스트 차트 생성
    chart = TimeSeriesChart()
    sample_data = generate_sample_data()
    chart.plot_device_usage(sample_data)
    
    layout.addWidget(chart)
    window.setCentralWidget(central_widget)
    window.setWindowTitle("시계열 그래프 테스트")
    window.resize(1000, 600)
    window.show()
    
    sys.exit(app.exec_())
