#!/usr/bin/env python3
"""
邮件连接诊断工具
"""

import smtplib
import ssl
import json
import socket
from email.mime.text import MIMEText

def test_smtp_connection():
    """测试SMTP连接"""
    
    # 读取配置
    with open('notification_config.json', 'r') as f:
        config = json.load(f)
    
    email_config = config['email']
    
    print("🔧 邮件连接诊断工具")
    print("=" * 40)
    print(f"📧 发件人: {email_config['sender_email']}")
    print(f"📧 收件人: {email_config['recipient_email']}")
    print(f"🔗 SMTP服务器: {email_config['smtp_server']}:{email_config['smtp_port']}")
    print(f"🔑 授权码: {'已设置' if email_config['sender_password'] else '未设置'}")
    
    # 测试网络连接
    print("\n📡 测试网络连接...")
    try:
        socket.create_connection((email_config['smtp_server'], email_config['smtp_port']), timeout=10)
        print("✅ 网络连接正常")
    except Exception as e:
        print(f"❌ 网络连接失败: {e}")
        return False
    
    # 测试SMTP连接
    print("\n🔗 测试SMTP连接...")
    try:
        context = ssl.create_default_context()
        
        with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
            print("✅ SMTP服务器连接成功")
            
            if email_config['use_tls']:
                server.starttls(context=context)
                print("✅ TLS加密启用成功")
            
            # 测试登录
            server.login(email_config['sender_email'], email_config['sender_password'])
            print("✅ SMTP认证成功")
            
            # 发送测试邮件
            msg = MIMEText("这是RL-Swarm邮件系统的连接测试邮件。", 'plain', 'utf-8')
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = "🧪 RL-Swarm 邮件连接测试"
            
            server.sendmail(
                email_config['sender_email'],
                email_config['recipient_email'],
                msg.as_string()
            )
            print("✅ 测试邮件发送成功！")
            print("📬 请检查邮箱 zhilinchn@126.com")
            return True
            
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP认证失败")
        print("💡 建议:")
        print("   1. 检查邮箱地址是否正确")
        print("   2. 检查SMTP授权码是否正确")
        print("   3. 确认已开启SMTP服务")
        return False
        
    except smtplib.SMTPServerDisconnected:
        print("❌ SMTP服务器断开连接")
        print("💡 建议:")
        print("   1. 检查网络连接")
        print("   2. 尝试使用其他SMTP服务器")
        return False
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        print("💡 建议:")
        print("   1. 检查防火墙设置")
        print("   2. 尝试使用其他邮箱服务商")
        print("   3. 检查邮箱是否存在")
        return False

def suggest_email_setup():
    """建议邮箱设置"""
    print("\n📧 邮箱配置建议:")
    print("=" * 40)
    
    print("🔑 推荐邮箱服务商:")
    print("1. 126邮箱 (smtp.126.com:587)")
    print("   - 注册: https://mail.126.com")
    print("   - 设置路径: 设置 → POP3/SMTP/IMAP → 开启SMTP")
    
    print("\n2. QQ邮箱 (smtp.qq.com:587)")
    print("   - 注册: https://mail.qq.com")
    print("   - 设置路径: 设置 → 账户 → 开启SMTP")
    
    print("\n3. Gmail (smtp.gmail.com:587)")
    print("   - 需要二步验证")
    print("   - 生成应用专用密码")
    
    print("\n🛠️ 重新配置邮箱:")
    print("python setup_notifications.py")

if __name__ == "__main__":
    success = test_smtp_connection()
    
    if not success:
        suggest_email_setup()
        
        print("\n❓ 常见问题:")
        print("1. 邮箱 'rl_swarm_monitor@126.com' 可能不存在")
        print("2. 建议使用您自己的126邮箱或QQ邮箱")
        print("3. 确保授权码不是登录密码，而是SMTP专用授权码") 