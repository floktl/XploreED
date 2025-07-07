import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        watch: {
            usePolling: true,
        },
        historyApiFallback: true,
        host: true,
        port: 5173,
        strictPort: true,
        hmr: {
            protocol: 'ws',
            host: 'localhost'
        },
        proxy: {
            '/api': {
                target: 'http://backend:5050',
                changeOrigin: true,
                secure: false,
            }
        }
    }
});
