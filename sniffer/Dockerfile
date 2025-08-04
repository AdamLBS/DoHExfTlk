FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    tcpdump \
    python3 \
    python3-pip \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    iproute2 && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    pip3 install --no-cache-dir scapy && \
    chmod 777 /tmp

COPY decode_live.py /app/decode_live.py
COPY run_sniffer.sh /app/run_sniffer.sh

WORKDIR /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh /app/run_sniffer.sh

ENTRYPOINT ["/app/entrypoint.sh"]
