# Kent-Dissertation: DoH Exfiltration Detection Platform

> **Complete platform for data exfiltration detection via DNS-over-HTTPS (DoH)**  
> *Cybersecurity research toolkit for analysis and detection of advanced exfiltration techniques*

[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-Educational-orange.svg)](#)

## 📋 Overview

This research platform enables the study and detection of data exfiltration techniques using DNS-over-HTTPS (DoH). It combines multiple complementary approaches: network traffic capture, behavioral analysis, machine learning, and data reconstruction.

### 🎯 Project objectives

- **Academic research**: Study of DoH exfiltration techniques
- **Advanced detection**: Combination of traditional and ML methods
- **Forensic analysis**: Reconstruction and analysis of exfiltrated data
- **Training**: Controlled environment for cybersecurity learning

## 🏗️ System architecture

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Client Tests  │  DoH Infrastructure │  Detection Layer  │
│                 │                     │                   │
│ • Exfil Clients │ • DoH Server        │ • Traffic Analyzer│
│ • Test Scripts  │ • DNS Resolver      │ • ML Models       │
│ • Config Tools  │ • TLS Proxy        │ • Pattern Detection│
└─────────────────┴─────────────────┴─────────────────┘
                            │
                    ┌───────────────┐
                    │ Data Analysis │
                    │               │
                    │ • DoHLyzer    │
                    │ • ML Trainer  │
                    │ • Classifiers │
                    └───────────────┘
```

## 🚀 Quick start

### Prerequisites
- Docker & Docker Compose
- Linux/macOS (WSL2 for Windows)
- 4GB RAM minimum

### Installation in 3 steps

```bash
# 1. Clone the project
git clone <repository-url>
cd Kent-Dissertation

# 2. Generate TLS certificates
chmod +x generate_certs.sh
./generate_certs.sh

# 3. Start the infrastructure
docker compose up -d
```

### Installation verification

```bash
# Check services
docker compose ps

# Test DoH server
docker exec -it client_test bash /scripts/test_doh.sh

# Run exfiltration test
docker exec -it client_test bash /scripts/test_exfiltration.sh
```

## 📚 Complete Documentation

| Document | Description |
|----------|-------------|
| [📖 User Guide](docs/user-guide.md) | Complete usage instructions and workflows |
| [🏗️ Technical Architecture](docs/architecture.md) | Infrastructure details and design |
| [🔧 Configuration Guide](docs/configuration.md) | Component configuration and customization |
| [🤖 Machine Learning](docs/ml-analysis.md) | ML models, training, and classification |
| [📊 Data Analysis](docs/data-analysis.md) | Traffic analysis and pattern detection |
| [🛠️ Development Guide](docs/development.md) | Developer setup and contribution guide |
| [❓ FAQ](docs/faq.md) | Frequently asked questions |
| [🔧 Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |
| [📋 Examples](docs/examples.md) | Usage examples and scenarios |

## 🧩 Main components

### DoH Infrastructure
- **DoH Server**: DNS-over-HTTPS server with TLS
- **DNS Resolver**: Unbound resolution backend
- **TLS Proxy**: Traefik for SSL termination

### Detection and analysis
- **Traffic Analyzer**: Network traffic capture and analysis
- **Exfiltration Server**: Pattern detection and reconstruction
- **DoHLyzer**: Behavioral analysis framework
- **ML Analyzer**: Machine learning models

### Clients and testing
- **Configuration Generator**: JSON-based test scenario creation (`config_generator.py`)
- **Exfiltration Client**: Advanced client with multiple encoding and evasion techniques
- **Test Scenarios**: APT simulation, stealth research, speed benchmarks
- **Test Scripts**: Automated testing and validation tools

## 📊 Detection features

### Traditional methods
- **Pattern analysis**: Detection of suspicious DNS structures
- **Temporal analysis**: Identification of abnormal rhythms
- **Content analysis**: Suspicious Base64 encoding detection

## 🤖 Machine Learning Workflow

### Training Phase
```bash
# 1. Train models on network flow datasets
cd ml_analyzer
python3 model_trainer.py

# Models are saved to /models/ directory
```

### Detection and Classification Phase
```bash
# 2. DoHLyzer analyzes traffic and generates flow data
# Results stored in traffic_analyzer/output/output.csv

# 3. Filter detected exfiltration queries
cd exfiltration/client
./filter_detection_csv.sh

# 4. Classify filtered queries with trained models
cd ../../ml_analyzer
python3 predictor.py --input ../traffic_analyzer/output/filtered_output.csv
```

The ML pipeline validates whether DoHLyzer-detected queries are truly malicious using pre-trained models.

### Data reconstruction
- **Automatic assembly**: Intelligent chunk reconstruction
- **Multi-format decoding**: Base64, Hex, Base32, custom encodings
- **File type detection**: Automatic identification and analysis
- **ML validation**: Classification of detected queries as malicious/benign

## 🎛️ Configuration Management

### JSON-based Configuration System
```bash
# Generate new configuration interactively
cd exfiltration/client/
python config_generator.py --create

# Use predefined templates
python config_generator.py --templates

# List available configurations
python config_generator.py --list

# Test configuration before use
python config_generator.py --test apt_simulation.json
```

### Configuration Examples

**APT Simulation:**
```json
{
  "name": "APT Simulation",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "update-service.local",
    "chunk_size": 8,
    "encoding": "base32",
    "timing_pattern": "random",
    "base_delay": 30.0,
    "encryption": true,
    "domain_rotation": true,
    "backup_domains": ["security-updates.local", "maintenance-api.local"]
  },
  "detection_expected": false
}
```

**Running with Configuration:**
```bash
python run_client.py --config test_configs/apt_simulation.json
```

### Main environment variables
```bash
# DoH Server
DOH_SERVER=https://doh.local/dns-query
TARGET_DOMAIN=exfill.local

# Detection
OUTPUT_DIR=/app/captured
RESOLVER_MONITOR="port 53"
TRAEFIK_MONITOR="port 443 and host traefik"

# Machine Learning
ML_MODEL_PATH=/models
QUICK_MODE=false
```

## 📈 Metrics and results

### Detection performance
- **Accuracy**: >95% on training datasets
- **False Positives**: <3% with optimization
- **Detection time**: <1s for simple patterns
- **Reconstruction**: 99% success rate

### Technical capabilities
- **Max throughput**: 1000+ queries/minute
- **File sizes**: Up to 100MB
- **Supported formats**: Text, binary, images, documents
- **Encodings**: Base64, Hex, Base32, custom

## 🔒 Security considerations

⚠️ **EDUCATIONAL USE ONLY**

This platform is designed for:
- ✅ Academic research
- ✅ Cybersecurity training
- ✅ Authorized testing in controlled environment
- ❌ No malicious use
- ❌ No unauthorized surveillance

## 🛠️ Development and contribution

### Code structure
```
├── exfiltration/          # Exfiltration clients and servers
├── DoHLyzer/             # DoH analysis framework
├── ml_analyzer/          # Machine learning models
├── traffic_analyzer/     # Network capture and analysis
├── classifier/           # Specialized classifiers
├── datasets/             # Training datasets
└── docs/                 # Complete documentation
```

### Testing and validation
```bash
# Unit tests
python -m pytest tests/

# Integration tests
./scripts/integration_tests.sh

# Performance benchmarks
./scripts/benchmark.sh
```

## 📋 Roadmap

### Current version (v1.0)
- ✅ Complete DoH infrastructure
- ✅ Pattern detection
- ✅ Basic Machine Learning
- ✅ Data reconstruction

### Next versions
- 🔄 Advanced real-time detection
- 🔄 Deep learning behavioral analysis
- 🔄 Web monitoring interface
- 🔄 REST API for integrations

## 📞 Support and resources

### Documentation
- [Complete FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Usage examples](docs/examples.md)

### Community
- GitHub Issues for bugs and features
- Discussions for general questions
- Wiki for collaborative documentation

## 📄 License and citations

This project is developed in an academic context. For any academic use, please cite:

```bibtex
@misc{kent-doh-detection-2025,
  title={DoH Exfiltration Detection Platform},
  author={[Your name]},
  year={2025},
  institution={University of Kent},
  note={Dissertation project}
}
```

---

**⚠️ Important reminder**: This platform is exclusively intended for research, education and authorized testing. Use for malicious activities is strictly prohibited and contrary to the spirit of the project.