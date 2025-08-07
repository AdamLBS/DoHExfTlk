#!/usr/bin/env python3
"""
DoH Traffic Interceptor

Intercepteur de trafic réseau pour capturer et analyser les requêtes DNS/DoH
sans remplacer le serveur DoH existant.
"""

import asyncio
import json
import logging
import signal
import sys
import time
import os
from typing import Dict, Optional
from scapy.all import sniff, DNS, DNSQR, IP, TCP, UDP
from scapy.layers.http import HTTPRequest, HTTPResponse
import threading
import queue

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DoHTrafficInterceptor:
    """Intercepteur de trafic DoH pour détecter l'exfiltration"""
    
    def __init__(self, interface=None, output_dir="/app/captured", 
                 capture_filter="port 53 or port 443 or port 8080",
                 doh_domains=None):
        self.interface = interface or "eth0"
        self.output_dir = output_dir
        self.capture_filter = capture_filter
        self.doh_domains = doh_domains or ['doh.local', 'exfill.local']
        self.dns_callback = None  # Callback function pour traiter les requêtes DNS
        self.packet_queue = queue.Queue()
        self.stats = {
            'total_packets': 0,
            'dns_packets': 0,
            'http_packets': 0,
            'exfiltration_detected': 0,
            'start_time': time.time()
        }
        self.running = False
        
        logger.info(f"🔍 DoH Traffic Interceptor initialized")
        logger.info(f"📡 Interface: {self.interface}")
        logger.info(f"🎯 Monitoring domains: {self.doh_domains}")
        logger.info(f"📁 Output directory: {self.output_dir}")
    
    def packet_handler(self, packet):
        """Gestionnaire de paquets capturés"""
        try:
            self.stats['total_packets'] += 1
            
            # Analyser les paquets DNS classiques
            if packet.haslayer(DNS):
                self._handle_dns_packet(packet)
            
            # Analyser les paquets HTTP/HTTPS (DoH)
            elif packet.haslayer(TCP):
                self._handle_tcp_packet(packet)
            
            # Log périodique des statistiques
            if self.stats['total_packets'] % 1000 == 0:
                self._log_stats()
                
        except Exception as e:
            logger.error(f"❌ Error processing packet: {e}")
    
    def _handle_dns_packet(self, packet):
        """Traite les paquets DNS classiques"""
        if packet.haslayer(DNSQR):
            self.stats['dns_packets'] += 1
            
            # Extraire les informations DNS
            dns_query = packet[DNSQR]
            domain = dns_query.qname.decode('utf-8').rstrip('.')
            source_ip = packet[IP].src if packet.haslayer(IP) else "unknown"
            
            logger.debug(f"🔍 DNS Query: {domain} from {source_ip}")
            
            # Créer les données de la requête
            query_data = {
                'query_name': domain,
                'src_ip': source_ip,
                'timestamp': time.time(),
                'domain': domain
            }
            
            # Appeler le callback si défini
            if self.dns_callback:
                self.dns_callback(query_data)
    
    def _handle_tcp_packet(self, packet):
        """Traite les paquets TCP (potentiellement DoH)"""
        if not packet.haslayer(IP):
            return
            
        # Vérifier si c'est du trafic vers les domaines DoH surveillés
        dest_port = packet[TCP].dport if packet.haslayer(TCP) else 0
        
        # Ports typiques pour DoH : 443 (HTTPS), 8080 (test)
        if dest_port in [443, 8080]:
            self.stats['http_packets'] += 1
            
            # Essayer d'extraire les données HTTP si possible
            try:
                if packet.haslayer(HTTPRequest):
                    self._analyze_http_request(packet)
            except:
                pass  # Pas de données HTTP lisibles
    
    def _analyze_http_request(self, packet):
        """Analyse les requêtes HTTP pour détecter DoH"""
        try:
            http_req = packet[HTTPRequest]
            host = http_req.Host.decode('utf-8') if http_req.Host else ""
            path = http_req.Path.decode('utf-8') if http_req.Path else ""
            
            # Vérifier si c'est une requête DoH
            doh_domains = ["doh.local", "exfill.local"]
            if '/dns-query' in path and any(domain in host for domain in doh_domains):
                source_ip = packet[IP].src
                
                # Extraire les paramètres de la requête
                if '?' in path:
                    query_params = path.split('?')[1]
                    params = dict(param.split('=') for param in query_params.split('&') if '=' in param)
                    
                    domain = params.get('name', '')
                    if domain:
                        logger.debug(f"🔍 DoH Query: {domain} from {source_ip}")
                        
                        # Créer les données de la requête
                        query_data = {
                            'query_name': domain,
                            'src_ip': source_ip,
                            'timestamp': time.time(),
                            'domain': domain
                        }
                        
                        # Appeler le callback si défini
                        if self.dns_callback:
                            self.dns_callback(query_data)
                            
        except Exception as e:
            logger.debug(f"Error analyzing HTTP request: {e}")
    
    def _log_stats(self):
        """Log les statistiques périodiquement"""
        uptime = time.time() - self.stats['start_time']
        logger.info(f"📊 Stats - Packets: {self.stats['total_packets']}, "
                   f"DNS: {self.stats['dns_packets']}, "
                   f"HTTP: {self.stats['http_packets']}, "
                   f"Exfil: {self.stats['exfiltration_detected']}, "
                   f"Uptime: {uptime:.1f}s")
    
    def start_capture(self):
        """Démarre la capture de paquets"""
        logger.info(f"🚀 Starting packet capture on {self.interface}")
        logger.info(f"🔍 Filter: {self.capture_filter}")
        
        self.running = True
        
        try:
            # Démarrer la capture avec Scapy
            sniff(
                iface=self.interface,
                filter=self.capture_filter,
                prn=self.packet_handler,
                stop_filter=lambda x: not self.running
            )
        except PermissionError:
            logger.error("❌ Permission denied. Run as root or with CAP_NET_RAW capability")
            raise
        except Exception as e:
            logger.error(f"❌ Capture error: {e}")
            raise
    
    def stop_capture(self):
        """Arrête la capture"""
        logger.info("🛑 Stopping packet capture...")
        self.running = False
        
        # Afficher les statistiques finales
        self.print_final_stats()
        self.exfil_server.print_statistics()
    
    def print_final_stats(self):
        """Affiche les statistiques finales"""
        uptime = time.time() - self.stats['start_time']
        
        logger.info(f"\n📈 FINAL STATISTICS:")
        logger.info(f"   ⏱️  Runtime: {uptime:.2f} seconds")
        logger.info(f"   📦 Total packets: {self.stats['total_packets']}")
        logger.info(f"   🔍 DNS packets: {self.stats['dns_packets']}")
        logger.info(f"   🌐 HTTP packets: {self.stats['http_packets']}")
        logger.info(f"   🎯 Exfiltration detected: {self.stats['exfiltration_detected']}")
        logger.info(f"   📊 Detection rate: {(self.stats['exfiltration_detected']/max(self.stats['dns_packets'], 1)*100):.2f}%")

class NetworkMonitor:
    """Moniteur réseau principal simplifié"""
    
    def __init__(self, interface: str = 'eth0', output_dir: str = '/app/captured', 
                 capture_filter: str = 'port 53 or port 443 or port 8080',
                 doh_domains: list = None):
        if doh_domains is None:
            doh_domains = ['doh.local', 'exfill.local']
        
        self.interface = interface
        self.output_dir = output_dir
        self.capture_filter = capture_filter
        self.doh_domains = doh_domains
        self.interceptor = None
        self.shutdown_event = threading.Event()
    
    def _load_config_from_env(self):
        """Charge la configuration depuis les variables d'environnement"""
        self.interface = os.getenv('INTERFACE', self.interface)
        self.output_dir = os.getenv('OUTPUT_DIR', self.output_dir)
        self.capture_filter = os.getenv('CAPTURE_FILTER', self.capture_filter)
        domains_str = os.getenv('DOH_DOMAINS', ','.join(self.doh_domains))
        self.doh_domains = domains_str.split(',') if domains_str else self.doh_domains
    
    def signal_handler(self, signum, frame):
        """Gestionnaire de signaux"""
        logger.info(f"📡 Received signal {signum}, shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Arrêt propre"""
        self.shutdown_event.set()
        if self.interceptor:
            self.interceptor.stop_capture()
    
    def run(self):
        """Lance le moniteur"""
        # Configuration des gestionnaires de signaux
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            logger.info("✅ DoH Traffic Monitor starting...")
            
            # Créer l'intercepteur avec les paramètres
            self.interceptor = DoHTrafficInterceptor(
                interface=self.interface,
                output_dir=self.output_dir,
                capture_filter=self.capture_filter,
                doh_domains=self.doh_domains
            )
            
            # Démarrer la capture dans un thread séparé
            capture_thread = threading.Thread(target=self.interceptor.start_capture)
            capture_thread.daemon = True
            capture_thread.start()
            
            # Attendre le signal d'arrêt
            self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Monitor error: {e}")
            raise
        finally:
            self.shutdown()

def check_permissions():
    """Vérifie les permissions nécessaires"""
    if os.geteuid() != 0:
        logger.warning("⚠️  Not running as root. May need CAP_NET_RAW capability for packet capture.")
        return False
    return True

def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DoH Traffic Interceptor")
    parser.add_argument('--config', help='Configuration file path (deprecated)')
    parser.add_argument('--interface', '-i', default='eth0', help='Network interface to monitor')
    parser.add_argument('--output', '-o', default='/app/captured', help='Output directory')
    parser.add_argument('--filter', help='Packet capture filter')
    parser.add_argument('--domains', help='Comma-separated list of DoH domains to monitor')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--check-perms', action='store_true', help='Check permissions and exit')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.check_perms:
        has_perms = check_permissions()
        print(f"Permissions check: {'✅ OK' if has_perms else '❌ FAILED'}")
        sys.exit(0 if has_perms else 1)
    
    # Vérifier les permissions
    if not check_permissions():
        logger.error("❌ Insufficient permissions for packet capture")
        sys.exit(1)
    
    # Configuration du moniteur
    doh_domains = args.domains.split(',') if args.domains else ['doh.local', 'exfill.local']
    capture_filter = args.filter if args.filter else 'port 53 or port 443 or port 8080'
    
    monitor = NetworkMonitor(
        interface=args.interface,
        output_dir=args.output,
        capture_filter=capture_filter,
        doh_domains=doh_domains
    )
    
    # Charger les variables d'environnement
    monitor._load_config_from_env()
    
    # Lancer le moniteur
    try:
        monitor.run()
    except KeyboardInterrupt:
        logger.info("👋 Monitor stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
