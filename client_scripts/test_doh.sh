#!/bin/bash

echo "=== Lancement des tests DoH (GET uniquement) pendant 60 secondes ==="
end_time=$((SECONDS + 60))

while [ $SECONDS -lt $end_time ]; do
  echo "🌀 $(date '+%T') - Nouvelle itération"

  # Test 1: GET DoH pour google.com
  echo "🔹 Requête DoH GET pour google.com"
  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=google.com&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "❌ Erreur GET"

  # Test 2: GET DoH pour cloudflare.com
  echo "🔹 Requête DoH GET pour cloudflare.com"
  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=cloudflare.com&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "❌ Erreur GET"

  # Test 3: GET DoH pour wikipedia.org
  echo "🔹 Requête DoH GET pour wikipedia.org"
  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=wikipedia.org&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "❌ Erreur GET"

  echo ""
done

echo "✅ Tests terminés."
