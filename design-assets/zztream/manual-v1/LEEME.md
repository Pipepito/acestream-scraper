# zztream · Kit de identidad visual v1.0

## Entrega

- `zztream-manual-identidad-v1.pdf`: manual de 20 páginas apaisadas, con texto
  seleccionable, fuentes incrustadas, firmas vectoriales e índice de navegación.
- `logos/`: logotipo e isotipo separados, en SVG de contornos y PNG transparente.
  Logotipo a 2000 px de ancho; isotipo a 1000 px. Tres versiones: negro, blanco y verde.
- `images/`: tres originales de Magnific y recortes editoriales derivados.
- `fonts/`: Barlow Condensed e Inter, instancias estáticas usadas y licencias OFL.
- `zztream-tokens.css`: colores, tipografías y espaciado base de implementación.
- `PROCEDENCIA.md`: prompts, modelo, resolución, créditos y atribución.
- `source/`: scripts Python reproducibles del sistema y del manual.
- `previews/`: portada, página de plataforma y hoja de contacto.

Propuesta: **DALE PLAY. A TU MUNDO.** Conserva el verde eléctrico, negro y
energía de SPORTZZ, ampliando el territorio a cine, series, música, cultura,
documental y deportes. No define un catálogo comercial confirmado.

## Revisión antes de producción

La firma zztream y el lema son propuestas, pendientes de aprobación y comprobación
legal de nombre y derechos. El isotipo procede del material de referencia del
usuario. Los mockups son orientativos y no sustituyen los vectores.
Los colores CMYK y tamaños mínimos requieren prueba física.

## Reconstrucción opcional

En una copia completa del kit, desde su raíz:

```sh
python3 -m venv .venv
.venv/bin/pip install reportlab pillow fonttools cairosvg pymupdf svglib
.venv/bin/python source/build_manual.py
```

`source/build_manual.py` acepta `ZZTREAM_ASSET_ROOT` como ruta del kit. Utiliza los
logos y las imágenes entregados, sin acceder a Magnific ni gastar créditos.
`build_identity.py` conserva la construcción inicial y requiere el export
original SPORTZZ en su ruta de referencia; no es necesario ejecutarlo.
