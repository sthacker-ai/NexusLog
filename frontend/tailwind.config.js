/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'retro-bg': '#f5f5dc',
                'retro-card': '#ffffff',
                'retro-border': '#333333',
                'retro-accent': '#4a90e2',
                'retro-accent-hover': '#357abd',
                'retro-success': '#5cb85c',
                'retro-warning': '#f0ad4e',
                'retro-danger': '#d9534f',
            },
            fontFamily: {
                'mono': ['"JetBrains Mono"', '"Courier New"', 'monospace'],
                'pixel': ['"Press Start 2P"', 'cursive'],
            },
            boxShadow: {
                'retro': '4px 4px 0px 0px rgba(0,0,0,0.2)',
                'retro-hover': '6px 6px 0px 0px rgba(0,0,0,0.3)',
            }
        },
    },
    plugins: [],
}
