# create network
podman network create frontend --subnet 10.101.1.2/24 --gateway 10.101.1.1

# create pod
# -p => show port for local connection
# --network => connecct network of podman 
podman pod craete --name vcl-pod --network frontend -p 8080:8080 -p 8443:8443


# start ubi container
# -e core_project => define core project name
# --userns keep-id => make container and host both can to modify program for develop
# -v /app:Z => define program folder : project_folder/src/project_name 
# U => Podman 會執行一個 chown 的動作，將主機目錄的擁有者改為容器內 appCore 對應的系統 UID。
#   主機視角：如果你進去容器看 appCore 是 UID 1000，但在 Rootless 模式下，這個 1000 在主機上可能會被映射成 101000。
#   結果：主機端的 gerald (1000) 突然發現 main.py 的擁有者變成了 101000，所以對你來說它就變成了「唯讀」。
podman run -d --name testpy -e core_project=coreVcl --network frontend --userns keep-id -v $(pwd)/coreVcl:/app:Z,U localhost/my-ubi-python:latest

# start nginx
# -v => standalone.conf: /etc/nginx/nginx.conf
# -v => nginx_conf/web/html:/opt/app-root/src:Z,ro -> web server
# -v => nginx_conf/conf/cerf/certs:/etc/nginx/certs:Z,ro
# nginx -g "daemon off;"
podman run -d --name vclnginx --pod vcl-pod  -v /home/gerald/DataHD/homeHD1/CodeProject/github/portfolio/cie1931/my_portfolio/server-vcl/nginx_conf/conf/nginx/standalone.conf:/etc/nginx/nginx.conf:Z -v /home/gerald/DataHD/homeHD1/CodeProject/github/portfolio/cie1931/my_portfolio/server-vcl/nginx_conf/web/html/:/opt/app-root/src:Z,ro -v /home/gerald/DataHD/homeHD1/CodeProject/github/portfolio/cie1931/my_portfolio/server-vcl/nginx_conf/conf/certs:/etc/nginx/certs:Z,ro registry.redhat.io/ubi8/nginx-122:latest nginx -g "daemon off;"

# start cloudflare 
# currently for develop
# --no-tls-verify -> ignore SSL license
podman run --rm --pod vcl-pod --name vcl-test-tunnel \
  docker.io/cloudflare/cloudflared:latest \
  tunnel --url https://localhost:8443 --no-tls-verify



