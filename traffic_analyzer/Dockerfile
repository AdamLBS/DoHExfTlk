FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    git \
    libpcap-dev \
    tcpdump \
    net-tools \
    iputils-ping \
    curl \
    gcc \
    python3-dev \
    netcat-openbsd \
    dnsutils \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/AdamLBS/DoHLyzer.git /app/DoHLyzer

WORKDIR /app/DoHLyzer

RUN pip install --no-cache-dir \
    scapy \
    pandas \
    numpy \
    netifaces \
    psutil \
    docker \
    requests

RUN pip install -r requirements.txt

COPY detect_interface.sh /app/detect_interface.sh
RUN chmod +x /app/detect_interface.sh
RUN mkdir -p /app/output

WORKDIR /app
ENV RUNTIME_UID=1000
ENV RUNTIME_GID=1000
ENV UMASK=0002


CMD ["bash", "detect_interface.sh"]
