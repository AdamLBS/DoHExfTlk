# DoH Exfiltration Detection System

## Overview

This system detects and reconstructs data exfiltration attempts using DNS over HTTPS (DoH) queries. It monitors network traffic in real-time and identifies suspicious patterns typical of data exfiltration techniques.

## 🎯 Detection Methodology

### Pattern Recognition
The system detects exfiltration attempts based on:
- **Subdomain encoding patterns**: `{index}-{base64_chunk}.{random}.target_domain`
- **Sequential chunk numbering**: Data split into numbered segments
- **Base64 encoding detection**: Identifies encoded data in DNS queries
- **Suspicious domain patterns**: Monitors for specific target domains

### Supported Exfiltration Patterns
- **Domain**: `exfill.local` (configurable)
- **Format**: `0-dGVzdA.abc123.exfill.local`
- **Encoding**: Base64 URL-safe encoding
- **Transport**: DNS queries via DoH

## 🔍 Detection Process

### 1. Network Interception
```bash
# Automatic interface detection
IFLINK=$(docker exec resolver cat /sys/class/net/eth0/iflink)
IFACE=$(ip link | grep -B1 "^ *$IFLINK:" | head -n 1 | awk '{print $2}')
```

### 2. Traffic Analysis
- Captures DNS packets on port 53
- Filters for target domain patterns
- Extracts chunk index and data payload
- Validates base64 encoding

### 3. Data Reconstruction
```python
# Chunk extraction and ordering
chunks[index] = base64_chunk
ordered_data = ''.join(chunks[i] for i in sorted(chunks))
decoded_data = base64.urlsafe_b64decode(ordered_data)
```

## 📊 Output Analysis

### Detection Files
Detected exfiltration attempts are saved as:
- `exfiltrated_data_1_chunks.txt` - First chunk detected
- `exfiltrated_data_2_chunks.txt` - Two chunks assembled
- `exfiltrated_data_N_chunks.txt` - Complete reconstruction

### File Content Analysis
```bash
# View all detected attempts
ls -la ./sniffer/output/

# Analyze reconstruction progress
for file in ./sniffer/output/exfiltrated_data_*.txt; do
    echo "=== $file ==="
    head -3 "$file"
    echo
done
```

## 🛠️ Customization

### Modify Target Domain
Edit `sniffer/decode_live.py`:
```python
DOMAIN = "your-target-domain.com"
```

### Adjust Detection Pattern
Modify the regex pattern:
```python
pattern = re.compile(r"(\d+)-([a-zA-Z0-9_\-]+=*)")
```

### Change Output Directory
```python
output_file = f"/custom/path/exfiltrated_data_{len(chunks)}_chunks.txt"
```

## 🚨 Detection Alerts

### Real-time Monitoring
The system provides real-time alerts:
```
[🚨 EXFILTRATION DETECTED] Chunk 0: dGVzdCBkYXRh... -> 0-dGVzdCBkYXRh.abc123.exfill.local
[🚨 EXFILTRATION DETECTED] Chunk 1: bGljZW5jZSBleA... -> 1-bGljZW5jZSBleA.def456.exfill.local
[✅] Rebuilt file with 2 chunks -> /app/output/exfiltrated_data_2_chunks.txt
```

### Alert Types
- **Chunk Detection**: Individual data chunk identified
- **Reconstruction Success**: Complete file assembled
- **Suspicious Queries**: Potential exfiltration attempts
- **Pattern Matches**: Domain/subdomain pattern hits

## 📈 Performance Metrics

### Detection Accuracy
- **True Positives**: Correctly identified exfiltration attempts
- **False Positives**: Legitimate queries flagged as suspicious
- **False Negatives**: Missed exfiltration attempts

### Reconstruction Success Rate
- **Complete**: All chunks received and assembled
- **Partial**: Some chunks missing or corrupted
- **Failed**: Unable to decode or reconstruct

## 🔧 Advanced Configuration

### Multi-Domain Detection
```python
DOMAINS = ["exfill.local", "data.evil.com", "leak.suspicious.net"]

def try_extract_chunk(qname):
    for domain in DOMAINS:
        if domain in qname:
            # Process detection logic
            pass
```

### Custom Encoding Support
```python
def decode_chunk(chunk):
    try:
        # Try base64 URL-safe
        return base64.urlsafe_b64decode(chunk)
    except:
        try:
            # Try standard base64
            return base64.b64decode(chunk)
        except:
            # Try hex encoding
            return bytes.fromhex(chunk)
```

### Enhanced Logging
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/output/detection.log'),
        logging.StreamHandler()
    ]
)
```

## 🧪 Testing Scenarios

### Basic Exfiltration Test
```bash
# Create test data
echo "Secret information" > /tmp/secret.txt

# Run exfiltration simulation
docker exec -it client_test bash /scripts/test_exfiltration.sh
```

### Multi-file Exfiltration
```bash
# Test with multiple files
for file in /tmp/secret*.txt; do
    python3 exfiltration_client.py "$file"
done
```

### Large Data Exfiltration  
```bash
# Generate large test file
dd if=/dev/urandom of=/tmp/large_secret.bin bs=1024 count=100

# Test chunking and reconstruction
python3 exfiltration_client.py /tmp/large_secret.bin
```

## 🎓 Educational Use Cases

### Cybersecurity Training
- Demonstrate data exfiltration techniques
- Practice network monitoring skills
- Learn DNS covert channel detection
- Understand base64 encoding in attacks

### Research Applications
- Protocol analysis and reverse engineering
- Network forensics methodology development
- Threat intelligence pattern creation
- Security tool effectiveness testing

## ⚡ Performance Optimization

### Memory Usage
- Efficient chunk storage with dictionaries
- Automatic cleanup of completed reconstructions
- Configurable maximum file size limits

### CPU Optimization
- Compiled regex patterns for faster matching
- Selective packet filtering to reduce processing
- Asynchronous I/O for file operations

### Network Efficiency
- Interface-specific packet capture
- Protocol-specific filtering (UDP port 53)
- Minimal packet inspection overhead

## 🔒 Security Considerations

### Ethical Use
- **Educational purposes only**
- **Authorized testing environments**
- **No unauthorized network monitoring**
- **Respect privacy and legal boundaries**

### Data Handling
- **Secure storage** of reconstructed data
- **Access control** for output files
- **Data retention policies**
- **Secure deletion** of sensitive information
