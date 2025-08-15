# Configuration Guide

## 🔧 System Configuration

This guide covers all configuration aspects of the DoH Exfiltration Detection Platform.

## Traefik TLS Configuration (`certs/tls.yml`)
```yaml
tls:
  certificates:
    - certFile: /certs/doh.local.crt
      keyFile: /certs/doh.local.key
      stores:
        - default
```

## 🎯 Exfiltration Client Configuration

### Configuration Generator Tool

The platform uses `config_generator.py` to create and manage exfiltration configurations via JSON files. This provides a flexible and reproducible way to define test scenarios. A few configurations files are already provided.

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
```

### JSON Configuration Format

The configuration format supports comprehensive exfiltration scenarios:

```json
{
  "name": "Burst",
  "description": "Burst",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "exfill.local",
    "chunk_size": 30,
    "encoding": "base64",
    "timing_pattern": "burst",
    "base_delay": 0.1,
    "compression": false,
    "encryption": false,
    "subdomain_randomization": false,
    "padding": false,
    "domain_rotation": false,
    "burst_size": 100,
    "burst_delay": 0.1
  },
  "test_files": [
    "/app/test_data/image.png"
  ],
  "notes": ""
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

## 📝 Configuration Best Practices

### Development Environment
- Use quick mode for ML training
- Enable verbose logging
- Reduce timeouts for faster iteration
- Use smaller datasets

### Security Hardening
- Change default domains and paths
- Use strong encryption keys

### Performance Tuning
- Adjust chunk sizes based on network conditions
- Optimize buffer sizes for packet capture
- Balance detection sensitivity vs. performance
- Configure appropriate resource limits
