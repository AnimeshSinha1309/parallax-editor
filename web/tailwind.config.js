/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Noctis Minimus Theme - Dark
        'vscode-bg-primary': '#1b2932',
        'vscode-bg-secondary': '#17232b',
        'vscode-bg-tertiary': '#0e1920',
        'vscode-text-primary': '#c5cdd3',
        'vscode-text-secondary': '#5e7887',
        'vscode-accent-blue': '#72b7c0',
        'vscode-accent-green': '#72c09f',
        'vscode-accent-yellow': '#d3b692',
        'vscode-accent-red': '#b96346',
        'vscode-accent-purple': '#7068b1',
        'vscode-accent-orange': '#c37455',
        'vscode-border': '#2e4554',
        'vscode-focus-border': '#5998c0',
      },
      fontFamily: {
        'sans': ['Montserrat', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        'mono': ['Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}

