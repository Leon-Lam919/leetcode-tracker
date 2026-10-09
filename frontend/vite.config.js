import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // 5174, not Vite's default 5173, so this can run next to the dashboard app.
    port: 5174,
    strictPort: true,
    // Forward /api calls to FastAPI so the browser sees one origin (no CORS in dev).
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
  },
})
