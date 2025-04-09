/** @type {import('tailwindcss').Config} */
export default {
    content: [
      "./index.html",
      "./src/**/*.{js,jsx,ts,tsx}",
      "./src/styles/index.css"
    ],
    theme: {
      extend: {},
    },
    plugins: [require('@tailwindcss/typography')],
  }
  