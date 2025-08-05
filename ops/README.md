# RL-Swarm 运维管理中心

## 📁 目录结构

```
ops/
├── 🚀 ops_manager.py              # 统一运维管理控制台 ⭐
├── 📚 README.md                   # 本文档
├── 
├── 📁 scripts/                    # 启动脚本
│   ├── run_rl_swarm_mac.sh       # Mac Mini M4优化训练脚本 ⭐
│   └── start_all_nodes.sh        # 多节点启动脚本
│
├── 📁 fixes/                      # 修复工具
│   ├── fix_mac_accelerate.py     # Apple Silicon兼容性修复 ⭐
│   ├── fix_mac_dependencies.sh   # 依赖修复脚本
│   └── preemptive_fixes.py       # 预防性系统检查 ⭐
│
├── 📁 notifications/              # 邮件通知系统
│   ├── notification_system_v2.py # yagmail邮件系统 ⭐
│   ├── setup_notifications.py    # 邮件配置向导
│   ├── test_yagmail.py          # yagmail测试
│   ├── diagnose_email.py        # 邮件诊断工具
│   ├── test_notification.py     # 通知测试套件
│   └── notification_system.py   # 原版邮件系统
│
├── 📁 monitoring/                 # 监控与可视化
│   ├── real_time_monitor.py      # 实时监控系统 ⭐
│   ├── interactive_dashboard.py  # 交互式仪表板
│   ├── launch_monitor.py        # 监控启动器
│   ├── reward_tracker.py        # 奖励追踪器
│   ├── enhanced_reward_demo.py   # 增强版演示
│   ├── test_monitor.py          # 监控测试
│   ├── realtime_data.db         # 实时监控数据
│   ├── rewards.db               # 奖励数据
│   └── *.html                   # 生成的报告文件
│
├── 📁 config/                     # 配置文件
│   └── notification_config.json  # 邮件通知配置
│
└── 📁 docs/                       # 运维文档
    ├── RL-Swarm运维管理文档.md
    ├── Apple-Silicon-兼容性问题解决方案.md
    └── 问题解决和通知系统部署总结.md
```

## 🚀 快速开始

### 启动运维管理中心
```bash
cd ops
python ops_manager.py
```

这将启动一个交互式菜单，提供以下功能：

## 🔧 主要功能

### 1. 系统修复与检查
- **Apple Silicon兼容性修复**: 修复accelerate库在ARM64上的问题
- **依赖问题修复**: 一键修复Mac依赖问题
- **系统预防性检查**: 磁盘、内存、网络等全面检查

### 2. 邮件通知系统
- **配置邮件通知**: 交互式配置SMTP设置
- **测试邮件发送**: 验证邮件通知功能
- **邮件诊断工具**: 排查邮件发送问题

### 3. 监控与可视化
- **实时监控**: Web界面监控训练状态
- **交互式仪表板**: 生成丰富的可视化报告
- **奖励数据追踪**: 分析训练奖励趋势

### 4. 训练管理
- **Mac优化训练**: 专门优化的Mac Mini M4训练脚本
- **多节点训练**: 分布式训练管理
- **监控功能测试**: 验证监控系统

## 🛠️ 直接使用脚本

### Apple Silicon修复
```bash
# 修复兼容性问题
python ops/fixes/fix_mac_accelerate.py

# 修复依赖问题
./ops/fixes/fix_mac_dependencies.sh

# 系统健康检查
python ops/fixes/preemptive_fixes.py
```

### 邮件通知
```bash
# 配置邮件
python ops/notifications/setup_notifications.py

# 测试邮件
python ops/notifications/test_yagmail.py

# 诊断问题
python ops/notifications/diagnose_email.py
```

### 监控系统
```bash
# 启动实时监控
python ops/monitoring/real_time_monitor.py
# 访问: http://localhost:5000

# 生成仪表板
python ops/monitoring/interactive_dashboard.py

# 奖励追踪
python ops/monitoring/reward_tracker.py
```

### 训练启动
```bash
# Mac优化训练 (推荐)
./ops/scripts/run_rl_swarm_mac.sh

# 多节点训练
./ops/scripts/start_all_nodes.sh
```

## ⚙️ 配置说明

### 邮件通知配置 (`config/notification_config.json`)
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

## 📊 监控数据

### 数据库文件
- `monitoring/realtime_data.db`: 实时性能和训练数据
- `monitoring/rewards.db`: 历史奖励数据

### 生成报告
- `monitoring/*.html`: 可视化报告文件
- 通过Web界面访问: http://localhost:5000

## 🚨 故障排除

### 常见问题快速解决
```bash
# Apple Silicon兼容性问题
python ops/fixes/fix_mac_accelerate.py

# 邮件发送失败
python ops/notifications/diagnose_email.py

# 监控启动失败
python ops/monitoring/test_monitor.py

# 依赖冲突
./ops/fixes/fix_mac_dependencies.sh
```

### 日志位置
- 训练日志: `../logs/swarm.log`
- 性能日志: `../logs/performance.log`
- 系统日志: `../logs/preemptive_fixes.log`

## 📚 文档资源

### 运维文档
- `docs/RL-Swarm运维管理文档.md`: 完整运维指南
- `docs/Apple-Silicon-兼容性问题解决方案.md`: 兼容性问题详解
- `docs/问题解决和通知系统部署总结.md`: 部署总结

### 在线资源
- 实时监控: http://localhost:5000
- 项目根目录: `../README.md`

## 🔄 自动化运维

### 推荐工作流程
1. **每日检查**: `python ops/fixes/preemptive_fixes.py`
2. **启动训练**: `./ops/scripts/run_rl_swarm_mac.sh`  
3. **监控训练**: `python ops/monitoring/real_time_monitor.py`
4. **生成报告**: `python ops/monitoring/interactive_dashboard.py`

### 系统别名设置
```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
alias ops="cd /Users/mac/work/gensyn/rl-swarm/ops && python ops_manager.py"
alias rl-train="cd /Users/mac/work/gensyn/rl-swarm && ./ops/scripts/run_rl_swarm_mac.sh"
alias rl-monitor="cd /Users/mac/work/gensyn/rl-swarm && python ops/monitoring/real_time_monitor.py"
alias rl-check="cd /Users/mac/work/gensyn/rl-swarm && python ops/fixes/preemptive_fixes.py"
```

## 📞 技术支持

- **邮件通知**: zhilinchn@126.com (配置后自动发送告警)
- **监控面板**: http://localhost:5000
- **运维中心**: `python ops_manager.py`

---

**🎯 运维目标**: 提供稳定、高效、智能的RL-Swarm运维环境  
**🔧 维护团队**: RL-Swarm运维组  
**�� 更新时间**: 2025-06-25 