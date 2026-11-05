import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Forward API calls to the FastAPI backend (Library_AI_Agent/server.py)
    proxy: { '/api': 'http://localhost:8000' },
  },
})
