#!/usr/bin/env python3
"""
RL-Swarm 自动重启监控脚本
专门检测错误并自动重启系统
"""

import time
import os
import re
import subprocess
import psutil
from datetime import datetime
from pathlib import Path

class SimpleAutoRestart:
    def __init__(self):
        self.project_root = Path(".")  # 直接使用当前目录作为项目根目录
        self.log_file = self.project_root / "logs/swarm.log"
        self.manage_script = self.project_root / "manage.sh" 
        self.last_position = 0
        self.restart_count = 0
        self.last_restart_time = None
        self.max_restarts_per_hour = 3
        
        print(f"🔧 监控系统初始化")
        print(f"📁 项目根目录: {self.project_root.absolute()}")
        print(f"📄 监控日志: {self.log_file.absolute()}")
        print(f"🚀 管理脚本: {self.manage_script.absolute()}")
        
        # 验证关键文件是否存在
        if not self.log_file.exists():
            print(f"⚠️ 警告: 日志文件 {self.log_file} 不存在，将等待创建")
        if not self.manage_script.exists():
            print(f"❌ 错误: 管理脚本 {self.manage_script} 不存在")
        else:
            print(f"✅ 管理脚本验证成功")
        
    def is_rl_swarm_running(self):
        """检查RL-Swarm是否运行"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if ('train_single_gpu.py' in cmdline or 
                    'hivemind_grpo_trainer.py' in cmdline):
                    return True, proc.info['pid']
            return False, None
        except Exception as e:
            print(f"❌ 检查进程状态出错: {e}")
            return False, None
            
    def stop_rl_swarm(self):
        """停止RL-Swarm进程"""
        print("🛑 停止RL-Swarm进程...")
        
        killed_pids = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in 
                      ['train_single_gpu.py', 'hivemind_grpo_trainer.py', 'run_rl_swarm']):
                    proc.terminate()
                    killed_pids.append(proc.info['pid'])
                    print(f"🔪 终止进程 PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 等待进程终止
        time.sleep(5)
        
        # 强制杀死仍在运行的进程
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(keyword in cmdline for keyword in 
                      ['train_single_gpu.py', 'hivemind_grpo_trainer.py', 'run_rl_swarm']):
                    proc.kill()
                    print(f"⚔️ 强制杀死进程 PID: {proc.info['pid']}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        print("✅ 进程停止完成")
        
    def start_rl_swarm(self):
        """启动RL-Swarm"""
        print("🚀 启动RL-Swarm...")
        
        try:
            if not self.manage_script.exists():
                print(f"❌ 管理脚本不存在: {self.manage_script}")
                return False
                
            # 启动进程
            process = subprocess.Popen(
                [str(self.manage_script)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            print("⏳ 等待启动完成...")
            time.sleep(20)  # 等待启动
            
            # 检查是否启动成功
            is_running, pid = self.is_rl_swarm_running()
            if is_running:
                print(f"✅ RL-Swarm 启动成功 (PID: {pid})")
                return True
            else:
                print("❌ RL-Swarm 启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动出错: {e}")
            return False
    
    def should_restart(self):
        """检查是否应该重启"""
        current_time = datetime.now()
        
        # 检查重启频率限制
        if self.last_restart_time:
            hours_since_last = (current_time - self.last_restart_time).total_seconds() / 3600
            if hours_since_last < 1 and self.restart_count >= self.max_restarts_per_hour:
                print(f"🚫 重启频率过高，跳过重启 (1小时内已重启{self.restart_count}次)")
                return False
        
        return True
        
    def restart_rl_swarm(self, reason):
        """重启RL-Swarm"""
        if not self.should_restart():
            return False
            
        print(f"\n🔄 开始重启RL-Swarm")
        print(f"📝 重启原因: {reason}")
        print(f"🕐 重启时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 停止现有进程
            self.stop_rl_swarm()
            
            # 等待系统稳定
            print("⏳ 等待系统稳定...")
            time.sleep(10)
            
            # 启动新进程
            success = self.start_rl_swarm()
            
            if success:
                self.restart_count += 1
                self.last_restart_time = datetime.now()
                
                # 记录重启日志
                log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 自动重启成功 - {reason} (第{self.restart_count}次)\n"
                with open(self.project_root / "logs/auto_restart.log", "a") as f:
                    f.write(log_msg)
                
                print(f"🎉 重启成功！(第{self.restart_count}次)")
                return True
            else:
                print(f"❌ 重启失败")
                return False
                
        except Exception as e:
            print(f"❌ 重启过程出错: {e}")
            return False
    
    def check_error_patterns(self, line):
        """检查错误模式"""
        error_patterns = [
            (r'UnboundLocalError.*current_batch', 'Apple Silicon accelerate兼容性问题'),
            (r'CUDA.*out of memory', 'GPU内存不足'),
            (r'ConnectionError', '网络连接问题'),
            (r'ModuleNotFoundError', '缺少依赖包'),
        ]
        
        for pattern, description in error_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                return description
        
        return None
    
    def monitor_log(self):
        """监控日志文件"""
        print(f"\n🔍 开始监控日志文件: {self.log_file}")
        
        if not self.log_file.exists():
            print(f"📄 日志文件不存在，等待创建...")
            while not self.log_file.exists():
                time.sleep(5)
            print(f"✅ 日志文件已创建")
        
        # 从文件末尾开始读取
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)  # 跳到文件末尾
            self.last_position = f.tell()
        
        print(f"📍 开始监控位置: {self.last_position}")
        print("🔄 监控中... (按 Ctrl+C 停止)")
        
        consecutive_errors = 0
        
        while True:
            try:
                # 检查文件大小
                current_size = self.log_file.stat().st_size
                
                if current_size > self.last_position:
                    # 读取新内容
                    with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        f.seek(self.last_position)
                        new_lines = f.readlines()
                        self.last_position = f.tell()
                    
                    # 检查每一行是否有错误
                    for line in new_lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # 检查错误模式
                        error_type = self.check_error_patterns(line)
                        
                        if error_type:
                            consecutive_errors += 1
                            print(f"\n🚨 检测到错误 ({consecutive_errors}): {error_type}")
                            print(f"📝 错误内容: {line[:100]}...")
                            
                            # 如果是关键错误，立即重启
                            if any(keyword in error_type for keyword in 
                                  ['Apple Silicon', 'GPU内存', '网络连接']):
                                
                                print(f"⚡ 检测到关键错误，立即重启")
                                if self.restart_rl_swarm(error_type):
                                    consecutive_errors = 0  # 重置错误计数
                                    print(f"🔄 重启完成，继续监控...")
                                else:
                                    print(f"❌ 重启失败，继续监控...")
                                
                        # 检查训练活动 (重置错误计数)
                        elif any(keyword in line for keyword in 
                               ["Training round:", "Joining round:", "Starting stage"]):
                            if consecutive_errors > 0:
                                print(f"✅ 检测到训练活动，重置错误计数")
                                consecutive_errors = 0
                
                time.sleep(2)  # 每2秒检查一次
                
            except KeyboardInterrupt:
                print(f"\n🛑 监控停止")
                break
            except Exception as e:
                print(f"❌ 监控过程出错: {e}")
                time.sleep(5)
    
    def start(self):
        """启动监控"""
        print("🍎 RL-Swarm 自动重启监控系统")
        print("=" * 50)
        
        # 检查初始状态
        is_running, pid = self.is_rl_swarm_running()
        print(f"📊 当前状态: {'运行中' if is_running else '未运行'}")
        if is_running:
            print(f"📍 进程PID: {pid}")
        
        # 开始监控
        self.monitor_log()

if __name__ == "__main__":
    monitor = SimpleAutoRestart()
    monitor.start() 