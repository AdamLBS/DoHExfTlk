# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker and Docker Compose installed
- Linux/macOS environment (Windows with WSL2)
- At least 2GB RAM available

### Step 1: Clone and Setup
```bash
git clone <repository-url>
cd Kent-Dissertation
```

### Step 2: Generate Certificates
```bash
chmod +x generate_certs.sh
./generate_certs.sh
```

### Step 3: Start Environment
```bash
docker compose up -d
```

### Step 4: Verify Services
```bash
# Check all containers are running
docker compose ps

# Should show:
# - traefik (Up)
# - doh_server (Up, healthy)
# - resolver (Up, healthy) 
# - sniffer_exfil (Up)
# - client_test (Up)
```

### Step 5: Test DoH Server
```bash
docker exec -it client_test bash /scripts/test_doh.sh
```
Expected output: Successful DoH queries with JSON responses

### Step 6: Test Exfiltration Detection
```bash
docker exec -it client_test bash /scripts/test_exfiltration.sh
```

### Step 7: View Detected Data
```bash
# List detected exfiltration attempts
ls -la ./sniffer/output/

# View reconstructed secret data
cat ./sniffer/output/exfiltrated_data_*_chunks.txt
```

## ✅ Success Indicators

### DoH Server Working
- HTTP 200 responses from DoH queries
- Valid JSON DNS responses
- TLS certificate accepted (with -k flag)

### Exfiltration Detection Working
- Files created in `./sniffer/output/`
- Reconstructed data matches original secret
- Progressive chunk files (1, 2, 3... chunks)

## 🛠️ Quick Troubleshooting

### Containers Not Starting
```bash
# View logs
docker compose logs sniffer_exfil
docker compose logs doh_server

# Rebuild if needed
docker compose build
```

### DoH Queries Failing
```bash
# Check certificate generation
ls -la ./certs/

# Verify hosts file in container
docker exec client_test cat /etc/hosts
```

### No Exfiltration Detection
```bash
# Check sniffer logs
docker logs sniffer_exfil --tail 20

# Verify network interface detection
docker exec sniffer_exfil ip link show
```

## 📖 Next Steps

1. **Read Full Documentation**: `README.md`
2. **Study Detection System**: `EXFILTRATION_DETECTION.md`
3. **Customize Configuration**: Edit `docker-compose.yml`
4. **Create Custom Tests**: Modify scripts in `client_scripts/`
5. **Analyze Output**: Review files in `sniffer/output/`

## 🔧 Common Customizations

### Change Target Domain
Edit `sniffer/decode_live.py`:
```python
DOMAIN = "your-domain.local"
```

### Modify Chunk Size
Edit `exfiltration/client.py`:
```python
CHUNK_SIZE = 50  # Increase for larger chunks
```

### Add Custom Certificates
Replace files in `./certs/` directory and restart Traefik

## 📞 Support

- Check the troubleshooting section in `README.md`
- Review Docker logs: `docker compose logs [service_name]`
- Verify network connectivity between containers
- Ensure proper file permissions on scripts
