if [ -p /tmp/live_dns.pcap ]; then
  rm /tmp/live_dns.pcap
fi

mkfifo /tmp/live_dns.pcap

tcpdump -i any udp port 53 -w /tmp/live_dns.pcap &

python decode_live.py /tmp/live_dns.pcap
