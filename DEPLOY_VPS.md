# Desplegar en un VPS propio (Namecheap Quasar)

Guía paso a paso para montar el Simulador DAD en un VPS Ubuntu (Quasar: 4 CPU
/ 6GB RAM / 120GB SSD), sin Vercel/Render/Railway ni panel de control
(cPanel/Webuzo) — solo SSH, Nginx y systemd.

Todos los comandos de este documento se ejecutan **dentro del VPS por SSH**,
no en tu PC con Windows (salvo que se indique lo contrario).

---

## 0. Antes de empezar — la bibliografía ya NO viaja por git

Las carpetas de bibliografía (`Bibliografia*`, `Biblioteca_*`,
`bibliografa_diplomado`, `Sostenibilidad_nacioanl`, `Fuentes_Web`) están
ahora en `.gitignore` y fueron sacadas del tracking de git (`git rm
--cached`) — quedan en tu disco local pero ya no se suben en los próximos
commits. Por eso `git clone` en el VPS NO las va a traer: hay que subirlas
aparte por `scp`/`rsync` (ver paso 5).

**Importante:** esto solo evita que seguros commits futuros las incluyan. Los
commits viejos que ya se subieron a GitHub siguen teniendo esos ~180MB en su
historial (varios documentos con derechos de autor de terceros — manuales
IFAC/IESBA/ISO, no leyes públicas). Si ese repositorio es público, sigue
expuesto por el historial aunque el estado actual ya no las liste. Si quieres
borrarlas también del historial (reescribe todos los commits, requiere force
push) dímelo aparte — es una operación irreversible y la hago solo si me la
pides explícitamente. La alternativa simple: pasar el repo a privado en
GitHub (Settings → Danger Zone → Change visibility), un clic, sin tocar el
historial.

---

## 1. Conectarte al VPS

Namecheap te da una IP y una contraseña de root por correo al aprovisionar el
Quasar. Desde PowerShell en tu PC:

```bash
ssh root@TU_IP_DEL_VPS
```

## 2. Configuración inicial del servidor

```bash
apt update && apt upgrade -y

# Usuario sin privilegios de root para correr la app (buena práctica, nunca
# corras servicios de internet como root)
adduser inglobals
usermod -aG sudo inglobals

# Firewall: solo SSH, HTTP y HTTPS abiertos al mundo
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable
```

Cierra esta sesión y vuelve a entrar ya como el usuario nuevo:

```bash
ssh inglobals@TU_IP_DEL_VPS
```

## 3. Instalar dependencias del sistema

```bash
sudo apt install -y python3.12 python3.12-venv python3-pip git nginx certbot python3-certbot-nginx

# Node.js 20 LTS (para compilar el frontend directamente en el servidor)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

## 4. Clonar el repositorio

```bash
cd ~
git clone https://github.com/wanfrev/vue-inglobalsApp.git
cd vue-inglobalsApp
```

Si el repo es privado, git te pedirá autenticación — usa un [personal access
token](https://github.com/settings/tokens) de GitHub como contraseña (no tu
contraseña de la cuenta).

## 5. Subir la bibliografía (desde tu PC, no por SSH)

Este paso se corre en **PowerShell/Git Bash de tu PC Windows**, no dentro del
VPS. Copia las 7 carpetas a la raíz del proyecto ya clonado en el servidor:

```bash
cd "C:\Users\wanfr\OneDrive\Documents\Commit\vue-inglobalsApp"
scp -r Bibliografia Bibliografia_pocesos_contables_sector_publico_vzla Biblioteca_Leyes_Vzla Biblioteca_colegio_contadores_publicos bibliografa_diplomado Sostenibilidad_nacioanl Fuentes_Web inglobals@TU_IP_DEL_VPS:~/vue-inglobalsApp/
```

Va a pedirte la contraseña del usuario `inglobals` y tardará varios minutos
(son ~180MB). Una vez termine, vuelve a la sesión SSH del VPS para seguir.

## 6. Backend

```bash
cd ~/vue-inglobalsApp/backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Crea el `.env` de producción (no se sube por git, así que hay que crearlo a
mano cada vez que montes un servidor nuevo):

```bash
nano .env
```

Pega esto, reemplazando `TU_DOMINIO.com` por tu dominio real y `AI_API_KEY`
por la misma clave de Gemini que ya usas en local (está en tu
`backend\.env` de Windows):

```
AI_API_KEY=tu_clave_real_de_gemini_aqui
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
AI_MODEL=gemini-3.6-flash
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=4000
AI_PRICE_INPUT_PER_1M=0.75
AI_PRICE_OUTPUT_PER_1M=3.75
CORS_ORIGINS=https://TU_DOMINIO.com,https://www.TU_DOMINIO.com
```

Guarda con `Ctrl+O`, Enter, y sal con `Ctrl+X`.

No hace falta tocar `DATA_DIR` — a diferencia de Render, en un VPS el disco
es tuyo y persistente, así que el valor por defecto (`backend/data`) ya
sirve.

Indexa la bibliografía (la primera vez descarga el modelo de embeddings,
~80MB, y tarda varios minutos en procesar los ~180MB de PDFs):

```bash
python scripts/ingest_knowledge_base.py
```

Verifica que arranca bien antes de seguir:

```bash
python -c "from app.main import app; print('OK, la app importa sin errores')"
deactivate
```

## 7. Frontend

```bash
cd ~/vue-inglobalsApp/frontend
```

Crea el `.env.production` con el dominio real (Vite lo incrusta en el build,
por eso tiene que existir ANTES de compilar):

```bash
echo "VITE_API_BASE_URL=https://TU_DOMINIO.com" > .env.production
```

```bash
npm install
npm run build
```

Esto genera `frontend/dist/` — son los archivos estáticos que Nginx va a
servir directamente.

## 8. Servicio systemd del backend

```bash
sudo cp ~/vue-inglobalsApp/deploy/inglobals-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable inglobals-backend
sudo systemctl start inglobals-backend
sudo systemctl status inglobals-backend
```

Deberías ver `active (running)`. Si no, revisa los logs:

```bash
sudo journalctl -u inglobals-backend -n 50 --no-pager
```

## 9. Nginx

```bash
sudo cp ~/vue-inglobalsApp/deploy/nginx.conf /etc/nginx/sites-available/inglobals
sudo nano /etc/nginx/sites-available/inglobals
```

Reemplaza las dos apariciones de `TU_DOMINIO.com` por tu dominio real, guarda
y sal. Luego:

```bash
sudo ln -s /etc/nginx/sites-available/inglobals /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

`nginx -t` debe decir "syntax is ok" y "test is successful" antes de seguir.

## 10. Apuntar el dominio y activar HTTPS

Antes de este paso, en el panel de DNS de Namecheap (o donde tengas el
dominio), crea un registro **A** apuntando `TU_DOMINIO.com` y
`www.TU_DOMINIO.com` a la IP del VPS. Espera unos minutos a que propague
(puedes verificar con `nslookup TU_DOMINIO.com` desde tu PC).

Con eso propagado:

```bash
sudo certbot --nginx -d TU_DOMINIO.com -d www.TU_DOMINIO.com
```

Certbot va a pedirte un correo y reescribir el Nginx config para servir por
HTTPS automáticamente (incluye la renovación automática del certificado, no
hay que hacer nada más después).

## 11. Verificar

Desde tu navegador: `https://TU_DOMINIO.com` debería cargar el Simulador DAD.
Escribe una consulta de prueba y confirma que responde.

Desde el VPS, para ver logs en vivo mientras pruebas:

```bash
sudo journalctl -u inglobals-backend -f
```

---

## Cómo actualizar el proyecto después de este primer despliegue

Cada vez que hagas cambios y quieras subirlos:

```bash
cd ~/vue-inglobalsApp
git pull

cd backend
source venv/bin/activate
pip install -r requirements.txt   # solo si cambiaron dependencias
deactivate
sudo systemctl restart inglobals-backend

cd ../frontend
npm install                        # solo si cambiaron dependencias
npm run build
```

No hace falta tocar Nginx ni systemd de nuevo salvo que cambies rutas o
puertos.

Si agregas documentos nuevos a la bibliografía, no viajan por `git pull` (ver
paso 0): vuelve a correr el `scp` del paso 5 solo para la carpeta que cambió,
y luego `python scripts/ingest_knowledge_base.py` en el VPS — el script se
salta los archivos que ya estaban indexados, así que es seguro correrlo de
nuevo.
