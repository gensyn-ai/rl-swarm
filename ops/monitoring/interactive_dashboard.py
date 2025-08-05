#!/usr/bin/env python3
"""
RL-Swarm 超级动态交互式图表系统
包含动画、过滤器、实时更新等高级功能
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.offline as pyo
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def create_super_interactive_dashboard():
    """创建超级交互式仪表板"""
    
    # 生成丰富的模拟数据
    data = generate_advanced_demo_data()
    
    # 创建多层级子图
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=(
            '🚀 实时奖励流 (可拖拽缩放)', '🎯 3D性能立体图', '📊 动态排名变化',
            '🔥 热力图时间序列', '⚡ CPU/内存双轴动画', '🏆 奖励分布直方图',
            '📈 累计收益瀑布图', '🎪 多维散点矩阵', '🌊 实时数据流'
        ),
        specs=[
            [{"secondary_y": False}, {"type": "scene"}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": True}, {"secondary_y": False}],
            [{"secondary_y": False}, {"secondary_y": False}, {"secondary_y": False}]
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    # 1. 实时奖励流 - 带动画和交互
    reward_trace = go.Scatter(
        x=data['timestamps'],
        y=data['rewards'],
        mode='lines+markers',
        name='💰 实时奖励',
        line=dict(
            color='#667eea', 
            width=3,
            shape='spline',  # 平滑曲线
            smoothing=0.3
        ),
        marker=dict(
            size=8,
            color=data['rewards'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="奖励值", x=1.02),
            line=dict(width=2, color='white')
        ),
        fill='tonexty',
        fillcolor='rgba(102, 126, 234, 0.1)',
        hovertemplate='<b>奖励流</b><br>' +
                     '时间: %{x}<br>' +
                     '奖励: %{y:.4f} ETH<br>' +
                     '排名: %{customdata[0]}<br>' +
                     '参与者: %{customdata[1]}<extra></extra>',
        customdata=list(zip(data['ranks'], data['participants']))
    )
    fig.add_trace(reward_trace, row=1, col=1)
    
    # 2. 3D性能立体图
    fig.add_trace(
        go.Scatter3d(
            x=data['cpu_usage'],
            y=data['memory_usage'],
            z=data['rewards'],
            mode='markers+lines',
            name='🎯 3D性能',
            marker=dict(
                size=5,
                color=data['efficiency_scores'],
                colorscale='Rainbow',
                opacity=0.8,
                line=dict(width=1, color='white')
            ),
            line=dict(color='#FF6B6B', width=2),
            hovertemplate='<b>3D性能视图</b><br>' +
                         'CPU: %{x:.1f}%<br>' +
                         '内存: %{y:.1f}%<br>' +
                         '奖励: %{z:.4f} ETH<br>' +
                         '效率: %{marker.color:.2f}<extra></extra>'
        ),
        row=1, col=2
    )
    
    # 3. 动态排名变化
    for i, hour in enumerate(range(0, 24, 4)):
        hour_data = data['hourly_ranks'][hour] if hour < len(data['hourly_ranks']) else []
        if hour_data:
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(hour_data))),
                    y=hour_data,
                    mode='lines+markers',
                    name=f'{hour:02d}:00',
                    line=dict(width=2),
                    marker=dict(size=6),
                    visible=(i == 0),  # 只显示第一个
                    hovertemplate=f'<b>{hour:02d}:00时段</b><br>' +
                                 '参与者: %{x}<br>' +
                                 '排名: %{y}<extra></extra>'
                ),
                row=1, col=3
            )
    
    # 4. 热力图时间序列
    heatmap_data = np.random.rand(7, 24) * 0.1  # 7天 x 24小时
    days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    hours = [f'{i:02d}:00' for i in range(24)]
    
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=hours[::2],  # 每2小时显示一次
            y=days,
            colorscale='Plasma',
            name='🔥 奖励热力图',
            hovertemplate='<b>奖励热力图</b><br>' +
                         '时间: %{x}<br>' +
                         '日期: %{y}<br>' +
                         '平均奖励: %{z:.4f}<extra></extra>'
        ),
        row=2, col=1
    )
    
    # 5. CPU/内存双轴动画
    fig.add_trace(
        go.Scatter(
            x=data['timestamps'],
            y=data['cpu_usage'],
            mode='lines',
            name='⚡ CPU使用率',
            line=dict(color='#FF6B6B', width=3),
            fill='tonexty',
            fillcolor='rgba(255, 107, 107, 0.1)',
            hovertemplate='<b>CPU监控</b><br>时间: %{x}<br>使用率: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['timestamps'],
            y=data['memory_usage'],
            mode='lines',
            name='💾 内存使用率',
            line=dict(color='#4ECDC4', width=3),
            yaxis='y2',
            fill='tonexty',
            fillcolor='rgba(78, 205, 196, 0.1)',
            hovertemplate='<b>内存监控</b><br>时间: %{x}<br>使用率: %{y:.1f}%<extra></extra>'
        ),
        row=2, col=2, secondary_y=True
    )
    
    # 6. 奖励分布直方图
    fig.add_trace(
        go.Histogram(
            x=data['rewards'],
            nbinsx=20,
            name='🏆 奖励分布',
            marker=dict(
                color='rgba(102, 126, 234, 0.7)',
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>奖励分布</b><br>' +
                         '奖励区间: %{x}<br>' +
                         '频次: %{y}<extra></extra>'
        ),
        row=2, col=3
    )
    
    # 7. 累计收益瀑布图
    cumulative_rewards = np.cumsum(data['rewards'])
    fig.add_trace(
        go.Waterfall(
            x=data['timestamps'][::10],  # 每10个点显示一次
            y=data['rewards'][::10],
            name='📈 收益瀑布',
            connector=dict(line=dict(color="rgb(63, 63, 63)")),
            increasing=dict(marker_color="green"),
            decreasing=dict(marker_color="red"),
            hovertemplate='<b>收益瀑布</b><br>' +
                         '时间: %{x}<br>' +
                         '变化: %{y:.4f} ETH<extra></extra>'
        ),
        row=3, col=1
    )
    
    # 8. 多维散点矩阵
    fig.add_trace(
        go.Scatter(
            x=data['efficiency_scores'],
            y=data['rewards'],
            mode='markers',
            name='🎪 效率vs奖励',
            marker=dict(
                size=10,
                color=data['ranks'],
                colorscale='Sunset',
                opacity=0.8,
                line=dict(width=1, color='white'),
                symbol='diamond'
            ),
            hovertemplate='<b>效率分析</b><br>' +
                         '效率分数: %{x:.2f}<br>' +
                         '奖励: %{y:.4f} ETH<br>' +
                         '排名: %{marker.color}<extra></extra>'
        ),
        row=3, col=2
    )
    
    # 9. 实时数据流模拟
    stream_data = data['rewards'][-50:]  # 最近50个数据点
    fig.add_trace(
        go.Scatter(
            y=stream_data,
            mode='lines+markers',
            name='🌊 数据流',
            line=dict(
                color='#50C878',
                width=2,
                dash='dash'
            ),
            marker=dict(
                size=4,
                color='#50C878'
            ),
            hovertemplate='<b>实时数据流</b><br>' +
                         '序号: %{x}<br>' +
                         '值: %{y:.4f}<extra></extra>'
        ),
        row=3, col=3
    )
    
    # 添加交互式控件和动画
    fig.update_layout(
        title=dict(
            text='🎯 RL-Swarm 超级动态交互式仪表板',
            font=dict(size=28, color='#2E86AB'),
            x=0.5
        ),
        height=1000,
        showlegend=True,
        template='plotly_white',
        font=dict(family="Arial, sans-serif", size=10),
        plot_bgcolor='rgba(248, 249, 250, 0.9)',
        paper_bgcolor='white',
        
        # 添加动画按钮
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=list([
                    dict(
                        args=[{"visible": [True] * 20}],  # 假设最多20个图表
                        label="🎬 播放动画",
                        method="restyle"
                    ),
                    dict(
                        args=[{"visible": [True if i % 2 == 0 else False for i in range(20)]}],
                        label="📊 奇数图表",
                        method="restyle"
                    ),
                    dict(
                        args=[{"visible": [True if i % 2 == 1 else False for i in range(20)]}],
                        label="📈 偶数图表",
                        method="restyle"
                    )
                ]),
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.02,
                yanchor="top"
            ),
        ],
        
        # 添加滑块控制
        sliders=[
            dict(
                active=23,
                currentvalue={"prefix": "时间段: "},
                pad={"t": 50},
                steps=[
                    dict(
                        label=f"{i:02d}:00",
                        method="restyle",
                        args=[{"visible": [j == i for j in range(6)]}]  # 对应排名变化图
                    ) for i in range(24)
                ]
            )
        ]
    )
    
    # 为3D图表设置场景
    fig.update_scenes(
        xaxis_title="CPU使用率 (%)",
        yaxis_title="内存使用率 (%)",
        zaxis_title="奖励 (ETH)",
        camera=dict(
            eye=dict(x=1.2, y=1.2, z=1.2)
        ),
        row=1, col=2
    )
    
    # 添加范围选择器
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1小时", step="hour", stepmode="backward"),
                dict(count=6, label="6小时", step="hour", stepmode="backward"),
                dict(count=1, label="1天", step="day", stepmode="backward"),
                dict(step="all", label="全部")
            ])
        ),
        row=1, col=1
    )
    
    # 保存为HTML
    html_file = "super_interactive_dashboard.html"
    
    # 添加自定义JavaScript增强交互性
    custom_js = """
    <script>
        // 添加更多交互功能
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 超级交互式仪表板已加载');
            
            // 自动刷新功能
            let autoRefresh = false;
            const refreshButton = document.createElement('button');
            refreshButton.innerHTML = '🔄 自动刷新';
            refreshButton.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-weight: bold;
                z-index: 1000;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                transition: all 0.3s ease;
            `;
            
            refreshButton.onmouseover = function() {
                this.style.transform = 'scale(1.05)';
                this.style.boxShadow = '0 6px 20px rgba(0,0,0,0.3)';
            };
            
            refreshButton.onmouseout = function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
            };
            
            refreshButton.onclick = function() {
                autoRefresh = !autoRefresh;
                this.innerHTML = autoRefresh ? '⏸️ 停止刷新' : '🔄 自动刷新';
                this.style.background = autoRefresh ? 
                    'linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)' : 
                    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
                
                if (autoRefresh) {
                    console.log('✅ 启动自动刷新');
                    startAutoRefresh();
                } else {
                    console.log('⏹️ 停止自动刷新');
                }
            };
            
            document.body.appendChild(refreshButton);
            
            function startAutoRefresh() {
                if (!autoRefresh) return;
                
                setTimeout(() => {
                    // 模拟数据更新
                    const plots = document.querySelectorAll('.plotly-graph-div');
                    plots.forEach(plot => {
                        if (plot.data) {
                            // 添加闪烁效果表示更新
                            plot.style.opacity = '0.5';
                            setTimeout(() => {
                                plot.style.opacity = '1';
                            }, 200);
                        }
                    });
                    
                    if (autoRefresh) {
                        startAutoRefresh();
                    }
                }, 3000);
            }
            
            // 添加键盘快捷键
            document.addEventListener('keydown', function(e) {
                if (e.ctrlKey || e.metaKey) {
                    switch(e.key) {
                        case 'r':
                            e.preventDefault();
                            refreshButton.click();
                            break;
                        case 'f':
                            e.preventDefault();
                            // 全屏模式
                            if (document.fullscreenElement) {
                                document.exitFullscreen();
                            } else {
                                document.documentElement.requestFullscreen();
                            }
                            break;
                    }
                }
            });
            
            // 添加性能指示器
            const perfIndicator = document.createElement('div');
            perfIndicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                z-index: 1000;
            `;
            document.body.appendChild(perfIndicator);
            
            setInterval(() => {
                const now = new Date();
                perfIndicator.innerHTML = `
                    🕒 ${now.toLocaleTimeString()}<br>
                    📊 图表: ${document.querySelectorAll('.plotly-graph-div').length}<br>
                    🔄 刷新: ${autoRefresh ? '开启' : '关闭'}
                `;
            }, 1000);
        });
    </script>
    """
    
    # 保存增强版HTML
    html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
    
    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 RL-Swarm 超级交互式仪表板</title>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .dashboard-container {{
                background: white;
                border-radius: 20px;
                padding: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                margin: 0 auto;
                max-width: 100%;
            }}
            .help-text {{
                position: fixed;
                bottom: 80px;
                right: 20px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                max-width: 200px;
                z-index: 999;
            }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            {html_content}
        </div>
        <div class="help-text">
            <strong>🎮 快捷键:</strong><br>
            Ctrl/Cmd + R: 切换刷新<br>
            Ctrl/Cmd + F: 全屏模式<br>
            鼠标滚轮: 缩放图表<br>
            拖拽: 平移图表
        </div>
        {custom_js}
    </body>
    </html>
    """
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    return html_file

def generate_advanced_demo_data():
    """生成高级演示数据"""
    print("🎲 生成高级交互演示数据...")
    
    # 生成30天的详细数据
    base_time = datetime.now() - timedelta(days=1)
    timestamps = []
    rewards = []
    cpu_usage = []
    memory_usage = []
    ranks = []
    participants = []
    efficiency_scores = []
    hourly_ranks = []
    
    # 生成每小时的数据
    for hour in range(24):
        for minute in range(0, 60, 5):  # 每5分钟一个数据点
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            timestamps.append(timestamp.strftime('%H:%M'))
            
            # 模拟奖励波动
            base_reward = 0.05 + 0.02 * np.sin(hour * np.pi / 12)  # 按小时周期变化
            noise = np.random.normal(0, 0.01)
            reward = max(0.01, base_reward + noise)
            rewards.append(reward)
            
            # 模拟系统性能
            base_cpu = 30 + 20 * np.sin(hour * np.pi / 12) + np.random.uniform(-10, 15)
            cpu_usage.append(max(5, min(95, base_cpu)))
            
            base_memory = 40 + 10 * np.cos(hour * np.pi / 8) + np.random.uniform(-8, 12)
            memory_usage.append(max(20, min(85, base_memory)))
            
            # 排名和参与者
            rank = np.random.randint(1, 50)
            ranks.append(rank)
            participants.append(np.random.randint(40, 120))
            
            # 效率分数
            efficiency = (reward / rank) * 100 + np.random.uniform(-5, 5)
            efficiency_scores.append(max(0, efficiency))
    
    # 生成每小时的排名分布
    for hour in range(24):
        hour_ranks = [np.random.randint(1, 50) for _ in range(20)]
        hourly_ranks.append(sorted(hour_ranks))
    
    return {
        'timestamps': timestamps,
        'rewards': rewards,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'ranks': ranks,
        'participants': participants,
        'efficiency_scores': efficiency_scores,
        'hourly_ranks': hourly_ranks
    }

if __name__ == "__main__":
    print("🚀 启动超级动态交互式图表系统...")
    
    dashboard_file = create_super_interactive_dashboard()
    
    print(f"\n🎉 超级交互式仪表板创建完成！")
    print(f"📊 文件: {dashboard_file}")
    print(f"\n✨ 功能特性:")
    print(f"   🎮 键盘快捷键控制")
    print(f"   🔄 自动刷新功能")
    print(f"   📱 响应式设计")
    print(f"   🎬 动画效果")
    print(f"   🎯 3D可视化")
    print(f"   📊 多图表联动")
    print(f"   🔍 缩放和平移")
    print(f"   💫 实时数据流")
    print(f"\n💡 打开仪表板:")
    print(f"   open {dashboard_file}")
    
    # 自动打开
    import os
    os.system(f"open {dashboard_file}") 