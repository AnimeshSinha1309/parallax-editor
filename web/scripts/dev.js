#!/usr/bin/env node

import { spawn } from 'child_process';

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

// Set environment variables
const env = {
  ...process.env,
  VITE_ENABLE_BACKEND: 'true',
  VITE_BACKEND_URL: `http://localhost:${backendPort}`
};

// Start vite dev server
const viteProcess = spawn('npx', ['vite'], {
  env,
  stdio: 'inherit'
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
