# 手動建立容器的指令參考（compose 以外的做法）
# 指令都在 repo 根目錄執行。路徑一律用 ./ 開頭：
#   Podman 的 -v 來源如果沒有 "/"（例如 coreVcl），會被當成「named volume 名稱」，
#   而不是資料夾，結果掛進去的是一個空的 volume。

# pull images
registry.redhat.io/ubi9/ubi
registry.redhat.io/ubi8/nginx-122
docker.io/cloudflare/cloudflared
registry.redhat.io/rhel9/postgresql-16
registry.redhat.io/rhel9/redis-7

# 產生 nginx 用的自簽憑證（只在本機，不進 git；第一次或要換金鑰時執行）
./server-vcl/gen-selfsigned-cert.sh

# 建立密碼（Podman secrets，只要做一次；密碼不寫在指令、檔案或 shell 歷史裡）
printf '%s' "$(openssl rand -hex 24)" | podman secret create redis_password -
printf '%s' "$(openssl rand -hex 24)" | podman secret create pg_password -

# create network（subnet 要寫網段位址 .0/24）
podman network create frontend --subnet 10.101.1.0/24 --gateway 10.101.1.1
podman network create backend_redis --subnet 10.66.0.0/24 --gateway 10.66.0.1

# create pod
# -p => 只綁 127.0.0.1：本機測試用，區網和外網連不到（對外一律走 tunnel）
# --network => connect network of podman
podman pod create --name vcl-pod --network frontend -p 127.0.0.1:8080:8080 -p 127.0.0.1:8443:8443

# create redis
# --ip => 10.66.0.3 for freeze ip address
# --secret ...,type=env => 把 secret 當環境變數 REDIS_PASSWORD 給容器
# -v => for store data to host
podman run -d --name vclredis --network backend_redis --ip 10.66.0.3 \
  --secret redis_password,type=env,target=REDIS_PASSWORD \
  -v redis_data:/var/lib/redis/data:Z \
  registry.redhat.io/rhel9/redis-7:latest

# create postgresql
# --ip 10.66.0.4（原本跟 redis 一樣是 .3，會衝突）
# -v ./sqldata => 主機資料夾；rootless 下容器內 postgres 是 UID 26，需要 :U 讓它可寫
#   （正式環境可改成先執行一次 podman unshare chown -R 26:26 ./sqldata，再只用 :Z）
podman run -d --name pgsql_db --network backend_redis --ip 10.66.0.4 \
  -e POSTGRESQL_USER=vcl -e POSTGRESQL_DATABASE=vision_db \
  --secret pg_password,type=env,target=POSTGRESQL_PASSWORD \
  -v ./sqldata:/var/lib/pgsql/data:Z,U \
  registry.redhat.io/rhel9/postgresql-16:latest


# start ubi container
# --name core_pj => standalone.conf 的 proxy_pass 指向 core_pj，名稱要一致，否則 nginx 起不來
# -e core_project => define core project name
# --userns keep-id => make container and host both can to modify program for develop
# -v ./coreVcl:/app:Z => 開發時把程式掛進容器，主機上改、容器內同步
# U => Podman 會執行一個 chown 的動作，將主機目錄的擁有者改為容器內 appCore 對應的系統 UID。
#   主機視角：如果你進去容器看 appCore 是 UID 1000，但在 Rootless 模式下，這個 1000 在主機上可能會被映射成 101000。
#   結果：主機端的 gerald (1000) 突然發現 main.py 的擁有者變成了 101000，所以對你來說它就變成了「唯讀」。
#   用了 --userns keep-id 時，容器內 UID 1000 就是主機的你，通常不需要 U。
podman run -d --name core_pj -e core_project=coreVcl --network frontend --network backend_redis \
  --userns keep-id -v ./coreVcl:/app:Z localhost/my-ubi-python:latest

# 檢查 nginx 設定（改完 standalone.conf 先跑這個，通過再重啟）
# label=disable：臨時容器不改 SELinux 標籤，避免正在跑的 vclnginx 讀不到檔案
podman run --rm --security-opt label=disable --network frontend \
  -v ./server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:ro \
  -v ./server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:ro \
  registry.redhat.io/ubi8/nginx-122:latest nginx -t

# start nginx
# -v => standalone.conf: /etc/nginx/nginx.conf
# -v => coreVcl/static:/opt/app-root/src/static:Z,ro -> 靜態檔由 nginx 直接回應
# -v => nginx_conf/conf/certs:/etc/nginx/certs:Z,ro
# nginx -g "daemon off;"
podman run -d --name vclnginx --pod vcl-pod \
  -v ./server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:Z \
  -v ./coreVcl/static:/opt/app-root/src/static:Z,ro \
  -v ./server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:Z,ro \
  registry.redhat.io/ubi8/nginx-122:latest nginx -g "daemon off;"

# start cloudflare
# currently for develop（quick tunnel：每次啟動網址都會變）
# --no-tls-verify -> 不驗證 nginx 的自簽憑證（tunnel -> nginx 在同一台主機）
podman run --rm --pod vcl-pod --name vcl-test-tunnel \
  docker.io/cloudflare/cloudflared:latest \
  tunnel --url https://localhost:8443 --no-tls-verify

# 雲端 VM：不用 pod 時的做法
# -p 只綁 127.0.0.1，外網連不到 nginx，只有同主機的 tunnel（--network host）連得到
podman run -d --name vclnginx --network frontend -p 127.0.0.1:8080:8080 -p 127.0.0.1:8443:8443 \
  -v ./server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:Z \
  -v ./coreVcl/static:/opt/app-root/src/static:Z,ro \
  -v ./server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:Z,ro \
  registry.redhat.io/ubi8/nginx-122:latest nginx -g "daemon off;"

# work on VM
podman run --rm --network host --name vcl-test-tunnel \
  docker.io/cloudflare/cloudflared:latest \
  tunnel --protocol http2 --url https://127.0.0.1:8443 --no-tls-verify
