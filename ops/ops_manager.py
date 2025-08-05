#!/usr/bin/env python3
"""
RL-Swarm 运维管理中心
统一管理所有运维功能的控制台
"""

import os
import sys
import subprocess
from pathlib import Path

# 获取ops目录的绝对路径
OPS_DIR = Path(__file__).parent.absolute()
ROOT_DIR = OPS_DIR.parent

def run_command(cmd, cwd=None):
    """执行命令并显示结果"""
    if cwd is None:
        cwd = ROOT_DIR
    
    print(f"🔧 执行: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 执行成功")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ 执行失败")
            if result.stderr:
                print(result.stderr)
    except Exception as e:
        print(f"❌ 执行异常: {e}")

def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("🚀 RL-Swarm 运维管理中心")
    print("="*60)
    
    print("\n🔧 系统修复与检查:")
    print("  1. Apple Silicon兼容性修复")
    print("  2. 依赖问题修复")
    print("  3. 系统预防性检查")
    
    print("\n📧 邮件通知系统:")
    print("  4. 配置邮件通知")
    print("  5. 测试邮件发送")
    print("  6. 邮件诊断工具")
    
    print("\n📊 监控与可视化:")
    print("  7. 启动实时监控")
    print("  8. 生成交互式仪表板")
    print("  9. 启动监控管理器")
    print(" 10. 奖励数据追踪")
    
    print("\n🚀 训练管理:")
    print(" 11. 启动Mac优化训练")
    print(" 12. 启动多节点训练")
    print(" 13. 测试监控功能")
    
    print("\n📁 文件管理:")
    print(" 14. 查看运维文档")
    print(" 15. 查看系统状态")
    print(" 16. 清理临时文件")
    
    print("\n 0. 退出")
    print("="*60)

def apple_silicon_fix():
    """Apple Silicon兼容性修复"""
    print("🔧 Apple Silicon兼容性修复...")
    run_command(f"python {OPS_DIR}/fixes/fix_mac_accelerate.py")

def dependency_fix():
    """依赖问题修复"""
    print("🔧 依赖问题修复...")
    run_command(f"chmod +x {OPS_DIR}/fixes/fix_mac_dependencies.sh && {OPS_DIR}/fixes/fix_mac_dependencies.sh")

def preemptive_check():
    """系统预防性检查"""
    print("🛡️ 系统预防性检查...")
    run_command(f"python {OPS_DIR}/fixes/preemptive_fixes.py")

def setup_notifications():
    """配置邮件通知"""
    print("📧 配置邮件通知...")
    run_command(f"python {OPS_DIR}/notifications/setup_notifications.py")

def test_email():
    """测试邮件发送"""
    print("📧 测试邮件发送...")
    run_command(f"python {OPS_DIR}/notifications/test_yagmail.py")

def diagnose_email():
    """邮件诊断工具"""
    print("🔍 邮件诊断工具...")
    run_command(f"python {OPS_DIR}/notifications/diagnose_email.py")

def start_monitor():
    """启动实时监控"""
    print("📊 启动实时监控...")
    print("🌐 监控面板将在 http://localhost:5000 启动")
    run_command(f"python {OPS_DIR}/monitoring/real_time_monitor.py")

def generate_dashboard():
    """生成交互式仪表板"""
    print("📊 生成交互式仪表板...")
    run_command(f"python {OPS_DIR}/monitoring/interactive_dashboard.py")

def launch_monitor_manager():
    """启动监控管理器"""
    print("📊 启动监控管理器...")
    run_command(f"python {OPS_DIR}/monitoring/launch_monitor.py")

def track_rewards():
    """奖励数据追踪"""
    print("💰 奖励数据追踪...")
    run_command(f"python {OPS_DIR}/monitoring/reward_tracker.py")

def start_mac_training():
    """启动Mac优化训练"""
    print("🚀 启动Mac优化训练...")
    print("🔧 自动应用Apple Silicon兼容性修复...")
    run_command(f"chmod +x {OPS_DIR}/scripts/run_rl_swarm_mac.sh && {OPS_DIR}/scripts/run_rl_swarm_mac.sh")

def start_multinode_training():
    """启动多节点训练"""
    print("🚀 启动多节点训练...")
    run_command(f"chmod +x {OPS_DIR}/scripts/start_all_nodes.sh && {OPS_DIR}/scripts/start_all_nodes.sh")

def test_monitoring():
    """测试监控功能"""
    print("🧪 测试监控功能...")
    run_command(f"python {OPS_DIR}/monitoring/test_monitor.py")

def show_docs():
    """查看运维文档"""
    print("📚 运维文档列表:")
    docs_dir = OPS_DIR / "docs"
    if docs_dir.exists():
        for doc in docs_dir.glob("*.md"):
            print(f"   📄 {doc.name}")
        print(f"\n📁 文档位置: {docs_dir}")
    else:
        print("❌ 文档目录不存在")

def show_status():
    """查看系统状态"""
    print("📋 系统状态:")
    
    # 检查各组件状态
    components = {
        "Apple Silicon修复": f"{OPS_DIR}/fixes/fix_mac_accelerate.py",
        "邮件通知配置": f"{OPS_DIR}/config/notification_config.json",
        "实时监控": f"{OPS_DIR}/monitoring/real_time_monitor.py",
        "训练脚本": f"{OPS_DIR}/scripts/run_rl_swarm_mac.sh",
    }
    
    for name, path in components.items():
        if os.path.exists(path):
            print(f"   ✅ {name}")
        else:
            print(f"   ❌ {name} (文件不存在)")
    
    # 检查数据库
    db_files = [
        OPS_DIR / "monitoring" / "realtime_data.db",
        OPS_DIR / "monitoring" / "rewards.db"
    ]
    
    print("\n💾 数据库状态:")
    for db in db_files:
        if db.exists():
            size = db.stat().st_size / 1024  # KB
            print(f"   ✅ {db.name} ({size:.1f} KB)")
        else:
            print(f"   ❌ {db.name} (不存在)")

def cleanup_temp():
    """清理临时文件"""
    print("🧹 清理临时文件...")
    
    temp_patterns = [
        "*.pyc",
        "__pycache__",
        "*.log",
        "*.tmp"
    ]
    
    for pattern in temp_patterns:
        run_command(f"find {ROOT_DIR} -name '{pattern}' -delete")
    
    print("✅ 临时文件清理完成")

def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("\n请选择操作 (0-16): ").strip()
            
            if choice == "0":
                print("👋 退出运维管理中心")
                break
            elif choice == "1":
                apple_silicon_fix()
            elif choice == "2":
                dependency_fix()
            elif choice == "3":
                preemptive_check()
            elif choice == "4":
                setup_notifications()
            elif choice == "5":
                test_email()
            elif choice == "6":
                diagnose_email()
            elif choice == "7":
                start_monitor()
            elif choice == "8":
                generate_dashboard()
            elif choice == "9":
                launch_monitor_manager()
            elif choice == "10":
                track_rewards()
            elif choice == "11":
                start_mac_training()
            elif choice == "12":
                start_multinode_training()
            elif choice == "13":
                test_monitoring()
            elif choice == "14":
                show_docs()
            elif choice == "15":
                show_status()
            elif choice == "16":
                cleanup_temp()
            else:
                print("❌ 无效选择，请重新输入")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，退出运维管理中心")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")
        
        input("\n按回车键继续...")

if __name__ == "__main__":
    main() 