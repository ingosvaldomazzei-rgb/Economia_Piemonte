import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://osservatorio-piemonte.netlify.app',
  vite: {
    plugins: [tailwindcss()]
  },
  integrations: [sitemap()],
  markdown: {
    shikiConfig: {
      theme: 'github-light'
    }
  }
});
