import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({
  plugins: [react()],
  server: {host: '0.0.0.0', allowedHosts: true, proxy: {'/api': {target: process.env.API_TARGET || 'http://127.0.0.1:8001', changeOrigin: false}}},
  preview: {host: '0.0.0.0', allowedHosts: true, proxy: {'/api': {target: process.env.API_TARGET || 'http://127.0.0.1:8001', changeOrigin: false}}}
});
