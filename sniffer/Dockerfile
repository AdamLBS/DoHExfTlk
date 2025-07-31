FROM python:3.11-slim

RUN apt-get update && apt-get install -y tcpdump libpcap-dev && \
    pip install --no-cache-dir scapy

COPY decode_live.py /app/decode_live.py
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app
CMD ["./entrypoint.sh"]
