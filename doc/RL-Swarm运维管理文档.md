# RL-Swarm 运维管理文档

## 📋 文档概述

本文档详细介绍RL-Swarm项目的所有运维工具、脚本和配置文件，为系统管理员和开发者提供完整的运维指南。

## 🗂️ 运维文件结构

### 📁 核心运维文件分类

```
rl-swarm/
├── 🔧 Apple Silicon兼容性修复
│   ├── fix_mac_accelerate.py
│   └── fix_mac_dependencies.sh
│
├── 📧 邮件通知系统  
│   ├── notification_system.py        # 原版通知系统
│   ├── notification_system_v2.py     # yagmail优化版 ⭐
│   ├── test_notification.py          # 通知测试套件
│   ├── setup_notifications.py        # 配置向导
│   ├── test_yagmail.py              # yagmail测试
│   ├── diagnose_email.py            # 邮件诊断工具
│   └── notification_config.json      # 邮件配置文件
│
├── 📊 系统监控与可视化
│   ├── real_time_monitor.py          # 实时监控系统 ⭐
│   ├── interactive_dashboard.py      # 交互式仪表板
│   ├── launch_monitor.py            # 监控启动器
│   ├── reward_tracker.py            # 奖励追踪器
│   ├── enhanced_reward_demo.py       # 增强版演示
│   └── test_monitor.py              # 监控测试
│
├── 🛡️ 预防性维护
│   └── preemptive_fixes.py          # 系统检查和修复 ⭐
│
├── 🚀 启动脚本
│   ├── run_rl_swarm_mac.sh          # Mac Mini M4优化版 ⭐
│   ├── run_rl_swarm.sh              # 通用版本
│   ├── run_rl_swarm_uv.sh           # UV包管理器版本
│   ├── run_rl_swarm_local.sh        # 本地测试版本
│   └── start_all_nodes.sh           # 多节点启动
│
├── 💾 数据存储
│   ├── realtime_data.db             # 实时监控数据
│   └── rewards.db                   # 奖励数据
│
├── 📄 生成报告
│   ├── super_interactive_dashboard.html
│   ├── comprehensive_reward_dashboard.html
│   ├── detailed_reward_report.html
│   ├── reward_dashboard.html
│   └── reward_summary_table.html
│
└── ⚙️ 配置文件
    ├── pyproject.toml               # 项目依赖配置
    ├── requirements-cpu.txt         # CPU版本依赖
    ├── requirements-gpu.txt         # GPU版本依赖
    └── docker-compose.yaml          # Docker配置
```

## 🔧 核心运维组件详解

### 1. Apple Silicon兼容性修复

#### `fix_mac_accelerate.py` ⭐
**功能**: 修复Apple Silicon上accelerate库的兼容性问题
```python
# 主要功能
- monkey patch修复 UnboundLocalError
- 应用MPS优化设置
- 自动检测Apple Silicon环境
```

**使用方法**:
```bash
python fix_mac_accelerate.py
```

#### `fix_mac_dependencies.sh`
**功能**: 修复Mac依赖问题的一键脚本
```bash
./fix_mac_dependencies.sh
```

### 2. 邮件通知系统

#### `notification_system_v2.py` ⭐ (推荐)
**功能**: 基于yagmail的邮件通知系统
```python
# 核心功能
- 训练错误自动通知
- 性能异常监控告警
- 训练停滞检测
- 多级别通知(紧急/错误/警告/信息)
- HTML格式邮件
```

**配置文件**: `notification_config.json`
```json
{
  "email": {
    "enabled": true,
    "sender_email": "zhilinchn@126.com",
    "recipient_email": "zhilinchn@126.com",
    "sender_password": "SMTP授权码"
  }
}
```

**使用方法**:
```bash
# 配置邮件
python setup_notifications.py

# 测试邮件
python test_notification.py quick

# 邮件诊断
python diagnose_email.py
```

### 3. 系统监控与可视化

#### `real_time_monitor.py` ⭐
**功能**: 实时监控系统，集成邮件通知
```python
# 监控功能
- 实时性能监控 (CPU/内存)
- 训练进度跟踪
- 自动异常检测
- Web界面 (http://localhost:5000)
- 邮件告警集成
```

**启动方法**:
```bash
python real_time_monitor.py
```

#### `interactive_dashboard.py`
**功能**: 交互式仪表板生成器
```python
# 9种图表类型
- 实时奖励流
- 3D性能立体图
- 动态排名变化
- 热力图时间序列
- CPU/内存双轴动画
```

#### `launch_monitor.py`
**功能**: 监控系统启动管理器
```bash
python launch_monitor.py
# 提供菜单选择不同监控功能
```

### 4. 预防性维护

#### `preemptive_fixes.py` ⭐
**功能**: 系统健康检查和预防性修复
```python
# 检查项目
- 磁盘空间检查 (最少10GB)
- 内存使用检查 (建议4GB+)
- 网络连接测试
- 权限修复
- PyTorch优化设置
- HuggingFace缓存管理
- 依赖完整性检查
```

**运行方法**:
```bash
python preemptive_fixes.py
```

### 5. 启动脚本

#### `run_rl_swarm_mac.sh` ⭐ (Mac Mini M4专用)
**功能**: Mac Mini M4优化的训练启动脚本
```bash
# 集成功能
- Apple Silicon兼容性修复
- 智能资源检测
- 内存优化配置
- 性能监控集成
- 错误自动处理
- 邮件通知集成
```

**使用方法**:
```bash
chmod +x run_rl_swarm_mac.sh
./run_rl_swarm_mac.sh
```

#### 其他启动脚本对比

| 脚本 | 适用环境 | 特点 |
|------|---------|------|
| `run_rl_swarm_mac.sh` | Mac Mini M4 | Apple Silicon优化，集成监控 |
| `run_rl_swarm.sh` | 通用Linux/Mac | 标准启动脚本 |
| `run_rl_swarm_uv.sh` | UV环境 | 使用UV包管理器 |
| `run_rl_swarm_local.sh` | 本地测试 | 简化配置，快速测试 |

## 🚀 运维操作手册

### 日常监控流程

#### 1. 系统健康检查
```bash
# 每日执行
python preemptive_fixes.py
```

#### 2. 启动训练
```bash
# Mac Mini M4 (推荐)
./run_rl_swarm_mac.sh

# 其他环境
./run_rl_swarm.sh
```

#### 3. 实时监控
```bash
# 启动监控面板
python real_time_monitor.py

# 访问Web界面
open http://localhost:5000
```

#### 4. 生成报告
```bash
# 生成交互式仪表板
python interactive_dashboard.py

# 启动管理器选择功能
python launch_monitor.py
```

### 故障排除流程

#### 🚨 训练错误处理
1. **自动通知**: 系统会自动发送邮件到 `zhilinchn@126.com`
2. **日志检查**: 查看 `logs/swarm.log` 和 `logs/performance.log`
3. **兼容性修复**: 运行 `python fix_mac_accelerate.py`
4. **依赖修复**: 运行 `./fix_mac_dependencies.sh`

#### 📧 邮件通知问题
```bash
# 诊断邮件连接
python diagnose_email.py

# 重新配置
python setup_notifications.py

# 测试发送
python test_yagmail.py
```

#### 📊 监控问题
```bash
# 测试监控功能
python test_monitor.py

# 检查数据库
ls -la *.db

# 重启监控
python real_time_monitor.py
```

### 性能优化建议

#### Mac Mini M4 特定优化
1. **内存管理**: 确保16GB内存高效使用
2. **CPU调度**: 4个性能核心优化配置
3. **MPS加速**: Apple Silicon GPU加速
4. **缓存优化**: HuggingFace缓存管理

#### 监控配置优化
1. **数据清理**: 定期清理旧的监控数据
2. **报告归档**: 保存重要的性能报告
3. **告警阈值**: 根据实际情况调整告警参数

## 📁 配置文件说明

### `notification_config.json` - 邮件配置
```json
{
  "email": {
    "enabled": true,                    // 是否启用邮件
    "smtp_server": "smtp.126.com",      // SMTP服务器
    "smtp_port": 587,                   // SMTP端口
    "sender_email": "zhilinchn@126.com", // 发件人
    "sender_password": "授权码",         // SMTP授权码
    "recipient_email": "zhilinchn@126.com", // 收件人
    "use_tls": true                     // 是否使用TLS
  }
}
```

### `pyproject.toml` - 项目依赖
```toml
[project]
dependencies = [
    "transformers>=4.46.0",  // 核心ML库
    "hivemind",              // 分布式训练
    "yagmail",               // 邮件发送 (新增)
    "flask",                 // Web监控 (新增)
    "psutil"                 // 系统监控 (新增)
]
```

## 🔄 自动化运维

### 系统启动时自动运行
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
alias rl-start="cd /Users/mac/work/gensyn/rl-swarm && ./run_rl_swarm_mac.sh"
alias rl-monitor="cd /Users/mac/work/gensyn/rl-swarm && python real_time_monitor.py"
alias rl-check="cd /Users/mac/work/gensyn/rl-swarm && python preemptive_fixes.py"
```

### 定时任务 (Cron)
```bash
# 编辑 crontab
crontab -e

# 每小时执行系统检查
0 * * * * cd /Users/mac/work/gensyn/rl-swarm && python preemptive_fixes.py

# 每天生成报告
0 6 * * * cd /Users/mac/work/gensyn/rl-swarm && python interactive_dashboard.py
```

## 📞 技术支持

### 日志文件位置
- 训练日志: `logs/swarm.log`
- 性能日志: `logs/performance.log`
- 预防性修复日志: `logs/preemptive_fixes.log`

### 常见问题解决
1. **Apple Silicon兼容性**: 运行 `python fix_mac_accelerate.py`
2. **邮件发送失败**: 运行 `python diagnose_email.py`
3. **依赖冲突**: 运行 `./fix_mac_dependencies.sh`
4. **性能问题**: 运行 `python preemptive_fixes.py`

### 联系方式
- 邮件通知: `zhilinchn@126.com`
- 监控面板: `http://localhost:5000`
- 文档位置: `doc/` 目录

## 🔮 未来扩展

### 计划功能
1. **短信通知**: 集成阿里云/腾讯云短信服务
2. **Webhook集成**: 企业微信/钉钉机器人通知
3. **集群管理**: 多节点自动化部署
4. **AI诊断**: 智能故障分析和建议

### 贡献指南
参考 `CONTRIBUTING.md` 文件，了解如何为运维系统贡献代码。

---

**📝 文档版本**: v2.0  
**🔄 更新时间**: 2025-06-25  
**👥 维护团队**: RL-Swarm 运维组 