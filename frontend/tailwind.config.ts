import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#fbfbfc",
        surface: "#ffffff",
        surfaceBorder: "#e5e7eb",
        primary: "#111827",
        accent: "#f43f5e",
        success: "#10b981",
        danger: "#ef4444",
      },
    },
  },
  plugins: [],
};
export default config;
