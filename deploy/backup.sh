#!/usr/bin/env bash
# Respaldo de los datos del simulador (lo único que NO está en git):
#   - base de datos SQLite (sesiones e historial de consultas)
#   - índice FAISS de la bibliografía y sus metadatos
#   - documentos subidos (uploads, incluidos los PDF originales de las leyes)
#   - el .env (claves de API)
#
# Uso (en el VPS):
#   bash ~/vue-inglobalsApp/deploy/backup.sh
#
# Para que corra solo cada madrugada (3:30 am), agrega esta línea con
# `crontab -e` (como el usuario inglobals):
#   30 3 * * * bash $HOME/vue-inglobalsApp/deploy/backup.sh >> $HOME/backups/backup.log 2>&1
#
# Guarda los últimos 7 respaldos en ~/backups. IMPORTANTE: un respaldo en el
# mismo servidor no te salva si el servidor deja de arrancar — baja una copia
# a tu PC de vez en cuando (desde PowerShell en tu PC):
#   scp inglobals@IP_DEL_VPS:backups/inglobals-*.tgz C:\respaldo_inglobals\
#
# El archivo contiene claves (.env): no lo subas a git ni lo compartas.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND="$REPO_ROOT/backend"
DATA="$BACKEND/data"
DEST="${BACKUP_DIR:-$HOME/backups}"
KEEP="${KEEP:-7}"
STAMP="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$DEST"
chmod 700 "$DEST"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) SQLite: con el modo WAL activo no basta copiar el archivo; la API de
#    backup de sqlite3 genera una copia consistente aunque haya consultas.
python3 - "$DATA/sqlite.db" "$TMP/sqlite_backup.db" <<'PY'
import sqlite3
import sys

src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close()
src.close()
PY

# 2) Índice FAISS: se copia bajo el mismo candado que usa el backend para
#    escribirlo, así no se captura a medias una subida de documentos.
if [ -d "$DATA/chroma" ]; then
    flock "$DATA/chroma/faiss.lock" cp -a "$DATA/chroma" "$TMP/chroma"
    rm -f "$TMP/chroma/faiss.lock"
fi

# 3) Todo junto en un solo archivo.
ARCHIVE="$DEST/inglobals-$STAMP.tgz"
INCLUDE=("-C" "$TMP" "sqlite_backup.db")
[ -d "$TMP/chroma" ] && INCLUDE+=("chroma")
[ -d "$DATA/uploads" ] && INCLUDE+=("-C" "$DATA" "uploads")
[ -f "$BACKEND/.env" ] && INCLUDE+=("-C" "$BACKEND" ".env")
tar czf "$ARCHIVE" "${INCLUDE[@]}"
chmod 600 "$ARCHIVE"

# 4) Conserva solo los últimos $KEEP.
ls -1t "$DEST"/inglobals-*.tgz | tail -n +"$((KEEP + 1))" | xargs -r rm -f

echo "$(date '+%F %T') OK  $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

# Para restaurar en un servidor nuevo (con el repo ya clonado):
#   tar xzf inglobals-FECHA.tgz -C /tmp/restaurar
#   cp /tmp/restaurar/sqlite_backup.db  backend/data/sqlite.db
#   cp -a /tmp/restaurar/chroma         backend/data/
#   cp -a /tmp/restaurar/uploads        backend/data/
#   cp /tmp/restaurar/.env              backend/.env
