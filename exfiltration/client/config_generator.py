#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

def create_evasion_config():
    print("DoH Evasion Configuration Generator")
    print("=" * 50)
    
    config = {
        "name": "",
        "description": "",
        "exfiltration_config": {},
        "test_files": []
    }
    
    config["name"] = input("Configuration name: ").strip()
    config["description"] = input("Description: ").strip()
    
    print("\nExfiltration configuration:")
    
    config["exfiltration_config"]["doh_server"] = input("DoH Server [https://doh.local/dns-query]: ").strip() or "https://doh.local/dns-query"
    config["exfiltration_config"]["target_domain"] = input("Target domain [exfill.local]: ").strip() or "exfill.local"
    
    chunk_size = input("Chunk size [30]: ").strip()
    config["exfiltration_config"]["chunk_size"] = int(chunk_size) if chunk_size else 30
    
    print("Available encoding: base64, hex, base32, custom")
    encoding = input("   Selection [base64]: ").strip() or "base64"
    config["exfiltration_config"]["encoding"] = encoding
    
    print("Timing patterns: regular, random, burst, stealth")
    timing = input("   Selection [regular]: ").strip() or "regular"
    config["exfiltration_config"]["timing_pattern"] = timing
    
    delay = input("Base delay in seconds [0.2]: ").strip()
    config["exfiltration_config"]["base_delay"] = float(delay) if delay else 0.2
    
    print("\nEvasion options:")
    config["exfiltration_config"]["compression"] = input("Compression [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["encryption"] = input("Encryption [y/N]: ").lower().startswith('y')
    
    if config["exfiltration_config"]["encryption"]:
        encryption_key = input("Encryption key: ").strip()
        config["exfiltration_config"]["encryption_key"] = encryption_key or "default_key"
    
    config["exfiltration_config"]["subdomain_randomization"] = input("Subdomain randomization [Y/n]: ").lower() != 'n'
    config["exfiltration_config"]["padding"] = input("Padding [y/N]: ").lower().startswith('y')
    
    domain_rotation = input("Domain rotation [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["domain_rotation"] = domain_rotation
    
    if domain_rotation:
        backup_domains = input("Backup domains (comma separated): ").strip()
        if backup_domains:
            config["exfiltration_config"]["backup_domains"] = [d.strip() for d in backup_domains.split(',')]
        else:
            config["exfiltration_config"]["backup_domains"] = []
    
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
    return config

def save_config(config: Dict[str, Any], filename: str = None) -> str:
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
    config_path = Path(filename)
    if not config_path.exists():
        config_path = Path("test_configs") / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {filename}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_configs():
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
            print()
            
        except Exception as e:
            print(f"Error loading {config_file}: {e}")

def main():
    parser = argparse.ArgumentParser(description='DoH Evasion Configuration Generator')
    parser.add_argument('--create', action='store_true',
                       help='Create a new configuration interactively')
    parser.add_argument('--list', action='store_true',
                       help='List all available configurations')
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
        
        
    elif args.edit:
        try:
            config = load_config(args.edit)
            print(f"Editing: {config['name']}")
            print("Press Enter to keep current value")
            
            new_name = input(f"Name [{config['name']}]: ").strip()
            if new_name:
                config['name'] = new_name
            
            new_desc = input(f"Description [{config['description']}]: ").strip()
            if new_desc:
                config['description'] = new_desc
            
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
        print("  --edit CONFIG Edit a configuration")
        print()
        print("Usage examples:")
        print("  python config_generator.py --create")
        print("  python config_generator.py --list")
        print("  python config_generator.py --templates")

if __name__ == "__main__":
    main()
