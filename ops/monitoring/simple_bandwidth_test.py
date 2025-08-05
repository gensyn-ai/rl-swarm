#!/usr/bin/env python3
"""
简单的网络带宽测试工具
用于诊断Tailscale是否影响实际带宽
"""

import subprocess
import time
import requests
import threading
import os
from datetime import datetime

class NetworkBandwidthTester:
    def __init__(self):
        self.tailscale_ip = "100.87.33.96"  # 从ifconfig发现的Tailscale IP
        self.test_results = {}
        
    def get_interface_stats(self, interface="utun4"):
        """获取指定网络接口的流量统计"""
        try:
            # macOS的netstat命令
            result = subprocess.run(['netstat', '-ibf', 'inet'], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if interface in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        return {
                            'interface': interface,
                            'bytes_in': int(parts[6]),
                            'bytes_out': int(parts[9]),
                            'timestamp': datetime.now()
                        }
        except Exception as e:
            print(f"获取接口统计失败: {e}")
        return None
    
    def monitor_interface_traffic(self, duration=60):
        """监控Tailscale接口流量变化"""
        print(f"🔍 监控Tailscale接口(utun4)流量 {duration}秒...")
        
        start_stats = self.get_interface_stats()
        if not start_stats:
            print("❌ 无法获取接口统计")
            return
            
        print(f"开始监控: {start_stats['timestamp']}")
        time.sleep(duration)
        
        end_stats = self.get_interface_stats()
        if not end_stats:
            print("❌ 无法获取结束统计")
            return
            
        # 计算流量差值
        bytes_in_diff = end_stats['bytes_in'] - start_stats['bytes_in']
        bytes_out_diff = end_stats['bytes_out'] - start_stats['bytes_out']
        
        # 转换为MB和Mbps
        mb_in = bytes_in_diff / 1024 / 1024
        mb_out = bytes_out_diff / 1024 / 1024
        mbps_in = (mb_in * 8) / duration
        mbps_out = (mb_out * 8) / duration
        
        print(f"\n📊 Tailscale流量统计 ({duration}秒):")
        print(f"   ⬇️  下行: {mb_in:.2f} MB ({mbps_in:.2f} Mbps)")
        print(f"   ⬆️  上行: {mb_out:.2f} MB ({mbps_out:.2f} Mbps)")
        print(f"   📈 总流量: {mb_in + mb_out:.2f} MB")
        
        return {
            'duration': duration,
            'mb_in': mb_in,
            'mb_out': mb_out,
            'mbps_in': mbps_in,
            'mbps_out': mbps_out,
            'total_mb': mb_in + mb_out
        }
    
    def test_internet_speed(self, test_name="通用测试"):
        """测试互联网速度"""
        print(f"\n🌐 {test_name} - 互联网速度测试...")
        
        # 使用speedtest-cli的简化版本
        test_servers = [
            "http://speedtest.tele2.net/10MB.zip",
            "http://download.thinkbroadband.com/10MB.zip",
        ]
        
        best_speed = 0
        for i, url in enumerate(test_servers):
            try:
                print(f"   测试服务器 {i+1}...")
                start_time = time.time()
                
                response = requests.get(url, stream=True, timeout=30)
                total_size = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        total_size += len(chunk)
                        # 限制下载量，避免过多流量
                        if total_size > 5 * 1024 * 1024:  # 5MB
                            break
                
                duration = time.time() - start_time
                speed_mbps = (total_size * 8) / (duration * 1024 * 1024)
                
                print(f"   📶 服务器{i+1}: {speed_mbps:.2f} Mbps ({total_size/1024/1024:.1f}MB in {duration:.1f}s)")
                best_speed = max(best_speed, speed_mbps)
                
            except Exception as e:
                print(f"   ❌ 服务器{i+1}测试失败: {e}")
        
        return best_speed
    
    def ping_test(self):
        """Ping测试延迟"""
        print("\n🏓 网络延迟测试...")
        
        targets = [
            ("8.8.8.8", "Google DNS"),
            ("1.1.1.1", "Cloudflare DNS"),
            ("114.114.114.114", "国内DNS")
        ]
        
        results = {}
        for ip, name in targets:
            try:
                result = subprocess.run(['ping', '-c', '4', ip], 
                                      capture_output=True, text=True, timeout=10)
                
                # 解析ping结果
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line:
                        # macOS ping输出格式: min/avg/max/stddev = 
                        avg_ms = float(line.split('=')[1].split('/')[1])
                        results[name] = avg_ms
                        print(f"   📡 {name}: {avg_ms:.1f}ms")
                        break
                        
            except Exception as e:
                print(f"   ❌ {name}({ip}) ping失败: {e}")
                results[name] = None
        
        return results
    
    def comprehensive_test(self):
        """综合网络测试"""
        print("🚀 开始综合网络带宽诊断...")
        print("=" * 50)
        
        # 1. 基础网络测试
        ping_results = self.ping_test()
        
        # 2. 互联网速度测试
        internet_speed = self.test_internet_speed("基准测试")
        
        # 3. 监控Tailscale流量（在后台运行网络活动时）
        print("\n⚠️  请在另一个终端执行一些网络活动（如访问网页、下载等）")
        print("   这样可以观察Tailscale是否参与了流量传输...")
        
        tailscale_stats = self.monitor_interface_traffic(30)
        
        # 4. 生成报告
        self.generate_report(ping_results, internet_speed, tailscale_stats)
    
    def generate_report(self, ping_results, internet_speed, tailscale_stats):
        """生成诊断报告"""
        print("\n" + "=" * 50)
        print("📋 网络带宽诊断报告")
        print("=" * 50)
        
        print(f"\n🌐 互联网连接:")
        print(f"   📶 下载速度: {internet_speed:.2f} Mbps")
        
        print(f"\n🏓 网络延迟:")
        for name, latency in ping_results.items():
            if latency:
                status = "正常" if latency < 50 else "较高" if latency < 100 else "过高"
                print(f"   📡 {name}: {latency:.1f}ms ({status})")
        
        print(f"\n🔗 Tailscale使用情况:")
        if tailscale_stats:
            ts = tailscale_stats
            if ts['total_mb'] > 1:
                print(f"   ⚠️  Tailscale有显著流量: {ts['total_mb']:.2f}MB")
                print(f"   📥 下行: {ts['mbps_in']:.2f} Mbps")
                print(f"   📤 上行: {ts['mbps_out']:.2f} Mbps")
                print(f"\n💡 建议: Tailscale可能正在处理部分网络流量")
            else:
                print(f"   ✅ Tailscale流量很少: {ts['total_mb']:.2f}MB")
                print(f"   💡 建议: Tailscale对带宽影响很小")
        
        print(f"\n🎯 诊断结论:")
        if tailscale_stats and tailscale_stats['total_mb'] > 10:
            print("   ⚠️  Tailscale可能正在影响网络性能")
            print("   💡 建议进一步检查Tailscale配置和路由")
        else:
            print("   ✅ Tailscale对带宽影响较小")
            print("   💡 网络性能问题可能来自其他原因")
        
        print("\n📝 下一步建议:")
        print("   1. 如需详细监控，运行: python3 simple_bandwidth_test.py --monitor")
        print("   2. 检查其他VPN/代理软件")
        print("   3. 测试不同时间段的网络性能")

def main():
    import sys
    
    tester = NetworkBandwidthTester()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--monitor':
        print("🔍 开始持续监控Tailscale流量...")
        while True:
            try:
                tester.monitor_interface_traffic(60)
                print("\n⏳ 60秒后继续监控...\n")
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n👋 监控结束")
                break
    else:
        tester.comprehensive_test()

if __name__ == "__main__":
    main() 