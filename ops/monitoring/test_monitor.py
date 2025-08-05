#!/usr/bin/env python3
"""
快速测试实时监控功能
"""

import subprocess
import sys
import time
import requests
import json

def test_monitor():
    """测试实时监控功能"""
    print("🧪 测试实时监控功能...")
    
    # 启动监控服务器
    print("🚀 启动监控服务器...")
    try:
        monitor_process = subprocess.Popen([
            sys.executable, "real_time_monitor.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(5)
        
        # 测试API
        print("📡 测试API接口...")
        try:
            response = requests.get("http://localhost:5000/api/latest-data", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print("✅ API响应成功!")
                print(f"📊 性能数据: {len(data.get('performance', []))} 条")
                print(f"💰 奖励数据: {len(data.get('rewards', []))} 条")
                
                # 显示一些示例数据
                if data.get('performance'):
                    latest_perf = data['performance'][0]
                    print(f"🔥 最新性能: CPU {latest_perf['cpu_usage']}%, 内存 {latest_perf['memory_usage']}%")
                
                if data.get('rewards'):
                    latest_reward = data['rewards'][0]
                    print(f"💎 最新奖励: 轮次 {latest_reward['round']}, 奖励 {latest_reward['reward']}")
                
            else:
                print(f"❌ API请求失败: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 无法连接到服务器: {e}")
        
        # 停止服务器
        print("⏹️ 停止服务器...")
        monitor_process.terminate()
        monitor_process.wait()
        print("✅ 测试完成!")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_monitor() 