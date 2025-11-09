/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light theme colors - Color Hunt Palette
        'vscode-bg-primary': '#EFFFFB',
        'vscode-bg-secondary': '#EFFFFB',
        'vscode-bg-tertiary': '#F5FFFD',
        'vscode-text-primary': '#272727',
        'vscode-text-secondary': '#5a5a5a',
        'vscode-accent-blue': '#4F98CA',
        'vscode-accent-green': '#50D890',
        'vscode-accent-yellow': '#F59E0B',
        'vscode-accent-red': '#EF4444',
        'vscode-accent-purple': '#A855F7',
        'vscode-accent-orange': '#F97316',
        'vscode-border': '#D5F5EC',
        'vscode-focus-border': '#50D890',
      },
      fontFamily: {
        'sans': ['Montserrat', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        'mono': ['Cascadia Code', 'Fira Code', 'Consolas', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}

