#!/usr/bin/env bash
# Block public DNS over HTTPS provider IPs on all interfaces (Linux) at program startup
# 
# This script is designed for use in program initialization: block all traffic to DoH providers like Cloudflare, Google, Quad9, NextDNS, AdGuard, and more
# Requires root privileges (use with sudo or as part of a systemd service/daemon)

# IPv4 addresses to block (expand as necessary)
DOH_IPS_V4=(
    "1.1.1.1"
    "1.0.0.1"
    "8.8.8.8"
    "8.8.4.4"
    "9.9.9.9"
    "149.112.112.112"
    "94.140.14.14"
    "94.140.15.15"
    "185.228.168.9"
    "185.228.168.168"
    "76.76.19.19"  # NextDNS
    "76.223.122.150"  # NextDNS
    "208.67.222.222"  # OpenDNS
    "208.67.220.220"  # OpenDNS
)

# IPv6 addresses to block
DOH_IPS_V6=(
    "2606:4700:4700::1111"
    "2606:4700:4700::1001"
    "2001:4860:4860::8888"
    "2001:4860:4860::8844"
    "2620:fe::9"
    "2620:fe::fe"
    "2a10:50c0::ad1:ff"
    "2a10:50c0::ad2:ff"
    "2a07:a8c0::"
    "2a07:a8c0::1"
    "2620:119:35::35"  # OpenDNS
    "2620:119:53::53"  # OpenDNS
)

# Block each IPv4
for ip in "${DOH_IPS_V4[@]}"; do
    iptables -A OUTPUT -d "$ip" -j REJECT
    iptables -A INPUT -s "$ip" -j REJECT
    iptables -A FORWARD -d "$ip" -j REJECT
    iptables -A FORWARD -s "$ip" -j REJECT
    echo "Blocked DoH IP $ip (IPv4)"
done

# Block each IPv6
for ip in "${DOH_IPS_V6[@]}"; do
    ip6tables -A OUTPUT -d "$ip" -j REJECT
    ip6tables -A INPUT -s "$ip" -j REJECT
    ip6tables -A FORWARD -d "$ip" -j REJECT
    ip6tables -A FORWARD -s "$ip" -j REJECT
    echo "Blocked DoH IP $ip (IPv6)"
done

exit 0
