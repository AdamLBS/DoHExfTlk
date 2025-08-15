#!/usr/bin/env bash
set -euo pipefail

# =====================[ Settings ]=====================
# Paths on the HOST
TEST_CONFIG_DIR="${TEST_CONFIG_DIR:-./test_configs}"     # contains .json config files
RESULTS_DIR="${RESULTS_DIR:-./results}"                  # where results are copied on the host
FILE_TO_EXFILTRATE="${FILE_TO_EXFILTRATE:-/app/test_data/image.png}"

# Docker Compose
DOCKER_COMPOSE_FILE="${DOCKER_COMPOSE_FILE:-../../docker-compose.yml}"

# Containers
EXFIL_CONTAINER="${EXFIL_CONTAINER:-exfil_client}"
ANALYZER_CONTAINER="${ANALYZER_CONTAINER:-traffic_analyzer}"

# Paths INSIDE exfil_client container
CLIENT_PY_PATH="${CLIENT_PY_PATH:-/app/run_client.py}"
IN_CONTAINER_CONFIG_DIR="${IN_CONTAINER_CONFIG_DIR:-/app/test_configs}"
IN_CONTAINER_CAPTURED_DIR="${IN_CONTAINER_CAPTURED_DIR:-/app/captured}"
IN_CONTAINER_FILTER_SCRIPT="${IN_CONTAINER_FILTER_SCRIPT:-/app/filter_detection_csv.sh}"
PREDICTOR_PY="${PREDICTOR_PY:-/ml/predictor.py}"

# =====================[ Helpers ]======================
die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo "[INFO] $*"; }

require_bin() {
  command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

# =====================[ Preflight ]====================
require_bin docker
require_bin awk
require_bin grep
require_bin sed
require_bin date

mkdir -p "$RESULTS_DIR"
[[ -d "$TEST_CONFIG_DIR" ]] || die "Config directory not found: $TEST_CONFIG_DIR"

shopt -s nullglob
configs=( "$TEST_CONFIG_DIR"/*.json )
shopt -u nullglob
(( ${#configs[@]} > 0 )) || die "No .json config found in: $TEST_CONFIG_DIR"

RUN_TS="$(date +%Y%m%d-%H%M%S)"
RUN_ROOT="$RESULTS_DIR/run-$RUN_TS"
mkdir -p "$RUN_ROOT"

info "Campaign started: $RUN_ROOT"
info "Detected ${#configs[@]} configuration(s)"

# =====================[ Start containers ]==============
info "Starting required containers (compose up -d)…"
docker compose -f "$DOCKER_COMPOSE_FILE" up -d "$EXFIL_CONTAINER" "$ANALYZER_CONTAINER"

info "Brief stabilization wait…"
sleep 5

# =====================[ Test loop ]=====================
for cfg in "${configs[@]}"; do
  cfg_base="$(basename "$cfg" .json)"
  test_id="${cfg_base}-$(date +%s)"
  out_dir="$RUN_ROOT/$cfg_base"
  mkdir -p "$out_dir/logs" "$out_dir/captured"

  echo
  echo "=================================================="
  echo "  Test: $cfg_base"
  echo "   ID : $test_id"
  echo "=================================================="

  docker exec "$EXFIL_CONTAINER" bash -lc "
    set -euo pipefail
    echo '[client] Starting quick test: $cfg_base.json'
    python3 \"$CLIENT_PY_PATH\" \
      --config \"$IN_CONTAINER_CONFIG_DIR/$cfg_base.json\" \
      \"$FILE_TO_EXFILTRATE\"

    echo '[client] Quick test finished. Sleeping 30s…'
    sleep 30

    echo '[client] Filtering CSV…'
    bash \"$IN_CONTAINER_FILTER_SCRIPT\"

    echo '[client] Selecting latest filtered CSV…'
    LAST_CSV=\$(ls -1t \"$IN_CONTAINER_CAPTURED_DIR\"/*.only_*.csv 2>/dev/null | head -n1 || true)
    if [[ -z \"\${LAST_CSV:-}\" || ! -f \"\$LAST_CSV\" ]]; then
      echo 'No filtered CSV found in $IN_CONTAINER_CAPTURED_DIR' >&2
      exit 3
    fi
    echo \"[client] Selected CSV: \$LAST_CSV\"

    echo '[client] Running predictor…'
    LOG_PATH=\"/tmp/predictor_${test_id}.log\"
    python3 \"$PREDICTOR_PY\" \"\$LAST_CSV\" 2>&1 | tee \"\$LOG_PATH\"

    # Emit markers that the host will parse:
    echo \"CSV_PATH=\$LAST_CSV\"
    echo \"PRED_LOG=\$LOG_PATH\"
  " | tee "$out_dir/logs/client.log"

  # ---------- Copy artifacts back to host ----------
  CSV_PATH_IN_CONTAINER="$(grep -Eo 'CSV_PATH=/.*\.csv' "$out_dir/logs/client.log" | sed 's/^CSV_PATH=//' | head -n1 || true)"
  PRED_LOG_IN_CONTAINER="$(grep -Eo 'PRED_LOG=/.*\.log' "$out_dir/logs/client.log" | sed 's/^PRED_LOG=//' | head -n1 || true)"

  if [[ -n "${CSV_PATH_IN_CONTAINER:-}" ]]; then
    docker cp "${EXFIL_CONTAINER}:${CSV_PATH_IN_CONTAINER}" "$out_dir/captured/$(basename "$CSV_PATH_IN_CONTAINER")" \
      || info "Could not docker cp CSV (continuing)."
  else
    info "Could not detect filtered CSV path from client log."
  fi

  if [[ -n "${PRED_LOG_IN_CONTAINER:-}" ]]; then
    docker cp "${EXFIL_CONTAINER}:${PRED_LOG_IN_CONTAINER}" "$out_dir/logs/$(basename "$PRED_LOG_IN_CONTAINER")" \
      || info "Could not docker cp predictor log (continuing)."
  fi
done

echo
info "All tests finished. Results in: $RUN_ROOT"

# =====================[ Overall aggregation ]=====================
echo
info "Computing overall per-model stats…"

declare -A BENIGN MALICIOUS TOTAL
MODELS=()

shopt -s nullglob
for logf in "$RUN_ROOT"/*/logs/predictor_*.log; do
  current=""
  benign=""
  malicious=""

  while IFS= read -r line; do
    if [[ "$line" =~ 🤖[[:space:]]+([A-Za-z0-9_]+): ]]; then
      current="${BASH_REMATCH[1]}"
      current="$(echo "$current" | tr '[:upper:]' '[:lower:]')"  # normalize
      if [[ " ${MODELS[*]} " != *" $current "* ]]; then
        MODELS+=( "$current" )
      fi
      benign=""
      malicious=""
      continue
    fi

    # Parse counts like:
    #   "- Benign: N"
    #   "- Malicious: M"
    if [[ "$line" =~ -[[:space:]]+Benign:[[:space:]]+([0-9]+) ]]; then
      benign="${BASHREMATCH[1]:-${BASH_REMATCH[1]}}"
      continue
    fi

    if [[ "$line" =~ -[[:space:]]+Malicious:[[:space:]]+([0-9]+) ]]; then
      malicious="${BASHREMATCH[1]:-${BASH_REMATCH[1]}}"
      if [[ -n "${current:-}" && -n "${benign:-}" && -n "${malicious:-}" ]]; then
        BENIGN["$current"]=$(( ${BENIGN["$current"]:-0} + benign ))
        MALICIOUS["$current"]=$(( ${MALICIOUS["$current"]:-0} + malicious ))
        TOTAL["$current"]=$(( ${TOTAL["$current"]:-0} + benign + malicious ))
        benign=""; malicious=""
      fi
      continue
    fi
  done < "$logf"
done
shopt -u nullglob

printf "\n%-24s %10s %12s %10s %14s\n" "Model" "Benign" "Malicious" "Total" "Detection Rate"
printf "%-24s %10s %12s %10s %14s\n" "------------------------" "----------" "------------" "----------" "--------------"

if (( ${#MODELS[@]} == 0 )); then
  echo "No predictor_* logs found to aggregate."
else
  for m in "${MODELS[@]}"; do
    b=${BENIGN["$m"]:-0}
    ml=${MALICIOUS["$m"]:-0}
    t=${TOTAL["$m"]:-0}
    if (( t > 0 )); then
      rate="$(awk -v m="$ml" -v t="$t" 'BEGIN{ printf("%.2f%%", (m*100.0)/t) }')"
    else
      rate="n/a"
    fi
    label="$(echo "$m" | tr '_' ' ' )"
    printf "%-24s %10d %12d %10d %14s\n" "$label" "$b" "$ml" "$t" "$rate"
  done
fi

echo

# =====================[ Pick best config (least detected) ]=====================
info "Ranking configs by 'least detected'…"

declare -A CFG_RATE CFG_MODEL

shopt -s nullglob
for cfgdir in "$RUN_ROOT"/*; do
  [[ -d "$cfgdir" ]] || continue
  cfg_name="$(basename "$cfgdir")"

  logf="$(ls -1t "$cfgdir"/logs/predictor_*.log 2>/dev/null | head -n1 || true)"
  [[ -f "$logf" ]] || { info "No predictor log for $cfg_name, skipping."; continue; }

  declare -A M_BENIGN M_MALICIOUS M_TOTAL
  current=""; benign=""; malicious=""

  while IFS= read -r line; do
    if [[ "$line" =~ 🤖[[:space:]]+([A-Za-z0-9_]+): ]]; then
      current="$(echo "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
      benign=""; malicious=""
      continue
    fi
    if [[ "$line" =~ -[[:space:]]+Benign:[[:space:]]+([0-9]+) ]]; then
      benign="${BASH_REMATCH[1]}"
      continue
    fi
    if [[ "$line" =~ -[[:space:]]+Malicious:[[:space:]]+([0-9]+) ]]; then
      malicious="${BASH_REMATCH[1]}"
      if [[ -n "$current" && -n "$benign" && -n "$malicious" ]]; then
        M_BENIGN["$current"]=$(( ${M_BENIGN["$current"]:-0} + benign ))
        M_MALICIOUS["$current"]=$(( ${M_MALICIOUS["$current"]:-0} + malicious ))
        M_TOTAL["$current"]=$(( ${M_TOTAL["$current"]:-0} + benign + malicious ))
        benign=""; malicious=""
      fi
      continue
    fi
  done < "$logf"

  chosen=""
  for cand in consensus random_forest logistic_regression gradient_boosting svm naive_bayes; do
    if [[ -n "${M_TOTAL[$cand]:-}" ]]; then chosen="$cand"; break; fi
  done
  if [[ -z "$chosen" ]]; then
    for k in "${!M_TOTAL[@]}"; do chosen="$k"; break; done
  fi

  if [[ -z "$chosen" || -z "${M_TOTAL[$chosen]:-}" || "${M_TOTAL[$chosen]}" -eq 0 ]]; then
    info "No usable stats for $cfg_name, skipping."
    continue
  fi

  rate="$(awk -v m="${M_MALICIOUS[$chosen]}" -v t="${M_TOTAL[$chosen]}" 'BEGIN{ printf("%.6f", (m+0.0)/t) }')"
  CFG_RATE["$cfg_name"]="$rate"
  CFG_MODEL["$cfg_name"]="$chosen"
done
shopt -u nullglob

printf "\n%-28s %-18s %-16s\n" "Config" "Model used" "Detection rate"
printf "%-28s %-18s %-16s\n" "----------------------------" "------------------" "----------------"
for cfg in "${!CFG_RATE[@]}"; do
  printf "%-28s %-18s %-16s\n" "$cfg" "${CFG_MODEL[$cfg]}" "$(awk -v r="${CFG_RATE[$cfg]}" 'BEGIN{ printf("%.2f%%", r*100) }')"
done | sort -k3,3V

best_cfg=""
best_rate=""
for cfg in "${!CFG_RATE[@]}"; do
  if [[ -z "$best_cfg" ]]; then
    best_cfg="$cfg"; best_rate="${CFG_RATE[$cfg]}"
  else
    if awk -v a="${CFG_RATE[$cfg]}" -v b="$best_rate" 'BEGIN{exit !(a<b)}'; then
      best_cfg="$cfg"; best_rate="${CFG_RATE[$cfg]}"
    fi
  fi
done

if [[ -n "$best_cfg" ]]; then
  printf "\n🏆 Best (least detected) config: %s  —  rate: %s  —  model: %s\n" \
    "$best_cfg" "$(awk -v r="$best_rate" 'BEGIN{ printf("%.2f%%", r*100) }')" "${CFG_MODEL[$best_cfg]}"
else
  echo "No configs could be ranked."
fi
