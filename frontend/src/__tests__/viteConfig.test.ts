import fs from 'fs';
import path from 'path';
import { hlsBuildOptions } from '../../bundling/hls';

const packagePath = require.resolve('hls.js/package.json');
const hlsPackage = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
const frontendPackage = JSON.parse(fs.readFileSync(path.join(__dirname, '../../package.json'), 'utf8'));

describe('modular HLS build compatibility', () => {
  it('retains every full-build feature declared by the installed player', () => {
    const declarations = fs.readFileSync(path.join(path.dirname(packagePath), 'src/define-plugin.d.ts'), 'utf8');
    const features = Array.from(declarations.matchAll(/declare const (__USE_\w+__): boolean/g)).map((match) => match[1]);
    const { define } = hlsBuildOptions(packagePath);

    expect(features.length).toBeGreaterThan(0);
    expect(Object.keys(define).filter((key) => key.startsWith('__USE_')).sort()).toEqual(features.sort());
    for (const feature of features) {
      expect(define[feature as keyof typeof define]).toBe('true');
    }
    expect(define.__VERSION__).toBe(JSON.stringify(hlsPackage.version));
  });

  it('pins the player and source dependencies to the upstream build versions', () => {
    expect(frontendPackage.dependencies['hls.js']).toBe(hlsPackage.version);
    for (const dependency of ['@svta/cml-cmcd', '@svta/cml-id3', '@svta/cml-utils', 'eventemitter3', 'url-toolkit']) {
      expect(frontendPackage.devDependencies[dependency]).toBe(hlsPackage.devDependencies[dependency]);
      const installed = JSON.parse(fs.readFileSync(path.join(__dirname, '../../node_modules', dependency, 'package.json'), 'utf8'));
      expect(installed.version).toBe(hlsPackage.devDependencies[dependency]);
    }
  });
});
