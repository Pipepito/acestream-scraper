"""Package verified canonical collections; never run their construction scripts."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'integration-manifest.json').read_text())
    output = args.output.resolve()
    if output == root or root in output.parents:
        parser.error('Choose an output directory outside design-assets.')
    output.mkdir(parents=True, exist_ok=True)
    for collection in manifest['collections']:
        name = collection['path']
        prefix = name.replace('/', '-')
        entries = sorted((e for e in manifest['files'] if e['collection'] == name), key=lambda e: e['path'])
        archive = output / (prefix + '.zip')
        # Verify everything before creating/overwriting the archive.
        for entry in entries:
            path = root / name / entry['path']
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise ValueError(f'Unsafe input: {path}')
            data = path.read_bytes()
            if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
                raise ValueError(f'Changed input: {path}')
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for entry in entries:
                info = zipfile.ZipInfo(f"{prefix}/{entry['path']}", date_time=(2026, 11, 10, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, (root / name / entry['path']).read_bytes(),
                                compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise ValueError(f'Invalid ZIP: {archive}')
        print(json.dumps({'archive': str(archive), 'files': len(entries), 'bytes': archive.stat().st_size,
                          'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
