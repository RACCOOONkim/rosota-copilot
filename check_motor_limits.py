#!/usr/bin/env python3
"""
모터의 현재 Angle_Limit 설정을 확인하는 스크립트
"""

import sys
from rosota_copilot.robot.so_arm import SOArm100Adapter

def main():
    print("=== 모터 Angle_Limit 확인 ===\n")
    
    # 로봇 연결
    robot = SOArm100Adapter()
    
    # 포트 찾기
    import glob
    import platform
    
    if platform.system() == "Darwin":  # macOS
        ports = glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
    else:  # Linux
        ports = glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    
    if not ports:
        print("❌ USB 포트를 찾을 수 없습니다.")
        return
    
    port = ports[0]
    print(f"🔌 연결 중: {port}\n")
    
    if not robot.connect(port=port):
        print("❌ 연결 실패")
        return
    
    print("✅ 연결 성공!\n")
    
    # 각 모터의 Angle_Limit 읽기
    print("📊 현재 모터 설정:\n")
    for i, motor_name in enumerate(robot.JOINT_NAMES):
        print(f"--- {motor_name} (ID: {i+1}) ---")
        
        try:
            # Present_Position 읽기 (현재 위치)
            current_pos = robot.motors_bus.read("Present_Position", motor_names=motor_name)
            if isinstance(current_pos, list):
                current_pos = current_pos[0]
            print(f"  Current Position: {current_pos:.2f}°")
            
            # Angle_Limit_Min 읽기
            min_limit = robot.motors_bus.read("Angle_Limit_Min", motor_names=motor_name)
            if isinstance(min_limit, list):
                min_limit = min_limit[0]
            print(f"  Angle_Limit_Min: {min_limit} (raw value)")
            
            # Angle_Limit_Max 읽기
            max_limit = robot.motors_bus.read("Angle_Limit_Max", motor_names=motor_name)
            if isinstance(max_limit, list):
                max_limit = max_limit[0]
            print(f"  Angle_Limit_Max: {max_limit} (raw value)")
            
            # Operating_Mode 읽기 (있다면)
            try:
                mode = robot.motors_bus.read("Operating_Mode", motor_names=motor_name)
                if isinstance(mode, list):
                    mode = mode[0]
                print(f"  Operating_Mode: {mode}")
            except:
                pass
            
            print()
            
        except Exception as e:
            print(f"  ❌ 읽기 실패: {e}\n")
    
    robot.disconnect()
    print("연결 종료")

if __name__ == "__main__":
    main()

