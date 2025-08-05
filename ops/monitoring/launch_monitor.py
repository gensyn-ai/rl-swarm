#!/usr/bin/env python3
"""
RL-Swarm 综合监控启动器
一键启动所有监控和可视化功能
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

def print_banner():
    """显示启动横幅"""
    print("\033[38;5;226m")
    print("""
🌟 ==========================================
🚀 RL-Swarm 综合监控中心
📱 专为 Mac Mini M4 优化
🌟 ==========================================
    """)
    print("\033[0m")

def check_files():
    """检查必要文件是否存在"""
    required_files = [
        "reward_tracker.py",
        "interactive_dashboard.py", 
        "real_time_monitor.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    print("✅ 所有必要文件检查完成")
    return True

def show_menu():
    """显示菜单选项"""
    print("\n🎯 请选择要启动的功能:")
    print("1. 🔥 启动实时监控服务器 (http://localhost:5000)")
    print("2. 📊 生成基础奖励报告")
    print("3. 🎪 生成超级交互式仪表板")
    print("4. 🎬 生成增强版演示仪表板")
    print("5. 🌈 启动所有功能")
    print("6. 📱 查看现有报告")
    print("0. ❌ 退出")
    
    return input("\n👆 请输入选项 (0-6): ").strip()

def start_real_time_monitor():
    """启动实时监控"""
    print("🚀 启动实时监控服务器...")
    try:
        process = subprocess.Popen([
            sys.executable, "-m", "real_time_monitor"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        time.sleep(3)
        
        # 打开浏览器
        webbrowser.open("http://localhost:5000")
        print("✅ 实时监控已启动: http://localhost:5000")
        
        return process
    except Exception as e:
        print(f"❌ 启动实时监控失败: {e}")
        return None

def generate_basic_report():
    """生成基础奖励报告"""
    print("📊 生成基础奖励报告...")
    try:
        result = subprocess.run([
            sys.executable, "reward_tracker.py", "--auto-open"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 基础奖励报告生成完成")
        else:
            print(f"❌ 报告生成失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 生成报告出错: {e}")

def generate_interactive_dashboard():
    """生成超级交互式仪表板"""
    print("🎪 生成超级交互式仪表板...")
    try:
        result = subprocess.run([
            sys.executable, "interactive_dashboard.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 超级交互式仪表板生成完成")
            webbrowser.open("super_interactive_dashboard.html")
        else:
            print(f"❌ 仪表板生成失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 生成仪表板出错: {e}")

def generate_enhanced_demo():
    """生成增强版演示仪表板"""
    print("🎬 生成增强版演示仪表板...")
    try:
        result = subprocess.run([
            sys.executable, "enhanced_reward_demo.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 增强版演示仪表板生成完成")
            # 打开报告
            time.sleep(1)
            webbrowser.open("comprehensive_reward_dashboard.html")
            webbrowser.open("detailed_reward_report.html")
        else:
            print(f"❌ 演示仪表板生成失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 生成演示仪表板出错: {e}")

def view_existing_reports():
    """查看现有报告"""
    html_files = list(Path(".").glob("*.html"))
    
    if not html_files:
        print("📭 没有找到现有报告")
        return
    
    print(f"\n📋 找到 {len(html_files)} 个报告文件:")
    for i, file in enumerate(html_files, 1):
        print(f"{i}. {file.name}")
    
    choice = input(f"\n选择要打开的报告 (1-{len(html_files)}) 或按回车查看全部: ").strip()
    
    if choice == "":
        # 打开所有报告
        print("🌈 打开所有报告...")
        for file in html_files:
            webbrowser.open(str(file))
            time.sleep(0.5)  # 避免同时打开太多标签
    elif choice.isdigit() and 1 <= int(choice) <= len(html_files):
        selected_file = html_files[int(choice) - 1]
        print(f"📊 打开报告: {selected_file.name}")
        webbrowser.open(str(selected_file))
    else:
        print("❌ 无效选择")

def start_all_functions():
    """启动所有功能"""
    print("🌈 启动所有功能...")
    
    # 生成所有报告
    print("\n1/4 📊 生成基础报告...")
    generate_basic_report()
    
    print("\n2/4 🎪 生成交互式仪表板...")
    generate_interactive_dashboard()
    
    print("\n3/4 🎬 生成演示仪表板...")
    generate_enhanced_demo()
    
    print("\n4/4 🔥 启动实时监控...")
    monitor_process = start_real_time_monitor()
    
    print("\n🎉 所有功能已启动!")
    print("\n📱 可以通过以下方式访问:")
    print("   • 实时监控: http://localhost:5000")
    print("   • 所有报告将在浏览器中自动打开")
    
    if monitor_process:
        try:
            print("\n按 Ctrl+C 停止监控服务器...")
            monitor_process.wait()
        except KeyboardInterrupt:
            print("\n⏹️ 正在停止监控服务器...")
            monitor_process.terminate()
            monitor_process.wait()
            print("✅ 监控服务器已停止")

def show_help():
    """显示帮助信息"""
    print("""
🆘 RL-Swarm 监控系统帮助

📋 功能说明:
1. 实时监控: 监控训练过程和系统性能，提供Web界面
2. 基础报告: 生成每日奖励统计表格和图表
3. 交互式仪表板: 超级动态的多图表可视化
4. 演示仪表板: 包含30天模拟数据的完整展示
5. 启动所有功能: 一键生成所有报告并启动监控

🎮 快捷键 (在交互式仪表板中):
• Ctrl/Cmd + R: 切换自动刷新
• Ctrl/Cmd + F: 全屏模式
• 鼠标滚轮: 缩放图表
• 拖拽: 平移图表

📊 报告文件:
• reward_summary_table.html: 基础奖励表格
• reward_dashboard.html: 基础图表
• super_interactive_dashboard.html: 超级交互式仪表板
• comprehensive_reward_dashboard.html: 完整演示仪表板
• detailed_reward_report.html: 详细统计报告

🔧 故障排除:
• 确保 RL-Swarm 正在运行
• 检查 logs/ 目录是否存在
• 确保端口 5000 未被占用
    """)

def main():
    """主函数"""
    print_banner()
    
    # 检查文件
    if not check_files():
        sys.exit(1)
    
    while True:
        try:
            choice = show_menu()
            
            if choice == "0":
                print("👋 再见！感谢使用 RL-Swarm 监控系统")
                break
            elif choice == "1":
                monitor_process = start_real_time_monitor()
                if monitor_process:
                    try:
                        print("按 Ctrl+C 返回主菜单...")
                        monitor_process.wait()
                    except KeyboardInterrupt:
                        print("\n⏹️ 停止监控服务器...")
                        monitor_process.terminate()
                        monitor_process.wait()
            elif choice == "2":
                generate_basic_report()
            elif choice == "3":
                generate_interactive_dashboard()
            elif choice == "4":
                generate_enhanced_demo()
            elif choice == "5":
                start_all_functions()
                break  # 启动所有功能后退出
            elif choice == "6":
                view_existing_reports()
            elif choice.lower() in ["help", "h", "?"]:
                show_help()
            else:
                print("❌ 无效选择，请重试")
            
            if choice != "5":  # 除了启动所有功能，其他操作完成后继续显示菜单
                input("\n按回车键继续...")
        
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {e}")
            input("按回车键继续...")

if __name__ == "__main__":
    main() 