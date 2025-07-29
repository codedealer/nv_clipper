import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig(({ command, mode }) => {
  const isDev = command === 'serve' || mode === 'development'

  return {
    plugins: [
      vue(),
    ],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    server: {
      port: 5173,
      host: 'localhost',
      cors: true,
      // Don't open browser automatically since we're using pywebview
      open: false
    },
    build: {
      outDir: '../clipper/gui/dist',
      emptyOutDir: true,
      // Development optimizations
      minify: isDev ? false : 'esbuild',
      sourcemap: isDev ? true : false,
      target: isDev ? 'esnext' : 'es2015',
      rollupOptions: {
        output: {
          // Ensure consistent file names for pywebview integration
          entryFileNames: 'assets/[name].js',
          chunkFileNames: 'assets/[name].js',
          assetFileNames: 'assets/[name].[ext]'
        }
      }
    },
    // Development optimizations
    esbuild: isDev ? {
      target: 'esnext'
    } : undefined,
    optimizeDeps: {
      include: ['vue', 'pinia', 'vue-router', 'element-plus'],
      exclude: isDev ? [] : undefined
    },
    base: './', // Use relative paths for pywebview
  }
})
