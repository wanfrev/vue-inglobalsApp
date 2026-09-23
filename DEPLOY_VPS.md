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

# Node.js 22 LTS (para compilar el frontend/landing directamente en el
# servidor). Con Node 20, el toolchain de Astro 5.17.x (undici, sharp) tira
# EBADENGINE y sharp no logra resolver su binario nativo — verificado en el
# VPS de producción.
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
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

Pega esto, reemplazando `AI_API_KEY` por la misma clave de Gemini que ya usas
en local (está en tu `backend\.env` de Windows). El simulador vive en
`inglobals.com/simulador` (mismo dominio que la landing, no un subdominio
aparte), así que `CORS_ORIGINS` es el dominio raíz:

```
AI_API_KEY=tu_clave_real_de_gemini_aqui
AI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
AI_MODEL=gemini-3.6-flash
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=4000
AI_PRICE_INPUT_PER_1M=0.75
AI_PRICE_OUTPUT_PER_1M=3.75
CORS_ORIGINS=https://inglobals.com,https://www.inglobals.com
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

## 7. Frontend (Simulador Vue → app.inglobals.com)

```bash
cd ~/vue-inglobalsApp/frontend
```

Crea el `.env.production` con el dominio real (Vite lo incrusta en el
build, por eso tiene que existir ANTES de compilar). El simulador vive bajo
`/simulador` del mismo dominio (no un subdominio), así que la API base es el
dominio raíz:

```bash
echo "VITE_API_BASE_URL=https://inglobals.com" > .env.production
```

```bash
npm install
npm run build
```

Esto genera `frontend/dist/` — son los archivos estáticos que Nginx va a
servir bajo `/simulador/` (`vite.config.js` ya tiene `base: '/simulador/'`
configurado, por eso los assets compilados van a referenciarse con ese
prefijo).

## 8. Landing (Astro → inglobals.com)

Sitio de marketing, 100% estático — no necesita systemd ni un proceso Node
corriendo, solo compilarlo una vez:

```bash
cd ~/vue-inglobalsApp/landing
echo "PUBLIC_SIMULATOR_URL=https://inglobals.com/simulador" > .env.production
npm install
npm run build
```

Esto genera `landing/dist/`. El botón "SIMULADOR" de `iyf.astro` ya apunta a
esa variable.

## 9. Servicio systemd del backend

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

## 10. Nginx (un solo dominio, dos apps)

```bash
sudo cp ~/vue-inglobalsApp/deploy/nginx.conf /etc/nginx/sites-available/inglobals
sudo ln -s /etc/nginx/sites-available/inglobals /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Si tu dominio no es `inglobals.com`, edita `server_name` antes del `nginx
-t` (`sudo nano /etc/nginx/sites-available/inglobals`) — y ajusta también
los `VITE_API_BASE_URL` / `PUBLIC_SIMULATOR_URL` de los pasos 7 y 8.

`nginx -t` debe decir "syntax is ok" y "test is successful" antes de seguir.

## 11. Apuntar el dominio y activar HTTPS

En el panel de DNS de Namecheap (o donde tengas el dominio), crea estos
registros **A** apuntando a la IP del VPS:

- `inglobals.com`
- `www.inglobals.com`

Espera unos minutos a que propague (`nslookup inglobals.com` desde tu PC).
Nota: `inglobals.com` hoy vive en Netlify — hasta que no cambies este
registro A, el dominio sigue sirviendo desde ahí. Puedes probar todo primero
contra la IP del VPS directamente (con `curl -H "Host: inglobals.com"
http://TU_IP_DEL_VPS/` o similar) y mover el DNS cuando estés conforme.

Con eso propagado:

```bash
sudo certbot --nginx -d inglobals.com -d www.inglobals.com
```

Certbot va a pedirte un correo y reescribir el Nginx config para servir por
HTTPS automáticamente (incluye renovación automática, no hay que hacer nada
más después).

## 12. Verificar

Desde tu navegador: `https://inglobals.com` debería cargar la landing, y
`https://inglobals.com/simulador` debería cargar el Simulador DAD — escribe
una consulta de prueba y confirma que responde. Y
`https://inglobals.com/iyf` debería mostrar el botón "SIMULADOR" ya
funcionando, llevándote al simulador.

Desde el VPS, para ver logs en vivo mientras pruebas:

```bash
sudo journalctl -u inglobals-backend -f
```

---

## Cómo actualizar el proyecto después de este primer despliegue

Un solo comando, desde cualquier carpeta del VPS:

```bash
bash ~/vue-inglobalsApp/deploy/update.sh
```

Hace todo: `git pull`, reinstala dependencias del backend, reinicia el
servicio systemd (y confirma que quedó `active`), recompila frontend y
landing. Si `git pull` falla porque hay cambios locales sin commitear en el
VPS (ej. tocaste algo a mano), el script se detiene ahí con el error de git
— resuélvelo (o descarta esos cambios) y vuelve a correrlo.

El script a propósito **no toca**:
- **La bibliografía** — no viaja por `git pull` (ver paso 0). Si agregas
  documentos nuevos, sube la carpeta que cambió con el `scp` del paso 5 y
  corre `python scripts/ingest_knowledge_base.py` tú mismo — es seguro
  correrlo de nuevo, se salta los archivos que ya estaban indexados.
- **El Nginx vivo** — certbot ya lo modificó con los bloques HTTPS;
  sobrescribirlo con `deploy/nginx.conf` se los borraría. Si ese archivo
  cambió en el pull, el script te avisa al final para que revises la
  diferencia y apliques el cambio a mano.

Si prefieres los pasos manuales (para entender qué hace, o depurar algo
puntual), son los mismos que ya viste en las Fases 4-9 de este documento,
sin el paso 0/5 de la bibliografía ni la configuración de Nginx/certbot.
