# Configuration Guide

## 🔧 System Configuration

This guide covers all configuration aspects of the DoH Exfiltration Detection Platform.

## 📄 Docker Compose Configuration

### Main Services Configuration

#### Traefik Proxy
```yaml
traefik:
  image: traefik:v2.10
  ports:
    - "80:80"      # HTTP
    - "443:443"    # HTTPS  
    - "8080:8080"  # Dashboard
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./certs:/certs:ro
  command:
    - "--api.insecure=true"
    - "--api.dashboard=true"
    - "--providers.docker=true"
    - "--providers.docker.exposedbydefault=false"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--providers.file.directory=/certs"
    - "--providers.file.watch=true"
```

**Key Configuration Options:**
- `api.dashboard`: Enable/disable Traefik dashboard
- `providers.docker.exposedbydefault`: Auto-expose Docker services
- `providers.file.watch`: Hot-reload certificate changes

#### DoH Server
```yaml
doh_server:
  image: satishweb/doh-server:latest
  environment:
    UPSTREAM_DNS_SERVER: "udp:resolver:53"
    DOH_HTTP_PREFIX: "/dns-query"
    DOH_SERVER_LISTEN: ":8053"
    DOH_SERVER_TIMEOUT: "10"
    DOH_SERVER_TRIES: "3"
    DOH_SERVER_VERBOSE: "true"
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.doh.rule=Host(`doh.local`)"
    - "traefik.http.routers.doh.entrypoints=websecure"
    - "traefik.http.routers.doh.tls=true"
```

**Environment Variables:**
- `UPSTREAM_DNS_SERVER`: Backend DNS resolver
- `DOH_HTTP_PREFIX`: DoH endpoint path
- `DOH_SERVER_TIMEOUT`: Query timeout in seconds
- `DOH_SERVER_TRIES`: Retry attempts for failed queries
- `DOH_SERVER_VERBOSE`: Enable detailed logging

### Detection Services Configuration

#### Exfiltration Interceptor
```yaml
exfil_interceptor:
  build: ./exfiltration/server/
  network_mode: host
  cap_add:
    - NET_RAW
    - NET_ADMIN
  environment:
    - OUTPUT_DIR=/app/captured
    - DOH_DOMAINS=doh.local,exfill.local
    - CAPTURE_FILTER=port 53 or port 443 or port 8080
    - PYTHONUNBUFFERED=1
```

**Configuration Parameters:**
- `OUTPUT_DIR`: Directory for captured exfiltration data
- `DOH_DOMAINS`: Comma-separated list of domains to monitor
- `CAPTURE_FILTER`: BPF filter for packet capture
- `network_mode: host`: Required for packet capture

#### Traffic Analyzer
```yaml
traffic_analyzer:
  build: ./traffic_analyzer/
  network_mode: host
  cap_add:
    - NET_RAW
    - NET_ADMIN
  environment:
    - PYTHONUNBUFFERED=1
    - OUTPUT_DIR=/app/output
```

**Volume Mounts:**
- `./traffic_analyzer/output:/app/output`: Analysis results
- `/var/run/docker.sock:/var/run/docker.sock:ro`: Docker API access

## 🌐 Network Configuration

### DNS Resolution Setup

#### Unbound Configuration (`resolver/unbound.conf`)
```ini
server:
    interface: 0.0.0.0
    port: 53
    do-ip4: yes
    do-ip6: no
    do-udp: yes
    do-tcp: yes
    
    # Security settings
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    
    # Performance
    num-threads: 2
    msg-cache-slabs: 4
    rrset-cache-slabs: 4
    infra-cache-slabs: 4
    key-cache-slabs: 4
    
    # Upstream DNS
    forward-zone:
        name: "."
        forward-addr: 8.8.8.8
        forward-addr: 1.1.1.1

# Custom domain overrides
local-zone: "exfill.local." static
local-data: "exfill.local. IN A 127.0.0.1"
```

### TLS Certificate Configuration

#### Certificate Generation (`generate_certs.sh`)
```bash
#!/bin/bash

# Generate CA private key
openssl genrsa -out certs/ca.key 4096

# Generate CA certificate
openssl req -new -x509 -days 365 -key certs/ca.key -out certs/ca.crt \
    -subj "/C=UK/ST=Kent/L=Canterbury/O=University/CN=DoH-CA"

# Generate server private key
openssl genrsa -out certs/doh.local.key 2048

# Generate certificate signing request
openssl req -new -key certs/doh.local.key -out certs/doh.local.csr \
    -subj "/C=UK/ST=Kent/L=Canterbury/O=University/CN=doh.local"

# Generate server certificate
openssl x509 -req -in certs/doh.local.csr -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/doh.local.crt -days 365
```

#### Traefik TLS Configuration (`certs/tls.yml`)
```yaml
tls:
  certificates:
    - certFile: /certs/doh.local.crt
      keyFile: /certs/doh.local.key
      stores:
        - default
  stores:
    default:
      defaultCertificate:
        certFile: /certs/doh.local.crt
        keyFile: /certs/doh.local.key
```

## 🎯 Exfiltration Client Configuration

### Configuration Generator Tool

The platform uses `config_generator.py` to create and manage exfiltration configurations via JSON files. This provides a flexible and reproducible way to define test scenarios.

#### Interactive Configuration Creation
```bash
cd exfiltration/client/
python config_generator.py --create
```

#### Configuration Management Commands
```bash
# List all available configurations
python config_generator.py --list

# Create template configurations
python config_generator.py --templates

# Test a configuration
python config_generator.py --test apt_simulation.json

# Edit existing configuration
python config_generator.py --edit stealth_research.json
```

### JSON Configuration Format

The configuration format supports comprehensive exfiltration scenarios:

```json
{
  "name": "APT Simulation",
  "description": "Simulation d'APT avec exfiltration très lente et discrète",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "update-service.local",
    "chunk_size": 8,
    "encoding": "base32",
    "timing_pattern": "random",
    "base_delay": 30.0,
    "delay_variance": 15.0,
    "compression": true,
    "encryption": true,
    "encryption_key": "apt_long_term_key",
    "subdomain_randomization": true,
    "domain_rotation": true,
    "backup_domains": [
      "security-updates.local",
      "maintenance-api.local",
      "status-check.local"
    ],
    "padding": true,
    "padding_size": 20
  },
  "test_files": [
    "financial_records.xlsx",
    "employee_data.csv"
  ]
  "notes": "Simulation APT : très lents délais, rotation domaines, chiffrement"
}
```

### Configuration Parameters

#### Basic Settings
- **`name`**: Configuration identifier
- **`description`**: Human-readable description
- **`test_files`**: Files to use for testing
- **`notes`**: Research notes and context

#### Exfiltration Configuration
- **`doh_server`**: DoH endpoint URL
- **`target_domain`**: Primary exfiltration domain
- **`chunk_size`**: Data chunk size (8-55 characters)
- **`encoding`**: Encoding method (base64, base32, hex, custom)

#### Timing Patterns
- **`timing_pattern`**: Pattern type (regular, random, burst, stealth)
- **`base_delay`**: Base delay between chunks (seconds)
- **`delay_variance`**: Random variance for timing (seconds)

#### Evasion Techniques
- **`compression`**: Enable data compression
- **`encryption`**: Enable data encryption
- **`encryption_key`**: Encryption key for data
- **`subdomain_randomization`**: Randomize subdomain patterns
- **`domain_rotation`**: Use multiple domains
- **`backup_domains`**: Alternative domains list
- **`padding`**: Add random padding
- **`padding_size`**: Size of padding data

### Preset Configuration Templates

#### Quick Test Configuration
```json
{
  "name": "Quick Test",
  "description": "Configuration rapide pour tests de base",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "exfill.local",
    "chunk_size": 30,
    "encoding": "base64",
    "timing_pattern": "regular",
    "base_delay": 0.3,
    "compression": false,
    "encryption": false,
    "subdomain_randomization": true
  },
  "test_files": ["sample.txt"]
  "notes": "Configuration de base pour validation rapide"
}
```

#### Stealth Research Configuration
```json
{
  "name": "Stealth Research",
  "description": "Configuration furtive pour recherche d'évasion",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "cdn-service.local",
    "chunk_size": 15,
    "encoding": "custom",
    "timing_pattern": "stealth",
    "base_delay": 5.0,
    "delay_variance": 2.0,
    "compression": true,
    "encryption": true,
    "encryption_key": "research_stealth_key",
    "subdomain_randomization": true,
    "padding": true,
    "padding_size": 12,
    "domain_rotation": true,
    "backup_domains": ["api-cache.local", "media-cdn.local"]
  },
  "test_files": ["sensitive_data.json", "credentials.txt"]
  "notes": "Techniques d'évasion avancées pour contourner la détection ML"
}
```

#### Speed Benchmark Configuration
```json
{
  "name": "Speed Benchmark",
  "description": "Configuration optimisée pour vitesse maximale",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "fast-api.local",
    "chunk_size": 55,
    "encoding": "base64",
    "timing_pattern": "burst",
    "base_delay": 0.001,
    "burst_size": 20,
    "burst_delay": 0.1,
    "compression": true,
    "subdomain_randomization": false,
    "max_retries": 1,
    "retry_delay": 0.05,
    "timeout": 2.0
  },
  "test_files": ["large_file.bin"],
  "notes": "Test de vitesse maximale - facilement détectable"
}
```

## 🔍 Detection Configuration

### Pattern Detection Settings
```python
# exfiltration/server/server.py
class DetectionConfig:
    # Domain patterns to monitor
    MONITORED_DOMAINS = ["exfill.local", "data.local", "leak.local"]
    
    # Pattern matching
    CHUNK_PATTERN = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 100
    
    # Timing analysis
    CHUNK_TIMEOUT = 30  # seconds
    SESSION_TIMEOUT = 300  # seconds
    
    # File reconstruction
    OUTPUT_DIR = "/app/captured"
    AUTO_DECODE = True
    SUPPORTED_ENCODINGS = ["base64", "hex", "base32"]
```

### Traffic Analysis Configuration
```python
# traffic_analyzer/config.py
class TrafficConfig:
    # Capture settings
    INTERFACE = "auto"  # Auto-detect or specify interface
    CAPTURE_FILTER = "port 53 or port 443"
    BUFFER_SIZE = 65536
    
    # Analysis settings
    FLOW_TIMEOUT = 60
    EXPORT_INTERVAL = 300
    OUTPUT_FORMAT = "csv"
    
    # Feature extraction
    PACKET_FEATURES = True
    TIMING_FEATURES = True
    STATISTICAL_FEATURES = True
```

## 🤖 Machine Learning Configuration

### Model Training Settings
```python
# ml_analyzer/config.py
class MLConfig:
    # Dataset settings
    QUICK_MODE = False
    MAX_SAMPLES = None
    TEST_SIZE = 0.2
    VALIDATION_SIZE = 0.25
    
    # Feature engineering
    NUMERIC_FEATURES = [
        'Duration', 'FlowBytesSent', 'FlowBytesReceived',
        'PacketLengthMean', 'PacketLengthVariance',
        'PacketTimeMean', 'PacketTimeVariance'
    ]
    
    # Model parameters
    CROSS_VAL_FOLDS = 5
    RANDOM_STATE = 42
    
    # Class balancing
    USE_SMOTE = True
    BALANCE_RATIO = 0.5
    
    # Model selection
    MODELS = {
        'random_forest': {
            'n_estimators': [100, 200],
            'max_depth': [10, 15, 20],
            'min_samples_split': [5, 10],
            'class_weight': ['balanced']
        },
        'gradient_boosting': {
            'n_estimators': [100, 150],
            'learning_rate': [0.05, 0.1],
            'max_depth': [3, 5],
            'subsample': [0.8, 0.9]
        }
    }
```

### Performance Optimization
```python
# Quick mode for development
MLConfig.QUICK_MODE = True
MLConfig.MAX_SAMPLES = 10000
MLConfig.CROSS_VAL_FOLDS = 3

# Production mode for accuracy
MLConfig.QUICK_MODE = False
MLConfig.MAX_SAMPLES = None
MLConfig.CROSS_VAL_FOLDS = 5
```

## 📊 Monitoring and Logging

### Log Configuration
```python
# Logging setup
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/detection.log',
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'exfiltration': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
```

### Metrics Collection
```python
# Metrics configuration
METRICS_CONFIG = {
    'enabled': True,
    'collection_interval': 60,  # seconds
    'export_format': 'prometheus',
    'metrics': {
        'detection_rate': True,
        'false_positive_rate': True,
        'reconstruction_success': True,
        'processing_latency': True
    }
}
```

## 🔒 Security Configuration

### Container Security
```yaml
# docker-compose.yml security settings
security_opt:
  - no-new-privileges:true
  - seccomp:unconfined  # Required for packet capture

read_only: true  # Where possible
tmpfs:
  - /tmp
  - /var/tmp

user: "1000:1000"  # Non-root where possible
```

### Network Security
```yaml
# Network isolation
networks:
  dohnet:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
```

### Resource Limits
```yaml
# Resource constraints
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## 🎛️ Environment Variables Reference

### Global Settings
```bash
# Core configuration
DOH_SERVER=https://doh.local/dns-query
TARGET_DOMAIN=exfill.local
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# Detection settings
OUTPUT_DIR=/app/captured
CAPTURE_FILTER="port 53 or port 443"
INTERFACE=auto

# ML settings
ML_MODEL_PATH=/models
QUICK_MODE=false
MAX_SAMPLES=50000

# Security settings
SSL_VERIFY=false
CERT_PATH=/certs
```

### Service-Specific Variables

#### DoH Server
```bash
UPSTREAM_DNS_SERVER=udp:resolver:53
DOH_HTTP_PREFIX=/dns-query
DOH_SERVER_LISTEN=:8053
DOH_SERVER_TIMEOUT=10
DOH_SERVER_TRIES=3
DOH_SERVER_VERBOSE=true
```

#### Detection Services
```bash
DOH_DOMAINS=doh.local,exfill.local
CHUNK_TIMEOUT=30
SESSION_TIMEOUT=300
AUTO_DECODE=true
SUPPORTED_ENCODINGS=base64,hex,base32
```

#### Traffic Analyzer
```bash
FLOW_TIMEOUT=60
EXPORT_INTERVAL=300
OUTPUT_FORMAT=csv
PACKET_FEATURES=true
TIMING_FEATURES=true
```

## 🔄 Configuration Updates

### Hot Reloading
Some configurations support hot reloading:
- TLS certificates (Traefik)
- DNS configuration (Unbound)
- Detection patterns (restart required)

### Configuration Validation
```bash
# Validate Docker Compose
docker compose config

# Test configuration changes
docker compose up --dry-run

# Apply configuration updates
docker compose up -d --force-recreate
```

### Backup and Restore
```bash
# Backup current configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    docker-compose.yml certs/ resolver/ datasets/

# Restore configuration
tar -xzf config_backup_YYYYMMDD.tar.gz
docker compose down
docker compose up -d
```

## 📝 Configuration Best Practices

### Development Environment
- Use quick mode for ML training
- Enable verbose logging
- Reduce timeouts for faster iteration
- Use smaller datasets

### Production Environment
- Disable debug logging
- Use proper TLS certificates
- Set appropriate resource limits
- Configure monitoring and alerting

### Security Hardening
- Change default domains and paths
- Use strong encryption keys
- Implement proper access controls
- Regular security updates

### Performance Tuning
- Adjust chunk sizes based on network conditions
- Optimize buffer sizes for packet capture
- Balance detection sensitivity vs. performance
- Configure appropriate resource limits
