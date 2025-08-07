#!/usr/bin/env python3
"""
DoH Exfiltration Configuration Manager

Gestionnaire de configurations pour faciliter la creation et la gestion
de differents scenarios d'exfiltration pour la recherche academique.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict, dataclass
from client import ExfiltrationConfig, EncodingType, TimingPattern

@dataclass
class ScenarioConfig:
    """Configuration d'un scenario de test"""
    name: str
    description: str
    exfiltration_config: ExfiltrationConfig
    test_data: str
    expected_detection: bool = False
    notes: str = ""

class DoHConfigManager:
    """Gestionnaire de configurations d'exfiltration"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
        self.scenarios: Dict[str, ScenarioConfig] = {}
        
        # Creer le repertoire de configuration
        os.makedirs(config_dir, exist_ok=True)
        
        # Charger les configurations predefinies
        self._load_predefined_scenarios()
    
    def _load_predefined_scenarios(self):
        """Charge les scenarios predefinies pour la recherche"""
        
        # Scenario 1: Exfiltration classique (facilement detectable)
        self.scenarios["classic_base64"] = ScenarioConfig(
            name="Classic Base64 Exfiltration",
            description="Exfiltration traditionnelle avec base64, pattern regulier, chunks moyens",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=30,
                encoding=EncodingType.BASE64,
                timing_pattern=TimingPattern.REGULAR,
                base_delay=0.2,
                compression=False,
                encryption=False,
                subdomain_randomization=False
            ),
            test_data="credentials.txt",
            expected_detection=True,
            notes="Pattern facilement detectable par les systemes de monitoring classiques"
        )
        
        # Scenario 2: Exfiltration furtive avancee
        self.scenarios["advanced_stealth"] = ScenarioConfig(
            name="Advanced Stealth Exfiltration",
            description="Exfiltration furtive avec encodage personnalise, compression, chiffrement",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=18,
                encoding=EncodingType.CUSTOM,
                timing_pattern=TimingPattern.STEALTH,
                base_delay=3.0,
                delay_variance=1.5,
                compression=True,
                encryption=True,
                encryption_key="research_key_2024",
                subdomain_randomization=True,
                padding=True,
                padding_size=8
            ),
            test_data="sensitive_database.json",
            expected_detection=False,
            notes="Techniques d'evasion avancees pour contourner la detection ML"
        )
        
        # Scenario 3: Exfiltration en rafales
        self.scenarios["burst_attack"] = ScenarioConfig(
            name="Burst Attack Pattern",
            description="Exfiltration rapide en rafales pour simuler un attaquant presse",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=45,
                encoding=EncodingType.HEX,
                timing_pattern=TimingPattern.BURST,
                base_delay=0.05,
                burst_size=8,
                burst_delay=2.5,
                compression=True,
                subdomain_randomization=True
            ),
            test_data="corporate_secrets.zip",
            expected_detection=True,
            notes="Pattern de rafales detectable par analyse temporelle"
        )
        
        # Scenario 4: Exfiltration lente et discrete
        self.scenarios["slow_drip"] = ScenarioConfig(
            name="Slow Drip Exfiltration",
            description="Exfiltration tres lente pour eviter la detection par volume",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=12,
                encoding=EncodingType.BASE32,
                timing_pattern=TimingPattern.RANDOM,
                base_delay=10.0,
                delay_variance=5.0,
                compression=True,
                encryption=True,
                encryption_key="long_term_persistence",
                subdomain_randomization=True,
                domain_rotation=True,
                backup_domains=["backup1.local", "backup2.local"]
            ),
            test_data="financial_data.csv",
            expected_detection=False,
            notes="Exfiltration sur plusieurs heures/jours pour APT simulation"
        )
        
        # Scenario 5: Exfiltration avec rotation de domaines
        self.scenarios["domain_rotation"] = ScenarioConfig(
            name="Domain Rotation Evasion",
            description="Exfiltration avec rotation de domaines pour eviter le blocage",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=25,
                encoding=EncodingType.BASE64,
                timing_pattern=TimingPattern.RANDOM,
                base_delay=1.0,
                delay_variance=0.5,
                domain_rotation=True,
                backup_domains=[
                    "cdn-cache.local",
                    "api-service.local", 
                    "media-content.local",
                    "static-assets.local"
                ],
                subdomain_randomization=True
            ),
            test_data="intellectual_property.pdf",
            expected_detection=False,
            notes="Technique d'evasion par rotation de domaines legitimes"
        )
        
        # Scenario 6: Exfiltration avec payload minimal
        self.scenarios["minimal_footprint"] = ScenarioConfig(
            name="Minimal Footprint",
            description="Exfiltration avec empreinte minimale pour tests de sensibilite",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=8,
                encoding=EncodingType.CUSTOM,
                timing_pattern=TimingPattern.STEALTH,
                base_delay=15.0,
                compression=True,
                encryption=True,
                encryption_key="minimal_key",
                subdomain_randomization=True,
                padding=True,
                padding_size=12
            ),
            test_data="api_keys.txt",
            expected_detection=False,
            notes="Test des limites de detection avec chunks tres petits"
        )
        
        # Scenario 7: Exfiltration aggressive
        self.scenarios["aggressive_extraction"] = ScenarioConfig(
            name="Aggressive Data Extraction",
            description="Exfiltration rapide et agressive simulant un incident de securite",
            exfiltration_config=ExfiltrationConfig(
                chunk_size=60,
                encoding=EncodingType.BASE64,
                timing_pattern=TimingPattern.BURST,
                base_delay=0.01,
                burst_size=15,
                burst_delay=0.5,
                compression=False,
                subdomain_randomization=False,
                max_retries=5,
                retry_delay=0.1
            ),
            test_data="complete_database_dump.sql",
            expected_detection=True,
            notes="Simulation d'attaque rapide avec forte probabilite de detection"
        )
    
    def get_scenario(self, name: str) -> Optional[ScenarioConfig]:
        """Recupere un scenario par nom"""
        return self.scenarios.get(name)
    
    def list_scenarios(self) -> List[str]:
        """Liste tous les scenarios disponibles"""
        return list(self.scenarios.keys())
    
    def get_scenario_details(self, name: str) -> Optional[Dict[str, Any]]:
        """Recupere les details d'un scenario"""
        scenario = self.scenarios.get(name)
        if not scenario:
            return None
        
        return {
            'name': scenario.name,
            'description': scenario.description,
            'test_data': scenario.test_data,
            'expected_detection': scenario.expected_detection,
            'notes': scenario.notes,
            'config': {
                'chunk_size': scenario.exfiltration_config.chunk_size,
                'encoding': scenario.exfiltration_config.encoding.value,
                'timing_pattern': scenario.exfiltration_config.timing_pattern.value,
                'base_delay': scenario.exfiltration_config.base_delay,
                'compression': scenario.exfiltration_config.compression,
                'encryption': scenario.exfiltration_config.encryption,
                'subdomain_randomization': scenario.exfiltration_config.subdomain_randomization,
                'domain_rotation': scenario.exfiltration_config.domain_rotation
            }
        }
    
    def create_custom_scenario(self, name: str, description: str, config: ExfiltrationConfig, 
                             test_data: str, expected_detection: bool = False, notes: str = "") -> bool:
        """Cree un scenario personnalise"""
        if name in self.scenarios:
            return False
        
        self.scenarios[name] = ScenarioConfig(
            name=name,
            description=description,
            exfiltration_config=config,
            test_data=test_data,
            expected_detection=expected_detection,
            notes=notes
        )
        
        return True
    
    def save_scenario(self, name: str, filename: Optional[str] = None) -> bool:
        """Sauvegarde un scenario dans un fichier JSON"""
        scenario = self.scenarios.get(name)
        if not scenario:
            return False
        
        if not filename:
            filename = f"{name}.json"
        
        filepath = os.path.join(self.config_dir, filename)
        
        # Convertir la configuration en dictionnaire serializable
        scenario_dict = {
            'name': scenario.name,
            'description': scenario.description,
            'test_data': scenario.test_data,
            'expected_detection': scenario.expected_detection,
            'notes': scenario.notes,
            'exfiltration_config': {
                'doh_server': scenario.exfiltration_config.doh_server,
                'target_domain': scenario.exfiltration_config.target_domain,
                'chunk_size': scenario.exfiltration_config.chunk_size,
                'encoding': scenario.exfiltration_config.encoding.value,
                'compression': scenario.exfiltration_config.compression,
                'encryption': scenario.exfiltration_config.encryption,
                'encryption_key': scenario.exfiltration_config.encryption_key,
                'timing_pattern': scenario.exfiltration_config.timing_pattern.value,
                'base_delay': scenario.exfiltration_config.base_delay,
                'delay_variance': scenario.exfiltration_config.delay_variance,
                'burst_size': scenario.exfiltration_config.burst_size,
                'burst_delay': scenario.exfiltration_config.burst_delay,
                'domain_rotation': scenario.exfiltration_config.domain_rotation,
                'backup_domains': scenario.exfiltration_config.backup_domains,
                'subdomain_randomization': scenario.exfiltration_config.subdomain_randomization,
                'padding': scenario.exfiltration_config.padding,
                'padding_size': scenario.exfiltration_config.padding_size,
                'max_retries': scenario.exfiltration_config.max_retries,
                'retry_delay': scenario.exfiltration_config.retry_delay,
                'timeout': scenario.exfiltration_config.timeout
            }
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(scenario_dict, f, indent=2)
            return True
        except Exception:
            return False
    
    def load_scenario(self, filename: str) -> bool:
        """Charge un scenario depuis un fichier JSON"""
        filepath = os.path.join(self.config_dir, filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r') as f:
                scenario_dict = json.load(f)
            
            # Reconstruire la configuration
            config_dict = scenario_dict['exfiltration_config']
            config = ExfiltrationConfig(
                doh_server=config_dict.get('doh_server', 'https://doh.local/dns-query'),
                target_domain=config_dict.get('target_domain', 'exfill.local'),
                chunk_size=config_dict.get('chunk_size', 30),
                encoding=EncodingType(config_dict.get('encoding', 'base64')),
                compression=config_dict.get('compression', False),
                encryption=config_dict.get('encryption', False),
                encryption_key=config_dict.get('encryption_key'),
                timing_pattern=TimingPattern(config_dict.get('timing_pattern', 'regular')),
                base_delay=config_dict.get('base_delay', 0.2),
                delay_variance=config_dict.get('delay_variance', 0.1),
                burst_size=config_dict.get('burst_size', 5),
                burst_delay=config_dict.get('burst_delay', 2.0),
                domain_rotation=config_dict.get('domain_rotation', False),
                backup_domains=config_dict.get('backup_domains', []),
                subdomain_randomization=config_dict.get('subdomain_randomization', True),
                padding=config_dict.get('padding', False),
                padding_size=config_dict.get('padding_size', 10),
                max_retries=config_dict.get('max_retries', 3),
                retry_delay=config_dict.get('retry_delay', 1.0),
                timeout=config_dict.get('timeout', 5.0)
            )
            
            # Creer le scenario
            scenario = ScenarioConfig(
                name=scenario_dict['name'],
                description=scenario_dict['description'],
                exfiltration_config=config,
                test_data=scenario_dict['test_data'],
                expected_detection=scenario_dict.get('expected_detection', False),
                notes=scenario_dict.get('notes', '')
            )
            
            self.scenarios[scenario.name] = scenario
            return True
            
        except Exception:
            return False
    
    def export_all_scenarios(self, filename: str = "all_scenarios.json") -> bool:
        """Exporte tous les scenarios dans un fichier"""
        filepath = os.path.join(self.config_dir, filename)
        
        all_scenarios = {}
        for name, scenario in self.scenarios.items():
            all_scenarios[name] = self.get_scenario_details(name)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(all_scenarios, f, indent=2)
            return True
        except Exception:
            return False
    
    def print_scenario_comparison(self):
        """Affiche une comparaison des scenarios"""
        print("\n📊 SCENARIO COMPARISON TABLE")
        print("=" * 100)
        print(f"{'Name':<20} {'Chunk':<6} {'Encoding':<8} {'Timing':<8} {'Encrypt':<7} {'Compress':<8} {'Detection':<9}")
        print("-" * 100)
        
        for name, scenario in self.scenarios.items():
            config = scenario.exfiltration_config
            print(f"{name[:19]:<20} "
                  f"{config.chunk_size:<6} "
                  f"{config.encoding.value[:7]:<8} "
                  f"{config.timing_pattern.value[:7]:<8} "
                  f"{'Yes' if config.encryption else 'No':<7} "
                  f"{'Yes' if config.compression else 'No':<8} "
                  f"{'High' if scenario.expected_detection else 'Low':<9}")
    
    def generate_research_report(self) -> str:
        """Genere un rapport de recherche sur les scenarios"""
        report = []
        report.append("# DoH Exfiltration Research Scenarios")
        report.append("## Generated by DoH Configuration Manager\n")
        
        report.append("### Scenario Overview")
        report.append(f"Total scenarios: {len(self.scenarios)}")
        detectable = sum(1 for s in self.scenarios.values() if s.expected_detection)
        report.append(f"Easily detectable: {detectable}")
        report.append(f"Evasive techniques: {len(self.scenarios) - detectable}\n")
        
        for name, scenario in self.scenarios.items():
            report.append(f"### {scenario.name}")
            report.append(f"**Description:** {scenario.description}")
            report.append(f"**Test Data:** {scenario.test_data}")
            report.append(f"**Expected Detection:** {'High' if scenario.expected_detection else 'Low'}")
            
            config = scenario.exfiltration_config
            report.append("**Configuration:**")
            report.append(f"- Chunk Size: {config.chunk_size} bytes")
            report.append(f"- Encoding: {config.encoding.value}")
            report.append(f"- Timing Pattern: {config.timing_pattern.value}")
            report.append(f"- Base Delay: {config.base_delay}s")
            report.append(f"- Compression: {'Enabled' if config.compression else 'Disabled'}")
            report.append(f"- Encryption: {'Enabled' if config.encryption else 'Disabled'}")
            report.append(f"- Domain Rotation: {'Enabled' if config.domain_rotation else 'Disabled'}")
            
            if scenario.notes:
                report.append(f"**Research Notes:** {scenario.notes}")
            
            report.append("")
        
        return "\n".join(report)

def main():
    """Demonstration du gestionnaire de configurations"""
    print("⚙️  DoH Exfiltration Configuration Manager")
    print("=" * 50)
    
    # Creer le gestionnaire
    manager = DoHConfigManager()
    
    # Lister les scenarios
    print(f"\n📋 Available scenarios: {len(manager.list_scenarios())}")
    for name in manager.list_scenarios():
        scenario = manager.get_scenario(name)
        detection = "🔴 High" if scenario.expected_detection else "🟢 Low"
        print(f"   • {scenario.name} - Detection: {detection}")
    
    # Afficher la comparaison
    manager.print_scenario_comparison()
    
    # Sauvegarder tous les scenarios
    manager.export_all_scenarios()
    print(f"\n💾 All scenarios exported to: configs/all_scenarios.json")
    
    # Generer le rapport de recherche
    report = manager.generate_research_report()
    with open("configs/research_report.md", 'w') as f:
        f.write(report)
    print(f"📄 Research report generated: configs/research_report.md")
    
    # Exemple d'utilisation d'un scenario
    print(f"\n🔬 Example: Using 'advanced_stealth' scenario")
    scenario = manager.get_scenario("advanced_stealth")
    if scenario:
        config = scenario.exfiltration_config
        print(f"   Chunk size: {config.chunk_size}")
        print(f"   Encoding: {config.encoding.value}")
        print(f"   Timing: {config.timing_pattern.value}")
        print(f"   Features: {'Encryption' if config.encryption else ''} "
              f"{'Compression' if config.compression else ''} "
              f"{'Randomization' if config.subdomain_randomization else ''}")

if __name__ == "__main__":
    main()
