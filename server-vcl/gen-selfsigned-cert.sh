#!/usr/bin/env bash
# 產生 tunnel -> nginx 這一段用的自簽憑證（只在本機產生，不進 git）。
#
#   ./server-vcl/gen-selfsigned-cert.sh          # 不存在才產生
#   ./server-vcl/gen-selfsigned-cert.sh --force  # 強制重新產生（換金鑰）
#
# 為什麼可以用自簽：
#   使用者看到的 HTTPS 憑證是 Cloudflare 的；這張只用在 cloudflared -> nginx
#   這段（同一台主機），cloudflared 以 --no-tls-verify 連線，不會驗證它。
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)/nginx_conf/conf/certs"
CRT="$DIR/server.crt"
KEY="$DIR/server.key"

# 憑證與私鑰必須「成對」存在才跳過；只缺一個也要重新產生，
# 否則 nginx 的 ssl_certificate / ssl_certificate_key 會有一個讀不到而起不來
if [[ -f "$CRT" && -f "$KEY" && "${1:-}" != "--force" ]]; then
  echo "憑證已存在：$CRT（要換新請加 --force）"
  exit 0
fi

mkdir -p "$DIR"
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout "$KEY" -out "$CRT" \
  -subj "/CN=vclnginx" \
  -addext "subjectAltName=DNS:vclnginx,DNS:localhost,IP:127.0.0.1" 2>/dev/null

# 權限 640：擁有者可讀寫、群組可讀、其他人不可讀。
# rootless Podman 下主機使用者對應容器內 root(0)，UBI nginx 以 UID 1001、群組 0 執行，
# 所以靠「群組可讀」讀得到金鑰。若 nginx 回報讀不到 key，再改成 644。
chmod 640 "$KEY"
chmod 644 "$CRT"

openssl x509 -in "$CRT" -noout -subject -enddate
echo "已產生：$CRT / $KEY"
