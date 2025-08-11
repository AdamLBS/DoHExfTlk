# Technical Architecture

## 🏗️ System Overview

The DoH Exfiltration Detection Platform is built on a microservices architecture using Docker containers, designed for modularity, scalability, and ease of deployment.

## 📐 Infrastructure Components

### Core Services

#### 1. DoH Infrastructure Layer
```
┌─────────────────────────────────────────┐
│             Traefik Proxy               │
│    ┌─────────────┬─────────────────────┐ │
│    │ Port 80/443 │ TLS Termination     │ │
│    │             │ Load Balancing      │ │
│    └─────────────┴─────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│            DoH Server                   │
│  ┌─────────────────────────────────────┐ │
│  │ satishweb/doh-server:latest         │ │
│  │ • Listens on port 8053              │ │
│  │ • Endpoint: /dns-query              │ │
│  │ • Upstream: DNS Resolver            │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           DNS Resolver                  │
│  ┌─────────────────────────────────────┐ │
│  │ Unbound DNS Resolver                │ │
│  │ • Port 53 (internal)                │ │
│  │ • Custom configuration              │ │
│  │ • Upstream DNS servers              │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 2. Detection and Analysis Layer
```
┌─────────────────────────────────────────┐
│        Exfiltration Interceptor         │
│  ┌─────────────────────────────────────┐ │
│  │ • Network mode: host                │ │
│  │ • Capabilities: NET_RAW, NET_ADMIN  │ │
│  │ • Monitors DNS Resolver traffic     │ │
│  │ • Captures clear DNS queries        │ │
│  │ • Real-time data extraction         │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Traffic Analyzer               │
│  ┌─────────────────────────────────────┐ │
│  │ • DoHLyzer integration              │ │
│  │ • Monitors Traefik DoH traffic      │ │
│  │ • Flow-based analysis               │ │
│  │ • Feature extraction               │ │
│  │ • CSV output generation             │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### 3. Client and Testing Layer
```
┌─────────────────────────────────────────┐
│           Exfiltration Client           │
│  ┌─────────────────────────────────────┐ │
│  │ • Local network requests            │ │
│  │ • DoH queries via Traefik           │ │
│  │ • Multiple encoding methods         │ │
│  │ • Configurable patterns             │ │
│  │ • Evasion capabilities              │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Test Client                   │
│  ┌─────────────────────────────────────┐ │
│  │ • Ubuntu 22.04 base                │ │
│  │ • Network tools (curl, dig, etc.)  │ │
│  │ • Test scripts collection           │ │
│  │ • DoH connectivity verification     │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```
│           Test Client                   │
│  ┌─────────────────────────────────────┐ │
│  │ • Ubuntu 22.04 base                │ │
│  │ • Network tools (curl, dig, etc.)  │ │
│  │ • Test scripts collection           │ │
│  │ • Connectivity verification         │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🔗 Network Architecture

### Network Topology
```
┌─────────────────────────────────────────────────────────┐
│                    Host Network                         │
│  ┌─────────────────┐  ┌─────────────────────────────────┐ │
│  │ Exfil Intercept │  │      Traffic Analyzer          │ │
│  │ (monitors       │  │      (monitors Traefik         │ │
│  │  DNS resolver)  │  │       DoH traffic)             │ │
│  └─────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────┐
│                  Docker Bridge Network                  │
│                      (dohnet)                           │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   Traefik   │  │ DoH Server  │  │   DNS Resolver  │   │
│  │   (proxy)   │  │ (doh-proxy) │  │   (unbound)     │   │
│  └─────────────┘  └─────────────┘  └─────────────────┘   │
│                                                         │
│  ┌─────────────┐  ┌─────────────────────────────────────┐ │
│  │Client Test  │  │      Exfiltration Client            │ │
│  │(local net)  │  │      (DoH requests)                 │ │
│  └─────────────┘  └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Port Mapping
| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Traefik | 80, 443, 8080 | 80, 443, 8080 | HTTP/HTTPS |
| DoH Server | 8053 | - | HTTP |
| DNS Resolver | 53 | - | UDP/TCP |
| ML Services | - | - | Internal only |

## 📊 Data Flow Architecture

### 1. DoH Query Processing and Monitoring
```
Client → Traefik → DoH Server → DNS Resolver
  ↓        ↓                       ↓
  ↓    Traffic Analyzer      Exfil Interceptor
  ↓    (DoHLyzer)           (Clear DNS Monitoring)
  ↓        ↓                       ↓
  ↓    Flow Analysis         Pattern Detection
  ↓    Feature Extract.      Data Reconstruction
  ↓        ↓                       ↓
  └────→ ML Classification ←───────┘
```

### 2. Dual Monitoring Architecture
```
                    ┌─ DoH Traffic (Encrypted) ─┐
                    │                           │
┌─────────────┐    ┌▼──────────────┐           ┌▼─────────────┐
│   Client    │ →  │   Traefik     │ ────────→ │ DoH Server   │
│             │    │   Proxy       │           │              │
│ • Local net │    │               │           │              │
│ • DoH reqs  │    └───────────────┘           └──────┬───────┘
└─────────────┘            │                           │
                           │                           │
                    ┌──────▼──────────┐               ┌▼─────────────┐
                    │ Traffic Analyzer│               │ DNS Resolver │
                    │   (DoHLyzer)    │               │              │
                    │                 │               │              │
                    │ • Listen Traefik│               └──────┬───────┘
                    │ • Flow analysis │                      │
                    │ • Encrypted     │               ┌──────▼──────────┐
                    │   traffic       │               │ Exfil Intercept │
                    └─────────────────┘               │                 │
                                                      │ • Listen Resolv │
                                                      │ • Clear queries │
                                                      │ • Data extract  │
                                                      └─────────────────┘
```

### 3. Exfiltration Detection Pipeline
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Capture   │ →  │   Parse     │ →  │   Detect    │
│             │    │             │    │             │
│ • DoH Flow  │    │ • Domain    │    │ • Patterns  │
│ • Clear DNS │    │ • Subdom.   │    │ • Encoding  │
│ • Metadata  │    │ • Timing    │    │ • Chunks    │
└─────────────┘    └─────────────┘    └─────────────┘
                                           │
┌─────────────┐    ┌─────────────┐    ┌───▼─────────┐
│   Store     │ ←  │ Reconstruct │ ←  │  Classify   │
│             │    │             │    │             │
│ • Files     │    │ • Assemble  │    │ • ML Models │
│ • Metadata  │    │ • Decode    │    │ • Rules     │
│ • Reports   │    │ • Verify    │    │ • Scores    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🐳 Docker Configuration Details

### Volume Mounts
```yaml
# Certificate management
./certs:/certs:ro

# Data persistence
./exfiltration/server/captured:/app/captured
./traffic_analyzer/output:/app/output
./models:/models

# Configuration
./resolver/unbound.conf:/etc/unbound/unbound.conf:ro
./client_scripts:/scripts:ro

# Runtime
/var/run/docker.sock:/var/run/docker.sock:ro
```

### Environment Variables
```yaml
# DoH Configuration
UPSTREAM_DNS_SERVER: "udp:resolver:53"
DOH_HTTP_PREFIX: "/dns-query"
DOH_SERVER_LISTEN: ":8053"

# Detection Configuration
OUTPUT_DIR: "/app/captured"
DOH_DOMAINS: "doh.local,exfill.local"
RESOLVER_MONITOR: "port 53"
TRAEFIK_MONITOR: "port 443 and host traefik"

# Client Configuration
DOH_SERVER: "https://doh.local/dns-query"
TARGET_DOMAIN: "exfill.local"
LOCAL_NETWORK: "true"
```

### Security Configuration
```yaml
# Network isolation
networks:
  - dohnet

# Capabilities for packet capture
cap_add:
  - NET_RAW
  - NET_ADMIN

# Read-only mounts where possible
volumes:
  - ./certs:/certs:ro
  - ./scripts:/scripts:ro
```

## 🔧 Component Details

### Traefik Configuration
```yaml
# Automatic service discovery
providers:
  docker: true
  file:
    directory: /certs
    watch: true

# TLS termination
entrypoints:
  web: ":80"
  websecure: ":443"

# SSL certificate handling
tls:
  certificates:
    - certFile: /certs/doh.local.crt
    - keyFile: /certs/doh.local.key
```

### DoH Server Configuration
- **Base Image**: `satishweb/doh-server:latest`
- **Protocol**: DNS-over-HTTPS (RFC 8484)
- **Endpoint**: `/dns-query`
- **Format**: JSON and binary
- **Upstream**: Internal DNS resolver

### DNS Resolver Configuration
- **Software**: Unbound
- **Features**: 
  - DNSSEC validation
  - Custom forwarding rules
  - Query logging
  - Cache management

### Detection Components
- **Dual Monitoring**: 
  - Traffic Analyzer monitors encrypted DoH traffic from Traefik
  - Exfil Interceptor monitors clear DNS queries from resolver
- **Pattern Detection**: Regex-based chunk identification
- **Traffic Analysis**: DoHLyzer integration for flow analysis  
- **ML Classification**: Multiple algorithms (RF, GB, LR, SVM)
- **Data Reconstruction**: Multi-format decoding and assembly from clear DNS

## 📈 Scalability Considerations

### Horizontal Scaling
- **Load Balancing**: Traefik can distribute across multiple DoH servers
- **Detection Scaling**: Multiple detection containers with shared storage
- **ML Processing**: Separate training and inference containers

### Performance Optimization
- **Resource Limits**: Configured per container
- **Memory Management**: Efficient chunk storage and cleanup
- **Network Optimization**: Host networking for capture performance

### Monitoring and Logging
- **Container Logs**: Centralized logging via Docker
- **Metrics Collection**: Performance and detection metrics
- **Health Checks**: Service availability monitoring

## 🔒 Security Architecture

### Network Security
- **Isolation**: Separate networks for different components
- **TLS**: End-to-end encryption for DoH traffic
- **Firewall**: Host-based filtering and Docker network policies

### Container Security
- **Minimal Images**: Alpine-based where possible
- **Non-root Users**: Limited privileges
- **Read-only Filesystems**: Where applicable
- **Resource Limits**: CPU and memory constraints

### Data Security
- **Encryption**: TLS in transit, optional at rest
- **Access Control**: Volume-based permissions
- **Audit Logging**: Complete operation trails
- **Data Retention**: Configurable cleanup policies

## 🎯 Design Principles

1. **Modularity**: Each component serves a specific purpose
2. **Scalability**: Easy to scale individual components
3. **Maintainability**: Clear separation of concerns
4. **Security**: Defense in depth approach
5. **Observability**: Comprehensive logging and monitoring
6. **Extensibility**: Plugin architecture for new detection methods
