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
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         ML Analyzer                     │
│  ┌─────────────────────────────────────┐ │
│  │ • Machine Learning models           │ │
│  │ • Feature preprocessing             │ │
│  │ • Real-time classification          │ │
│  │ • Model training & evaluation       │ │
│  │ • Performance metrics               │ │
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

#### 4. Data Storage and Analysis Layer
```
┌─────────────────────────────────────────┐
│           Dataset Management            │
│  ┌─────────────────────────────────────┐ │
│  │ • L2 benign dataset                 │ │
│  │ • L2 malicious dataset              │ │
│  │ • Training/testing splits           │ │
│  │ • Feature engineering               │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│        Model Training Pipeline          │
│  ┌─────────────────────────────────────┐ │
│  │ • Classifier training               │ │
│  │ • Model validation                  │ │
│  │ • Performance evaluation            │ │
│  │ • Model persistence                 │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🔗 Network Architecture

### Network Topology
```
┌─────────────────────────────────────────────────────────┐
│                    Docker Bridge Network                  │
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
│                                                         │
│  ┌─────────────┐  ┌─────────────────────────────────────┐ │
│  │ML Analyzer  │  │      Model Training                 │ │
│  │(inference)  │  │      (batch processing)             │ │
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
             ↓
         ML Reports
```

### 2. Machine Learning Pipeline
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Raw Data   │ →  │ Preprocess  │ →  │  Training   │
│             │    │             │    │             │
│ • DoH flows │    │ • Clean     │    │ • RF, GB    │
│ • DNS logs  │    │ • Engineer  │    │ • LR, SVM   │
│ • Features  │    │ • Normalize │    │ • Validation│
└─────────────┘    └─────────────┘    └─────────────┘
                                           │
┌─────────────┐    ┌─────────────┐    ┌───▼─────────┐
│  Deploy     │ ←  │  Evaluate   │ ←  │  Models     │
│             │    │             │    │             │
│ • Production│    │ • Metrics   │    │ • Saved     │
│ • Real-time │    │ • Reports   │    │ • Versioned │
│ • Inference │    │ • Compare   │    │ • Artifacts │
└─────────────┘    └─────────────┘    └─────────────┘
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

## 🔧 Component Details

### DoH Server Configuration
- **Base Image**: `satishweb/doh-server:latest`
- **Protocol**: DNS-over-HTTPS (RFC 8484)
- **Endpoint**: `/dns-query`
- **Format**: JSON and binary
- **Upstream**: Internal DNS resolver

### DNS Resolver Configuration
- **Software**: Unbound

### Detection Components
- **Dual Monitoring**: 
  - Traffic Analyzer monitors encrypted DoH traffic from Traefik
  - Exfil Interceptor monitors clear DNS queries from resolver
- **Pattern Detection**: Regex-based chunk identification
- **Traffic Analysis**: DoHLyzer integration for flow analysis  
- **ML Classification**: Multiple algorithms (RF, GB, LR, SVM)
- **Data Reconstruction**: Multi-format decoding and assembly from clear DNS

### Machine Learning Components
- **Dataset Management**: L2 benign/malicious datasets with preprocessing
- **Model Training**: Automated pipeline with cross-validation
- **Classification**: Real-time inference with ensemble methods
- **Evaluation**: Comprehensive metrics and performance reports
- **Model Persistence**: Versioned model artifacts and metadata

## 📈 Scalability Considerations

### Horizontal Scaling
- **Load Balancing**: Traefik can distribute across multiple DoH servers
- **Detection Scaling**: Multiple detection containers with shared storage

### Performance Optimization
- **Network Optimization**: Host networking for capture performance

### Monitoring and Logging
- **Container Logs**: Centralized logging via Docker
- **Metrics Collection**: Performance and detection metrics
- **Health Checks**: Service availability monitoring
- **ML Metrics**: Model performance and drift detection

## 🔒 Security Architecture

### Network Security
- **Isolation**: Separate networks for different components
- **TLS**: End-to-end encryption for DoH traffic
- **Firewall**: Host-based filtering and Docker network policies
- **Certificate Management**: Automated cert generation and rotation

### Container Security
- **Minimal Images**: Alpine-based where possible
- **Read-only Filesystems**: Where applicable
- **Resource Limits**: CPU and memory constraints
- **Capability Dropping**: Minimal required capabilities

### Data Security
- **Access Control**: Volume-based permissions
- **Data Retention**: Configurable cleanup policies

## 🎯 Design Principles

1. **Modularity**: Each component serves a specific purpose
2. **Scalability**: Easy to scale individual components
3. **Maintainability**: Clear separation of concerns
4. **Security**: Defense in depth approach
5. **Observability**: Comprehensive logging and monitoring
6. **Extensibility**: Plugin architecture for new detection methods
7. **Reproducibility**: Consistent environments and deterministic builds
8. **Performance**: Optimized for real-time processing and ML inference

## 📋 Project Structure Mapping

```
Kent-Dissertation/
├── certs/                  # TLS certificates and configuration
├── classifier/             # ML model training and evaluation
├── client_scripts/         # Testing and connectivity scripts
├── datasets/              # Training datasets (L2 benign/malicious)
├── docs/                  # Documentation (this file)
├── DoHLyzer/             # Traffic analysis integration
├── exfiltration/         # Exfiltration client and server
├── ml_analyzer/          # Real-time ML inference
├── ml_reports/           # Model performance reports
├── models/               # Trained model artifacts
├── resolver/             # DNS resolver configuration
├── traffic_analyzer/     # DoH traffic monitoring
├── docker-compose.yml    # Container orchestration
├── generate_certs.sh     # Certificate generation script
└── .env                  # Environment configuration
```

For detailed setup instructions, see [docs/development.md](docs/development.md).