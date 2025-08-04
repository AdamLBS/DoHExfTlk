import argparse
from scapy.all import sniff, DNSQR
import base64
import re
from collections import defaultdict
import os

DOMAIN = "exfill.local"  # Domaine local pour les tests
chunks = defaultdict(str)
pattern = re.compile(r"(\d+)-([a-zA-Z0-9_\-]+=*)")

def try_extract_chunk(qname):
    if DOMAIN not in qname:
        return None, None
    m = pattern.match(qname.split('.')[0])
    if m:
        index = int(m.group(1))
        chunk = m.group(2)
        return index, chunk
    return None, None

def try_rebuild(chunks):
    try:
        ordered = ''.join(chunks[i] for i in sorted(chunks))
        padded = ordered + '=' * (-len(ordered) % 4)
        data = base64.urlsafe_b64decode(padded)
        
        # Créer le répertoire output s'il n'existe pas
        os.makedirs("/app/output", exist_ok=True)
        
        output_file = f"/app/output/exfiltrated_data_{len(chunks)}_chunks.txt"
        with open(output_file, "wb") as f:
            f.write(data)
        print(f"[✅] Rebuilt file with {len(chunks)} chunks -> {output_file}")
        print(f"[📄] Content preview: {data[:100].decode('utf-8', errors='ignore')}...")
    except Exception as e:
        print(f"[⚠️] Rebuild failed: {e}")

def process_packet(pkt):
    if pkt.haslayer(DNSQR):
        qname = pkt[DNSQR].qname.decode(errors="ignore")
        index, chunk = try_extract_chunk(qname)
        if index is not None:
            chunks[index] = chunk
            print(f"[� EXFILTRATION DETECTED] Chunk {index}: {chunk[:15]}... -> {qname}")
            try_rebuild(chunks)
        else:
            # Log des requêtes DNS normales pour debug
            if "exfill" in qname.lower():
                print(f"[🔍] Suspicious DNS query: {qname}")

def main():
    parser = argparse.ArgumentParser(description="Live DNS exfiltration sniffer")
    parser.add_argument("--iface", required=True, help="Interface réseau à écouter (ex: eth0, vethXXX)")
    args = parser.parse_args()

    print(f"🟢 Live DoH exfil sniffer started on interface {args.iface}...")
    print(f"🎯 Monitoring for exfiltration patterns on domain: {DOMAIN}")
    print(f"📁 Output directory: /app/output/")
    print("="*60)
    
    sniff(filter="udp port 53", prn=process_packet, store=0, iface=args.iface)

if __name__ == "__main__":
    main()
