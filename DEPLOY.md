# Cómo desplegar — todo en Render (frontend + backend juntos)

Estos pasos requieren tu cuenta (GitHub, Render), así que no los puedo hacer
yo directamente — pero el proyecto ya está configurado para que sea un solo
flujo.

## Pasos

1. Sube este repo a GitHub si no lo has hecho.
2. En [render.com](https://render.com) → **New** → **Blueprint** → conecta el
   repo. Render detecta `render.yaml` en la raíz y propone **dos servicios**:
   - `inglobals-backend` (la API en Python)
   - `inglobals-frontend` (el sitio estático de Vue)
3. Antes de confirmar, Render te pide el valor de la única variable
   realmente secreta (`sync: false` en `render.yaml`):
   - `AI_API_KEY` → tu clave de Gemini (la misma que ya está en `backend/.env` local).
4. Confirma. Render construye y publica ambos servicios. El backend queda en
   el plan **Free** por defecto — sirve para probar, pero los datos (cuentas,
   historial) se borran en cada reinicio. El sitio estático del frontend es
   gratis siempre, sin ese problema.
5. Listo — abre la URL del `inglobals-frontend` y ya debería funcionar
   contra el backend real.

## Si Render asigna otros nombres de dominio

`render.yaml` asume que los servicios quedan como
`inglobals-backend.onrender.com` e `inglobals-frontend.onrender.com` (eso
pasa si esos nombres están libres). Si Render te asignó nombres distintos
(por ejemplo con un sufijo, porque alguien más ya usaba ese nombre):

1. Copia la URL real de cada servicio desde el dashboard de Render.
2. En el servicio del backend → **Environment** → actualiza `CORS_ORIGINS`
   con la URL real del frontend.
3. En el servicio del frontend → **Environment** → actualiza
   `VITE_API_BASE_URL` con la URL real del backend, y vuelve a desplegar el
   frontend (Vite incrusta esta variable en el build, no la lee en vivo).

## Cuando quieras que los datos persistan de verdad

El plan gratis del backend no permite disco persistente — border cuenta que
"probar gratis" significa que el historial y las cuentas de usuario se
pierden en cada reinicio. Cuando estés listo para usuarios reales:

1. En `render.yaml`, cambia `plan: free` por `plan: starter` en el servicio
   `inglobals-backend`.
2. Descomenta el bloque `disk:` y la variable `DATA_DIR` de ese mismo
   servicio (están comentados con instrucciones justo ahí).
3. Vuelve a desplegar (`git push`, Render redespliega solo si conectaste
   auto-deploy, o hazlo manual desde el dashboard).

## Notas

- **`AI_API_KEY` nunca se sube al repo** — vive solo en el dashboard de
  Render (y en tu `backend/.env` local, que está en `.gitignore`).
- El plan gratis "duerme" el backend tras un rato sin uso; la primera
  consulta después de eso tarda más (arranque en frío). Es normal.
- Repositorio legal (leyes/normas indexadas): sigue siendo un proceso aparte,
  vía `POST /api/v1/documents/upload` — desplegar no lo hace por ti.
- Si en el futuro prefieres el frontend específicamente en Vercel (por
  ejemplo por un dominio o equipo que ya tengan ahí), el repo también trae
  `vercel.json` listo para eso — no hace falta usarlo si te quedas en Render.
