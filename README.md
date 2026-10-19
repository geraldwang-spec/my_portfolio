# Vision Color Lab

A self-hosted portfolio platform for manufacturing quality tools: camera focus
inspection, LED color checks (CIE 1931) and quality data, built on Flask and
rootless Podman and published through Cloudflare Tunnel.

**Status: work in progress.** Working today: sign-up, login, email
verification and password reset. Next: PostgreSQL with Alembic migrations, then
the focus inspection API.

## Architecture

```text
 Browser
    |  HTTPS (Cloudflare edge certificate)
    v
 +------------------+
 |    Cloudflare    |
 +--------+---------+
          |  Cloudflare Tunnel: outbound-only, no inbound ports on the host
==========|============================================ host: rootless Podman ===
          v
 +------------------+
 |   vcl_tunnel     |  cloudflared
 +--------+---------+
          |  HTTPS :8443 (self-signed, same host)        network: frontend
          v
 +------------------+
 |    vclnginx      |  TLS, real client IP, rate limiting, /static/
 +--------+---------+
          |  HTTP :5000
          v
 +------------------+
 |     core_pj      |  Flask + SQLAlchemy (UBI 9, Python 3.11)
 +---+----------+---+
     |          |                                    network: backend_redis
     v          v
 +---------+  +---------+
 | MariaDB |  |  Redis  |
 +---------+  +---------+
   users       password reset codes (TTL)
```

- **No inbound ports.** cloudflared opens an outbound connection to Cloudflare,
  so the host's firewall only needs SSH.
- **Two networks.** The databases sit on `backend_redis` only and publish no
  ports to the public interface; nginx and the tunnel cannot reach them.
- **Secrets** are Podman secrets mounted at `/run/secrets/<name>`, never stored
  in the repo, `.env` or compose files.
- **Real client IP.** nginx trusts `X-Forwarded-For` only from the tunnel's
  network, so rate limiting is per user rather than per tunnel.

## Repository layout

```text
coreVcl/              Flask app (auth, templates, static JS/CSS)
server-vcl/           nginx config, self-signed cert script, manual setup notes
Containerfile         Python 3.11 image on UBI 9
podman-compose.yaml   all services for local development
deplay.sh             one-command setup: pull images, create certs, start services
```

## Quick start (development)

Requirements: Podman 4.5+, podman-compose, OpenSSL and a free Red Hat account
(for `registry.redhat.io`). Runs on x86_64 and ARM64.

1. Create `.env` from the template and fill in the values:

   ```bash
   cp .env.example .env
   ```

   ```ini
   BACKEND_SUBNET=10.66.0.0/24
   BACKEND_GATEWAY=10.66.0.1
   REDIS_IP=10.66.0.3
   MYSQL_USER=vcl
   MYSQL_DATABASE=vision_db
   MARIADB_IP=10.66.0.4
   MAIL_USERNAME=you@example.com
   # Optional. Leave empty to use the quick tunnel's random URL.
   PUBLIC_BASE_URL=
   ```

2. Create the secrets once. Generated passwords never appear in a command,
   a file or your shell history:

   ```bash
   for s in mysql_password mysql_root_password redis_password secret_key; do
     podman secret exists "$s" || printf '%s' "$(openssl rand -hex 24)" | podman secret create "$s" -
   done
   read -rs -p "mail password: " MAIL_PASSWORD; echo
   printf '%s' "$MAIL_PASSWORD" | podman secret create mail_password -
   unset MAIL_PASSWORD
   ```

3. Start everything:

   ```bash
   ./deplay.sh
   ```

4. Install Python packages and run Flask inside the app container:

   ```bash
   podman exec core_pj python3 -m pip install --user -r requirements.txt
   podman exec -it core_pj python3 app.py
   ```

5. Find the public URL:

   ```bash
   podman logs vcl_tunnel 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com'
   ```

Stop everything with `podman-compose -p vcl down`. Data in `./sqldata` and
`./redis_data` is kept.

> **Development only.** `app.py` runs Flask's built-in server with
> `debug=True`. Do not expose it through a tunnel for longer than a test session.

To create each container by hand instead of using compose, see
[`server-vcl/readme.txt`](server-vcl/readme.txt).

## License

[MIT](LICENSE)
