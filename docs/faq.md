# DoHExfTlk — Frequently Asked Questions (FAQ)

> **Legal note:** This toolkit is for academic research, cybersecurity training, and authorized testing in controlled environments only. Use it only on systems you own or have explicit permission to test.

---

## General

### 1) What is DoHExfTlk?
DoHExfTlk is a research-oriented toolkit to **study and detect data exfiltration over DNS-over-HTTPS (DoH)**. It bundles a DoH stack (Traefik TLS proxy, DoH server, DNS resolver), traffic analysis (pcap/flows), a rule-based layer, and **ML models** for classification.

### 2) What is it *not*?
It is **not** a production network security product. It is a **lab framework** for research, training, and experiments.

### 3) What are the main components?
- **Traefik** — TLS termination and routing (ingress)
- **DoH Server** — Handles `/dns-query` and forwards to resolver
- **DNS Resolver** — Upstream resolver (e.g., Unbound)
- **Traffic Analyzer** — Listens on Traefik side (HTTPS/HTTP visibility)
- **Exfil Interceptor** — Listens on Resolver side (raw DNS visibility)
- **DoHLyzer** — Behavioral analysis on flows
- **ML Analyzer** — Model training (`trainer.py`) & prediction (`predict.py`)
- **Exfiltration Client** — Generates DoH exfiltration traffic based on JSON configs

---

## Setup & Requirements

### 4) What are the prerequisites?
- **Docker & Docker Compose**
- Linux/macOS (Windows via **WSL2** recommended)
- ~4 GB RAM minimum

### 5) How do I start the platform?
```bash
# 1. Clone repository
git clone git@github.com:AdamLBS/DohExfTlk.git
cd DoHExfTlk

# 2. Download the dataset's CSVs used for the model training (l1-benign.csv & l2-malicious.csv)
wget http://cicresearch.ca/CICDataset/DoHBrw-2020/Dataset/CSVs/Total_CSVs.zip
unzip Total_CSVs.zip
mkdir -p datasets
cp l2-benign.csv l2-malicious.csv datasets/

# 2. Generate TLS certificates
chmod +x generate_certs.sh
./generate_certs.sh

# 3. Start infrastructure
docker compose up -d
```

### 6) How do I verify the DoH server is responding?
```bash
docker compose ps
docker exec -it client_test bash /scripts/test_doh.sh
```
Alternatively, from any client that trusts your lab CA:
```bash
curl -k -H "Accept: application/dns-json"   "https://doh.local/dns-query?name=example.com&type=A"
```

### 7) Which ports and endpoints are used?
- **Traefik** exposes **HTTPS 443** (default). DoH endpoint is typically **`/dns-query`**.
- Internal services are networked via Docker; no direct exposure is required beyond Traefik.

### 8) Certificates: how do I deal with TLS trust?
- The stack uses **self-signed/dev certificates** by default. For quick tests use `curl -k`.
- For browsers or strict clients, import the generated **CA certificate** (from `./certs`) into the trust store of your lab machine/VM.

---

## Exfiltration Client & Scenarios

### 9) How do I run a test scenario?
```bash
cd exfiltration/client
python run_client.py --config test_configs/burst.json TESTFILEPATH
```
You can generate or list configs with:
```bash
python config_generator.py --create
python config_generator.py --list
```

### 10) What can I customize in scenarios?
- **Encoding**: base64, hex, base32, or custom
- **Chunking**: payload split size
- **Timing patterns**: regular, random, burst, stealth
- **Delays**: base delay / jitter
- **Encryption**: symmetric key (optional)
- **Domain rotation**: primary/backup domains
- **Target**: DoH endpoint (e.g., `https://doh.local/dns-query`)

### 11) How do I add a new encoding or timing pattern?
Extend the enums/classes in the exfiltration client (e.g., `EncodingType`, `TimingPattern`) and implement the encoding/timing logic. Then expose it via the JSON schema of `config_generator.py`.

---

## Detection & ML

### 12) What is the typical detection pipeline?
1. **Capture** traffic (Traefik & Resolver sides)
2. **DoHLyzer** extracts flows/features → `traffic_analyzer/output/output.csv`
3. Optional: **filter** detections (e.g., `exfiltration/client/filter_detection_csv.sh`)
4. **ML inference** with `ml_analyzer/predict.py` on the (filtered) CSV

### 13) How do I train models?
```bash
cd ml_analyzer
python trainer.py --quick --fpr 0.01
```
- `--quick`: smaller grid & sample cap for faster iterations
- `--fpr`: target False Positive Rate used to tune decision threshold

### 14) What dataset format is required for training?
- CSV files in `datasets/` containing a **`Label`** column and the expected **numeric features** (missing are median-imputed). Labels are string tags (`benign`/`malicious`, etc.).

### 15) Which models are used?
- **Quick mode**: RandomForest, LogisticRegression
- **Full mode**: adds GradientBoosting and SVC (with probability enabled)
All models are wrapped in a **scikit-learn Pipeline** + **isotonic calibration**. Hyper-parameters are tuned via **GridSearchCV**.

### 16) Where are models and thresholds saved?
Trainer writes to `models/`:
- `models/<name>.pkl` — pipeline (preprocessing + calibrated estimator)
- `models/thresholds.json` — tuned thresholds (picked on validation at target FPR)
- `models/best_model.pkl` — best model by test AUC
- `models/metadata.json` — environment & feature info
- `models/preprocessors.pkl` — scaler, label encoder (best-effort)

### 17) How do thresholds affect false positives?
The predictor applies a per-model threshold from `thresholds.json`. Lowering the threshold **increases** sensitivity (more TPR but more FPR). Raise it for fewer false positives. You can also rerun training with a stricter `--fpr` target.

### 18) How do I run predictions?
```bash
cd ml_analyzer
python predict.py ../traffic_analyzer/output/filtered_output.csv   
```
Outputs a table with **benign/malicious counts**, **threshold used**, and **average confidence**.

### 19) What is the DoHXP rule-based model?
A transparent, JSON-defined scorer that turns rule hits into a probability:
DoHXP is specified here : https://ieeexplore.ieee.org/document/9844067

```json
{
  "rules": [
    { "feature": "PacketLengthMean", "op": ">", "value": 400, "weight": 0.6 },
    { "feature": "PacketTimeVariance", "op": "<", "value": 0.001, "weight": 0.5 },
    { "feature": "FlowReceivedRate", "op": ">", "value": 20000, "weight": 0.4 }
  ],
  "aggregation": "sum",
  "clip": [0.0, 1.0],
  "bias": 0.0
}
```
You can change `aggregation` to `mean`, adjust `clip`, and add/remove rules.

---

## Data Flow & Monitoring

### 20) How does traffic flow through the stack?
- Client → **Traefik (HTTPS/DoH)** → DoH Server → DNS Resolver
- **Traffic Analyzer** listens on the Traefik side
- **Exfil Interceptor** listens on the Resolver side

---

## Troubleshooting

### 21) `docker compose up` fails or services crash
- Check port conflicts (e.g., something else binding **:443**)
- Ensure `./certs` exists (run `./generate_certs.sh`)
- Run `docker compose logs -f traefik doh_server resolver` to inspect logs

### 22) DoH queries fail with TLS errors
- Use `curl -k` for quick tests
- Import the generated **CA** cert into your trust store if you want strict TLS

### 23) No detections appear in outputs
- Verify the exfil client actually targets `https://doh.local/dns-query`
- Ensure Traffic Analyzer/Exfil Interceptor containers are **running**
- Confirm DoHLyzer produced `traffic_analyzer/output/output.csv`

### 24) Predictor says “no models loaded”
- Make sure you trained first: `python trainer.py --quick`
- Check for existing files under `models/*.pkl` and `models/thresholds.json`

### 25) Class imbalance is hurting results
- Keep **SMOTE** on (default)
- Try `undersample`/`combined` in `balance_dataset`
- Add more benign samples

### 26) Performance tips
- Use **quick mode** while iterating
- Reduce dataset size or feature set during development
- Avoid capturing beyond what you need for your experiments

---

## Security & Ethics

### 27) Is it safe to run on a production network?
No. Use **isolated lab networks**, VMs, or containers. Do not route real corporate traffic through this stack.

### 28) Are there legal risks?
Yes, if misused. Only test systems with explicit permission and follow your local laws/regulations.

---

## Extending & Contributing

### 29) How do I add a new ML model?
Add a new entry in `self.models_config` (trainer), provide a param grid, and ensure the estimator supports `predict_proba` (or is wrapped/calibrated).

### 30) How do I add features?
Update the **shared feature list** in both `trainer.py` and `predict.py`. Keep the order consistent. Retrain before predicting.

### 31) Where should I open issues or propose changes?
Use the GitHub **Issues** for bugs/feature requests and **Discussions** for questions. PRs are welcome with a small description and tests if applicable.

---

## Quick Commands Cheat Sheet

```bash
# Start
./generate_certs.sh && docker compose up -d

# Test DoH
docker exec -it client_test bash /scripts/test_doh.sh

# Run the testing pipeline
cd exfiltration/client && bash run_pipeline.sh

# Train ML
cd ml_analyzer && python trainer.py --quick --fpr 0.01

# Predict
python predict.py ../traffic_analyzer/output/filtered_output.csv 

# Logs
docker compose logs -f traefik doh_server resolver
```
---