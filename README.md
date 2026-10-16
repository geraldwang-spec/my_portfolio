# my_portfolio
# setting env by .env.example
MYSQL_USER => define sql user name
MYSQL_DATABASE => define database name
MAIL_USERNAME => define mail user name

# setting import passowrd by user
printf '%s' "$MYSQL_PASSWORD"      | podman secret create mysql_password -
printf '%s' "$MYSQL_ROOT_PASSWORD" | podman secret create mysql_root_password -
printf '%s' "$REDIS_PASSWORD"      | podman secret create redis_password -
printf '%s' "$SECRET_KEY"          | podman secret create secret_key -
printf '%s' "$MAIL_PASSWORD"       | podman secret create mail_password -
