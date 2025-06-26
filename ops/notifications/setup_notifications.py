#!/usr/bin/env python3
"""
RL-Swarm 通知系统设置脚本
一键配置和测试邮件通知功能
"""

import os
import sys
import json
from notification_system import NotificationManager, setup_notification_config

def interactive_setup():
    """交互式设置通知系统"""
    print("🔧 RL-Swarm 通知系统设置向导")
    print("=" * 50)
    
    print("\n📧 邮件通知配置")
    print("默认收件人邮箱: zhilinchn@126.com")
    print("如需修改收件人，请编辑 notification_config.json")
    
    print("\n📝 发件人邮箱设置:")
    print("推荐使用专门的监控邮箱（如126邮箱、QQ邮箱等）")
    
    sender_email = input("输入发件人邮箱 (留空使用默认): ").strip()
    if not sender_email:
        sender_email = "rl_swarm_monitor@126.com"
    
    print(f"\n🔑 邮箱授权码设置:")
    print("注意: 这里需要的不是邮箱登录密码，而是SMTP授权码")
    print("获取方式:")
    print("- 126邮箱: 设置 → POP3/SMTP/IMAP → 开启SMTP服务 → 获取授权码")
    print("- QQ邮箱: 设置 → 账户 → 开启SMTP服务 → 获取授权码")
    print("- Gmail: 需要开启二步验证并生成应用密码")
    
    sender_password = input("输入SMTP授权码 (留空跳过邮件配置): ").strip()
    
    # 保存配置
    config = {
        "email": {
            "enabled": bool(sender_password),
            "smtp_server": "smtp.126.com" if "126" in sender_email else ("smtp.qq.com" if "qq" in sender_email else "smtp.gmail.com"),
            "smtp_port": 587,
            "sender_email": sender_email,
            "sender_password": sender_password,
            "recipient_email": "zhilinchn@126.com",
            "use_tls": True
        },
        "sms": {
            "enabled": False,
            "provider": "aliyun",
            "api_key": "",
            "api_secret": "",
            "phone_number": "",
            "template_id": ""
        },
        "alert_levels": {
            "critical": "🚨",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
    }
    
    # 保存配置文件
    with open("notification_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n✅ 配置已保存到 notification_config.json")
    
    if sender_password:
        print("\n🧪 开始测试邮件发送...")
        test_email()
    else:
        print("\n⚠️ 未配置邮件密码，跳过邮件测试")
        print("配置完成后可运行: python test_notification.py quick")

def test_email():
    """测试邮件发送"""
    try:
        notifier = NotificationManager()
        
        title = "🎉 RL-Swarm 通知系统配置成功"
        message = """恭喜！RL-Swarm 通知系统已成功配置。

🖥️ 主机: Mac Mini M4
📍 项目: /Users/mac/work/gensyn/rl-swarm
⏰ 配置时间: """ + f"{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        message += """

🔔 通知功能:
✅ 训练错误自动通知
✅ 系统资源异常告警
✅ 训练停滞检测
✅ 性能监控报告

现在可以安心运行训练，系统会在出现问题时及时通知您！

🚀 启动训练: ./run_rl_swarm_mac.sh
📊 监控面板: python real_time_monitor.py"""

        success = notifier.send_alert(title, message, "info")
        
        if success:
            print("✅ 测试邮件发送成功！")
            print("📬 请检查邮箱 zhilinchn@126.com")
            return True
        else:
            print("❌ 测试邮件发送失败，请检查配置")
            return False
            
    except Exception as e:
        print(f"❌ 邮件测试失败: {e}")
        return False

def quick_setup_with_defaults():
    """使用默认配置快速设置（不配置邮件密码）"""
    print("⚡ 快速设置通知系统（默认配置）...")
    
    config = {
        "email": {
            "enabled": False,  # 默认禁用，需要用户手动配置密码
            "smtp_server": "smtp.126.com",
            "smtp_port": 587,
            "sender_email": "rl_swarm_monitor@126.com",
            "sender_password": "",
            "recipient_email": "zhilinchn@126.com",
            "use_tls": True
        },
        "sms": {
            "enabled": False,
            "provider": "aliyun",
            "api_key": "",
            "api_secret": "",
            "phone_number": "",
            "template_id": ""
        },
        "alert_levels": {
            "critical": "🚨",
            "error": "❌", 
            "warning": "⚠️",
            "info": "ℹ️"
        }
    }
    
    with open("notification_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ 默认配置已保存")
    print("📝 若要启用邮件通知，请运行: python setup_notifications.py")

def show_usage():
    """显示使用说明"""
    print("""
🔧 RL-Swarm 通知系统使用说明
=========================================

📧 邮件通知功能:
- 训练错误自动通知
- 系统资源异常告警  
- 训练停滞检测
- 性能监控报告

🚀 快速开始:
1. 配置通知系统:  python setup_notifications.py
2. 测试邮件发送:  python test_notification.py quick
3. 启动监控系统:  python real_time_monitor.py

📱 短信通知 (预留接口):
- 支持阿里云、腾讯云、Twilio
- 需要在 notification_config.json 中配置API密钥

⚙️ 配置文件: notification_config.json
📋 测试脚本: test_notification.py
📊 监控系统: real_time_monitor.py (已集成通知功能)

🔗 集成状态:
✅ 实时监控系统已集成邮件通知
✅ 训练脚本已集成异常检测
✅ 预防性修复系统已部署

遇到问题？查看日志: logs/preemptive_fixes.log
""")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_setup_with_defaults()
        elif sys.argv[1] == "test":
            test_email()
        elif sys.argv[1] == "help":
            show_usage()
        else:
            print("用法:")
            print("  python setup_notifications.py        # 完整配置")
            print("  python setup_notifications.py quick  # 快速设置默认配置")
            print("  python setup_notifications.py test   # 测试邮件发送")
            print("  python setup_notifications.py help   # 显示帮助")
    else:
        interactive_setup()

if __name__ == "__main__":
    main() 