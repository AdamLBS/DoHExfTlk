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

### 1. ML Model Development
```bash
# Train models on network flow data
cd ml_analyzer
python3 model_trainer.py

# Models saved to /models/
ls ../models/
```

### 2. Traffic Analysis
```bash
# DoHLyzer generates flow analysis
# Results in traffic_analyzer/output/output.csv

# Filter for detected exfiltration queries only
cd exfiltration/client
./filter_detection_csv.sh

# This creates filtered dataset with malicious queries
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

# Debug network issues
docker exec [container] netstat -tulpn
docker exec [container] tcpdump -i any -n
```

### Python Debugging
```python
# Add debugging to Python code
import logging
logging.basicConfig(level=logging.DEBUG)

# Breakpoint debugging
import pdb; pdb.set_trace()
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

# Monitor network performance
docker exec traffic_analyzer iftop
```

### Code Optimization
- Use efficient data structures
- Implement proper caching
- Optimize database queries
- Profile ML model performance

## 🤝 Contributing Guidelines

### Code Style
- Follow PEP 8 for Python
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

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

### Documentation
- Update README for new features
- Add inline code comments
- Document configuration changes
- Update API documentation

## 🔐 Security Considerations

### Development Security
- Use development certificates only
- Don't commit secrets to Git
- Regular dependency updates
- Code security scanning

### Production Deployment
- Use proper TLS certificates
- Implement access controls
- Monitor for vulnerabilities
- Regular security audits

## 🚀 Deployment

### Production Build
```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Deploy with production settings
docker compose -f docker-compose.prod.yml up -d
```

### Monitoring Setup
```bash
# Add monitoring stack
docker compose -f docker-compose.yml -f monitoring.yml up -d

# View metrics
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
```

## 📋 Maintenance

### Regular Tasks
- Update Docker images
- Clean old detection data
- Retrain ML models
- Review security logs

### Backup Procedures
```bash
# Backup configuration
tar -czf backup_$(date +%Y%m%d).tar.gz \
    docker-compose.yml certs/ datasets/ models/

# Backup detection data
docker cp exfil_interceptor:/app/captured ./backup/captured/
docker cp traffic_analyzer:/app/output ./backup/analysis/
```

This development guide provides the essential information for working with the DoH Exfiltration Detection Platform while keeping focus on the practical workflow and key components.
