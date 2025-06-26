#!/usr/bin/env python3
"""
通知系统测试脚本
测试邮件和短信通知功能
"""

import sys
import traceback
from datetime import datetime
from notification_system import NotificationManager, setup_notification_config

def test_email_notification():
    """测试邮件通知功能"""
    print("📧 测试邮件通知功能...")
    
    try:
        # 初始化通知管理器
        notifier = NotificationManager()
        
        # 测试不同级别的通知
        test_cases = [
            {
                "level": "info",
                "title": "系统测试 - 信息通知",
                "message": "这是一条测试信息，验证邮件通知系统工作正常。"
            },
            {
                "level": "warning", 
                "title": "系统测试 - 警告通知",
                "message": "这是一条测试警告，验证警告级别邮件的显示效果。"
            },
            {
                "level": "error",
                "title": "系统测试 - 错误通知", 
                "message": "这是一条测试错误，验证错误级别邮件的显示效果。"
            },
            {
                "level": "critical",
                "title": "系统测试 - 紧急通知",
                "message": "这是一条测试紧急通知，验证最高级别告警的显示效果。"
            }
        ]
        
        success_count = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 测试 {i}/4: {test_case['level'].upper()} 级别通知")
            
            success = notifier.send_alert(
                title=test_case["title"],
                message=test_case["message"], 
                alert_level=test_case["level"],
                send_email=True,
                send_sms=False
            )
            
            if success:
                print(f"✅ {test_case['level']} 级别通知发送成功")
                success_count += 1
            else:
                print(f"❌ {test_case['level']} 级别通知发送失败")
            
            # 避免发送过快
            import time
            time.sleep(2)
        
        print(f"\n📊 测试结果: {success_count}/4 成功")
        return success_count == 4
        
    except Exception as e:
        print(f"❌ 邮件测试失败: {e}")
        traceback.print_exc()
        return False

def test_training_error_notification():
    """测试训练错误通知"""
    print("\n🚨 测试训练错误通知...")
    
    try:
        notifier = NotificationManager()
        
        # 模拟训练错误
        error_message = "UnboundLocalError: cannot access local variable 'current_batch'"
        stack_trace = """Traceback (most recent call last):
  File "hivemind_exp/gsm8k/train_single_gpu.py", line 67, in <module>
    main()
  File "hivemind_exp/trainer/hivemind_grpo_trainer.py", line 338, in train
    self._train()
  File ".venv/lib/python3.11/site-packages/accelerate/data_loader.py", line 576
    UnboundLocalError: cannot access local variable 'current_batch'"""
        
        success = notifier.send_training_error(error_message, stack_trace)
        
        if success:
            print("✅ 训练错误通知发送成功")
            return True
        else:
            print("❌ 训练错误通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 训练错误通知测试失败: {e}")
        return False

def test_system_warning_notification():
    """测试系统警告通知"""
    print("\n⚠️ 测试系统警告通知...")
    
    try:
        notifier = NotificationManager()
        
        # 模拟系统警告
        warning_details = """内存使用率: 85%
磁盘空间: 2.1GB 剩余
CPU温度: 82°C
网络连接: 正常

建议:
- 清理内存或重启系统
- 清理磁盘空间
- 检查散热情况"""
        
        success = notifier.send_system_warning("资源使用率过高", warning_details)
        
        if success:
            print("✅ 系统警告通知发送成功")
            return True
        else:
            print("❌ 系统警告通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 系统警告通知测试失败: {e}")
        return False

def test_training_complete_notification():
    """测试训练完成通知"""
    print("\n🎉 测试训练完成通知...")
    
    try:
        notifier = NotificationManager()
        
        # 模拟训练完成
        performance_stats = """训练轮次: 1000
总训练时间: 2小时45分钟
平均奖励: 0.85
最佳奖励: 0.92
内存峰值: 12.3GB
CPU平均使用率: 68%"""
        
        success = notifier.send_training_complete(1000, performance_stats)
        
        if success:
            print("✅ 训练完成通知发送成功")
            return True
        else:
            print("❌ 训练完成通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 训练完成通知测试失败: {e}")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🧪 RL-Swarm 通知系统测试")
    print("=" * 50)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查配置
    try:
        notifier = NotificationManager()
        config = notifier.config_manager.config
        
        if not config["email"]["sender_password"]:
            print("\n⚠️ 邮件密码未配置，请先配置通知系统!")
            print("运行: python notification_system.py")
            return False
            
        print(f"\n📧 邮件配置:")
        print(f"   发件人: {config['email']['sender_email']}")
        print(f"   收件人: {config['email']['recipient_email']}")
        print(f"   SMTP服务器: {config['email']['smtp_server']}:{config['email']['smtp_port']}")
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False
    
    # 执行测试
    tests = [
        ("基础邮件通知", test_email_notification),
        ("训练错误通知", test_training_error_notification), 
        ("系统警告通知", test_system_warning_notification),
        ("训练完成通知", test_training_complete_notification),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {e}")
            results[test_name] = False
    
    # 测试总结
    print(f"\n{'='*50}")
    print("📋 测试总结:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 总体结果: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！邮件通知系统工作正常。")
        print("📬 请检查邮箱 zhilinchn@126.com 查看测试邮件")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接")
    
    return passed == total

def quick_test():
    """快速测试 - 只发送一封测试邮件"""
    print("⚡ 快速测试邮件发送...")
    
    try:
        notifier = NotificationManager()
        
        title = "RL-Swarm 通知系统测试"
        message = f"""这是一封测试邮件，用于验证RL-Swarm通知系统是否工作正常。

🕒 发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ 发送主机: Mac Mini M4
📍 项目位置: /Users/mac/work/gensyn/rl-swarm

如果您收到这封邮件，说明通知系统配置成功！

🎉 系统准备就绪，可以开始监控RL-Swarm训练了。"""
        
        success = notifier.send_alert(title, message, "info")
        
        if success:
            print("✅ 测试邮件发送成功！")
            print("📬 请检查邮箱 zhilinchn@126.com")
            return True
        else:
            print("❌ 测试邮件发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 快速测试失败: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_test()
        elif sys.argv[1] == "config":
            setup_notification_config()
        else:
            print("用法:")
            print("  python test_notification.py           # 运行完整测试")
            print("  python test_notification.py quick     # 快速测试")
            print("  python test_notification.py config    # 配置通知系统")
    else:
        run_all_tests()

if __name__ == "__main__":
    main() 