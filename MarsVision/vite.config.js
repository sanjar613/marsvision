import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import process from 'node:process'

// https://vite.dev/config/
const apiTarget = process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
