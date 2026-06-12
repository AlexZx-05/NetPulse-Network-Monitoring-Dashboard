#!/usr/bin/env bash
set -euo pipefail

apt-get update
apt-get install -y docker.io docker-compose-plugin git
systemctl enable --now docker

cd /opt
git clone https://github.com/YOUR_ORG/netpulse.git || true
cd netpulse

cp .env.example .env
sed -i "s/replace-with-a-strong-random-secret/$(openssl rand -hex 32)/" .env

docker compose pull || true
docker compose up -d --build
