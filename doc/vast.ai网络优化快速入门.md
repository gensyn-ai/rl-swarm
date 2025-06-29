# vast.ai网络优化快速入门指南

## 🚀 5分钟快速优化

### 第一步：网络质量测试

```bash
# 一键网络测试脚本
curl -fsSL https://speedtest.net/cli | sudo sh
ping -c 10 vast.ai
traceroute vast.ai
```

### 第二步：基础网络优化

```bash
#!/bin/bash
# 复制粘贴运行即可
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.wmem_max=134217728
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
sudo sysctl -w net.core.default_qdisc=fq
echo "✅ 基础网络优化完成"
```

### 第三步：验证优化效果

```bash
# 测试延迟改善
ping -c 20 vast.ai | tail -1
```

## 📊 快速网络评估表

| 延迟范围 | 网络质量 | 建议方案 | 预期收益 |
|----------|----------|----------|----------|
| <150ms | 优秀 ⭐⭐⭐⭐⭐ | 维持现状 | +0% |
| 150-200ms | 良好 ⭐⭐⭐⭐ | 基础优化 | +15% |
| 200-300ms | 一般 ⭐⭐⭐ | 升级网络 | +30% |
| >300ms | 需改善 ⭐⭐ | CN2专线 | +50% |

## 🔧 常用网络工具

### 网络监控命令
```bash
# 实时带宽监控
iftop -i eth0

# 网络连接状态
ss -tuln

# 路由表查看
ip route show
```

### 性能测试工具
```bash
# 安装测试工具
sudo apt install iperf3 mtr-tiny nethogs

# 带宽测试
iperf3 -c vast.ai -p 5201

# 路由质量分析
mtr vast.ai
```

## 💰 成本效益快速计算

```python
# 简单ROI计算器
def calculate_network_roi(current_latency, current_income, upgrade_cost):
    if current_latency > 300:
        improvement = 0.5  # 50%改善
    elif current_latency > 200:
        improvement = 0.3  # 30%改善
    else:
        improvement = 0.15  # 15%改善
    
    new_income = current_income * (1 + improvement)
    monthly_profit = new_income - current_income
    roi_months = upgrade_cost / monthly_profit
    
    print(f"月收益增加: ¥{monthly_profit:.0f}")
    print(f"投资回收期: {roi_months:.1f}个月")
    return roi_months

# 示例使用
calculate_network_roi(250, 15000, 6000)
# 输出: 月收益增加: ¥4500, 投资回收期: 1.3个月
```

## 📞 快速联系方式

- **CN2 GIA申请**: 中国电信企业客户经理
- **CTGNet咨询**: 400-118-0808
- **技术支持**: 加入vast.ai中文社群

## ⚡ 应急处理

### 网络中断快速恢复
```bash
# 网络服务重启
sudo systemctl restart networking
sudo systemctl restart docker

# DNS刷新
sudo systemctl flush-dns
```

### 性能突然下降
```bash
# 检查网络使用情况
nethogs
# 重启网络接口
sudo ifdown eth0 && sudo ifup eth0
```

---

*💡 提示：建议先从基础优化开始，观察效果后再考虑升级网络方案* 