# SPORTZZ — BRAND PROMO / 10 SECONDS

Edición 09.11.2026 · **EL DEPORTE. SIN PAUSA.**

## Entregables

| Archivo | Contenido |
|---|---|
| `sportzz-brand-promo-10s-master.mp4` | Máster H.264 con textos, SVG oficiales, interfaz conceptual, música/efectos y voz española |
| `sportzz-brand-promo-10s-web.mp4` | Versión H.264 comprimida para web, con voz y sonido |
| `sportzz-brand-promo-10s-silent.mp4` | Composición final sin pista de audio |
| `sportzz-brand-promo-10s-clean.mp4` | Placa limpia sin textos, logos ni interfaz añadida; pantalla vacía y tres segundos finales negros, sin audio |
| `sportzz-brand-promo-10s-web.webm` | Versión web VP9 sin audio, apta para autoplay/loop |
| `sportzz-brand-promo-poster.webp` | Póster estático con los SVG originales y tipografía de marca |
| `previews/sportzz-brand-promo-storyboard.webp` | Fotogramas de revisión con tiempos y números de frame |
| `validation.json` | Resolución, duración, número de fotogramas, códecs y presencia de audio comprobados con FFprobe |
| `generation.json` | Prompts efectivamente enviados, modelos, voz y créditos |

**Resolución final: 1280 × 720, por la indicación posterior «720p» del usuario.**
No es un máster 1080p o 4K ni se ha ampliado para aparentarlo.
Todos los vídeos editados tienen 240 fotogramas a 24 fps y 10,000 segundos.
La entrega es SDR Rec.709; no se etiqueta como HDR ni Dolby Vision.

## Montaje

- **00:00–00:02:** negro inicial breve, impacto de zapatilla sobre tartán,
  mirada de concentración y focos; texto «EL DEPORTE.».
- **00:02–00:04:** fútbol, baloncesto y tenis; texto «SIN PAUSA.», con PAUSA
  en verde SPORTZZ. Los cortes deportivos de la generación son aproximados
  dentro de esta ventana, no un cronometraje biomecánico de las acciones.
- **00:04–00:07:** dispositivo y cámara suave. Interfaz conceptual compuesta
  localmente en la pantalla, más «Explora. Descubre. Vive el directo.».
- **00:07–00:10:** cierre reconstruido en postproducción: negro #080B09,
  banda geométrica a 18° respecto a la vertical, isotipo primero y logotipo
  después. Lema y línea secundaria del briefing. Se omite el CTA opcional
  para no sobrecargar el cierre de tres segundos.

El logotipo y el isotipo proceden de los SVG SPORTZZ auténticos facilitados.
No los ha dibujado un modelo de imagen o vídeo. Las tipografías son Barlow
Condensed Bold e Inter; sus fuentes y licencias OFL se conservan en el proyecto.

## Interfaz conceptual

La pantalla se compone mediante cuatro esquinas revisadas y una homografía
interpolada durante el movimiento de cámara. El archivo editable de referencia es
`source/video/sportzz-concept-ui-authored.png`; las coordenadas están en
`source/video/screen-tracking.json`.

La interfaz muestra únicamente categorías genéricas y navegación: Deportes,
Programación, Directos, Fútbol, Baloncesto y Tenis. No inventa competiciones,
equipos, fechas, resultados ni una programación comercial. Incluye la indicación
«INTERFAZ CONCEPTUAL». Las fotografías de categorías proceden de la colección
SPORTZZ generada previamente y representan escenas ficticias.

Para sustituirla, usar una captura real del producto y conservar el encaje de
pantalla. La versión `clean` permite una composición alternativa sin overlays.

## Audio

Voz sintética de catálogo mediante Magnific / ElevenLabs v3:
**Emilio Salcedo**, descripción de voz española peninsular, natural y segura.
No es un clon de la voz de una persona aportada por el usuario.

Texto:

> Descubre el deporte en streaming. Explora disciplinas, consulta la programación
> y encuentra tu próximo directo. SPORTZZ.

La toma MP3 generada dura aproximadamente 7,63 s y entra a los 0,60 s del montaje.
La base combina el audio nativo de la generación con percusión electrónica seca
y pulsos originales sintetizados localmente. No se ha incorporado música de
Apple, Nike ni de un anuncio existente. La base se reduce bajo la voz y la mezcla
se normaliza con objetivo -16 LUFS y techo -1,5 dBTP.

En el proyecto se conservan voz original, voz colocada en el timeline, base y
mezcla final como stems separados. La revisión técnica del audio no sustituye
la aprobación artística de escucha por el propietario.

## Procedencia, coste y correcciones

- Una generación de vídeo con **Seedance 2.5**, a 720p, con audio: **4.400 créditos**.
- Una generación de voz mediante **ElevenLabs v3**: **28 créditos**.
- **Total: 4.428 créditos de Magnific.** Sin nuevas generaciones de pago.
- La copia de trabajo descargada es el preview H.264 ofrecido por Magnific,
  no el MOV original sin transformar. El MOV permanece disponible desde la
  página de la creación enlazada en `generation.json`.
- El contenedor recibido declaraba 10,05 s. El montaje final se conforma a
  240 fotogramas y se recorta a 10,000 s; no se da por cumplida la duración
  únicamente porque se hubiera solicitado «10 segundos» en el prompt.
- El modelo añadió una marca reconocible en la zapatilla pese a la prohibición.
  Se realizó limpieza temporal local con máscara seguida por SIFT/RANSAC e
  inpainting. Se sustituyen los fotogramas de impacto no registrables por negro
  inicial y se adelanta dos frames el corte a la mirada para evitar una zona
  inestable del último gesto. La placa `clean` también contiene estas correcciones.
- El cierre, la diagonal, los textos y los SVG se incorporan localmente; el modelo
  no determina la geometría final ni la escritura de SPORTZZ.

La imagen sigue siendo sintética: puede contener pequeñas imprecisiones en
equipamiento, manos o biomecánica. La limpieza local de la zapatilla suaviza
parte de la textura. No presentar las escenas como cobertura de un evento real
ni como material técnico de entrenamiento.

## Pendiente antes de una campaña comercial

- Aprobación creativa final y revisión de escucha.
- Comprobaciones de derechos, posibles semejanzas, marcas y contexto comercial.
- Sustitución de la interfaz conceptual por capturas reales cuando existan.

No se inventan licencias fotográficas, musicales ni cesiones de imagen.
El material fuente sin retocar es exclusivamente referencia de edición y no se
debe publicar como la pieza final. Se conserva en la VM, pero **no se incluye
en el ZIP de entrega**, porque contiene la marca de zapatilla rechazada.
El ZIP incluye la placa visual corregida, los stems y los recursos de composición.

## Reconstrucción local

Los scripts en `source/scripts/` no llaman a servicios de pago. Requieren Python,
Pillow, NumPy, OpenCV, CairoSVG, fontTools y un FFmpeg con libx264/libvpx/AAC.

1. `generation_record.py` conserva la ficha de las dos llamadas realizadas.
2. `retouch_source.py` prepara la placa visual corregida.
3. `render_promo.py` genera textos, encaje de pantalla, cierre, audio y exports.

Para repetir también el retoque se necesita la copia fuente conservada en la VM
o recuperar la creación desde Magnific. El script conserva máscaras, coordenadas,
fuentes y SVG. Los intermediarios en
`work/` no son entregables y no es necesario incluirlos en el paquete web.
