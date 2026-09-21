// @ts-check
import { defineConfig, passthroughImageService } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
  // "passthrough" en vez del servicio Sharp por defecto: sirve las imágenes
  // tal cual, sin redimensionar/convertir a webp. Evita depender del binario
  // nativo de Sharp (dio un bug real en el VPS de producción al resolverlo
  // en Linux). Para una landing con pocas imágenes, el costo (páginas un
  // poco más pesadas) es aceptable frente a la fragilidad de esa dependencia
  // nativa. Se puede revisar más adelante si el peso de página importa.
  image: {
    service: passthroughImageService(),
  },
  vite: {
    plugins: [tailwindcss()]
  }
});