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
        'vscode-bg-secondary': '#0a0a0a',
        'vscode-bg-tertiary': '#121212',
        'vscode-text-primary': '#e8e8e8',
        'vscode-text-secondary': '#6b7280',
        'vscode-accent-blue': '#3b82f6',
        'vscode-accent-green': '#10b981',
        'vscode-accent-yellow': '#f59e0b',
        'vscode-accent-red': '#ef4444',
        'vscode-accent-purple': '#a855f7',
        'vscode-accent-orange': '#f97316',
        'vscode-border': '#1f1f1f',
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

