#!/usr/bin/env bash
# Actualiza el simulador en el VPS con un solo comando: trae el código nuevo,
# reinstala dependencias, recompila frontend + landing, y reinicia el
# backend. Uso (desde cualquier carpeta, en el VPS):
#
#   bash ~/vue-inglobalsApp/deploy/update.sh
#
# Pensado para actualizaciones normales, DESPUÉS del primer despliegue
# completo (ver DEPLOY_VPS.md). No sirve para el setup inicial (asume que
# backend/venv, frontend/node_modules y landing/node_modules ya existen).
#
# A propósito NO toca:
#   - La bibliografía: viaja por scp aparte, no por git (ver paso 0/5 de
#     DEPLOY_VPS.md). Si agregaste documentos nuevos, sube la carpeta que
#     cambió y corre `python scripts/ingest_knowledge_base.py` tú mismo.
#   - El Nginx vivo: certbot ya lo modificó con los bloques HTTPS —
#     sobrescribirlo con deploy/nginx.conf se los borraría. Si ese archivo
#     cambió en el pull, este script te avisa al final para que lo revises
#     y apliques el cambio a mano.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Pide (y cachea) la contraseña de sudo de una vez al principio, en vez de
# fallar a medio camino si se escribe mal más adelante.
sudo -v

echo "==> Repositorio: $REPO_ROOT"
BEFORE_REV="$(git rev-parse HEAD)"

echo "==> git pull"
git pull --ff-only

AFTER_REV="$(git rev-parse HEAD)"
if [ "$BEFORE_REV" = "$AFTER_REV" ]; then
    echo "==> Sin cambios nuevos (ya estabas al día) — igual se reinstala/recompila todo por si acaso."
else
    echo "==> Cambios traídos: ${BEFORE_REV:0:7} -> ${AFTER_REV:0:7}"
fi
CHANGED_FILES="$(git diff --name-only "$BEFORE_REV" "$AFTER_REV" || true)"

echo ""
echo "==> Backend: dependencias"
cd "$REPO_ROOT/backend"
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd "$REPO_ROOT"

echo ""
echo "==> Backend: servicio systemd"
sudo cp "$REPO_ROOT/deploy/inglobals-backend.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart inglobals-backend
sleep 1
if sudo systemctl is-active --quiet inglobals-backend; then
    echo "    backend: active (running)"
else
    echo "    ERROR: el backend no quedó activo. Revisa:"
    echo "      sudo journalctl -u inglobals-backend -n 50 --no-pager"
    exit 1
fi

echo ""
echo "==> Frontend (simulador)"
cd "$REPO_ROOT/frontend"
npm install
npm run build
cd "$REPO_ROOT"

echo ""
echo "==> Landing (Astro)"
cd "$REPO_ROOT/landing"
npm install
npm run build
cd "$REPO_ROOT"

echo ""
if echo "$CHANGED_FILES" | grep -qx "deploy/nginx.conf"; then
    echo "==> AVISO: deploy/nginx.conf cambió en este pull."
    echo "    El archivo vivo (/etc/nginx/sites-enabled/inglobals) ya fue modificado por"
    echo "    certbot con los bloques HTTPS — sobrescribirlo con este lo rompería."
    echo "    Revisa la diferencia y aplica el cambio a mano:"
    echo "      diff /etc/nginx/sites-enabled/inglobals $REPO_ROOT/deploy/nginx.conf"
fi
if echo "$CHANGED_FILES" | grep -qx "backend/requirements.txt\|backend/scripts/ingest_knowledge_base.py"; then
    echo "==> AVISO: cambió requirements.txt o el script de ingesta."
    echo "    Si el cambio afecta el índice RAG, puede valer la pena correr de nuevo:"
    echo "      cd backend && source venv/bin/activate && python scripts/ingest_knowledge_base.py"
fi

echo ""
echo "==> Listo. Todo actualizado y corriendo."
