from pathlib import Path
import shutil, re
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
import cairosvg

ROOT=Path(__file__).parent
REF=Path('/srv/opencode-workspace/assets/designer-reference/sportzz-frontend')
for d in ['logos','fonts','images','previews','source']:
    (ROOT/d).mkdir(parents=True,exist_ok=True)
for f in (REF/'public/fonts/sportzz').glob('*.ttf'):
    shutil.copy2(f,ROOT/'fonts'/f.name)
shutil.copytree(REF/'public/fonts/sportzz/licenses',ROOT/'fonts/licenses',dirs_exist_ok=True)
font=instantiateVariableFont(TTFont(ROOT/'fonts/Inter-Variable.ttf'),{'wght':900},inplace=False)
font.save(ROOT/'fonts/Inter-Black.ttf')
for weight,name in [(400,'Regular'),(600,'SemiBold')]:
    instantiateVariableFont(TTFont(ROOT/'fonts/Inter-Variable.ttf'),{'wght':weight},inplace=False).save(ROOT/f'fonts/Inter-{name}.ttf')
gs=font.getGlyphSet(); cmap=font.getBestCmap()
pen=SVGPathPen(gs); x=0
for ch in 'tream':
    glyph=gs[cmap[ord(ch)]]
    glyph.draw(TransformPen(pen,(1,0,0,1,x,0)))
    x+=glyph.width-65
path=pen.getCommands()
# Angular ZZ links the new wordmark to the inherited symbol; all lettering is outlined.
zz='M0 0H940V210L310 780H940V1000H0V790L630 220H0Z M1000 0H1940V210L1310 780H1940V1000H1000V790L1630 220H1000Z'
body=f'<g transform="translate(350 1350) skewX(-14)"><path d="{zz}" transform="translate(0 -1000)"/><path d="{path}" transform="translate(1950 0) scale(.72 -.72)"/></g>'
width=350+1950+x*.72+330
symbol=(REF/'public/brand/sportzz/isotipo-verde.svg').read_text()
for name,col in [('negro','#080B09'),('blanco','#F5F7F3'),('verde','#B6FF00')]:
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} 1550" fill="{col}">{body}</svg>'
    (ROOT/f'logos/zztream-logotipo-{name}.svg').write_text(svg)
    cairosvg.svg2png(bytestring=svg.encode(),write_to=str(ROOT/f'logos/zztream-logotipo-{name}.png'),output_width=2000)
    iso=re.sub(r'fill="#[0-9A-Fa-f]{6}"',f'fill="{col}"',symbol)
    (ROOT/f'logos/zztream-isotipo-{name}.svg').write_text(iso)
    cairosvg.svg2png(bytestring=iso.encode(),write_to=str(ROOT/f'logos/zztream-isotipo-{name}.png'),output_width=1000)
white=(ROOT/'logos/zztream-logotipo-blanco.svg').read_text()
sheet=f'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="800" viewBox="0 0 1600 800"><rect width="1600" height="800" fill="#080B09"/><svg x="120" y="110" width="1360" height="330" viewBox="0 0 {width:.0f} 1550" fill="#F5F7F3">{body}</svg><svg x="640" y="490" width="320" height="225" viewBox="0 0 315 221">'+re.search(r'<path.*?/>',symbol).group(0)+'</svg></svg>'
cairosvg.svg2png(bytestring=sheet.encode(),write_to=str(ROOT/'logos/zztream-reference.png'))
print(ROOT/'logos/zztream-reference.png')
