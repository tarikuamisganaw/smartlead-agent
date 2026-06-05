import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#17201b",
        panel: "#f8faf8",
        line: "#dbe3dc",
        brand: "#24745f",
        accent: "#b6432f",
        gold: "#b98524",
      },
      boxShadow: {
        soft: "0 16px 40px rgba(25, 42, 35, 0.10)",
      },
    },
  },
  plugins: [],
};

export default config;
