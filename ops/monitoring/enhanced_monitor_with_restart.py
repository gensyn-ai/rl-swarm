#!/usr/bin/env python3
"""
RL-Swarm 增强版实时监控系统
包含错误检测、自动重启和通知功能
"""

import time
import os
import re
import threading
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutoRestartMonitor:
    """增强版监控系统 - 包含自动重启功能"""
    
    def __init__(self, log_dir: str = "logs", project_root: str = "."):
        self.log_dir = Path(project_root) / log_dir
        self.project_root = Path(project_root)
        self.db_path = self.project_root / "ops/monitoring/realtime_data.db"
        self.is_running = False
        
        # 进程管理
        self.rl_swarm_process = None
        self.last_restart_time = None
        self.restart_count = 0
        self.max_restarts_per_hour = 3
        
        # 记录文件的最后读取位置
        self.file_positions = {}
        
        # 错误检测参数
        self.last_error_time = None
        self.error_count = 0
        self.last_training_activity = datetime.now()
        self.consecutive_errors = 0
        self.last_health_check = datetime.now()
        
        # 初始化数据库
        self.init_database()
        
        logger.info(f"🔧 监控系统初始化完成")
        logger.info(f"�� 日志目录: {self.log_dir}")
        logger.info(f"📊 数据库路径: {self.db_path}")
    
    def init_database(self):
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 错误记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            error_type TEXT,
            message TEXT,
            stack_trace TEXT,
            auto_restart BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 重启记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS restart_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            reason TEXT,
            restart_count INTEGER,
            success BOOLEAN,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_rl_swarm_process(self) -> bool:
        """检查RL-Swarm进程是否运行"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if ('train_single_gpu.py' in cmdline or 
                    'hivemind_grpo_trainer.py' in cmdline or
                    'run_rl_swarm' in cmdline):
                    self.rl_swarm_process = proc
                    return True
            return False
        except Exception as e:
            logger.error(f"检查进程状态出错: {e}")
            return False
    
    def watch_log_file(self, file_path: Path, parser_func, check_interval: float = 1.0):
        """监控日志文件变化"""
        if not file_path.exists():
            logger.warning(f"📄 日志文件不存在: {file_path}")
            # 等待文件创建
            while self.is_running and not file_path.exists():
                time.sleep(5)
                logger.debug(f"等待日志文件创建: {file_path}")
            
            if not self.is_running:
                return
            
            logger.info(f"✅ 日志文件已创建: {file_path}")
        
        # 获取文件的最后位置
        file_key = str(file_path)
        if file_key not in self.file_positions:
            self.file_positions[file_key] = 0
        
        logger.info(f"🔍 开始监控日志文件: {file_path}")
        
        while self.is_running:
            try:
                # 检查文件大小
                current_size = file_path.stat().st_size
                last_position = self.file_positions[file_key]
                
                if current_size > last_position:
                    # 读取新内容
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(last_position)
                        new_lines = f.readlines()
                        self.file_positions[file_key] = f.tell()
                    
                    # 解析新行
                    for line in new_lines:
                        line = line.strip()
                        if line:
                            parser_func(line)
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"监控文件 {file_path} 时出错: {e}")
                time.sleep(5)
    
    def parse_swarm_log_line(self, line: str):
        """解析swarm.log中的一行"""
        try:
            # 检查错误模式
            error_detected = self.detect_error_patterns(line)
            
            if error_detected:
                self.handle_error_detection(error_detected, line)
            
            # 检查训练活动
            if any(keyword in line for keyword in ["Training round:", "Joining round:", "Starting stage"]):
                self.last_training_activity = datetime.now()
                logger.debug("🎯 训练活动检测到")
                
        except Exception as e:
            logger.error(f"解析swarm日志行出错: {e}")
    
    def detect_error_patterns(self, line: str) -> Optional[Dict]:
        """检测错误模式"""
        error_patterns = [
            {
                'pattern': r'UnboundLocalError.*current_batch',
                'type': 'accelerate_compatibility_error',
                'severity': 'critical',
                'auto_restart': True,
                'description': 'Apple Silicon accelerate兼容性问题'
            },
            {
                'pattern': r'CUDA.*out of memory',
                'type': 'gpu_memory_error',
                'severity': 'critical', 
                'auto_restart': True,
                'description': 'GPU内存不足'
            },
            {
                'pattern': r'ConnectionError|connection.*refused',
                'type': 'network_error',
                'severity': 'high',
                'auto_restart': True,
                'description': '网络连接问题'
            },
            {
                'pattern': r'ModuleNotFoundError|ImportError',
                'type': 'dependency_error',
                'severity': 'critical',
                'auto_restart': False,
                'description': '缺少依赖包'
            },
            {
                'pattern': r'Exception.*|Error.*|Traceback.*',
                'type': 'general_error',
                'severity': 'medium',
                'auto_restart': False,
                'description': '一般异常'
            }
        ]
        
        for error_config in error_patterns:
            if re.search(error_config['pattern'], line, re.IGNORECASE):
                return {
                    'type': error_config['type'],
                    'severity': error_config['severity'],
                    'auto_restart': error_config['auto_restart'],
                    'description': error_config['description'],
                    'message': line,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        
        return None
    
    def handle_error_detection(self, error_info: Dict, full_line: str):
        """处理检测到的错误"""
        current_time = datetime.now()
        
        # 记录错误
        self.log_error_to_database(error_info, full_line)
        
        # 更新错误计数
        self.consecutive_errors += 1
        self.last_error_time = current_time
        
        logger.error(f"🚨 检测到错误: {error_info['description']}")
        logger.error(f"📝 错误类型: {error_info['type']}")
        logger.error(f"⚠️ 严重程度: {error_info['severity']}")
        
        # 判断是否需要自动重启
        should_restart = (
            error_info['auto_restart'] and
            error_info['severity'] in ['critical', 'high'] and
            self.should_restart()
        )
        
        if should_restart:
            logger.warning(f"🔄 准备自动重启 RL-Swarm (连续错误: {self.consecutive_errors})")
            self.restart_rl_swarm(f"错误检测: {error_info['description']}")
        else:
            reason = "不满足重启条件" if not error_info['auto_restart'] else "达到重启限制"
            logger.info(f"⏸️ 不执行自动重启: {reason}")
    
    def should_restart(self) -> bool:
        """判断是否应该重启"""
        current_time = datetime.now()
        
        # 检查重启频率限制
        if self.last_restart_time:
            hours_since_last = (current_time - self.last_restart_time).total_seconds() / 3600
            if hours_since_last < 1 and self.restart_count >= self.max_restarts_per_hour:
                logger.warning(f"🚫 重启频率过高，暂停自动重启 (1小时内已重启{self.restart_count}次)")
                return False
        
        return True
    
    def restart_rl_swarm(self, reason: str):
        """重启RL-Swarm系统"""
        current_time = datetime.now()
        
        logger.info(f"🔄 开始重启 RL-Swarm: {reason}")
        
        try:
            # 1. 停止现有进程
            self.stop_rl_swarm()
            
            # 2. 等待进程完全停止
            time.sleep(10)
            
            # 3. 启动新进程
            success = self.start_rl_swarm()
            
            # 4. 记录重启信息
            self.log_restart_to_database(reason, success)
            
            if success:
                self.restart_count += 1
                self.last_restart_time = current_time
                self.consecutive_errors = 0  # 重置错误计数
                logger.info(f"✅ RL-Swarm 重启成功 (第{self.restart_count}次)")
            else:
                logger.error(f"❌ RL-Swarm 重启失败")
                
        except Exception as e:
            logger.error(f"重启过程出错: {e}")
            self.log_restart_to_database(f"{reason} (重启失败: {e})", False)
    
    def stop_rl_swarm(self):
        """停止RL-Swarm进程"""
        logger.info("🛑 停止现有 RL-Swarm 进程...")
        
        try:
            # 查找并终止相关进程
            killed_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline for keyword in 
                          ['train_single_gpu.py', 'hivemind_grpo_trainer.py', 'run_rl_swarm']):
                        proc.terminate()
                        killed_processes.append(proc.info['pid'])
                        logger.info(f"🔪 终止进程 PID: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 等待进程正常终止
            time.sleep(5)
            
            # 强制杀死仍在运行的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if any(keyword in cmdline for keyword in 
                          ['train_single_gpu.py', 'hivemind_grpo_trainer.py', 'run_rl_swarm']):
                        proc.kill()
                        logger.warning(f"⚔️ 强制杀死进程 PID: {proc.info['pid']}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.info("✅ RL-Swarm 进程已停止")
            
        except Exception as e:
            logger.error(f"停止进程时出错: {e}")
    
    def start_rl_swarm(self) -> bool:
        """启动RL-Swarm进程"""
        logger.info("🚀 启动新的 RL-Swarm 进程...")
        
        try:
            # 使用管理脚本启动
            start_script = self.project_root / "manage.sh"
            if start_script.exists():
                # 在后台启动
                process = subprocess.Popen(
                    [str(start_script)],
                    cwd=str(self.project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid  # 创建新的进程组
                )
                
                # 等待几秒钟确认启动
                time.sleep(15)
                
                # 检查进程是否启动成功
                if self.check_rl_swarm_process():
                    logger.info("✅ RL-Swarm 启动成功")
                    return True
                else:
                    logger.error("❌ RL-Swarm 启动失败 - 未检测到进程")
                    return False
            else:
                logger.error(f"❌ 启动脚本不存在: {start_script}")
                return False
                
        except Exception as e:
            logger.error(f"启动RL-Swarm时出错: {e}")
            return False
    
    def log_error_to_database(self, error_info: Dict, full_line: str):
        """记录错误到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO error_logs 
            (timestamp, error_type, message, stack_trace, auto_restart)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                error_info['timestamp'],
                error_info['type'],
                error_info['description'],
                full_line,
                error_info['auto_restart']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"记录错误到数据库失败: {e}")
    
    def log_restart_to_database(self, reason: str, success: bool):
        """记录重启信息到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO restart_logs 
            (timestamp, reason, restart_count, success)
            VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                reason,
                self.restart_count + 1,
                success
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"记录重启信息到数据库失败: {e}")
    
    def health_check(self):
        """定期健康检查"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 检查训练活动
                inactive_duration = (current_time - self.last_training_activity).total_seconds()
                
                # 如果超过30分钟没有训练活动，检查进程状态
                if inactive_duration > 1800:  # 30分钟
                    logger.warning(f"⚠️ 训练活动停滞 {int(inactive_duration/60)} 分钟")
                    
                    if not self.check_rl_swarm_process():
                        logger.error("🚨 RL-Swarm 进程未运行，执行重启")
                        self.restart_rl_swarm("进程停止检测")
                    else:
                        logger.info("✅ RL-Swarm 进程正常运行")
                
                time.sleep(300)  # 每5分钟检查一次
                
            except Exception as e:
                logger.error(f"健康检查出错: {e}")
                time.sleep(60)
    
    def start_monitoring(self):
        """启动监控系统"""
        logger.info("🚀 启动增强版监控系统...")
        self.is_running = True
        
        # 启动各个监控线程
        threads = []
        
        # 监控swarm.log
        swarm_log = self.log_dir / "swarm.log"
        thread1 = threading.Thread(
            target=self.watch_log_file,
            args=(swarm_log, self.parse_swarm_log_line, 1.0),
            daemon=True
        )
        threads.append(thread1)
        
        # 健康检查线程
        thread2 = threading.Thread(target=self.health_check, daemon=True)
        threads.append(thread2)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        logger.info("✅ 所有监控线程已启动")
        logger.info("📊 监控状态:")
        logger.info(f"   - Swarm日志: {swarm_log}")
        logger.info(f"   - 健康检查: 每5分钟")
        logger.info(f"   - 最大重启次数: {self.max_restarts_per_hour}/小时")
        
        try:
            # 主循环
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 收到停止信号")
        finally:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """停止监控系统"""
        logger.info("🛑 停止监控系统...")
        self.is_running = False

def main():
    """主函数"""
    print("🍎 RL-Swarm 增强版监控系统 (Mac Mini M4)")
    print("=" * 50)
    print("功能:")
    print("✅ 实时日志监控")
    print("✅ 错误自动检测") 
    print("✅ 智能自动重启")
    print("✅ 健康状态检查")
    print("=" * 50)
    
    # 创建监控实例
    monitor = AutoRestartMonitor()
    
    print(f"\n🚀 监控系统启动中...")
    print("按 Ctrl+C 停止监控")
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 监控系统已停止")

if __name__ == "__main__":
    main()
