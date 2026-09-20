/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
	theme: {
		extend: {
			colors: {
				azulCorp: '#0f172a', // Azul oscuro/slate elegante
				verdeEsm: '#10b981', // Para la "S" de Sostenibilidad
				violetaIA: '#8b5cf6', // Para la "S" de Inteligencia Artificial
			},
		},
	},
	plugins: [],
};
