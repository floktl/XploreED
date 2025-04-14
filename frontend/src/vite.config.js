import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    watch: {
      usePolling: true,
    },
    historyApiFallback: true,
    host: '0.0.0.0', // 👈 allow external connections, required in Docker/Render
    port: 5173,
    strictPort: true,
    hmr: {
      protocol: 'ws',
      host: process.env.HOST || 'localhost', // fallback to localhost for local dev
    },
  },
});
