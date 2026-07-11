#!/bin/bash
set -e

echo "[1/5] checking and craeting folder for local development and database ..."
if [ ! -d "./coreVcl" ]; then
  echo "Can't find coreVcl foler, and then auto creating ..."
  mkdir -p ./coreVcl/templates ./coreVcl/static
else
  echo "coreVcl folder exist"
fi

if [ ! -d "./sqldata" ]; then
  echo "Can't find sqldata foler, and then auto creating ..."
  mkdir -p ./sqldata
else
  echo "sqldata folder exist"
fi

if [ ! -d "./redis_data" ]; then
  echo "Can't find redis_data foler, and then auto creating ..."
  mkdir -p ./redis_data
else
  echo "redis_data folder exist"
fi

echo "[2/5] change user and group"
sudo chown -R $(whoami):$(whoami) ./coreVcl ./sqldata ./redis_data 2>/dev/null

echo "[3/5] login redhat"
podman login registry.redhat.io

echo "[4/5] pull container image..."
podman pull registry.redhat.io/rhel9/redis-7:latest
podman pull registry.redhat.io/ubi8/nginx-122:latest
podman pull docker.io/cloudflare/cloudflared:latest
podman pull registry.redhat.io/rhel9/mariadb-1011
podman pull registry.access.redhat.com/ubi9/ubi

# echo "[4/5] initial podman network and container structure ..."
# podman-compose -p vcl up --no-start

echo "[5/5] launch all server ..."
# podman-compose -p vcl start
podman-compose -p vcl up -d --build

echo "🏁 =========================================="
echo "🎉 Vision Color Lab 開發環境一鍵啟動成功！"
echo "💡 現在你可以直接在 ./coreVcl 下用 Git 或直接改 Code，容器內會即時同步！"
echo "=============================================="
