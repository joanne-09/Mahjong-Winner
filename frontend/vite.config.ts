import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const nodeEnv = (globalThis as typeof globalThis & {
  process?: { env?: Record<string, string | undefined> };
}).process?.env ?? {};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: nodeEnv.VITE_BASE_PATH || '/Mahjong-Winner/', // GitHub Pages base path by default
})
