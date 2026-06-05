/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      keyframes: {
        slidein: { "0%": { opacity: 0, transform: "translateY(-8px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        pingsoft: { "0%": { transform: "scale(1)", opacity: 0.6 }, "100%": { transform: "scale(2.2)", opacity: 0 } },
      },
      animation: { slidein: "slidein .35s cubic-bezier(.22,1,.36,1)", pingsoft: "pingsoft 1.8s ease-out infinite" },
    },
  },
  plugins: [],
};
