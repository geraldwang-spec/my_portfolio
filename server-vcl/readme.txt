# 手動建立容器（podman-compose 以外的做法）
#
# 用途：一個一個建立容器，方便除錯、理解 compose 實際做了什麼。
# 平常開發用 ./deplay.sh（podman-compose）就好。
#
# 注意事項
# - 所有指令都在 repo 根目錄執行。
# - 容器名稱和 podman-compose.yaml 相同，不要和 compose 同時跑，名稱會衝突。
# - -v 的來源一律用 ./ 開頭：Podman 遇到沒有 "/" 的來源（例如 coreVcl）
#   會當成 named volume 的名稱，掛進去的是一個空的 volume。
# - 目前程式（coreVcl/auth/login_setting.py）連的是 MariaDB。
#   改用 PostgreSQL 是階段 1 的工作，屆時程式、compose 和這份文件一起改。

# ------------------------------------------------------------------
# 0. 登入 Red Hat registry、下載映像、建置 Flask 映像
# ------------------------------------------------------------------
podman login registry.redhat.io
podman pull registry.redhat.io/rhel9/redis-7:latest
podman pull registry.redhat.io/rhel9/mariadb-1011:latest
podman pull registry.redhat.io/ubi8/nginx-122:latest
# cloudflared 固定版本，和 compose 一致；用 latest 的話每次拉到的版本可能不同
podman pull docker.io/cloudflare/cloudflared:2026.10.0

# Flask 用的映像（Containerfile 以 ubi9/ubi 為基底，ARM64 / x86_64 都可建置）
podman build -t localhost/my-ubi-python:latest -f Containerfile .

# ------------------------------------------------------------------
# 1. 資料夾與自簽憑證
# ------------------------------------------------------------------
# bind mount 的來源資料夾必須先存在，否則 podman run 會失敗
mkdir -p ./sqldata ./redis_data

# nginx 用的自簽憑證（只在本機產生，不進 git；第一次或要換金鑰時執行）
./server-vcl/gen-selfsigned-cert.sh

# ------------------------------------------------------------------
# 2. 機密（Podman secrets，只要做一次）
# ------------------------------------------------------------------
# 名稱要和程式讀取的一致：modules/Settings.py 的 read_secret() 讀 /run/secrets/<名稱>
# 用 printf '%s' "$(...)" 是為了去掉結尾換行：程式會 strip()，但資料庫容器不會，
# 換行留著的話兩邊密碼就對不上。
for s in mysql_password mysql_root_password redis_password secret_key; do
  podman secret exists "$s" || printf '%s' "$(openssl rand -hex 24)" | podman secret create "$s" -
done

# 寄信用的應用程式密碼要自己輸入；read -s 不回顯，也不會留在 shell 歷史裡
read -rs -p "mail password: " MAIL_PASSWORD; echo
printf '%s' "$MAIL_PASSWORD" | podman secret create mail_password -
unset MAIL_PASSWORD

# ------------------------------------------------------------------
# 3. 網路
# ------------------------------------------------------------------
# frontend：tunnel <-> nginx <-> Flask
#   網段必須和 standalone.conf 的 set_real_ip_from 一致，nginx 才會採信 tunnel 帶來的使用者 IP
# backend_redis：Flask <-> MariaDB / Redis（資料庫不接 frontend，也不對主機發布 port）
podman network create frontend --subnet 10.101.1.0/24 --gateway 10.101.1.1
podman network create backend_redis --subnet 10.66.0.0/24 --gateway 10.66.0.1

# ------------------------------------------------------------------
# 4. Redis（存密碼重設碼，附 TTL）
# ------------------------------------------------------------------
# --secret ...,type=env => 以環境變數 REDIS_PASSWORD 交給容器
# :Z => 只有這個容器使用，給私有 SELinux 標籤
# :U => 把資料夾擁有者改成容器內 redis 使用者對應的 UID（rootless 下才寫得進去）
podman run -d --name vclredis --network backend_redis --ip 10.66.0.3 \
  --secret redis_password,type=env,target=REDIS_PASSWORD \
  -v ./redis_data:/var/lib/redis/data:Z,U \
  registry.redhat.io/rhel9/redis-7:latest

# ------------------------------------------------------------------
# 5. MariaDB
# ------------------------------------------------------------------
podman run -d --name mariadb_db --network backend_redis --ip 10.66.0.4 \
  -e MYSQL_USER=vcl -e MYSQL_DATABASE=vision_db \
  --secret mysql_password,type=env,target=MYSQL_PASSWORD \
  --secret mysql_root_password,type=env,target=MYSQL_ROOT_PASSWORD \
  -v ./sqldata:/var/lib/mysql:Z,U \
  registry.redhat.io/rhel9/mariadb-1011:latest

# ------------------------------------------------------------------
# 6. Flask 容器（core_pj）
# ------------------------------------------------------------------
# --name core_pj => standalone.conf 的 proxy_pass 指向 core_pj:5000，名稱要一致
# -e ... => 程式用 require_env() 讀的設定；值要和步驟 4、5 一致
# --secret 不加 type => 以檔案掛在 /run/secrets/<名稱>，給 read_secret() 讀
# --userns keep-id => 容器內 appCore(UID 1000) 就是主機上的你，主機改的程式容器內可直接用
# :z（小寫）=> 共用標籤。vclnginx 也會掛 ./coreVcl/static；
#   兩邊都用 :Z 的話，後啟動的容器會把標籤改成自己私有的，另一個就讀不到（nginx 回 403）
# tail -f /dev/null => 讓容器保持執行。Containerfile 的預設 CMD 是 gunicorn + FastAPI，
#   和目前的 Flask 程式不合，不覆蓋的話容器會直接結束
podman run -d --name core_pj --network frontend --network backend_redis \
  --userns keep-id \
  -e MYSQL_USER=vcl -e MYSQL_DATABASE=vision_db -e MARIADB_IP=10.66.0.4 \
  -e REDIS_IP=10.66.0.3 \
  -e MAIL_USERNAME=you@example.com \
  --secret secret_key --secret mysql_password --secret redis_password --secret mail_password \
  -v ./coreVcl:/app:z \
  localhost/my-ubi-python:latest tail -f /dev/null

# 安裝 Python 套件：裝在容器內 appCore 的 ~/.local，容器刪掉重建後要再裝一次
podman exec core_pj python3 -m pip install --user -r requirements.txt

# ------------------------------------------------------------------
# 7. nginx
# ------------------------------------------------------------------
# 先檢查設定（改完 standalone.conf 都先跑這個，通過再重啟 vclnginx）
# label=disable：臨時容器不改 SELinux 標籤，避免正在跑的 vclnginx 讀不到檔案
# 要在步驟 6 之後跑：nginx -t 會解析 proxy_pass 的主機名稱 core_pj
podman run --rm --security-opt label=disable --network frontend \
  -v ./server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:ro \
  -v ./server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:ro \
  registry.redhat.io/ubi8/nginx-122:latest nginx -t

# 啟動 nginx
# 靜態檔 ./coreVcl/static 由 nginx 直接回應，用 :z（原因見步驟 6）
# -p 只綁 127.0.0.1：本機瀏覽器可以用 https://127.0.0.1:8443 測試，區網和外網連不到；
#   對外一律走 tunnel。不需要本機測試時可以拿掉 -p。
podman run -d --name vclnginx --network frontend \
  -p 127.0.0.1:8443:8443 \
  -v ./server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:Z,ro \
  -v ./server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:Z,ro \
  -v ./coreVcl/static:/opt/app-root/src/static:z,ro \
  registry.redhat.io/ubi8/nginx-122:latest nginx -g "daemon off;"

# ------------------------------------------------------------------
# 8. Cloudflare Tunnel
# ------------------------------------------------------------------
# 目前是 quick tunnel：每次啟動網址都會變（固定網域要改用具名 tunnel + token）
# --name vcl_tunnel => Settings.public_base_url() 會向 http://vcl_tunnel:2000 查目前網址，名稱要一致
# --protocol http2 => 部分網路環境擋 QUIC(UDP)，固定用 TCP
# --no-tls-verify => 不驗證 nginx 的自簽憑證（tunnel -> nginx 在同一台主機、同一個容器網路）
# 本機和雲端 VM 用同一組指令；tunnel 只有對外連出，主機不需要開任何對外 port
podman run -d --name vcl_tunnel --network frontend \
  docker.io/cloudflare/cloudflared:2026.10.0 \
  tunnel --no-autoupdate --metrics 0.0.0.0:2000 --protocol http2 \
  --url https://vclnginx:8443 --no-tls-verify

# 查目前的對外網址
podman logs vcl_tunnel 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com'

# ------------------------------------------------------------------
# 9. 啟動 Flask
# ------------------------------------------------------------------
# 前景執行，Ctrl+C 停止。app.py 監聽 port 5000，要和 standalone.conf 的 proxy_pass 一致
# ⚠️ app.py 目前用 debug=True：只能在開發時用，接上 tunnel 後等於公開在網路上
podman exec -it core_pj python3 app.py

# ------------------------------------------------------------------
# 10. 停止與清除
# ------------------------------------------------------------------
# 資料在 ./sqldata、./redis_data，刪除容器不會刪資料；secrets 和網路也會保留
podman rm -f vcl_tunnel vclnginx core_pj mariadb_db vclredis
# 連網路一起清掉（要重建時再從步驟 3 開始）
podman network rm frontend backend_redis
