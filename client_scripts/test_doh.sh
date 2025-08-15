#!/bin/bash

end_time=$((SECONDS + 60))

while [ $SECONDS -lt $end_time ]; do
  echo "🌀 $(date '+%T') - Nouvelle itération"

  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=google.com&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "Error"

  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=cloudflare.com&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "Error"

  curl -k --insecure \
       -H "Accept: application/dns-json" \
       -H "User-Agent: DoH-Test-Client/1.0" \
       "https://doh.local/dns-query?name=wikipedia.org&type=A" \
       -s -w "\nStatus: %{http_code}\n" || echo "Error"

  echo ""
done

