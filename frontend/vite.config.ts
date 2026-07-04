import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // use 127.0.0.1 explicitly: on some systems Node resolves
        // "localhost" to ::1 while uvicorn only listens on IPv4
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
