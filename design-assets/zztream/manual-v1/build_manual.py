from pathlib import Path
import re, json, shutil, zipfile, math, os
from PIL import Image, ImageOps, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
import pymupdf as fitz

R=Path(os.environ.get('ZZTREAM_ASSET_ROOT',Path(__file__).resolve().parent.parent if Path(__file__).parent.name=='source' else Path(__file__).parent))
W,H=960,600
BG='#080B09'; FG='#F5F7F3'; GREEN='#B6FF00'; CARD='#171D19'; MUTED='#AFB8B0'; LINE='#38433B'; RED='#FF726B'
for name,file in [('Display','BarlowCondensed-Bold.ttf'),('Display600','BarlowCondensed-SemiBold.ttf'),('Body','Inter-Regular.ttf'),('Medium','Inter-SemiBold.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(R/'fonts'/file)))
# Crop wordmark masters to their visible bounds, retaining true vector paths.
for p in (R/'logos').glob('zztream-logotipo-*.svg'):
    s=p.read_text()
    if 'data-trimmed' in s: continue
    im=Image.open(p.with_suffix('.png')); box=im.getbbox()
    vb=[float(v) for v in re.search(r'viewBox="([^"]+)"',s).group(1).split()]
    sx=vb[2]/im.width; sy=vb[3]/im.height
    new=f'{box[0]*sx:.3f} {box[1]*sy:.3f} {(box[2]-box[0])*sx:.3f} {(box[3]-box[1])*sy:.3f}'
    s=re.sub(r'viewBox="[^"]+"',f'viewBox="{new}" data-trimmed="true"',s,count=1)
    p.write_text(s)
    import cairosvg
    cairosvg.svg2png(bytestring=s.encode(),write_to=str(p.with_suffix('.png')),output_width=2000)

editor=Image.open(R/'images/zztream-editorial-original.png').convert('RGB')
ew,eh=editor.size
for i,name in enumerate(['cine','musica','documental']):
    editor.crop((round(i*ew/3),0,round((i+1)*ew/3),eh)).save(R/f'images/zztream-{name}-recorte.jpg',quality=95)

c=canvas.Canvas(str(R/'zztream-manual-identidad-v1.pdf'),pagesize=(W,H),pageCompression=1)
c.setTitle('zztream — Manual de identidad visual / 1.0')
c.setAuthor('zztream · Dirección de identidad')
c.setSubject('Sistema visual, voz, interfaz y aplicaciones · propuesta de identidad · noviembre 2026')
n=0
def rect(x,y,w,h,color,r=0,stroke=None):
    c.setFillColor(HexColor(color));c.setStrokeColor(HexColor(stroke or color))
    if r:c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=bool(stroke))
    else:c.rect(x,H-y-h,w,h,fill=1,stroke=bool(stroke))
def line(x,y,x2,y2,color=LINE,width=.7):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.line(x,H-y,x2,H-y2)
def text(s,x,y,size=13,font='Body',color=FG):
    c.setFillColor(HexColor(color));c.setFont(font,size);c.drawString(x,H-y-size*.82,s)
def para(s,x,y,w,size=13,color=MUTED,font='Body',leading=None):
    st=ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.5,textColor=HexColor(color))
    p=Paragraph(s,st);_,h=p.wrap(w,500);p.drawOn(c,x,H-y-h);return h
def label(s,x,y,color=GREEN):text(s,x,y,10,'Medium',color)
def title(s,sub=None):
    text(s,48,84,37,'Display')
    if sub:para(sub,48,139,864,12)
def page(section):
    global n
    n+=1;rect(0,0,W,H,BG)
    label('ZZTREAM / MANUAL DE IDENTIDAD',48,26)
    text(section,670,26,9.5,'Body',MUTED)
    line(48,49,912,49)
    text('IDENTIDAD VISUAL / 1.0 · NOVIEMBRE 2026',48,570,8,'Body',MUTED)
    text(f'{n:02} / 20',864,570,8,'Body',MUTED)
    c.bookmarkPage(f'p{n}');c.addOutlineEntry(section,f'p{n}',0)
def end():c.showPage()
cache={}
def logo(x,y,w=250,col='blanco',iso=False):
    key=(col,iso)
    if key not in cache:cache[key]=svg2rlg(str(R/f'logos/zztream-{"isotipo" if iso else "logotipo"}-{col}.svg'))
    d=cache[key];scale=w/d.width
    c.saveState();c.translate(x,H-y-d.height*scale);c.scale(scale,scale);renderPDF.draw(d,c,0,0);c.restoreState()
    return d.height*scale
def image(name,x,y,w,h,fit='cover'):
    p=R/'images'/name
    im=Image.open(p).convert('RGB')
    if fit=='cover':im=ImageOps.fit(im,(round(w*2),round(h*2)),method=Image.Resampling.LANCZOS)
    else:
        scale=min(w/im.width,h/im.height);nw,nh=im.width*scale,im.height*scale
        x+=(w-nw)/2;y+=(h-nh)/2;w,h=nw,nh
    c.drawInlineImage(im,x,H-y-h,width=w,height=h)
def button(s,x,y,w=142,state='normal'):
    color=GREEN if state in ['normal','focus'] else '#C8FF4D' if state=='hover' else '#344037'
    rect(x,y,w,39,color,6)
    text(s,x+15,y+12,11,'Medium',BG if state!='disabled' else MUTED)
    if state=='focus':
        c.setStrokeColor(HexColor(FG));c.setLineWidth(2);c.roundRect(x-4,H-y-43,w+8,47,9,fill=0,stroke=1)
def note(s,y=523):para(s,48,y,864,10)
def bullets(items,x,y,w=365,size=12):
    for s in items:
        rect(x,y+6,4,4,GREEN);h=para(s,x+17,y,w-17,size,FG);y+=h+13

# 01 — Cover
page('00 / INTRODUCCIÓN')
logo(48,93,365)
label('PLATAFORMA DE STREAMING · ENTRETENIMIENTO',48,198)
text('DALE PLAY.',48,239,75,'Display')
text('A TU MUNDO.',48,313,75,'Display',GREEN)
para('Manual de identidad visual<br/>Logotipo, lenguaje gráfico y aplicaciones.',48,431,410,17,FG)
image('zztream-editorial-original.png',546,84,366,430)
rect(546,485,366,29,GREEN);text('CINE / SERIES / MÚSICA / CULTURA / DEPORTES',559,495,8,'Medium',BG)
text('VERSIÓN 1.0 · PROPUESTA DE IDENTIDAD',48,531,9,'Medium',MUTED)
end()
# 02 — Essence
page('01 / ESENCIA')
title('Hecha para lo que te mueve.','La misma energía visual. Un universo de contenidos más amplio.')
text('ENERGÍA.',48,208,51,'Display',GREEN)
text('CURIOSIDAD.',48,263,51,'Display')
text('CONEXIÓN.',48,318,51,'Display')
para('zztream conecta a las personas con historias, directos y descubrimientos. El deporte forma parte del mundo de la marca; no define su límite.',48,394,408,14)
image('zztream-editorial-original.png',505,202,407,258)
label('CARÁCTER',505,484)
para('Intenso, abierto y preciso. Sin ruido visual, elitismo ni promesas exageradas.',505,505,395,12)
end()
# 03 — Signature
page('02 / FIRMA')
title('Dos signos. Un mundo abierto.','Nueva firma zztream y continuidad del isotipo ZZ de la identidad de referencia.')
label('A / LOGOTIPO PRINCIPAL',48,204);label('B / ISOTIPO',647,204)
logo(48,268,500);logo(679,245,190,'verde',True)
line(48,397,912,397)
text('zztream',48,421,23,'Display')
para('Firma preferente en web, campañas y primeras apariciones. Escritura de marca en texto: zztream, siempre en minúscula.',48,459,486,13)
text('ZZ circular',647,421,23,'Display')
para('Para avatar, app y marca de canal cuando el contexto ya identifica la plataforma.',647,459,265,13)
note('Logotipo vectorial propuesto para esta adaptación. El isotipo mantiene el SVG de referencia; no se extrae de imágenes generadas.',535)
end()
# 04 — Versions
page('03 / VERSIONES')
title('Color sin alterar la forma.','Rellenos planos y una única versión por aplicación. No combinar colores dentro de la firma.')
for x,y,bg,col,lab in [(48,202,FG,'negro','01 / Negro sobre claro'),(491,202,CARD,'blanco','02 / Blanco sobre negro'),(48,366,CARD,'verde','03 / Verde sobre negro'),(491,366,GREEN,'negro','04 / Negro sobre verde')]:
    rect(x,y,421,118,bg,7);logo(x+29,y+35,274,col);logo(x+329,y+31,68,col,True)
    text(lab,x,y+128,11,'Body',MUTED)
note('Blanco sobre fotografía oscura y despejada. Verde solo sobre negro o carbón. En fondos complejos, usar un contenedor liso.',539)
end()
# 05 — Clear space
page('04 / PROTECCIÓN')
title('Dale espacio para respirar.','Medir desde los límites visibles del signo, no desde el lienzo o la caja del archivo.')
x,y,w=80,264,478
lh=logo(x,y,w)
for yy in [y-lh/4,y,y+lh,y+lh*1.25]:line(x-30,yy,x+w+30,yy)
for xx in [x-lh/4,x,x+w,x+w+lh/4]:line(xx,y-37,xx,y+lh+37)
text('x',x+4,y-lh/4+2,11,'Medium',GREEN)
logo(706,226,159,'verde',True)
rect(677,198,217,168,BG,stroke=LINE);logo(706,226,159,'verde',True)
label('LOGOTIPO / X = 1/4 DE SU ALTURA',48,421)
para('Mantener al menos x libre en todo el perímetro. En composiciones densas, ampliar a 1,5x.',48,449,499,13)
label('ISOTIPO / X = 1/4 DE SU ALTURA',637,421)
para('Mínimos iniciales de uso:<br/>Logotipo: 140 px / 28 mm de ancho.<br/>Isotipo: 48 px / 12 mm de ancho.',637,449,275,12)
note('Estos mínimos son de partida: comprobar lectura real en móvil, TV, impresión y bordado antes de producir.',535)
end()
# 06 — Incorrect usage
page('05 / USOS INCORRECTOS')
title('La marca no se deforma.','Usar los vectores del kit. Las muestras tachadas muestran lo que nunca debe hacerse.')
bad=[('01 / No estirar','Conservar la proporción.'),('02 / No girar','La inclinación ya está diseñada.'),('03 / No añadir efectos','Sin sombras, biseles ni contornos.'),('04 / No recolorear partes','Un solo relleno por firma.'),('05 / No restar contraste','No usar verde sobre blanco.'),('06 / No recomponer','No unir firma y símbolo a voluntad.')]
for i,(a,b) in enumerate(bad):
    x=48+(i%3)*295;y=202+(i//3)*162
    rect(x,y,274,143,CARD,7)
    if i==4:rect(x+13,y+13,248,63,FG)
    c.saveState()
    if i==0:
        cy=H-y-45;c.translate(0,cy);c.scale(1,.5);c.translate(0,-cy);logo(x+20,y+22,230)
    elif i==1:
        cx=x+137;cy=H-y-45;c.translate(cx,cy);c.rotate(10);c.translate(-cx,-cy);logo(x+28,y+22,214)
    else:
        if i==2:logo(x+24,y+26,220,'verde')
        logo(x+20,y+22,220,'verde' if i==4 else 'blanco')
        if i==3:
            c.saveState();part=c.beginPath();part.rect(x+20,H-y-77,63,62);c.clipPath(part,stroke=0,fill=0)
            logo(x+20,y+22,220,'verde');c.restoreState()
        if i==5:logo(x+222,y+25,40,'verde',True)
    c.restoreState()
    line(x+16,y+14,x+259,y+76,RED,1.6)
    text(a,x+15,y+92,12,'Medium');text(b,x+15,y+116,9,'Body',MUTED)
end()
# 07 — Palette
page('06 / COLOR')
title('Verde que activa. Negro que enfoca.','La paleta conserva el reconocimiento de la identidad original, más allá del género del contenido.')
colors=[('VERDE ZZTREAM',GREEN,'182 / 255 / 0','29 / 0 / 100 / 0'),('NEGRO ZZTREAM',BG,'8 / 11 / 9','27 / 0 / 18 / 96'),('BLANCO NIEBLA',FG,'245 / 247 / 243','1 / 0 / 2 / 3'),('CARBÓN',CARD,'23 / 29 / 25','21 / 0 / 14 / 89')]
for i,(name,col,rgb,cmyk) in enumerate(colors):
    x=48+i*220;label(name,x,208)
    rect(x,239,204,130,col,stroke=LINE if i==1 else None)
    text(col,x+14,332,22,'Display',BG if i in [0,2] else FG)
    text('RGB '+rgb,x,391,10,'Body')
    text('CMYK APROX.',x,423,9,'Medium',MUTED)
    text(cmyk,x,445,10,'Body',MUTED)
note('RGB y HEX son la referencia digital. CMYK orientativos: el verde eléctrico pierde intensidad en cuatricromía. Seleccionar tinta directa con el impresor y validar una prueba; no hay Pantone fijado.',505)
end()
# 08 — Contrast
page('07 / COLOR APLICADO')
title('El contraste también es identidad.','Reparto orientativo: 60% oscuro, 25% fotografía y claros, 15% verde de acento.')
rect(48,202,518,65,BG,stroke=LINE);rect(566,202,216,65,FG);rect(782,202,130,65,GREEN)
text('60 / OSCURO',65,226,14);text('25 / APOYO',581,226,14,color=BG);text('15 / ACENTO',797,226,13,color=BG)
def luminance(h):
    cs=[int(h[i:i+2],16)/255 for i in (1,3,5)];cs=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in cs]
    return sum(v*k for v,k in zip(cs,[.2126,.7152,.0722]))
for i,(fg,bg,name) in enumerate([(BG,GREEN,'Negro sobre verde'),(FG,BG,'Blanco sobre negro'),(GREEN,BG,'Verde sobre negro'),(GREEN,FG,'Verde sobre blanco')]):
    x=48+i*220;rect(x,301,204,88,bg);text('Aa 123',x+15,319,41,'Body',fg)
    text(name,x,405,11)
    ratio=(max(luminance(fg),luminance(bg))+.05)/(min(luminance(fg),luminance(bg))+.05)
    text(f'{ratio:.2f}:1',x,437,30,'Display',GREEN if ratio>=4.5 else RED)
    text('Apto para texto normal' if ratio>=4.5 else 'No usar para texto',x,481,10,color=MUTED)
note('WCAG 2.2: objetivo 4,5:1 para texto normal y 3:1 para texto grande y elementos de interfaz aplicables. Los estados no dependen solo del color.',530)
end()
# 09 — Typography
page('08 / TIPOGRAFÍA')
title('Potencia arriba. Claridad en todo lo demás.','El logotipo se usa como dibujo vectorial. Ninguna fuente de interfaz lo sustituye.')
label('TITULARES / BARLOW CONDENSED',48,207);label('LECTURA E INTERFAZ / INTER',516,207)
text('DALE PLAY.',48,246,64,'Display');text('A TU MUNDO.',48,312,64,'Display',GREEN)
text('Tu próxima historia empieza aquí.',516,251,20,'Medium')
para('Encuentra una película, descubre un concierto o vuelve al directo que te interesa. El contenido cambia; la experiencia sigue siendo clara.',516,297,385,16,FG)
para('Bold 700 para campañas y titulares. SemiBold 600 para subtítulos. Usar su condensación natural; no estrechar las letras.',48,418,400,13)
para('Regular 400 · Medium 500 · SemiBold 600<br/>Para navegación, botones, fichas, descripciones, horarios y subtítulos. Sin falsa cursiva ni compresión.',516,418,385,13)
note('Barlow Condensed e Inter: SIL Open Font License 1.1. Fuentes y licencias incluidas. La firma propuesta parte de contornos de Inter Black y dos Z dibujadas.',534)
end()
# 10 — Hierarchy
page('09 / JERARQUÍA')
title('Un sistema que funciona en pantalla.','Escala inicial para web: tamaños / interlineados en px. Ajustar al contexto, sin perder jerarquía.')
cols=[48,209,411,530,659]
for x,s in zip(cols,['NIVEL','FAMILIA / PESO','ESCRITORIO','MÓVIL','MUESTRA']):label(s,x,201)
rows=[('H1 / Hero','Barlow Condensed 700','72 / 72','44 / 46','DALE PLAY. A TU MUNDO.'),('H2 / Sección','Barlow Condensed 700','48 / 50','32 / 36','HOY EN ZZTREAM'),('H3 / Tarjeta','Inter 600','24 / 30','20 / 26','Una historia por descubrir'),('Texto','Inter 400','18 / 28','16 / 24','Elige lo que te apetece ver.'),('Botón','Inter 600','16 / 20','16 / 20','Explorar contenido'),('Etiqueta','Inter 600','12 / 16','12 / 16','EN DIRECTO')]
for i,row in enumerate(rows):
    y=239+i*43;line(48,y-10,912,y-10)
    for j,(x,s) in enumerate(zip(cols,row)):text(s,x,y,10 if j==1 else 11,'Display' if j==4 and i<2 else 'Body')
note('Titulares de 2 a 6 palabras, normalmente en mayúsculas. Cuerpo en caja normal, alineado a la izquierda. Lectura orientativa: 45–75 caracteres por línea.',523)
end()
# 11 — Graphics
page('10 / RECURSOS GRÁFICOS')
title('La diagonal marca el ritmo.','Un recurso secundario que une todas las categorías sin convertirlas en una sola estética.')
for i,(head,body) in enumerate([('Cortes a 18°','18° respecto a la vertical en bandas y contenedores. Es una regla de composición, no una modificación de la firma.'),('Patrones de baja intensidad','Repetir la diagonal sobre carbón con contraste bajo. No colocar patrones intensos detrás del texto.'),('Un gesto dominante','Una banda, un corte o una fotografía protagonista. Evitar rayos ilustrados, brillos y decoraciones simultáneas.')]):
    y=205+i*108;label(f'0{i+1}',48,y);text(head,91,y-4,23,'Display');para(body,91,y+29,424,12)
rect(585,201,327,303,CARD)
c.saveState();p=c.beginPath();p.moveTo(585,H-201);p.lineTo(737,H-201);p.lineTo(638,H-504);p.lineTo(585,H-504);p.close();c.setFillColor(HexColor(GREEN));c.drawPath(p,fill=1,stroke=0);c.restoreState()
c.saveState();clip=c.beginPath();clip.rect(585,H-504,327,303);c.clipPath(clip,stroke=0,fill=0)
for x in range(730,1020,23):line(x,201,x-98,504,LINE,2)
c.restoreState()
text('18°',718,400,66,'Display')
end()
# 12 — Photography
page('11 / DIRECCIÓN DE IMAGEN')
title('Historias distintas. Emoción compartida.','Cine, series, música, cultura, documental y deporte conviven sin uniformar su personalidad.')
image('zztream-editorial-original.png',48,201,566,318)
label('SÍ',651,201)
bullets(['Luz con volumen y negros con detalle.','Personas y escenas creíbles.','Variedad de géneros y miradas.','Encuadres con espacio para el mensaje.'],651,229,261,11)
label('EVITAR',651,413)
para('Saturación extrema, rostros tapados, neón artificial y reutilizar el mismo motivo en todas las campañas.',651,437,261,11)
note('Imagen conceptual generada con Magnific / Nano Banana 2. No representa películas, conciertos ni documentales disponibles. En campañas reales, usar material autorizado.',532)
end()
# 13 — Voice
page('12 / VOZ')
title('Hablar de lo que apetece ver.','Mensajes cortos, activos y comprensibles. Intensidad en la idea, no en la exageración.')
label('TERRITORIO VERBAL',48,201)
text('DALE PLAY.',48,239,63,'Display');text('A TU MUNDO.',48,304,63,'Display',GREEN)
para('Lema creativo propuesto. Expresa elección y curiosidad; no promete catálogo ilimitado ni disponibilidad permanente.',48,403,420,13)
label('EN VEZ DE',542,201);para('La experiencia definitiva con absolutamente todo el entretenimiento.',542,226,359,15)
label('MEJOR',542,303);para('Tu próxima historia empieza aquí.',542,328,359,19,FG,'Medium')
label('ACCIONES',542,402);para('Ver ahora · Explorar contenido<br/>Ver programación · Añadir a mi lista',542,427,359,14,FG)
note('No prometer 4K, gratuidad, ausencia de anuncios, exclusivas o derechos sin verificar. «En directo» solo identifica una emisión realmente en curso.',526)
end()
# 14 — Platform
page('13 / PLATAFORMA')
title('Una portada para descubrir.','Aplicación conceptual: la maquetación y los textos son editados; las imágenes de contenido son sintéticas.')
rect(48,194,864,323,CARD,9);logo(67,210,122)
for x,s in [(223,'Inicio'),(295,'Explorar'),(383,'Directos'),(467,'Mi lista'),(817,'Mi cuenta')]:text(s,x,218,10,'Medium',GREEN if s=='Inicio' else FG)
rect(61,249,838,254,BG)
image('zztream-editorial-original.png',489,249,410,254)
label('DESCUBRE ZZTREAM',80,271)
text('DALE PLAY.',80,302,45,'Display');text('A TU MUNDO.',80,348,45,'Display',GREEN)
text('Historias, directos y algo por descubrir.',80,405,11)
button('Explorar contenido',80,440,163)
for x,s in [(48,'01 / MARCA VISIBLE'),(343,'02 / UNA ACCIÓN PRINCIPAL'),(654,'03 / VARIEDAD DE CONTENIDOS')]:label(s,x,536)
end()
# 15 — Components
page('14 / COMPONENTES')
title('El verde guía la siguiente acción.','Retícula de 8 px, radio base de 8 px y espaciados de 16, 24, 32 y 48 px.')
label('ACCIONES',48,204);label('ESTADOS Y LECTURA',528,204)
for x,y,state,lab,s in [(48,243,'normal','NORMAL','Ver ahora'),(264,243,'hover','HOVER','Ver ahora'),(48,352,'focus','FOCO VISIBLE','Ver ahora'),(264,352,'disabled','DESACTIVADO','No disponible')]:
    button(s,x,y,173,state);text(lab,x,y+54,9,'Medium',MUTED)
rect(528,240,384,213,CARD,8);rect(548,260,91,23,GREEN,4);text('EN DIRECTO',558,267,9,'Medium',BG)
text('Hoy · 20:30',663,267,10,color=MUTED)
text('Una noche en el escenario',548,305,22,'Display')
para('Música · Concierto de concepto<br/>Estado, categoría y acción antes que decoración.',548,344,343,12)
text('!  No se ha podido cargar el vídeo.',548,403,11,color=FG)
text('Reintentar',548,426,11,'Medium',GREEN)
para('Área táctil recomendada: 44 × 44 px como mínimo. Conservar foco de 2 px, nombre accesible y alternativa al hover.',48,448,389,12)
note('Color + texto + icono para errores y avisos. El verde de marca no convierte cualquier estado en «éxito». La hora del ejemplo no anuncia un evento real.',530)
end()
# 16 — Broadcast
page('15 / VÍDEO Y RETRANSMISIÓN')
title('Reconocible sin tapar la historia.','Zona segura orientativa: 5% del ancho y del alto. Comprobar subtítulos y controles del reproductor.')
image('zztream-musica-recorte.jpg',48,199,643,318)
c.setDash(4,4)
for a,b,d,e in [(80,215,659,215),(80,501,659,501),(80,215,80,501),(659,215,659,501)]:line(a,b,d,e,FG)
c.setDash()
logo(595,227,49,'blanco',True)
rect(94,231,77,26,GREEN,4);text('EN DIRECTO',101,240,9,'Medium',BG)
rect(94,426,411,61,BG);rect(94,426,5,61,GREEN)
text('LA MÚSICA TAMBIÉN SE VIVE.',112,440,22,'Display');text('zztream · Aplicación conceptual',112,469,10)
label('MARCA DE CANAL',730,205);para('Isotipo blanco en esquina superior. Reducir presencia, no legibilidad.',730,232,182,12)
label('RÓTULOS',730,333);para('Negro o carbón, blanco y un acento verde. No invadir rostros, créditos ni subtítulos.',730,360,182,12)
note('Movimiento: entradas y salidas de 180–250 ms, sin destellos. Respetar movimiento reducido. No etiquetar como directo una pieza grabada.',534)
end()
# 17 — Social
page('16 / REDES SOCIALES')
title('Tres formatos. La misma energía.','Una idea por pieza. La proporción cambia; la marca y la lectura se mantienen.')
rect(48,201,272,272,GREEN);logo(66,220,167,'negro')
text('DALE',66,290,49,'Display',BG);text('PLAY A',66,340,49,'Display',BG);text('TU MUNDO.',66,390,49,'Display',BG)
rect(351,201,243,304,CARD);logo(369,217,143)
image('zztream-musica-recorte.jpg',365,261,215,151)
text('HOY SUENA',369,431,32,'Display');text('EN ZZTREAM.',369,465,32,'Display',GREEN)
rect(647,201,171,304,BG,stroke=LINE);logo(663,227,139,'verde');logo(684,302,99,'verde',True)
text('DESCUBRE',663,405,25,'Display');text('ALGO NUEVO.',663,431,25,'Display');rect(663,469,139,23,GREEN,4);text('Explorar contenido',675,477,8,'Medium',BG)
for x,y,s in [(48,486,'FEED / 1080 × 1080'),(351,519,'FEED / 1080 × 1350'),(647,519,'STORY / 1080 × 1920')]:text(s,x,y,9,'Medium',GREEN)
note('Stories: reservar inicialmente 250 px arriba y abajo, y comprobar la plantilla de cada plataforma. Ejemplos conceptuales; no anuncian estrenos ni eventos reales.',542)
end()
# 18 — Digital mockup
page('17 / MOCKUP DIGITAL')
title('zztream, en todas tus pantallas.','Visual de concepto generado con Magnific usando la firma propuesta y el isotipo de referencia.')
image('zztream-mockup-digital-original.png',48,185,864,365,fit='contain')
end()
# 19 — Physical mockup
page('18 / MOCKUP FÍSICO')
title('Una identidad que sale de la pantalla.','Camiseta, acreditación y micrófono: una marca de entretenimiento, no una equipación deportiva.')
image('zztream-mockup-fisico-original.png',48,202,643,322,fit='contain')
label('PRODUCCIÓN',730,208);para('Usar el SVG maestro para imprimir o bordar. El mockup ilustra el acabado y puede reinterpretar detalles de la firma.',730,236,182,12)
label('MATERIALES',730,388);para('Textil negro, superficies mates y verde intenso. Validar color, tamaño y detalle con una muestra física.',730,416,182,12)
end()
# 20 — Handoff
page('19 / ENTREGA')
title('Todo listo para aplicar la propuesta.','El kit adjunto reúne los recursos realmente incluidos. La aprobación final de marca queda pendiente.')
for i,(h,b) in enumerate([('Logos vectoriales','Firma zztream e isotipo ZZ por separado. SVG de contornos y PNG transparentes en negro, blanco y verde.'),('Imágenes y mockups','Tres originales generados con Magnific a 1K, recortes editoriales derivados y nota de procedencia.'),('Tipografías y sistema','Barlow Condensed, Inter, licencias OFL, tokens CSS y fuentes de construcción del manual.')]):
    y=205+i*100;label(f'0{i+1}',48,y);text(h,91,y-4,25,'Display');para(b,91,y+33,466,12)
label('ANTES DE PUBLICAR',644,205)
bullets(['Usar el vector, no una captura.','Respetar margen y proporción.','Comprobar contraste y foco.','Validar móvil, TV e impresión.','Confirmar derechos y oferta real.','Verificar nombre y registro de marca.'],644,239,268,11)
note('Referencias: fonts.google.com · rsms.me/inter · w3.org/WAI/WCAG22. Continuidad visual desde el material SPORTZZ facilitado. Imágenes: Magnific / Google Nano Banana 2, 225 créditos. Edición 09.11.2026.',528)
end();c.save()

(R/'zztream-tokens.css').write_text('''/* zztream · identidad visual propuesta v1.0 */
:root {
  --zz-lime: #B6FF00; --zz-black: #080B09; --zz-white: #F5F7F3;
  --zz-charcoal: #171D19; --zz-muted: #AFB8B0; --zz-line: #38433B;
  --zz-font-display: "Barlow Condensed", sans-serif;
  --zz-font-body: "Inter", sans-serif;
  --zz-radius: 8px; --zz-space-unit: 8px;
  --zz-space-2: 16px; --zz-space-3: 24px; --zz-space-4: 32px; --zz-space-6: 48px;
  --zz-focus-width: 2px; --zz-touch-target: 44px; --zz-motion: 200ms;
}
@media (prefers-reduced-motion: reduce) { :root { --zz-motion: 0ms; } }
''')

doc=fitz.open(R/'zztream-manual-identidad-v1.pdf')
assert len(doc)==20
thumbs=[];outside=[]
for i,p in enumerate(doc):
    pix=p.get_pixmap(matrix=fitz.Matrix(1.3,1.3));pix.save(R/f'previews/pagina-{i+1:02}.png')
    im=Image.open(R/f'previews/pagina-{i+1:02}.png');im.thumbnail((384,240))
    thumbs.append(im)
    for b in p.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            for s in l['spans']:
                x0,y0,x1,y1=s['bbox']
                if x0<0 or y0<0 or x1>W+1 or y1>H+1:outside.append((i+1,s['text']))
sheet=Image.new('RGB',(384*4,268*5),'#202821');d=ImageDraw.Draw(sheet)
for i,im in enumerate(thumbs):
    x=(i%4)*384;y=(i//4)*268;sheet.paste(im,(x,y));d.text((x+8,y+244),f'{i+1:02} / 20',fill='white')
sheet.save(R/'previews/zztream-manual-contacto.jpg',quality=93)
(R/'validation.json').write_text(json.dumps({'pages':len(doc),'page_size_pt':[W,H],'out_of_page_text':outside,'image_generation_count':3,'magnific_credits':225},indent=2))
assert not outside,outside
print('PDF built and rendered: 20 pages; no out-of-page text.')
