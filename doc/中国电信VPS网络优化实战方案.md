# 中国电信+VPS网络优化实战方案

## 🔍 问题诊断

你当前架构：`中国电信宽带 → tailscale → 美国VPS → vast.ai`

**核心问题**：
1. 美国VPS成为瓶颈，跑不满带宽
2. 延迟过高影响vast.ai使用体验

## 🚀 立即可执行的优化方案

### 方案1：VPS升级优化（最直接）

```bash
# 1. VPS性能测试脚本
#!/bin/bash
echo "=== VPS性能诊断 ==="

# 带宽测试
curl -s https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py | python3

# CPU性能测试  
echo "CPU核心数: $(nproc)"
dd if=/dev/zero of=/tmp/test bs=1M count=1024

# 内存测试
free -h

# 网络延迟测试到关键节点
ping -c 5 vast.ai
ping -c 5 8.8.8.8
traceroute vast.ai

echo "=== 建议 ==="
echo "如果上传带宽 < 50Mbps，需要升级VPS"
echo "如果延迟 > 200ms，需要更换VPS位置"
```

**VPS选择建议**：

| 服务商 | 位置 | 带宽 | 延迟 | 月费 | 推荐度 |
|--------|------|------|------|------|--------|
| Vultr | 洛杉矶 | 1Gbps | 150ms | $20 | ⭐⭐⭐⭐⭐ |
| DigitalOcean | 旧金山 | 1Gbps | 160ms | $24 | ⭐⭐⭐⭐ |
| Linode | 弗里蒙特 | 1Gbps | 140ms | $20 | ⭐⭐⭐⭐⭐ |
| AWS Lightsail | 俄勒冈 | 高速 | 180ms | $20 | ⭐⭐⭐ |
| BandwagonHost | 洛杉矶CN2 | 2.5Gbps | 130ms | $50 | ⭐⭐⭐⭐⭐ |

**立即执行**：
```bash
# 测试你当前VPS到vast.ai的实际性能
curl -o /dev/null -s -w "时间: %{time_total}s\n下载速度: %{speed_download} bytes/sec\n" \
  https://vast.ai/api/v0/instances/
```

### 方案2：tailscale配置优化

```bash
# tailscale优化配置
sudo tailscale set --accept-routes=true
sudo tailscale set --accept-dns=false  # 避免DNS污染
sudo tailscale set --operator=$USER

# 强制使用DERP中继优化
sudo tailscale set --advertise-exit-node=true

# 查看当前路由状态
tailscale status --peers=false --self=false
```

**tailscale高级优化**：

```json
// /etc/tailscale/tailscaled.state 优化配置
{
  "Config": {
    "PreferredDERP": 11,  // 强制使用旧金山DERP节点
    "DisableUPnP": true,
    "NetfilterMode": 2,
    "DebugFlags": ["derp-force-websockets"]
  }
}
```

### 方案3：多线路负载均衡（推荐）

```bash
#!/bin/bash
# 多VPS负载均衡脚本

# VPS配置
declare -A VPS_LIST=(
    ["vps1"]="美西Vultr"
    ["vps2"]="美西Linode" 
    ["vps3"]="美东DigitalOcean"
)

# 实时检测最优路径
function find_best_vps() {
    best_vps=""
    min_latency=9999
    
    for vps in "${!VPS_LIST[@]}"; do
        latency=$(ping -c 3 $vps.example.com | tail -1 | awk -F '/' '{print $4}')
        echo "${VPS_LIST[$vps]}: ${latency}ms"
        
        if (( $(echo "$latency < $min_latency" | bc -l) )); then
            min_latency=$latency
            best_vps=$vps
        fi
    done
    
    echo "最优VPS: ${VPS_LIST[$best_vps]} (${min_latency}ms)"
    return $best_vps
}

# 自动切换路由
function switch_route() {
    best_vps=$(find_best_vps)
    tailscale set --exit-node=$best_vps
    echo "已切换到: $best_vps"
}

# 每10分钟检测一次
while true; do
    switch_route
    sleep 600
done
```

### 方案4：专业级优化方案（终极）

```bash
# WireGuard + 多出口优化
apt update && apt install wireguard-tools

# 生成密钥对
wg genkey | tee privatekey | wg pubkey > publickey

# WireGuard配置文件 (/etc/wireguard/wg0.conf)
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat privatekey)
Address = 10.66.66.1/24
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
ListenPort = 51820

# 美西VPS1
[Peer]
PublicKey = VPS1_PUBLIC_KEY
Endpoint = vps1.example.com:51820
AllowedIPs = 10.66.66.2/32
PersistentKeepalive = 25

# 美西VPS2  
[Peer]
PublicKey = VPS2_PUBLIC_KEY
Endpoint = vps2.example.com:51820
AllowedIPs = 10.66.66.3/32
PersistentKeepalive = 25
EOF

# 启动WireGuard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
```

## 🔧 实时监控与自动优化

```python
#!/usr/bin/env python3
import subprocess
import time
import json
import requests

class NetworkOptimizer:
    def __init__(self):
        self.vps_endpoints = [
            "vps1.example.com",
            "vps2.example.com", 
            "vps3.example.com"
        ]
        self.current_vps = None
        self.min_latency_threshold = 150  # ms
        
    def test_latency(self, endpoint):
        """测试到指定端点的延迟"""
        try:
            result = subprocess.run(
                ['ping', '-c', '3', endpoint],
                capture_output=True, text=True, timeout=10
            )
            # 解析ping结果
            lines = result.stdout.split('\n')
            for line in lines:
                if 'avg' in line:
                    latency = float(line.split('/')[4])
                    return latency
        except:
            return 999
            
    def test_bandwidth(self, endpoint):
        """测试到指定端点的带宽"""
        try:
            start_time = time.time()
            response = requests.get(f"http://{endpoint}/100MB.bin", 
                                  stream=True, timeout=30)
            total_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                total_size += len(chunk)
                if time.time() - start_time > 10:  # 10秒测试
                    break
            
            duration = time.time() - start_time
            bandwidth = (total_size * 8) / (duration * 1024 * 1024)  # Mbps
            return bandwidth
        except:
            return 0
            
    def find_optimal_vps(self):
        """找到最优VPS"""
        best_vps = None
        best_score = 0
        
        for vps in self.vps_endpoints:
            latency = self.test_latency(vps)
            bandwidth = self.test_bandwidth(vps)
            
            # 综合评分 (带宽权重0.7，延迟权重0.3)
            score = (bandwidth * 0.7) + ((300 - latency) * 0.3)
            
            print(f"{vps}: 延迟={latency}ms, 带宽={bandwidth:.1f}Mbps, 评分={score:.1f}")
            
            if score > best_score:
                best_score = score
                best_vps = vps
                
        return best_vps, best_score
        
    def switch_to_vps(self, vps):
        """切换到指定VPS"""
        if vps != self.current_vps:
            print(f"切换路由到: {vps}")
            subprocess.run(['tailscale', 'set', f'--exit-node={vps}'])
            self.current_vps = vps
            
    def run_optimization_loop(self):
        """运行优化循环"""
        while True:
            print(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} 网络优化检测 ===")
            
            optimal_vps, score = self.find_optimal_vps()
            
            if optimal_vps:
                self.switch_to_vps(optimal_vps)
                print(f"当前最优路径: {optimal_vps} (评分: {score:.1f})")
            
            # 每5分钟检测一次
            time.sleep(300)

if __name__ == "__main__":
    optimizer = NetworkOptimizer()
    optimizer.run_optimization_loop()
```

## 💰 成本效益分析

| 方案 | 月成本 | 延迟改善 | 带宽提升 | 实施难度 | 推荐度 |
|------|--------|----------|----------|----------|--------|
| VPS升级 | +$20-50 | 30-50ms | 2-5倍 | ⭐ | ⭐⭐⭐⭐⭐ |
| tailscale优化 | $0 | 10-20ms | 20% | ⭐⭐ | ⭐⭐⭐⭐ |
| 多线路负载 | +$40-80 | 50-80ms | 3-8倍 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| WireGuard专线 | +$60-120 | 80-100ms | 5-10倍 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 立即行动计划

### 今天就能做的（免费）：
1. **运行VPS性能测试脚本**，确定瓶颈位置
2. **优化tailscale配置**，强制使用最优DERP节点
3. **测试不同时间段的网络质量**，找到最佳使用时间

### 本周内完成（低成本）：
1. **更换VPS供应商**，选择BandwagonHost或Vultr洛杉矶
2. **部署网络监控脚本**，实时追踪性能变化
3. **配置自动路由切换**，根据网络质量动态选择

### 本月内完成（投资版）：
1. **部署多VPS负载均衡**，确保冗余和性能
2. **搭建WireGuard专线**，获得最佳网络性能
3. **建立完整监控体系**，实现无人值守优化

## ⚡ 快速验证脚本

```bash
#!/bin/bash
echo "=== 网络优化效果验证 ==="

echo "1. 测试到vast.ai的延迟..."
ping -c 10 vast.ai | tail -1

echo "2. 测试实际带宽..."
curl -o /dev/null -s -w "下载速度: %{speed_download} bytes/sec\n" \
  https://speed.cloudflare.com/__down?bytes=100000000

echo "3. 测试连接稳定性..."
mtr --report --report-cycles=10 vast.ai

echo "4. 当前路由路径..."
traceroute vast.ai | head -15

echo "=== 优化建议 ==="
echo "如果延迟 > 200ms，需要更换VPS位置"
echo "如果带宽 < 50Mbps，需要升级VPS配置" 
echo "如果丢包 > 2%，需要检查路由配置"
```

**核心建议**：先升级VPS（最具性价比），再考虑多线路方案。大部分情况下，一个好的美西VPS就能解决你80%的问题。 