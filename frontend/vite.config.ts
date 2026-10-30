import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { createRequire } from 'node:module';
import { hlsBuildOptions } from './bundling/hls';

const require = createRequire(import.meta.url);
const hlsBuild = hlsBuildOptions(require.resolve('hls.js/package.json'));

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: { alias: hlsBuild.alias },
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
    ...hlsBuild.define,
    'process.env.NODE_ENV': JSON.stringify(mode),
  },
  build: {
    outDir: 'dist',
    rolldownOptions: {
      output: {
        codeSplitting: {
          // Assign dependency modules once; otherwise overlapping groups can
          // create initialization cycles between MUI, React and their helpers.
          includeDependenciesRecursively: false,
          groups: [
            { name: 'react-vendor', test: /node_modules\/(react|react-dom|scheduler)\//, priority: 40 },
            {
              // Controllers depend on the media primitives. Keep that boundary
              // intact: size-based splits can snapshot uninitialized mux classes.
              name: (id) => /hls\.js\/src\/(controller\/|hls\.ts|config\.ts|exports-)/.test(id)
                ? 'player-vendor' : 'player-media',
              test: /node_modules\/(hls\.js|@svta|eventemitter3|url-toolkit)\//,
              priority: 30,
            },
            { name: 'mui-data-grid', test: /node_modules\/@mui\/x-data-grid\//, maxSize: 650_000, priority: 30 },
            { name: 'mui-icons', test: /node_modules\/@mui\/icons-material\//, priority: 30 },
            // Keep UI helpers (Emotion/transitions) with MUI, including their
            // shared dependencies, rather than extracting cyclic common chunks.
            { name: 'mui-vendor', test: /node_modules\//, priority: 10 },
            { name: 'data-vendor', test: /node_modules\/(@tanstack\/(react-query|query-core)|axios)\//, priority: 20 },
            { name: 'tv-channels-page', test: /\/src\/pages\/TVChannels\.tsx$/ },
          ],
        },
      },
    },
  },
}));
