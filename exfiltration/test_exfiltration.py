#!/usr/bin/env python3
"""
DoH Exfiltration Test Suite

Suite de tests complete pour valider le systeme d'exfiltration DoH
avec differentes configurations et scenarios de test.
"""

import sys
import os
import time
import tempfile
import json
from typing import List, Dict, Any

# Ajouter le chemin pour importer nos modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from client import DoHExfiltrationClient, ExfiltrationConfig, EncodingType, TimingPattern
from server import DoHExfiltrationServer

class DoHExfiltrationTester:
    """Testeur pour le systeme d'exfiltration DoH"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="doh_test_")
        self.server = DoHExfiltrationServer(os.path.join(self.temp_dir, "captured"))
        self.test_results = []
        
        print(f"🧪 DoH Exfiltration Test Suite initialized")
        print(f"📁 Temp directory: {self.temp_dir}")
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Cree un fichier de test"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def create_binary_test_file(self, filename: str, data: bytes) -> str:
        """Cree un fichier binaire de test"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(data)
        return filepath
    
    def simulate_doh_traffic(self, client: DoHExfiltrationClient, data_or_file, is_file: bool = True) -> List[str]:
        """
        Simule le trafic DoH en interceptant les requetes du client
        et en les transmettant au serveur
        """
        captured_domains = []
        
        # Monkey patch pour capturer les requetes
        original_get = client.session.get
        
        def mock_get(url, params=None, headers=None, timeout=None):
            # Capturer le domaine de la requete
            if params and 'name' in params:
                domain = params['name']
                captured_domains.append(domain)
                
                # Transmettre au serveur pour analyse
                source_ip = "192.168.1.100"  # IP simulee
                self.server.process_dns_request(domain, source_ip)
            
            # Simuler une reponse HTTP 200
            class MockResponse:
                status_code = 200
                def json(self):
                    return {"Status": 0, "Answer": []}
            
            return MockResponse()
        
        # Appliquer le mock
        client.session.get = mock_get
        
        try:
            # Executer l'exfiltration
            if is_file:
                success = client.exfiltrate_file(data_or_file)
            else:
                success = client.exfiltrate_data(data_or_file, "test_data")
        finally:
            # Restaurer la methode originale
            client.session.get = original_get
        
        return captured_domains
    
    def test_basic_exfiltration(self) -> Dict[str, Any]:
        """Test d'exfiltration basique"""
        print("\n🔬 Test 1: Basic Text Exfiltration")
        print("-" * 40)
        
        # Creer un fichier de test
        test_content = "This is a secret message for DoH exfiltration testing!"
        test_file = self.create_test_file("secret.txt", test_content)
        
        # Configuration client
        config = ExfiltrationConfig(
            chunk_size=20,
            encoding=EncodingType.BASE64,
            timing_pattern=TimingPattern.REGULAR,
            base_delay=0.01  # Tres rapide pour les tests
        )
        
        client = DoHExfiltrationClient(config)
        
        # Simuler l'exfiltration
        start_time = time.time()
        domains = self.simulate_doh_traffic(client, test_file, is_file=True)
        duration = time.time() - start_time
        
        # Analyser les resultats
        result = {
            'test_name': 'basic_exfiltration',
            'success': len(domains) > 0,
            'original_size': len(test_content.encode()),
            'domains_generated': len(domains),
            'duration': duration,
            'domains': domains[:3],  # Premiers domaines pour verification
            'server_sessions': len(self.server.sessions)
        }
        
        self.test_results.append(result)
        
        print(f"✅ Generated {len(domains)} DNS queries")
        print(f"⏱️  Duration: {duration:.3f}s")
        print(f"🔍 Server captured {len(self.server.sessions)} sessions")
        
        return result
    
    def test_binary_exfiltration(self) -> Dict[str, Any]:
        """Test d'exfiltration de donnees binaires"""
        print("\n🔬 Test 2: Binary Data Exfiltration")
        print("-" * 40)
        
        # Creer des donnees binaires de test
        binary_data = bytes(range(256)) + b"Binary test data with special chars: \x00\xFF\x7F"
        test_file = self.create_binary_test_file("binary.dat", binary_data)
        
        # Configuration avec compression
        config = ExfiltrationConfig(
            chunk_size=25,
            encoding=EncodingType.BASE64,
            compression=True,
            timing_pattern=TimingPattern.RANDOM,
            base_delay=0.01,
            delay_variance=0.005
        )
        
        client = DoHExfiltrationClient(config)
        
        # Simuler l'exfiltration
        start_time = time.time()
        domains = self.simulate_doh_traffic(client, test_file, is_file=True)
        duration = time.time() - start_time
        
        result = {
            'test_name': 'binary_exfiltration',
            'success': len(domains) > 0,
            'original_size': len(binary_data),
            'domains_generated': len(domains),
            'duration': duration,
            'compression': True,
            'server_sessions': len(self.server.sessions)
        }
        
        self.test_results.append(result)
        
        print(f"✅ Generated {len(domains)} DNS queries")
        print(f"⏱️  Duration: {duration:.3f}s")
        print(f"🗜️  Compression enabled")
        
        return result
    
    def test_stealth_exfiltration(self) -> Dict[str, Any]:
        """Test d'exfiltration furtive"""
        print("\n🔬 Test 3: Stealth Exfiltration")
        print("-" * 40)
        
        # Donnees sensibles simulees
        sensitive_data = json.dumps({
            "passwords": ["admin123", "secret456"],
            "api_keys": ["sk-abc123", "pk-def456"],
            "database": "postgresql://user:pass@host/db"
        }, indent=2).encode()
        
        # Configuration furtive
        config = ExfiltrationConfig(
            chunk_size=15,  # Petits chunks
            encoding=EncodingType.CUSTOM,  # Encodage personnalise
            timing_pattern=TimingPattern.STEALTH,
            base_delay=0.02,  # Plus lent
            compression=True,
            encryption=True,
            encryption_key="secret_key_2024",
            subdomain_randomization=True,
            padding=True
        )
        
        client = DoHExfiltrationClient(config)
        
        # Simuler l'exfiltration
        start_time = time.time()
        domains = self.simulate_doh_traffic(client, sensitive_data, is_file=False)
        duration = time.time() - start_time
        
        result = {
            'test_name': 'stealth_exfiltration',
            'success': len(domains) > 0,
            'original_size': len(sensitive_data),
            'domains_generated': len(domains),
            'duration': duration,
            'encryption': True,
            'compression': True,
            'custom_encoding': True,
            'server_sessions': len(self.server.sessions)
        }
        
        self.test_results.append(result)
        
        print(f"✅ Generated {len(domains)} DNS queries")
        print(f"⏱️  Duration: {duration:.3f}s")
        print(f"🔐 Encryption + Compression + Custom encoding")
        
        return result
    
    def test_burst_exfiltration(self) -> Dict[str, Any]:
        """Test d'exfiltration en rafale"""
        print("\n🔬 Test 4: Burst Exfiltration")
        print("-" * 40)
        
        # Creer un fichier plus volumineux
        large_content = "CONFIDENTIAL DATA\n" * 100
        large_content += "This is a large file to test burst transmission patterns.\n" * 50
        test_file = self.create_test_file("large_secret.txt", large_content)
        
        # Configuration en rafale
        config = ExfiltrationConfig(
            chunk_size=40,  # Gros chunks
            encoding=EncodingType.BASE64,
            timing_pattern=TimingPattern.BURST,
            base_delay=0.001,  # Tres rapide dans les rafales
            burst_size=5,
            burst_delay=0.05  # Pause entre rafales
        )
        
        client = DoHExfiltrationClient(config)
        
        # Simuler l'exfiltration
        start_time = time.time()
        domains = self.simulate_doh_traffic(client, test_file, is_file=True)
        duration = time.time() - start_time
        
        result = {
            'test_name': 'burst_exfiltration',
            'success': len(domains) > 0,
            'original_size': len(large_content.encode()),
            'domains_generated': len(domains),
            'duration': duration,
            'burst_pattern': True,
            'server_sessions': len(self.server.sessions)
        }
        
        self.test_results.append(result)
        
        print(f"✅ Generated {len(domains)} DNS queries")
        print(f"⏱️  Duration: {duration:.3f}s")
        print(f"💥 Burst pattern: {config.burst_size} chunks per burst")
        
        return result
    
    def test_server_reconstruction(self) -> Dict[str, Any]:
        """Test de reconstruction des donnees par le serveur"""
        print("\n🔬 Test 5: Server Data Reconstruction")
        print("-" * 40)
        
        # Attendre que le serveur complete les reconstructions
        time.sleep(0.5)
        
        # Analyser les sessions du serveur
        sessions = self.server.list_active_sessions()
        completed_sessions = [s for s in sessions if s['is_complete']]
        
        print(f"📊 Total sessions: {len(sessions)}")
        print(f"✅ Completed sessions: {len(completed_sessions)}")
        
        # Verifier les fichiers reconstruits
        captured_dir = os.path.join(self.temp_dir, "captured")
        if os.path.exists(captured_dir):
            files = os.listdir(captured_dir)
            binary_files = [f for f in files if f.endswith('.bin')]
            metadata_files = [f for f in files if f.endswith('.json')]
            
            print(f"💾 Reconstructed files: {len(binary_files)}")
            print(f"📄 Metadata files: {len(metadata_files)}")
            
            # Analyser quelques fichiers
            for binary_file in binary_files[:3]:
                file_path = os.path.join(captured_dir, binary_file)
                file_size = os.path.getsize(file_path)
                print(f"   📁 {binary_file}: {file_size} bytes")
        
        result = {
            'test_name': 'server_reconstruction',
            'total_sessions': len(sessions),
            'completed_sessions': len(completed_sessions),
            'reconstruction_rate': len(completed_sessions) / len(sessions) if sessions else 0,
            'files_created': len(binary_files) if 'binary_files' in locals() else 0
        }
        
        self.test_results.append(result)
        return result
    
    def run_all_tests(self):
        """Execute tous les tests"""
        print("🚀 Starting DoH Exfiltration Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Executer les tests
        tests = [
            self.test_basic_exfiltration,
            self.test_binary_exfiltration,
            self.test_stealth_exfiltration,
            self.test_burst_exfiltration,
            self.test_server_reconstruction
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"❌ Test failed: {e}")
        
        total_duration = time.time() - start_time
        
        # Afficher le resume
        self.print_test_summary(total_duration)
        
        # Afficher les statistiques du serveur
        self.server.print_statistics()
    
    def print_test_summary(self, total_duration: float):
        """Affiche le resume des tests"""
        print(f"\n📊 TEST SUMMARY")
        print("=" * 60)
        
        successful_tests = sum(1 for r in self.test_results if r.get('success', True))
        total_tests = len(self.test_results)
        
        print(f"⏱️  Total duration: {total_duration:.2f}s")
        print(f"✅ Successful tests: {successful_tests}/{total_tests}")
        print(f"📡 Total domains generated: {sum(r.get('domains_generated', 0) for r in self.test_results)}")
        
        print(f"\n📋 Individual Test Results:")
        for result in self.test_results:
            status = "✅" if result.get('success', True) else "❌"
            name = result.get('test_name', 'unknown')
            print(f"   {status} {name}")
            
            if 'domains_generated' in result:
                print(f"      📡 Domains: {result['domains_generated']}")
            if 'duration' in result:
                print(f"      ⏱️  Time: {result['duration']:.3f}s")
            if 'original_size' in result:
                print(f"      📦 Size: {result['original_size']} bytes")
        
        # Sauvegarder les resultats
        results_file = os.path.join(self.temp_dir, "test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        print(f"📁 Test artifacts in: {self.temp_dir}")

def main():
    """Fonction principale"""
    tester = DoHExfiltrationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
