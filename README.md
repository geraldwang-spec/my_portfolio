# my_portfolio
# auto operate
./deplay.sh

# manual operate
# 1. setting env by .env.example
# -- backend ---
BACKEND_SUBNET=setting backend subnet ip
BACKEND_GATEWAY=setting backend gateway

# --- redis ---
REDIS_IP=setting redis ip

# --- Mariadb ---
MYSQL_USER=sql username
MYSQL_DATABASE=sql database
MARIADB_IP= sql server ip

# ---  Mail ---
MAIL_USERNAME=seting mail username

# cloudflare url
PUBLIC_BASE_URL=setting cloudflare fix url

# setting import passowrd by user
printf '%s' "$MYSQL_PASSWORD"      | podman secret create mysql_password -
printf '%s' "$MYSQL_ROOT_PASSWORD" | podman secret create mysql_root_password -
printf '%s' "$REDIS_PASSWORD"      | podman secret create redis_password -
printf '%s' "$SECRET_KEY"          | podman secret create secret_key -
printf '%s' "$MAIL_PASSWORD"       | podman secret create mail_password -

# 2. general nginx ssl
./server-vcl/gen-selfsigned-cert.sh

# 3. launch all container
podman-compose -p vcl -f podman-compose.yaml up -d

# 4. start flask
podman exec -it core_pj pyhton3 app.py

# 5. stop all container
podman-compose -p vcl -f podman-compose.yaml down
