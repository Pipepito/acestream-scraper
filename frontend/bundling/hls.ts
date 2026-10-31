import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

// Match the full upstream ESM build. Keep source modules visible to the bundler
// instead of importing the indivisible, already-bundled distribution file.
// Review these flags and build dependencies whenever the pinned HLS version changes.
export function hlsBuildOptions(packagePath: string) {
  const packageRoot = dirname(packagePath);
  const hlsPackage = JSON.parse(readFileSync(packagePath, 'utf8')) as { version: string };
  const define = {
    __VERSION__: JSON.stringify(hlsPackage.version),
    __USE_ALT_AUDIO__: 'true',
    __USE_EME_DRM__: 'true',
    __USE_SUBTITLES__: 'true',
    __USE_CMCD__: 'true',
    __USE_CONTENT_STEERING__: 'true',
    __USE_VARIABLE_SUBSTITUTION__: 'true',
    __USE_M2TS_ADVANCED_CODECS__: 'true',
    __USE_MEDIA_CAPABILITIES__: 'true',
    __USE_INTERSTITIALS__: 'true',
    __USE_IFRAMES__: 'true',
  };

  const alias = [
    { find: /^hls\.js$/, replacement: join(packageRoot, 'src/exports-named.ts') },
    // Keep the worker out of main-thread ESM, matching upstream fullEsm.
    { find: /^\.\/transmuxer-worker$/, replacement: join(packageRoot, 'src/empty-es.js') },
  ];

  return { define, alias };
}
