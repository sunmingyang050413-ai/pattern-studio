#!/usr/bin/env bash
# Run as root on Ubuntu 24.04. Does not expose ports or upload credentials.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io docker-compose-v2 python3 curl ca-certificates unzip
systemctl enable --now docker
install -d -m 0755 /opt/pattern-studio
docker --version
docker compose version
df -h /
free -h
