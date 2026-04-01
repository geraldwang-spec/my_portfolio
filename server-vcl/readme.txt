# create network
podman network create frontend --subnet 10.101.1.2/24 --gateway 10.101.1.1

# create pod
# -p => show port for local connection
# --network => connecct network of podman 
podman pod craete --name vcl-pod --network frontend -p 8080:8080 -p 8443:8443


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
