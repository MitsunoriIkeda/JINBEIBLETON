import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    proxy: {
      '/samples': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        secure: false,
      },
      '/api': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})

