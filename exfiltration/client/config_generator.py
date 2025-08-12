#!/usr/bin/env python3
"""
DoH Evasion Configuration Generator

Outil pour créer, modifier et tester des configurations d'évasion DoH
pour les tests de recherche en sécurité.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

def create_evasion_config():
    """Interface interactive pour créer une configuration d'évasion"""
    print("🔧 DoH Evasion Configuration Generator")
    print("=" * 50)
    
    config = {
        "name": "",
        "description": "",
        "exfiltration_config": {},
        "test_files": [],
        "detection_expected": False,
        "notes": ""
    }
    
    # Informations de base
    config["name"] = input("📝 Nom de la configuration: ").strip()
    config["description"] = input("📋 Description: ").strip()
    
    # Configuration d'exfiltration
    print("\n⚙️ Configuration d'exfiltration:")
    
    # Serveur et domaine
    config["exfiltration_config"]["doh_server"] = input("🌐 Serveur DoH [https://doh.local/dns-query]: ").strip() or "https://doh.local/dns-query"
    config["exfiltration_config"]["target_domain"] = input("🎯 Domaine cible [exfill.local]: ").strip() or "exfill.local"
    
    # Taille des chunks
    chunk_size = input("📦 Taille des chunks [30]: ").strip()
    config["exfiltration_config"]["chunk_size"] = int(chunk_size) if chunk_size else 30
    
    # Encodage
    print("🔢 Encodage disponible: base64, hex, base32, custom")
    encoding = input("   Sélection [base64]: ").strip() or "base64"
    config["exfiltration_config"]["encoding"] = encoding
    
    # Pattern de timing
    print("⏱️ Patterns de timing: regular, random, burst, stealth")
    timing = input("   Sélection [regular]: ").strip() or "regular"
    config["exfiltration_config"]["timing_pattern"] = timing
    
    # Délai de base
    delay = input("⏲️ Délai de base en secondes [0.2]: ").strip()
    config["exfiltration_config"]["base_delay"] = float(delay) if delay else 0.2
    
    # Options d'évasion
    print("\n🕵️ Options d'évasion:")
    config["exfiltration_config"]["compression"] = input("🗜️ Compression [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["encryption"] = input("🔐 Chiffrement [y/N]: ").lower().startswith('y')
    
    if config["exfiltration_config"]["encryption"]:
        encryption_key = input("🔑 Clé de chiffrement: ").strip()
        config["exfiltration_config"]["encryption_key"] = encryption_key or "default_key"
    
    config["exfiltration_config"]["subdomain_randomization"] = input("🎲 Randomisation sous-domaines [Y/n]: ").lower() != 'n'
    config["exfiltration_config"]["padding"] = input("📏 Padding [y/N]: ").lower().startswith('y')
    
    # Rotation de domaines
    domain_rotation = input("🔄 Rotation de domaines [y/N]: ").lower().startswith('y')
    config["exfiltration_config"]["domain_rotation"] = domain_rotation
    
    if domain_rotation:
        backup_domains = input("🔗 Domaines de backup (séparés par virgules): ").strip()
        if backup_domains:
            config["exfiltration_config"]["backup_domains"] = [d.strip() for d in backup_domains.split(',')]
        else:
            config["exfiltration_config"]["backup_domains"] = []
    
    # Paramètres avancés pour timing spéciaux
    if timing == "random":
        variance = input("📊 Variance de délai [0.1]: ").strip()
        config["exfiltration_config"]["delay_variance"] = float(variance) if variance else 0.1
    elif timing == "burst":
        burst_size = input("💥 Taille des rafales [5]: ").strip()
        config["exfiltration_config"]["burst_size"] = int(burst_size) if burst_size else 5
        burst_delay = input("⏳ Délai entre rafales [2.0]: ").strip()
        config["exfiltration_config"]["burst_delay"] = float(burst_delay) if burst_delay else 2.0
    elif timing == "stealth":
        variance = input("📊 Variance de délai pour furtivité [1.0]: ").strip()
        config["exfiltration_config"]["delay_variance"] = float(variance) if variance else 1.0
    
    # Métadonnées
    print("\n📋 Métadonnées:")
    test_files = input("📁 Fichiers de test (séparés par virgules): ").strip()
    if test_files:
        config["test_files"] = [f.strip() for f in test_files.split(',')]
    
    config["detection_expected"] = input("🚨 Détection attendue [y/N]: ").lower().startswith('y')
    config["notes"] = input("📝 Notes de recherche: ").strip()
    
    return config

def save_config(config: Dict[str, Any], filename: str = None) -> str:
    """Sauvegarde une configuration dans un fichier JSON"""
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
    """Charge une configuration depuis un fichier JSON"""
    config_path = Path(filename)
    if not config_path.exists():
        config_path = Path("test_configs") / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {filename}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def list_configs():
    """Liste toutes les configurations disponibles"""
    config_dir = Path("test_configs")
    if not config_dir.exists():
        print("📁 Aucune configuration trouvée")
        return
    
    configs = list(config_dir.glob("*.json"))
    if not configs:
        print("📁 Aucune configuration trouvée")
        return
    
    print(f"📋 Configurations disponibles ({len(configs)}):")
    print("=" * 50)
    
    for config_file in sorted(configs):
        try:
            config = load_config(config_file)
            detection = "🔴 High" if config.get("detection_expected", False) else "🟢 Low"
            
            exfil_config = config.get("exfiltration_config", {})
            chunk_size = exfil_config.get("chunk_size", "?")
            encoding = exfil_config.get("encoding", "?")
            timing = exfil_config.get("timing_pattern", "?")
            
            print(f"📄 {config_file.stem}")
            print(f"   📝 {config.get('description', 'No description')}")
            print(f"   ⚙️ Chunks: {chunk_size}, Encoding: {encoding}, Timing: {timing}")
            print(f"   🎯 Detection: {detection}")
            if config.get("notes"):
                print(f"   📋 Notes: {config['notes']}")
            print()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement de {config_file}: {e}")

def create_template_configs():
    """Crée des configurations de template pour différents scénarios"""
    templates = [
        {
            "name": "Quick Test",
            "description": "Configuration rapide pour tests de base",
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
            "detection_expected": True,
            "notes": "Configuration de base pour validation rapide"
        },
        {
            "name": "Stealth Research",
            "description": "Configuration furtive pour recherche d'évasion",
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
            "detection_expected": False,
            "notes": "Techniques d'évasion avancées pour contourner la détection ML"
        },
        {
            "name": "Speed Benchmark",
            "description": "Configuration optimisée pour vitesse maximale",
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
            "detection_expected": True,
            "notes": "Test de vitesse maximale - facilement détectable"
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
        print(f"✅ Configurations template créées: {', '.join(created)}")
    else:
        print("ℹ️ Toutes les configurations template existent déjà")

def test_config(config_file: str, test_file: str = None):
    """Teste une configuration avec un fichier"""
    try:
        config = load_config(config_file)
        print(f"🧪 Test de la configuration: {config['name']}")
        print(f"📝 Description: {config['description']}")
        
        if not test_file:
            # Créer un fichier de test temporaire
            test_file = "temp_test_file.txt"
            with open(test_file, 'w') as f:
                f.write("Test data for DoH exfiltration configuration validation.\n")
                f.write("This file will be used to test the JSON configuration.\n")
                f.write("Configuration: " + config['name'] + "\n")
                f.write("Timestamp: " + str(time.time()) + "\n")
            print(f"📁 Fichier de test créé: {test_file}")
        
        # Utiliser le script de test avec la configuration
        import subprocess
        cmd = [sys.executable, "run_client.py", "--config", config_file, test_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test réussi!")
        else:
            print("❌ Test échoué:")
            print(result.stderr)
        
        # Nettoyer le fichier temporaire
        if test_file == "temp_test_file.txt" and os.path.exists(test_file):
            os.remove(test_file)
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

def main():
    """Fonction principale avec interface en ligne de commande"""
    parser = argparse.ArgumentParser(description='DoH Evasion Configuration Generator')
    parser.add_argument('--create', action='store_true',
                       help='Créer une nouvelle configuration interactivement')
    parser.add_argument('--list', action='store_true',
                       help='Lister toutes les configurations disponibles')
    parser.add_argument('--templates', action='store_true',
                       help='Créer les configurations template')
    parser.add_argument('--test', metavar='CONFIG',
                       help='Tester une configuration')
    parser.add_argument('--file', metavar='FILE',
                       help='Fichier à utiliser pour le test')
    parser.add_argument('--edit', metavar='CONFIG',
                       help='Éditer une configuration existante')
    
    args = parser.parse_args()
    
    if args.create:
        print("🎯 Création d'une nouvelle configuration d'évasion DoH")
        config = create_evasion_config()
        filepath = save_config(config)
        print(f"\n✅ Configuration sauvegardée: {filepath}")
        
    elif args.list:
        list_configs()
        
    elif args.templates:
        create_template_configs()
        
    elif args.test:
        test_config(args.test, args.file)
        
    elif args.edit:
        try:
            config = load_config(args.edit)
            print(f"📝 Édition de: {config['name']}")
            print("💡 Appuyez sur Entrée pour garder la valeur actuelle")
            
            # Interface d'édition simplifiée
            new_name = input(f"Nom [{config['name']}]: ").strip()
            if new_name:
                config['name'] = new_name
            
            new_desc = input(f"Description [{config['description']}]: ").strip()
            if new_desc:
                config['description'] = new_desc
            
            # Sauvegarder
            filepath = save_config(config)
            print(f"✅ Configuration mise à jour: {filepath}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'édition: {e}")
        
    else:
        print("🔧 DoH Evasion Configuration Generator")
        print("=" * 40)
        print("📋 Options disponibles:")
        print("  --create      Créer une nouvelle configuration")
        print("  --list        Lister les configurations")
        print("  --templates   Créer les templates de base")
        print("  --test CONFIG Tester une configuration")
        print("  --edit CONFIG Éditer une configuration")
        print()
        print("💡 Exemples d'utilisation:")
        print("  python config_generator.py --create")
        print("  python config_generator.py --list")
        print("  python config_generator.py --test stealth_research.json")
        print("  python config_generator.py --templates")

if __name__ == "__main__":
    main()
