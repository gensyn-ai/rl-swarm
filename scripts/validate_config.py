#!/usr/bin/env python3
"""
Configuration validation script for RL Swarm.
Validates environment variables and configuration files before startup.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional


class ConfigValidator:
    """Validates RL Swarm configuration."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_env_vars(self) -> bool:
        """Validate required environment variables."""
        required_vars = [
            'SWARM_CONTRACT',
            'PRG_CONTRACT',
        ]
        
        optional_vars = [
            'HF_TOKEN',
            'MODEL_NAME',
            'ORG_ID',
            'IDENTITY_PATH',
        ]
        
        # Check required variables
        for var in required_vars:
            if not os.getenv(var):
                self.errors.append(f"Required environment variable {var} is not set")
        
        # Check optional variables and warn if missing
        for var in optional_vars:
            if not os.getenv(var):
                self.warnings.append(f"Optional environment variable {var} is not set")
        
        # Validate URLs
        urls_to_check = [
            ('ALCHEMY_URL', os.getenv('ALCHEMY_URL')),
            ('MODAL_PROXY_URL', os.getenv('MODAL_PROXY_URL')),
            ('JUDGE_BASE_URL', os.getenv('JUDGE_BASE_URL')),
        ]
        
        for var_name, url in urls_to_check:
            if url and not (url.startswith('http://') or url.startswith('https://')):
                self.errors.append(f"{var_name} must be a valid HTTP/HTTPS URL")
        
        return len(self.errors) == 0
    
    def validate_config_file(self, config_path: str) -> bool:
        """Validate YAML configuration file."""
        if not os.path.exists(config_path):
            self.errors.append(f"Configuration file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check required sections
            required_sections = [
                'training',
                'blockchain',
                'game_manager',
            ]
            
            for section in required_sections:
                if section not in config:
                    self.errors.append(f"Required section '{section}' missing from config")
            
            # Validate training parameters
            if 'training' in config:
                training = config['training']
                if 'max_round' not in training or training['max_round'] <= 0:
                    self.errors.append("training.max_round must be a positive integer")
                
                if 'max_stage' not in training or training['max_stage'] <= 0:
                    self.errors.append("training.max_stage must be a positive integer")
            
            return len(self.errors) == 0
            
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML in config file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading config file: {e}")
            return False
    
    def validate_docker_setup(self) -> bool:
        """Validate Docker setup."""
        # Check if Docker is available
        if os.system("docker --version > /dev/null 2>&1") != 0:
            self.warnings.append("Docker is not available or not in PATH")
            return False
        
        # Check if docker-compose is available
        if os.system("docker-compose --version > /dev/null 2>&1") != 0:
            if os.system("docker compose version > /dev/null 2>&1") != 0:
                self.warnings.append("docker-compose is not available")
        
        return True
    
    def validate_directories(self) -> bool:
        """Validate required directories exist or can be created."""
        required_dirs = [
            'logs',
            'user/modal-login',
            'user/keys',
            'user/configs',
            'user/logs',
        ]
        
        for dir_path in required_dirs:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self.errors.append(f"Cannot create directory {dir_path}: {e}")
        
        return len(self.errors) == 0
    
    def validate_node_setup(self) -> bool:
        """Validate Node.js setup for modal-login."""
        if os.system("node --version > /dev/null 2>&1") != 0:
            self.warnings.append("Node.js is not available - required for modal-login")
            return False
        
        if os.system("yarn --version > /dev/null 2>&1") != 0:
            self.warnings.append("Yarn is not available - will be installed automatically")
        
        return True
    
    def run_validation(self) -> bool:
        """Run all validations."""
        print("🔍 Validating RL Swarm configuration...")
        
        # Run all validation checks
        env_valid = self.validate_env_vars()
        config_valid = self.validate_config_file('rgym_exp/config/rg-swarm.yaml')
        docker_valid = self.validate_docker_setup()
        dirs_valid = self.validate_directories()
        node_valid = self.validate_node_setup()
        
        # Print results
        if self.errors:
            print("\n❌ Configuration Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print("\n⚠️  Configuration Warnings:")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        success = len(self.errors) == 0
        
        if success:
            print("\n✅ Configuration validation passed!")
        else:
            print(f"\n❌ Configuration validation failed with {len(self.errors)} errors")
        
        return success


def main():
    """Main entry point."""
    validator = ConfigValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()