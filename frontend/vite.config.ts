import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(mode),
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/react/') || id.includes('node_modules/react-dom/')) {
            return 'react-vendor';
          }

          if (id.includes('node_modules/hls.js')) {
            return 'player-vendor';
          }

          if (id.includes('node_modules/@mui/x-data-grid')) {
            return 'mui-data-grid';
          }

          if (id.includes('node_modules/@mui/icons-material')) {
            return 'mui-icons';
          }

          if (id.includes('node_modules/@mui')) {
            return 'mui-vendor';
          }

          if (id.includes('node_modules/@tanstack/react-query') || id.includes('node_modules/@tanstack/query-core') || id.includes('node_modules/axios')) {
            return 'data-vendor';
          }

          if (id.includes('/src/pages/TVChannels.tsx')) {
            return 'tv-channels-page';
          }

          return undefined;
        },
      },
    },
  },
}));
