#!/usr/bin/env python3
"""
DoH Evasion Configuration Generator

Tool for creating, modifying and testing DoH evasion configurations
for security research testing.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

def create_evasion_config():
    """Interactive interface to create an evasion configuration"""
    print("DoH Evasion Configuration Generator")
    print("=" * 50)
    
    config = {
        "name": "",
        "description": "",
        "exfiltration_config": {},
        "test_files": [],
        "notes": ""
    }
    
    # Basic information
    config["name"] = input("Configuration name: ").strip()
    config["description"] = input("Description: ").strip()
    
    # Exfiltration configuration
    print("\nExfiltration configuration:")
    
    # Server and domain
    config["exfiltration_config"]["doh_server"] = input("DoH Server [https://doh.local/dns-query]: ").strip() or "https://doh.local/dns-query"
    config["exfiltration_config"]["target_domain"] = input("Target domain [exfill.local]: ").strip() or "exfill.local"
    
    # Chunk size
    chunk_size = input("Chunk size [30]: ").strip()
    config["exfiltration_config"]["chunk_size"] = int(chunk_size) if chunk_size else 30
    
    # Encoding
    print("Available encoding: base64, hex, base32, custom")
    encoding = input("   Selection [base64]: ").strip() or "base64"
    config["exfiltration_config"]["encoding"] = encoding
    
    # Timing pattern
    print("Timing patterns: regular, random, burst, stealth")
    timing = input("   Selection [regular]: ").strip() or "regular"
    config["exfiltration_config"]["timing_pattern"] = timing
    
    # Base delay
    delay = input("Base delay in seconds [0.2]: ").strip()
    config["exfiltration_config"]["base_delay"] = float(delay) if delay else 0.2
    
    # Evasion options
    print("\nEvasion options:")
    config["exfiltration_config"]["compression"] = input("Compression [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["encryption"] = input("Encryption [y/N]: ").lower().startswith('y')
    
    if config["exfiltration_config"]["encryption"]:
        encryption_key = input("Encryption key: ").strip()
        config["exfiltration_config"]["encryption_key"] = encryption_key or "default_key"
    
    config["exfiltration_config"]["subdomain_randomization"] = input("Subdomain randomization [Y/n]: ").lower() != 'n'
    config["exfiltration_config"]["padding"] = input("Padding [y/N]: ").lower().startswith('y')
    
    # Domain rotation
    domain_rotation = input("Domain rotation [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["domain_rotation"] = domain_rotation
    
    if domain_rotation:
        backup_domains = input("Backup domains (comma separated): ").strip()
        if backup_domains:
            config["exfiltration_config"]["backup_domains"] = [d.strip() for d in backup_domains.split(',')]
        else:
            config["exfiltration_config"]["backup_domains"] = []
    
    # Advanced parameters for special timing
    if timing == "random":
        variance = input("Delay variance [0.1]: ").strip()
        config["exfiltration_config"]["delay_variance"] = float(variance) if variance else 0.1
    elif timing == "burst":
        burst_size = input("Burst size [5]: ").strip()
        config["exfiltration_config"]["burst_size"] = int(burst_size) if burst_size else 5
        burst_delay = input("Delay between bursts [2.0]: ").strip()
        config["exfiltration_config"]["burst_delay"] = float(burst_delay) if burst_delay else 2.0
    elif timing == "stealth":
        variance = input("Delay variance for stealth [1.0]: ").strip()
        config["exfiltration_config"]["delay_variance"] = float(variance) if variance else 1.0
    
    # Metadata
    print("\nMetadata:")
    test_files = input("Test files (comma separated): ").strip()
    if test_files:
        config["test_files"] = [f.strip() for f in test_files.split(',')]
    
    config["notes"] = input("Research notes: ").strip()
    
    return config

def save_config(config: Dict[str, Any], filename: str = None) -> str:
    """Save configuration to a JSON file"""
    if not filename:
        safe_name = config["name"].lower().replace(" ", "_").replace("-", "_")
        filename = f"{safe_name}.json"
    
    config_dir = Path("test_configs")
    config_dir.mkdir(exist_ok=True)
    
    filepath = config_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return str(filepath)

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from a JSON file"""
    config_path = Path(filename)
    if not config_path.exists():
        config_path = Path("test_configs") / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {filename}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_configs():
    """List all available configurations"""
    config_dir = Path("test_configs")
    if not config_dir.exists():
        print("No configurations found")
        return
    
    configs = list(config_dir.glob("*.json"))
    if not configs:
        print("No configurations found")
        return
    
    print(f"Available configurations ({len(configs)}):")
    print("=" * 50)
    
    for config_file in sorted(configs):
        try:
            config = load_config(config_file)
            
            exfil_config = config.get("exfiltration_config", {})
            chunk_size = exfil_config.get("chunk_size", "?")
            encoding = exfil_config.get("encoding", "?")
            timing = exfil_config.get("timing_pattern", "?")
            
            print(f"{config_file.stem}")
            print(f"   {config.get('description', 'No description')}")
            print(f"   Chunks: {chunk_size}, Encoding: {encoding}, Timing: {timing}")
            print(f"   Detection: {detection}")
            if config.get("notes"):
                print(f"   Notes: {config['notes']}")
            print()
            
        except Exception as e:
            print(f"Error loading {config_file}: {e}")

def create_template_configs():
    """Create template configurations for different scenarios"""
    templates = [
        {
            "name": "Quick Test",
            "description": "Quick configuration for basic tests",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "exfill.local",
                "chunk_size": 30,
                "encoding": "base64",
                "timing_pattern": "regular",
                "base_delay": 0.3,
                "compression": False,
                "encryption": False,
                "subdomain_randomization": True
            },
            "test_files": ["sample.txt"],
            "notes": "Basic configuration for quick validation"
        },
        {
            "name": "Stealth Research",
            "description": "Stealth configuration for evasion research",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "cdn-service.local",
                "chunk_size": 15,
                "encoding": "custom",
                "timing_pattern": "stealth",
                "base_delay": 5.0,
                "delay_variance": 2.0,
                "compression": True,
                "encryption": True,
                "encryption_key": "research_stealth_key",
                "subdomain_randomization": True,
                "padding": True,
                "padding_size": 12,
                "domain_rotation": True,
                "backup_domains": ["api-cache.local", "media-cdn.local"]
            },
            "test_files": ["sensitive_data.json", "credentials.txt"],
            "notes": "Advanced evasion techniques to bypass ML detection"
        },
        {
            "name": "Speed Benchmark",
            "description": "Configuration optimized for maximum speed",
            "exfiltration_config": {
                "doh_server": "https://doh.local/dns-query",
                "target_domain": "fast-api.local",
                "chunk_size": 55,
                "encoding": "base64",
                "timing_pattern": "burst",
                "base_delay": 0.001,
                "burst_size": 20,
                "burst_delay": 0.1,
                "compression": True,
                "subdomain_randomization": False,
                "max_retries": 1,
                "retry_delay": 0.05,
                "timeout": 2.0
            },
            "test_files": ["large_file.bin"],
            "notes": "Maximum speed test - easily detectable"
        }
    ]
    
    config_dir = Path("test_configs")
    config_dir.mkdir(exist_ok=True)
    
    created = []
    for template in templates:
        filename = template["name"].lower().replace(" ", "_") + ".json"
        filepath = config_dir / filename
        
        if not filepath.exists():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)
            created.append(filename)
    
    if created:
        print(f"Template configurations created: {', '.join(created)}")
    else:
        print("All template configurations already exist")

def test_config(config_file: str, test_file: str = None):
    """Test a configuration with a file"""
    try:
        config = load_config(config_file)
        print(f"Testing configuration: {config['name']}")
        print(f"Description: {config['description']}")
        
        if not test_file:
            # Create temporary test file
            test_file = "temp_test_file.txt"
            with open(test_file, 'w') as f:
                f.write("Test data for DoH exfiltration configuration validation.\n")
                f.write("This file will be used to test the JSON configuration.\n")
                f.write("Configuration: " + config['name'] + "\n")
                f.write("Timestamp: " + str(time.time()) + "\n")
            print(f"Test file created: {test_file}")
        
        # Use test script with configuration
        import subprocess
        cmd = [sys.executable, "run_client.py", "--config", config_file, test_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Test successful!")
        else:
            print("Test failed:")
            print(result.stderr)
        
        # Clean up temporary file
        if test_file == "temp_test_file.txt" and os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"Test error: {e}")

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='DoH Evasion Configuration Generator')
    parser.add_argument('--create', action='store_true',
                       help='Create a new configuration interactively')
    parser.add_argument('--list', action='store_true',
                       help='List all available configurations')
    parser.add_argument('--templates', action='store_true',
                       help='Create template configurations')
    parser.add_argument('--test', metavar='CONFIG',
                       help='Test a configuration')
    parser.add_argument('--file', metavar='FILE',
                       help='File to use for testing')
    parser.add_argument('--edit', metavar='CONFIG',
                       help='Edit an existing configuration')
    
    args = parser.parse_args()
    
    if args.create:
        print("Creating new DoH evasion configuration")
        config = create_evasion_config()
        filepath = save_config(config)
        print(f"\nConfiguration saved: {filepath}")
        
    elif args.list:
        list_configs()
        
    elif args.templates:
        create_template_configs()
        
    elif args.test:
        test_config(args.test, args.file)
        
    elif args.edit:
        try:
            config = load_config(args.edit)
            print(f"Editing: {config['name']}")
            print("Press Enter to keep current value")
            
            # Simplified editing interface
            new_name = input(f"Name [{config['name']}]: ").strip()
            if new_name:
                config['name'] = new_name
            
            new_desc = input(f"Description [{config['description']}]: ").strip()
            if new_desc:
                config['description'] = new_desc
            
            # Save
            filepath = save_config(config)
            print(f"Configuration updated: {filepath}")
            
        except Exception as e:
            print(f"Editing error: {e}")
        
    else:
        print("DoH Evasion Configuration Generator")
        print("=" * 40)
        print("Available options:")
        print("  --create      Create a new configuration")
        print("  --list        List configurations")
        print("  --templates   Create base templates")
        print("  --test CONFIG Test a configuration")
        print("  --edit CONFIG Edit a configuration")
        print()
        print("Usage examples:")
        print("  python config_generator.py --create")
        print("  python config_generator.py --list")
        print("  python config_generator.py --test stealth_research.json")
        print("  python config_generator.py --templates")

if __name__ == "__main__":
    main()
