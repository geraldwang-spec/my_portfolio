#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "[1/5] checking and creating folder for local development and database ..."
if [ ! -f ./coreVcl/app.py ]; then
  echo "Error: Can't find ./coreVcl/app.py" >&2
  echo "Please execute at root of repo, and complete git clone or not" >&2
  exit 1
fi

for d in ./sqldata ./redis_data; do
  if [ ! -d "$d" ]; then
    echo "Can't find $d, creating..."
    mkdir -p "$d"
  else
    echo "$d exists"
  fi
done

# echo "[2/5] change user and group"
# sudo chown -R $(whoami):$(whoami) ./coreVcl ./sqldata ./redis_data 2>/dev/null

echo "[2/5] login redhat"
podman login registry.redhat.io

echo "[3/5] pull container image..."
podman pull registry.redhat.io/rhel9/redis-7:latest
podman pull registry.redhat.io/ubi8/nginx-122:latest
podman pull docker.io/cloudflare/cloudflared:latest
podman pull registry.redhat.io/rhel9/mariadb-1011
podman pull registry.access.redhat.com/ubi9/ubi

# echo "[4/5] initial podman network and container structure ..."
# podman-compose -p vcl up --no-start
echo "[4/5] checking certs..."
./server-vcl/gen-selfsigned-cert.sh

echo "[5/5] launch all server ..."
# podman-compose -p vcl start
podman-compose -p vcl up -d --build

echo "🏁 =========================================="
echo "🎉 Vision Color Lab 開發環境一鍵啟動成功！"
echo "💡 現在你可以直接在 ./coreVcl 下用 Git 或直接改 Code，容器內會即時同步！"
echo "=============================================="
