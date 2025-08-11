# FAQ - Frequently Asked Questions

## 🎯 General Questions

### What is the DoH Exfiltration Detection Platform?
A comprehensive research platform for studying and detecting data exfiltration techniques using DNS-over-HTTPS (DoH). It combines network traffic analysis, pattern detection, machine learning, and forensic reconstruction.

### What is the purpose of this platform?
- **Academic research** on DoH exfiltration techniques
- **Cybersecurity training** in controlled environments
- **Detection method development** and validation
- **Forensic analysis** of exfiltration attempts

### Is this platform ready for production use?
This is primarily a research and educational platform. While it demonstrates effective detection techniques, production deployment would require additional hardening, monitoring, and integration work.

## 🔧 Technical Questions

### How does the detection work?
The platform uses multiple detection approaches:
1. **Pattern Analysis**: Detects suspicious DNS query structures
2. **Statistical Analysis**: Identifies anomalous traffic patterns
3. **Machine Learning**: Classifies queries as benign/malicious
4. **Behavioral Analysis**: Analyzes timing and frequency patterns

### What ML workflow is used?
1. Train models on network flow datasets (`model_trainer.py`)
2. DoHLyzer analyzes traffic and generates flow data
3. Filter detected queries (`filter_detection_csv.sh`)
4. Classify filtered queries (`predictor.py`)

### What exfiltration techniques are supported?
- Base64/Hex/Base32 encoding
- Chunked data transmission
- Domain rotation and randomization
- Various timing patterns (regular, burst, stealth)
- Multiple data types (text, binary, images)

## 🚀 Setup and Installation

### What are the system requirements?
- **OS**: Linux, macOS, or Windows with WSL2
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 10GB free space
- **CPU**: 2+ cores for ML training
- **Software**: Docker & Docker Compose

### Why do I need to generate certificates?
The platform uses HTTPS for DoH communication. Self-signed certificates are generated for the local `doh.local` domain to enable secure DoH testing in the isolated environment.

### Can I use custom domains?
Yes, modify the `TARGET_DOMAIN` and `DOH_DOMAINS` environment variables in `docker-compose.yml` and update the certificate generation accordingly.

## 🔍 Usage Questions

### How do I test exfiltration detection?
```bash
# Basic test
docker exec -it client_test bash /scripts/test_exfiltration.sh

# Custom test
docker exec -it exfil_client python3 client.py
```

### How do I view detection results?
```bash
# List detected files
ls -la exfiltration/server/captured/

# View traffic analysis
cat traffic_analyzer/output/output.csv

# Check ML predictions
python3 ml_analyzer/predictor.py --analyze
```

### How do I train new ML models?
```bash
# Quick training (development)
python3 ml_analyzer/model_trainer.py --quick

# Full training (production)
python3 ml_analyzer/model_trainer.py
```

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check port conflicts
sudo netstat -tlpn | grep -E ":(80|443|8080)\s"

# Restart services
docker compose down && docker compose up -d
```

### DoH server not responding
```bash
# Check certificate validity
openssl x509 -in certs/doh.local.crt -text -noout

# Verify DNS resolution in container
docker exec client_test nslookup doh.local

# Check Traefik logs
docker logs traefik
```

### Detection not working
```bash
# Verify network capture
docker exec exfil_interceptor tcpdump -i any -c 10

# Check detection logs
docker logs exfil_interceptor --tail 50

# Verify interface detection
docker exec exfil_interceptor ip link show
```

### ML models not training
```bash
# Check dataset availability
ls -la datasets/

# Verify Python dependencies
docker exec -it exfil_client pip list

# Check memory usage
docker stats
```

## 📊 Performance Questions

### How much data can be exfiltrated?
The platform can handle files up to 100MB, though performance depends on:
- Chunk size configuration
- Network latency
- Detection system load
- Available memory

### What's the detection accuracy?
Performance varies by configuration:
- **Pattern Detection**: >99% for structured exfiltration
- **ML Classification**: >95% on training datasets
- **False Positives**: <3% with optimized thresholds

### How fast is the detection?
- **Real-time Pattern Detection**: <1 second
- **ML Classification**: <5 seconds per batch
- **Full Reconstruction**: Depends on file size and chunks

## 🔒 Security Questions

### Is this platform safe to use?
Yes, when used as intended:
- ✅ Isolated Docker environment
- ✅ Self-signed certificates
- ✅ No external network access required
- ❌ Should not be used for actual malicious activities

### Can this be detected by real security systems?
The exfiltration techniques demonstrated here could be detected by:
- Advanced DNS monitoring systems
- Machine learning-based network analysis
- Behavioral analysis systems
- Proper DoH traffic inspection

### How can organizations defend against these techniques?
- Monitor DNS query patterns and volumes
- Implement DoH traffic inspection
- Use machine learning for anomaly detection
- Deploy network behavior analysis
- Regular security awareness training

## 💾 Data Questions

### Where is data stored?
- **Detected Files**: `exfiltration/server/captured/`
- **Traffic Analysis**: `traffic_analyzer/output/`
- **ML Models**: `models/`
- **Datasets**: `datasets/`

### How is data cleaned up?
Manual cleanup is required:
```bash
# Clean detection results
rm -rf exfiltration/server/captured/*

# Clean analysis data
rm -rf traffic_analyzer/output/*

# Reset ML models
rm -rf models/*
```

### Can I export results?
```bash
# Export detection data
docker cp exfil_interceptor:/app/captured ./results/

# Export analysis data
docker cp traffic_analyzer:/app/output ./analysis/

# Export models
docker cp exfil_client:/models ./trained_models/
```

## 🎓 Educational Questions

### What can I learn from this platform?
- DoH protocol internals
- Data exfiltration techniques
- Network traffic analysis
- Machine learning for cybersecurity
- Docker containerization
- DNS security concepts

### How can I extend the platform?
- Implement new exfiltration techniques
- Add detection algorithms
- Create custom ML features
- Develop new analysis tools
- Add visualization dashboards

### What's the academic value?
- Understanding covert channels
- Studying DNS security
- Analyzing ML in cybersecurity
- Research in network forensics
- Educational demonstration tool

## 🤝 Community Questions

### How can I contribute?
- Report bugs and issues
- Suggest new features
- Improve documentation
- Add test cases
- Share research findings

### Where can I get help?
- GitHub Issues for bugs
- GitHub Discussions for questions
- Documentation in `/docs` folder
- Code comments and examples

### Can I use this in my research?
Yes, please cite the project in academic work:
```bibtex
@misc{kent-doh-detection-2025,
  title={DoH Exfiltration Detection Platform},
  author={[Your name]},
  year={2025},
  institution={University of Kent}
}
```
