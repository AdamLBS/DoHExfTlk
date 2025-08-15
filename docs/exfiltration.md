# DoHExfTlk — Exfiltration Guide

> This guide shows how to run a full **DoH exfiltration → detection → ML validation** pipeline using your `run_pipeline.sh` and the exfiltration server.

---

## TL;DR — One command
```bash
# From the repo root (where docker-compose.yml lives)
cd exfiltration/client
bash scripts/run_pipeline.sh
```
- The script will iterate **all `*.json`** configs in `./test_configs/`, run a test for each, pull back artifacts, aggregate ML stats, and rank configs by **least detected**.

---

## What the pipeline does 
1. **Starts containers** (exfil client + traffic analyzer).
2. For each **config JSON**:
   - Runs the **exfiltration client** (`run_client.py`) against your DoH endpoint, using the file you set (default: `/app/test_data/image.png`).
   - Waits ~30s for traffic to be captured.
   - **Filters** DoHLyzer output to keep only suspected exfil flows.
   - **Classifies** those flows with `ml/predictor.py` (per‑model thresholds).
   - Copies the **filtered CSV** and **predictor log** back to the host.
3. Prints a **per‑model summary** and a final **ranking of configs** (which one evaded best).

---

## Files & folders that matter
- **Configs (input):** `exfiltration/client/test_configs/*.json`
- **Results (output on host):** `exfiltration/client/results/run-YYYYmmdd-HHMMSS/`
  - One subfolder per config, containing:
    - `logs/client.log` & `logs/predictor_*.log`
    - `captured/*.only_*.csv` (filtered flows used by the predictor)
- **ML scripts:** `ml_analyzer/trainer.py`, `ml/predictor.py`

---

## Environment switches (quick reference)
You can override these when launching the script:
```
TEST_CONFIG_DIR   # default ./test_configs
RESULTS_DIR       # default ./results
DOCKER_COMPOSE_FILE  # default ../../docker-compose.yml
EXFIL_CONTAINER   # default exfil_client
ANALYZER_CONTAINER# default traffic_analyzer

CLIENT_PY_PATH            # default /app/run_client.py
IN_CONTAINER_CONFIG_DIR   # default /app/test_configs
IN_CONTAINER_CAPTURED_DIR # default /app/captured
IN_CONTAINER_FILTER_SCRIPT# default /app/filter_detection_csv.sh
PREDICTOR_PY              # default /ml/predictor.py
FILE_TO_EXFILTRATE        # default /app/test_data/image.png
```
**Example:**
```bash
RESULTS_DIR=./my_runs FILE_TO_EXFILTRATE=/app/test_data/doc.pdf bash scripts/run_pipeline.sh
```

---

## Reading the output
At the end you’ll see two things:

1) **Per‑model totals** (aggregated over all configs):
```
Model                   Benign    Malicious     Total   Detection Rate
random forest              280          528       808       65.35%
logistic regression        778           30       808        3.71%
...
```
2) **Config ranking** (lower rate = better evasion):
```
Config                      Model used        Detection rate
apt_simulation              random_forest        12.50%
stealth_burst               logistic_regression   3.23%
...
🏆 Best (least detected): stealth_burst — 3.23% — model: logistic_regression
```

> If no logs are found for a config, you’ll see a message and it will be skipped.

---

## Exfiltration Server
- Listens on your chosen interface (default `eth0`) via `DoHTrafficInterceptor`.
- **Detects** suspicious DoH queries (e.g., domains containing `exfill`, `data`, `leak`).
- **Parses chunks** named like: `TIMESTAMP-INDEX-TOTAL-ENCODED...`  
  (e.g., `17545887-12-143-k8I4U...`)
- **Reassembles** when all chunks arrive, tries to **decode** in order:
  1) URL‑safe Base64 → 2) Base64 → 3) Base32 → 4) Hex → else raw bytes
- **Writes a file** to `/app/captured/` and **guesses type** by magic bytes; renames with extension when possible (e.g., `.png`, `.pdf`, `.zip`).

> Tip: sessions are tracked in memory; once complete, the server cleans them up.

---

## Minimal troubleshooting
- **No filtered CSV found**: ensure the traffic actually hit `/dns-query` and the filter script path is correct (`IN_CONTAINER_FILTER_SCRIPT`).  
- **Predictor says no models**: train first (`ml_analyzer/trainer.py`), then re‑run pipeline.
- **TLS errors**: for quick tests use `curl -k` or import the generated CA into your lab machine.
- **Ranking empty**: check per‑config `logs/predictor_*.log` for model sections (🤖 markers).

---

## Good to know
- Add new test scenarios by dropping more `*.json` files into `test_configs/`.
- Change the file you exfiltrate with `FILE_TO_EXFILTRATE` (inside the exfil client container path).
- You can tune ML thresholds by retraining with a different `--fpr` target.
- The final winner is the config with the **lowest malicious rate** for the chosen model.