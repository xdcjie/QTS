import react from '@vitejs/plugin-react'
import path from 'path'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['tests/vitest.setup.ts'],
    include: ['tests/**/*.spec.ts', 'tests/**/*.spec.tsx'],
    exclude: ['tests/e2e/**'],
  },
})
