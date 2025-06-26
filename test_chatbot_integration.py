#!/usr/bin/env python3
"""
챗봇 연동 테스트

개선된 챗봇과 패널 간의 통신 및 명령 처리를 테스트합니다.
"""

import time
import threading
from enhanced_chatbot import SmartChatBot
from communication import send_message

def test_chatbot_commands():
    """챗봇 명령어 테스트"""
    print("🤖 챗봇 연동 테스트 시작...\n")
    
    # 테스트할 명령어들
    test_commands = [
        "안녕하세요",
        "거실 조명 켜줘",
        "모든 조명 꺼줘", 
        "에어컨 24도로 설정해줘",
        "디바이스 상태 알려줘",
        "도움말",
        "고마워요"
    ]
    
    print("📝 테스트할 명령어 목록:")
    for i, cmd in enumerate(test_commands, 1):
        print(f"  {i}. {cmd}")
    
    print("\n💡 실제 테스트 방법:")
    print("1. 패널을 먼저 실행하세요:")
    print("   python run_extended_panel.py")
    print("\n2. 그 다음 개선된 챗봇을 실행하세요:")
    print("   python run_smart_chatbot.py")
    print("\n3. 챗봇에서 위의 명령어들을 테스트해보세요!")
    
    print("\n🔍 기대되는 동작:")
    print("• 자연스러운 한국어 명령 인식")
    print("• 디바이스 상태 실시간 조회")
    print("• 패턴 감지 시 스마트한 규칙 제안")
    print("• 빠른 응답 버튼으로 편리한 조작")
    print("• 컨텍스트 기반 대화 지속")
    
    return True

def simulate_pattern_detection():
    """패턴 감지 시뮬레이션"""
    print("\n🔍 패턴 감지 시뮬레이션...")
    
    # 패널이 실행 중이라고 가정하고 패턴 감지 메시지 전송
    pattern_message = "패턴 감지: 거실조명 18:00 ON"
    
    try:
        send_message(pattern_message, port=7778)
        print(f"✅ 패턴 감지 메시지 전송: {pattern_message}")
        print("💬 챗봇에서 자동화 규칙 생성 제안을 확인하세요!")
    except Exception as e:
        print(f"❌ 메시지 전송 실패: {str(e)}")
        print("💡 패널과 챗봇이 모두 실행 중인지 확인하세요.")

def test_chatbot_features():
    """챗봇 주요 기능 테스트"""
    print("\n🎯 개선된 챗봇 주요 기능:")
    
    features = [
        {
            "name": "자연어 이해",
            "description": "한국어 명령을 자연스럽게 이해하고 처리",
            "examples": ["거실 조명 켜줘", "에어컨 온도 올려줘", "모든 불 꺼줘"]
        },
        {
            "name": "컨텍스트 인식", 
            "description": "대화 맥락을 기억하고 적절한 응답 제공",
            "examples": ["이전 명령 기억", "연관된 질문 처리", "상황별 맞춤 응답"]
        },
        {
            "name": "빠른 응답 버튼",
            "description": "자주 사용하는 명령을 버튼으로 제공",
            "examples": ["Yes/No 버튼", "모든 조명 제어", "상태 조회"]
        },
        {
            "name": "실시간 상태 표시",
            "description": "시스템 연결 상태와 디바이스 정보 표시",
            "examples": ["연결 상태", "현재 시간", "활성 디바이스 수"]
        },
        {
            "name": "스마트 패턴 감지",
            "description": "사용 패턴을 분석하고 자동화 규칙 제안",
            "examples": ["반복 행동 감지", "규칙 생성 제안", "사용자 확인 요청"]
        }
    ]
    
    for i, feature in enumerate(features, 1):
        print(f"\n{i}. 🔧 {feature['name']}")
        print(f"   📋 {feature['description']}")
        print(f"   💡 예시: {', '.join(feature['examples'])}")
    
    print("\n✨ 사용법:")
    print("• 자연스럽게 말하듯이 명령하세요")
    print("• 빠른 버튼을 활용하여 편리하게 조작하세요")
    print("• 패턴 감지 알림이 오면 Yes/No로 응답하세요")
    print("• '도움말'을 입력하면 사용 가능한 명령어를 볼 수 있습니다")

if __name__ == "__main__":
    print("🏠 스마트홈 챗봇 연동 테스트\n")
    
    # 기본 명령어 테스트
    test_chatbot_commands()
    
    # 주요 기능 설명
    test_chatbot_features()
    
    # 패턴 감지 시뮬레이션 (선택사항)
    print("\n" + "="*50)
    user_input = input("패턴 감지 시뮬레이션을 실행하시겠어요? (y/n): ")
    if user_input.lower() in ['y', 'yes', '네', 'ㅇ']:
        simulate_pattern_detection()
    
    print("\n🎉 테스트 준비 완료!")
    print("\n실제 테스트를 위해 다음 순서로 실행하세요:")
    print("1️⃣ python run_extended_panel.py")
    print("2️⃣ python run_smart_chatbot.py") 
    print("3️⃣ 챗봇에서 명령어 테스트!")
