#!/usr/bin/env python3
"""
RL-Swarm 增强版奖励展示系统
生成更丰富的模拟数据来展示完整功能
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime, timedelta
import random

def generate_rich_demo_data():
    """生成丰富的演示数据"""
    print("🎲 生成丰富的演示数据...")
    
    rewards_data = []
    performance_data = []
    base_time = datetime.now() - timedelta(days=30)  # 30天数据
    
    # 模拟30天的训练数据
    for day in range(30):
        date = base_time + timedelta(days=day)
        
        # 周末和工作日的不同模式
        is_weekend = date.weekday() >= 5
        is_holiday = day in [7, 14, 21]  # 模拟一些特殊日期
        
        # 每日轮次数：周末更多，假期更少
        if is_holiday:
            rounds_per_day = np.random.randint(5, 12)
        elif is_weekend:
            rounds_per_day = np.random.randint(15, 25)
        else:
            rounds_per_day = np.random.randint(8, 18)
        
        daily_rewards = []
        
        for round_num in range(rounds_per_day):
            # 模拟学习效果：随时间增长
            learning_factor = 1 + (day / 30) * 0.5
            
            # 基础奖励随技能提升
            base_reward = 0.05 + (day * 0.003) + np.random.uniform(-0.01, 0.02)
            
            # 周末奖励加成
            if is_weekend:
                base_reward *= 1.2
            
            # 假期期间可能表现不稳定
            if is_holiday:
                base_reward *= np.random.uniform(0.7, 1.3)
            
            # 一天中的时间影响（模拟精力状态）
            hour = np.random.randint(8, 23)
            if 9 <= hour <= 11 or 14 <= hour <= 16:  # 精力充沛时间
                time_bonus = 1.1
            elif hour >= 22:  # 深夜可能表现下降
                time_bonus = 0.9
            else:
                time_bonus = 1.0
            
            final_reward = base_reward * learning_factor * time_bonus
            final_reward = max(0.01, final_reward)  # 确保最小奖励
            
            # 排名：表现好的时候排名更高
            if final_reward > 0.1:
                rank = np.random.randint(1, 15)
            elif final_reward > 0.05:
                rank = np.random.randint(10, 30)
            else:
                rank = np.random.randint(20, 50)
            
            timestamp = date.replace(hour=hour, minute=np.random.randint(0, 59))
            
            rewards_data.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'round': 800 + day * 20 + round_num,
                'stage': np.random.randint(0, 4),
                'reward': round(final_reward, 4),
                'rank': rank,
                'participants': np.random.randint(40, 120),
                'day_type': '周末' if is_weekend else ('假期' if is_holiday else '工作日')
            })
            
            daily_rewards.append(final_reward)
        
        # 生成对应的性能数据（每小时一次）
        for hour in range(8, 24):
            # CPU使用率：训练时更高
            if len(daily_rewards) > 0 and hour >= 9:
                cpu_base = 35 + np.random.uniform(-10, 25)
                # 训练强度影响CPU
                training_intensity = len(daily_rewards) / rounds_per_day
                cpu_usage = min(95, cpu_base + training_intensity * 20)
            else:
                cpu_usage = 5 + np.random.uniform(-2, 15)
            
            # 内存使用：随训练进度变化
            if len(daily_rewards) > 0:
                memory_base = 40 + (len(daily_rewards) / rounds_per_day) * 30
                memory_usage = memory_base + np.random.uniform(-10, 15)
            else:
                memory_usage = 25 + np.random.uniform(-5, 15)
            
            memory_usage = max(15, min(85, memory_usage))
            
            perf_timestamp = date.replace(hour=hour, minute=30)
            performance_data.append({
                'timestamp': perf_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'cpu_usage': round(cpu_usage, 2),
                'memory_usage': round(memory_usage, 2),
                'memory_free': round(100 - memory_usage, 2)
            })
    
    return rewards_data, performance_data

def create_comprehensive_dashboard():
    """创建全面的仪表板"""
    rewards_data, performance_data = generate_rich_demo_data()
    
    # 转换为DataFrame
    df_rewards = pd.DataFrame(rewards_data)
    df_perf = pd.DataFrame(performance_data)
    
    df_rewards['timestamp'] = pd.to_datetime(df_rewards['timestamp'])
    df_rewards['date'] = df_rewards['timestamp'].dt.date
    df_perf['timestamp'] = pd.to_datetime(df_perf['timestamp'])
    
    # 计算每日统计
    daily_stats = df_rewards.groupby('date').agg({
        'round': 'count',
        'reward': ['sum', 'mean', 'max'],
        'rank': 'mean',
        'participants': 'mean'
    }).round(4)
    
    daily_stats.columns = ['rounds_completed', 'total_rewards', 'avg_reward', 'best_reward', 'avg_rank', 'avg_participants']
    daily_stats['efficiency_score'] = (daily_stats['total_rewards'] / daily_stats['avg_rank'] * 100).round(2)
    daily_stats = daily_stats.reset_index()
    
    # 创建大型仪表板
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=(
            '💰 每日总奖励趋势', '🏆 排名表现', '⚡ CPU & 内存使用',
            '📊 奖励分布热图', '🔄 完成轮次统计', '📈 累计收益',
            '🎯 效率分数走势', '📅 周统计对比', '🚀 性能优化建议'
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": True}],
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    # 1. 每日总奖励趋势
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['total_rewards'],
            mode='lines+markers',
            name='每日总奖励',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6, color='#667eea'),
            fill='tonexty',
            fillcolor='rgba(102, 126, 234, 0.1)',
            hovertemplate='日期: %{x}<br>奖励: %{y:.4f} ETH<extra></extra>'
        ),
        row=1, col=1
    )
    
    # 2. 排名表现散点图
    fig.add_trace(
        go.Scatter(
            x=df_rewards['reward'],
            y=df_rewards['rank'],
            mode='markers',
            name='奖励vs排名',
            marker=dict(
                size=8,
                color=df_rewards['reward'],
                colorscale='Viridis',
                showscale=False,
                opacity=0.7
            ),
            hovertemplate='奖励: %{x:.4f}<br>排名: %{y}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. CPU和内存使用（双Y轴）
    # 采样性能数据以避免过多点
    perf_sample = df_perf.sample(min(100, len(df_perf))).sort_values('timestamp')
    
    fig.add_trace(
        go.Scatter(
            x=perf_sample['timestamp'],
            y=perf_sample['cpu_usage'],
            mode='lines',
            name='CPU使用率(%)',
            line=dict(color='#FF6B6B', width=2),
            hovertemplate='时间: %{x}<br>CPU: %{y:.1f}%<extra></extra>'
        ),
        row=1, col=3
    )
    
    fig.add_trace(
        go.Scatter(
            x=perf_sample['timestamp'],
            y=perf_sample['memory_usage'],
            mode='lines',
            name='内存使用率(%)',
            line=dict(color='#4ECDC4', width=2),
            yaxis='y2',
            hovertemplate='时间: %{x}<br>内存: %{y:.1f}%<extra></extra>'
        ),
        row=1, col=3, secondary_y=True
    )
    
    # 4. 奖励分布热图（按小时和日期）
    df_rewards['hour'] = df_rewards['timestamp'].dt.hour
    df_rewards['day_name'] = df_rewards['timestamp'].dt.day_name()
    
    # 简化热图数据
    heatmap_data = df_rewards.groupby(['day_name', 'hour'])['reward'].mean().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='day_name', columns='hour', values='reward').fillna(0)
    
    # 只显示关键数据
    if len(heatmap_pivot) > 0:
        fig.add_trace(
            go.Heatmap(
                z=heatmap_pivot.values[:5, :12],  # 限制大小
                x=list(range(8, 20)),
                y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                colorscale='Viridis',
                name='奖励热图',
                hovertemplate='时间: %{x}:00<br>星期: %{y}<br>平均奖励: %{z:.4f}<extra></extra>'
            ),
            row=2, col=1
        )
    
    # 5. 完成轮次柱状图
    fig.add_trace(
        go.Bar(
            x=daily_stats['date'][-14:],  # 最近14天
            y=daily_stats['rounds_completed'][-14:],
            name='完成轮次',
            marker_color='#764ba2',
            hovertemplate='日期: %{x}<br>轮次: %{y}<extra></extra>'
        ),
        row=2, col=2
    )
    
    # 6. 累计收益
    daily_stats['cumulative_rewards'] = daily_stats['total_rewards'].cumsum()
    fig.add_trace(
        go.Scatter(
            x=daily_stats['date'],
            y=daily_stats['cumulative_rewards'],
            mode='lines+markers',
            name='累计收益',
            line=dict(color='#50C878', width=3),
            marker=dict(size=5, color='#50C878'),
            fill='tozeroy',
            fillcolor='rgba(80, 200, 120, 0.1)',
            hovertemplate='日期: %{x}<br>累计: %{y:.4f} ETH<extra></extra>'
        ),
        row=2, col=3
    )
    
    # 7. 效率分数走势
    colors = ['#FF6B6B' if score < daily_stats['efficiency_score'].mean() else '#4CAF50' 
              for score in daily_stats['efficiency_score']]
    
    fig.add_trace(
        go.Bar(
            x=daily_stats['date'][-10:],  # 最近10天
            y=daily_stats['efficiency_score'][-10:],
            name='效率分数',
            marker_color=colors[-10:],
            hovertemplate='日期: %{x}<br>效率: %{y:.2f}<extra></extra>'
        ),
        row=3, col=1
    )
    
    # 8. 周统计对比
    df_rewards['week'] = df_rewards['timestamp'].dt.isocalendar().week
    weekly_stats = df_rewards.groupby('week')['reward'].agg(['sum', 'count']).reset_index()
    weekly_stats.columns = ['week', 'total_reward', 'total_rounds']
    
    if len(weekly_stats) > 0:
        fig.add_trace(
            go.Scatter(
                x=weekly_stats['week'][-4:],  # 最近4周
                y=weekly_stats['total_reward'][-4:],
                mode='lines+markers',
                name='周收益',
                line=dict(color='#FF9500', width=3),
                marker=dict(size=8, color='#FF9500'),
                hovertemplate='第%{x}周<br>收益: %{y:.4f} ETH<extra></extra>'
            ),
            row=3, col=2
        )
    
    # 9. 性能优化建议（文本信息）
    avg_cpu = df_perf['cpu_usage'].mean()
    avg_memory = df_perf['memory_usage'].mean()
    total_reward = daily_stats['total_rewards'].sum()
    
    suggestions = []
    if avg_cpu > 70:
        suggestions.append("🔥 CPU使用率较高，考虑调整并行度")
    if avg_memory > 75:
        suggestions.append("💾 内存使用较多，可优化缓存设置")
    if total_reward > 5:
        suggestions.append("🚀 表现优秀！继续保持")
    else:
        suggestions.append("📈 可以尝试优化训练策略")
    
    suggestion_text = "<br>".join(suggestions)
    
    fig.add_annotation(
        text=f"<b>💡 性能优化建议</b><br><br>{suggestion_text}<br><br>" +
             f"📊 平均CPU: {avg_cpu:.1f}%<br>" +
             f"💾 平均内存: {avg_memory:.1f}%<br>" +
             f"💰 总收益: {total_reward:.4f} ETH",
        xref="x domain", yref="y domain",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False,
        font=dict(size=12, color="#2E86AB"),
        bgcolor="rgba(230, 230, 250, 0.8)",
        bordercolor="#2E86AB",
        borderwidth=2,
        row=3, col=3
    )
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text='🎯 RL-Swarm Mac Mini M4 完整性能仪表板',
            font=dict(size=24, color='#2E86AB'),
            x=0.5
        ),
        height=1200,
        showlegend=True,
        template='plotly_white',
        font=dict(family="Arial, sans-serif", size=10),
        plot_bgcolor='rgba(248, 249, 250, 0.8)',
        paper_bgcolor='white'
    )
    
    # 保存文件
    html_file = "comprehensive_reward_dashboard.html"
    pyo.plot(fig, filename=html_file, auto_open=False)
    
    # 生成详细的统计表格
    create_detailed_table(daily_stats, total_reward, avg_cpu, avg_memory)
    
    return html_file

def create_detailed_table(daily_stats, total_reward, avg_cpu, avg_memory):
    """创建详细的统计表格"""
    
    # 计算更多统计信息
    best_day = daily_stats.loc[daily_stats['total_rewards'].idxmax()]
    worst_day = daily_stats.loc[daily_stats['total_rewards'].idxmin()]
    avg_daily = daily_stats['total_rewards'].mean()
    
    table_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏆 RL-Swarm 详细奖励报告</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                padding: 30px;
            }}
            .stat-card {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                border-left: 5px solid #667eea;
            }}
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #2E86AB;
                margin: 10px 0;
            }}
            .table-container {{
                padding: 0 30px 30px;
                overflow-x: auto;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            th {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                padding: 12px 15px;
                border-bottom: 1px solid #eee;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            .highlight {{
                background: linear-gradient(45deg, #FFD700, #FFA500);
                color: white;
                font-weight: bold;
            }}
            .performance-indicator {{
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                margin-right: 8px;
            }}
            .excellent {{ background: #4CAF50; }}
            .good {{ background: #FFC107; }}
            .poor {{ background: #F44336; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 RL-Swarm Mac Mini M4 详细奖励报告</h1>
                <p>专业的分布式训练性能分析</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">💰 总收益</div>
                    <div class="stat-value">{total_reward:.4f} ETH</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">📅 日均收益</div>
                    <div class="stat-value">{avg_daily:.4f} ETH</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">🔥 平均CPU</div>
                    <div class="stat-value">{avg_cpu:.1f}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">💾 平均内存</div>
                    <div class="stat-value">{avg_memory:.1f}%</div>
                </div>
            </div>
            
            <div class="table-container">
                <h2>📊 每日详细统计</h2>
                <table>
                    <thead>
                        <tr>
                            <th>📅 日期</th>
                            <th>🔄 轮次</th>
                            <th>💰 总奖励</th>
                            <th>📊 平均奖励</th>
                            <th>🏅 最佳奖励</th>
                            <th>🎯 效率分数</th>
                            <th>📈 表现</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # 添加每日数据行
    for _, row in daily_stats.iterrows():
        # 性能评级
        if row['efficiency_score'] >= daily_stats['efficiency_score'].quantile(0.8):
            performance_class = "excellent"
            performance_text = "优秀"
        elif row['efficiency_score'] >= daily_stats['efficiency_score'].quantile(0.5):
            performance_class = "good"
            performance_text = "良好"
        else:
            performance_class = "poor"
            performance_text = "一般"
        
        # 高亮最佳和最差日期
        row_class = ""
        if row['date'] == best_day['date']:
            row_class = "highlight"
        
        table_html += f"""
        <tr class="{row_class}">
            <td>{row['date']}</td>
            <td>{row['rounds_completed']}</td>
            <td>{row['total_rewards']:.4f}</td>
            <td>{row['avg_reward']:.4f}</td>
            <td>{row['best_reward']:.4f}</td>
            <td>{row['efficiency_score']:.2f}</td>
            <td><span class="performance-indicator {performance_class}"></span>{performance_text}</td>
        </tr>
        """
    
    table_html += f"""
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                    <h3>🎯 关键洞察</h3>
                    <ul style="line-height: 1.8;">
                        <li><strong>🚀 最佳表现日：</strong>{best_day['date']} (收益: {best_day['total_rewards']:.4f} ETH)</li>
                        <li><strong>📉 最低表现日：</strong>{worst_day['date']} (收益: {worst_day['total_rewards']:.4f} ETH)</li>
                        <li><strong>📈 改进空间：</strong>{((best_day['total_rewards'] - worst_day['total_rewards']) / worst_day['total_rewards'] * 100):.1f}% 提升潜力</li>
                        <li><strong>🏆 总训练轮次：</strong>{daily_stats['rounds_completed'].sum()} 轮</li>
                        <li><strong>⚡ 系统效率：</strong>{'高效运行' if avg_cpu < 70 and avg_memory < 75 else '需要优化'}</li>
                    </ul>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("detailed_reward_report.html", 'w', encoding='utf-8') as f:
        f.write(table_html)

if __name__ == "__main__":
    print("🚀 生成增强版 RL-Swarm 奖励仪表板...")
    print("📊 包含30天完整模拟数据")
    
    dashboard_file = create_comprehensive_dashboard()
    
    print(f"\n🎉 增强版报告生成完成！")
    print(f"📊 交互式仪表板: {dashboard_file}")
    print(f"📋 详细报告: detailed_reward_report.html")
    print(f"\n💡 打开报告:")
    print(f"   open {dashboard_file}")
    print(f"   open detailed_reward_report.html")
    
    # 自动打开
    import os
    os.system(f"open {dashboard_file}")
    os.system("open detailed_reward_report.html") 