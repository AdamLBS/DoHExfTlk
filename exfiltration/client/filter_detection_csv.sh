#!/usr/bin/env bash
set -euo pipefail

# --- Config ---------------------------------------------------------------
INPUT_CSV="${1:-/traffic_analyzer/output/output.csv}"         # ou passe le chemin en 1er argument
OUTPUT_DIR="${OUTPUT_DIR:-/app/captured}"        # override via variable d'env
mkdir -p "$OUTPUT_DIR"

# --- Récup IP du conteneur ------------------------------------------------
get_container_ip() {
  local ip=""
  # Méthode robuste: IP utilisée pour sortir vers Internet
  if command -v ip &>/dev/null; then
    ip="$(ip route get 1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1); exit}}' || true)"
  fi
  # Fallback: hostname -I
  if [[ -z "${ip}" ]] && command -v hostname &>/dev/null; then
    ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  fi
  # Fallback: eth0
  if [[ -z "${ip}" ]] && command -v ip &>/dev/null; then
    ip="$(ip -o -4 addr show dev eth0 2>/dev/null | awk '{print $4}' | cut -d/ -f1 || true)"
  fi

  if [[ -z "${ip}" ]]; then
    echo "[❌] Impossible de déterminer l'IP du conteneur." >&2
    exit 1
  fi
  echo "$ip"
}

CONTAINER_IP="$(get_container_ip)"
echo "[✅] IP du conteneur: ${CONTAINER_IP}"

if [[ ! -f "$INPUT_CSV" ]]; then
  echo "[❌] Fichier introuvable: $INPUT_CSV" >&2
  exit 1
fi

base="$(basename "$INPUT_CSV")"
stem="${base%.csv}"
OUTPUT_CSV="${OUTPUT_DIR}/${stem}.only_${CONTAINER_IP}.csv"

# --- Filtrage CSV ---------------------------------------------------------
# 1) Essaye de filtrer proprement sur les colonnes SourceIP/DestinationIP (si présentes)
# 2) Sinon, fallback: conserve les lignes contenant l'IP (grep)
awk -v ip="$CONTAINER_IP" -F',' '
  NR==1 {
    # normaliser l’en-tête (enlever guillemets)
    for (i=1;i<=NF;i++) { gsub(/"/, "", $i); hdr[$i]=i }
    print $0
    next
  }
  {
    # Si colonnes présentes, filtre exact sur SourceIP/DestinationIP
    if (("SourceIP" in hdr) || ("DestinationIP" in hdr)) {
      s = ("SourceIP" in hdr) ? hdr["SourceIP"] : 0
      d = ("DestinationIP" in hdr) ? hdr["DestinationIP"] : 0

      # enlever guillemets éventuels autour des champs comparés
      if (s && $s == "\"" ip "\"") $s = ip
      if (d && $d == "\"" ip "\"") $d = ip

      if ((s && $s == ip) || (d && $d == ip)) print $0
    } else {
      # Pas d’info colonnes -> on passe la main (signal au shell)
      exit 99
    }
  }
' "$INPUT_CSV" > "$OUTPUT_CSV" || {
  # Fallback si awk a quitté avec code 99 (pas de colonnes IP)
  if [[ $? -eq 99 ]]; then
    echo "[ℹ️] Colonnes SourceIP/DestinationIP non trouvées, fallback grep."
    {
      IFS= read -r header
      printf "%s\n" "$header"
      grep -F "$CONTAINER_IP" || true
    } < "$INPUT_CSV" > "$OUTPUT_CSV"
  else
    echo "[❌] Erreur inattendue lors du filtrage." >&2
    exit 1
  fi
}

echo "[✅] CSV filtré créé: $OUTPUT_CSV"
