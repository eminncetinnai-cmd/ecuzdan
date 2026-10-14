/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
    "./routes/**/*.py",
  ],
  theme: {
    extend: {
      fontFamily: {
        outfit: ['Outfit', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
