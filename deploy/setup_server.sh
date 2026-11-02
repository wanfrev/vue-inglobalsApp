#!/usr/bin/env bash
# Monta TODO el simulador en un servidor Ubuntu nuevo (22.04 o 24.04) y, si le
# das un respaldo, restaura los datos (bibliografía indexada, historial, .env,
# certificados SSL y configuración de Nginx).
#
# Uso, COMO ROOT en el servidor nuevo (después de copiar el respaldo con scp):
#
#   apt-get update && apt-get install -y git
#   git clone https://github.com/wanfrev/vue-inglobalsApp.git /root/vue-inglobalsApp
#   bash /root/vue-inglobalsApp/deploy/setup_server.sh /root/respaldo2.tgz
#
# Sin respaldo (servidor limpio, tendrás que crear el .env y reindexar):
#   bash /root/vue-inglobalsApp/deploy/setup_server.sh
#
# Variables opcionales: DOMAIN (default inglobals.com), APP_USER (default
# inglobals). Es seguro volver a correrlo: salta lo que ya está hecho.
#
# NO está probado de punta a punta en un servidor limpio: los pasos replican
# los de DEPLOY_VPS.md, que sí se usaron a mano. Si algo falla, el mensaje de
# error dice en qué paso; corrige y vuelve a correrlo.

set -euo pipefail

BACKUP="${1:-}"
DOMAIN="${DOMAIN:-inglobals.com}"
APP_USER="${APP_USER:-inglobals}"
REPO_URL="https://github.com/wanfrev/vue-inglobalsApp.git"
HOME_DIR="/home/$APP_USER"
APP_DIR="$HOME_DIR/vue-inglobalsApp"
export DEBIAN_FRONTEND=noninteractive

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: corre este script como root (sudo -i)."; exit 1
fi
if [ -n "$BACKUP" ] && [ ! -f "$BACKUP" ]; then
    echo "ERROR: no existe el respaldo $BACKUP"; exit 1
fi

step() { echo; echo "==> $*"; }

step "1/9 Paquetes del sistema"
apt-get update
apt-get install -y python3-venv python3-pip git nginx certbot python3-certbot-nginx ufw curl build-essential
if ! command -v node >/dev/null || [ "$(node -v | cut -d. -f1 | tr -d v)" -lt 22 ]; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi

step "2/9 Swap de 4 GB y firewall"
if [ -z "$(swapon --show --noheadings)" ]; then
    fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
ufw allow OpenSSH >/dev/null; ufw allow 80 >/dev/null; ufw allow 443 >/dev/null
ufw --force enable

step "3/9 Usuario $APP_USER"
if ! id "$APP_USER" >/dev/null 2>&1; then
    adduser --disabled-password --gecos "" "$APP_USER"
    usermod -aG sudo "$APP_USER"
    echo "    >>> Al terminar, ponle contraseña con:  passwd $APP_USER"
fi
# Ubuntu 22.04+ crea el home cerrado (750): Nginx necesita poder atravesarlo.
chmod o+x "$HOME_DIR"

step "4/9 Código"
if [ ! -d "$APP_DIR/.git" ]; then
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
else
    sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
fi

step "5/9 Restaurar datos del respaldo"
if [ -n "$BACKUP" ]; then
    R="$(mktemp -d)"
    tar xzf "$BACKUP" -C "$R"
    B="$APP_DIR/backend"
    if [ -d "$R/home/$APP_USER/vue-inglobalsApp/backend/data" ]; then
        # Formato "rescate" (respaldo.tgz / respaldo2.tgz hechos desde el rescate).
        cp -a "$R/home/$APP_USER/vue-inglobalsApp/backend/data" "$B/"
        [ -f "$R/home/$APP_USER/vue-inglobalsApp/backend/.env" ] && cp "$R/home/$APP_USER/vue-inglobalsApp/backend/.env" "$B/.env"
    elif [ -f "$R/sqlite_backup.db" ]; then
        # Formato de deploy/backup.sh.
        mkdir -p "$B/data"
        cp "$R/sqlite_backup.db" "$B/data/sqlite.db"
        [ -d "$R/chroma" ] && cp -a "$R/chroma" "$B/data/"
        [ -d "$R/uploads" ] && cp -a "$R/uploads" "$B/data/"
        [ -f "$R/.env" ] && cp "$R/.env" "$B/.env"
    else
        echo "ERROR: el respaldo no tiene el formato esperado."; exit 1
    fi
    chown -R "$APP_USER:$APP_USER" "$B/data"
    [ -f "$B/.env" ] && chown "$APP_USER:$APP_USER" "$B/.env" && chmod 600 "$B/.env"
    # Certificados SSL y Nginx del servidor anterior (valen mientras el dominio
    # apunte a este servidor).
    [ -d "$R/etc/letsencrypt" ] && cp -a "$R/etc/letsencrypt" /etc/
    [ -f "$R/etc/nginx/sites-available/inglobals" ] && cp "$R/etc/nginx/sites-available/inglobals" /etc/nginx/sites-available/inglobals
    rm -rf "$R"
else
    echo "    (sin respaldo: crea $APP_DIR/backend/.env a mano y reindexa la bibliografía)"
fi

step "6/9 Backend (Python, PyTorch solo-CPU, modelo de embeddings)"
sudo -u "$APP_USER" bash -c "
    set -e
    cd '$APP_DIR/backend'
    [ -d venv ] || python3 -m venv venv
    source venv/bin/activate
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt
    python -c \"from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); from app.main import app; print('BACKEND OK')\"
"

step "7/9 Frontend y landing"
sudo -u "$APP_USER" bash -c "
    set -e
    export NODE_OPTIONS='--max-old-space-size=1536'
    cd '$APP_DIR/frontend'
    echo 'VITE_API_BASE_URL=https://$DOMAIN' > .env.production
    npm install
    nice -n 10 timeout 900 npm run build
    cd '$APP_DIR/landing'
    echo 'PUBLIC_SIMULATOR_URL=https://$DOMAIN/simulador' > .env.production
    npm install
    nice -n 10 timeout 900 npm run build
"

step "8/9 Servicio del backend"
cp "$APP_DIR/deploy/inglobals-backend.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now inglobals-backend
sleep 6
systemctl is-active inglobals-backend
curl -s http://127.0.0.1:8000/api/v1/health; echo

step "9/9 Nginx y respaldo diario"
if [ ! -f /etc/nginx/sites-available/inglobals ]; then
    cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/inglobals
    echo "    Nginx sin HTTPS todavía: cuando el DNS de $DOMAIN apunte aquí, corre:"
    echo "      certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi
grep -q 'client_max_body_size 25m' /etc/nginx/sites-available/inglobals || \
    sed -i 's|location /api/ {|location /api/ {\n        client_max_body_size 25m;|' /etc/nginx/sites-available/inglobals
ln -sf /etc/nginx/sites-available/inglobals /etc/nginx/sites-enabled/inglobals
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

sudo -u "$APP_USER" mkdir -p "$HOME_DIR/backups"
CRON='30 3 * * * bash $HOME/vue-inglobalsApp/deploy/backup.sh >> $HOME/backups/backup.log 2>&1'
( sudo -u "$APP_USER" crontab -l 2>/dev/null | grep -v 'deploy/backup.sh' || true; echo "$CRON" ) | sudo -u "$APP_USER" crontab -

echo
echo "LISTO. Pendiente: 1) passwd $APP_USER   2) apuntar el DNS de $DOMAIN a la IP de este servidor"
echo "          3) si no restauraste certificados: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "          4) verificar https://$DOMAIN/simulador/"
