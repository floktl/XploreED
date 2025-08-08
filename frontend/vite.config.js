import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'
import path from 'path'
import dotenv from 'dotenv'

// Load shared env from backend if present (monorepo convenience)
const backendEnvPath = path.resolve(__dirname, '../backend/secrets/.env')
if (fs.existsSync(backendEnvPath)) {
  dotenv.config({ path: backendEnvPath })
}

// Decide target based on VITE_ENV
// - if VITE_ENV=development → local backend
// - else (unset/anything else) → docker network backend
const proxyTarget = (process.env.VITE_ENV || '').toLowerCase() === 'development'
  ? 'http://localhost:5050'
  : 'http://backend:5050'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
})

