import legacy from '@vitejs/plugin-legacy'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: './',
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11'],
    }),react()],
})
