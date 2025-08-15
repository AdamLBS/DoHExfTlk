#!/usr/bin/env python3

import json
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import asdict
from client import ExfiltrationConfig, EncodingType, TimingPattern, DoHExfiltrationClient

logger = logging.getLogger(__name__)

class JSONConfigLoader:    
    def __init__(self, config_dir: str = "test_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        os.chown(self.config_dir, 1000, 1000)
        
    
    def load_config_from_file(self, config_path: str) -> Optional[ExfiltrationConfig]:
        try:
            config_file = Path(config_path)
            if not config_file.exists():
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
        try:
            scenario_file = self.config_dir / f"{scenario_name}.json"
            if not scenario_file.exists():
                logger.error(f"Scenario not found: {scenario_name}")
                return None
            
            with open(scenario_file, 'r', encoding='utf-8') as f:
                scenario_data = json.load(f)
            
            if 'exfiltration_config' in scenario_data:
                config = self._json_to_config(scenario_data['exfiltration_config'])
                scenario_data['exfiltration_config'] = config
            
            return scenario_data
            
        except Exception as e:
            logger.error(f"Error loading scenario {scenario_name}: {e}")
            return None
    
    def save_config_to_file(self, config: ExfiltrationConfig, filename: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
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
        config_files = []
        for file in self.config_dir.glob("*.json"):
            config_files.append(file.stem)
        return sorted(config_files)
    
    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        required_fields = ['doh_server', 'target_domain', 'chunk_size']
        
        for field in required_fields:
            if field not in config_data:
                logger.error(f"Missing required field: {field}")
                return False
        
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
        if not self.validate_config(config_data):
            raise ValueError("Invalid configuration data")
        
        encoding = EncodingType.BASE64
        if 'encoding' in config_data:
            encoding = EncodingType(config_data['encoding'])
        
        timing_pattern = TimingPattern.REGULAR
        if 'timing_pattern' in config_data:
            timing_pattern = TimingPattern(config_data['timing_pattern'])
        
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