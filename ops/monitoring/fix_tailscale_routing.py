#!/usr/bin/env python3
"""
Tailscale路由问题诊断和修复工具
"""

import subprocess
import sys

def check_tailscale_routes():
    """检查Tailscale相关路由"""
    print("🔍 检查当前路由配置...")
    
    try:
        result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        print("\n📋 Tailscale相关路由:")
        tailscale_routes = []
        for line in lines:
            if 'utun4' in line and ('default' in line or '.' in line):
                print(f"   {line}")
                tailscale_routes.append(line)
        
        if any('default' in route for route in tailscale_routes):
            print("\n⚠️  发现问题: Tailscale被设置为默认路由（出口节点）")
            print("   这会导致所有流量都通过Tailscale转发，严重影响网速！")
            return True
        else:
            print("\n✅ Tailscale路由配置正常")
            return False
            
    except Exception as e:
        print(f"❌ 检查路由失败: {e}")
        return False

def get_tailscale_app_path():
    """查找Tailscale应用路径"""
    possible_paths = [
        "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
        "/usr/local/bin/tailscale",
        "/opt/homebrew/bin/tailscale"
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, 'version'], capture_output=True, text=True)
            if result.returncode == 0:
                return path
        except:
            continue
    return None

def fix_tailscale_exit_node():
    """修复Tailscale出口节点配置"""
    print("\n🛠 尝试修复Tailscale配置...")
    
    # 查找tailscale命令
    tailscale_cmd = get_tailscale_app_path()
    if not tailscale_cmd:
        print("❌ 未找到Tailscale命令行工具")
        print("\n📝 手动修复步骤:")
        print("1. 打开Tailscale应用")
        print("2. 找到设置中的'Use Tailscale DNS'或'Exit Node'选项")
        print("3. 关闭'Use as exit node'功能")
        print("4. 重启Tailscale")
        return False
    
    try:
        # 尝试禁用出口节点
        print(f"   使用命令: {tailscale_cmd}")
        
        # 检查当前状态
        result = subprocess.run([tailscale_cmd, 'status'], capture_output=True, text=True)
        print("   当前Tailscale状态:")
        print(f"   {result.stdout}")
        
        # 尝试禁用出口节点
        print("   尝试禁用出口节点...")
        result = subprocess.run([tailscale_cmd, 'set', '--exit-node='], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 成功禁用出口节点!")
            return True
        else:
            print(f"❌ 禁用失败: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

def manual_route_fix():
    """手动删除problematic routes"""
    print("\n⚠️  如果上述方法无效，可以尝试手动删除路由:")
    print("请在终端中运行以下命令（需要sudo权限）:")
    print()
    print("sudo route delete default -interface utun4")
    print()
    print("⚠️  注意: 这可能会暂时断开Tailscale连接")

def test_after_fix():
    """修复后测试网络"""
    print("\n🧪 修复后网络测试...")
    
    try:
        # 简单ping测试
        result = subprocess.run(['ping', '-c', '3', '8.8.8.8'], 
                              capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            for line in lines:
                if 'avg' in line:
                    avg_ms = float(line.split('=')[1].split('/')[1])
                    if avg_ms < 100:
                        print(f"✅ 网络延迟已改善: {avg_ms:.1f}ms")
                    else:
                        print(f"⚠️  延迟仍然较高: {avg_ms:.1f}ms")
                    break
        else:
            print("❌ 网络连接测试失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    print("🚀 Tailscale路由问题诊断和修复工具")
    print("=" * 50)
    
    # 1. 检查问题
    has_problem = check_tailscale_routes()
    
    if not has_problem:
        print("\n✅ 没有发现Tailscale路由问题")
        return
    
    # 2. 尝试修复
    print("\n" + "=" * 50)
    fixed = fix_tailscale_exit_node()
    
    if not fixed:
        manual_route_fix()
        return
    
    # 3. 测试
    print("\n" + "=" * 50)
    test_after_fix()
    
    print("\n📝 建议:")
    print("1. 重新运行带宽测试: python3 simple_bandwidth_test.py")
    print("2. 如果问题仍然存在，考虑重启Tailscale应用")
    print("3. 检查Tailscale管理面板的出口节点设置")

if __name__ == "__main__":
    main() 