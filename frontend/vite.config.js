import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  // El simulador vive en inglobals.com/simulador, no en la raíz del dominio
  // (ahí vive la landing de Astro) — sin esto, los assets compilados
  // (JS/CSS con hash) se referenciarían desde "/", que le pertenece a la
  // landing, y la app cargaría en blanco.
  base: '/simulador/',
  build: {
    // No publicar mapas de código fuente en producción — es una de las
    // medidas razonables de protección de código que pidió el cliente.
    sourcemap: false,
  },
  plugins: [
    vue(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'logo.png'],
      manifest: {
        name: 'Inglobals — DAD Dashboard',
        short_name: 'Inglobals',
        description: 'Auditoría inteligente para un futuro sostenible. Tablero de comandos DAD.',
        // El manifest de PWA necesita el scope/start_url explícitos cuando
        // la app no vive en la raíz del origen.
        scope: '/simulador/',
        start_url: '/simulador/',
        theme_color: '#0f172a',
        background_color: '#0f172a',
        display: 'standalone',
        orientation: 'portrait',
        lang: 'es',
        icons: [
          {
            src: 'logo.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: 'logo.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
    }),
  ],
})
