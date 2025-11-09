#!/usr/bin/env node

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Parse command line arguments
const args = process.argv.slice(2);
let backendPort = '8000'; // default port

for (let i = 0; i < args.length; i++) {
  if (args[i] === '--backend_port' && i + 1 < args.length) {
    backendPort = args[i + 1];
    break;
  } else if (args[i].startsWith('--backend_port=')) {
    backendPort = args[i].split('=')[1];
    break;
  }
}

// Create a temporary config file that extends the base config
const configPath = join(__dirname, '..', 'vite.config.ts');
const tempConfigContent = `
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  define: {
    '__BACKEND_PORT__': '"${backendPort}"',
  },
})
`;

// Write the config (we'll use the define option instead)
// Actually, let's pass it via command line to vite

// Start vite with define option
const viteArgs = [
  'vite',
  '--config', configPath,
];

console.log(`Starting dev server with backend port: ${backendPort}`);

// Set environment variable for the config to read
process.env.BACKEND_PORT = backendPort;

const viteProcess = spawn('npx', viteArgs, {
  stdio: 'inherit',
  cwd: join(__dirname, '..')
});

viteProcess.on('exit', (code) => {
  process.exit(code || 0);
});

process.on('SIGINT', () => {
  viteProcess.kill('SIGINT');
});

process.on('SIGTERM', () => {
  viteProcess.kill('SIGTERM');
});
