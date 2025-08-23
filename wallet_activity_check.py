# -*- coding: utf-8 -*-
import json
import sys
import time
import requests
import urllib3
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import argparse
import logging
from pathlib import Path

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WalletActivityChecker:
    """
    钱包活跃度检查器
    结合wallet_monitor.py的查询方法和gensyncheck.py的重启信号功能
    """
    
    def __init__(self):
        self.base_url = "https://gensyn-testnet.explorer.alchemy.com/api/v2/addresses"
        self.request_timeout = 30
        self.max_retries = 3
        self.alert_threshold_hours = 4  # 4小时阈值
    
    def query_wallet_with_retry(self, wallet_address: str) -> Optional[Dict]:
        """
        带重试机制的钱包查询（使用指数退避策略）
        """
        url = f"{self.base_url}/{wallet_address}/internal-transactions"
        
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    # 指数退避：2秒, 4秒, 8秒
                    wait_time = 2 * (2 ** attempt)
                    print(f"第{attempt+1}次查询失败，{wait_time}秒后重试...")
                    time.sleep(wait_time)
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(
                    url,
                    timeout=self.request_timeout,
                    verify=False,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"成功查询钱包 {wallet_address}")
                return data
                
            except requests.exceptions.Timeout:
                print(f"第{attempt+1}次查询超时")
            except requests.exceptions.ConnectionError as e:
                print(f"第{attempt+1}次连接失败: {e}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"第{attempt+1}次查询遇到限流(429)，需要更长等待时间")
                    if attempt < self.max_retries - 1:
                        wait_time = 10 * (2 ** attempt)  # 更长的等待时间
                        print(f"限流重试，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                else:
                    print(f"第{attempt+1}次HTTP错误: {e}")
            except Exception as e:
                print(f"第{attempt+1}次查询失败: {e}")
        
        print(f"钱包查询失败，已重试{self.max_retries}次")
        return None
    
    def check_wallet_activity(self, wallet_address: str) -> Dict:
        """
        检查钱包活跃度
        """
        result = {
            'wallet_address': wallet_address,
            'status': 'unknown',
            'last_transaction_time': None,
            'hours_since_last_tx': 0,
            'needs_restart': False,
            'error': None
        }
        
        try:
            print(f"正在查询钱包: {wallet_address}")
            data = self.query_wallet_with_retry(wallet_address)
            
            if not data:
                result['status'] = 'query_failed'
                result['error'] = 'API查询失败'
                return result
            
            items = data.get('items', [])
            if not items:
                result['status'] = 'no_transactions'
                result['error'] = '没有找到交易记录'
                return result
            
            # 获取最新交易
            latest_transaction = items[0]
            timestamp_str = latest_transaction.get('timestamp')
            
            if not timestamp_str:
                result['status'] = 'no_timestamp'
                result['error'] = '交易记录没有时间戳'
                return result
            
            # 解析时间（处理不同的时间格式）
            try:
                if timestamp_str.endswith('Z'):
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
            except ValueError as e:
                result['status'] = 'invalid_timestamp'
                result['error'] = f'时间格式解析失败: {e}'
                return result
            
            # 计算时间差
            now = datetime.now(timezone.utc)
            time_diff = now - timestamp
            hours_since_last_tx = time_diff.total_seconds() / 3600
            
            # 格式化时间显示
            formatted_time = self._format_time_diff(time_diff)
            
            result.update({
                'status': 'success',
                'last_transaction_time': timestamp_str,
                'formatted_time_diff': formatted_time,
                'hours_since_last_tx': hours_since_last_tx,
                'needs_restart': hours_since_last_tx > self.alert_threshold_hours,
                'transaction_hash': latest_transaction.get('transaction_hash', '')
            })
            
            return result
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            return result
    
    def _format_time_diff(self, time_diff: timedelta) -> str:
        """
        格式化时间差显示
        """
        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}天{hours}小时{minutes}分钟前"
        elif hours > 0:
            return f"{hours}小时{minutes}分钟前"
        elif minutes > 0:
            return f"{minutes}分钟前"
        else:
            return f"{seconds}秒前"
    
    def run_check(self, wallet_address: str):
        """
        执行单次检查
        """
        print("=" * 50)
        print(f"钱包活跃度检查")
        print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"钱包地址: {wallet_address}")
        print(f"活跃度阈值: {self.alert_threshold_hours} 小时")
        print("=" * 50)
        
        result = self.check_wallet_activity(wallet_address)
        
        if result['status'] == 'success':
            print(f"✅ 查询成功")
            print(f"最后交易时间: {result['last_transaction_time']}")
            print(f"距离现在: {result['formatted_time_diff']}")
            print(f"距离现在已过去: {result['hours_since_last_tx']:.2f} 小时")
            print(f"最新交易哈希: {result['transaction_hash'][:20]}...")
            
            if result['needs_restart']:
                print("🚨 警告: 钱包超过4小时未活跃!")
                print("__NEED_RESTART__")
                return True  # 需要重启
            else:
                print("✅ 钱包活跃正常")
                return False  # 不需要重启
        else:
            print(f"❌ 查询失败: {result['error']}")
            print("⚠️ 查询失败，跳过本次重启，主流程继续运行。")
            return False

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='钱包活跃度检查工具')
    parser.add_argument('wallet_address', help='要检查的钱包地址')
    parser.add_argument('--threshold', type=float, default=4.0, 
                       help='活跃度阈值（小时，默认4小时）')
    
    args = parser.parse_args()
    
    # 验证钱包地址格式
    wallet_address = args.wallet_address.strip()
    if not wallet_address:
        print("错误: 钱包地址不能为空！")
        sys.exit(1)
    
    if not wallet_address.startswith('0x') or len(wallet_address) != 42:
        print("错误: 钱包地址格式不正确！应该是42位的十六进制地址，以0x开头")
        sys.exit(1)
    
    # 创建检查器并设置阈值
    checker = WalletActivityChecker()
    checker.alert_threshold_hours = args.threshold
    
    # 执行检查
    try:
        needs_restart = checker.run_check(wallet_address)
        if needs_restart:
            sys.exit(0)  # 需要重启，正常退出
        else:
            sys.exit(1)  # 不需要重启，非零退出码
    except KeyboardInterrupt:
        print("\n检查被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"检查过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()