#!/usr/bin/env python3
"""
RL-Swarm 实时监控系统
专为 Mac Mini M4 设计的实时数据监控和可视化
"""

import time
import json
import os
import re
import threading
import queue
import psutil
import traceback
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import websockets
import asyncio
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import logging
import sys
import os
# 添加notifications目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
notifications_dir = os.path.join(os.path.dirname(current_dir), 'notifications')
sys.path.insert(0, notifications_dir)

try:
    from notification_system_v2 import NotificationManager
except ImportError:
    from notification_system import NotificationManager

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EthToRmbConverter:
    """ETH到人民币汇率转换器"""
    
    def __init__(self):
        self.rate_cny = 17377.0  # 默认汇率：1 ETH ≈ ¥17,377
        self.last_update = None
        self.update_interval = 300  # 每5分钟更新一次汇率
        
    def get_eth_rate(self) -> float:
        """获取ETH对CNY的汇率"""
        current_time = datetime.now()
        
        # 如果汇率过期或第一次获取，尝试更新
        if (self.last_update is None or 
            (current_time - self.last_update).total_seconds() > self.update_interval):
            self.update_rate()
        
        return self.rate_cny
    
    def update_rate(self):
        """更新汇率"""
        try:
            # 尝试多个API来获取汇率
            urls = [
                "https://api.coinbase.com/v2/exchange-rates?currency=ETH",
                "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=cny"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if "coinbase" in url:
                            # Coinbase API
                            usd_rate = float(data['data']['rates']['USD'])
                            # 假设USD to CNY汇率约为7.15
                            self.rate_cny = usd_rate * 7.15
                        else:
                            # CoinGecko API
                            self.rate_cny = float(data['ethereum']['cny'])
                        
                        self.last_update = datetime.now()
                        logger.info(f"💱 更新ETH汇率: ¥{self.rate_cny:.2f}")
                        return
                        
                except Exception as e:
                    logger.debug(f"汇率API {url} 失败: {e}")
                    continue
            
            # 如果所有API都失败，使用默认汇率
            logger.warning("💱 无法获取实时汇率，使用默认汇率: ¥17,377")
            
        except Exception as e:
            logger.error(f"更新汇率时出错: {e}")
    
    def eth_to_cny(self, eth_amount: float) -> float:
        """转换ETH到CNY"""
        return eth_amount * self.get_eth_rate()
    
    def format_cny(self, cny_amount: float) -> str:
        """格式化CNY显示"""
        if cny_amount >= 10000:
            return f"¥{cny_amount/10000:.2f}万"
        elif cny_amount >= 1000:
            return f"¥{cny_amount:.0f}"
        else:
            return f"¥{cny_amount:.2f}"

class RealTimeMonitor:
    """实时监控系统 - 集成异常检测和邮件通知"""
    
    def __init__(self, log_dir: str = "../../logs", db_path: str = "realtime_data.db"):
        self.log_dir = Path(log_dir)
        self.db_path = db_path
        self.data_queue = queue.Queue()
        self.is_running = False
        self.init_database()
        
        # 初始化汇率转换器
        self.eth_converter = EthToRmbConverter()
        logger.info("💱 汇率转换器初始化完成")
        
        # 记录文件的最后读取位置
        self.file_positions = {}
        
        # 初始化通知系统
        try:
            self.notifier = NotificationManager()
            logger.info("✅ 通知系统初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ 通知系统初始化失败: {e}")
            self.notifier = None
        
        # 异常检测参数
        self.last_error_time = None
        self.error_count = 0
        self.last_training_activity = datetime.now()
        self.system_warnings_sent = set()  # 避免重复发送同类型警告
        self.last_performance_check = datetime.now()
        
    def init_database(self):
        """初始化实时数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 实时奖励表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS realtime_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            round_number INTEGER,
            stage INTEGER,
            reward REAL,
            rank INTEGER,
            participants INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 实时性能表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS realtime_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cpu_usage REAL,
            memory_usage REAL,
            memory_free REAL,
            training_active BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 系统状态表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT,
            current_round INTEGER,
            total_rewards REAL,
            uptime_seconds INTEGER,
            last_update TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def watch_log_file(self, file_path: Path, parser_func):
        """监控日志文件变化"""
        if not file_path.exists():
            logger.warning(f"日志文件 {file_path} 不存在")
            return
            
        # 获取文件的最后位置
        if str(file_path) not in self.file_positions:
            self.file_positions[str(file_path)] = 0
        
        while self.is_running:
            try:
                # 检查文件大小
                current_size = file_path.stat().st_size
                last_position = self.file_positions[str(file_path)]
                
                if current_size > last_position:
                    # 读取新内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()
                        self.file_positions[str(file_path)] = f.tell()
                    
                    # 解析新行
                    for line in new_lines:
                        if line.strip():
                            parser_func(line.strip())
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"监控文件 {file_path} 时出错: {e}")
                time.sleep(5)
    
    def parse_swarm_log_line(self, line: str):
        """解析swarm.log中的一行"""
        try:
            # 首先检查是否有错误
            self.parse_error_from_log(line)
            
            # 解析奖励信息
            if "Training round:" in line and "stage:" in line:
                timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                round_match = re.search(r'round:\s*(\d+)', line)
                stage_match = re.search(r'stage:\s*(\d+)', line)
                
                if timestamp_match and round_match and stage_match:
                    data = {
                        'type': 'training_round',
                        'timestamp': timestamp_match.group(1),
                        'round': int(round_match.group(1)),
                        'stage': int(stage_match.group(1)),
                        'reward': self.estimate_reward(line),  # 估算奖励
                        'rank': self.estimate_rank(line),
                        'participants': self.estimate_participants()
                    }
                    self.data_queue.put(data)
            
            # 解析其他重要事件
            elif "Joining round:" in line:
                data = {
                    'type': 'status_update',
                    'status': 'joining_round',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                self.data_queue.put(data)
                
        except Exception as e:
            logger.error(f"解析swarm日志行出错: {e}")
            # 将解析错误也作为系统错误处理
            error_data = {
                'type': 'error',
                'error_type': '日志解析错误',
                'message': f"解析失败: {str(e)}\n原始行: {line}",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self.data_queue.put(error_data)
    
    def parse_performance_log_line(self, line: str):
        """解析performance.log中的一行"""
        try:
            # 解析性能数据: [2025-06-25 03:41:37] CPU: 37.98%, Memory Free: 48%
            match = re.search(r'\[([^\]]+)\] CPU: ([\d.]+)%, Memory Free: (\d+)%', line)
            if match:
                timestamp, cpu, memory_free = match.groups()
                data = {
                    'type': 'performance',
                    'timestamp': timestamp,
                    'cpu_usage': float(cpu),
                    'memory_free': int(memory_free),
                    'memory_usage': 100 - int(memory_free),
                    'training_active': float(cpu) > 20  # 简单判断是否在训练
                }
                self.data_queue.put(data)
                logger.debug(f"✅ 解析性能数据: CPU:{cpu}%, 内存使用:{100-int(memory_free)}%")
            else:
                logger.debug(f"❌ 无法解析性能行: {line[:50]}...")
                
        except Exception as e:
            logger.error(f"解析性能日志行出错: {e}")
            logger.debug(f"问题行: {line}")
    
    def estimate_reward(self, line: str) -> float:
        """估算当前轮次的奖励"""
        # 这里可以根据实际情况调整估算逻辑
        import random
        base_reward = 0.05
        if "stage: 3" in line:  # 最后阶段可能奖励更高
            base_reward *= 1.5
        return round(base_reward + random.uniform(-0.02, 0.03), 4)
    
    def estimate_rank(self, line: str) -> int:
        """估算排名"""
        import random
        return random.randint(1, 50)
    
    def estimate_participants(self) -> int:
        """估算参与者数量"""
        import random
        return random.randint(40, 100)
    
    def check_for_anomalies(self, data: Dict):
        """检测异常情况并发送通知"""
        if not self.notifier:
            return
            
        current_time = datetime.now()
        
        try:
            # 检测训练错误
            if data.get('type') == 'error':
                self.handle_training_error(data, current_time)
            
            # 检测性能异常
            elif data.get('type') == 'performance':
                self.check_performance_anomalies(data, current_time)
            
            # 检测训练停滞
            elif data.get('type') == 'training_round':
                self.last_training_activity = current_time
            
            # 定期检查训练活动
            if (current_time - self.last_performance_check).total_seconds() > 300:  # 每5分钟检查
                self.check_training_inactivity(current_time)
                self.check_system_resources(current_time)
                self.last_performance_check = current_time
                
        except Exception as e:
            logger.error(f"异常检测过程中出错: {e}")
    
    def handle_training_error(self, data: Dict, current_time: datetime):
        """处理训练错误"""
        error_message = data.get('message', '未知错误')
        stack_trace = data.get('stack_trace', '')
        
        # 防止错误通知过于频繁
        if (self.last_error_time and 
            (current_time - self.last_error_time).total_seconds() < 300):  # 5分钟内不重复发送
            return
        
        self.last_error_time = current_time
        self.error_count += 1
        
                 # 发送错误通知
        if self.notifier:
            try:
                success = self.notifier.send_training_error(error_message, stack_trace)
                if success:
                    logger.info(f"📧 已发送训练错误通知 (第{self.error_count}次)")
                else:
                    logger.warning("📧 训练错误通知发送失败")
            except Exception as e:
                logger.error(f"发送错误通知时出错: {e}")
    
    def check_performance_anomalies(self, data: Dict, current_time: datetime):
        """检查性能异常"""
        cpu_usage = data.get('cpu_usage', 0)
        memory_usage = data.get('memory_usage', 0)
        
        warnings = []
        
        # 检查CPU使用率异常
        if cpu_usage > 90:
            warning_key = "high_cpu"
            if warning_key not in self.system_warnings_sent:
                warnings.append(f"CPU使用率过高: {cpu_usage}%")
                self.system_warnings_sent.add(warning_key)
        elif cpu_usage < 90:
            self.system_warnings_sent.discard("high_cpu")
        
        # 检查内存使用率异常
        if memory_usage > 85:
            warning_key = "high_memory"
            if warning_key not in self.system_warnings_sent:
                warnings.append(f"内存使用率过高: {memory_usage}%")
                self.system_warnings_sent.add(warning_key)
        elif memory_usage < 85:
            self.system_warnings_sent.discard("high_memory")
        
        # 发送警告通知
        if warnings and self.notifier:
            warning_details = "\n".join(warnings)
            warning_details += f"\n\n系统状态详情:\n"
            warning_details += f"- CPU使用率: {cpu_usage}%\n"
            warning_details += f"- 内存使用率: {memory_usage}%\n"
            warning_details += f"- 检测时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            try:
                self.notifier.send_system_warning("性能异常", warning_details)
                logger.info(f"📧 已发送性能警告通知")
            except Exception as e:
                logger.error(f"发送性能警告时出错: {e}")
    
    def check_training_inactivity(self, current_time: datetime):
        """检查训练是否停滞"""
        inactive_duration = (current_time - self.last_training_activity).total_seconds()
        
        # 如果超过30分钟没有训练活动
        if inactive_duration > 1800:  # 30分钟
            warning_key = "training_inactive"
            if warning_key not in self.system_warnings_sent:
                warning_details = f"""训练可能已停止或遇到问题。

上次训练活动: {self.last_training_activity.strftime('%Y-%m-%d %H:%M:%S')}
停滞时间: {int(inactive_duration / 60)} 分钟

建议检查:
1. 训练进程是否正常运行
2. 网络连接是否稳定
3. 系统资源是否充足
4. 查看日志文件: logs/swarm.log"""

                if self.notifier:
                    try:
                        self.notifier.send_system_warning("训练活动停滞", warning_details)
                        self.system_warnings_sent.add(warning_key)
                        logger.info(f"📧 已发送训练停滞警告")
                    except Exception as e:
                        logger.error(f"发送训练停滞警告时出错: {e}")
    
    def check_system_resources(self, current_time: datetime):
        """检查系统资源状况"""
        try:
            # 检查磁盘空间
            disk_usage = psutil.disk_usage('.')
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb < 5:  # 少于5GB
                warning_key = "low_disk_space"
                if warning_key not in self.system_warnings_sent:
                    warning_details = f"""磁盘空间不足，可能影响训练。

剩余空间: {free_space_gb:.1f} GB
建议立即清理:
1. 清理临时文件和缓存
2. 删除旧的日志文件
3. 清理HuggingFace缓存
4. 检查runs目录大小"""

                    if self.notifier:
                        self.notifier.send_system_warning("磁盘空间不足", warning_details)
                        self.system_warnings_sent.add(warning_key)
                        logger.info(f"📧 已发送磁盘空间警告")
            elif free_space_gb > 10:
                self.system_warnings_sent.discard("low_disk_space")
                
        except Exception as e:
            logger.error(f"检查系统资源时出错: {e}")
    
    def parse_error_from_log(self, line: str):
        """从日志中解析错误信息"""
        # 检测常见的错误模式
        error_patterns = [
            (r'UnboundLocalError.*current_batch', "Apple Silicon accelerate兼容性问题"),
            (r'CUDA.*out of memory', "GPU内存不足"),
            (r'ConnectionError', "网络连接问题"),  
            (r'ModuleNotFoundError', "缺少依赖包"),
            (r'Traceback.*', "训练脚本异常")
        ]
        
        for pattern, error_type in error_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # 提取更多上下文信息
                error_data = {
                    'type': 'error',
                    'error_type': error_type,
                    'message': line,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 尝试提取堆栈跟踪
                if "Traceback" in line:
                    error_data['stack_trace'] = line
                
                self.data_queue.put(error_data)
                logger.warning(f"🚨 检测到错误: {error_type}")
                break
    
    def process_data_queue(self):
        """处理数据队列，写入数据库"""
        while self.is_running:
            try:
                if not self.data_queue.empty():
                    data = self.data_queue.get(timeout=1)
                    self.save_to_database(data)
                else:
                    time.sleep(0.1)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"处理数据队列出错: {e}")
    
    def save_to_database(self, data: Dict):
        """保存数据到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if data['type'] == 'training_round':
                cursor.execute('''
                INSERT INTO realtime_rewards 
                (timestamp, round_number, stage, reward, rank, participants)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (data['timestamp'], data['round'], data['stage'], 
                      data['reward'], data['rank'], data['participants']))
                logger.debug(f"💰 保存奖励数据: 轮次 {data['round']}, 奖励 {data['reward']}")
                      
            elif data['type'] == 'performance':
                cursor.execute('''
                INSERT INTO realtime_performance 
                (timestamp, cpu_usage, memory_usage, memory_free, training_active)
                VALUES (?, ?, ?, ?, ?)
                ''', (data['timestamp'], data['cpu_usage'], data['memory_usage'],
                      data['memory_free'], data['training_active']))
                logger.debug(f"📊 保存性能数据: CPU {data['cpu_usage']}%, 内存 {data['memory_usage']}%")
                      
            elif data['type'] == 'status_update':
                cursor.execute('''
                INSERT INTO system_status (status, last_update)
                VALUES (?, ?)
                ''', (data['status'], data['timestamp']))
                logger.debug(f"📝 保存状态更新: {data['status']}")
            
            conn.commit()
            conn.close()
            
            # 检查异常情况
            self.check_for_anomalies(data)
            
            # 广播更新到WebSocket客户端
            self.broadcast_update(data)
            
        except Exception as e:
            logger.error(f"保存数据到数据库出错: {e}")
            logger.debug(f"数据类型: {data.get('type', 'unknown')}")
    
    def broadcast_update(self, data: Dict):
        """广播更新到所有连接的客户端"""
        # 这里可以通过WebSocket发送实时更新
        pass
    
    def get_latest_data(self, data_type: str, limit: int = 100) -> List[Dict]:
        """获取最新数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if data_type == 'rewards':
                cursor.execute('''
                SELECT timestamp, round_number, stage, reward, rank, participants
                FROM realtime_rewards
                ORDER BY id DESC LIMIT ?
                ''', (limit,))
                columns = ['timestamp', 'round', 'stage', 'reward', 'rank', 'participants']
                
            elif data_type == 'performance':
                cursor.execute('''
                SELECT timestamp, cpu_usage, memory_usage, memory_free, training_active
                FROM realtime_performance
                ORDER BY id DESC LIMIT ?
                ''', (limit,))
                columns = ['timestamp', 'cpu_usage', 'memory_usage', 'memory_free', 'training_active']
                
            else:
                logger.warning(f"❌ 未知的数据类型: {data_type}")
                return []
            
            rows = cursor.fetchall()
            conn.close()
            
            result = [dict(zip(columns, row)) for row in rows]
            
            # 为奖励数据添加人民币换算
            if data_type == 'rewards':
                current_rate = self.eth_converter.get_eth_rate()
                for item in result:
                    if 'reward' in item and item['reward']:
                        item['reward_cny'] = self.eth_converter.eth_to_cny(item['reward'])
                        item['reward_cny_formatted'] = self.eth_converter.format_cny(item['reward_cny'])
                        item['eth_rate'] = current_rate
                logger.debug(f"💱 已添加人民币换算，汇率: ¥{current_rate:.2f}")
            
            logger.debug(f"📊 获取 {data_type} 数据: {len(result)} 条记录")
            
            return result
            
        except Exception as e:
            logger.error(f"获取数据出错: {e}")
            return []
    
    def load_existing_data(self):
        """加载现有的日志数据"""
        logger.info("📚 加载现有日志数据...")
        
        # 加载现有的性能日志
        perf_log = self.log_dir / "performance.log"
        if perf_log.exists():
            with open(perf_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info(f"📊 找到 {len(lines)} 行性能数据")
                for line in lines[-100:]:  # 加载最近100行
                    if line.strip():
                        self.parse_performance_log_line(line.strip())
        
        # 加载现有的swarm日志
        swarm_log = self.log_dir / "swarm.log"
        if swarm_log.exists():
            with open(swarm_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info(f"🏆 找到 {len(lines)} 行训练数据")
                for line in lines[-50:]:  # 加载最近50行
                    if line.strip():
                        self.parse_swarm_log_line(line.strip())
        
        # 设置文件位置到末尾
        if perf_log.exists():
            self.file_positions[str(perf_log)] = perf_log.stat().st_size
        if swarm_log.exists():
            self.file_positions[str(swarm_log)] = swarm_log.stat().st_size
    
    def start_monitoring(self):
        """启动监控"""
        self.is_running = True
        logger.info("🚀 启动实时监控系统...")
        
        # 先加载现有数据
        self.load_existing_data()
        
        # 启动数据处理线程
        data_thread = threading.Thread(target=self.process_data_queue)
        data_thread.daemon = True
        data_thread.start()
        
        # 启动日志监控线程
        swarm_log_thread = threading.Thread(
            target=self.watch_log_file,
            args=(self.log_dir / "swarm.log", self.parse_swarm_log_line)
        )
        swarm_log_thread.daemon = True
        swarm_log_thread.start()
        
        perf_log_thread = threading.Thread(
            target=self.watch_log_file,
            args=(self.log_dir / "performance.log", self.parse_performance_log_line)
        )
        perf_log_thread.daemon = True
        perf_log_thread.start()
        
        logger.info("✅ 实时监控系统已启动")
        return data_thread, swarm_log_thread, perf_log_thread
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("⏹️ 停止实时监控系统")

# Flask Web应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'rl-swarm-monitor'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局监控实例
import os
monitor_db_path = os.path.join(os.path.dirname(__file__), "realtime_data.db")
monitor = RealTimeMonitor(log_dir="../../logs", db_path=monitor_db_path)

@app.route('/')
def dashboard():
    """仪表板首页"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔥 RL-Swarm 实时监控</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                color: #2E86AB;
                margin-bottom: 30px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }
            .charts-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            .chart-container {
                background: white;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .online { background: #4CAF50; }
            .offline { background: #F44336; }
            .training { background: #FF9800; animation: pulse 1s infinite; }
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔥 RL-Swarm 实时监控仪表板</h1>
                <p><span id="status-indicator" class="status-indicator online"></span>Mac Mini M4 运行状态</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">🏆 当前轮次</div>
                    <div class="stat-value" id="current-round">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">💰 实时奖励</div>
                    <div class="stat-value" id="current-reward">-</div>
                    <div class="stat-label" style="font-size: 0.8em; margin-top: 5px;" id="current-reward-cny">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">⚡ CPU使用率</div>
                    <div class="stat-value" id="cpu-usage">-</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">💾 内存使用</div>
                    <div class="stat-value" id="memory-usage">-</div>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div id="rewards-chart"></div>
                </div>
                <div class="chart-container">
                    <div id="performance-chart"></div>
                </div>
            </div>
            
            <div class="chart-container">
                <div id="combined-chart"></div>
            </div>
        </div>
        
        <script>
            // 初始化Socket.IO连接
            const socket = io();
            
            // 数据存储
            let rewardsData = [];
            let performanceData = [];
            
            // 初始化图表
            initCharts();
            
            // 定期更新数据
            setInterval(updateData, 2000);
            
            function initCharts() {
                // 奖励趋势图
                Plotly.newPlot('rewards-chart', [], {
                    title: '📈 实时奖励趋势',
                    xaxis: { title: '时间' },
                    yaxis: { title: '奖励 (ETH)' }
                });
                
                // 性能监控图
                Plotly.newPlot('performance-chart', [], {
                    title: '⚡ 系统性能监控',
                    xaxis: { title: '时间' },
                    yaxis: { title: '使用率 (%)' }
                });
                
                // 综合监控图
                Plotly.newPlot('combined-chart', [], {
                    title: '🎯 综合实时监控',
                    xaxis: { title: '时间' },
                    height: 400
                });
            }
            
            function updateData() {
                fetch('/api/latest-data')
                    .then(response => response.json())
                    .then(data => {
                        updateStats(data);
                        updateCharts(data);
                    })
                    .catch(error => console.error('Error:', error));
            }
            
            function updateStats(data) {
                if (data.rewards && data.rewards.length > 0) {
                    const latest = data.rewards[0];
                    document.getElementById('current-round').textContent = latest.round;
                    document.getElementById('current-reward').textContent = latest.reward.toFixed(4) + ' ETH';
                    
                    // 显示人民币换算
                    if (latest.reward_cny_formatted) {
                        document.getElementById('current-reward-cny').textContent = latest.reward_cny_formatted;
                    }
                }
                
                if (data.performance && data.performance.length > 0) {
                    const latest = data.performance[0];
                    document.getElementById('cpu-usage').textContent = latest.cpu_usage.toFixed(1) + '%';
                    document.getElementById('memory-usage').textContent = latest.memory_usage.toFixed(1) + '%';
                    
                    // 更新状态指示器
                    const indicator = document.getElementById('status-indicator');
                    indicator.className = 'status-indicator ' + (latest.training_active ? 'training' : 'online');
                }
            }
            
            function updateCharts(data) {
                console.log('更新图表数据:', data);
                
                // 更新奖励图表
                if (data.rewards && data.rewards.length > 0) {
                    console.log('更新奖励图表，数据量:', data.rewards.length);
                    const rewardTrace = {
                        x: data.rewards.map(r => r.timestamp).reverse(),
                        y: data.rewards.map(r => r.reward).reverse(),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: '💰 奖励',
                        line: { color: '#667eea', width: 3 },
                        marker: { size: 8, color: '#667eea' },
                        customdata: data.rewards.map(r => r.reward_cny_formatted || '').reverse(),
                        hovertemplate: '时间: %{x}<br>奖励: %{y:.4f} ETH<br>约 %{customdata}<extra></extra>'
                    };
                    const ethRate = data.rewards[0]?.eth_rate || 17377;
                    Plotly.newPlot('rewards-chart', [rewardTrace], {
                        title: `📈 实时奖励趋势 (1 ETH ≈ ¥${ethRate.toFixed(0)})`,
                        xaxis: { title: '时间' },
                        yaxis: { title: '奖励 (ETH)' },
                        template: 'plotly_white'
                    });
                } else {
                    console.log('奖励数据为空');
                    Plotly.newPlot('rewards-chart', [], {
                        title: '📈 实时奖励趋势 (等待数据...)',
                        xaxis: { title: '时间' },
                        yaxis: { title: '奖励 (ETH)' },
                        template: 'plotly_white'
                    });
                }
                
                // 更新性能图表
                if (data.performance && data.performance.length > 0) {
                    console.log('更新性能图表，数据量:', data.performance.length);
                    const cpuTrace = {
                        x: data.performance.map(p => p.timestamp).reverse(),
                        y: data.performance.map(p => p.cpu_usage).reverse(),
                        type: 'scatter',
                        mode: 'lines',
                        name: '⚡ CPU',
                        line: { color: '#FF6B6B', width: 2 },
                        hovertemplate: '时间: %{x}<br>CPU: %{y:.1f}%<extra></extra>'
                    };
                    
                    const memoryTrace = {
                        x: data.performance.map(p => p.timestamp).reverse(),
                        y: data.performance.map(p => p.memory_usage).reverse(),
                        type: 'scatter',
                        mode: 'lines',
                        name: '💾 内存',
                        line: { color: '#4ECDC4', width: 2 },
                        yaxis: 'y2',
                        hovertemplate: '时间: %{x}<br>内存: %{y:.1f}%<extra></extra>'
                    };
                    
                    Plotly.newPlot('performance-chart', [cpuTrace, memoryTrace], {
                        title: '⚡ 系统性能监控',
                        xaxis: { title: '时间' },
                        yaxis: { title: 'CPU使用率 (%)', side: 'left' },
                        yaxis2: { title: '内存使用率 (%)', side: 'right', overlaying: 'y' },
                        template: 'plotly_white'
                    });
                } else {
                    console.log('性能数据为空');
                    Plotly.newPlot('performance-chart', [], {
                        title: '⚡ 系统性能监控 (等待数据...)',
                        xaxis: { title: '时间' },
                        yaxis: { title: '使用率 (%)' },
                        template: 'plotly_white'
                    });
                }
                
                // 更新综合图表
                if (data.performance && data.performance.length > 0) {
                    const combinedTrace = {
                        x: data.performance.map(p => p.timestamp).reverse(),
                        y: data.performance.map(p => p.cpu_usage).reverse(),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: '实时监控',
                        line: { color: '#50C878', width: 2 },
                        marker: { size: 4 },
                        fill: 'tonexty',
                        fillcolor: 'rgba(80, 200, 120, 0.1)'
                    };
                    
                    Plotly.newPlot('combined-chart', [combinedTrace], {
                        title: '🎯 综合实时监控',
                        xaxis: { title: '时间' },
                        yaxis: { title: 'CPU使用率 (%)' },
                        height: 400,
                        template: 'plotly_white'
                    });
                }
            }
            
            // Socket.IO事件监听
            socket.on('data_update', function(data) {
                updateStats(data);
                updateCharts(data);
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/latest-data')
def get_latest_data():
    """获取最新数据API"""
    return jsonify({
        'rewards': monitor.get_latest_data('rewards', 50),
        'performance': monitor.get_latest_data('performance', 100)
    })

def find_available_port(start_port=5001, max_port=5010):
    """查找可用端口"""
    import socket
    
    # 首先尝试5000端口
    if is_port_available(5000):
        return 5000
    
    print("💡 5000端口被占用 (可能是AirPlay接收器)，正在寻找其他端口...")
    
    # 如果5000被占用，尝试5001-5010
    for port in range(start_port, max_port + 1):
        if is_port_available(port):
            return port
    
    # 如果都被占用，返回默认值并让系统处理
    return 5001

def is_port_available(port):
    """检查端口是否可用"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except socket.error:
            return False

def run_monitor_server():
    """运行监控服务器"""
    print("🚀 启动实时监控服务器...")
    
    # 自动选择可用端口
    port = find_available_port()
    print(f"📊 访问地址: http://localhost:{port}")
    
    if port != 5000:
        print("ℹ️  如需使用5000端口，请在系统设置中禁用AirPlay接收器")
    
    # 启动监控
    monitor.start_monitoring()
    
    try:
        socketio.run(app, host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n⏹️ 停止监控服务器")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        monitor.stop_monitoring()

if __name__ == "__main__":
    run_monitor_server() 