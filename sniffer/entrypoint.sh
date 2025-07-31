#!/bin/bash
set -e

# Lancer unbound en arrière-plan
unbound-anchor -a /var/lib/unbound/root.key
unbound-control-setup
unbound -d &

# Lancer le script Python qui sniffe directement sur l'interface eth0
python3 /app/decode_live.py
