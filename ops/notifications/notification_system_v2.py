#!/usr/bin/env python3
"""
RL-Swarm 通知系统 v2.0
使用yagmail开源库，支持邮件和短信通知
"""

import yagmail
import json
import os
import time
from datetime import datetime
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
                "sender_email": "zhilinchn@126.com",
                "sender_password": "",
                "recipient_email": "zhilinchn@126.com",
                "use_tls": True,
                "use_ssl": False
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

class YagmailNotifier:
    """基于yagmail的邮件通知器"""
    
    def __init__(self, config):
        self.config = config["email"]
        self.logger = logging.getLogger(__name__)
        self._yag = None
        
    def _get_yagmail_client(self):
        """获取yagmail客户端（延迟初始化）"""
        if self._yag is None:
            try:
                if self.config.get('use_ssl', False):
                    # SSL模式
                    self._yag = yagmail.SMTP(
                        user=self.config['sender_email'],
                        password=self.config['sender_password'],
                        host=self.config['smtp_server'],
                        port=self.config['smtp_port'],
                        smtp_ssl=True
                    )
                else:
                    # TLS模式
                    self._yag = yagmail.SMTP(
                        user=self.config['sender_email'],
                        password=self.config['sender_password'],
                        host=self.config['smtp_server'],
                        port=self.config['smtp_port']
                    )
            except Exception as e:
                self.logger.error(f"初始化yagmail客户端失败: {e}")
                return None
        return self._yag
    
    def send_email(self, subject, body, alert_level="info"):
        """发送邮件"""
        if not self.config["enabled"]:
            self.logger.info("邮件通知已禁用")
            return False
        
        if not self.config["sender_password"]:
            self.logger.error("邮件密码未设置，无法发送邮件")
            return False
        
        try:
            yag = self._get_yagmail_client()
            if yag is None:
                return False
            
            # 设置醒目的标题
            alert_icons = {
                "critical": "🚨【紧急】",
                "error": "❌【错误】", 
                "warning": "⚠️【警告】",
                "info": "ℹ️【信息】"
            }
            
            icon = alert_icons.get(alert_level, "📧")
            full_subject = f"{icon} {subject}"
            
            # 创建HTML邮件内容
            html_body = self._create_html_body(subject, body, alert_level)
            
            # 发送邮件
            yag.send(
                to=self.config["recipient_email"],
                subject=full_subject,
                contents=html_body
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
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 25px; line-height: 1.6; }}
                .footer {{ background: #f1f3f4; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .alert-box {{ background: #f8f9fa; border-left: 4px solid {color}; padding: 15px; margin: 15px 0; }}
                .timestamp {{ font-size: 14px; opacity: 0.9; }}
                pre {{ background: #f1f3f4; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🤖 RL-Swarm 监控告警</h2>
                    <p class="timestamp">⏰ {timestamp}</p>
                </div>
                
                <div class="content">
                    <h3>📋 告警详情</h3>
                    <p><strong>标题:</strong> {subject}</p>
                    
                    <div class="alert-box">
                        <pre>{body}</pre>
                    </div>
                    
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #eee;">
                    
                    <h3>🖥️ 系统信息</h3>
                    <p>🖥️ <strong>主机:</strong> Mac Mini M4</p>
                    <p>📍 <strong>位置:</strong> /Users/mac/work/gensyn/rl-swarm</p>
                    <p>📧 <strong>邮件库:</strong> yagmail (开源库)</p>
                </div>
                
                <div class="footer">
                    <p>🔧 监控系统: RL-Swarm Monitor v2.0 (powered by yagmail)</p>
                    <p><em>此邮件由RL-Swarm监控系统自动发送，请勿回复</em></p>
                </div>
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
        
        # TODO: 实现具体的短信发送逻辑
        self.logger.info("短信发送功能待实现")
        return False

class NotificationManager:
    """通知管理器 v2.0"""
    
    def __init__(self, config_file="notification_config.json"):
        self.config_manager = NotificationConfig(config_file)
        self.email_notifier = YagmailNotifier(self.config_manager.config)
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

if __name__ == "__main__":
    # 测试新的通知系统
    notifier = NotificationManager()
    
    success = notifier.send_alert(
        "🎉 yagmail 通知系统测试",
        "新的基于yagmail的通知系统已成功部署！\n\n功能更强大，发送更稳定。",
        "info"
    )
    
    if success:
        print("✅ yagmail通知系统测试成功！")
    else:
        print("❌ yagmail通知系统测试失败") 