import sys
from scapy.all import PcapReader, DNSQR
import base64

fifo_path = sys.argv[1]

def try_decode(sub):
    try:
        return base64.b64decode(sub).decode("utf-8", errors="ignore")
    except:
        return None

print("🟢 Sniffer started. Waiting for DNS queries...\n")
sys.stdout.flush()

with PcapReader(fifo_path) as pcap:
    for pkt in pcap:
        if pkt.haslayer(DNSQR):
            qname = pkt[DNSQR].qname.decode()
            sub = qname.split('.')[0]
            decoded = try_decode(sub)
            if decoded:
                print(f"[📥] {decoded}")
                sys.stdout.flush()
                with open("output.txt", "a") as f:
                    f.write(decoded + "\n")
