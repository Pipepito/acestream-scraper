import fs from 'fs';
import path from 'path';

describe('vite config', () => {
  it('defines manual chunks for large framework and page bundles', () => {
    const configSource = fs.readFileSync(path.join(__dirname, '..', '..', 'vite.config.ts'), 'utf8');

    expect(configSource).toContain('manualChunks');
    expect(configSource).toContain("return 'react-vendor'");
    expect(configSource).toContain("return 'mui-vendor'");
    expect(configSource).toContain("return 'mui-data-grid'");
    expect(configSource).toContain("return 'mui-icons'");
    expect(configSource).toContain("return 'data-vendor'");
    expect(configSource).toContain("return 'tv-channels-page'");
    expect(configSource).toContain("return 'player-vendor'");
    expect(configSource).toContain("id.includes('node_modules/react/')");
    expect(configSource).toContain("id.includes('node_modules/react-dom/')");
    expect(configSource).toContain("id.includes('node_modules/hls.js')");
  });
});
