"""Derive small transparent PNG assets from the retained Magnific logo concept.

No AI call, redraw, vector tracing or additional credits. Original stays intact.
The white matte is removed; flat fills are normalized to the existing brand tokens.
"""

import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--provenance', required=True, type=Path)
    args = parser.parse_args()
    output = Path(__file__).resolve().parent / 'assets/zztreams'
    output.mkdir(exist_ok=True)
    original = Image.open(args.original).convert('RGB')
    cyan_mask = Image.new('L', original.size)
    ink_mask = Image.new('L', original.size)
    cyan_pixels, ink_pixels = [], []
    for red, green, blue in original.get_flattened_data():
        if min(red, green, blue) >= 245:
            cyan_pixels.append(0)
            ink_pixels.append(0)
        elif green - red > 20 and blue - red > 20:
            cyan_pixels.append(min(255, round((255 - red) / 235 * 255)))
            ink_pixels.append(0)
        else:
            cyan_pixels.append(0)
            ink_pixels.append(min(255, round((255 - min(red, green, blue)) / 245 * 255)))
    cyan_mask.putdata(cyan_pixels)
    ink_mask.putdata(ink_pixels)
    # The generated concept has one cyan symbol, then an ink wordmark.
    symbol_box = cyan_mask.point(lambda value: 255 if value > 128 else 0).getbbox()
    word_box = ink_mask.point(lambda value: 255 if value > 128 else 0).getbbox()
    assert symbol_box and word_box and symbol_box[2] < word_box[0], 'Inspect concept before deriving assets'
    # Keep low-alpha neutral matte pixels around the cyan mark out of the ink
    # layer. The empty gap is inspected above; neither shape is redrawn.
    boundary = (symbol_box[2] + word_box[0]) // 2
    ink_mask.paste(0, (0, 0, boundary, original.height))
    cyan_mask.paste(0, (boundary, 0, original.width, original.height))
    union = (min(symbol_box[0], word_box[0]), min(symbol_box[1], word_box[1]), max(symbol_box[2], word_box[2]), max(symbol_box[3], word_box[3]))
    colors = {'ink': '#0a0f0d', 'paper': '#f2f5f3', 'cyan': '#2ee6d6'}
    entries = []

    def save(name, image):
        image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        path = output / name
        image.save(path, optimize=True)
        entries.append({'file': 'assets/zztreams/' + name, 'dimensions': list(image.size), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    for variant in ['ink', 'paper']:
        word = Image.new('RGBA', original.size, colors[variant])
        word.putalpha(ink_mask)
        symbol = Image.new('RGBA', original.size, colors['cyan'])
        symbol.putalpha(cyan_mask)
        lockup = Image.alpha_composite(symbol, word)
        save('lockup-' + variant + '.png', lockup.crop(union))
        save('wordmark-' + variant + '.png', word.crop(word_box))
    for variant in ['cyan', 'ink', 'paper']:
        symbol = Image.new('RGBA', original.size, colors[variant])
        symbol.putalpha(cyan_mask)
        save('symbol-' + variant + '.png', symbol.crop(symbol_box))
    save('logo-concept-1k.png', original.copy())
    provenance = json.loads(args.provenance.read_text())
    provenance['original_sha256'] = hashlib.sha256(args.original.read_bytes()).hexdigest()
    provenance['derivation'] = 'Local white-matte removal, separate symbol/wordmark crops, token-normalized flat fills and 1024px maximum PNG exports. Raster derivatives, not vector masters. No additional generation charge.'
    provenance['files'] = entries
    (output / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(json.dumps({'symbol_box': symbol_box, 'wordmark_box': word_box, 'files': entries}, indent=2))


if __name__ == '__main__':
    main()
