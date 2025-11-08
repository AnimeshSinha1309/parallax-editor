/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'vscode-bg-primary': '#1e1e1e',
        'vscode-bg-secondary': '#252526',
        'vscode-bg-tertiary': '#2d2d30',
        'vscode-text-primary': '#cccccc',
        'vscode-text-secondary': '#969696',
        'vscode-accent-blue': '#007acc',
        'vscode-accent-green': '#89d185',
        'vscode-accent-yellow': '#dcdcaa',
        'vscode-accent-red': '#f48771',
        'vscode-border': '#3e3e42',
        'vscode-focus-border': '#007acc',
      },
      fontFamily: {
        'mono': ['Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}

