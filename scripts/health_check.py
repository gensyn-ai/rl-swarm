#!/usr/bin/env python3
"""
Health check script for RL Swarm components.
Checks the status of various services and components.
"""

import os
import sys
import time
import requests
import subprocess
from typing import Dict, List, Tuple


class HealthChecker:
    """Health checker for RL Swarm components."""
    
    def __init__(self):
        self.checks: List[Tuple[str, bool]] = []
    
    def check_docker_services(self) -> bool:
        """Check if Docker services are running."""
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                services = ["swarm-cpu", "swarm-gpu", "fastapi", "otel-collector"]
                running_services = []
                
                for service in services:
                    if service in output and "Up" in output:
                        running_services.append(service)
                
                if running_services:
                    print(f"✅ Docker services running: {', '.join(running_services)}")
                    return True
                else:
                    print("⚠️  No RL Swarm Docker services found running")
                    return False
            else:
                print("❌ Docker is not running or not accessible")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Docker command timed out")
            return False
        except FileNotFoundError:
            print("❌ Docker command not found")
            return False
        except Exception as e:
            print(f"❌ Error checking Docker services: {e}")
            return False
    
    def check_web_service(self, url: str = "http://localhost:8080/api/healthz") -> bool:
        """Check if web service is responding."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Web service is healthy")
                return True
            else:
                print(f"⚠️  Web service returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Web service is not accessible")
            return False
        except requests.exceptions.Timeout:
            print("❌ Web service request timed out")
            return False
        except Exception as e:
            print(f"❌ Error checking web service: {e}")
            return False
    
    def check_modal_login(self, url: str = "http://localhost:3000") -> bool:
        """Check if modal login service is responding."""
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("✅ Modal login service is accessible")
                return True
            else:
                print(f"⚠️  Modal login service returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Modal login service is not accessible")
            return False
        except requests.exceptions.Timeout:
            print("❌ Modal login service request timed out")
            return False
        except Exception as e:
            print(f"❌ Error checking modal login service: {e}")
            return False
    
    def check_log_files(self) -> bool:
        """Check if log files are being created and updated."""
        log_files = [
            "logs/swarm.log",
            "logs/yarn.log",
        ]
        
        healthy_logs = []
        for log_file in log_files:
            if os.path.exists(log_file):
                # Check if file was modified in the last 5 minutes
                mtime = os.path.getmtime(log_file)
                if time.time() - mtime < 300:  # 5 minutes
                    healthy_logs.append(log_file)
        
        if healthy_logs:
            print(f"✅ Active log files: {', '.join(healthy_logs)}")
            return True
        else:
            print("⚠️  No recently updated log files found")
            return False
    
    def check_gpu_availability(self) -> bool:
        """Check if GPU is available for CUDA operations."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpus = result.stdout.strip().split('\n')
                print(f"✅ GPU(s) available: {len(gpus)} device(s)")
                for i, gpu in enumerate(gpus):
                    print(f"   GPU {i}: {gpu}")
                return True
            else:
                print("⚠️  nvidia-smi command failed")
                return False
                
        except FileNotFoundError:
            print("ℹ️  nvidia-smi not found (CPU-only mode)")
            return True  # Not an error for CPU-only setups
        except subprocess.TimeoutExpired:
            print("❌ nvidia-smi command timed out")
            return False
        except Exception as e:
            print(f"❌ Error checking GPU: {e}")
            return False
    
    def check_disk_space(self, min_gb: float = 10.0) -> bool:
        """Check available disk space."""
        try:
            statvfs = os.statvfs('.')
            available_bytes = statvfs.f_frsize * statvfs.f_bavail
            available_gb = available_bytes / (1024**3)
            
            if available_gb >= min_gb:
                print(f"✅ Disk space: {available_gb:.1f} GB available")
                return True
            else:
                print(f"⚠️  Low disk space: {available_gb:.1f} GB available (minimum: {min_gb} GB)")
                return False
                
        except Exception as e:
            print(f"❌ Error checking disk space: {e}")
            return False
    
    def check_memory_usage(self) -> bool:
        """Check system memory usage."""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            mem_total = None
            mem_available = None
            
            for line in meminfo.split('\n'):
                if line.startswith('MemTotal:'):
                    mem_total = int(line.split()[1]) * 1024  # Convert to bytes
                elif line.startswith('MemAvailable:'):
                    mem_available = int(line.split()[1]) * 1024  # Convert to bytes
            
            if mem_total and mem_available:
                mem_used = mem_total - mem_available
                usage_percent = (mem_used / mem_total) * 100
                
                print(f"✅ Memory usage: {usage_percent:.1f}% ({mem_used/(1024**3):.1f}/{mem_total/(1024**3):.1f} GB)")
                
                if usage_percent > 90:
                    print("⚠️  High memory usage detected")
                    return False
                return True
            else:
                print("⚠️  Could not determine memory usage")
                return False
                
        except FileNotFoundError:
            print("ℹ️  Memory info not available (non-Linux system)")
            return True
        except Exception as e:
            print(f"❌ Error checking memory usage: {e}")
            return False
    
    def run_health_check(self) -> bool:
        """Run all health checks."""
        print("🏥 Running RL Swarm Health Check...\n")
        
        checks = [
            ("Docker Services", self.check_docker_services),
            ("Web Service", self.check_web_service),
            ("Modal Login", self.check_modal_login),
            ("Log Files", self.check_log_files),
            ("GPU Availability", self.check_gpu_availability),
            ("Disk Space", self.check_disk_space),
            ("Memory Usage", self.check_memory_usage),
        ]
        
        passed = 0
        total = len(checks)
        
        for check_name, check_func in checks:
            print(f"\n🔍 Checking {check_name}...")
            try:
                result = check_func()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ Error in {check_name}: {e}")
        
        print(f"\n📊 Health Check Summary: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All systems healthy!")
            return True
        elif passed >= total * 0.7:  # 70% threshold
            print("⚠️  Some issues detected, but system should be functional")
            return True
        else:
            print("❌ Multiple issues detected, system may not function properly")
            return False


def main():
    """Main entry point."""
    checker = HealthChecker()
    success = checker.run_health_check()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()