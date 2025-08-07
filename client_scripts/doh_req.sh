#!/bin/bash
# filepath: /home/ubuntu/Kent-Dissertation/exfiltration/generate_normal_doh_traffic.sh

# Script pour générer du trafic DoH normal pendant 40 secondes
# Simule un utilisateur normal qui fait des requêtes DNS légitimes

DOH_SERVER="https://doh.local/dns-query"
DURATION=40
START_TIME=$(date +%s)
END_TIME=$((START_TIME + DURATION))

# Domaines légitimes pour les tests
LEGITIMATE_DOMAINS=(
    "google.com"
    "facebook.com"
    "youtube.com"
    "amazon.com"
    "microsoft.com"
    "apple.com"
    "netflix.com"
    "twitter.com"
    "wikipedia.org"
    "reddit.com"
    "github.com"
    "stackoverflow.com"
    "linkedin.com"
    "instagram.com"
    "whatsapp.com"
    "zoom.us"
    "dropbox.com"
    "spotify.com"
    "adobe.com"
    "salesforce.com"
    "office.com"
    "gmail.com"
    "yahoo.com"
    "bing.com"
    "cnn.com"
    "bbc.com"
    "nytimes.com"
    "weather.com"
    "cloudflare.com"
    "ubuntu.com"
)

# Types de requêtes DNS légitimes
QUERY_TYPES=("A" "AAAA" "MX" "TXT" "NS")

# User agents légitimes
USER_AGENTS=(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
    "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15"
)

echo "🌐 Generating legitimate DoH traffic for ${DURATION} seconds..."
echo "📡 DoH Server: ${DOH_SERVER}"
echo "⏰ Start time: $(date)"

TOTAL_REQUESTS=0
SUCCESSFUL_REQUESTS=0

while [ $(date +%s) -lt $END_TIME ]; do
    # Sélectionner un domaine aléatoire
    DOMAIN=${LEGITIMATE_DOMAINS[$RANDOM % ${#LEGITIMATE_DOMAINS[@]}]}
    
    # Sélectionner un type de requête aléatoire
    QUERY_TYPE=${QUERY_TYPES[$RANDOM % ${#QUERY_TYPES[@]}]}
    
    # Sélectionner un user agent aléatoire
    USER_AGENT=${USER_AGENTS[$RANDOM % ${#USER_AGENTS[@]}]}
    
    # Faire la requête DoH
    RESPONSE=$(curl -s -w "%{http_code}" \
        -H "Accept: application/dns-json" \
        -H "User-Agent: ${USER_AGENT}" \
        -H "Cache-Control: no-cache" \
        --connect-timeout 3 \
        --max-time 5 \
    "${DOH_SERVER}?name=${DOMAIN}&type=${QUERY_TYPE}" 2>/dev/null)
    
    HTTP_CODE="${RESPONSE: -3}"
    
    ((TOTAL_REQUESTS++))
    
    if [ "$HTTP_CODE" = "200" ]; then
        ((SUCCESSFUL_REQUESTS++))
        echo "✅ [${TOTAL_REQUESTS}] ${QUERY_TYPE} ${DOMAIN} - Success"
    else
        echo "❌ [${TOTAL_REQUESTS}] ${QUERY_TYPE} ${DOMAIN} - Failed (HTTP: ${HTTP_CODE})"
    fi
    
    # Délai aléatoire entre 0.1 et 2 secondes (comportement humain normal)
    DELAY=$(echo "scale=2; $RANDOM/32768*1.9+0.1" | bc -l 2>/dev/null || echo "0.5")
    sleep $DELAY
    
    # Afficher le progrès toutes les 10 requêtes
    if [ $((TOTAL_REQUESTS % 10)) -eq 0 ]; then
        ELAPSED=$(($(date +%s) - START_TIME))
        REMAINING=$((DURATION - ELAPSED))
        RATE=$(echo "scale=1; $TOTAL_REQUESTS/$ELAPSED" | bc -l 2>/dev/null || echo "N/A")
        echo "📊 Progress: ${ELAPSED}s/${DURATION}s - ${TOTAL_REQUESTS} requests - ${RATE} req/s - ${REMAINING}s remaining"
    fi
done

echo ""
echo "🏁 Traffic generation completed!"
echo "⏰ End time: $(date)"
echo "📈 Statistics:"
echo "   📋 Total requests: ${TOTAL_REQUESTS}"
echo "   ✅ Successful: ${SUCCESSFUL_REQUESTS}"
echo "   ❌ Failed: $((TOTAL_REQUESTS - SUCCESSFUL_REQUESTS))"
echo "   📊 Success rate: $(echo "scale=1; $SUCCESSFUL_REQUESTS*100/$TOTAL_REQUESTS" | bc -l 2>/dev/null || echo "N/A")%"

if [ $TOTAL_REQUESTS -gt 0 ]; then
    AVG_RATE=$(echo "scale=1; $TOTAL_REQUESTS/$DURATION" | bc -l 2>/dev/null || echo "N/A")
    echo "   ⚡ Average rate: ${AVG_RATE} requests/second"
fi