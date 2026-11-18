# SPORTZZ VISUAL ASSETS — COLLECTION 1.0

**EL DEPORTE. SIN PAUSA.** · Edición 09.11.2026

Biblioteca de producción basada en el manual SPORTZZ v1.0 del 27.10.2026.
No es una identidad alternativa y no utiliza los recursos del proyecto zztream.

## Contenido

- Ocho fotografías independientes: atletismo, fútbol, baloncesto, tenis,
  automovilismo, natación, ciclismo y ambiente de estadio.
- Ocho mockups: monitor, portátil, teléfono, tableta, TV, conjunto de tres
  dispositivos, estudio de retransmisión y kit físico.
- Cinco recursos gráficos principales: patrón, conjunto de cortes, textura,
  fondo de estadio y fondo de movimiento. Los cuatro cortes también se exportan
  como SVG independientes; el fondo de movimiento incluye un SVG adicional.
- 70 iconos SVG originales normalizados y un sprite de 70 símbolos.
- Cuatro hojas de contacto requeridas: fotografía, mockups, iconos y gráficos.
  También se incluyen muestra inicial, vistas por familia y revisión de tamaños.
- Catálogo HTML adaptable, buscador de iconos, selector de tamaño y fondos claro/oscuro.
- Manifiestos, registro de prompts, scripts reproducibles e inventario de archivos.

## Directorios

```text
index.html
ASSET-README.md
assets/
  brand/                   SVG SPORTZZ auténticos y fuentes con licencias OFL
  magnific/
    photography/{hero,sports,editorial}/
    mockups/{devices,broadcast,brand-applications}/
    graphics/{patterns,textures,backgrounds}/
    previews/
    manifests/
  icons/
    {navigation,actions,status,data,media}/
    sprite.svg
    icon-manifest.json
sources/
  magnific-references/      Estudios vectoriales, máscaras y sus previews
  rejected/                Dos originales rechazados; NO usar en producción
  scripts/                 Geometría, exportación, validación y catálogo
```

## Catálogo principal

Las rutas completas, dimensiones reales, prompts y aplicaciones están en
`assets/magnific/manifests/sportzz-visual-assets.json`.

| ID | Nombre base obligatorio | Destino |
|---|---|---|
| PHOTO-01 | sportzz-photo-hero-athletics-16x9 | photography/hero |
| PHOTO-02 | sportzz-photo-football-action-16x9 | photography/sports |
| PHOTO-03 | sportzz-photo-basketball-action-16x9 | photography/sports |
| PHOTO-04 | sportzz-photo-tennis-action-16x9 | photography/sports |
| PHOTO-05 | sportzz-photo-motorsport-action-16x9 | photography/sports |
| PHOTO-06 | sportzz-photo-swimming-action-16x9 | photography/sports |
| PHOTO-07 | sportzz-photo-cycling-action-16x9 | photography/sports |
| PHOTO-08 | sportzz-photo-stadium-atmosphere-16x9 | photography/editorial |
| MOCKUP-01 | sportzz-mockup-desktop-monitor-16x9 | mockups/devices |
| MOCKUP-02 | sportzz-mockup-laptop-16x9 | mockups/devices |
| MOCKUP-03 | sportzz-mockup-mobile-phone-4x5 | mockups/devices |
| MOCKUP-04 | sportzz-mockup-tablet-landscape-16x9 | mockups/devices |
| MOCKUP-05 | sportzz-mockup-smart-tv-livingroom-16x9 | mockups/devices |
| MOCKUP-06 | sportzz-mockup-multi-device-16x9 | mockups/devices |
| MOCKUP-07 | sportzz-mockup-broadcast-studio-16x9 | mockups/broadcast |
| MOCKUP-08 | sportzz-mockup-physical-brand-kit-4x3 | mockups/brand-applications |
| GRAPHIC-01 | sportzz-graphic-diagonal-pattern-18deg.svg | graphics/patterns |
| GRAPHIC-02 | sportzz-graphic-signal-cuts.svg | graphics/patterns |
| GRAPHIC-03 | sportzz-graphic-carbon-texture-tile.webp | graphics/textures |
| GRAPHIC-04 | sportzz-graphic-stadium-dark-background-16x9.webp | graphics/backgrounds |
| GRAPHIC-05 | sportzz-graphic-motion-background-16x9.webp | graphics/backgrounds |

Los nombres raster terminan en `.webp`. Los originales llevan `-master.png`.
Las variantes adaptables de fotografía y mockups llevan `-640w` y `-1280w`.

## Resolución y formatos

- Imágenes generadas con **Google Nano Banana 2 a 2K mediante Magnific**.
- Originales panorámicos: 2752 × 1536 px; teléfono: 1856 × 2304 px;
  kit físico: 2400 × 1792 px; textura: 2048 × 2048 px.
- Los originales no son exactamente 16:9/4:5/4:3. Las versiones web usan un
  recorte central mínimo y reducción, **nunca estiramiento ni ampliación**.
- Hero web: 2400 × 1350. Resto de fotografías: 2048 × 1152.
- Mockups horizontales: 2048 × 1152. Teléfono: 1600 × 2000.
  Kit físico: 2048 × 1536. Son tamaños del lienzo, no de su pantalla interior.
- WebP de imagen: calidad 88. Textura seamless: WebP sin pérdida para conservar
  exactamente la igualdad de píxeles en bordes opuestos.
- SVG geométricos editables: sin raster incrustado, sin filtros y sin tipografía.

## Procedencia y transformaciones

Se realizaron 21 generaciones raster: 19 recursos iniciales y dos correcciones
dirigidas. Se generaron dos referencias SVG con Recraft v4 Pro Vector a través
de Magnific: muestra de cinco iconos y estudio de recursos geométricos.

**Coste total comunicado por Magnific: 2.325 créditos**
(21 × 75 + 2 × 375). No se especificaron semillas. No se utilizó un proveedor de
pago alternativo, escalado generativo ni compra de créditos.

Los prompts efectivamente enviados, no solo los propuestos por el briefing,
figuran en `sportzz-generation-log.json`. No se guardan enlaces firmados ni
credenciales. Los originales permanecen descargados y se incluyen en el paquete
completo; no dependen de que continúen activos los enlaces de Magnific.

### Correcciones y diferencias técnicas

1. **Monitor:** la primera generación mostraba la parte trasera. Se rechazó y
   sustituyó por una fotografía frontal apta para composición. Primer intento
   preservado únicamente bajo `sources/rejected/`.
2. **Tenis:** el primer intento inventaba publicidad. Se rechazó y se generó una
   pista de práctica sin publicidad. La escena final muestra un golpe a dos manos;
   no debe emplearse como material de instrucción biomecánica.
3. **Kit físico:** el modelo añadió pequeños pseudo-signos verdes al lanyard.
   Se eliminaron mediante máscara e inpainting local. Se entregan original intacto,
   máscara y `-compositing-master.png`; la versión WebP usa la imagen limpia.
4. **Patrón y cortes:** el estudio vectorial generado no garantizaba continuidad
   ni ángulos exactos. Se reconstruyeron matemáticamente. La referencia se conserva,
   pero no se presenta como arte final.
5. **Textura:** se creó una variante modular mediante mosaico reflejado. Se
   comprueba igualdad exacta entre bordes opuestos del WebP sin pérdida.
6. **Fondo de movimiento:** el modelo interpretó los 18° de manera aproximada.
   El WebP de producción procede de un SVG reconstruido a 18° exactos, sin
   degradados y con centro despejado; el PNG generado se conserva como referencia.
7. **Iconos:** la muestra SVG de Magnific no respetaba la retícula y confundía
   activity con un corazón. Se reconstruyó la geometría para crear una familia
   original coherente. Los 70 archivos son vectores reales, **no 70 salidas nativas
   individuales de Magnific**, ni una hoja raster renombrada. No se importaron
   paths de Font Awesome ni de otra biblioteca comercial.

Los logos SPORTZZ provienen del material de referencia facilitado:
`sportzz-frontend/public/brand/sportzz/`. Se copian sin redibujar ni cambiar su
geometría. Barlow Condensed e Inter se incluyen con sus licencias OFL.

## Uso web e iconos

Montar `assets/` como directorio estático. Los ejemplos de ruta absoluta asumen
que ese directorio se sirve desde la raíz; adaptar el prefijo si corresponde.

```html
<svg width="24" height="24" aria-hidden="true">
  <use href="/assets/icons/sprite.svg#home"></use>
</svg>

<button type="button" aria-label="Buscar">
  <svg width="20" height="20" aria-hidden="true">
    <use href="/assets/icons/sprite.svg#search"></use>
  </svg>
</button>
```

```css
.icon { color: #F5F7F3; width: 24px; height: 24px; }
.icon--accent { color: #B6FF00; }
.section {
  background-color: #171D19;
  background-image: url('/assets/magnific/graphics/patterns/sportzz-graphic-diagonal-pattern-18deg.svg');
  background-repeat: repeat;
}
```

Los símbolos del sprite incluyen sus propios atributos de trazo y heredan
`currentColor`. No es necesario imponer stroke en cada instancia. Conservar la
proporción cuadrada al usar 16, 20, 24 o 32 px. No añadir `vector-effect:
non-scaling-stroke`: el peso nominal se escala de forma proporcional.
Los iconos decorativos usan `aria-hidden`; los botones necesitan nombre accesible.
El icono loader es estático: cualquier animación del producto debe respetar
`prefers-reduced-motion`.

## Pantallas y marcas: composición pendiente

Las superficies se entregan vacías. Identificar las cuatro esquinas de la
pantalla, ajustar la perspectiva de la captura real y enmascarar biseles.
Las pantallas sintéticas no garantizan una relación de aspecto comercial exacta.
No deformar una UI para encajar: adaptar su recorte o su lienzo primero.
El interior del monitor puede parecer ligeramente más alto que 16:9.

Usar los SVG auténticos para aplicar SPORTZZ al kit físico. No extraer marcas de
mockups ni afirmar que sus materiales/color constituyen una prueba de imprenta.

## Revisión y límites

- Hay revisión interna visual y validación técnica de formatos, nombres y rutas.
- Se comprueban 70 archivos independientes, IDs únicos, SVG sin raster, trazo,
  currentColor y renderizado a 16/20/24/32 px sin clipping.
- Los resultados detallados y la revisión del catálogo en Chromium aislado están
  en `assets/magnific/manifests/sportzz-validation-report.json`.
- La fotografía sintética puede contener imprecisiones pequeñas en multitudes,
  equipamiento, biomecánica o arquitectura. No es una certificación anatómica ni
  una reproducción de un evento real.
- **Pendiente:** aprobación final de la marca, comprobaciones de semejanza,
  derechos de imagen/marca y adecuación comercial, además de composición con
  capturas reales. No se inventa una licencia fotográfica ni se declara que las
  personas representadas hayan cedido derechos.
- No usar sintéticos como cobertura documental de competiciones reales.
- No emplear las hojas de contacto ni los recursos rechazados en la interfaz.

## Catálogo local y reconstrucción

El catálogo no necesita conexión externa ni build. Servirlo por HTTP para que
funcione el sprite SVG externo en todos los navegadores; `file://` puede bloquearlo.

```sh
python3 -m http.server 8766 --bind 0.0.0.0
```

Detener el servidor con Ctrl+C al terminar. No se deja ningún servidor ejecutándose
como parte de esta entrega.

Para reconstruir derivados a partir del paquete completo, crear un entorno Python
local e instalar `sources/scripts/requirements.txt`, después ejecutar:

```sh
python3 sources/scripts/build_icons.py
python3 sources/scripts/build_library.py
```

Estos scripts no llaman a Magnific ni consumen créditos. No modifican los
originales PNG. El paquete web ligero excluye masters y fuentes de construcción;
el paquete completo los conserva.
