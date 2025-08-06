# DoH (DNS over HTTPS) Local Testing Environment

This project sets up a complete DoH local environment for testing and analyzing DNS over HTTPS traffic, including data exfiltration detection capabilities.

## 🏗️ Architecture

- **Traefik**: Reverse proxy with self-signed certificates for HTTPS termination
- **DoH Server**: DNS over HTTPS server (satishweb/doh-server) 
- **Resolver**: Unbound DNS resolver as backend for actual DNS resolution
- **Sniffer**: Network traffic capture container with exfiltration detection
- **Client Test**: Ubuntu container for running DoH tests and simulations

## 🚀 Quick Start

### 1. Generate Self-Signed Certificates
```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

### 2. Start the Environment
```bash
docker compose up -d
```

**Note**: No host system modifications required. Everything is automatically configured within containers.

## 🧪 Testing

### Basic DoH Server Test
```bash
docker exec -it client_test bash /scripts/test_doh.sh
```
This script tests:
- DoH queries via HTTPS
- Certificate validation with self-signed certs
- Direct server connectivity
- Classic DNS resolution via resolver

### Data Exfiltration Simulation
```bash
docker exec -it client_test bash /scripts/test_exfiltration.sh
```
This script:
- Creates a secret file with sensitive data
- Splits data into base64-encoded chunks
- Exfiltrates data via DoH queries using subdomain encoding
- Sends requests to `https://doh.local/dns-query`

### Continuous DoH Exfiltration Test
```bash
docker exec -it client_test bash /scripts/exfiltrate_doh.sh
```

## 🔍 Exfiltration Detection System

The sniffer container automatically detects and reconstructs exfiltrated data:

### Detection Pattern
- **Target Domain**: `exfill.local`
- **Subdomain Format**: `{index}-{base64_chunk}.{random}.exfill.local`
- **Method**: Network packet inspection on resolver interface

### Real-time Reconstruction
Detected exfiltration data is automatically:
1. **Intercepted** from DNS queries
2. **Decoded** from base64 chunks  
3. **Reassembled** in correct order
4. **Saved** to `/sniffer/output/exfiltrated_data_X_chunks.txt`

### Viewing Detected Data
```bash
# List all detected exfiltration attempts
ls -la ./sniffer/output/

# View reconstructed data
cat ./sniffer/output/exfiltrated_data_7_chunks.txt
```

## 🌐 Service Access

- **DoH Server**: `https://doh.local/dns-query`
- **Traefik Dashboard**: `http://localhost:8080`
- **DNS Resolver**: `localhost:53` (via resolver container)

## 🔧 Advanced Testing

### Testing from Host System
If you want to test from the host system, add the DNS entry:
```bash
echo "127.0.0.1    doh.local" | sudo tee -a /etc/hosts
```

Then test:
```bash
curl -k -H "Accept: application/dns-json" \
     "https://doh.local/dns-query?name=google.com&type=A"
```

### Custom Exfiltration Script
The environment includes a Python client for custom exfiltration testing:
```bash
# Edit the exfiltration script
vim ./exfiltration/client.py

# Run custom exfiltration
docker exec -it client_test python3 /path/to/your/script.py
```

## 📊 Monitoring and Analysis

### Real-time Sniffer Logs
```bash
# View sniffer logs
docker logs sniffer_exfil --tail 50 --follow

# Check sniffer status
docker compose ps sniffer_exfil
```

### Network Interface Detection
The sniffer automatically detects the correct network interface:
- Identifies the resolver container's veth interface
- Captures DNS traffic in real-time  
- Filters for exfiltration patterns

## 🛡️ Security Features

### Certificate Management
- **Self-signed certificates** for local testing
- **Automatic certificate generation** via OpenSSL
- **TLS termination** handled by Traefik

### Traffic Isolation
- **Containerized environment** prevents host contamination
- **Network isolation** with custom Docker network
- **Privileged capabilities** only where necessary (NET_ADMIN, NET_RAW)

## 📁 Project Structure

```
├── docker-compose.yml          # Main orchestration file
├── generate_certs.sh          # Certificate generation script
├── certs/                     # Self-signed certificates
│   ├── doh.local.crt
│   ├── doh.local.key
│   └── tls.yml
├── sniffer/                   # Traffic capture and analysis
│   ├── Dockerfile
│   ├── decode_live.py         # Exfiltration detection script
│   ├── run_sniffer.sh         # Sniffer startup script
│   └── output/               # Detected exfiltration data
├── client_scripts/           # Test scripts for client container
│   ├── test_doh.sh
│   ├── test_exfiltration.sh
│   └── exfiltrate_doh.sh
├── exfiltration/            # Exfiltration client code
│   ├── client.py
│   └── secret.txt
└── resolver/               # DNS resolver configuration
    └── unbound.conf
```

## 🐛 Troubleshooting

### Common Issues

**Container Restart Loop**
```bash
# Check container logs
docker logs sniffer_exfil --tail 20

# Rebuild if needed
docker compose build sniffer_exfil
```

**DoH Queries Failing**
```bash
# Verify certificates
docker exec traefik ls -la /certs/

# Check DoH server logs  
docker logs doh_server --tail 20
```

**No Exfiltration Detection**
```bash
# Verify sniffer is running
docker compose ps sniffer_exfil

# Check output directory
ls -la ./sniffer/output/
```

## 🎯 Use Cases

### Research & Education
- **DNS over HTTPS analysis**
- **Exfiltration technique demonstration**  
- **Network security research**
- **Protocol behavior study**

### Security Testing
- **DoH-based data exfiltration detection**
- **Network monitoring validation**
- **IDS/IPS testing with DoH traffic**
- **Threat hunting practice**

### Development
- **DoH client/server development**
- **Custom detection algorithm testing**
- **Network forensics tool development**

## ⚠️ Important Notes

- **Self-signed certificates** will show browser security warnings
- **Use `-k` flag** with curl to ignore certificate errors
- **Fully offline environment** - no internet required once containers are built
- **Educational/research use only** - not for production environments


