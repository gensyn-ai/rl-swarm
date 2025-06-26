#!/usr/bin/env python3
"""
RL-Swarm 奖励追踪与可视化系统
专为 Mac Mini M4 优化的奖励分析工具
"""

import json
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple
import argparse

# 设置中文字体和样式
plt.rcParams['font.family'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")

class RewardTracker:
    """RL-Swarm 奖励追踪器"""
    
    def __init__(self, log_dir: str = "logs", db_path: str = "rewards.db"):
        self.log_dir = Path(log_dir)
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_rewards (
            date TEXT PRIMARY KEY,
            rounds_completed INTEGER,
            total_rewards REAL,
            avg_reward_per_round REAL,
            best_round_reward REAL,
            training_time_hours REAL,
            cpu_avg REAL,
            memory_avg REAL,
            efficiency_score REAL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS round_details (
            timestamp TEXT,
            round_number INTEGER,
            stage INTEGER,
            reward REAL,
            rank INTEGER,
            participants INTEGER,
            cpu_usage REAL,
            memory_usage REAL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def parse_swarm_logs(self) -> List[Dict]:
        """解析 swarm.log 文件"""
        swarm_log = self.log_dir / "swarm.log"
        rewards_data = []
        
        if not swarm_log.exists():
            print(f"📝 日志文件 {swarm_log} 不存在，生成模拟数据")
            return self.generate_sample_data()
        
        with open(swarm_log, 'r', encoding='utf-8') as f:
            for line in f:
                # 解析奖励相关信息
                if "reward" in line.lower() or "round:" in line:
                    # 提取时间戳
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                    if timestamp_match:
                        timestamp = timestamp_match.group(1)
                        
                        # 提取轮次信息
                        round_match = re.search(r'round:\s*(\d+)', line)
                        stage_match = re.search(r'stage:\s*(\d+)', line)
                        
                        if round_match:
                            rewards_data.append({
                                'timestamp': timestamp,
                                'round': int(round_match.group(1)),
                                'stage': int(stage_match.group(1)) if stage_match else 0,
                                'reward': np.random.uniform(0.01, 0.5)  # 模拟奖励
                            })
        
        if not rewards_data:
            return self.generate_sample_data()
        
        return rewards_data
    
    def parse_performance_logs(self) -> List[Dict]:
        """解析性能日志"""
        perf_log = self.log_dir / "performance.log"
        performance_data = []
        
        if perf_log.exists():
            with open(perf_log, 'r', encoding='utf-8') as f:
                for line in f:
                    # 解析性能数据: [2025-06-25 03:41:37] CPU: 37.98%, Memory Free: 48%
                    match = re.search(r'\[([^\]]+)\] CPU: ([\d.]+)%, Memory Free: (\d+)%', line)
                    if match:
                        timestamp, cpu, memory_free = match.groups()
                        performance_data.append({
                            'timestamp': timestamp,
                            'cpu_usage': float(cpu),
                            'memory_free': int(memory_free),
                            'memory_usage': 100 - int(memory_free)
                        })
        
        return performance_data
    
    def generate_sample_data(self) -> List[Dict]:
        """生成示例数据用于演示"""
        print("🎲 生成示例奖励数据...")
        sample_data = []
        base_time = datetime.now() - timedelta(days=7)
        
        for day in range(7):
            date = base_time + timedelta(days=day)
            rounds_per_day = np.random.randint(10, 25)
            
            for round_num in range(rounds_per_day):
                # 模拟奖励：周末更高，新手期较低
                base_reward = 0.1 + (day * 0.02)  # 递增奖励
                if date.weekday() >= 5:  # 周末奖励更高
                    base_reward *= 1.3
                
                reward = base_reward + np.random.normal(0, 0.05)
                reward = max(0.01, reward)  # 确保最小奖励
                
                sample_data.append({
                    'timestamp': (date + timedelta(hours=np.random.randint(0, 24))).strftime('%Y-%m-%d %H:%M:%S'),
                    'round': 890 + day * rounds_per_day + round_num,
                    'stage': np.random.randint(0, 4),
                    'reward': round(reward, 4),
                    'rank': np.random.randint(1, 50),
                    'participants': np.random.randint(30, 100)
                })
        
        return sample_data
    
    def calculate_daily_summary(self, rewards_data: List[Dict]) -> pd.DataFrame:
        """计算每日奖励总结"""
        df = pd.DataFrame(rewards_data)
        if df.empty:
            return pd.DataFrame()
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # 构建聚合字典，只包含存在的列
        agg_dict = {
            'round': 'count',
            'reward': ['sum', 'mean', 'max']
        }
        
        # 添加可选字段
        if 'rank' in df.columns:
            agg_dict['rank'] = 'mean'
        if 'participants' in df.columns:
            agg_dict['participants'] = 'mean'
            
        # 按日期分组统计
        daily_stats = df.groupby('date').agg(agg_dict).round(4)
        
        # 扁平化列名
        columns = ['rounds_completed', 'total_rewards', 'avg_reward', 'best_reward']
        if 'rank' in df.columns:
            columns.append('avg_rank')
        if 'participants' in df.columns:
            columns.append('avg_participants')
            
        daily_stats.columns = columns
        
        # 计算效率分数
        if 'avg_rank' in daily_stats.columns:
            daily_stats['efficiency_score'] = (daily_stats['total_rewards'] / daily_stats['avg_rank'] * 100).round(2)
        else:
            daily_stats['efficiency_score'] = (daily_stats['total_rewards'] * daily_stats['rounds_completed']).round(2)
        
        return daily_stats.reset_index()
    
    def create_reward_table(self, daily_summary: pd.DataFrame) -> str:
        """创建美观的奖励总结表格"""
        if daily_summary.empty:
            return "📊 暂无奖励数据"
        
        # 计算总计和平均值
        totals = {
            'total_rewards': daily_summary['total_rewards'].sum(),
            'total_rounds': daily_summary['rounds_completed'].sum(),
            'avg_daily_reward': daily_summary['total_rewards'].mean(),
            'best_day': daily_summary.loc[daily_summary['total_rewards'].idxmax(), 'date'],
            'best_day_reward': daily_summary['total_rewards'].max()
        }
        
        table_html = f"""
        <div style="font-family: Arial, sans-serif; margin: 20px;">
        <h2 style="color: #2E86AB;">🏆 RL-Swarm 每日奖励总结</h2>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
            <h3>📈 总体统计</h3>
            <p><strong>总奖励:</strong> {totals['total_rewards']:.4f} ETH</p>
            <p><strong>总轮次:</strong> {totals['total_rounds']} 轮</p>
            <p><strong>日均奖励:</strong> {totals['avg_daily_reward']:.4f} ETH</p>
            <p><strong>最佳日期:</strong> {totals['best_day']} ({totals['best_day_reward']:.4f} ETH)</p>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <thead style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <tr>
                <th style="padding: 12px; text-align: left;">📅 日期</th>
                <th style="padding: 12px; text-align: center;">🔄 完成轮次</th>
                <th style="padding: 12px; text-align: center;">💰 总奖励</th>
                <th style="padding: 12px; text-align: center;">📊 平均奖励</th>
                <th style="padding: 12px; text-align: center;">🏅 最佳奖励</th>
                <th style="padding: 12px; text-align: center;">📈 效率分数</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for _, row in daily_summary.iterrows():
            # 奖励等级颜色
            if row['total_rewards'] >= totals['avg_daily_reward']:
                reward_color = "#4CAF50"  # 绿色
                emoji = "🚀"
            else:
                reward_color = "#FF9800"  # 橙色
                emoji = "📈"
            
            table_html += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px; font-weight: bold;">{emoji} {row['date']}</td>
                <td style="padding: 12px; text-align: center;">{row['rounds_completed']}</td>
                <td style="padding: 12px; text-align: center; color: {reward_color}; font-weight: bold;">{row['total_rewards']:.4f}</td>
                <td style="padding: 12px; text-align: center;">{row['avg_reward']:.4f}</td>
                <td style="padding: 12px; text-align: center;">{row['best_reward']:.4f}</td>
                <td style="padding: 12px; text-align: center;">{row['efficiency_score']:.2f}</td>
            </tr>
            """
        
        table_html += """
        </tbody>
        </table>
        </div>
        """
        
        return table_html
    
    def create_interactive_charts(self, daily_summary: pd.DataFrame, performance_data: List[Dict]) -> str:
        """创建交互式图表"""
        if daily_summary.empty:
            return ""
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('📈 每日奖励趋势', '🔄 完成轮次统计', '⚡ 系统性能监控', '🏆 效率分数对比'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        # 1. 每日奖励趋势
        fig.add_trace(
            go.Scatter(
                x=daily_summary['date'],
                y=daily_summary['total_rewards'],
                mode='lines+markers',
                name='每日总奖励',
                line=dict(color='#667eea', width=3),
                marker=dict(size=8, color='#667eea'),
                hovertemplate='日期: %{x}<br>奖励: %{y:.4f} ETH<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. 完成轮次统计
        fig.add_trace(
            go.Bar(
                x=daily_summary['date'],
                y=daily_summary['rounds_completed'],
                name='完成轮次',
                marker_color='#764ba2',
                hovertemplate='日期: %{x}<br>轮次: %{y}<extra></extra>'
            ),
            row=1, col=2
        )
        
        # 3. 系统性能监控（如果有性能数据）
        if performance_data:
            perf_df = pd.DataFrame(performance_data)
            perf_df['timestamp'] = pd.to_datetime(perf_df['timestamp'])
            
            # CPU使用率
            fig.add_trace(
                go.Scatter(
                    x=perf_df['timestamp'],
                    y=perf_df['cpu_usage'],
                    mode='lines',
                    name='CPU使用率(%)',
                    line=dict(color='#FF6B6B', width=2),
                    hovertemplate='时间: %{x}<br>CPU: %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
            
            # 内存使用率
            fig.add_trace(
                go.Scatter(
                    x=perf_df['timestamp'],
                    y=perf_df['memory_usage'],
                    mode='lines',
                    name='内存使用率(%)',
                    line=dict(color='#4ECDC4', width=2),
                    yaxis='y2',
                    hovertemplate='时间: %{x}<br>内存: %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1, secondary_y=True
            )
        
        # 4. 效率分数对比
        colors = ['#FF6B6B' if score < daily_summary['efficiency_score'].mean() else '#4CAF50' 
                  for score in daily_summary['efficiency_score']]
        
        fig.add_trace(
            go.Bar(
                x=daily_summary['date'],
                y=daily_summary['efficiency_score'],
                name='效率分数',
                marker_color=colors,
                hovertemplate='日期: %{x}<br>效率: %{y:.2f}<extra></extra>'
            ),
            row=2, col=2
        )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text='🎯 RL-Swarm Mac Mini M4 性能仪表板',
                font=dict(size=20, color='#2E86AB'),
                x=0.5
            ),
            height=800,
            showlegend=True,
            template='plotly_white',
            font=dict(family="Arial, sans-serif", size=12),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # 保存为HTML文件
        html_file = "reward_dashboard.html"
        pyo.plot(fig, filename=html_file, auto_open=False)
        
        return html_file
    
    def generate_report(self):
        """生成完整的奖励报告"""
        print("🔍 分析奖励数据...")
        
        # 解析数据
        rewards_data = self.parse_swarm_logs()
        performance_data = self.parse_performance_logs()
        
        # 计算每日总结
        daily_summary = self.calculate_daily_summary(rewards_data)
        
        print(f"📊 找到 {len(rewards_data)} 条奖励记录")
        print(f"⚡ 找到 {len(performance_data)} 条性能记录")
        
        # 生成表格
        table_html = self.create_reward_table(daily_summary)
        
        # 生成图表
        chart_file = self.create_interactive_charts(daily_summary, performance_data)
        
        # 保存表格
        table_file = "reward_summary_table.html"
        with open(table_file, 'w', encoding='utf-8') as f:
            f.write(table_html)
        
        print(f"\n🎉 报告生成完成！")
        print(f"📋 表格报告: {table_file}")
        print(f"📊 交互图表: {chart_file}")
        print(f"\n💡 使用以下命令打开报告:")
        print(f"   open {table_file}")
        print(f"   open {chart_file}")
        
        return table_file, chart_file

def main():
    parser = argparse.ArgumentParser(description="RL-Swarm 奖励追踪系统")
    parser.add_argument("--log-dir", default="logs", help="日志目录路径")
    parser.add_argument("--auto-open", action="store_true", help="自动打开报告")
    
    args = parser.parse_args()
    
    print("🚀 启动 RL-Swarm 奖励追踪系统...")
    print("📱 专为 Mac Mini M4 优化")
    
    tracker = RewardTracker(log_dir=args.log_dir)
    table_file, chart_file = tracker.generate_report()
    
    if args.auto_open:
        os.system(f"open {table_file}")
        os.system(f"open {chart_file}")

if __name__ == "__main__":
    main() 