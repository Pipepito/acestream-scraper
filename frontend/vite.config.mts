import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { createRequire } from 'node:module';
import { hlsBuildOptions } from './bundling/hls.ts';

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
        changeOrigin: false,
      },
    },
  },
  define: {
    ...hlsBuild.define,
    'process.env.NODE_ENV': JSON.stringify(mode),
  },
  build: {
    outDir: 'dist',
    modulePreload: {
      // Every lazy import runs after the HTML entry has executed. Its shared
      // exports can remain imports, but preloading that entry again is redundant
      // and WebKit reports the late preload as unused. Keep all other preloads.
      resolveDependencies: (_url, dependencies, { hostType }) => hostType === 'js'
        ? dependencies.filter(dependency => !dependency.startsWith('assets/app-entry-'))
        : dependencies,
    },
    rolldownOptions: {
      output: {
        entryFileNames: 'assets/app-entry-[hash].js',
        codeSplitting: {
          // Assign dependency modules once; otherwise overlapping groups can
          // create initialization cycles between MUI, React and their helpers.
          includeDependenciesRecursively: false,
          groups: [
            { name: 'react-vendor', test: /node_modules\/(react|react-dom|scheduler)\//, priority: 40 },
            {
              debugName: 'hls',
              // Controllers depend on the media primitives. Keep that boundary
              // intact: size-based splits can snapshot uninitialized mux classes.
              name: (id) => /hls\.js\/src\/(controller\/|hls\.ts|config\.ts|exports-)/.test(id)
                ? 'player-vendor' : 'player-media',
              test: /node_modules\/(hls\.js|@svta|eventemitter3|url-toolkit)\//,
              priority: 30,
            },
            { name: 'mui-data-grid', test: /node_modules\/@mui\/x-data-grid\//, maxSize: 650_000, priority: 30 },
            { name: 'mui-icons', test: /node_modules\/@mui\/icons-material\//, priority: 30 },
            { name: 'messages-en', test: /\/src\/i18n\/messages\/(en|.+-en)\.(ts|json)$/, priority: 20 },
            { name: 'messages-es', test: /\/src\/i18n\/messages\/(es|.+-es)\.(ts|json)$/, priority: 20 },
            { name: 'router-vendor', test: /node_modules\/(react-router|react-router-dom|@remix-run)\//, priority: 20 },
            { name: 'localization-vendor', test: /node_modules\/(i18next|react-i18next|html-parse-stringify|void-elements)\//, priority: 20 },
            { name: 'date-vendor', test: /node_modules\/date-fns\//, priority: 20 },
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
