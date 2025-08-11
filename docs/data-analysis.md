# Data Analysis Guide

## 📊 Overview

This guide covers the comprehensive data analysis capabilities of the DoH Exfiltration Detection Platform, including traffic analysis, pattern detection, and forensic reconstruction.

## 🔍 Data Collection and Sources

### Traffic Capture Methods

#### 1. Network Packet Capture
```python
# Real-time packet capture with custom filters
CAPTURE_FILTER = "port 53 or port 443 or port 8080"

# Interface detection for Docker environments
def detect_network_interface():
    """Auto-detect the correct network interface"""
    iflink = subprocess.check_output([
        "docker", "exec", "resolver", 
        "cat", "/sys/class/net/eth0/iflink"
    ]).decode().strip()
    
    iface = subprocess.check_output([
        "ip", "link", "|", "grep", "-B1", f"^ *{iflink}:", 
        "|", "head", "-n", "1", "|", "awk", "'{print $2}'"
    ], shell=True).decode().strip()
    
    return iface.rstrip(':')
```

#### 2. DoH Query Interception
```python
def intercept_doh_queries(interface="eth0"):
    """Capture and parse DoH queries"""
    def packet_handler(packet):
        if packet.haslayer(DNS):
            query_name = packet[DNS].qd.qname.decode()
            timestamp = packet.time
            
            # Extract metadata
            query_data = {
                'timestamp': timestamp,
                'query_name': query_name,
                'query_type': packet[DNS].qd.qtype,
                'source_ip': packet[IP].src,
                'dest_ip': packet[IP].dst,
                'packet_size': len(packet)
            }
            
            process_query(query_data)
    
    sniff(iface=interface, filter=CAPTURE_FILTER, prn=packet_handler)
```

### Data Storage Architecture

#### Flow-based Storage
```csv
Timestamp,SourceIP,DestIP,SourcePort,DestPort,Protocol,Duration,
BytesSent,BytesReceived,PacketCount,QueryName,QueryType,ResponseCode
2025-08-11 10:30:15,192.168.1.100,1.1.1.1,54321,443,HTTPS,1.234,
1024,2048,12,example.com,A,NOERROR
```

#### Exfiltration Event Storage
```json
{
  "session_id": "1722855015_abc123",
  "timestamp": "2025-08-11T10:30:15Z",
  "detection_method": "pattern_matching",
  "chunks_detected": 15,
  "chunks_total": 15,
  "reconstruction_status": "complete",
  "file_info": {
    "size_bytes": 2048,
    "type": "text/plain",
    "encoding": "utf-8",
    "md5_hash": "5d41402abc4b2a76b9719d911017c592"
  },
  "exfiltration_metadata": {
    "target_domain": "exfill.local",
    "chunk_size": 25,
    "encoding_method": "base64",
    "timing_pattern": "regular"
  }
}
```

## 🔬 Pattern Analysis

### DNS Query Pattern Detection

#### 1. Subdomain Structure Analysis
```python
def analyze_subdomain_patterns(query_name):
    """Analyze subdomain for exfiltration patterns"""
    
    # Pattern: session_id-index-total-data.random.domain
    pattern = re.compile(r"(\d+)-(\d+)-(\d+)-([a-zA-Z0-9_\-=]+)\.([a-z0-9]+)\.(.+)")
    
    match = pattern.match(query_name)
    if match:
        session_id, index, total, data_chunk, random_part, domain = match.groups()
        
        return {
            'pattern_type': 'structured_exfiltration',
            'session_id': session_id,
            'chunk_index': int(index),
            'total_chunks': int(total),
            'data_chunk': data_chunk,
            'randomization': random_part,
            'target_domain': domain,
            'confidence': 0.95
        }
    
    # Pattern: base64-like data in subdomain
    base64_pattern = re.compile(r"^[A-Za-z0-9+/=]{20,}$")
    subdomain = query_name.split('.')[0]
    
    if base64_pattern.match(subdomain) and len(subdomain) > 20:
        return {
            'pattern_type': 'base64_exfiltration',
            'data_chunk': subdomain,
            'confidence': 0.75
        }
    
    return None
```

#### 2. Timing Pattern Analysis
```python
def analyze_timing_patterns(query_times):
    """Analyze query timing for suspicious patterns"""
    
    if len(query_times) < 3:
        return None
    
    # Calculate inter-query intervals
    intervals = np.diff(sorted(query_times))
    
    # Statistical analysis
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    cv = std_interval / mean_interval if mean_interval > 0 else 0
    
    # Pattern classification
    if cv < 0.1:  # Very regular
        pattern = 'automated_regular'
        suspicion = 0.8
    elif cv < 0.3:  # Somewhat regular
        pattern = 'semi_automated'
        suspicion = 0.6
    elif cv > 0.8:  # Very irregular
        pattern = 'random_timing'
        suspicion = 0.3
    else:
        pattern = 'human_like'
        suspicion = 0.2
    
    return {
        'timing_pattern': pattern,
        'mean_interval': mean_interval,
        'coefficient_variation': cv,
        'suspicion_score': suspicion,
        'sample_size': len(intervals)
    }
```

### Statistical Analysis

#### Query Frequency Analysis
```python
def analyze_query_frequency(queries_per_domain):
    """Analyze query frequency patterns"""
    
    frequency_stats = {}
    
    for domain, query_count in queries_per_domain.items():
        # Z-score analysis for outlier detection
        domain_stats = {
            'query_count': query_count,
            'queries_per_hour': query_count / 24,  # Assuming 24h window
            'suspicion_factors': []
        }
        
        # High frequency indicators
        if query_count > 1000:
            domain_stats['suspicion_factors'].append('high_frequency')
        
        # Subdomain complexity analysis
        subdomains = [q.split('.')[0] for q in queries if domain in q]
        avg_subdomain_length = np.mean([len(s) for s in subdomains])
        
        if avg_subdomain_length > 30:
            domain_stats['suspicion_factors'].append('long_subdomains')
        
        # Entropy analysis
        subdomain_entropy = calculate_entropy(''.join(subdomains))
        if subdomain_entropy > 4.0:
            domain_stats['suspicion_factors'].append('high_entropy')
        
        domain_stats['subdomain_entropy'] = subdomain_entropy
        frequency_stats[domain] = domain_stats
    
    return frequency_stats

def calculate_entropy(data):
    """Calculate Shannon entropy of data"""
    if not data:
        return 0
    
    # Count character frequencies
    char_counts = {}
    for char in data:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calculate entropy
    entropy = 0
    total_chars = len(data)
    
    for count in char_counts.values():
        probability = count / total_chars
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy
```

## 🧩 Data Reconstruction

### Chunk Assembly Process

#### 1. Chunk Collection and Validation
```python
class ChunkAssembler:
    """Handles collection and assembly of data chunks"""
    
    def __init__(self):
        self.sessions = {}
        self.session_lock = threading.Lock()
    
    def add_chunk(self, session_id, chunk_index, total_chunks, data_chunk):
        """Add a chunk to the assembly process"""
        
        with self.session_lock:
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'chunks': {},
                    'total_expected': total_chunks,
                    'start_time': time.time(),
                    'last_activity': time.time()
                }
            
            session = self.sessions[session_id]
            
            # Validate chunk
            if self._validate_chunk(data_chunk):
                session['chunks'][chunk_index] = data_chunk
                session['last_activity'] = time.time()
                
                # Check if complete
                if len(session['chunks']) >= session['total_expected']:
                    return self._assemble_session(session_id)
        
        return None
    
    def _validate_chunk(self, chunk):
        """Validate chunk format and content"""
        # Check base64 format
        try:
            base64.urlsafe_b64decode(chunk + '==')
            return True
        except:
            try:
                base64.b64decode(chunk + '==')
                return True
            except:
                return False
    
    def _assemble_session(self, session_id):
        """Assemble complete session data"""
        session = self.sessions[session_id]
        chunks = session['chunks']
        total_chunks = session['total_expected']
        
        # Order chunks
        ordered_data = []
        for i in range(total_chunks):
            if i not in chunks:
                return None  # Missing chunk
            ordered_data.append(chunks[i])
        
        # Decode assembled data
        combined_data = ''.join(ordered_data)
        decoded_data = self._decode_data(combined_data)
        
        if decoded_data:
            # Analyze reconstructed data
            file_info = self._analyze_reconstructed_data(decoded_data)
            
            # Save to file
            output_path = self._save_reconstructed_data(
                session_id, decoded_data, file_info
            )
            
            # Cleanup session
            del self.sessions[session_id]
            
            return {
                'session_id': session_id,
                'file_path': output_path,
                'file_info': file_info,
                'chunks_count': total_chunks
            }
        
        return None
```

#### 2. Multi-format Decoding
```python
def decode_data(encoded_data):
    """Attempt multiple decoding methods"""
    
    decoders = [
        ('base64_urlsafe', lambda x: base64.urlsafe_b64decode(x + '==')),
        ('base64_standard', lambda x: base64.b64decode(x + '==')),
        ('base32', lambda x: base64.b32decode(x + '========')),
        ('hex', lambda x: bytes.fromhex(x)),
        ('ascii85', lambda x: base64.a85decode(x))
    ]
    
    for method_name, decoder in decoders:
        try:
            decoded = decoder(encoded_data)
            
            # Validate decoded data
            if _is_valid_decoded_data(decoded):
                return {
                    'data': decoded,
                    'method': method_name,
                    'success': True
                }
        except Exception as e:
            continue
    
    return {
        'data': encoded_data.encode('utf-8', errors='ignore'),
        'method': 'raw',
        'success': False
    }

def _is_valid_decoded_data(data):
    """Validate that decoded data is reasonable"""
    if not data:
        return False
    
    # Check for common file signatures
    file_signatures = [
        b'\x89PNG',        # PNG
        b'\xFF\xD8\xFF',   # JPEG
        b'GIF8',           # GIF
        b'%PDF',           # PDF
        b'PK\x03\x04',     # ZIP
        b'\x1F\x8B',       # GZIP
    ]
    
    for sig in file_signatures:
        if data.startswith(sig):
            return True
    
    # Check if mostly printable text
    try:
        text = data.decode('utf-8')
        printable_ratio = sum(c.isprintable() or c.isspace() for c in text) / len(text)
        return printable_ratio > 0.7
    except:
        pass
    
    # Check entropy (not too random, not too structured)
    entropy = calculate_entropy(data)
    return 1.0 < entropy < 7.0
```

### File Type Analysis

#### Automatic File Type Detection
```python
def analyze_file_type(data):
    """Comprehensive file type analysis"""
    
    analysis = {
        'size': len(data),
        'type': 'unknown',
        'encoding': 'binary',
        'confidence': 0.0,
        'metadata': {}
    }
    
    # Magic number detection
    magic_signatures = {
        b'\x89PNG\r\n\x1a\n': {'type': 'PNG Image', 'ext': '.png', 'confidence': 1.0},
        b'\xFF\xD8\xFF': {'type': 'JPEG Image', 'ext': '.jpg', 'confidence': 1.0},
        b'GIF8': {'type': 'GIF Image', 'ext': '.gif', 'confidence': 1.0},
        b'%PDF': {'type': 'PDF Document', 'ext': '.pdf', 'confidence': 1.0},
        b'PK\x03\x04': {'type': 'ZIP Archive', 'ext': '.zip', 'confidence': 0.9},
        b'\x1F\x8B\x08': {'type': 'GZIP Archive', 'ext': '.gz', 'confidence': 1.0},
        b'RIFF': {'type': 'RIFF Container', 'ext': '.wav/.avi', 'confidence': 0.8},
        b'\x00\x00\x01\x00': {'type': 'Windows Icon', 'ext': '.ico', 'confidence': 0.9},
    }
    
    for signature, info in magic_signatures.items():
        if data.startswith(signature):
            analysis.update(info)
            return analysis
    
    # Text analysis
    text_analysis = analyze_text_content(data)
    if text_analysis['is_text']:
        analysis.update(text_analysis)
        return analysis
    
    # Binary analysis
    analysis.update({
        'type': 'Binary Data',
        'encoding': 'binary',
        'confidence': 0.5,
        'entropy': calculate_entropy(data)
    })
    
    return analysis

def analyze_text_content(data):
    """Analyze if data is text and determine type"""
    
    encodings = ['utf-8', 'ascii', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            text = data.decode(encoding)
            
            # Calculate printable ratio
            printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
            printable_ratio = printable_chars / len(text)
            
            if printable_ratio > 0.85:
                # Determine text type
                text_type = determine_text_type(text)
                
                return {
                    'is_text': True,
                    'type': text_type['type'],
                    'encoding': encoding,
                    'confidence': text_type['confidence'],
                    'ext': text_type['ext'],
                    'metadata': {
                        'line_count': len(text.split('\n')),
                        'word_count': len(text.split()),
                        'char_count': len(text),
                        'printable_ratio': printable_ratio
                    }
                }
        except UnicodeDecodeError:
            continue
    
    return {'is_text': False}

def determine_text_type(text):
    """Determine specific text file type"""
    
    lower_text = text.lower()
    
    # Programming languages
    if any(keyword in lower_text for keyword in ['def ', 'import ', 'class ', 'print(']):
        return {'type': 'Python Code', 'ext': '.py', 'confidence': 0.9}
    
    if any(keyword in lower_text for keyword in ['function', 'var ', 'const ', 'let ']):
        return {'type': 'JavaScript Code', 'ext': '.js', 'confidence': 0.9}
    
    # Markup languages
    if any(tag in lower_text for tag in ['<html', '<!doctype', '<head>', '<body>']):
        return {'type': 'HTML Document', 'ext': '.html', 'confidence': 0.95}
    
    if text.strip().startswith('{') and text.strip().endswith('}'):
        try:
            json.loads(text)
            return {'type': 'JSON Data', 'ext': '.json', 'confidence': 0.95}
        except:
            pass
    
    # Configuration files
    if any(pattern in lower_text for pattern in ['[section]', 'key=value', '# comment']):
        return {'type': 'Configuration File', 'ext': '.conf', 'confidence': 0.8}
    
    # Default text
    return {'type': 'Plain Text', 'ext': '.txt', 'confidence': 0.7}
```

## 📈 Flow Analysis with DoHLyzer

### Feature Extraction Pipeline

#### Network Flow Features
```python
def extract_flow_features(packets):
    """Extract comprehensive flow features"""
    
    if not packets:
        return None
    
    # Basic flow information
    flow_start = min(p.timestamp for p in packets)
    flow_end = max(p.timestamp for p in packets)
    duration = flow_end - flow_start
    
    # Packet sizes
    packet_sizes = [len(p.payload) for p in packets if hasattr(p, 'payload')]
    
    # Inter-packet times
    timestamps = sorted([p.timestamp for p in packets])
    inter_packet_times = np.diff(timestamps)
    
    # Directional features
    sent_packets = [p for p in packets if p.direction == 'outbound']
    received_packets = [p for p in packets if p.direction == 'inbound']
    
    features = {
        # Basic flow features
        'Duration': duration,
        'TotalPackets': len(packets),
        'FlowBytesSent': sum(len(p.payload) for p in sent_packets),
        'FlowBytesReceived': sum(len(p.payload) for p in received_packets),
        
        # Packet size statistics
        'PacketLengthMean': np.mean(packet_sizes) if packet_sizes else 0,
        'PacketLengthStd': np.std(packet_sizes) if packet_sizes else 0,
        'PacketLengthVariance': np.var(packet_sizes) if packet_sizes else 0,
        'PacketLengthMin': min(packet_sizes) if packet_sizes else 0,
        'PacketLengthMax': max(packet_sizes) if packet_sizes else 0,
        
        # Timing statistics
        'PacketTimeMean': np.mean(inter_packet_times) if len(inter_packet_times) > 0 else 0,
        'PacketTimeStd': np.std(inter_packet_times) if len(inter_packet_times) > 0 else 0,
        'PacketTimeVariance': np.var(inter_packet_times) if len(inter_packet_times) > 0 else 0,
        
        # Advanced features
        'FlowSentRate': len(sent_packets) / duration if duration > 0 else 0,
        'FlowReceivedRate': len(received_packets) / duration if duration > 0 else 0,
        'AvgPacketSize': np.mean(packet_sizes) if packet_sizes else 0,
        'PacketSizeRatio': (len(sent_packets) / len(received_packets)) if received_packets else 0
    }
    
    return features
```

#### DoH-Specific Features
```python
def extract_doh_features(doh_queries):
    """Extract DoH-specific features"""
    
    features = {}
    
    # Query characteristics
    query_names = [q.query_name for q in doh_queries]
    subdomain_lengths = [len(q.split('.')[0]) for q in query_names]
    
    features.update({
        'AvgSubdomainLength': np.mean(subdomain_lengths),
        'MaxSubdomainLength': max(subdomain_lengths) if subdomain_lengths else 0,
        'SubdomainLengthVariance': np.var(subdomain_lengths),
        'UniqueSubdomains': len(set(q.split('.')[0] for q in query_names)),
        'QueryCount': len(doh_queries)
    })
    
    # Entropy analysis
    all_subdomains = ''.join(q.split('.')[0] for q in query_names)
    features['SubdomainEntropy'] = calculate_entropy(all_subdomains)
    
    # Character analysis
    subdomain_chars = ''.join(q.split('.')[0] for q in query_names)
    features.update({
        'AlphaRatio': sum(c.isalpha() for c in subdomain_chars) / len(subdomain_chars) if subdomain_chars else 0,
        'DigitRatio': sum(c.isdigit() for c in subdomain_chars) / len(subdomain_chars) if subdomain_chars else 0,
        'SpecialCharRatio': sum(not c.isalnum() for c in subdomain_chars) / len(subdomain_chars) if subdomain_chars else 0
    })
    
    # Pattern detection
    base64_pattern = re.compile(r'^[A-Za-z0-9+/=]+$')
    base64_count = sum(1 for q in query_names if base64_pattern.match(q.split('.')[0]))
    features['Base64LikeRatio'] = base64_count / len(query_names) if query_names else 0
    
    return features
```

### Anomaly Detection

#### Statistical Anomaly Detection
```python
def detect_statistical_anomalies(flow_features, baseline_stats):
    """Detect statistical anomalies in flow features"""
    
    anomalies = {}
    
    for feature, value in flow_features.items():
        if feature in baseline_stats:
            baseline_mean = baseline_stats[feature]['mean']
            baseline_std = baseline_stats[feature]['std']
            
            # Z-score calculation
            if baseline_std > 0:
                z_score = abs(value - baseline_mean) / baseline_std
                
                anomalies[feature] = {
                    'value': value,
                    'z_score': z_score,
                    'is_anomaly': z_score > 3.0,  # 3-sigma rule
                    'severity': 'high' if z_score > 4 else 'medium' if z_score > 2 else 'low'
                }
    
    return anomalies
```

#### Time Series Analysis
```python
def analyze_temporal_patterns(timestamps, values):
    """Analyze temporal patterns in data"""
    
    if len(timestamps) < 10:
        return None
    
    # Convert to time series
    ts = pd.Series(values, index=pd.to_datetime(timestamps))
    
    # Detect periodicity
    from scipy.fft import fft, fftfreq
    
    # FFT for frequency analysis
    fft_values = fft(values)
    frequencies = fftfreq(len(values))
    
    # Find dominant frequencies
    power_spectrum = np.abs(fft_values) ** 2
    dominant_freq_idx = np.argmax(power_spectrum[1:len(power_spectrum)//2]) + 1
    dominant_frequency = frequencies[dominant_freq_idx]
    
    # Trend analysis
    from scipy.stats import linregress
    x = np.arange(len(values))
    slope, intercept, r_value, p_value, std_err = linregress(x, values)
    
    return {
        'dominant_frequency': dominant_frequency,
        'trend_slope': slope,
        'trend_r_squared': r_value ** 2,
        'trend_significance': p_value,
        'is_periodic': power_spectrum[dominant_freq_idx] > np.mean(power_spectrum) * 5,
        'has_trend': abs(slope) > std_err * 2 and p_value < 0.05
    }
```

## 📊 Visualization and Reporting

### Real-time Dashboards
```python
def generate_detection_dashboard():
    """Generate real-time detection dashboard"""
    
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=['Detection Events', 'Query Volume', 'Anomaly Scores', 'Top Domains'],
        specs=[[{'type': 'scatter'}, {'type': 'bar'}],
               [{'type': 'heatmap'}, {'type': 'pie'}]]
    )
    
    # Detection events over time
    detection_data = get_recent_detections()
    fig.add_trace(
        go.Scatter(
            x=detection_data['timestamp'],
            y=detection_data['count'],
            mode='lines+markers',
            name='Detections'
        ),
        row=1, col=1
    )
    
    # Query volume by hour
    volume_data = get_query_volume_hourly()
    fig.add_trace(
        go.Bar(
            x=volume_data['hour'],
            y=volume_data['count'],
            name='Query Volume'
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_layout(
        title='DoH Exfiltration Detection Dashboard',
        showlegend=True,
        height=600
    )
    
    return fig
```

### Forensic Reports
```python
def generate_forensic_report(session_data):
    """Generate comprehensive forensic report"""
    
    report = {
        'summary': {
            'session_id': session_data['session_id'],
            'detection_time': session_data['timestamp'],
            'total_data_bytes': session_data['file_info']['size_bytes'],
            'chunks_count': session_data['chunks_detected'],
            'reconstruction_success': session_data['reconstruction_status'] == 'complete'
        },
        
        'technical_details': {
            'exfiltration_method': analyze_exfiltration_method(session_data),
            'encoding_analysis': analyze_encoding_method(session_data),
            'timing_analysis': analyze_timing_patterns(session_data['query_times']),
            'domain_analysis': analyze_target_domains(session_data['domains'])
        },
        
        'file_analysis': {
            'file_type': session_data['file_info']['type'],
            'file_hash': session_data['file_info']['md5_hash'],
            'content_preview': generate_content_preview(session_data['reconstructed_data']),
            'metadata': session_data['file_info']['metadata']
        },
        
        'indicators': {
            'iocs': extract_indicators_of_compromise(session_data),
            'network_signatures': generate_network_signatures(session_data),
            'behavioral_patterns': identify_behavioral_patterns(session_data)
        },
        
        'recommendations': generate_security_recommendations(session_data)
    }
    
    return report
```

## 🎯 Advanced Analytics

### Machine Learning Integration
```python
def integrate_ml_analysis(flow_data):
    """Integrate machine learning analysis with traffic data"""
    
    # Load trained models
    models = load_trained_models()
    
    # Extract features
    features = extract_comprehensive_features(flow_data)
    
    # Predict with ensemble
    predictions = {}
    for model_name, model in models.items():
        pred_proba = model.predict_proba([features])[0]
        predictions[model_name] = {
            'malicious_probability': pred_proba[1],
            'benign_probability': pred_proba[0],
            'prediction': 'malicious' if pred_proba[1] > 0.5 else 'benign'
        }
    
    # Ensemble prediction
    avg_malicious_prob = np.mean([p['malicious_probability'] for p in predictions.values()])
    
    return {
        'individual_predictions': predictions,
        'ensemble_probability': avg_malicious_prob,
        'final_prediction': 'malicious' if avg_malicious_prob > 0.5 else 'benign',
        'confidence': max(avg_malicious_prob, 1 - avg_malicious_prob)
    }
```

### Threat Intelligence Integration
```python
def enrich_with_threat_intelligence(detection_data):
    """Enrich detections with threat intelligence"""
    
    enriched_data = detection_data.copy()
    
    # Domain reputation check
    domains = extract_domains(detection_data)
    for domain in domains:
        reputation = check_domain_reputation(domain)
        enriched_data['domain_reputation'][domain] = reputation
    
    # IP reputation check
    ips = extract_ips(detection_data)
    for ip in ips:
        reputation = check_ip_reputation(ip)
        enriched_data['ip_reputation'][ip] = reputation
    
    # Pattern matching against known attacks
    attack_patterns = match_known_attack_patterns(detection_data)
    enriched_data['known_patterns'] = attack_patterns
    
    return enriched_data
```

This comprehensive data analysis framework provides deep insights into DoH exfiltration attempts, enabling both real-time detection and thorough forensic analysis of security incidents.
