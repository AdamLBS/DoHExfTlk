FROM mvance/unbound

RUN apt-get update && apt-get install -y tcpdump python3 python3-pip && \
    pip3 install --no-cache-dir scapy --break-system-packages && \
    chmod 777 /tmp

COPY decode_live.py /app/decode_live.py

WORKDIR /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 53/udp
ENTRYPOINT ["/app/entrypoint.sh"]
