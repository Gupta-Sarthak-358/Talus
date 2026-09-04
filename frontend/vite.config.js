import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: false,
    host: true,
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          // NOTE: no 'vendor' entry — react/react-dom resolve into index
          // (a vendor chunk came out empty). Router gets its own chunk.
          router: ['react-router-dom'],
          leaflet: ['leaflet', 'react-leaflet'],
          charts: ['recharts'],
          icons: ['lucide-react'],
        },
      },
    },
  },
});
