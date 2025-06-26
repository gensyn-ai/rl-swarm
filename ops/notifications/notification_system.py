#!/usr/bin/env python3
"""
RL-Swarm 通知系统
支持邮件和短信通知，用于项目异常中断时的告警
"""

import smtplib
import ssl
import json
import os
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path
import logging

class NotificationConfig:
    """通知配置管理"""
    
    def __init__(self, config_file="notification_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        default_config = {
            "email": {
                "enabled": True,
                "smtp_server": "smtp.126.com",
                "smtp_port": 587,
                "sender_email": "rl_swarm_monitor@126.com",
                "sender_password": "",  # 需要用户设置
                "recipient_email": "zhilinchn@126.com",
                "use_tls": True
            },
            "sms": {
                "enabled": False,
                "provider": "aliyun",  # 支持 aliyun, tencent, twilio
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
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                # 合并配置
                default_config.update(saved_config)
            except Exception as e:
                print(f"配置文件加载失败: {e}")
        
        return default_config
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"配置文件保存失败: {e}")
    
    def setup_email(self, sender_email=None, sender_password=None, recipient_email=None):
        """设置邮件配置"""
        if sender_email:
            self.config["email"]["sender_email"] = sender_email
        if sender_password:
            self.config["email"]["sender_password"] = sender_password
        if recipient_email:
            self.config["email"]["recipient_email"] = recipient_email
        
        self.save_config()

class EmailNotifier:
    """邮件通知器"""
    
    def __init__(self, config):
        self.config = config["email"]
        self.logger = logging.getLogger(__name__)
    
    def send_email(self, subject, body, alert_level="info"):
        """发送邮件"""
        if not self.config["enabled"]:
            self.logger.info("邮件通知已禁用")
            return False
        
        if not self.config["sender_password"]:
            self.logger.error("邮件密码未设置，无法发送邮件")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            
            # 设置发件人（带名称）
            alert_icon = NotificationConfig().config["alert_levels"].get(alert_level, "📧")
            sender_name = f"RL-Swarm监控系统 {alert_icon}"
            msg['From'] = formataddr((sender_name, self.config["sender_email"]))
            msg['To'] = self.config["recipient_email"]
            
            # 设置醒目的标题
            priority_prefix = {
                "critical": "🚨【紧急】",
                "error": "❌【错误】", 
                "warning": "⚠️【警告】",
                "info": "ℹ️【信息】"
            }.get(alert_level, "📧")
            
            msg['Subject'] = f"{priority_prefix} {subject}"
            
            # 添加优先级标记
            if alert_level in ["critical", "error"]:
                msg['X-Priority'] = '1'  # 高优先级
                msg['X-MSMail-Priority'] = 'High'
            
            # 构建HTML邮件内容
            html_body = self._create_html_body(subject, body, alert_level)
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # 发送邮件
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"]) as server:
                if self.config["use_tls"]:
                    server.starttls(context=context)
                
                server.login(self.config["sender_email"], self.config["sender_password"])
                server.sendmail(
                    self.config["sender_email"], 
                    self.config["recipient_email"], 
                    msg.as_string()
                )
            
            self.logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    def _create_html_body(self, subject, body, alert_level):
        """创建HTML邮件内容"""
        colors = {
            "critical": "#dc3545",
            "error": "#fd7e14", 
            "warning": "#ffc107",
            "info": "#0dcaf0"
        }
        
        color = colors.get(alert_level, "#6c757d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ background-color: #f8f9fa; padding: 20px; border-left: 4px solid {color}; margin: 20px 0; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .timestamp {{ color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🤖 RL-Swarm 监控告警</h2>
                <p class="timestamp">⏰ {timestamp}</p>
            </div>
            
            <div class="content">
                <h3>📋 告警详情</h3>
                <p><strong>标题:</strong> {subject}</p>
                <hr>
                <pre style="white-space: pre-wrap; font-family: monospace; background: #fff; padding: 10px; border-radius: 3px;">{body}</pre>
            </div>
            
            <div class="footer">
                <p>🖥️ 主机: Mac Mini M4</p>
                <p>📍 位置: /Users/mac/work/gensyn/rl-swarm</p>
                <p>🔧 监控系统: RL-Swarm Monitor v1.0</p>
                <hr>
                <p><em>此邮件由RL-Swarm监控系统自动发送，请勿回复</em></p>
            </div>
        </body>
        </html>
        """
        
        return html

class SMSNotifier:
    """短信通知器（预留接口）"""
    
    def __init__(self, config):
        self.config = config["sms"]
        self.logger = logging.getLogger(__name__)
    
    def send_sms(self, message, alert_level="info"):
        """发送短信（预留接口）"""
        if not self.config["enabled"]:
            self.logger.info("短信通知已禁用")
            return False
        
        # TODO: 根据provider实现不同的短信发送逻辑
        provider = self.config["provider"]
        
        if provider == "aliyun":
            return self._send_aliyun_sms(message, alert_level)
        elif provider == "tencent":
            return self._send_tencent_sms(message, alert_level)
        elif provider == "twilio":
            return self._send_twilio_sms(message, alert_level)
        else:
            self.logger.error(f"不支持的短信服务提供商: {provider}")
            return False
    
    def _send_aliyun_sms(self, message, alert_level):
        """阿里云短信接口"""
        # TODO: 实现阿里云短信SDK
        self.logger.info("阿里云短信接口待实现")
        return False
    
    def _send_tencent_sms(self, message, alert_level):
        """腾讯云短信接口"""
        # TODO: 实现腾讯云短信SDK
        self.logger.info("腾讯云短信接口待实现")
        return False
    
    def _send_twilio_sms(self, message, alert_level):
        """Twilio短信接口"""
        # TODO: 实现Twilio短信SDK
        self.logger.info("Twilio短信接口待实现")
        return False

class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config_file="notification_config.json"):
        self.config_manager = NotificationConfig(config_file)
        self.email_notifier = EmailNotifier(self.config_manager.config)
        self.sms_notifier = SMSNotifier(self.config_manager.config)
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, title, message, alert_level="error", send_email=True, send_sms=False):
        """发送告警通知"""
        success = True
        
        if send_email:
            email_success = self.email_notifier.send_email(title, message, alert_level)
            success = success and email_success
        
        if send_sms:
            sms_success = self.sms_notifier.send_sms(f"{title}\n{message}", alert_level)
            success = success and sms_success
        
        return success
    
    def send_training_error(self, error_message, stack_trace=None):
        """发送训练错误通知"""
        title = "RL-Swarm 训练中断"
        
        body = f"""训练过程中发生错误，请及时检查！

🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🖥️ 主机: Mac Mini M4
📍 项目: RL-Swarm

❌ 错误信息:
{error_message}
"""
        
        if stack_trace:
            body += f"""
📊 堆栈跟踪:
{stack_trace}
"""
        
        body += """
🔧 建议操作:
1. 检查日志文件: logs/swarm.log
2. 检查系统资源使用情况
3. 重新运行: ./run_rl_swarm_mac.sh
4. 查看监控面板: http://localhost:5000

如需技术支持，请保存此邮件内容。
"""
        
        return self.send_alert(title, body, "critical", send_email=True, send_sms=False)
    
    def send_system_warning(self, warning_type, details):
        """发送系统警告"""
        title = f"系统警告: {warning_type}"
        
        body = f"""系统检测到异常情况，请注意！

🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚠️ 警告类型: {warning_type}

📋 详情:
{details}

建议及时检查系统状态。
"""
        
        return self.send_alert(title, body, "warning", send_email=True, send_sms=False)
    
    def send_training_complete(self, round_num, performance_stats):
        """发送训练完成通知"""
        title = f"RL-Swarm 训练完成 - 轮次 {round_num}"
        
        body = f"""训练成功完成！

🕒 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 训练轮次: {round_num}

📊 性能统计:
{performance_stats}

🎉 训练任务圆满完成！
"""
        
        return self.send_alert(title, body, "info", send_email=True, send_sms=False)

def setup_notification_config():
    """交互式设置通知配置"""
    config_manager = NotificationConfig()
    
    print("🔧 RL-Swarm 通知系统配置")
    print("=" * 40)
    
    # 邮件配置
    print("\n📧 邮件配置:")
    sender_email = input(f"发件人邮箱 [{config_manager.config['email']['sender_email']}]: ").strip()
    if sender_email:
        config_manager.config['email']['sender_email'] = sender_email
    
    sender_password = input("发件人邮箱密码 (SMTP授权码): ").strip()
    if sender_password:
        config_manager.config['email']['sender_password'] = sender_password
    
    recipient_email = input(f"收件人邮箱 [{config_manager.config['email']['recipient_email']}]: ").strip()
    if recipient_email:
        config_manager.config['email']['recipient_email'] = recipient_email
    
    config_manager.save_config()
    print("✅ 配置已保存")
    
    return config_manager

if __name__ == "__main__":
    # 交互式配置
    setup_notification_config() 