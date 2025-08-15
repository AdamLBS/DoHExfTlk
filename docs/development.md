# Development Guide

## 🛠️ Development Environment Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Git
- Text editor/IDE

### Quick Development Setup
```bash
# Clone repository
git clone https://github.com/AdamLBS/Kent-Dissertation.git
cd Kent-Dissertation

# Start development environment
docker compose up -d

# Access development containers
docker exec -it exfil_client bash
docker exec -it traffic_analyzer bash
```

## 📁 Project Structure

```
Kent-Dissertation/
├── docker-compose.yml          # Main orchestration
├── generate_certs.sh           # TLS certificate generation
├── 
├── exfiltration/               # Exfiltration components
│   ├── client/                 # Sophisticated exfiltration client
│   │   ├── client.py          # Main client implementation
│   │   ├── config_generator.py # Configuration utilities
│   │   └── filter_detection_csv.sh # Filter detected queries
│   └── server/                 # Detection and reconstruction
│       ├── server.py          # Pattern detection server
│       └── traffic_interceptor.py # Network capture
│
├── DoHLyzer/                   # Traffic analysis framework
│   ├── analyzer/              # Core analysis engine
│   ├── meter/                 # Traffic measurement
│   └── visualizer/            # Data visualization
│
├── ml_analyzer/                # Machine learning pipeline
│   ├── model_trainer.py       # Train detection models
│   └── predictor.py           # Classify detected queries
│
├── traffic_analyzer/           # Network flow analysis
│   └── output/                # Analysis results (CSV)
│
├── datasets/                   # Training datasets
├── models/                     # Trained ML models
└── docs/                      # Documentation
```

## 🔄 Development Workflow

### 0. Dataset Preparation
```bash
# Download CIRA-CIC-DoHBrw-2020 dataset
# Source: https://www.unb.ca/cic/datasets/dohbrw-2020.html

wget http://cicresearch.ca/CICDataset/DoHBrw-2020/Dataset/CSVs/Total_CSVs.zip
unzip Total_CSVs.zip
mkdir -p datasets
cp l2-benign.csv l2-malicious.csv datasets/

# Verify dataset structure
head -5 datasets/*.csv
```

### 1. ML Model Development
```bash
# Train models on CIRA-CIC-DoHBrw-2020 dataset
cd ml_analyzer
python3 model_trainer.py

# Models saved to /models/
ls ../models/
```

### 2. Traffic Analysis
```bash
# DoHLyzer generates flow analysis
# Results in traffic_analyzer/output/output.csv
docker compose up traffic_analyzer
```

### 3. Query Classification
```bash
# Use trained models to classify detected queries
cd ml_analyzer
python3 predictor.py --input ../traffic_analyzer/output/filtered_output.csv

# Results show which detected queries are confirmed malicious
```

### 4. Testing Exfiltration
```bash
# Test different exfiltration scenarios
docker exec -it exfil_client python3 client.py

# Monitor detection
docker logs -f exfil_interceptor
docker logs -f traffic_analyzer
```

## 🧪 Testing Framework

### Unit Tests
```bash
# Run component tests
python -m pytest tests/

# Test specific components
python -m pytest tests/test_exfiltration_client.py
python -m pytest tests/test_detection_patterns.py
```

### Integration Tests
```bash
# End-to-end exfiltration tests
./scripts/test_exfiltration_scenarios.sh

# Performance benchmarks
./scripts/benchmark_detection.sh
```

### Manual Testing
```bash
# Test DoH connectivity
docker exec -it client_test bash /scripts/test_doh.sh

# Test pattern detection
docker exec -it client_test bash /scripts/test_exfiltration.sh
```

## 🔧 Configuration for Development

### Environment Variables
```bash
# Development overrides
export LOG_LEVEL=DEBUG
export QUICK_MODE=true
export MAX_SAMPLES=1000

# Enable verbose logging
export DOH_SERVER_VERBOSE=true
export PYTHONUNBUFFERED=1
```

### Development Docker Compose
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  exfil_client:
    build: ./exfiltration/client
    volumes:
      - ./exfiltration/client:/app  # Live code reload
      - ./datasets:/datasets
    environment:
      - LOG_LEVEL=DEBUG
```

## 🐛 Debugging

### Container Debugging
```bash
# Access running containers
docker exec -it [container_name] bash

# View logs with timestamps
docker logs -f -t [container_name]

```


### Network Analysis
```bash
# Monitor DoH traffic
docker exec traffic_analyzer tcpdump -i any port 443

# Check DNS resolution
docker exec client_test dig @resolver google.com

# Test DoH queries manually
curl -H "accept: application/dns-json" \
     "https://doh.local/dns-query?name=example.com&type=A"
```

## 📊 Performance Optimization

### Resource Monitoring
```bash
# Monitor container resources
docker stats

# Check disk usage
docker system df

```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/new-detection-method

# Make changes and test
git add .
git commit -m "Add new detection method"

# Push and create PR
git push origin feature/new-detection-method
```