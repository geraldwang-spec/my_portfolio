#!/bin/bash
set -e

echo "[1/5] checking and craeting folder for local development and database ..."
mkdir -p ./sqldata
mkdir -p ./coreVcl

echo "[2/5] login redhat"
podman login registry.redhat.io

echo "[3/5] pull container image..."
podman pull registry.redhat.io/rhel9/redis-7:latest
podman pull registry.redhat.io/rhel9/postgresql-16:latest
podman pull registry.redhat.io/ubi9/python-39:latest
podman pull registry.redhat.io/ubi8/nginx-122:latest
podman pull docker.io/cloudflare/cloudflared:latest

echo "[4/5] initial podman network and container structure ..."
podman-compose -p vcl up --no-start

echo "[4/5] launch all server ..."
podman-compose -p vcl start

echo "🏁 =========================================="
echo "🎉 Vision Color Lab 開發環境一鍵啟動成功！"
echo "💡 現在你可以直接在 ./coreVcl 下用 Git 或直接改 Code，容器內會即時同步！"
echo "=============================================="
