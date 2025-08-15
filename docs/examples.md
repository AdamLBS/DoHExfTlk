# Usage Example

### Launch a full exfiltration scenario
```bash
# Train model
cd ml_analyzer
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python model_trainer.py
# Wait for training to be finished

# Launch the pipeline

cd DoHExfTlk/exfiltration/client
bash run_pipeline.sh

```

Example of output : 

```
[273/274] Sent chunk: 17552566-0272-0274-7Kq_LxaSW-Bhb7J7AwkXfLPFUZ6hou....
2025-08-15 11:18:06,736 - INFO - Integration test successful!
2025-08-15 11:18:06,736 - INFO - Exfiltration Statistics:
2025-08-15 11:18:06,736 - INFO -   - File: image.png
2025-08-15 11:18:06,736 - INFO -   - Size: 6,918 bytes
2025-08-15 11:18:06,736 - INFO -   - Configuration: config file '/app/test_configs/speed.json'
2025-08-15 11:18:06,736 - INFO -   - Total chunks: 274
2025-08-15 11:18:06,736 - INFO -   - Successful chunks: 274
2025-08-15 11:18:06,736 - INFO -   - Failed chunks: 0
2025-08-15 11:18:06,736 - INFO -   - Success rate: 100.0%
2025-08-15 11:18:06,736 - INFO -   - Total time: 5.54 seconds
[274/274] Sent chunk: 17552566-0273-0274-L_PWwBulpGdys1HCL-B5eFj2QGGwAA....

Transmission complete: 100.0% success rate
Actual time: 5.5s (estimated: 3.9s)

📈 EXFILTRATION STATISTICS:
   Duration: 5.50 seconds
   Total chunks: 274
   Successful: 274
   Failed: 0
   Retries: 0
   Success rate: 100.0%
   Throughput: 1256.78 bytes/sec
   Total bytes: 6918
2025-08-15 11:18:06,737 - INFO -   - Average speed: 1.2 KB/s
2025-08-15 11:18:06,737 - INFO - Integration test completed successfully!
2025-08-15 11:18:06,741 - INFO - Exfiltration completed successfully!
2025-08-15 11:18:06,741 - INFO - File '/app/test_data/image.png' has been exfiltrated via DoH
[client] Quick test finished. Sleeping 30s…
[client] Filtering CSV…
[client] Selecting latest filtered CSV…
[client] Selected CSV: /app/captured/output.only_172.18.0.5.csv
[client] Running predictor…
2025-08-15 11:18:38,070 - ERROR - Error loading ../models/gradient_boosting.pkl: Can't get attribute '__pyx_unpickle_CyHalfBinomialLoss' on <module 'sklearn._loss._loss' from '/usr/local/lib/python3.11/site-packages/sklearn/_loss/_loss.cpython-311-x86_64-linux-gnu.so'>
2025-08-15 11:18:38,075 - INFO - Loaded model: logistic_regression
2025-08-15 11:18:38,193 - INFO - Loaded model: random_forest
2025-08-15 11:18:38,194 - INFO - Loaded DoHXP rule-based model from ../models/dohxp_model.json
2025-08-15 11:18:38,194 - INFO - Loading data: /app/captured/output.only_172.18.0.5.csv
2025-08-15 11:18:38,207 - INFO - Features used: 31/31
2025-08-15 11:18:38,207 - INFO - === PREDICTIONS ===
2025-08-15 11:18:38,215 - INFO - 🤖 LOGISTIC_REGRESSION:
2025-08-15 11:18:38,215 - INFO -    - Benign: 1
2025-08-15 11:18:38,215 - INFO -    - Malicious: 0
2025-08-15 11:18:38,215 - INFO -    - Threshold applied: 0.957
2025-08-15 11:18:38,215 - INFO -    - Avg confidence: 0.995
2025-08-15 11:18:38,245 - INFO - 🤖 RANDOM_FOREST:
2025-08-15 11:18:38,245 - INFO -    - Benign: 1
2025-08-15 11:18:38,245 - INFO -    - Malicious: 0
2025-08-15 11:18:38,245 - INFO -    - Threshold applied: 0.209
2025-08-15 11:18:38,245 - INFO -    - Avg confidence: 0.980
2025-08-15 11:18:38,246 - INFO - 🤖 DOHXP:
2025-08-15 11:18:38,246 - INFO -    - Benign: 0
2025-08-15 11:18:38,246 - INFO -    - Malicious: 1
2025-08-15 11:18:38,246 - INFO -    - Threshold applied: 0.500
2025-08-15 11:18:38,246 - INFO -    - Avg confidence: 1.000
2025-08-15 11:18:38,246 - INFO - 
=== SUMMARY OF PREDICTIONS ===

Model                      Benign    Malicious      Total Threshold   Confidence
--------------------------------------------------------------------------------
logistic_regression             1            0          1    0.957        0.995
random_forest                   1            0          1    0.209        0.980
dohxp                           0            1          1    0.500        1.000
CSV_PATH=/app/captured/output.only_172.18.0.5.csv
PRED_LOG=/tmp/predictor_speed-1755256680.log
Successfully copied 3.07kB to /home/ubuntu/Kent-Dissertation/exfiltration/client/results/run-20250815-105441/speed/captured/output.only_172.18.0.5.csv
Successfully copied 3.58kB to /home/ubuntu/Kent-Dissertation/exfiltration/client/results/run-20250815-105441/speed/logs/predictor_speed-1755256680.log
```