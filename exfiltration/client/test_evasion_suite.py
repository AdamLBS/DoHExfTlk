#!/usr/bin/env python3
"""
Automated DoH Evasion Testing Suite

Suite de tests automatisés pour évaluer différentes techniques d'évasion DoH
et leurs taux de détection.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvasionTestSuite:
    """Suite de tests d'évasion DoH"""
    
    def __init__(self, results_dir: str = "test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_single_test(self, config_file: str, test_file: str, 
                       timeout: int = 300) -> Dict[str, Any]:
        """
        Exécute un test unique avec une configuration donnée
        
        Args:
            config_file: Fichier de configuration à tester
            test_file: Fichier à exfiltrer
            timeout: Timeout en secondes
            
        Returns:
            Résultats du test
        """
        logger.info(f"🧪 Testing configuration: {config_file}")
        
        start_time = time.time()
        
        try:
            # Préparer la commande
            cmd = [
                sys.executable, "quick_test_json.py",
                "--config", config_file,
                test_file
            ]
            
            # Exécuter le test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Analyser les résultats
            success = result.returncode == 0
            
            # Extraire les statistiques de la sortie
            stats = self._parse_output_stats(result.stdout)
            
            test_result = {
                'config_file': config_file,
                'test_file': test_file,
                'success': success,
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            }
            
            # Charger les métadonnées de la configuration
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                test_result['config_name'] = config_data.get('name', 'Unknown')
                test_result['description'] = config_data.get('description', '')
                test_result['detection_expected'] = config_data.get('detection_expected', False)
            except:
                pass
            
            if success:
                logger.info(f"✅ Test succeeded in {duration:.2f}s")
            else:
                logger.error(f"❌ Test failed in {duration:.2f}s")
                logger.error(f"Error: {result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Test timed out after {timeout}s")
            return {
                'config_file': config_file,
                'test_file': test_file,
                'success': False,
                'duration': timeout,
                'return_code': -1,
                'error': 'Timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            return {
                'config_file': config_file,
                'test_file': test_file,
                'success': False,
                'duration': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _parse_output_stats(self, output: str) -> Dict[str, Any]:
        """Parse les statistiques de la sortie du test"""
        stats = {}
        
        lines = output.split('\n')
        for line in lines:
            if 'File size:' in line and 'bytes' in line:
                try:
                    size_str = line.split('File size:')[1].split('bytes')[0].strip()
                    stats['file_size'] = int(size_str.replace(',', ''))
                except:
                    pass
            elif 'Total chunks:' in line:
                try:
                    chunks = int(line.split('Total chunks:')[1].strip())
                    stats['total_chunks'] = chunks
                except:
                    pass
            elif 'Successful chunks:' in line:
                try:
                    successful = int(line.split('Successful chunks:')[1].strip())
                    stats['successful_chunks'] = successful
                except:
                    pass
            elif 'Success rate:' in line:
                try:
                    rate_str = line.split('Success rate:')[1].split('%')[0].strip()
                    stats['success_rate'] = float(rate_str)
                except:
                    pass
            elif 'Average speed:' in line:
                try:
                    speed_str = line.split('Average speed:')[1].split('KB/s')[0].strip()
                    stats['avg_speed_kbps'] = float(speed_str)
                except:
                    pass
        
        return stats
    
    def run_test_suite(self, config_files: List[str], test_files: List[str],
                      timeout: int = 300) -> List[Dict[str, Any]]:
        """
        Exécute une suite complète de tests
        
        Args:
            config_files: Liste des fichiers de configuration à tester
            test_files: Liste des fichiers à exfiltrer
            timeout: Timeout par test
            
        Returns:
            Liste des résultats de tests
        """
        logger.info(f"🚀 Starting evasion test suite")
        logger.info(f"📋 Configurations: {len(config_files)}")
        logger.info(f"📁 Test files: {len(test_files)}")
        logger.info(f"🧪 Total tests: {len(config_files) * len(test_files)}")
        
        self.start_time = time.time()
        self.test_results = []
        
        total_tests = len(config_files) * len(test_files)
        current_test = 0
        
        for config_file in config_files:
            for test_file in test_files:
                current_test += 1
                logger.info(f"📊 Progress: {current_test}/{total_tests} - {config_file} + {test_file}")
                
                result = self.run_single_test(config_file, test_file, timeout)
                self.test_results.append(result)
                
                # Pause entre les tests pour éviter la surcharge
                time.sleep(1)
        
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        logger.info(f"🎉 Test suite completed in {total_duration:.2f}s")
        
        return self.test_results
    
    def generate_report(self, output_file: str = None) -> str:
        """Génère un rapport des résultats de tests"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"evasion_test_report_{timestamp}.json"
        
        report = {
            'test_suite_info': {
                'start_time': datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
                'end_time': datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
                'total_duration': self.end_time - self.start_time if self.start_time and self.end_time else 0,
                'total_tests': len(self.test_results)
            },
            'summary': self._generate_summary(),
            'test_results': self.test_results
        }
        
        output_path = self.results_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Report generated: {output_path}")
        
        # Générer aussi un rapport markdown
        md_file = output_path.with_suffix('.md')
        self._generate_markdown_report(report, md_file)
        
        return str(output_path)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Génère un résumé des résultats"""
        if not self.test_results:
            return {}
        
        successful_tests = [r for r in self.test_results if r.get('success', False)]
        failed_tests = [r for r in self.test_results if not r.get('success', False)]
        
        # Statistiques par configuration
        config_stats = {}
        for result in self.test_results:
            config = result.get('config_file', 'Unknown')
            if config not in config_stats:
                config_stats[config] = {'total': 0, 'successful': 0, 'failed': 0}
            
            config_stats[config]['total'] += 1
            if result.get('success', False):
                config_stats[config]['successful'] += 1
            else:
                config_stats[config]['failed'] += 1
        
        # Calcul des moyennes
        durations = [r.get('duration', 0) for r in self.test_results if r.get('duration')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_tests': len(self.test_results),
            'successful_tests': len(successful_tests),
            'failed_tests': len(failed_tests),
            'success_rate': len(successful_tests) / len(self.test_results) * 100,
            'average_duration': avg_duration,
            'config_statistics': config_stats
        }
    
    def _generate_markdown_report(self, report: Dict[str, Any], output_file: Path):
        """Génère un rapport markdown lisible"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# DoH Evasion Test Report\n\n")
            
            # Info générale
            info = report['test_suite_info']
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Duration:** {info.get('total_duration', 0):.2f} seconds\n")
            f.write(f"**Total Tests:** {info.get('total_tests', 0)}\n\n")
            
            # Résumé
            summary = report['summary']
            f.write("## Summary\n\n")
            f.write(f"- **Success Rate:** {summary.get('success_rate', 0):.1f}%\n")
            f.write(f"- **Successful Tests:** {summary.get('successful_tests', 0)}\n")
            f.write(f"- **Failed Tests:** {summary.get('failed_tests', 0)}\n")
            f.write(f"- **Average Duration:** {summary.get('average_duration', 0):.2f} seconds\n\n")
            
            # Statistiques par configuration
            f.write("## Configuration Statistics\n\n")
            f.write("| Configuration | Total | Success | Failed | Success Rate |\n")
            f.write("|---------------|-------|---------|--------|--------------|\n")
            
            for config, stats in summary.get('config_statistics', {}).items():
                rate = stats['successful'] / stats['total'] * 100 if stats['total'] > 0 else 0
                f.write(f"| {Path(config).stem} | {stats['total']} | {stats['successful']} | {stats['failed']} | {rate:.1f}% |\n")
            
            # Résultats détaillés
            f.write("\n## Detailed Results\n\n")
            
            for result in report['test_results']:
                config_name = result.get('config_name', Path(result.get('config_file', '')).stem)
                test_file = Path(result.get('test_file', '')).name
                success = "✅" if result.get('success') else "❌"
                duration = result.get('duration', 0)
                
                f.write(f"### {success} {config_name} - {test_file}\n\n")
                f.write(f"- **Duration:** {duration:.2f}s\n")
                f.write(f"- **Configuration:** {result.get('config_file', 'N/A')}\n")
                
                if result.get('stats'):
                    stats = result['stats']
                    f.write(f"- **File Size:** {stats.get('file_size', 'N/A')} bytes\n")
                    f.write(f"- **Chunks:** {stats.get('successful_chunks', 0)}/{stats.get('total_chunks', 0)}\n")
                    f.write(f"- **Success Rate:** {stats.get('success_rate', 0):.1f}%\n")
                    f.write(f"- **Speed:** {stats.get('avg_speed_kbps', 0):.2f} KB/s\n")
                
                if not result.get('success'):
                    error = result.get('error', result.get('stderr', 'Unknown error'))
                    f.write(f"- **Error:** {error}\n")
                
                f.write("\n")
        
        logger.info(f"📄 Markdown report generated: {output_file}")

def create_test_files(test_dir: str = "test_data") -> List[str]:
    """Crée des fichiers de test de différentes tailles"""
    test_path = Path(test_dir)
    test_path.mkdir(exist_ok=True)
    
    test_files = []
    
    # Petit fichier texte
    small_file = test_path / "small_test.txt"
    with open(small_file, 'w') as f:
        f.write("This is a small test file for DoH exfiltration testing.\n")
        f.write("Contains basic text data.\n")
    test_files.append(str(small_file))
    
    # Fichier moyen avec JSON
    medium_file = test_path / "medium_test.json"
    test_data = {
        "users": [
            {"id": i, "name": f"User{i}", "email": f"user{i}@example.com"}
            for i in range(100)
        ]
    }
    with open(medium_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    test_files.append(str(medium_file))
    
    # Fichier binaire
    binary_file = test_path / "binary_test.bin"
    with open(binary_file, 'wb') as f:
        f.write(b'\x00\x01\x02\x03' * 256)  # 1KB de données binaires
    test_files.append(str(binary_file))
    
    logger.info(f"✅ Created {len(test_files)} test files in {test_dir}")
    return test_files

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='DoH Evasion Testing Suite')
    parser.add_argument('--configs', nargs='*',
                       help='Configuration files to test (default: all in test_configs/)')
    parser.add_argument('--files', nargs='*',
                       help='Test files to use (default: create test files)')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Timeout per test in seconds (default: 300)')
    parser.add_argument('--output', default=None,
                       help='Output file for results (default: auto-generated)')
    parser.add_argument('--create-files', action='store_true',
                       help='Create test files and exit')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Créer des fichiers de test si demandé
    if args.create_files:
        create_test_files()
        return
    
    # Déterminer les configurations à tester
    if args.configs:
        config_files = args.configs
    else:
        config_dir = Path("test_configs")
        if config_dir.exists():
            config_files = [str(f) for f in config_dir.glob("*.json")]
        else:
            logger.error("❌ No configuration directory found. Run with --create-files first.")
            return
    
    if not config_files:
        logger.error("❌ No configuration files found")
        return
    
    # Déterminer les fichiers de test
    if args.files:
        test_files = args.files
    else:
        test_files = create_test_files()
    
    # Vérifier que les fichiers existent
    missing_configs = [f for f in config_files if not Path(f).exists()]
    missing_files = [f for f in test_files if not Path(f).exists()]
    
    if missing_configs:
        logger.error(f"❌ Missing configuration files: {missing_configs}")
        return
    
    if missing_files:
        logger.error(f"❌ Missing test files: {missing_files}")
        return
    
    # Exécuter la suite de tests
    logger.info(f"🎯 Starting evasion test suite")
    logger.info(f"📋 Configurations: {[Path(f).stem for f in config_files]}")
    logger.info(f"📁 Test files: {[Path(f).name for f in test_files]}")
    
    test_suite = EvasionTestSuite()
    results = test_suite.run_test_suite(config_files, test_files, args.timeout)
    
    # Générer le rapport
    report_file = test_suite.generate_report(args.output)
    
    # Afficher le résumé
    summary = test_suite._generate_summary()
    print(f"\n📊 Test Suite Summary:")
    print(f"   Total tests: {summary['total_tests']}")
    print(f"   Successful: {summary['successful_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    print(f"   Average duration: {summary['average_duration']:.2f}s")
    print(f"   Report: {report_file}")

if __name__ == "__main__":
    main()
