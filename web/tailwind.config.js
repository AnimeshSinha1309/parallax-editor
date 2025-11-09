/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark theme colors
        'vscode-bg-primary': '#0a0a0a',
        'vscode-bg-secondary': '#121212',
        'vscode-bg-tertiary': '#1a1a1a',
        'vscode-text-primary': '#e8e8e8',
        'vscode-text-secondary': '#9ca3af',
        'vscode-accent-blue': '#3b82f6',
        'vscode-accent-green': '#10b981',
        'vscode-accent-yellow': '#f59e0b',
        'vscode-accent-red': '#ef4444',
        'vscode-accent-purple': '#a855f7',
        'vscode-accent-orange': '#f97316',
        'vscode-border': '#27272a',
        'vscode-focus-border': '#3b82f6',
      },
      fontFamily: {
        'sans': ['Montserrat', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        'mono': ['Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}

