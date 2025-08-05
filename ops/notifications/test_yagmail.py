#!/usr/bin/env python3
"""
使用yagmail开源库测试邮件发送
"""

import yagmail
import json

def test_yagmail_send():
    """用yagmail测试邮件发送"""
    
    # 读取配置
    with open('notification_config.json', 'r') as f:
        config = json.load(f)
    
    email_config = config['email']
    
    print("📧 使用yagmail测试邮件发送...")
    print(f"发件人: {email_config['sender_email']}")
    print(f"收件人: {email_config['recipient_email']}")
    
    try:
        # 使用yagmail发送邮件
        yag = yagmail.SMTP(
            user=email_config['sender_email'],
            password=email_config['sender_password'],
            host=email_config['smtp_server'],
            port=email_config['smtp_port']
        )
        
        # 发送HTML格式的测试邮件
        html_content = """
        <html>
        <body>
            <h2>🎉 RL-Swarm 邮件通知测试</h2>
            <p>恭喜！邮件通知系统配置成功！</p>
            
            <h3>📋 系统信息:</h3>
            <ul>
                <li>🖥️ 主机: Mac Mini M4</li>
                <li>📍 项目: RL-Swarm</li>
                <li>📧 使用库: yagmail (开源库)</li>
                <li>⏰ 测试时间: 现在</li>
            </ul>
            
            <h3>🔔 通知功能:</h3>
            <ul>
                <li>✅ 训练错误自动通知</li>
                <li>✅ 系统资源异常告警</li>
                <li>✅ 训练停滞检测</li>
                <li>✅ 性能监控报告</li>
            </ul>
            
            <p><strong>🚀 现在可以安心运行训练了！</strong></p>
            
            <hr>
            <p><em>此邮件由RL-Swarm监控系统自动发送</em></p>
        </body>
        </html>
        """
        
        yag.send(
            to=email_config['recipient_email'],
            subject='🎉 RL-Swarm 邮件通知测试成功',
            contents=html_content
        )
        
        print("✅ 邮件发送成功！")
        print("📬 请检查你的邮箱 zhilinchn@126.com")
        return True
        
    except Exception as e:
        print(f"❌ yagmail发送失败: {e}")
        
        # 尝试其他配置
        print("\n🔄 尝试备用配置...")
        try:
            # 尝试不同的端口配置
            yag2 = yagmail.SMTP(
                user=email_config['sender_email'],
                password=email_config['sender_password'],
                host='smtp.126.com',
                port=465,  # SSL端口
                smtp_ssl=True
            )
            
            yag2.send(
                to=email_config['recipient_email'],
                subject='🎉 RL-Swarm 邮件通知测试 (SSL)',
                contents='这是使用SSL端口465的测试邮件。'
            )
            
            print("✅ 使用SSL端口发送成功！")
            
            # 更新配置为SSL模式
            config['email']['smtp_port'] = 465
            config['email']['use_ssl'] = True
            config['email']['use_tls'] = False
            
            with open('notification_config.json', 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print("✅ 已更新配置为SSL模式")
            return True
            
        except Exception as e2:
            print(f"❌ SSL模式也失败: {e2}")
            return False

if __name__ == "__main__":
    success = test_yagmail_send()
    
    if success:
        print("\n🎊 邮件通知系统配置完成！")
        print("现在运行训练时，如果出现问题会自动发送邮件通知。")
    else:
        print("\n❓ 邮件发送仍然失败，可能的原因:")
        print("1. SMTP授权码不正确")
        print("2. 126邮箱的SMTP服务未开启")
        print("3. 网络防火墙阻止SMTP连接")
        print("4. 授权码已过期")
        print("\n🔧 建议:")
        print("1. 重新登录126邮箱生成新的授权码")
        print("2. 确认SMTP服务已开启")
        print("3. 尝试用其他网络环境") 