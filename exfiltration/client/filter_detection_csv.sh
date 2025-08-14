#!/usr/bin/env bash
set -euo pipefail

# --- Config ---------------------------------------------------------------
INPUT_CSV="${1:-/traffic_analyzer/output/output.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-/app/captured}"
mkdir -p "$OUTPUT_DIR"

# --- IP du conteneur ------------------------------------------------------
get_container_ip() {
  local ip=""
  if command -v ip &>/dev/null; then
    ip="$(ip route get 1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}' || true)"
  fi
  if [[ -z "$ip" ]] && command -v hostname &>/dev/null; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  fi
  if [[ -z "$ip" ]] && command -v ip &>/dev/null; then
    ip="$(ip -o -4 addr show dev eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 || true)"
  fi
  [[ -n "$ip" ]] || { echo "Impossible de déterminer l'IP du conteneur." >&2; exit 1; }
  echo "$ip"
}
CONTAINER_IP="$(get_container_ip)"

[[ -f "$INPUT_CSV" ]] || { echo "Fichier introuvable: $INPUT_CSV" >&2; exit 1; }

base="$(basename "$INPUT_CSV")"
stem="${base%.csv}"
OUTPUT_CSV="${OUTPUT_DIR}/${stem}.only_${CONTAINER_IP}.csv"

tmp_file="$(mktemp)"
trap 'rm -f "$tmp_file"' EXIT

# --- 1 passe, uniquement via SourceIP/DestinationIP -----------------------
awk -v ip="$CONTAINER_IP" -F',' -v out_match="$OUTPUT_CSV" -v out_keep="$tmp_file" '
  function stripq(x){ gsub(/^"|"$/, "", x); return x }

  NR==1 {
    # indexe les colonnes
    for (i=1;i<=NF;i++){ h=$i; gsub(/"/,"",h); idx[h]=i }
    if (!("SourceIP" in idx) && !("DestinationIP" in idx)) {
      printf "Colonnes SourceIP/DestinationIP introuvables.\n" > "/dev/stderr"
      exit 2
    }
    s = ("SourceIP" in idx) ? idx["SourceIP"] : 0
    d = ("DestinationIP" in idx) ? idx["DestinationIP"] : 0
    # entête dans les deux sorties
    print $0 > out_match
    print $0 > out_keep
    next
  }

  {
    sval = (s ? stripq($s) : "")
    dval = (d ? stripq($d) : "")
    if ( (s && sval==ip) || (d && dval==ip) ) {
      print $0 >> out_match
    } else {
      print $0 >> out_keep
    }
  }
' "$INPUT_CSV"

# Remplace l’original par les lignes gardées (avec entête)
mv -f "$tmp_file" "$INPUT_CSV"
chown "1000:1000" "$INPUT_CSV"
trap - EXIT

echo "✅ Filtré → $OUTPUT_CSV"
echo "✅ Supprimé du fichier original (entête conservé) → $INPUT_CSV"
