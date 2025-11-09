import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Get backend port from environment (set by dev script)
const backendPort = process.env.BACKEND_PORT || '8000';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    '__BACKEND_PORT__': JSON.stringify(backendPort),
  },
})
