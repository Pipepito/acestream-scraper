# Composed workflow specification · review 06

Application evidence pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. Composed design proposals, author-reviewed through the recorded checks; not user-approved or implemented. 146 compositions; 473 field occurrences. Original names and machine values remain unchanged.

Read [interaction contracts](interaction-contracts.md), [source contracts](source-contracts.md), [traceability](traceability-matrix.md), [rendered verification](verification-review-06.md) and [acceptance protocols](acceptance-protocols.md). The local prototype is intentionally not an API/client implementation. Adapter names below describe integration boundaries; use the linked current source for exact callable signatures and request paths.

## Future implementation boundary

A screen is a composed workflow, not necessarily a new route. Dialog-intent compositions can reuse the existing dialog host; on phones use a full-height dialog with the same accessible title, safe Cancel, focus return and dirty guard. Do not add routes merely to mirror this gallery. Existing routing, account gates and API transactions remain authoritative.

Every form below inherits validation before submission, disabled pending submission, local inline errors, server-error draft retention, explicit stale-conflict review, a safe cancel, and the stated transaction boundary. “Default” distinguishes repository defaults from illustrative saved values. A fixture is never permission to change defaults. Blank, null, zero and unknown remain distinct. Server validation remains authoritative; the prototype models representative checks.

Select options are written as `machine value → English / Español`. Optional field values, domain data, IDs, addresses, dates and logs must not be translated. Credentials never persist in prototype storage. All numbers in screenshots are synthetic.

<a id="recording-schedule"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-schedule`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Schedule a programme / Programar una grabación

[Open composition](workflow-prototype.html?screen=recording-schedule) · existing route/context: `/live-tv?channel=demo` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Keep the programme’s exact times, or adjust them before scheduling. / Conserva el horario exacto del programa o ajústalo antes de programar.

**Evidence:** [RecordingDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingDialog.tsx)

**Permission:** recordings; management policy applies to commands. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, capacity, stale. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **capacity:** No recording slot is available for this period. Change the time or review upcoming recordings. / No hay capacidad para este horario. Cambia la hora o revisa las próximas grabaciones.
- **stale:** The programme changed after you opened it. Compare the saved times with the current guide before scheduling. / El programa cambió desde que lo abriste. Compara los horarios guardados con la guía actual antes de programar.

**Implementation constraint for `stale`:** The programme changed after you opened it. Review the saved snapshot and current guide; do not silently replace the times. / El programa cambió desde que lo abriste. Revisa la captura y la guía actual; no sustituyas el horario sin confirmación.

**Read-only context: Coastlines: the Atlantic / Coastlines: the Atlantic**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| TV channel / Canal de TV | Northlight / Northlight |
| Programme snapshot / Horario del programa | 8 Nov 2026 · 20:00–20:45 · Europe/Madrid / 8 Nov 2026 · 20:00–20:45 · Europe/Madrid |
| Recording source / Fuente de grabación | Available channel streams; may differ from the one you are watching. / Emisiones disponibles del canal; pueden diferir de la que estás viendo. |

### Recording times / Horario de grabación

**Save timing:** explicit action. **Action:** Schedule recording / Programar grabación. **Boundary:** `recordingService.create`. Submit this resource only; other sections retain independent state.

**Consequence:** 45 minutes reserved. Guide updates do not reschedule it. / 45 minutos reservados. Actualizar la guía no cambia el horario.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recording.adjust_times` · checkbox | Adjust programme times / Ajustar horario del programa<br>Off keeps the guide’s exact instants. / Desactivado conserva los instantes exactos de la guía. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `recording.timezone` · text | Timezone / Zona horaria<br>Use a city timezone such as Europe/Madrid. New recordings start with your browser timezone; it cannot change when editing. / Usa una zona como Europe/Madrid. Las nuevas grabaciones usan la del navegador; no cambia al editar. | Load current saved/server value; illustrative fixture: Europe/Madrid | Adapter/contract note: IANA name. Browser zone for new recordings; locked when editing. / Nombre IANA. Zona del navegador para nuevas grabaciones; bloqueada al editar.; enabled when recording.adjust_times is on; [API constraint](source-contracts.md#recordings-recordingcreate-timezone) |
| `recording.start_time` · datetime-local | Start / Inicio<br>Allow time for the source to start. Guide changes will not move this recording. / Deja tiempo para iniciar la emisión. Los cambios de guía no moverán esta grabación. | Load current saved/server value; illustrative fixture: 2026-11-08T20:00 | enabled when recording.adjust_times is on; [API constraint](source-contracts.md#recordings-recordingcreate-start_time) |
| `recording.end_time` · datetime-local | End / Fin<br>After start; at most 720 minutes. Exact programme times remain until you edit. / Posterior al inicio; máximo 720 minutos. Se conserva el horario del programa hasta que lo edites. | Load current saved/server value; illustrative fixture: 2026-11-08T20:45 | enabled when recording.adjust_times is on; [API constraint](source-contracts.md#recordings-recordingcreate-end_time) |

**Explanation:** Needs an active TV channel with an enabled stream, recording permission and persistent storage. Opening this form records nothing. / Requiere un canal de TV activo con una emisión activada, permiso y almacenamiento persistente. Abrir el formulario no graba nada.

**Contextual exits:** [Repeated or missing clock time / Hora repetida o inexistente](workflow-prototype.html?screen=recording-dst); [Record now / Grabar ahora](workflow-prototype.html?screen=recording-now).

<a id="recording-dst"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-dst`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Choose the exact time / Elegir la hora exacta

[Open composition](workflow-prototype.html?screen=recording-dst) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** This local time happens twice when clocks go back. / Esta hora local se repite cuando se retrasa el reloj.

**Evidence:** [recordingTimes.ts](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/utils/recordingTimes.ts)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, gap. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **gap:** This time does not exist in Europe/Madrid. Choose a time before 02:00 or from 03:00. / Esta hora no existe en Europe/Madrid. Elige una hora anterior a las 02:00 o a partir de las 03:00.

**Explanation:** Synthetic clock-change example: 25 October 2026, Europe/Madrid. The two 02:30 times are different instants. / Ejemplo del cambio de hora: 25 de octubre de 2026, Europe/Madrid. Las dos horas 02:30 son instantes distintos.

### Resolve both times / Precisar ambos horarios

**Save timing:** explicit action. **Action:** Use these instants / Usar estos instantes. **Boundary:** `recordingService.create / edit`. Submit this resource only; other sections retain independent state.

**Consequence:** The schedule uses the selected UTC instants; changing interface language does not change them. / La programación usa los instantes UTC elegidos; cambiar el idioma no los modifica.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recording.start_choice` · select | Which 02:30 start? / ¿Qué inicio a las 02:30?<br>No choice is selected for an ambiguous edited time. / Una hora editada ambigua no tiene selección inicial. | Load current saved/server value; illustrative fixture:  | required=True;  → Choose an instant / Elige un instante; 2026-10-25T00:30:00Z → 02:30 UTC+02 · first / 02:30 UTC+02 · primera; 2026-10-25T01:30:00Z → 02:30 UTC+01 · second / 02:30 UTC+01 · segunda |
| `recording.end_choice` · select | Which 02:50 end? / ¿Qué fin a las 02:50?<br>Choose an instant after the start. We show the offset and UTC value. / Elige un instante posterior al inicio. Mostramos el desfase y el valor UTC. | Load current saved/server value; illustrative fixture:  | required=True;  → Choose an instant / Elige un instante; 2026-10-25T00:50:00Z → 02:50 UTC+02 · first / 02:50 UTC+02 · primera; 2026-10-25T01:50:00Z → 02:50 UTC+01 · second / 02:50 UTC+01 · segunda |

**Explanation:** Spring gap: 29 March 2026 at 02:30 does not exist here. Keep the entered value, mark the field and require a valid time; never move it to 03:30 silently. / Salto de primavera: el 29 de marzo de 2026 a las 02:30 no existe aquí. Conserva el valor, marca el campo y exige una hora válida; nunca lo cambies a las 03:30 en silencio.

**Contextual exits:** [Back to schedule / Volver a programación](workflow-prototype.html?screen=recording-schedule).

<a id="recording-now"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-now`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Record now / Grabar ahora

[Open composition](workflow-prototype.html?screen=recording-now) · existing route/context: `/live-tv` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Capture this TV channel until the selected end time. / Graba este canal de TV hasta la hora elegida.

**Evidence:** [RecordingDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Northlight / Northlight**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Start / Inicio | Now · fixed when this intent opens / Ahora · fijado al abrir esta solicitud |
| Source / Fuente | Selected from the TV channel’s available streams / Se elige entre las emisiones disponibles del canal |

### When should it stop? / ¿Cuándo debe terminar?

**Save timing:** explicit action. **Action:** Start recording / Iniciar grabación. **Boundary:** `recordingService.create`. Submit this resource only; other sections retain independent state.

**Consequence:** Recording request accepted; capture may still be starting. / Solicitud aceptada; la captura puede estar iniciándose.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recording.end_time` · datetime-local | End / Fin<br>1–720 minutes from now. Server admission checks storage and capacity again. / De 1 a 720 minutos desde ahora. El servidor vuelve a comprobar espacio y capacidad. | Load current saved/server value; illustrative fixture: 2026-11-07T21:00 | required=True |

**Contextual exits:** [Starting and recovering / Inicio y recuperación](workflow-prototype.html?screen=recording-active); [Recording settings / Ajustes de grabación](workflow-prototype.html?screen=recording-settings).

<a id="recording-active"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-active`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Recording in progress / Grabación en curso

[Open composition](workflow-prototype.html?screen=recording-active) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** A short interruption is visible without hiding the captured parts. / Una interrupción breve queda visible sin ocultar las partes capturadas.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, starting, finalizing, interrupted. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **starting:** Waiting for an eligible source. No recorded duration is known yet. / Esperando una emisión apta. Aún no se conoce la duración grabada. Page title: Starting recording / Iniciando grabación.
- **finalizing:** Capture stopped. Files are being finalized; playback is available only when a part is ready. / La captura terminó. Finalizando archivos; solo se reproducen las partes listas. Page title: Finalizing recording / Finalizando grabación.
- **interrupted:** Restart detected. The recording journal is being recovered. Previous parts remain visible. / Se detectó un reinicio. Recuperando el registro de grabación. Las partes anteriores siguen visibles. Page title: Recovering recording / Recuperando grabación.

**Read-only context: Coastlines: the Atlantic / Coastlines: the Atlantic**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| State / Estado | Recovering · trying another available source / Recuperando · probando otra emisión disponible |
| Captured / Capturado | 18 min · 0.7 GiB · synthetic / 18 min · 0,7 GiB · ficticio |
| Planned end / Fin previsto | 21:00 · Europe/Madrid / 21:00 · Europe/Madrid |
| Gap / Interrupción | 20:18–20:20 · capture interrupted / 20:18–20:20 · captura interrumpida |

### Change the end time / Cambiar la hora de fin

**Save timing:** explicit action. **Action:** Save end time / Guardar fin. **Boundary:** `recordingService.edit`. Submit this resource only; other sections retain independent state.

**Consequence:** The requested end changed; already captured media is retained. / Se cambió el fin solicitado; se conserva lo ya capturado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recording.end_time` · datetime-local | End / Fin<br>Only the end time can change during recording. The start and timezone stay fixed. / Solo se puede cambiar el fin durante la grabación. El inicio y la zona permanecen fijos. | Load current saved/server value; illustrative fixture: 2026-11-07T21:00 | Adapter/contract note: Start and timezone are locked for an active recording. Save uses its current revision. / El inicio y la zona están bloqueados para una grabación activa. Se guarda con la revisión actual. |

**Stop recording / Detener grabación:** Stop Coastlines: the Atlantic now? The captured part remains available if finalization succeeds. / ¿Detener Coastlines: the Atlantic ahora? La parte capturada estará disponible si finaliza correctamente.

Result copy: Stop requested. Finalizing the captured files; this is not file deletion. / Detención solicitada. Finalizando los archivos; no se están eliminando.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Parts and gaps / Partes e interrupciones](workflow-prototype.html?screen=recording-parts).

### Authored composition for `starting`

[Open this state](workflow-prototype.html?screen=recording-active&state=starting). This replaces the default content rather than placing a warning over contradictory fixture data.

**Read-only context: Coastlines: the Atlantic / Coastlines: the Atlantic**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| State / Estado | Starting · waiting for source / Iniciando · esperando emisión |
| Captured / Capturado | No captured media yet / Todavía sin contenido capturado |
| Planned end / Fin previsto | 21:00 · Europe/Madrid / 21:00 · Europe/Madrid |
| Gap / Interrupción | No captured media yet / Todavía sin contenido capturado |

**Retained editor:** Change the end time / Cambiar la hora de fin. Same fields and transaction defined above; state eligibility can disable editing.

**Retained command:** Stop recording / Detener grabación. Disabled while finalizing or recovering the interrupted journal.

**Contextual exits:** [Parts and gaps / Partes e interrupciones](workflow-prototype.html?screen=recording-parts).

### Authored composition for `finalizing`

[Open this state](workflow-prototype.html?screen=recording-active&state=finalizing). This replaces the default content rather than placing a warning over contradictory fixture data.

**Read-only context: Coastlines: the Atlantic / Coastlines: the Atlantic**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| State / Estado | Finalizing saved parts / Finalizando partes guardadas |
| Captured / Capturado | 18 min · 0.7 GiB · synthetic / 18 min · 0,7 GiB · ficticio |
| Planned end / Fin previsto | 21:00 · Europe/Madrid / 21:00 · Europe/Madrid |
| Gap / Interrupción | 20:18–20:20 · capture interrupted / 20:18–20:20 · captura interrumpida |

**Retained editor:** Change the end time / Cambiar la hora de fin. Same fields and transaction defined above; state eligibility can disable editing.

**Retained command:** Stop recording / Detener grabación. Disabled while finalizing or recovering the interrupted journal.

**Contextual exits:** [Parts and gaps / Partes e interrupciones](workflow-prototype.html?screen=recording-parts).

### Authored composition for `interrupted`

[Open this state](workflow-prototype.html?screen=recording-active&state=interrupted). This replaces the default content rather than placing a warning over contradictory fixture data.

**Read-only context: Coastlines: the Atlantic / Coastlines: the Atlantic**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| State / Estado | Interrupted · recovering journal / Interrumpida · recuperando registro |
| Captured / Capturado | 18 min · 0.7 GiB · synthetic / 18 min · 0,7 GiB · ficticio |
| Planned end / Fin previsto | 21:00 · Europe/Madrid / 21:00 · Europe/Madrid |
| Gap / Interrupción | 20:18–20:20 · capture interrupted / 20:18–20:20 · captura interrumpida |

**Retained editor:** Change the end time / Cambiar la hora de fin. Same fields and transaction defined above; state eligibility can disable editing.

**Retained command:** Stop recording / Detener grabación. Disabled while finalizing or recovering the interrupted journal.

**Contextual exits:** [Parts and gaps / Partes e interrupciones](workflow-prototype.html?screen=recording-parts).

<a id="recording-parts"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-parts`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Parts and playback / Partes y reproducción

[Open composition](workflow-prototype.html?screen=recording-parts) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Play each available part; the missing interval is not hidden. / Reproduce cada parte disponible; el intervalo perdido queda visible.

**Evidence:** [RecordingPlayback.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingPlayback.tsx); [recordings.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/recordings.py)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unsupported, preparing, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unsupported:** This part cannot play in the browser. Download the original or prepare a supported compatible copy. / Esta parte no se puede reproducir en el navegador. Descarga el original o prepara una copia compatible.
- **preparing:** Preparing playback for Part 1. Original files are unchanged. / Preparando reproducción de la Parte 1. Los originales no cambian.
- **art-absent:** No artwork is available. Names and actions are ready. / No hay imagen disponible. Los nombres y acciones siguen listos.
- **art-slow:** Artwork is taking longer. Continue without it. / La imagen tarda. Puedes continuar sin ella.
- **art-blocked:** Artwork could not be loaded from this address. Use the text details. / No se pudo cargar la imagen de esta dirección. Consulta los datos.
- **art-rejected:** This image type is not supported. Use the text details. / El tipo de imagen no es compatible. Consulta los datos.
- **art-oversized:** The image exceeds the safe size limit. It has not been opened. / La imagen supera el límite seguro. No se ha abierto.
- **art-decode-failed:** This image could not be displayed. Try loading it again. / No se pudo mostrar la imagen. Prueba a cargarla de nuevo.
- **art-changed:** The artwork changed. Load the new image when you are ready. / La imagen cambió. Carga la nueva cuando quieras.

**Player region:** Coastlines: the Atlantic · Part 1 · ready · static player illustration / Parte 1 · lista · ilustración estática del reproductor. Static illustration only; use the media interaction contract for ownership and integrated acceptance.

**Original parts / Partes originales**

- Part 1 / Parte 1: 20:00–20:18 · 0.7 GiB · ready / 20:00–20:18 · 0,7 GiB · lista [Open related workflow](workflow-prototype.html?screen=recording-copy).
- Missing interval / Intervalo perdido: 20:18–20:20 · no media / 20:18–20:20 · sin archivo
- Part 2 / Parte 2: 20:20–20:45 · 0.9 GiB · ready / 20:20–20:45 · 0,9 GiB · lista [Open related workflow](workflow-prototype.html?screen=recording-copy).

**Choose a part / Elegir parte:** Preparing this part for browser playback. Closing releases only this viewer. / Preparando esta parte para el navegador. Cerrar libera solo este espectador.

No automatic selection. Exactly one choice. Show row-specific result; expire selection on review-token/revision changes.

**Protect recording / Proteger grabación:** Protect all saved parts from deletion and retention cleanup? / ¿Proteger todas las partes frente a eliminación manual y automática?

Result copy: Protected. Remove protection explicitly before deleting. / Protegida. Quita la protección expresamente antes de eliminar.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Delete files / Eliminar archivos](workflow-prototype.html?screen=recording-delete); [Storage and retention / Espacio y conservación](workflow-prototype.html?screen=recording-storage).

<a id="recording-copy"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-copy`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Prepare a compatible copy / Preparar una copia compatible

[Open composition](workflow-prototype.html?screen=recording-copy) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Keep the original and create an additional file for your player. / Conserva el original y crea otro archivo para tu reproductor.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, failed, ready-copy. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **failed:** Preparation failed. The original remains available. Retry preparation after checking storage. / La preparación falló. El original sigue disponible. Reintenta tras revisar el espacio.
- **ready-copy:** Compatible copy ready. Both original and copy appear under Part 1. / Copia compatible lista. El original y la copia aparecen en la Parte 1.

**Read-only context: Part 1 / Parte 1**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Original / Original | MPEG-TS · H.264 / AC-3 · synthetic / MPEG-TS · H.264 / AC-3 · ficticio |
| Space / Espacio | The copy needs additional disk space; its final size is unknown. / La copia necesita espacio adicional; su tamaño final es desconocido. |

### Copy type / Tipo de copia

**Save timing:** explicit action. **Action:** Prepare copy / Preparar copia. **Boundary:** `recordingService.convert`. Submit this resource only; other sections retain independent state.

**Consequence:** Queued for preparation. Scheduled recording takes priority. / En cola de preparación. Grabar tiene prioridad.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `conversion.profile` · select | Compatibility / Compatibilidad<br>MP4 remux keeps codecs. AAC converts audio; neither replaces the original. / MP4 conserva los códecs. AAC convierte el audio; ninguna sustituye el original. | Load current saved/server value; illustrative fixture: remux | remux → MP4 · keep video and audio / MP4 · conservar vídeo y audio; aac → MP4 · AAC audio / MP4 · audio AAC; [API constraint](source-contracts.md#recordings-recordingconversion-profile) |

**Preparation / Preparación**

- Waiting for recording / Esperando a la grabación: Preparation resumes when capture no longer needs the resources. / La preparación continúa cuando la captura libera los recursos.
- Original retained / Original conservado: Download original remains available when no file hold prevents it. / El original sigue disponible para descargar según su estado.

<a id="recording-settings"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-settings`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Recording settings / Ajustes de grabación

[Open composition](workflow-prototype.html?screen=recording-settings) · existing route/context: `/settings?tab=automation` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** One shared editor, reached from Recordings and Settings. / Un editor compartido, accesible desde Grabaciones y Ajustes.

**Evidence:** [RecordingSettingsFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingSettingsFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, unavailable. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unavailable:** Recording storage is not configured. Ask the server owner to provide a persistent RECORDINGS_DIR; settings cannot create a disk mount. / El almacenamiento no está configurado. Pide al propietario un RECORDINGS_DIR persistente; estos ajustes no crean un montaje.

**Explanation:** Recording folder is deployment-owned. Example: persistent storage is available. No path is edited here. / La carpeta se configura en el despliegue. Ejemplo: hay almacenamiento persistente. Aquí no se edita la ruta.

### Capture and storage limits / Límites de captura y espacio

**Save timing:** explicit action. **Action:** Save recording settings / Guardar ajustes de grabación. **Boundary:** `recordingService.configure`. Submit this resource only; other sections retain independent state.

**Consequence:** Only recording settings are saved. Retention changes can delete eligible files on cleanup. / Solo se guardan estos ajustes. La limpieza puede eliminar archivos elegibles.

**Confirmation:** Review before saving: disabling stops active recordings and cancels schedules. Retention deletes eligible unprotected files. Saved files remain when merely disabling. / Antes de guardar: desactivar detiene grabaciones y cancela programaciones. La conservación elimina archivos elegibles sin protección. Desactivar por sí solo conserva archivos.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recordings.enabled` · checkbox | Enable recordings / Activar grabaciones<br>Off by default. Disabling stops active recordings and cancels future ones; saved files remain. / Desactivado por defecto. Al desactivar se detienen las grabaciones y se cancelan las futuras; se conservan archivos. | Load current saved/server value; illustrative fixture: True | [API constraint](source-contracts.md#recordings-recordingsettings-enabled) |
| `recordings.max_concurrent` · number | Simultaneous recordings / Grabaciones simultáneas<br>1–4. More slots need sufficient bandwidth and storage. / 1–4. Más plazas requieren ancho de banda y espacio. | Load current saved/server value; illustrative fixture: 1 | min=1; max=4; [API constraint](source-contracts.md#recordings-recordingsettings-max_concurrent) |
| `recordings.min_free_bytes` · number | Keep free (GiB) / Espacio libre mínimo (GiB)<br>Default 2 GiB; minimum 64 MiB (0.0625 GiB). Recording stops if free space falls below this limit. / Por defecto 2 GiB; mínimo 64 MiB (0,0625 GiB). La grabación se detiene si el espacio libre baja del límite. | Load current saved/server value; illustrative fixture: 2 | min=0.0625; step=any; Adapter/contract note: Default 2 GiB; minimum 64 MiB (0.0625 GiB). API stores bytes. Low space stops capture. / Por defecto 2 GiB; mínimo 64 MiB (0,0625 GiB). La API guarda bytes. El espacio insuficiente detiene la captura.; [API constraint](source-contracts.md#recordings-recordingsettings-min_free_bytes) |
| `recordings.max_recording_bytes` · number | Maximum recording size (GiB) / Tamaño máximo (GiB)<br>Default 100 GiB; minimum 1 MiB. This is a file limit, not a duration estimate. / Por defecto 100 GiB; mínimo 1 MiB. Es un límite de tamaño, no una duración. | Load current saved/server value; illustrative fixture: 100 | min=0.0009765625; step=any; [API constraint](source-contracts.md#recordings-recordingsettings-max_recording_bytes) |
| `recordings.retention_enabled` · checkbox | Delete old unprotected recordings automatically / Eliminar automáticamente grabaciones antiguas sin protección<br>Off keeps files until you delete them. Enabling proposes 30 days. / Desactivado conserva los archivos hasta que los elimines. Al activar se proponen 30 días. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `recordings.retention_days` · number | Delete after (days) / Eliminar después de (días)<br>1–3650. Protected, active and reader-held media cannot be deleted. / 1–3650. No elimina archivos protegidos, activos o en uso. | Load current saved/server value; illustrative fixture: 30 | min=1; max=3650; enabled when recordings.retention_enabled is on; [API constraint](source-contracts.md#recordings-recordingsettings-retention_days) |

**Contextual exits:** [Review storage / Revisar almacenamiento](workflow-prototype.html?screen=recording-storage); [Disable impact preview / Revisar efectos al desactivar](workflow-prototype.html?screen=recording-disable).

<a id="recording-storage"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-storage`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Storage for recordings / Espacio para grabaciones

[Open composition](workflow-prototype.html?screen=recording-storage) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Free space belongs to the recording filesystem. / El espacio libre corresponde al sistema de archivos de grabaciones.

**Evidence:** [RecordingOverview.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/recordings/RecordingOverview.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, low. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **low:** Free space is below the configured reserve. Capture stops; protected recordings remain protected. / El espacio libre está por debajo de la reserva. Se detiene la captura; las grabaciones protegidas siguen protegidas.

**Read-only context: Synthetic storage snapshot / Muestra ficticia de espacio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Available space / Espacio disponible | 18.4 GiB / 18.4 GiB |
| Keep free / Reserva mínima | 2 GiB / 2 GiB |
| Automatic deletion / Eliminación automática | Off / Desactivada |
| Recorded files / Archivos grabados | 6.2 GiB · partial scan, more files may exist / 6,2 GiB · exploración parcial; puede haber más archivos |

**Explanation:** A partial scan is not the total used space. No remaining recording time is promised. / Una exploración parcial no es el total ocupado. No se promete un tiempo de grabación restante.

**Contextual exits:** [Change limits and retention / Cambiar límites y conservación](workflow-prototype.html?screen=recording-settings); [Filesystem details / Detalles del sistema de archivos](workflow-prototype.html?screen=storage); [Review protected files / Revisar archivos protegidos](workflow-prototype.html?screen=recording-parts).

<a id="recording-cancel"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-cancel`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Cancel this schedule / Cancelar esta programación

[Open composition](workflow-prototype.html?screen=recording-cancel) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Review the exact consequence before continuing. / Revisa la consecuencia exacta antes de continuar.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Coastlines: the Atlantic · 8 Nov, 20:00. This programme will not be recorded. Saved files and other schedules remain. / Coastlines: the Atlantic · 8 nov, 20:00. Este programa no se grabará. Se conservan archivos y otras programaciones.

**Cancel this schedule / Cancelar esta programación:** Coastlines: the Atlantic · 8 Nov, 20:00. This programme will not be recorded. Saved files and other schedules remain. / Coastlines: the Atlantic · 8 nov, 20:00. Este programa no se grabará. Se conservan archivos y otras programaciones.

Result copy: Schedule cancelled. It remains in history. / Programación cancelada. Sigue en el historial.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Keep recording files / Conservar archivos](workflow-prototype.html?screen=recording-parts); [Upcoming schedule / Próxima programación](workflow-prototype.html?screen=recording-schedule).

<a id="recording-delete"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-delete`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Delete saved files / Eliminar archivos guardados

[Open composition](workflow-prototype.html?screen=recording-delete) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Review the exact consequence before continuing. / Revisa la consecuencia exacta antes de continuar.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict, held. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **held:** Nothing was deleted. A file is protected, active or in use; refresh its state before retrying. / No se eliminó nada. Hay un archivo protegido, activo o en uso; actualiza su estado antes de reintentar.

**Explanation:** Delete every original and compatible part of Coastlines: the Atlantic? This cannot be undone. The history entry remains. Protected, active or in-use media is rejected. / ¿Eliminar todas las partes originales y compatibles de Coastlines: the Atlantic? Es irreversible. Se conserva el historial. Se rechazan archivos protegidos, activos o en uso.

**Delete saved files / Eliminar archivos guardados:** Delete every original and compatible part of Coastlines: the Atlantic? This cannot be undone. The history entry remains. Protected, active or in-use media is rejected. / ¿Eliminar todas las partes originales y compatibles de Coastlines: the Atlantic? Es irreversible. Se conserva el historial. Se rechazan archivos protegidos, activos o en uso.

Result copy: Files deleted; history remains. Space may not update until the next storage scan. / Archivos eliminados; el historial permanece. El espacio puede tardar hasta la siguiente exploración.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Keep recording files / Conservar archivos](workflow-prototype.html?screen=recording-parts); [Upcoming schedule / Próxima programación](workflow-prototype.html?screen=recording-schedule).

<a id="recording-disable"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** contextual editor or detail. **Canonical editor:** `recording-disable`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Disable all recording / Desactivar las grabaciones

[Open composition](workflow-prototype.html?screen=recording-disable) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Review the exact consequence before continuing. / Revisa la consecuencia exacta antes de continuar.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Example impact: stop 1 active recording and cancel 2 schedules. Saved files remain. Recheck counts before saving; unknown counts are not zero. / Efecto de ejemplo: detener 1 grabación y cancelar 2 programaciones. Se conservan archivos. Recomprueba las cantidades; desconocido no significa cero.

**Disable all recording / Desactivar las grabaciones:** Example impact: stop 1 active recording and cancel 2 schedules. Saved files remain. Recheck counts before saving; unknown counts are not zero. / Efecto de ejemplo: detener 1 grabación y cancelar 2 programaciones. Se conservan archivos. Recomprueba las cantidades; desconocido no significa cero.

Result copy: Recording disabled. Saved files remain available according to file state. / Grabaciones desactivadas. Los archivos guardados permanecen según su estado.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Keep recording files / Conservar archivos](workflow-prototype.html?screen=recording-parts); [Upcoming schedule / Próxima programación](workflow-prototype.html?screen=recording-schedule).

<a id="access-activate"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-activate`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Choose who can use this installation / Elegir quién puede usar esta instalación

[Open composition](workflow-prototype.html?screen=access-activate) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Accounts can be activated now or later in Settings → Access. / Las cuentas se pueden activar ahora o después en Ajustes → Acceso.

**Evidence:** [AccountSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccountSetup.tsx)

**Permission:** bootstrap authority / legacy header; supported transport. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, blocked. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **blocked:** Open this installation with HTTPS, or use its private address while connected to your home network. / Abre la instalación por HTTPS o usa su dirección privada desde tu red doméstica.

**Explanation:** This synthetic example uses private-address HTTP on a home connection. Accounts are supported here; HTTP is unencrypted. Public-address HTTP is blocked. / Este ejemplo usa HTTP con dirección privada en una conexión doméstica. Admite cuentas; HTTP no cifra la conexión. HTTP con dirección pública está bloqueado.

### First administrator / Primer administrador

**Save timing:** explicit action. **Action:** Create administrator / Crear administrador. **Boundary:** `accessService.bootstrap`. Submit this resource only; other sections retain independent state.

**Consequence:** Accounts enabled. Public viewing and trusted IPTV still have separate policies. / Cuentas activadas. El acceso público y el IPTV de confianza mantienen políticas independientes.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `bootstrap.enabled` · checkbox | Enable accounts / Activar cuentas<br>If off, anyone who can reach the app can manage it, subject to the existing API token. / Si se desactiva, quien acceda a la app podrá administrarla, salvo la protección del token existente. | Load current saved/server value; illustrative fixture: True | [API constraint](source-contracts.md#access-bootstrap-enabled) |
| `account.username` · text | Username / Usuario<br>1–64 characters: letters, numbers, underscore, dot or hyphen. Cannot rename an existing account here. / 1–64 caracteres: letras, números, guion bajo, punto o guion. Aquí no se renombra una cuenta. | Load current saved/server value; illustrative fixture: viewer-demo | required=True; maxlength=64; pattern=[a-zA-Z0-9_.-]+; [API constraint](source-contracts.md#access-credentials-username) |
| `account.password` · password | New password / Contraseña nueva<br>12–128 Unicode characters. Use a password you do not share with players. / 12–128 caracteres Unicode. Usa una contraseña que no compartas con reproductores. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=128; minlength=12; [API constraint](source-contracts.md#access-passwordchange-password) |
| `bootstrap.password_confirmation` · password | Confirm password / Confirmar contraseña<br>Must match the new password. / Debe coincidir con la contraseña nueva. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True |
| `bootstrap.legacy_token` · password | Existing API token / Token de API existente<br>Only shown when deployment token protection exists. Sent as a header, never copied into a public URL. / Solo se muestra si existe protección de token. Se envía en cabecera, nunca en una URL pública. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | Advanced disclosure |
| `bootstrap.migrate_legacy_token` · checkbox | Keep the existing token for playback only / Conservar el token existente solo para reproducción<br>Required by the current activation flow when a legacy token exists. Administrative scripts need a new header credential. / Obligatorio en la activación actual si existe un token anterior. Los scripts administrativos necesitan otra credencial de cabecera. | Load current saved/server value; illustrative fixture: False | Advanced disclosure; [API constraint](source-contracts.md#access-bootstrap-migrate_legacy_token) |

**Contextual exits:** [Public viewing policy / Política de acceso público](workflow-prototype.html?screen=access-policy); [Connection restrictions / Restricciones de conexión](workflow-prototype.html?screen=access-transport).

### Authored composition for `blocked`

[Open this state](workflow-prototype.html?screen=access-activate&state=blocked). This replaces the default content rather than placing a warning over contradictory fixture data.

**Explanation:** Accounts cannot be activated over public-address HTTP. Open this installation using HTTPS, or its private address from your home network. / No se pueden activar cuentas por HTTP público. Abre la instalación por HTTPS o por su dirección privada desde casa.

**Read-only context: Connection / Conexión**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Address type / Tipo de dirección | Public hostname · unencrypted HTTP / Nombre público · HTTP sin cifrar |
| Password entry / Entrada de contraseña | Unavailable on this connection / No disponible en esta conexión |

**Contextual exits:** [Supported connections / Conexiones compatibles](workflow-prototype.html?screen=access-transport).

<a id="access-login"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-login`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Sign in / Iniciar sesión

[Open composition](workflow-prototype.html?screen=access-login) · existing route/context: `/watch` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Return to the permitted page after signing in. / Vuelve a la página permitida tras iniciar sesión.

**Evidence:** [LoginForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/LoginForm.tsx)

**Permission:** public sign-in. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, expired, denied. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **expired:** Your session expired. Sign in again, then review any unfinished changes before saving. / Tu sesión caducó. Inicia sesión y revisa los cambios pendientes antes de guardarlos.
- **denied:** Those details did not sign you in. Check the username and password and try again. / No se pudo iniciar sesión. Comprueba el usuario y la contraseña e inténtalo de nuevo.

**Implementation constraint for `expired`:** Your session expired. Sign in again. Protected data is cleared; do not replay an interrupted save automatically. / La sesión caducó. Inicia sesión otra vez. Se borran los datos protegidos; no se repite un guardado interrumpido.

**Implementation constraint for `denied`:** Those details did not sign you in. Check the username and password; do not reveal whether an account exists. / Esos datos no permiten iniciar sesión. Revisa usuario y contraseña; no se revela si la cuenta existe.

### Your account / Tu cuenta

**Save timing:** explicit action. **Action:** Sign in / Iniciar sesión. **Boundary:** `accessService.login`. Submit this resource only; other sections retain independent state.

**Consequence:** Signed in. Only permitted viewing features are available. / Sesión iniciada. Solo están disponibles las funciones permitidas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `account.username` · text | Username / Usuario<br>1–64 characters: letters, numbers, underscore, dot or hyphen. Cannot rename an existing account here. / 1–64 caracteres: letras, números, guion bajo, punto o guion. Aquí no se renombra una cuenta. | Load current saved/server value; illustrative fixture: viewer-demo | required=True; maxlength=64; pattern=[a-zA-Z0-9_.-]+; [API constraint](source-contracts.md#access-credentials-username) |
| `login.password` · password | Password / Contraseña<br>Enter your account password. Password reset is an owner command, not a guessed recovery link. / Introduce la contraseña de tu cuenta. El propietario puede restablecerla con un comando. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=128 |

**Contextual exits:** [Connection help / Ayuda de conexión](workflow-prototype.html?screen=access-transport); [Viewing permissions / Permisos de visualización](workflow-prototype.html?screen=viewer).

<a id="access-account"></a>

**Simplified location:** Settings → Account permissions. **Composition:** section. **Canonical editor:** `access-account`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Account permissions / Permisos de cuenta

[Open composition](workflow-prototype.html?screen=access-account) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Give viewer-demo only the features they should use. / Concede a viewer-demo solo las funciones que deba usar.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, last-admin. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **last-admin:** This is the last enabled administrator. Keep it enabled and administrative, or create another administrator first. Nothing changed. / Es el último administrador activo. Mantenlo activo y administrador, o crea otro antes. No se cambió nada.

### viewer-demo / viewer-demo

**Save timing:** explicit action. **Action:** Save account / Guardar cuenta. **Boundary:** `accessService.updateUser`. Submit this resource only; other sections retain independent state.

**Consequence:** Account updated. Its sessions are signed out and API credentials revoked when permissions change. / Cuenta actualizada. Al cambiar permisos se cierran sus sesiones y se revocan sus credenciales API.

**Confirmation:** Changing permissions signs out viewer-demo and revokes its credentials. Players using those credentials need replacement links. Continue? / Cambiar permisos cierra las sesiones de viewer-demo y revoca sus credenciales. Los reproductores necesitan enlaces nuevos. ¿Continuar?. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `account.administrator` · checkbox | Administrator / Administrador<br>Administrators manage the installation and can use all viewing features. / Los administradores gestionan la instalación y acceden a todas las funciones. | Load current saved/server value; illustrative fixture: False | [API constraint](source-contracts.md#access-accountupdate-administrator) |
| `account.enabled` · checkbox | Account enabled / Cuenta activada<br>Disabling signs out this account. The last enabled administrator cannot be disabled or demoted. / Al desactivar se cierran sus sesiones. No se puede desactivar ni degradar al último administrador. | Load current saved/server value; illustrative fixture: True | [API constraint](source-contracts.md#access-accountupdate-enabled) |
| `permissions.live` · checkbox | Live TV / TV en directo<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.channels` · checkbox | Channels / Canales<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.guide` · checkbox | Programme guide / Guía de programación<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.events` · checkbox | Events / Eventos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.recordings` · checkbox | Recordings / Grabaciones<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.playlists` · checkbox | Playlists / Listas de reproducción<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.cast` · checkbox | Cast to my devices / Enviar a mis dispositivos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.cast_server` · checkbox | Cast to server devices / Enviar a dispositivos del servidor<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |

**Explanation:** Casting to your devices and controlling server devices have separate permissions. Remote control also needs to be enabled. / Enviar a tus dispositivos y controlar los del servidor tienen permisos distintos. El control remoto también debe estar activado.

**Contextual exits:** [Create account / Crear cuenta](workflow-prototype.html?screen=access-create); [Review sessions / Revisar sesiones](workflow-prototype.html?screen=access-sessions).

<a id="access-create"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-create`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Create an account / Crear una cuenta

[Open composition](workflow-prototype.html?screen=access-create) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Start with viewing permissions and review the exact scope. / Empieza con permisos de visualización y revisa su alcance.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### New account / Cuenta nueva

**Save timing:** explicit action. **Action:** Create account / Crear cuenta. **Boundary:** `accessService.createUser`. Submit this resource only; other sections retain independent state.

**Consequence:** Account created. Share its initial password through a private channel. / Cuenta creada. Comparte la contraseña inicial por un canal privado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `account.username` · text | Username / Usuario<br>1–64 characters: letters, numbers, underscore, dot or hyphen. Cannot rename an existing account here. / 1–64 caracteres: letras, números, guion bajo, punto o guion. Aquí no se renombra una cuenta. | Load current saved/server value; illustrative fixture: viewer-demo | required=True; maxlength=64; pattern=[a-zA-Z0-9_.-]+; [API constraint](source-contracts.md#access-credentials-username) |
| `account.password` · password | New password / Contraseña nueva<br>12–128 Unicode characters. Use a password you do not share with players. / 12–128 caracteres Unicode. Usa una contraseña que no compartas con reproductores. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=128; minlength=12; [API constraint](source-contracts.md#access-passwordchange-password) |
| `account.administrator` · checkbox | Administrator / Administrador<br>Off by default. Giving this permission grants management access. / Desactivado por defecto. Este permiso concede administración. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `permissions.live` · checkbox | Live TV / TV en directo<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.channels` · checkbox | Channels / Canales<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.guide` · checkbox | Programme guide / Guía de programación<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.events` · checkbox | Events / Eventos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.recordings` · checkbox | Recordings / Grabaciones<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.playlists` · checkbox | Playlists / Listas de reproducción<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.cast` · checkbox | Cast to my devices / Enviar a mis dispositivos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |
| `permissions.cast_server` · checkbox | Cast to server devices / Enviar a dispositivos del servidor<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | disabled when account.administrator is on |

**Contextual exits:** [Edit existing permissions / Editar permisos existentes](workflow-prototype.html?screen=access-account).

<a id="access-policy"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-policy`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Viewing without signing in / Ver sin iniciar sesión

[Open composition](workflow-prototype.html?screen=access-policy) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Public pages, IPTV clients and administrators have different access rules. / Las páginas públicas, clientes IPTV y administradores tienen reglas distintas.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Public viewing and IPTV / Acceso público e IPTV

**Save timing:** explicit action. **Action:** Save viewing policy / Guardar política de acceso. **Boundary:** `accessService.savePolicy`. Submit this resource only; other sections retain independent state.

**Consequence:** Only viewing policy saved. Account permissions and reverse-proxy trust are unchanged. / Solo se guardó la política. Los permisos y la confianza de proxy se mantienen.

**Confirmation:** Review the selected public features and networks before making them accessible without sign-in. / Revisa las funciones y redes seleccionadas antes de permitir el acceso sin sesión.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `public_features.live` · checkbox | Live TV / TV en directo<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | No additional prototype constraint; preserve current source validation. |
| `public_features.channels` · checkbox | Channels / Canales<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | No additional prototype constraint; preserve current source validation. |
| `public_features.guide` · checkbox | Programme guide / Guía de programación<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | No additional prototype constraint; preserve current source validation. |
| `public_features.events` · checkbox | Events / Eventos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | No additional prototype constraint; preserve current source validation. |
| `public_features.cast` · checkbox | Cast to my devices / Enviar a mis dispositivos<br>This feature only. Administrative access is separate. / Solo esta función. La administración es independiente. | Repository default: false for policy; UI account seed live/channels/guide; API account default [] | No additional prototype constraint; preserve current source validation. |
| `policy.public_playlists` · checkbox | Allow public playlists, guides and media / Permitir listas, guías y contenido públicos<br>Off by default. Allows credential-free export and media routes according to policy. / Desactivado por defecto. Permite exportación y contenido sin credenciales según la política. | Load current saved/server value; illustrative fixture: False | [API constraint](source-contracts.md#access-accesspolicy-public_playlists) |
| `policy.local_iptv` · checkbox | Allow IPTV on trusted local networks / Permitir IPTV en redes locales de confianza<br>A proxy or Docker gateway alone is not evidence of local IPTV access. / Un proxy o una pasarela Docker por sí solos no prueban acceso IPTV local. | Load current saved/server value; illustrative fixture: False | [API constraint](source-contracts.md#access-accesspolicy-local_iptv) |
| `policy.local_networks` · text | Trusted IPTV client networks / Redes de clientes IPTV de confianza<br>Comma-separated CIDRs; at most 16. Separate from proxy trust and Cast home networks. / CIDR separados por comas; máximo 16. Independientes de la confianza de proxy y de las redes Cast. | Load current saved/server value; illustrative fixture:  | enabled when policy.local_iptv is on; [API constraint](source-contracts.md#access-accesspolicy-local_networks) |

**Contextual exits:** [Casting permissions and trust / Permisos y confianza de Cast](workflow-prototype.html?screen=casting-settings); [Reverse proxies and tuner access / Proxies y acceso al sintonizador](workflow-prototype.html?screen=network).

<a id="access-password"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-password`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Change your password / Cambiar tu contraseña

[Open composition](workflow-prototype.html?screen=access-password) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** This signs out your sessions and revokes your API credentials. / Se cerrarán tus sesiones y se revocarán tus credenciales API.

**Evidence:** [PasswordForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/PasswordForm.tsx)

**Permission:** signed-in account; own password. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Verify and replace / Verificar y sustituir

**Save timing:** explicit action. **Action:** Change password / Cambiar contraseña. **Boundary:** `accessService.password`. Submit this resource only; other sections retain independent state.

**Consequence:** Password changed. Sign in again and replace revoked playback/API credentials. / Contraseña cambiada. Inicia sesión y sustituye las credenciales revocadas.

**Confirmation:** Continue and sign out every session for this account? All its API credentials will be revoked. / ¿Continuar y cerrar todas las sesiones de esta cuenta? Se revocarán todas sus credenciales API.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `password.current_password` · password | Current password / Contraseña actual<br>Required to authorize the change. / Necesaria para autorizar el cambio. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True |
| `account.password` · password | New password / Contraseña nueva<br>12–128 Unicode characters. Use a password you do not share with players. / 12–128 caracteres Unicode. Usa una contraseña que no compartas con reproductores. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=128; minlength=12; [API constraint](source-contracts.md#access-passwordchange-password) |
| `password.password_confirmation` · password | Confirm new password / Confirmar contraseña nueva<br>Must match exactly; count Unicode characters, not UTF-16 units. / Debe coincidir exactamente; cuenta caracteres Unicode, no unidades UTF-16. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True |

<a id="access-sessions"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-sessions`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Login sessions / Sesiones iniciadas

[Open composition](workflow-prototype.html?screen=access-sessions) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Review the last activity and expiry before signing a session out. / Revisa la actividad y caducidad antes de cerrar una sesión.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **empty:** No sessions were returned. Refresh before interpreting this as successful revocation. / No se devolvieron sesiones. Actualiza antes de interpretarlo como una revocación correcta.

**Sessions · synthetic / Sesiones · ficticias**

- viewer-demo · this session / viewer-demo · esta sesión: Created 7 Nov 16:00 · last active 16:18 · expires 8 Nov 16:00 / Creada 7 nov 16:00 · activa 16:18 · caduca 8 nov 16:00
- viewer-demo · another session / viewer-demo · otra sesión: Created 6 Nov 09:00 · last active 7 Nov 12:00 / Creada 6 nov 09:00 · activa 7 nov 12:00

**Sign out this session / Cerrar esta sesión:** Sign out this session? You will return to Sign in. No other session is selected. / ¿Cerrar esta sesión? Volverás al inicio de sesión. No se selecciona ninguna otra.

Result copy: Session signed out. Protected information is cleared. / Sesión cerrada. Se borran los datos protegidos.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Sign out the other session / Cerrar la otra sesión:** Sign out the selected session for viewer-demo? / ¿Cerrar la sesión seleccionada de viewer-demo?

Result copy: Selected session signed out. / Sesión seleccionada cerrada.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Playback and API credentials / Credenciales IPTV y API](workflow-prototype.html?screen=access-credentials).

<a id="access-credentials"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-credentials`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Playback and API credentials / Credenciales de reproducción y API

[Open composition](workflow-prototype.html?screen=access-credentials) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Create the smallest access scope your client needs. / Crea el ámbito mínimo que necesite tu cliente.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### New credential / Credencial nueva

**Save timing:** explicit action. **Action:** Create credential / Crear credencial. **Boundary:** `accessService.issueCredential`. Submit this resource only; other sections retain independent state.

**Consequence:** Created. The next screen shows it once. Do not include it in screenshots or support reports. / Creada. La siguiente pantalla la muestra una vez. No la incluyas en capturas o informes.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `credential.label` · text | Credential label / Nombre de credencial<br>1–80 characters; use a recognisable client name. / 1–80 caracteres; usa un nombre de cliente reconocible. | Load current saved/server value; illustrative fixture: Demo player | required=True; maxlength=80; [API constraint](source-contracts.md#access-credentialcreate-label) |
| `credential.kind` · select | Access / Acceso<br>Playback credentials may be used in IPTV URLs. Administrative credentials belong only in headers. / Las de reproducción pueden ir en URLs IPTV. Las administrativas solo van en cabeceras. | Load current saved/server value; illustrative fixture: playback | playback → Playback only / Solo reproducción; admin → Administrative API / API administrativa; [API constraint](source-contracts.md#access-credentialcreate-kind) |

**Revoke Demo player / Revocar Demo player:** This credential stops working. Reload IPTV clients with a replacement URL; no undo is available. / Esta credencial dejará de funcionar. Recarga los clientes IPTV con una URL nueva; no se puede deshacer.

Result copy: Credential revoked. Existing URLs need replacement. / Credencial revocada. Hay que sustituir las URLs.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="access-secret"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-secret`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Save your new credential / Guardar la credencial nueva

[Open composition](workflow-prototype.html?screen=access-secret) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Shown once. The value below is deliberately not a usable credential. / Se muestra una vez. El valor inferior no es una credencial utilizable.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict, copy-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **copy-failed:** Copy is unavailable. Select the displayed value and copy it manually before dismissing. / No se puede copiar. Selecciona el valor y cópialo manualmente antes de ocultarlo.

**Synthetic read-only output:**

```text
DEMO — NOT A CREDENTIAL
```

**Copy action:** Copy example value / Copiar valor de ejemplo. Placeholder `DEMO — NOT A CREDENTIAL`; show success or a selectable fallback without logging the value.

**Dismiss credential / Ocultar credencial:** After dismissal you cannot reveal this credential again. Create a new one if you lose it. / Tras ocultarla no podrás volver a verla. Crea otra si la pierdes.

Result copy: Credential hidden. Only its label and scope remain. / Credencial oculta. Solo quedan su nombre y ámbito.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Explanation:** Copy failure must leave the value selectable and visible. Never place a secret in the page URL, analytics or persistent browser preferences. / Si falla la copia, el valor sigue visible y seleccionable. Nunca se guarda en la URL, analítica o preferencias persistentes.

<a id="access-disable"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-disable`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Remove account protection / Quitar la protección de cuentas

[Open composition](workflow-prototype.html?screen=access-disable) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** This is different from disabling one account. / Esto es distinto de desactivar una cuenta.

**Evidence:** [AccessSettings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccessSettings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** All accounts and their credentials will be removed. Anyone who can reach the app can manage it unless deployment API-token protection remains. / Se eliminarán todas las cuentas y credenciales. Quien acceda podrá administrar la app salvo que siga protegida por el token del despliegue.

### Confirm removal / Confirmar retirada

**Save timing:** explicit action. **Action:** Disable user management / Desactivar gestión de usuarios. **Boundary:** `accessService.disable`. Submit this resource only; other sections retain independent state.

**Consequence:** Account protection removed. Existing deployment token policy still applies. / Protección de cuentas retirada. Sigue vigente la política del token del despliegue.

**Confirmation:** Remove every account and credential? This cannot be undone from the catalogue backup. / ¿Eliminar todas las cuentas y credenciales? No se recuperan desde una copia del catálogo.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `access.confirm` · checkbox | I understand account protection will be removed / Entiendo que se quitará la protección de cuentas<br>This does not delete the channel catalogue. / No elimina el catálogo de canales. | Load current saved/server value; illustrative fixture: False | required=True |
| `access.current_password` · password | Administrator password / Contraseña de administrador<br>Required. The independent access store is not a catalogue backup. / Obligatoria. El almacén independiente de acceso no es una copia del catálogo. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True |

<a id="access-transport"></a>

**Simplified location:** Settings → Account permissions. **Composition:** contextual editor or detail. **Canonical editor:** `access-transport`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Use a supported connection / Usar una conexión compatible

[Open composition](workflow-prototype.html?screen=access-transport) · existing route/context: `/settings?tab=access` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Use the right connection for the action you need. / Usa la conexión adecuada para la acción que necesitas.

**Evidence:** [AccountTransportNotice.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/access/AccountTransportNotice.tsx)

**Permission:** informational; no network action. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Connection rules / Reglas de conexión**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Accounts / Cuentas | HTTPS, or private-IP HTTP over a private connection, including Docker NAT. / HTTPS o HTTP con IP privada por una conexión privada, incluido NAT de Docker. |
| Public-address HTTP / HTTP con dirección pública | Accounts blocked, even if this address is trusted for Cast. / Cuentas bloqueadas, aunque la dirección sea de confianza para Cast. |
| Telegram authorization / Autorización Telegram | HTTPS or localhost plus the dedicated Telegram header token. / HTTPS o localhost y el token de cabecera de Telegram. |
| IPTV clients / Clientes IPTV | Separate local-network and playback-credential policy. / Política independiente de redes y credenciales de reproducción. |

**Contextual exits:** [Return to sign in / Volver al inicio de sesión](workflow-prototype.html?screen=access-login); [Review player address / Revisar dirección para reproductores](workflow-prototype.html?screen=public-address).

<a id="channels"></a>

**Simplified location:** TV channels → TV channels. **Composition:** primary destination. **Canonical editor:** `channels`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## TV channels / Canales de TV

[Open composition](workflow-prototype.html?screen=channels) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Organize channels without losing their streams or guide links. / Organiza los canales conservando sus emisiones y vínculos de guía.

**Evidence:** [TVChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannels.tsx); [TVChannelFilters.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelFilters.tsx); [TVChannelsTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelsTable.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **filtered:** No channels match these filters. Clear filters to see the catalogue; this does not stop playback. / Ningún canal coincide. Quita filtros para ver el catálogo; no se detiene la reproducción.

**Contextual exits:** [Add channels / Añadir canales](workflow-prototype.html?screen=add-channels).

### Find channels / Buscar canales

**Save timing:** explicit action. **Action:** Apply filters / Aplicar filtros. **Boundary:** `local URL / catalogue query`. View/preview only; no persistent data mutation.

**Consequence:** Filters applied. The playing channel is retained. / Filtros aplicados. Se conserva el canal en reproducción.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `filter.search` · search | Search / Buscar<br>Filters the complete catalogue before pagination. / Filtra el catálogo completo antes de paginar. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `filter.category` · select | Category / Categoría<br>All categories by default. Original category names are preserved. / Todas por defecto. Se conservan los nombres originales. | Load current saved/server value; illustrative fixture:  |  → All categories / Todas las categorías; Documentary → Documentary / Documentary; News → News / News |
| `filter.status` · select | Status / Estado<br>Active or inactive TV channels. Verified signal is a separate advanced filter. / Canales activos o inactivos. Señal verificada es otro filtro avanzado. | Load current saved/server value; illustrative fixture:  |  → Any status / Cualquier estado; true → Active / Activo; false → Inactive / Inactivo |
| `filter.favorite` · select | Favorites only / Solo favoritos<br>Favorites belong to TV channels. / Los favoritos pertenecen a canales de TV. | Load current saved/server value; illustrative fixture:  |  → Any / Cualquiera; true → Favorites / Favoritos; false → Not favorites / No favoritos |
| `filter.country` · text | Country / País<br>Optional original country code. / Código de país original opcional. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `filter.language` · text | Language / Idioma<br>Channel audio language, not interface language. / Idioma de audio del canal, no de la interfaz. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `filter.epg` · select | Guide mapping / Vinculación de guía<br>A guide link is separate from verified media signal. / El vínculo de guía es independiente de señal. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; yes → Mapped / Vinculada; no → Not mapped / Sin vincular |
| `filter.epg_source_id` · select | Guide source / Fuente de guía<br>Choose the guide source as well as the channel name to avoid mixing identical names. / Elige la fuente de guía además del nombre para distinguir nombres iguales. | Load current saved/server value; illustrative fixture:  | Adapter/contract note: Source-qualified choice; never infer by display name alone. / Elección identificada por fuente; no deduzcas solo por nombre.; Advanced disclosure;  → All sources / Todas; 1 → Sample guide / Sample guide; 2 → Regional guide / Regional guide |
| `filter.streams` · select | Attached streams / Emisiones asignadas<br>Catalogue-wide filter, before sorting and pagination. / Filtro de catálogo completo, antes de ordenar y paginar. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; any → With streams / Con emisiones; none → Without streams / Sin emisiones; multiple → Multiple streams / Varias emisiones |
| `filter.signal` · select | Stream signal / Señal de emisiones<br>Latest identified A/V packets; ID-found alone is not signal. / Últimos paquetes A/V identificados; ID encontrado no es señal. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; verified → At least one verified / Alguna verificada; unverified → None verified / Ninguna verificada; unknown → All not checked / Ninguna comprobada |
| `filter.number` · select | Channel number / Número<br>Presence only. Blank means no filter. / Solo presencia. Vacío no filtra. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; yes → Present / Presente; no → Missing / Ausente |
| `filter.logo_url` · select | Logo / Logo<br>Presence only. Blank means no filter. / Solo presencia. Vacío no filtra. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; yes → Present / Presente; no → Missing / Ausente |
| `filter.website` · select | Website / Web<br>Presence only. Blank means no filter. / Solo presencia. Vacío no filtra. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; yes → Present / Presente; no → Missing / Ausente |
| `filter.description` · select | Description / Descripción<br>Presence only. Blank means no filter. / Solo presencia. Vacío no filtra. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; yes → Present / Presente; no → Missing / Ausente |
| `filter.min_number` · number | Minimum number / Número mínimo<br>Non-negative whole number; blank removes this bound. / Entero no negativo; vacío elimina límite. | Load current saved/server value; illustrative fixture:  | min=0; step=1; Advanced disclosure |
| `filter.max_number` · number | Maximum number / Número máximo<br>Non-negative whole number; blank removes this bound. / Entero no negativo; vacío elimina límite. | Load current saved/server value; illustrative fixture:  | min=0; step=1; Advanced disclosure |
| `filter.min_streams` · number | Minimum streams / Emisiones mínimas<br>Non-negative whole number; blank removes this bound. / Entero no negativo; vacío elimina límite. | Load current saved/server value; illustrative fixture:  | min=0; step=1; Advanced disclosure |
| `filter.max_streams` · number | Maximum streams / Emisiones máximas<br>Non-negative whole number; blank removes this bound. / Entero no negativo; vacío elimina límite. | Load current saved/server value; illustrative fixture:  | min=0; step=1; Advanced disclosure |
| `filter.sort` · select | Sort by / Ordenar por<br>Applied after catalogue-wide filters and before pagination. / Después de filtros de catálogo y antes de paginar. | Load current saved/server value; illustrative fixture: name | name → Name / Nombre; channel_number → Number / Número; category → Category / Categoría; country → Country / País |
| `filter.page_size` · select | Rows per page / Filas por página<br>Changing size resets to first page. Counts describe filtered total. / Cambiar tamaño vuelve a primera página. Recuento del total filtrado. | Load current saved/server value; illustrative fixture: 25 | 10 → 10 / 10; 25 → 25 / 25; 50 → 50 / 50; 100 → 100 / 100 |

**Catalogue · 3 synthetic channels / Catálogo · 3 canales ficticios**

- 1 · Northlight / 1 · Northlight: Favorite · verified 16:00 · Documentary / Favorito · verificado 16:00 · Documentary [Open related workflow](workflow-prototype.html?screen=channel-detail).
- 2 · World 24 / 2 · World 24: Unknown · News / Desconocido · News [Open related workflow](workflow-prototype.html?screen=channel-detail).
- 3 · Atelier / 3 · Atelier: Offline · checked yesterday / Sin señal · comprobado ayer [Open related workflow](workflow-prototype.html?screen=channel-detail).

**Contextual exits:** [Add or edit a TV channel / Añadir o editar canal](workflow-prototype.html?screen=channel-edit); [Reorder complete catalogue / Reordenar catálogo completo](workflow-prototype.html?screen=channel-reorder); [Review stream matches / Revisar coincidencias de emisiones](workflow-prototype.html?screen=stream-match).

**Contextual exits:** [Number and favorite controls / Controles de número y favorito](workflow-prototype.html?screen=channel-inline).

<a id="channel-edit"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-edit`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Edit TV channel / Editar canal de TV

[Open composition](workflow-prototype.html?screen=channel-edit) · existing route/context: `/tv-channels/:id` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Keep channel identity separate from its playable streams. / Separa la identidad del canal de sus emisiones.

**Evidence:** [TVChannelFormDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelFormDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Channel details / Datos del canal

**Save timing:** explicit action. **Action:** Save channel / Guardar canal. **Boundary:** `tvChannelService.create / update`. Submit this resource only; other sections retain independent state.

**Consequence:** Channel metadata saved. Linked streams remain separate. / Datos guardados. Las emisiones vinculadas siguen separadas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `tv.name` · text | Channel name / Nombre del canal<br>Required. Preserve the channel’s own name in both languages. / Obligatorio. Conserva el nombre propio en ambos idiomas. | Load current saved/server value; illustrative fixture: Northlight | required=True |
| `tv.channel_number` · number | Channel number / Número de canal<br>Blank clears the number. Inline inventory edits save on Enter or blur; this form saves with its button. / Vacío borra el número. En la lista se guarda con Intro o al salir; aquí se guarda con el botón. | Load current saved/server value; illustrative fixture: 1 | No additional prototype constraint; preserve current source validation. |
| `tv.category` · text | Category / Categoría<br>Original catalogue value. / Valor original del catálogo. | Load current saved/server value; illustrative fixture: Documentary | No additional prototype constraint; preserve current source validation. |
| `tv.is_active` · checkbox | Active / Activo<br>Hidden channels remain stored. / Los canales ocultos siguen guardados. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `tv.is_favorite` · checkbox | Favorite / Favorito<br>Stored with this TV channel, not in this browser. / Se guarda con el canal, no en este navegador. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `tv.description` · textarea | Description / Descripción<br>Optional channel description; preserve original text. / Descripción opcional; conserva su texto original. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `tv.logo_url` · text | Logo URL / URL del logotipo<br>Optional. A failed image must not hide the channel name. / Opcional. Si falla la imagen, el nombre debe seguir visible. | Load current saved/server value; illustrative fixture: https://images.example.invalid/northlight.png | Advanced disclosure |
| `tv.country` · text | Country / País<br>Preserve source country or edition. / Conserva el país o edición original. | Load current saved/server value; illustrative fixture: ES | Advanced disclosure |
| `tv.language` · text | Language / Idioma<br>Original channel language. / Idioma original del canal. | Load current saved/server value; illustrative fixture: es | Advanced disclosure |
| `tv.website` · text | Website / Web<br>Optional channel website. / Web opcional del canal. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `tv.epg_id` · text | Guide XML ID / ID XML de guía<br>Pair with the actual guide source when identity is ambiguous. / Combina con la fuente real cuando haya ambigüedad. | Load current saved/server value; illustrative fixture: northlight.example | Advanced disclosure |
| `tv.epg_source_id` · select | Guide source / Fuente de guía<br>Do not choose the lowest row ID when sources collide. / No elijas el ID de fila menor si coinciden fuentes. | Load current saved/server value; illustrative fixture: sample-guide | Advanced disclosure; sample-guide → Sample guide / Sample guide; regional-guide → Regional guide / Regional guide |

**Contextual exits:** [Return to channel / Volver al canal](workflow-prototype.html?screen=channel-detail).

<a id="channel-detail"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-detail`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Northlight / Northlight

[Open composition](workflow-prototype.html?screen=channel-detail) · existing route/context: `/tv-channels/:id` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Choose a source, review signal, or manage guide information. / Elige una emisión, revisa la señal o gestiona la guía.

**Evidence:** [TVChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannelDetail.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **art-absent:** No artwork is available. Names and actions are ready. / No hay imagen disponible. Los nombres y acciones siguen listos.
- **art-slow:** Artwork is taking longer. Continue without it. / La imagen tarda. Puedes continuar sin ella.
- **art-blocked:** Artwork could not be loaded from this address. Use the text details. / No se pudo cargar la imagen de esta dirección. Consulta los datos.
- **art-rejected:** This image type is not supported. Use the text details. / El tipo de imagen no es compatible. Consulta los datos.
- **art-oversized:** The image exceeds the safe size limit. It has not been opened. / La imagen supera el límite seguro. No se ha abierto.
- **art-decode-failed:** This image could not be displayed. Try loading it again. / No se pudo mostrar la imagen. Prueba a cargarla de nuevo.
- **art-changed:** The artwork changed. Load the new image when you are ready. / La imagen cambió. Carga la nueva cuando quieras.

**Read-only context: Channel summary / Resumen del canal**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Number / Favorite / Número / Favorito | 1 · Yes / 1 · Sí |
| Guide / Guía | Sample guide : northlight.example / Sample guide : northlight.example |
| Now / Next / Ahora / Después | Coastlines: the Atlantic · Inside the studio / Coastlines: the Atlantic · Inside the studio |

**Available streams / Emisiones disponibles**

- Northlight HD / Northlight HD: Verified signal · 0 peers · sample 7 Nov 16:00 / Señal verificada · 0 pares · muestra 7 nov 16:00 [Open related workflow](workflow-prototype.html?screen=stream-stats).
- Northlight backup / Northlight backup: Not checked · rates unknown / Sin comprobar · velocidades desconocidas [Open related workflow](workflow-prototype.html?screen=stream-stats).

**Contextual exits:** [Watch / guide / record / Ver / guía / grabar](workflow-prototype.html?screen=live); [Preferred stream order / Orden de emisiones preferidas](workflow-prototype.html?screen=channel-preferences); [Add existing streams / Añadir emisiones existentes](workflow-prototype.html?screen=channel-assign); [Open source-qualified guide / Abrir guía con su fuente](workflow-prototype.html?screen=guide-detail); [Edit channel / Editar canal](workflow-prototype.html?screen=channel-edit); [Delete channel / Eliminar canal](workflow-prototype.html?screen=channel-delete).

<a id="channel-reorder"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-reorder`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Reorder all TV channels / Reordenar todos los canales de TV

[Open composition](workflow-prototype.html?screen=channel-reorder) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Move items with arrow buttons or drag handles, then save. / Mueve elementos con flechas o arrastrando y después guarda.

**Evidence:** [TVChannelReorder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelReorder.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** The inventory changed elsewhere. Nothing was saved. Reload the complete list and review your order again. / El inventario cambió en otro lugar. No se guardó nada. Recarga la lista completa y revisa el orden.

**Explanation:** All 3 synthetic items are shown. Filters and pagination do not narrow this edit. / Se muestran los 3 elementos ficticios. Los filtros y la paginación no limitan esta edición.

**Reorder / Reorder:** Save consecutive numbers for all channels together. Cancel keeps the saved numbers. / Guarda números consecutivos para todos los canales juntos. Cancelar conserva los números guardados.

**Contextual exits:** [Cancel and return / Cancelar y volver](workflow-prototype.html?screen=channels).

<a id="channel-preferences"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-preferences`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Preferred streams for Northlight / Emisiones preferidas para Northlight

[Open composition](workflow-prototype.html?screen=channel-preferences) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Move items with arrow buttons or drag handles, then save. / Mueve elementos con flechas o arrastrando y después guarda.

**Evidence:** [TVChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVChannelDetail.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** The inventory changed elsewhere. Nothing was saved. Reload the complete list and review your order again. / El inventario cambió en otro lugar. No se guardó nada. Recarga la lista completa y revisa el orden.

**Explanation:** All 3 synthetic items are shown. Filters and pagination do not narrow this edit. / Se muestran los 3 elementos ficticios. Los filtros y la paginación no limitan esta edición.

**Reorder / Reorder:** Preferences apply only to eligible streams; recent offline, inactive or unsupported streams stay excluded. Recent failures still deprioritize a source. / Las preferencias solo afectan a emisiones aptas; las inactivas, incompatibles o sin señal reciente siguen excluidas. Los fallos recientes reducen la prioridad.

**Contextual exits:** [Cancel and return / Cancelar y volver](workflow-prototype.html?screen=channels).

<a id="streams"></a>

**Simplified location:** TV channels → Streams. **Composition:** section. **Canonical editor:** `streams`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Streams / Emisiones

[Open composition](workflow-prototype.html?screen=streams) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** A stream is one playable source. Several can belong to one TV channel. / Una emisión es una fuente reproducible. Varias pueden pertenecer al mismo canal.

**Evidence:** [AcestreamChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/AcestreamChannels.tsx); [ChannelFilterBar.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/channels/ChannelFilterBar.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Find streams / Buscar emisiones

**Save timing:** explicit action. **Action:** Filter streams / Filtrar emisiones. **Boundary:** `channelService query`. View/preview only; no persistent data mutation.

**Consequence:** Catalogue filter updated. / Filtro del catálogo actualizado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `filter.search` · search | Search / Buscar<br>Filters the complete catalogue before pagination. / Filtra el catálogo completo antes de paginar. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `filter.category` · select | Category / Categoría<br>All categories by default. Original category names are preserved. / Todas por defecto. Se conservan los nombres originales. | Load current saved/server value; illustrative fixture:  |  → All categories / Todas las categorías; Documentary → Documentary / Documentary; News → News / News |
| `filter.status` · select | Status / Estado<br>Active or inactive TV channels. Verified signal is a separate advanced filter. / Canales activos o inactivos. Señal verificada es otro filtro avanzado. | Load current saved/server value; illustrative fixture:  |  → Any status / Cualquier estado; true → Active / Activo; false → Inactive / Inactivo |
| `streams.source` · select | Source / Fuente<br>Exact source identity; applied before count and pagination. / Identidad exacta; se filtra antes de contar y paginar. | Load current saved/server value; illustrative fixture:  |  → All sources / Todas las fuentes; source-demo → Family channels / Family channels |
| `streams.group` · text | Group / Grupo<br>Original group value. / Nombre de grupo original. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `streams.active` · select | Active / Activa<br>Filter enabled and disabled streams. / Filtra emisiones activadas y desactivadas. | Load current saved/server value; illustrative fixture:  | Advanced disclosure;  → Any / Cualquiera; true → Enabled / Activada; false → Disabled / Desactivada |
| `streams.assigned` · select | Linked to TV channel / Vinculada a canal de TV<br>Blank includes both; filtering never changes association. / Vacío incluye ambas; filtrar no cambia asociación. | Load current saved/server value; illustrative fixture:  |  → Any / Cualquiera; true → Linked / Vinculada; false → Not linked / Sin vincular |

**Signal and ownership / Señal y pertenencia**

- Northlight HD / Northlight HD: Verified signal · Family channels → Northlight / Señal verificada · Family channels → Northlight [Open related workflow](workflow-prototype.html?screen=stream-stats).
- Atelier backup / Atelier backup: Lookup found · media not verified · unassigned / ID encontrado · señal sin verificar · sin canal [Open related workflow](workflow-prototype.html?screen=stream-stats).
- World 24 alternate / World 24 alternate: Check error · previous observation retained / Error al comprobar · se conserva la muestra anterior [Open related workflow](workflow-prototype.html?screen=stream-stats).

**Contextual exits:** [Add a stream manually / Añadir una emisión manualmente](workflow-prototype.html?screen=stream-edit); [Bulk actions / Acciones en lote](workflow-prototype.html?screen=stream-bulk); [Review name matches / Revisar coincidencias de nombre](workflow-prototype.html?screen=stream-match); [Offline cleanup settings / Ajustes de limpieza sin señal](workflow-prototype.html?screen=offline-cleanup).

**Contextual exits:** [Activity details / Detalles de actividad](workflow-prototype.html?screen=channel-activity).

<a id="stream-stats"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `stream-stats`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Northlight HD · observations / Northlight HD · observaciones

[Open composition](workflow-prototype.html?screen=stream-stats) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** A successful lookup is not proof that video or audio is arriving. / Encontrar el ID no demuestra que lleguen vídeo o audio.

**Evidence:** [StreamStatistics.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/channels/StreamStatistics.tsx); [ChannelActivityLogDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelActivityLogDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unknown, not-found. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unknown:** There is no measurement yet. Importing a channel does not check whether video or audio is arriving. / Aún no hay medición. Importar un canal no comprueba si llega vídeo o audio.
- **not-found:** The engine explicitly reported ID not found. This differs from timeout or engine error. / El motor indicó expresamente ID no encontrado. Es distinto de agotamiento de tiempo o error del motor.

**Implementation constraint for `unknown`:** No measurement is available. Show unknown, not zero. Importing did not prove signal. / No hay medición. Muestra desconocido, no cero. Importar no demostró señal.

**Read-only context: Last observation · synthetic / Última observación · ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Verified signal / Señal verificada | Yes · identified audio/video packets / Sí · paquetes identificados de audio/vídeo |
| Engine lookup / Búsqueda en motor | ID found / ID encontrado |
| Observed at / Observado el | 7 Nov 2026 · 16:00 UTC / 7 Nov 2026 · 16:00 UTC |
| Peers / Pares | 0 · measured, not missing / 0 · medido, no ausente |
| Download / upload / Descarga / subida | 420 / 0 Kbytes/sec / 420 / 0 Kbytes/sec |
| Encoded media bitrate / Tasa del contenido codificado | Unknown · different from network download rate / Desconocida · distinta de la velocidad de descarga |

**Activity / Actividad**

- 16:00 · checked / 16:00 · comprobada: Media packets verified / Paquetes de contenido verificados
- 15:00 · skipped / 15:00 · omitida: Active playback protected; previous observation retained / Reproducción protegida; se conserva la muestra previa

**Check this stream / Comprobar esta emisión:** A bounded check can wait or be skipped to protect playback. Request one check? / La comprobación limitada puede esperar u omitirse para proteger la reproducción. ¿Solicitarla?

Result copy: Check queued. Waiting is not offline. / Comprobación en cola. Esperar no significa sin señal.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Edit metadata / Editar datos](workflow-prototype.html?screen=stream-edit).

### Authored composition for `unknown`

[Open this state](workflow-prototype.html?screen=stream-stats&state=unknown). This replaces the default content rather than placing a warning over contradictory fixture data.

**Read-only context: Northlight HD · no measurement yet / Northlight HD · sin medición**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Verified signal / Señal verificada | Not checked / Sin comprobar |
| Engine ID lookup / Búsqueda de ID | Unknown / Desconocida |
| Peers / Pares | Unknown · not zero / Desconocido · no es cero |
| Download / upload / Descarga / subida | Unknown · no observation time / Desconocido · sin hora de observación |
| Encoded bitrate / Bitrate codificado | Unknown / Desconocido |

**Explanation:** Skipped checks leave the last known measurement unchanged. If a previous measurement exists, its original time stays visible. / Las comprobaciones omitidas conservan la última medición. Si hay una anterior, se mantiene visible su hora original.

**Contextual exits:** [Review checking engine / Revisar motor de comprobación](workflow-prototype.html?screen=automation); [Back to streams / Volver a emisiones](workflow-prototype.html?screen=streams).

<a id="stream-edit"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `stream-edit`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add and link a stream / Añadir y vincular una emisión

[Open composition](workflow-prototype.html?screen=stream-edit) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Add a stream and optionally link it to an existing TV channel in the same step. / Añade una emisión y, si quieres, vincúlala a un canal de TV en el mismo paso.

**Evidence:** [QuickEditDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/QuickEditDialog.tsx); [TVChannelLinkField.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelLinkField.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, excluded. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** This stream is already linked to another channel. The existing link was preserved; review it before reassignment. / Esta emisión ya está vinculada a otro canal. Se conservó el vínculo; revísalo antes de reasignar.
- **excluded:** An import rule excludes this stream. Only an explicit manual override may bypass it. / Una regla excluye esta emisión. Solo una excepción manual explícita permite omitirla.

### Stream details / Datos de emisión

**Save timing:** explicit action. **Action:** Add stream / Añadir emisión. **Boundary:** `channelService.create`. Submit this resource only; other sections retain independent state.

**Consequence:** Stream and selected channel link saved together. / Emisión y vínculo elegidos guardados juntos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `stream.name` · text | Stream name / Nombre de emisión<br>Required; original source name. / Obligatorio; nombre original de fuente. | Load current saved/server value; illustrative fixture: Northlight HD | required=True |
| `stream.id` · text | AceStream ID / ID de AceStream<br>40 hexadecimal characters. Read-only after creation; never store a search infohash without resolving it. / 40 caracteres hexadecimales. Solo lectura tras crear; resuelve el infohash de búsqueda antes de guardarlo. | Load current saved/server value; illustrative fixture: 0000000000000000000000000000000000000000 | required=True; pattern=[0-9a-fA-F]{40} |
| `stream.tv_channel_id` · select | Link to TV channel / Vincular a canal de TV<br>Optional here; shared searchable number/name/country/category picker. Add and association commit together. / Opcional aquí; selector compartido por número, nombre, país y categoría. Alta y vínculo se guardan juntos. | Load current saved/server value; illustrative fixture:  |  → No channel / Sin canal; 1 → 1 · Northlight · ES · Documentary / 1 · Northlight · ES · Documentary; 2 → 2 · World 24 · GB · News / 2 · World 24 · GB · News |
| `stream.group` · text | Group / Grupo<br>Optional original group. / Grupo original opcional. | Load current saved/server value; illustrative fixture: Documentary | No additional prototype constraint; preserve current source validation. |
| `stream.logo` · text | Logo URL / URL de logotipo<br>Optional; keeps the original URL. / Opcional; conserva la URL original. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `stream.tvg_id` · text | TVG ID / ID TVG<br>Guide ID written into playlists. Keep machine value intact. / ID de guía exportado en listas. Conserva su valor exacto. | Load current saved/server value; illustrative fixture: northlight.example | Advanced disclosure |
| `stream.tvg_name` · text | TVG name / Nombre TVG<br>Original guide name. / Nombre original de guía. | Load current saved/server value; illustrative fixture: Northlight | Advanced disclosure |
| `stream.is_active` · checkbox | Show in playlist / Mostrar en listas<br>Existing editor flag; hidden streams remain stored. / Opción del editor; las emisiones ocultas siguen guardadas. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `stream.epg_update_protected` · checkbox | Keep my guide fields / Conservar mis campos de guía<br>Protect metadata against guide updates. / Protege los datos frente a actualizaciones de guía. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `stream.allow_excluded` · checkbox | Override this import exclusion / Ignorar esta exclusión de importación<br>Explicit manual-add exception only. Never reuse it in automatic imports. / Excepción explícita solo para alta manual. Nunca se reutiliza en importaciones automáticas. | Load current saved/server value; illustrative fixture: False | Advanced disclosure |

**Explanation:** Create-only ID and allow-excluded fields disappear when editing; the existing ID remains read-only. The online observation is not an editable claim of signal. / ID y excepción de exclusión solo al crear; al editar el ID es solo lectura. La observación de señal no es una afirmación editable.

**Contextual exits:** [Add from Search / Añadir desde Buscar](workflow-prototype.html?screen=search-add-link).

<a id="stream-bulk"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `stream-bulk`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Bulk stream actions / Acciones en lote

[Open composition](workflow-prototype.html?screen=stream-bulk) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Only explicitly selected streams are affected. / Solo se afectan las emisiones seleccionadas expresamente.

**Evidence:** [BulkOperations.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BulkOperations.tsx); [BatchAssignDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BatchAssignDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Selection / Selección:** Selection retained across pages; show total selected and hidden-by-filter count. / Se conserva la selección entre páginas; muestra el total y cuántas ocultan los filtros.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

### Apply one change / Aplicar un cambio

**Save timing:** explicit action. **Action:** Apply selected change / Aplicar cambio seleccionado. **Boundary:** `channelService bulk commands`. Submit this resource only; other sections retain independent state.

**Consequence:** Report changed, skipped and failed rows separately; do not claim all succeeded. / Informa por separado de cambios, omisiones y fallos; no afirmes éxito total.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `bulk.action` · select | Action / Acción<br>Unspecified metadata stays unchanged. Do not turn an empty field into a bulk clear implicitly. / Los datos no indicados se conservan. Un campo vacío no borra datos en lote implícitamente. | Load current saved/server value; illustrative fixture: activate | activate → Enable / Activar; deactivate → Disable / Desactivar; group → Change group / Cambiar grupo; assign → Assign TV channel / Asignar canal |
| `bulk.group` · text | New group / Grupo nuevo<br>Only sent for Change group. / Solo se envía al cambiar grupo. | Load current saved/server value; illustrative fixture: Documentary | Advanced disclosure |
| `bulk.tv_channel_id` · select | TV channel / Canal de TV<br>Only sent for Assign. Existing conflicting assignments require review. / Solo se envía al asignar. Los vínculos en conflicto requieren revisión. | Load current saved/server value; illustrative fixture: 1 | Advanced disclosure; 1 → Northlight / Northlight; 2 → World 24 / World 24 |

**Delete selected streams / Eliminar emisiones seleccionadas:** Delete the selected stream records and their TV links? TV channels remain. Recheck selection and current impact. / ¿Eliminar emisiones seleccionadas y sus vínculos? Se conservan canales de TV. Recomprueba selección y efecto.

Result copy: Selected deletion finished; review individual failures before retrying. / Eliminación terminada; revisa los fallos individuales antes de reintentar.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [All editable metadata / Todos los datos editables](workflow-prototype.html?screen=stream-bulk-fields).

<a id="channel-assign"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-assign`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Assign existing streams / Asignar emisiones existentes

[Open composition](workflow-prototype.html?screen=channel-assign) · existing route/context: `/tv-channels/:id` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Search the catalogue and select the exact sources for Northlight. / Busca en el catálogo y selecciona las emisiones exactas para Northlight.

**Evidence:** [BatchAcestreamAssignment.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BatchAcestreamAssignment.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Available streams / Emisiones disponibles:** Show assigned, already linked and conflicting results. Moving a stream clears its previous preference position. / Muestra asignadas, ya vinculadas y conflictos. Mover una emisión borra su posición preferida anterior.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

**Contextual exits:** [Review name suggestions / Revisar sugerencias de nombres](workflow-prototype.html?screen=stream-match); [Back to Northlight / Volver a Northlight](workflow-prototype.html?screen=channel-detail).

<a id="stream-match"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `stream-match`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Match streams to TV channels / Vincular emisiones a canales de TV

[Open composition](workflow-prototype.html?screen=stream-match) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Similar names are optional suggestions for your review. / Los nombres parecidos son sugerencias opcionales para revisar.

**Evidence:** [TVAutoMatchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVAutoMatchDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, ambiguous. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **ambiguous:** Two TV channels have similar names. Review their details and choose one for this stream. / Dos canales de TV tienen nombres parecidos. Revisa sus datos y elige uno para esta emisión.

**Implementation constraint for `ambiguous`:** Northlight has two TV candidates. Select one target for that stream; do not select both or choose by row ID. / Northlight tiene dos candidatos. Elige un destino; no selecciones ambos ni elijas por ID de fila.

**Explanation:** This assigns streams to TV channels. It does not assign programme guides or enable exact-match automation. / Esto asigna emisiones a canales de TV. No asigna guías ni activa vinculación automática.

### Suggestion options / Opciones de sugerencias

**Save timing:** explicit action. **Action:** Refresh preview / Actualizar vista previa. **Boundary:** `TVMatchOptions preview`. View/preview only; no persistent data mutation.

**Consequence:** Preview refreshed without changing assignments. / Vista previa actualizada sin cambiar asignaciones.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `matching.include_similar` · checkbox | Include similar names for review / Incluir nombres parecidos para revisar<br>Off by default; no result starts selected. / Desactivado por defecto; ningún resultado empieza seleccionado. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `matching.assumed_country` · text | Country for unlabeled entries / País para entradas sin país<br>Matching only. Explicit country and edition metadata still wins. / Solo para comparar. Los datos explícitos de país y edición tienen prioridad. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Review proposed assignments / Revisar asignaciones:** One target per stream. Changing target removes its old selection; exact bulk selection respects the current filter. / Un destino por emisión. Cambiarlo quita la selección anterior; seleccionar exactas respeta el filtro.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

**Contextual exits:** [Programme-guide matching is separate / La vinculación de guía es independiente](workflow-prototype.html?screen=guide-match).

<a id="channel-delete"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-delete`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Delete Northlight? / ¿Eliminar Northlight?

[Open composition](workflow-prototype.html?screen=channel-delete) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Review channel deletion separately from deleting its streams. / Revisa la eliminación del canal por separado de sus emisiones.

**Evidence:** [TVChannelDeleteDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelDeleteDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** The TV channel and its associations are removed. Existing stream records are retained by the channel-delete flow; source deletion has different options. / Se elimina el canal de TV y sus asociaciones. Este flujo conserva las emisiones; eliminar una fuente tiene otras opciones.

**Delete TV channel / Eliminar canal de TV:** Delete Northlight and its channel-specific configuration? Recheck dependent schedules and server response before claiming success. / ¿Eliminar Northlight y su configuración? Recomprueba programaciones dependientes y respuesta antes de afirmar éxito.

Result copy: Channel removed. Refresh inventory; retained streams remain manageable. / Canal eliminado. Actualiza el catálogo; se pueden gestionar las emisiones conservadas.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="guide-sources"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** section. **Canonical editor:** `guide-sources`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Programme guides / Guías de programación

[Open composition](workflow-prototype.html?screen=guide-sources) · existing route/context: `/epg?tab=sources` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Add a guide, then review which channel each listing belongs to. / Añade una guía y revisa a qué canal pertenece cada programación.

**Evidence:** [EPGSourcesTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGSourcesTable.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Guide sources / Fuentes de guía**

- Sample guide / Sample guide: Enabled · updated 16:00 · 3 guide channels / Activada · actualizada 16:00 · 3 canales [Open related workflow](workflow-prototype.html?screen=guide-source).
- Regional guide / Regional guide: Disabled · imported identities still exist / Desactivada · las identidades importadas siguen existiendo [Open related workflow](workflow-prototype.html?screen=guide-source).

**Contextual exits:** [Add guide source / Añadir fuente de guía](workflow-prototype.html?screen=guide-source); [Review channel matches / Revisar coincidencias](workflow-prototype.html?screen=guide-match); [Browse guide channels / Consultar canales de guía](workflow-prototype.html?screen=guide-detail); [Coverage / Cobertura](workflow-prototype.html?screen=guide-coverage); [Export XMLTV / Exportar XMLTV](workflow-prototype.html?screen=guide-export); [Rules / Reglas](workflow-prototype.html?screen=guide-rule).

**Contextual exits:** [Guide inventory and day / Inventario y día](workflow-prototype.html?screen=guide-inventory).

**Contextual exits:** [Automatic exact matches / Coincidencias exactas automáticas](workflow-prototype.html?screen=guide-auto).

<a id="guide-source"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-source`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Edit guide source / Editar fuente de guía

[Open composition](workflow-prototype.html?screen=guide-source) · existing route/context: `/epg?tab=sources` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** The same editor is used in setup and guide management. / El mismo editor se usa en la configuración inicial y gestión de guías.

**Evidence:** [EPGSourceDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGSourceDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Source details / Datos de fuente

**Save timing:** explicit action. **Action:** Save guide source / Guardar fuente de guía. **Boundary:** `epgService.createSource / updateSource`. Submit this resource only; other sections retain independent state.

**Consequence:** Source saved. Refresh and reviewed matching are separate actions. / Fuente guardada. Actualizar y revisar coincidencias son acciones separadas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `epg.name` · text | Guide name / Nombre de guía<br>Required; a recognisable source name. / Obligatorio; un nombre reconocible. | Load current saved/server value; illustrative fixture: Sample guide | required=True |
| `epg.url` · url | Guide URL / URL de guía<br>XMLTV or a supported regional guide. Guarded fetches preserve the entire previous guide on failure. / XMLTV o una guía regional admitida. Un fallo conserva la guía anterior completa. | Load current saved/server value; illustrative fixture: https://guide.example.invalid/listings.xml | required=True |
| `epg.enabled` · checkbox | Refresh this source / Actualizar esta fuente<br>Disabled sources still participate in imported-ID identity checks. / Las fuentes desactivadas siguen contando para comprobar IDs importados. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

**Refresh guide / Actualizar guía:** Request a bounded refresh? It may wait behind other maintenance. / ¿Solicitar una actualización limitada? Puede esperar a otras tareas.

Result copy: Guide refresh waiting. Old listings remain until a successful import. / Actualización en espera. Se conservan los programas anteriores hasta importar correctamente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Remove guide source / Eliminar fuente de guía:** Remove this guide source and its imported listings? Review affected guide links; TV channels and streams are separate. / ¿Eliminar esta fuente y sus programas importados? Revisa los vínculos afectados; canales y emisiones son independientes.

Result copy: Guide source removed; review channels without listings. / Fuente eliminada; revisa los canales sin programación.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Next: review guide matches / Siguiente: revisar coincidencias](workflow-prototype.html?screen=guide-match).

<a id="guide-detail"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-detail`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Northlight · Sample guide / Northlight · Sample guide

[Open composition](workflow-prototype.html?screen=guide-detail) · existing route/context: `/epg/channels/:id` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Source-qualified programme details and matching rules. / Programación y reglas identificadas por su fuente.

**Evidence:** [EPGChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPGChannelDetail.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Guide identity / Identidad de guía**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Source / Fuente | Sample guide / Sample guide |
| XML ID / XML ID | northlight.example / northlight.example |
| TV channel / Canal de TV | Northlight / Northlight |

**Schedule · Europe/Madrid / Programación · Europe/Madrid**

- 20:00 · Coastlines: the Atlantic / 20:00 · Coastlines: the Atlantic: 45 min · original programme title / 45 min · título original [Open related workflow](workflow-prototype.html?screen=recording-schedule).
- 20:45 · Inside the studio / 20:45 · Inside the studio: 30 min · guide data, not verified media / 30 min · datos de guía, no señal verificada [Open related workflow](workflow-prototype.html?screen=recording-schedule).

**Contextual exits:** [Add a matching rule / Añadir regla de coincidencia](workflow-prototype.html?screen=guide-rule); [Link a TV channel / Vincular canal de TV](workflow-prototype.html?screen=guide-choice); [Create TV channel from guide / Crear canal de TV desde guía](workflow-prototype.html?screen=channel-edit).

<a id="guide-choice"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-choice`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Choose the correct guide source / Elegir la fuente de guía correcta

[Open composition](workflow-prototype.html?screen=guide-choice) · existing route/context: `/epg?tab=matching` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** The same name can identify different channels or editions. / El mismo nombre puede identificar canales o ediciones diferentes.

**Evidence:** [EPGMatchAnalysisPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGMatchAnalysisPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Atelier · ambiguous match / Atelier · coincidencia ambigua:** Preserve the selected source plus XML ID. No numeric-row tie-break is allowed. / Conserva fuente e ID XML seleccionados. No se desempata por ID numérico.

No automatic selection. Exactly one choice. Show row-specific result; expire selection on review-token/revision changes.

**Contextual exits:** [Inspect schedule before choosing / Revisar programación antes de elegir](workflow-prototype.html?screen=guide-detail).

<a id="guide-match"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-match`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Review guide matches / Revisar coincidencias de guía

[Open composition](workflow-prototype.html?screen=guide-match) · existing route/context: `/epg?tab=matching` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Preview the full source scope; explicitly select what to apply. / Revisa todas las fuentes del ámbito y selecciona qué aplicar.

**Evidence:** [EPGMatchAnalysisPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGMatchAnalysisPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** The source scope or preview changed. Selection is cleared; fetch and review a fresh preview. No stale row is applied. / Cambió el ámbito o la vista previa. Se borra la selección; obtén y revisa otra. No se aplica una fila obsoleta.

### Preview scope / Ámbito de vista previa

**Save timing:** explicit action. **Action:** Preview matches / Ver coincidencias. **Boundary:** `guideSetupService preview`. View/preview only; no persistent data mutation.

**Consequence:** The guide may have changed. Apply only after the latest preview has been reviewed. / La guía puede haber cambiado. Aplica solo tras revisar la vista más reciente.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `guide.source_id` · select | Guide source / Fuente de guía<br>Changing scope invalidates the old preview. / Cambiar el ámbito invalida la vista previa. | Load current saved/server value; illustrative fixture:  |  → All sources / Todas las fuentes; sample → Sample guide / Sample guide |
| `guide.strictness` · select | Matching level / Nivel de coincidencia<br>Reviewed matching only; automatic matching remains conservative and exact. / Solo para revisión; la automatización sigue siendo conservadora y exacta. | Load current saved/server value; illustrative fixture: strict | strict → Strict / Estricto; balanced → Balanced / Equilibrado; loose → Relaxed review / Revisión flexible |

**Matches / Coincidencias:** The guide may have changed. Apply only after the latest preview has been reviewed. / La guía puede haber cambiado. Aplica solo tras revisar la vista más reciente.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

**Contextual exits:** [Review ambiguous Atelier / Revisar Atelier ambiguo](workflow-prototype.html?screen=guide-choice); [Automatic exact matching / Vinculación exacta automática](workflow-prototype.html?screen=guide-auto).

**Contextual exits:** [Start watching / Empezar a ver](workflow-prototype.html?screen=dashboard).

<a id="guide-rule"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-rule`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Guide matching rule / Regla de coincidencia de guía

[Open composition](workflow-prototype.html?screen=guide-rule) · existing route/context: `/epg/channels/:id` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Rules belong to a specific guide channel. / Las reglas pertenecen a un canal de guía concreto.

**Evidence:** [EPGChannelDetail.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPGChannelDetail.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Target / Destino**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Source / channel / Fuente / canal | Sample guide : northlight.example / Sample guide : northlight.example |

### Include or exclude a name / Incluir o excluir un nombre

**Save timing:** explicit action. **Action:** Add rule / Añadir regla. **Boundary:** `epgService stringMappings`. Submit this resource only; other sections retain independent state.

**Consequence:** The next guide refresh uses the rule. / La siguiente actualización de guía usa la regla.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `rule.search_pattern` · text | Pattern / Patrón<br>Uses the existing matching pattern semantics; do not silently turn literal input into a regex. / Usa la semántica actual; no conviertas texto literal en regex sin indicarlo. | Load current saved/server value; illustrative fixture: Northlight | required=True |
| `rule.is_exclusion` · checkbox | Exclude this match / Excluir esta coincidencia<br>Off includes names that match; on prevents a false match. / Desactivado incluye coincidencias; activado evita una coincidencia falsa. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Delete rule / Eliminar regla:** Matching stops using this pattern from the next guide refresh. / Se deja de usar este patrón desde la siguiente actualización.

Result copy: Rule removed. Existing assignments are not a fresh review result. / Regla eliminada. Las asignaciones existentes no son una revisión nueva.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="guide-auto"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-auto`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Automatic exact matching / Vinculación exacta automática

[Open composition](workflow-prototype.html?screen=guide-auto) · existing route/context: `/settings?tab=automation` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Opt in only after you understand what successful imports can change. / Activa solo después de entender qué puede cambiar tras importar.

**Evidence:** [GuideMatchingFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/GuideMatchingFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### After successful updates / Tras actualizaciones correctas

**Save timing:** immediate. **Action:** Save matching preference / Guardar preferencia. **Boundary:** `configService epg-matching`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved for future successful updates. Ambiguous names still need your review. / Guardado para futuras actualizaciones correctas. Los nombres ambiguos requieren revisión.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `epg_matching.enabled` · checkbox | Enable automatic exact matching / Activar vinculación exacta automática<br>Off by default. Can create TV channels and assign unassigned streams after successful source or guide updates. Ambiguous names still need review. / Desactivado por defecto. Puede crear canales y asignar emisiones sin canal tras actualizar fuentes o guías. Lo ambiguo sigue necesitando revisión. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Read-only context: Last result / Último resultado**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Outcome / Resultado | Created 1 · assigned 2 · needs review 1 / Creado 1 · asignadas 2 · requiere revisión 1 |
| Finished / Finalizado | 7 Nov 16:00 · synthetic / 7 nov 16:00 · ficticio |

<a id="guide-export"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-export`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Export programme guide / Exportar guía de programación

[Open composition](workflow-prototype.html?screen=guide-export) · existing route/context: `/epg?tab=export` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Use the same channel identities as your playlist. / Usa las mismas identidades de canal que tu lista.

**Evidence:** [EPGXmlOutputPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGXmlOutputPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Export options / Opciones de exportación

**Save timing:** explicit action. **Action:** Generate XMLTV / Generar XMLTV. **Boundary:** `epgService.generateXml`. View/preview only; no persistent data mutation.

**Consequence:** A guide file is prepared for the selected channels and dates. Its channel names match the playlist. / Se prepara una guía para los canales y fechas elegidos. Los nombres coinciden con la lista.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `xml.search_term` · search | Search channels / Buscar canales<br>Only include matching channels. / Incluye solo canales coincidentes. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `xml.favorites_only` · checkbox | Favorites only / Solo favoritos<br>Uses TV-channel favorites. / Usa favoritos de canales de TV. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `xml.days_back` · range | Start of export range (days from today) / Inicio del intervalo (días desde hoy)<br>Start up to 14 days before today. Default: yesterday (−1). / Empieza hasta 14 días antes de hoy. Por defecto: ayer (−1). | Load current saved/server value; illustrative fixture: -1 | min=-14; max=0; Adapter/contract note: Start 0–14 days before today; display default −1. The API stores days_back=1, so convert this offset to its absolute count. / Inicio de 0 a 14 días antes de hoy; defecto visible −1. API guarda days_back=1; convierte el desfase a recuento absoluto. |
| `xml.days_forward` · range | End of export range (days from today) / Fin del intervalo (días desde hoy)<br>Default: 7 days ahead. Choose from 14 days before to 14 days after today; the end cannot precede the start. / Por defecto: 7 días después. Elige entre 14 días antes y 14 después de hoy; el fin no puede preceder al inicio. | Load current saved/server value; illustrative fixture: 7 | min=-14; max=14 |

**Synthetic read-only output:**

```text
<tv>
  <channel id="sample-guide:northlight.example">
    <display-name>Northlight</display-name>
  </channel>
</tv>
```

**Contextual exits:** [Check coverage / Consultar cobertura](workflow-prototype.html?screen=guide-coverage); [Matching playlist / Lista correspondiente](workflow-prototype.html?screen=playlist).

<a id="guide-coverage"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-coverage`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Guide coverage / Cobertura de guía

[Open composition](workflow-prototype.html?screen=guide-coverage) · existing route/context: `/epg` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Missing listings are separate from missing signal. / La falta de programas es distinta de la falta de señal.

**Evidence:** [GuideCoverage.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/GuideCoverage.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **partial:** One guide source failed to refresh. These counts describe the last available data, not complete current coverage. / Una fuente falló. Las cifras describen los últimos datos disponibles, no la cobertura actual completa.

**Read-only context: Synthetic coverage / Cobertura ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| TV channels / Canales de TV | 3 / 3 |
| With source-qualified guide / Con guía identificada por fuente | 2 / 2 |
| Listings today / Programación hoy | 1 · one source could not refresh / 1 · una fuente no se pudo actualizar |
| Streams linked / Emisiones vinculadas | 4 of 6 / 4 de 6 |

**Needs attention / Requiere atención**

- Atelier / Atelier: Choose between two guide identities / Elige entre dos identidades de guía [Open related workflow](workflow-prototype.html?screen=guide-choice).
- World 24 / World 24: Guide linked; no programmes in the selected window / Guía vinculada; sin programas en este intervalo [Open related workflow](workflow-prototype.html?screen=guide-source).

<a id="playlist"></a>

**Simplified location:** Where would you like to watch? → Your playlist. **Composition:** section. **Canonical editor:** `playlist`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Your playlist / Tu lista de reproducción

[Open composition](workflow-prototype.html?screen=playlist) · existing route/context: `/playlist` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Choose what to include, then copy the player link or download M3U. / Elige qué incluir y copia el enlace o descarga M3U.

**Evidence:** [PlaylistOptionsForm.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/playlist/PlaylistOptionsForm.tsx); [PlaylistLinkPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/playlist/PlaylistLinkPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, credential, managed, filtered. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **credential:** This export needs a playback credential. Never paste an administrative header credential into a player URL. / Esta exportación necesita una credencial de reproducción. Nunca pegues una credencial administrativa en la URL.
- **managed:** Account policy requires relay links. The saved custom format remains stored for contexts that permit it. / La política exige enlaces de la app. Se conserva el formato propio para los contextos permitidos.
- **filtered:** No channels match these options. Change the filters to include channels in the playlist. / Ningún canal coincide con estas opciones. Cambia los filtros para incluir canales en la lista.

**Implementation constraint for `filtered`:** These options produce no entries. Change filters; do not present an empty playlist as a failed server. / Estas opciones no producen entradas. Cambia filtros; una lista vacía no es un fallo del servidor.

**Synthetic read-only output:**

```text
https://tv.example.invalid/app/playlists/m3u?format=tv-relay
```

**Copy action:** Copy example playlist link / Copiar enlace de ejemplo. Placeholder `https://tv.example.invalid/app/playlists/m3u?format=tv-relay`; show success or a selectable fallback without logging the value.

### Playlist options / Opciones de lista

**Save timing:** explicit action. **Action:** Prepare M3U / Preparar M3U. **Boundary:** `usePlaylistLink / playlistService`. View/preview only; no persistent data mutation.

**Consequence:** Export uses the chosen options and the same guide IDs as XMLTV. No source was deleted. / Usa las opciones y los mismos IDs de guía que XMLTV. No se elimina ninguna fuente.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `playlist.search` · search | Search channels / Buscar canales<br>Filters exported names; does not change the catalogue. / Filtra nombres exportados; no cambia el catálogo. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `playlist.only_online` · checkbox | Only online channels / Solo canales con señal<br>Latest verified observation is not a guarantee of present availability. / La última observación verificada no garantiza disponibilidad actual. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `playlist.favorites_only` · checkbox | Favorite TV channels only / Solo canales favoritos<br>Unassigned streams cannot be favorites. / Las emisiones sin canal no pueden ser favoritas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `playlist.include_unassigned` · checkbox | Include unassigned streams at the end / Incluir emisiones sin canal al final<br>Disabled for favorites-only. Individual relay links have no TV-channel failover. / No disponible con solo favoritos. Los enlaces individuales no tienen alternativas de canal. | Load current saved/server value; illustrative fixture: False | disabled when playlist.favorites_only is on |
| `playlist.format` · select | Stream link format / Formato de enlace<br>Accounts force app relay links to protect source credentials. Default uses the saved format, otherwise acestream://. / Las cuentas fuerzan enlaces de la app para proteger credenciales. Por defecto usa el formato guardado o acestream://. | Load current saved/server value; illustrative fixture: tv-relay | default → Default / Predeterminado; tv-relay → TV channel relay / Canal de TV con alternativas; demo → Demo format / Formato de ejemplo |
| `playlist.per_source` · checkbox | List each source under its channel / Listar cada emisión bajo su canal<br>Only for TV relay formats; each source opens alone without failover. / Solo para formatos de canal; cada emisión se abre sola sin alternativas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `playlist.include_groups` · text | Include groups / Incluir grupos<br>Repeated query parameters preserve original values, including commas inside known group names. / Los parámetros repetidos conservan valores originales y comas en nombres conocidos. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `playlist.exclude_groups` · text | Exclude groups / Excluir grupos<br>Exclusions remain when editing a stream format. / Se conservan exclusiones al editar un formato. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |

**Contextual exits:** [Manage shared stream formats / Gestionar formatos compartidos](workflow-prototype.html?screen=formats); [Address used by players / Dirección para reproductores](workflow-prototype.html?screen=public-address); [Playback credentials / Credenciales de reproducción](workflow-prototype.html?screen=access-credentials); [Download matching guide / Descargar guía correspondiente](workflow-prototype.html?screen=guide-export).

**Contextual exits:** [Address and credentials / Dirección y credenciales](workflow-prototype.html?screen=public-address); [Shared stream formats / Formatos de emisión compartidos](workflow-prototype.html?screen=formats).

<a id="formats"></a>

**Simplified location:** Where would you like to watch? → Your playlist. **Composition:** contextual editor or detail. **Canonical editor:** `formats`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Stream link formats / Formatos de enlaces de emisión

[Open composition](workflow-prototype.html?screen=formats) · existing route/context: `/settings?tab=links` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Shared editor used by Playlist and Settings → Stream links. / Editor compartido de Listas y Ajustes → Enlaces.

**Evidence:** [StreamLinkFormatsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StreamLinkFormatsSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Saved formats / Formatos guardados**

- Built-in / Integrado: acestream:// · fallback / acestream:// · alternativa [Open related workflow](workflow-prototype.html?screen=format-edit).
- Demo relay / Demo relay: {tv_channel_id} · stable TV identity / {tv_channel_id} · identidad estable [Open related workflow](workflow-prototype.html?screen=format-edit).

### Add named format / Añadir formato

**Save timing:** explicit action. **Action:** Save format / Guardar formato. **Boundary:** `baseUrlService.createBaseUrl`. Submit this resource only; other sections retain independent state.

**Consequence:** Named format saved; playlist filters and selection stay in place. / Formato guardado; se mantienen los filtros y selección de lista.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `format.name` · text | Format name / Nombre del formato<br>Required for named formats; built-in format has no name editor. / Obligatorio en formatos propios; el integrado no permite editar el nombre. | Load current saved/server value; illustrative fixture: Demo relay | required=True |
| `format.pattern` · text | Link pattern / Patrón del enlace<br>Use {tv_channel_id} for a stable TV relay, {channel_id} for a stream, and optional {pid}. A plain prefix is also supported. / Usa {tv_channel_id} para un canal estable, {channel_id} para una emisión y {pid} opcional. También admite un prefijo simple. | Load current saved/server value; illustrative fixture: https://tv.example.invalid/app/tuner/tv/{tv_channel_id}.ts | required=True |
| `format.is_default` · checkbox | Use as default / Usar por defecto<br>Use this format by default. It replaces the previous default selection. / Usa este formato por defecto. Sustituye la selección anterior. | Load current saved/server value; illustrative fixture: False | Adapter/contract note: Setting a new default clears the old default in the same API operation. / Elegir otro predeterminado desmarca el anterior en la misma operación. |

### Append PID / Añadir PID

**Save timing:** explicit action. **Action:** Save this setting / Guardar este ajuste. **Boundary:** `configService independent setting: links.add_pid`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success. / Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `links.add_pid` · checkbox | Append PID / Añadir PID<br>Existing identifier option; keep unique direct-player PIDs and ownership rules. / Opción existente; conserva PID únicos y reglas de propiedad. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

### Use AppID / Usar AppID

**Save timing:** explicit action. **Action:** Save this setting / Guardar este ajuste. **Boundary:** `configService independent setting: links.app_id`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success. / Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `links.app_id` · checkbox | Use AppID / Usar AppID<br>Existing link compatibility option. Not a background-job setting. / Opción de compatibilidad de enlaces. No es un ajuste de tareas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Return to playlist with filters / Volver a la lista con filtros](workflow-prototype.html?screen=playlist).

<a id="format-edit"></a>

**Simplified location:** Where would you like to watch? → Your playlist. **Composition:** contextual editor or detail. **Canonical editor:** `format-edit`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Edit Demo relay / Editar Demo relay

[Open composition](workflow-prototype.html?screen=format-edit) · existing route/context: `/settings?tab=links` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Preview the exact pattern without translating placeholders. / Revisa el patrón exacto sin traducir marcadores.

**Evidence:** [StreamLinkFormatsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StreamLinkFormatsSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Pattern / Patrón

**Save timing:** explicit action. **Action:** Save pattern / Guardar patrón. **Boundary:** `baseUrlService.updateBaseUrl`. Submit this resource only; other sections retain independent state.

**Consequence:** Format updated for future generated links. Already copied links are not rewritten. / Formato actualizado para enlaces futuros. Los ya copiados no se reescriben.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `format.name` · text | Format name / Nombre del formato<br>Required for named formats; built-in format has no name editor. / Obligatorio en formatos propios; el integrado no permite editar el nombre. | Load current saved/server value; illustrative fixture: Demo relay | required=True |
| `format.pattern` · text | Link pattern / Patrón del enlace<br>Use {tv_channel_id} for a stable TV relay, {channel_id} for a stream, and optional {pid}. A plain prefix is also supported. / Usa {tv_channel_id} para un canal estable, {channel_id} para una emisión y {pid} opcional. También admite un prefijo simple. | Load current saved/server value; illustrative fixture: https://tv.example.invalid/app/tuner/tv/{tv_channel_id}.ts | required=True |

**Delete named format / Eliminar formato:** Delete Demo relay? Review players using this named format and show the effective fallback after removal. / ¿Eliminar Demo relay? Revisa reproductores que lo usan y muestra la alternativa efectiva después.

Result copy: Named format removed. Refresh format selection and show the resulting effective link. / Formato eliminado. Actualiza selección y muestra el enlace efectivo.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Explanation:** The built-in format is edited through its own pattern control and cannot be treated as a deletable named entry. / El patrón integrado se edita en su control y no se trata como una entrada propia eliminable.

<a id="source-web"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-web`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Web or playlist source / Fuente web o lista

[Open composition](workflow-prototype.html?screen=source-web) · existing route/context: `/scraper?tab=sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the source, then explicitly request its first import. / Guarda la fuente y solicita expresamente la primera importación.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, import-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **import-failed:** Source saved, but import failed. Existing channels remain. Retry update; do not add the source again. / Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.

**Explanation:** Paste a website or playlist address. Save it for later, or find its channels now. / Pega una dirección web o de lista. Guárdala para más tarde o busca sus canales ahora.

### Source configuration / Configuración de fuente

**Save timing:** explicit action. **Action:** Save source only / Solo guardar fuente. **Boundary:** `scraperService createURL / updateURL`. Submit this resource only; other sections retain independent state.

**Consequence:** Save only keeps the source. Save and find channels saves it, then queues an import separately. / Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.name` · text | Source name (optional) / Nombre de fuente (opcional)<br>Up to 255 characters. This original name appears in source filters. / Hasta 255 caracteres. Aparece en los filtros con su nombre original. | Load current saved/server value; illustrative fixture: Family channels | maxlength=255 |
| `source.url` · text | Source address / Dirección de fuente<br>Paste the complete address. Save only keeps it for later; finding channels starts an import. / Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True; Adapter/contract note: Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches. / Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas. |
| `source.url_type` · select | Source type / Tipo de fuente<br>Use the normal website option unless your provider asks for a specific type. / Usa la opción web normal salvo que tu proveedor indique otro tipo. | Load current saved/server value; illustrative fixture: regular | Adapter/contract note: HTTP/HTTPS pages and nested playlists keep redirect, DNS and private-network safeguards. / Las páginas HTTP/HTTPS y listas anidadas conservan las protecciones de redirección, DNS y red privada.; auto → Auto-detect / Detección automática; regular → Regular HTTP / HTTP común; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS; broadcaster → Built-in broadcaster / Proveedor integrado |
| `source.enabled` · checkbox | Update this source / Actualizar esta fuente<br>Enabled by default. Disabled retains saved channels. / Activada por defecto. Desactivar conserva los canales. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `source.scrape_bare_ids` · checkbox | Recognize bare content IDs / Reconocer IDs sin enlace<br>Off by default for ordinary sources. Broadcaster adapters disable this option. / Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción. | Repository default: False | Advanced disclosure |

**Save and find channels / Guardar y buscar canales:** Save this source, then queue one import? These are separate operations. / ¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.

Result copy: Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source. / Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Custom extraction recipe / Receta de extracción](workflow-prototype.html?screen=helper-installed); [Remove source / Eliminar fuente](workflow-prototype.html?screen=source-remove); [Review orphaned streams / Revisar emisiones huérfanas](workflow-prototype.html?screen=sources-orphans).

<a id="source-auto"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-auto`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Automatic source detection / Detección automática de fuente

[Open composition](workflow-prototype.html?screen=source-auto) · existing route/context: `/scraper?tab=sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the source, then explicitly request its first import. / Guarda la fuente y solicita expresamente la primera importación.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, import-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **import-failed:** Source saved, but import failed. Existing channels remain. Retry update; do not add the source again. / Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.

**Explanation:** The current form starts with Auto-detect. A custom recipe is optional and never proves signal. / El formulario actual empieza con detección automática. La receta es opcional y no demuestra señal.

### Source configuration / Configuración de fuente

**Save timing:** explicit action. **Action:** Save source only / Solo guardar fuente. **Boundary:** `scraperService createURL / updateURL`. Submit this resource only; other sections retain independent state.

**Consequence:** Save only keeps the source. Save and find channels saves it, then queues an import separately. / Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.name` · text | Source name (optional) / Nombre de fuente (opcional)<br>Up to 255 characters. This original name appears in source filters. / Hasta 255 caracteres. Aparece en los filtros con su nombre original. | Load current saved/server value; illustrative fixture: Family channels | maxlength=255 |
| `source.url` · text | Source address / Dirección de fuente<br>Paste the complete address. Save only keeps it for later; finding channels starts an import. / Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True; Adapter/contract note: Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches. / Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas. |
| `source.url_type` · select | Source type / Tipo de fuente<br>Use the normal website option unless your provider asks for a specific type. / Usa la opción web normal salvo que tu proveedor indique otro tipo. | Load current saved/server value; illustrative fixture: auto | Adapter/contract note: The current form starts with Auto-detect. A custom recipe is optional and never proves signal. / El formulario actual empieza con detección automática. La receta es opcional y no demuestra señal.; auto → Auto-detect / Detección automática; regular → Regular HTTP / HTTP común; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS; broadcaster → Built-in broadcaster / Proveedor integrado |
| `source.enabled` · checkbox | Update this source / Actualizar esta fuente<br>Enabled by default. Disabled retains saved channels. / Activada por defecto. Desactivar conserva los canales. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `source.scrape_bare_ids` · checkbox | Recognize bare content IDs / Reconocer IDs sin enlace<br>Off by default for ordinary sources. Broadcaster adapters disable this option. / Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción. | Repository default: False | Advanced disclosure |

**Save and find channels / Guardar y buscar canales:** Save this source, then queue one import? These are separate operations. / ¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.

Result copy: Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source. / Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Custom extraction recipe / Receta de extracción](workflow-prototype.html?screen=helper-installed); [Remove source / Eliminar fuente](workflow-prototype.html?screen=source-remove); [Review orphaned streams / Revisar emisiones huérfanas](workflow-prototype.html?screen=sources-orphans).

<a id="source-zeronet"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-zeronet`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## ZeroNet source / Fuente ZeroNet

[Open composition](workflow-prototype.html?screen=source-zeronet) · existing route/context: `/scraper?tab=sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the source, then explicitly request its first import. / Guarda la fuente y solicita expresamente la primera importación.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, import-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **import-failed:** Source saved, but import failed. Existing channels remain. Retry update; do not add the source again. / Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.

**Explanation:** Uses the configured ZeroNet gateway. Unavailable gateway is a prerequisite error, not an empty catalogue. / Usa la pasarela ZeroNet configurada. Si falta, es un requisito pendiente, no un catálogo vacío.

### Source configuration / Configuración de fuente

**Save timing:** explicit action. **Action:** Save source only / Solo guardar fuente. **Boundary:** `scraperService createURL / updateURL`. Submit this resource only; other sections retain independent state.

**Consequence:** Save only keeps the source. Save and find channels saves it, then queues an import separately. / Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.name` · text | Source name (optional) / Nombre de fuente (opcional)<br>Up to 255 characters. This original name appears in source filters. / Hasta 255 caracteres. Aparece en los filtros con su nombre original. | Load current saved/server value; illustrative fixture: Family channels | maxlength=255 |
| `source.url` · text | Source address / Dirección de fuente<br>Paste the complete address. Save only keeps it for later; finding channels starts an import. / Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True; Adapter/contract note: Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches. / Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas. |
| `source.url_type` · select | Source type / Tipo de fuente<br>Use the normal website option unless your provider asks for a specific type. / Usa la opción web normal salvo que tu proveedor indique otro tipo. | Load current saved/server value; illustrative fixture: zeronet | Adapter/contract note: Uses the configured ZeroNet gateway. Unavailable gateway is a prerequisite error, not an empty catalogue. / Usa la pasarela ZeroNet configurada. Si falta, es un requisito pendiente, no un catálogo vacío.; auto → Auto-detect / Detección automática; regular → Regular HTTP / HTTP común; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS; broadcaster → Built-in broadcaster / Proveedor integrado |
| `source.enabled` · checkbox | Update this source / Actualizar esta fuente<br>Enabled by default. Disabled retains saved channels. / Activada por defecto. Desactivar conserva los canales. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `source.scrape_bare_ids` · checkbox | Recognize bare content IDs / Reconocer IDs sin enlace<br>Off by default for ordinary sources. Broadcaster adapters disable this option. / Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción. | Repository default: False | Advanced disclosure |

**Save and find channels / Guardar y buscar canales:** Save this source, then queue one import? These are separate operations. / ¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.

Result copy: Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source. / Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Custom extraction recipe / Receta de extracción](workflow-prototype.html?screen=helper-installed); [Remove source / Eliminar fuente](workflow-prototype.html?screen=source-remove); [Review orphaned streams / Revisar emisiones huérfanas](workflow-prototype.html?screen=sources-orphans).

<a id="source-ipfs"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-ipfs`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## IPFS source / Fuente IPFS

[Open composition](workflow-prototype.html?screen=source-ipfs) · existing route/context: `/scraper?tab=sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the source, then explicitly request its first import. / Guarda la fuente y solicita expresamente la primera importación.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, import-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **import-failed:** Source saved, but import failed. Existing channels remain. Retry update; do not add the source again. / Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.

**Explanation:** Uses the configured IPFS gateway. Preserve content identity; show bounded-fetch failures without deleting saved channels. / Usa la pasarela IPFS. Conserva la identidad; muestra fallos limitados sin borrar canales.

### Source configuration / Configuración de fuente

**Save timing:** explicit action. **Action:** Save source only / Solo guardar fuente. **Boundary:** `scraperService createURL / updateURL`. Submit this resource only; other sections retain independent state.

**Consequence:** Save only keeps the source. Save and find channels saves it, then queues an import separately. / Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.name` · text | Source name (optional) / Nombre de fuente (opcional)<br>Up to 255 characters. This original name appears in source filters. / Hasta 255 caracteres. Aparece en los filtros con su nombre original. | Load current saved/server value; illustrative fixture: Family channels | maxlength=255 |
| `source.url` · text | Source address / Dirección de fuente<br>Paste the complete address. Save only keeps it for later; finding channels starts an import. / Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True; Adapter/contract note: Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches. / Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas. |
| `source.url_type` · select | Source type / Tipo de fuente<br>Use the normal website option unless your provider asks for a specific type. / Usa la opción web normal salvo que tu proveedor indique otro tipo. | Load current saved/server value; illustrative fixture: ipfs | Adapter/contract note: Uses the configured IPFS gateway. Preserve content identity; show bounded-fetch failures without deleting saved channels. / Usa la pasarela IPFS. Conserva la identidad; muestra fallos limitados sin borrar canales.; auto → Auto-detect / Detección automática; regular → Regular HTTP / HTTP común; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS; broadcaster → Built-in broadcaster / Proveedor integrado |
| `source.enabled` · checkbox | Update this source / Actualizar esta fuente<br>Enabled by default. Disabled retains saved channels. / Activada por defecto. Desactivar conserva los canales. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `source.scrape_bare_ids` · checkbox | Recognize bare content IDs / Reconocer IDs sin enlace<br>Off by default for ordinary sources. Broadcaster adapters disable this option. / Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción. | Repository default: False | Advanced disclosure |

**Save and find channels / Guardar y buscar canales:** Save this source, then queue one import? These are separate operations. / ¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.

Result copy: Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source. / Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Custom extraction recipe / Receta de extracción](workflow-prototype.html?screen=helper-installed); [Remove source / Eliminar fuente](workflow-prototype.html?screen=source-remove); [Review orphaned streams / Revisar emisiones huérfanas](workflow-prototype.html?screen=sources-orphans).

<a id="source-provider"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-provider`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Built-in broadcaster / Proveedor integrado

[Open composition](workflow-prototype.html?screen=source-provider) · existing route/context: `/scraper?tab=sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the source, then explicitly request its first import. / Guarda la fuente y solicita expresamente la primera importación.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, import-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **import-failed:** Source saved, but import failed. Existing channels remain. Retry update; do not add the source again. / Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.

**Explanation:** Registry-backed adapters provide their own fixed address. Saving still does not import channels. / Los adaptadores del registro proporcionan su dirección fija. Guardar no importa canales.

### Source configuration / Configuración de fuente

**Save timing:** explicit action. **Action:** Save source only / Solo guardar fuente. **Boundary:** `scraperService createURL / updateURL`. Submit this resource only; other sections retain independent state.

**Consequence:** Save only keeps the source. Save and find channels saves it, then queues an import separately. / Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.provider` · select | Built-in provider / Proveedor integrado<br>Choose from the installed registry; unavailable registry has Retry. Existing custom names are preserved. / Elige del registro instalado; si falla, reintenta. Se conservan nombres propios. | Load current saved/server value; illustrative fixture: demo | demo → Synthetic adapter · not a real provider / Adaptador ficticio · no es real |
| `source.name` · text | Source name (optional) / Nombre de fuente (opcional)<br>Up to 255 characters. This original name appears in source filters. / Hasta 255 caracteres. Aparece en los filtros con su nombre original. | Load current saved/server value; illustrative fixture: Family channels | maxlength=255 |
| `source.url_type` · select | Source type / Tipo de fuente<br>Use the normal website option unless your provider asks for a specific type. / Usa la opción web normal salvo que tu proveedor indique otro tipo. | Load current saved/server value; illustrative fixture: broadcaster | Adapter/contract note: Registry-backed adapters provide their own fixed address. Saving still does not import channels. / Los adaptadores del registro proporcionan su dirección fija. Guardar no importa canales.; auto → Auto-detect / Detección automática; regular → Regular HTTP / HTTP común; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS; broadcaster → Built-in broadcaster / Proveedor integrado |
| `source.url` · text | Source address / Dirección de fuente<br>Paste the complete address. Save only keeps it for later; finding channels starts an import. / Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True; readonly=True; Adapter/contract note: Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches. / Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas. |
| `source.enabled` · checkbox | Update this source / Actualizar esta fuente<br>Enabled by default. Disabled retains saved channels. / Activada por defecto. Desactivar conserva los canales. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `source.scrape_bare_ids` · checkbox | Recognize bare content IDs / Reconocer IDs sin enlace<br>Off by default for ordinary sources. Broadcaster adapters disable this option. / Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción. | Repository default: False | disabled=True; Advanced disclosure |

**Save and find channels / Guardar y buscar canales:** Save this source, then queue one import? These are separate operations. / ¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.

Result copy: Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source. / Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Custom extraction recipe / Receta de extracción](workflow-prototype.html?screen=helper-installed); [Remove source / Eliminar fuente](workflow-prototype.html?screen=source-remove); [Review orphaned streams / Revisar emisiones huérfanas](workflow-prototype.html?screen=sources-orphans).

<a id="source-results"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-results`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Import result / Resultado de importación

[Open composition](workflow-prototype.html?screen=source-results) · existing route/context: `/scraper` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Saved, queued, imported and verified are different facts. / Guardado, en cola, importado y verificado son hechos distintos.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, waiting, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **waiting:** Waiting for the current guide refresh. A second request does not create a duplicate job. / Esperando a la actualización de guía. Otra solicitud no duplica la tarea.
- **partial:** Some records could not be imported. Existing channels remain available; review the results below. / Algunos registros no se pudieron importar. Los canales existentes siguen disponibles; revisa los resultados.

**Implementation constraint for `partial`:** Some records failed. Keep existing channels and show imported, excluded, invalid and failed counts separately. / Fallaron algunos registros. Conserva canales y separa cantidades importadas, excluidas, inválidas y fallidas.

**Read-only context: Family channels · synthetic / Family channels · ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Source / Fuente | Saved / Guardada |
| Queue / Cola | Finished / Terminada |
| Imported / Importadas | 8 new · 2 unchanged · 1 excluded / 8 nuevas · 2 sin cambios · 1 excluida |
| Signal / Señal | Not checked / Sin comprobar |

**Contextual exits:** [Review imported streams / Revisar emisiones](workflow-prototype.html?screen=streams); [Assign TV channels / Asignar canales](workflow-prototype.html?screen=channel-assign); [Schedule updates / Programar actualizaciones](workflow-prototype.html?screen=automation).

**Contextual exits:** [Next: add a programme guide / Siguiente: añadir una guía](workflow-prototype.html?screen=setup-guide); [Review imported channels / Revisar canales importados](workflow-prototype.html?screen=channels).

<a id="source-remove"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `source-remove`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Remove Family channels? / ¿Eliminar Family channels?

[Open composition](workflow-prototype.html?screen=source-remove) · existing route/context: `/scraper` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** The source’s streams can be removed or retained explicitly. / Puedes eliminar o conservar expresamente sus emisiones.

**Evidence:** [DeleteSourceDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/scraper/DeleteSourceDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Review impact / Revisar efecto

**Save timing:** explicit action. **Action:** Remove source / Eliminar fuente. **Boundary:** `DELETE scrapers/urls/{id}?delete_streams=`. Submit this resource only; other sections retain independent state.

**Consequence:** Source removed. If streams were retained, orphan cleanup remains a separate reviewed action. / Fuente eliminada. Si se conservaron emisiones, su limpieza requiere revisión aparte.

**Confirmation:** Remove Family channels with the selected stream-deletion choice? Existing TV channels remain. / ¿Eliminar Family channels según la opción elegida para emisiones? Se conservan canales de TV.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `source.delete_streams` · checkbox | Also delete this source’s streams / Eliminar también sus emisiones<br>Current default is on. Example: 8 source-owned streams, 3 linked to TV channels. TV channels remain. / El valor actual por defecto está activado. Ejemplo: 8 emisiones, 3 vinculadas a canales. Se conservan canales de TV. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

<a id="sources-orphans"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `sources-orphans`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Streams without a saved source / Emisiones sin fuente guardada

[Open composition](workflow-prototype.html?screen=sources-orphans) · existing route/context: `/scraper` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Choose only the former sources you want to clean up. / Elige solo las antiguas fuentes que quieras limpiar.

**Evidence:** [OrphanedSourcesDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/scraper/OrphanedSourcesDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Orphaned source groups / Grupos de fuentes huérfanas:** Server rejects sources that are configured again. Manual, W3U, Telegram and saved-search ownership is excluded. / El servidor rechaza fuentes que vuelven a estar configuradas. Se excluyen pertenencias manuales, W3U, Telegram y búsquedas.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

**Explanation:** Nothing is selected initially. Previewing groups deletes nothing. / Nada está seleccionado inicialmente. Consultar los grupos no elimina nada.

<a id="w3u"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `w3u`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Review W3U catalogue / Revisar catálogo W3U

[Open composition](workflow-prototype.html?screen=w3u) · existing route/context: `/scraper?tab=w3u` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Folders organize the publisher’s catalogue; they are not TV-channel assignments. / Las carpetas organizan el catálogo del editor; no son asignaciones a canales.

**Evidence:** [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, expired. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **expired:** Preview expired or catalogue revision changed. Load a new preview; old selection is not authorization. / Vista previa caducada o revisión cambiada. Carga otra; la selección anterior no autoriza importar.

### Load a catalogue preview / Consultar catálogo

**Save timing:** explicit action. **Action:** Preview catalogue / Ver catálogo. **Boundary:** `catalogueService preview`. View/preview only; no persistent data mutation.

**Consequence:** Preview only. If this review expires, load a fresh preview before importing. / Solo vista previa. Si caduca la revisión, carga otra antes de importar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `catalogue.url` · url | Catalogue URL / URL de catálogo<br>Bounded structured documents only. Publisher scripts are never executed. / Solo documentos estructurados limitados. Nunca se ejecutan scripts del editor. | Load current saved/server value; illustrative fixture: https://catalogue.example.invalid/sample.w3u | required=True |

**Sample catalogue / Live / Documentary / Sample catalogue / Live / Documentary:** Preview only. If this review expires, load a fresh preview before importing. / Solo vista previa. Si caduca la revisión, carga otra antes de importar.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

**Other entries / Otras entradas**

- Film archive / Film archive: VOD · not imported as a channel / VOD · no se importa como canal [Open related workflow](workflow-prototype.html?screen=w3u-detail).
- Northlight Cup / Northlight Cup: Event · review through Events / Evento · revisar desde Eventos [Open related workflow](workflow-prototype.html?screen=event-import).
- Website / Website: Unsupported resolver · source host only / Resolución incompatible · solo host de origen [Open related workflow](workflow-prototype.html?screen=w3u-detail).

**Contextual exits:** [Import settings / Ajustes de importación](workflow-prototype.html?screen=w3u-save); [Assign folder streams / Asignar emisiones de carpeta](workflow-prototype.html?screen=w3u-folder).

<a id="w3u-save"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `w3u-save`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Save reviewed catalogue / Guardar catálogo revisado

[Open composition](workflow-prototype.html?screen=w3u-save) · existing route/context: `/scraper?tab=w3u` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Import only selected compatible live entries. / Importa solo las entradas de directo compatibles seleccionadas.

**Evidence:** [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Catalogue and import / Catálogo e importación

**Save timing:** explicit action. **Action:** Save catalogue / Guardar catálogo. **Boundary:** `catalogueService save`. Submit this resource only; other sections retain independent state.

**Consequence:** Catalogue saved with selected branches. Review per-entry outcome. / Catálogo guardado con las ramas elegidas. Revisa el resultado por entrada.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `catalogue.name` · text | Catalogue name / Nombre de catálogo<br>1–255 characters. / 1–255 caracteres. | Load current saved/server value; illustrative fixture: Sample catalogue | required=True; maxlength=255 |
| `catalogue.mode` · select | Import streams / Importar emisiones<br>Preserve current compatibility modes and reviewed branch selection. / Conserva modos de compatibilidad y selección revisada. | Load current saved/server value; illustrative fixture: compatible | compatible → Compatible entries / Entradas compatibles; acestream → AceStream only / Solo AceStream |
| `catalogue.confirm_live` · checkbox | Import reviewed entries as permanent live channels / Importar entradas revisadas como emisiones permanentes<br>Off saves the catalogue only. On imports only the reviewed compatible live entries; confirmation is required for import. / Desactivado guarda solo el catálogo. Activado importa solo entradas de directo compatibles revisadas; importar exige confirmación. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `catalogue.refresh_enabled` · checkbox | Refresh with scheduled scraping / Actualizar con las tareas de fuentes<br>Opt-in. Only reviewed identities refresh automatically; missing entries and deselection do not prune saved channels. / Opcional. Solo se actualizan identidades revisadas; las ausencias o deselecciones no borran canales. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Explanation:** Save only is valid. Import and refresh permissions are separate: enabling refresh must not admit new unreviewed identities. / Guardar sin importar es válido. Importar y actualizar tienen permisos separados: activar actualización no admite identidades sin revisar.

**Remove catalogue / Eliminar catálogo:** Remove refresh configuration? Imported channels remain, including partially refreshed entries. / ¿Eliminar la configuración de actualización? Se conservan canales, incluidos los actualizados parcialmente.

Result copy: Catalogue removed; imported streams retained. / Catálogo eliminado; emisiones conservadas.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="w3u-detail"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `w3u-detail`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Catalogue entry details / Detalles de entrada

[Open composition](workflow-prototype.html?screen=w3u-detail) · existing route/context: `/scraper?tab=w3u` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Keep supported media separate from a publisher website or VOD. / Distingue contenido compatible de web del editor o VOD.

**Evidence:** [Catalogues.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Catalogues.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Film archive / Film archive**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Type / Tipo | VOD · excluded from live-channel import / VOD · excluido de importación de directo |
| Origin host / Host de origen | catalogue.example.invalid / catalogue.example.invalid |
| Header names / Nombres de cabecera | User-Agent · Referer · no values shown / User-Agent · Referer · sin valores |
| State / Estado | Retained original metadata / Datos originales conservados |

### Browse options / Opciones de consulta

**Save timing:** explicit action. **Action:** Apply view options / Aplicar opciones. **Boundary:** `local catalogue view`. View/preview only; no persistent data mutation.

**Consequence:** View updated; no import or playback started. / Vista actualizada; no se importó ni reprodujo.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `catalogue.search` · search | Search catalogue / Buscar en catálogo<br>Local reviewed inventory. / Inventario local revisado. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `catalogue.content_type` · select | Content type / Tipo de contenido<br>Live, event, VOD or unknown. / Directo, evento, VOD o desconocido. | Load current saved/server value; illustrative fixture: all | all → All / Todos; live → Live / Directo; event → Event / Evento; vod → VOD / VOD; unknown → Unknown / Desconocido |
| `catalogue.show` · select | Show / Mostrar<br>Review supported, unsupported and imported states. / Revisa estados compatibles, incompatibles e importados. | Load current saved/server value; illustrative fixture: all | all → All entries / Todas las entradas; favorites → Favorites / Favoritas; recent → Recently opened / Abiertas recientemente |
| `catalogue.artwork` · checkbox | Load publisher artwork / Cargar imágenes del editor<br>Explicit opt-in; failing artwork leaves original names visible. / Activación explícita; si falla la imagen el nombre sigue visible. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

<a id="w3u-folder"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `w3u-folder`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Assign a catalogue folder / Asignar una carpeta del catálogo

[Open composition](workflow-prototype.html?screen=w3u-folder) · existing route/context: `/scraper?tab=w3u` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** This explicit action is separate from importing streams. / Esta acción expresa es independiente de importar emisiones.

**Evidence:** [FolderMatchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/catalogues/FolderMatchDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Sample catalogue / Live / Northlight / Sample catalogue / Live / Northlight

**Save timing:** explicit action. **Action:** Assign reviewed folder / Asignar carpeta revisada. **Boundary:** `catalogueService folder assignment`. Submit this resource only; other sections retain independent state.

**Consequence:** Commit atomically; changed or vanished rows require another review. Unimported streams are skipped. / Guardado atómico; filas cambiadas o ausentes requieren revisar. Se omiten emisiones sin importar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `folder.tv_channel_id` · select | Existing TV channel / Canal de TV existente<br>Choose an existing channel or a new name, not both. / Elige un canal o un nombre nuevo, no ambos. | Load current saved/server value; illustrative fixture: 1 |  → Create a channel instead / Crear un canal; 1 → Northlight / Northlight |
| `folder.create_name` · text | New channel name / Nombre de canal nuevo<br>Used only when creating a new TV channel. / Solo se usa al crear un canal nuevo. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `folder.reassign` · checkbox | Move already assigned streams / Mover emisiones ya asignadas<br>Off preserves existing assignments. Deepest folders are processed first in reviewed batch matching. / Desactivado conserva vínculos. En lote se procesan primero las carpetas más profundas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Review destination channel / Revisar canal de destino](workflow-prototype.html?screen=channel-assign).

<a id="saved-search"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `saved-search`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Saved search / Búsqueda guardada

[Open composition](workflow-prototype.html?screen=saved-search) · existing route/context: `/scraper?tab=searches` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Save the definition without starting an import. / Guarda la definición sin iniciar una importación.

**Evidence:** [SavedSearchDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/SavedSearchDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Search definition / Definición de búsqueda

**Save timing:** explicit action. **Action:** Save search / Guardar búsqueda. **Boundary:** `savedSearchService save`. Submit this resource only; other sections retain independent state.

**Consequence:** Definition saved only. Existing memberships and channels are retained. / Solo se guardó la definición. Se conservan pertenencias y canales.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `saved_search.name` · text | Name / Nombre<br>1–100 characters. / 1–100 caracteres. | Load current saved/server value; illustrative fixture: Northlight discovery | required=True; maxlength=100 |
| `saved_search.query` · text | Query / Consulta<br>1–256 characters. Editing query or category pauses refresh. / 1–256 caracteres. Editar consulta o categoría pausa las actualizaciones. | Load current saved/server value; illustrative fixture: Northlight | required=True; maxlength=256 |
| `saved_search.category` · text | Category / Categoría<br>Optional original search category, up to 100 characters. / Categoría original opcional, hasta 100 caracteres. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `saved_search.refresh_enabled` · checkbox | Refresh automatically / Actualizar automáticamente<br>New searches start paused. Preview then explicitly enable after reviewing. / Las nuevas empiezan pausadas. Consulta resultados y activa expresamente después. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Preview and run / Consultar y ejecutar](workflow-prototype.html?screen=saved-search-preview); [Review import exclusions / Revisar exclusiones](workflow-prototype.html?screen=exclusion).

<a id="saved-search-preview"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `saved-search-preview`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Preview a saved search / Consultar búsqueda guardada

[Open composition](workflow-prototype.html?screen=saved-search-preview) · existing route/context: `/scraper?tab=searches` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Resolve results and inspect exclusions before queueing an additive import. / Resuelve resultados y revisa exclusiones antes de poner una importación aditiva en cola.

**Evidence:** [SavedSearches.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/SavedSearches.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Northlight discovery / Northlight discovery**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Preview / Vista previa | 2 importable · 1 excluded · 1 unresolved / 2 importables · 1 excluida · 1 sin resolver |
| Preview expiry / Caducidad | 5 minutes · bound to definition revision / 5 minutos · ligada a la revisión |

**Run this search / Ejecutar esta búsqueda:** Import eligible results additively? The definition, exclusion policy and run ownership are checked again. / ¿Importar resultados aptos de forma aditiva? Se revalidan definición, exclusiones y propiedad de ejecución.

Result copy: Waiting in maintenance queue. A second request cannot duplicate this run. / Esperando en la cola. Otra solicitud no duplica esta ejecución.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Recent runs / Ejecuciones recientes**

- 7 Nov 16:00 · partial / 7 nov 16:00 · parcial: 2 added · 1 excluded · 1 unresolved / 2 añadidas · 1 excluida · 1 sin resolver
- 6 Nov 16:00 · interrupted / 6 nov 16:00 · interrumpida: Restart interrupted the old run; existing channels retained / El reinicio interrumpió la ejecución; canales conservados

<a id="exclusion"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `exclusion`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Import exclusion rule / Regla de exclusión de importación

[Open composition](workflow-prototype.html?screen=exclusion) · existing route/context: `/scraper?tab=exclusions` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Affects future permanent imports, not existing channels or playback. / Afecta a futuras importaciones permanentes, no a canales existentes ni reproducción.

**Evidence:** [ImportExclusions.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/imports/ImportExclusions.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Rule / Regla

**Save timing:** explicit action. **Action:** Save exclusion / Guardar exclusión. **Boundary:** `importExclusionService save`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved. Future imports use this rule; existing channels stay unchanged. / Guardado. Las futuras importaciones usan esta regla; los canales existentes se conservan.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `exclusion.kind` · select | Match by / Comparar por<br>Use the current supported literal rule type; no arbitrary regex execution. / Usa el tipo literal admitido; no se ejecuta regex arbitrario. | Load current saved/server value; illustrative fixture: name_contains | name_contains → Name contains / Nombre contiene; name_equals → Exact name / Nombre exacto; stream_id_equals → Exact content ID / ID de contenido exacto |
| `exclusion.value` · text | Value / Valor<br>1–256 characters. Original matching value is not translated. / 1–256 caracteres. No se traduce el valor de comparación. | Load current saved/server value; illustrative fixture: Demo unwanted | required=True; maxlength=256 |
| `exclusion.enabled` · checkbox | Rule enabled / Regla activada<br>On by default. / Activada por defecto. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `exclusion.note` · textarea | Note (optional) / Nota (opcional)<br>Up to 500 characters for the operator. / Hasta 500 caracteres para el operador. | Load current saved/server value; illustrative fixture:  | maxlength=500 |

**Preview impact / Ver efecto:** Preview a bounded sample without deleting existing channels? / ¿Consultar una muestra limitada sin eliminar canales?

Result copy: 3 of 200 sampled candidates match. Partial sample is not a catalogue-wide count. / Coinciden 3 de 200 candidatos de muestra. No es el total del catálogo.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Delete rule / Eliminar regla:** Future imports can admit these candidates again. Existing channels are not rewritten. / Las futuras importaciones pueden admitir candidatos. No se reescriben canales existentes.

Result copy: Rule deleted. / Regla eliminada.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="search"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `search`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Find new streams / Buscar emisiones nuevas

[Open composition](workflow-prototype.html?screen=search) · existing route/context: `/search` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Search the provider catalogue, not only your saved streams. / Busca en el catálogo del proveedor, no solo en tus emisiones guardadas.

**Evidence:** [Search.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Search.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, engine. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **engine:** The playback engine could not resolve the selected catalogue ID. Nothing was saved or played; retry resolution when it is available. / El motor no pudo resolver el ID seleccionado. No se guardó ni reprodujo nada; reintenta cuando esté disponible.

### Discovery search / Búsqueda de nuevas emisiones

**Save timing:** explicit action. **Action:** Search catalogue / Buscar en catálogo. **Boundary:** `searchService.search`. View/preview only; no persistent data mutation.

**Consequence:** Results are catalogue infohashes. Resolve Add or Play before using a content ID. / Los resultados son infohashes. Resuelve Añadir o Reproducir antes de usar un ID.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `search.query` · text | Search / Buscar<br>Original programme or channel name. Search results are not imported automatically. / Nombre original del programa o canal. Los resultados no se importan solos. | Load current saved/server value; illustrative fixture: Northlight | required=True |
| `search.category` · text | Category / Categoría<br>Optional provider category. / Categoría opcional del proveedor. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Synthetic results / Resultados ficticios**

- Northlight HD / Northlight HD: Not saved · broadcast check not requested / Sin guardar · sin comprobación solicitada [Open related workflow](workflow-prototype.html?screen=search-add-link).
- Northlight alternate / Northlight alternate: Excluded by rule · import requires review / Excluida por regla · requiere revisión [Open related workflow](workflow-prototype.html?screen=search-add-link).

**Contextual exits:** [Save this search / Guardar búsqueda](workflow-prototype.html?screen=saved-search); [Add a known content ID / Añadir un ID conocido](workflow-prototype.html?screen=stream-edit).

<a id="search-add-link"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `search-add-link`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add and link Northlight HD / Añadir y vincular Northlight HD

[Open composition](workflow-prototype.html?screen=search-add-link) · existing route/context: `/search` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Resolve the result, then import and assign it together. / Resuelve el resultado; después importa y asigna juntos.

**Evidence:** [AddAndLinkDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/search/AddAndLinkDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, unresolved, excluded, catalogue-unavailable. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unresolved:** The playable stream could not be identified. Try resolving it again before adding it. / No se pudo identificar la emisión reproducible. Reintenta resolverla antes de añadirla.
- **excluded:** Import exclusion applies. Do not bypass it through Search; review the rule or explicit manual-add workflow. / Se aplica una exclusión. Buscar no la omite; revisa la regla o el alta manual expresa.
- **catalogue-unavailable:** The TV-channel list could not load. Your selected result is retained. Retry before adding and linking it. / No se pudo cargar la lista de TV. Se conserva el resultado elegido. Reintenta antes de añadirlo y vincularlo.
- **conflict:** Stream already belongs to another TV channel. Its assignment remains unchanged. / La emisión ya pertenece a otro canal. Se conserva su asignación.

**Implementation constraint for `unresolved`:** Resolution failed. Do not use the catalogue infohash as a content ID. / Falló la resolución. No uses el infohash del catálogo como ID.

**Implementation constraint for `catalogue-unavailable`:** TV catalogue unavailable. Keep the chosen search result and offer Retry; no partial stream import. / Catálogo de TV no disponible. Conserva el resultado y ofrece Reintentar; no importes parcialmente.

**Explanation:** Catalogue infohash → resolved content ID → one atomic Add and Link. Resolution alone creates no channel or playback session. / Infohash → ID resuelto → alta y vínculo atómicos. Resolver no crea canales ni inicia reproducción.

### Select a TV channel / Seleccionar canal de TV

**Save timing:** explicit action. **Action:** Add and link / Añadir y vincular. **Boundary:** `searchService.resolve + import tv_channel_id`. Submit this resource only; other sections retain independent state.

**Consequence:** Stream imported and linked in one transaction, or neither change applied. / Emisión importada y vinculada en una transacción, o no se aplica ninguno de los cambios.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `add_link.tv_channel_id` · select | TV channel / Canal de TV<br>Required. Shared picker searches number, name, country and category. Preserve existing conflicting assignment. / Obligatorio. Selector compartido por número, nombre, país y categoría. Conserva asignaciones en conflicto. | Load current saved/server value; illustrative fixture:  | required=True;  → Choose a TV channel / Elige un canal; 1 → 1 · Northlight · ES · Documentary / 1 · Northlight · ES · Documentary; 2 → 2 · World 24 · GB · News / 2 · World 24 · GB · News |

**Contextual exits:** [Create a TV channel first / Crear primero un canal](workflow-prototype.html?screen=channel-edit).

<a id="helper-installed"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-installed`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Test a source recipe / Probar una receta de fuente

[Open composition](workflow-prototype.html?screen=helper-installed) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Fetch a bounded sample or paste one; testing changes no source or channel. / Obtén una muestra limitada o pégala; probar no cambia fuentes ni canales.

**Evidence:** [ExtractionBuilder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/ExtractionBuilder.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Sample from installation / Muestra desde la instalación

**Save timing:** explicit action. **Action:** Fetch sample / Obtener muestra. **Boundary:** `recipeService.fetch`. View/preview only; no persistent data mutation.

**Consequence:** Sample fetched for preview only. Saved source and channels are untouched. / Muestra obtenida solo para revisar. Fuente y canales no cambian.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `fetch.url` · url | Source URL / URL de fuente<br>Guarded fetch from the installation. DNS pinning and redirects remain protected. / Consulta protegida desde la instalación. Conserva DNS fijado y redirecciones seguras. | Load current saved/server value; illustrative fixture: https://source.example.invalid/channels | required=True |
| `fetch.url_type` · select | Source type / Tipo de fuente<br>Auto, regular HTTP, ZeroNet or IPFS; same guarded source pipeline. / Automático, HTTP, ZeroNet o IPFS; mismo flujo protegido. | Load current saved/server value; illustrative fixture: auto | auto → Auto / Automático; regular → HTTP / HTTP; zeronet → ZeroNet / ZeroNet; ipfs → IPFS / IPFS |

**Contextual exits:** [HTML / visual picker / HTML / selector visual](workflow-prototype.html?screen=helper-html); [JSON paths / Rutas JSON](workflow-prototype.html?screen=helper-json); [Text / regular expressions / Texto / expresiones regulares](workflow-prototype.html?screen=helper-regex); [Raw and manual fields / Texto y campos manuales](workflow-prototype.html?screen=helper-manual); [Test and save to source / Probar y guardar en fuente](workflow-prototype.html?screen=helper-results).

<a id="helper-standalone"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-standalone`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Build a recipe offline / Crear una receta sin conexión

[Open composition](workflow-prototype.html?screen=helper-standalone) · existing route/context: `standalone helper` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** This helper never connects to your installation. / Este asistente nunca se conecta a tu instalación.

**Evidence:** [standalone.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/standalone.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Paste a synthetic sample or choose a local file. No server address, credentials, fetch-from-installation or Save source action belongs here. / Pega una muestra ficticia o elige un archivo local. Aquí no hay dirección de servidor, credenciales, consulta a instalación ni Guardar fuente.

### Sample input / Muestra de entrada

**Save timing:** explicit action. **Action:** Use sample / Usar muestra. **Boundary:** `standalone recipe worker`. View/preview only; no persistent data mutation.

**Consequence:** Sample loaded locally. Choose fields; no channel data was written. / Muestra cargada localmente. Elige campos; no se escribió ningún canal.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `sample.file` · file | Local sample file / Archivo local de muestra<br>Read locally; never upload from this standalone helper. Sample limit 32 MiB. / Se lee localmente; nunca se sube desde el asistente independiente. Límite 32 MiB. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `sample.text` · textarea | HTML, text or JSON sample / Muestra HTML, texto o JSON<br>Input limit and smaller rendering budget are different. Keep names and IDs in each record paired. / El límite de entrada y el presupuesto de visualización son distintos. Conserva nombre e ID emparejados por registro. | Load current saved/server value; illustrative fixture: [{"name":"Northlight HD","id":"0000000000000000000000000000000000000000","group":"Documentary"}] | No additional prototype constraint; preserve current source validation. |
| `recipe.catalogue` · select | Starter recipe / Receta inicial<br>Versioned fixture-tested catalogue. Choosing a new mode resets fields only after a draft warning. / Catálogo versionado y probado. Cambiar modo reinicia campos solo tras avisar del borrador. | Load current saved/server value; illustrative fixture:  |  → Start empty / Empezar vacía; demo → Synthetic paired JSON / JSON emparejado ficticio |
| `recipe.pasted` · textarea | Recipe JSON (optional) / JSON de receta (opcional)<br>Import up to 512 KiB, validate schema/version, then test. / Importa hasta 512 KiB, valida esquema y versión, y prueba. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |

**Contextual exits:** [Choose JSON fields / Elegir campos JSON](workflow-prototype.html?screen=helper-json); [Choose HTML fields / Elegir campos HTML](workflow-prototype.html?screen=helper-html); [Choose regex fields / Elegir campos regex](workflow-prototype.html?screen=helper-regex); [Large sample path / Muestras grandes](workflow-prototype.html?screen=helper-large).

<a id="helper-html"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-html`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Pick fields in HTML / Elegir campos en HTML

[Open composition](workflow-prototype.html?screen=helper-html) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** A selector finds each repeating row; field selectors are relative to that row. / Un selector encuentra cada fila; los campos se buscan dentro de ella.

**Evidence:** [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **timeout:** The bounded test stopped before completing. Simplify the record rule or use a smaller sample. Existing channels are unchanged. / La prueba se detuvo antes de terminar. Simplifica la regla o reduce la muestra. Los canales no cambian.
- **invalid:** This extraction rule is not supported. Your draft is retained. Correct the highlighted field before testing again. / Esta regla no es compatible. Se conserva el borrador. Corrige el campo marcado antes de probar de nuevo.

**Implementation constraint for `invalid`:** This rule is not supported. Keep the draft and show the field-level reason without running unbounded regex. / Esta regla no se admite. Conserva el borrador y muestra el motivo sin ejecutar regex sin límites.

**Synthetic sample:**

```text
[{"name":"Northlight HD","id":"0000000000000000000000000000000000000000","group":"Documentary"}]
```

### Paired record fields / Campos emparejados

**Save timing:** explicit action. **Action:** Test recipe / Probar receta. **Boundary:** `recipeService.preview / standalone worker`. View/preview only; no persistent data mutation.

**Consequence:** Read-only bounded test. Changing sample or recipe invalidates the previous test; do not enable Save from stale results. / Prueba limitada sin cambios. Cambiar muestra o receta invalida la prueba anterior; no permitas guardar resultados antiguos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recipe.name` · text | Recipe name / Nombre de receta<br>1–100 characters. / 1–100 caracteres. | Load current saved/server value; illustrative fixture: Sample paired records | required=True; maxlength=100 |
| `recipe.version` · text | Recipe version / Versión de receta<br>Semantic version such as 1.0.0; schema_version remains 1. / Versión como 1.0.0; schema_version permanece en 1. | Load current saved/server value; illustrative fixture: 1.0.0 | required=True; pattern=\d+\.\d+\.\d+ |
| `recipe.mode` · select | Source format / Formato de fuente<br>Changing format clears incompatible rules only after confirmation. / Cambiar formato borra reglas incompatibles solo tras confirmar. | Load current saved/server value; illustrative fixture: html | html → HTML elements / Elementos HTML; json → JSON response / Respuesta JSON; regex → Text / regex / Texto / regex |
| `recipe.records` · text | Repeating record / Registro repetido<br>A selector finds each repeating row; field selectors are relative to that row. / Un selector encuentra cada fila; los campos se buscan dentro de ella. | Load current saved/server value; illustrative fixture: .channel | maxlength=1024 |
| `recipe.fields.name.selector` · text | Name selector / Selector de nombre<br>Relative to each row; blank selects the row itself. Maximum 256 characters. / Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres. | Load current saved/server value; illustrative fixture: a | maxlength=256 |
| `recipe.fields.name.attribute` · text | Name attribute / Atributo de nombre<br>Blank reads text; href reads a link. Maximum 80 characters. / Vacío lee texto; href lee enlace. Máximo 80 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=80 |
| `recipe.fields.name.pattern` · text | Name regex / Regex de nombre<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024 |
| `recipe.fields.id.selector` · text | Content ID selector / Selector de id de contenido<br>Relative to each row; blank selects the row itself. Maximum 256 characters. / Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres. | Load current saved/server value; illustrative fixture: a | maxlength=256 |
| `recipe.fields.id.attribute` · text | Content ID attribute / Atributo de id de contenido<br>Blank reads text; href reads a link. Maximum 80 characters. / Vacío lee texto; href lee enlace. Máximo 80 caracteres. | Load current saved/server value; illustrative fixture: href | maxlength=80 |
| `recipe.fields.id.pattern` · text | Content ID regex / Regex de id de contenido<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024 |
| `recipe.fields.group.selector` · text | Group selector / Selector de grupo<br>Relative to each row; blank selects the row itself. Maximum 256 characters. / Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=256; Advanced disclosure |
| `recipe.fields.group.attribute` · text | Group attribute / Atributo de grupo<br>Blank reads text; href reads a link. Maximum 80 characters. / Vacío lee texto; href lee enlace. Máximo 80 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=80; Advanced disclosure |
| `recipe.fields.group.pattern` · text | Group regex / Regex de grupo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.fields.logo.selector` · text | Logo selector / Selector de logotipo<br>Relative to each row; blank selects the row itself. Maximum 256 characters. / Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=256; Advanced disclosure |
| `recipe.fields.logo.attribute` · text | Logo attribute / Atributo de logotipo<br>Blank reads text; href reads a link. Maximum 80 characters. / Vacío lee texto; href lee enlace. Máximo 80 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=80; Advanced disclosure |
| `recipe.fields.logo.pattern` · text | Logo regex / Regex de logotipo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.fields.epg_id.selector` · text | Guide ID selector / Selector de id de guía<br>Relative to each row; blank selects the row itself. Maximum 256 characters. / Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=256; Advanced disclosure |
| `recipe.fields.epg_id.attribute` · text | Guide ID attribute / Atributo de id de guía<br>Blank reads text; href reads a link. Maximum 80 characters. / Vacío lee texto; href lee enlace. Máximo 80 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=80; Advanced disclosure |
| `recipe.fields.epg_id.pattern` · text | Guide ID regex / Regex de id de guía<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.flags` · text | Regex flags / Opciones regex<br>i ignores case; m line anchors; s includes newlines. No named groups or backreferences. / i ignora mayúsculas; m ancla líneas; s incluye saltos. Sin grupos con nombre ni referencias inversas. | Load current saved/server value; illustrative fixture: is | pattern=[ims]{0,3} |

**Contextual exits:** [Manual selection / Selección manual](workflow-prototype.html?screen=helper-manual); [Independent helper / Asistente independiente](workflow-prototype.html?screen=helper-standalone).

<a id="helper-json"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-json`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Read fields from JSON / Leer campos de JSON

[Open composition](workflow-prototype.html?screen=helper-json) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Records array path, or blank for a root array. Field paths are relative to each object. / Ruta del array, o vacío para array raíz. Los campos son relativos a cada objeto.

**Evidence:** [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **timeout:** The bounded test stopped before completing. Simplify the record rule or use a smaller sample. Existing channels are unchanged. / La prueba se detuvo antes de terminar. Simplifica la regla o reduce la muestra. Los canales no cambian.
- **invalid:** This extraction rule is not supported. Your draft is retained. Correct the highlighted field before testing again. / Esta regla no es compatible. Se conserva el borrador. Corrige el campo marcado antes de probar de nuevo.

**Implementation constraint for `invalid`:** This rule is not supported. Keep the draft and show the field-level reason without running unbounded regex. / Esta regla no se admite. Conserva el borrador y muestra el motivo sin ejecutar regex sin límites.

**Synthetic sample:**

```text
[{"name":"Northlight HD","id":"0000000000000000000000000000000000000000","group":"Documentary"}]
```

### Paired record fields / Campos emparejados

**Save timing:** explicit action. **Action:** Test recipe / Probar receta. **Boundary:** `recipeService.preview / standalone worker`. View/preview only; no persistent data mutation.

**Consequence:** Read-only bounded test. Changing sample or recipe invalidates the previous test; do not enable Save from stale results. / Prueba limitada sin cambios. Cambiar muestra o receta invalida la prueba anterior; no permitas guardar resultados antiguos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recipe.name` · text | Recipe name / Nombre de receta<br>1–100 characters. / 1–100 caracteres. | Load current saved/server value; illustrative fixture: Sample paired records | required=True; maxlength=100 |
| `recipe.version` · text | Recipe version / Versión de receta<br>Semantic version such as 1.0.0; schema_version remains 1. / Versión como 1.0.0; schema_version permanece en 1. | Load current saved/server value; illustrative fixture: 1.0.0 | required=True; pattern=\d+\.\d+\.\d+ |
| `recipe.mode` · select | Source format / Formato de fuente<br>Changing format clears incompatible rules only after confirmation. / Cambiar formato borra reglas incompatibles solo tras confirmar. | Load current saved/server value; illustrative fixture: json | html → HTML elements / Elementos HTML; json → JSON response / Respuesta JSON; regex → Text / regex / Texto / regex |
| `recipe.records` · text | Repeating record / Registro repetido<br>Records array path, or blank for a root array. Field paths are relative to each object. / Ruta del array, o vacío para array raíz. Los campos son relativos a cada objeto. | Load current saved/server value; illustrative fixture: channels | maxlength=1024 |
| `recipe.fields.name.path` · text | Name JSON path / Ruta JSON de nombre<br>Relative to the record. An ID array yields several streams with the same name; maximum 256 characters. / Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres. | Load current saved/server value; illustrative fixture: name | maxlength=256 |
| `recipe.fields.name.pattern` · text | Name regex / Regex de nombre<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024 |
| `recipe.fields.id.path` · text | Content ID JSON path / Ruta JSON de id de contenido<br>Relative to the record. An ID array yields several streams with the same name; maximum 256 characters. / Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres. | Load current saved/server value; illustrative fixture: id | maxlength=256 |
| `recipe.fields.id.pattern` · text | Content ID regex / Regex de id de contenido<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024 |
| `recipe.fields.group.path` · text | Group JSON path / Ruta JSON de grupo<br>Relative to the record. An ID array yields several streams with the same name; maximum 256 characters. / Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres. | Load current saved/server value; illustrative fixture: group | maxlength=256; Advanced disclosure |
| `recipe.fields.group.pattern` · text | Group regex / Regex de grupo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.fields.logo.path` · text | Logo JSON path / Ruta JSON de logotipo<br>Relative to the record. An ID array yields several streams with the same name; maximum 256 characters. / Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres. | Load current saved/server value; illustrative fixture: logo | maxlength=256; Advanced disclosure |
| `recipe.fields.logo.pattern` · text | Logo regex / Regex de logotipo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.fields.epg_id.path` · text | Guide ID JSON path / Ruta JSON de id de guía<br>Relative to the record. An ID array yields several streams with the same name; maximum 256 characters. / Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres. | Load current saved/server value; illustrative fixture: epg_id | maxlength=256; Advanced disclosure |
| `recipe.fields.epg_id.pattern` · text | Guide ID regex / Regex de id de guía<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=1024; Advanced disclosure |
| `recipe.flags` · text | Regex flags / Opciones regex<br>i ignores case; m line anchors; s includes newlines. No named groups or backreferences. / i ignora mayúsculas; m ancla líneas; s incluye saltos. Sin grupos con nombre ni referencias inversas. | Load current saved/server value; illustrative fixture: is | pattern=[ims]{0,3} |

**Contextual exits:** [Manual selection / Selección manual](workflow-prototype.html?screen=helper-manual); [Independent helper / Asistente independiente](workflow-prototype.html?screen=helper-standalone).

<a id="helper-regex"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-regex`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Read paired text records / Leer registros de texto emparejados

[Open composition](workflow-prototype.html?screen=helper-regex) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Each bounded regex match is one record. Name and ID extraction run inside that record. / Cada coincidencia limitada es un registro. Nombre e ID se extraen dentro de ese registro.

**Evidence:** [RecipeFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, timeout, invalid. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **timeout:** The bounded test stopped before completing. Simplify the record rule or use a smaller sample. Existing channels are unchanged. / La prueba se detuvo antes de terminar. Simplifica la regla o reduce la muestra. Los canales no cambian.
- **invalid:** This extraction rule is not supported. Your draft is retained. Correct the highlighted field before testing again. / Esta regla no es compatible. Se conserva el borrador. Corrige el campo marcado antes de probar de nuevo.

**Implementation constraint for `invalid`:** This rule is not supported. Keep the draft and show the field-level reason without running unbounded regex. / Esta regla no se admite. Conserva el borrador y muestra el motivo sin ejecutar regex sin límites.

**Synthetic sample:**

```text
[{"name":"Northlight HD","id":"0000000000000000000000000000000000000000","group":"Documentary"}]
```

### Paired record fields / Campos emparejados

**Save timing:** explicit action. **Action:** Test recipe / Probar receta. **Boundary:** `recipeService.preview / standalone worker`. View/preview only; no persistent data mutation.

**Consequence:** Read-only bounded test. Changing sample or recipe invalidates the previous test; do not enable Save from stale results. / Prueba limitada sin cambios. Cambiar muestra o receta invalida la prueba anterior; no permitas guardar resultados antiguos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recipe.name` · text | Recipe name / Nombre de receta<br>1–100 characters. / 1–100 caracteres. | Load current saved/server value; illustrative fixture: Sample paired records | required=True; maxlength=100 |
| `recipe.version` · text | Recipe version / Versión de receta<br>Semantic version such as 1.0.0; schema_version remains 1. / Versión como 1.0.0; schema_version permanece en 1. | Load current saved/server value; illustrative fixture: 1.0.0 | required=True; pattern=\d+\.\d+\.\d+ |
| `recipe.mode` · select | Source format / Formato de fuente<br>Changing format clears incompatible rules only after confirmation. / Cambiar formato borra reglas incompatibles solo tras confirmar. | Load current saved/server value; illustrative fixture: regex | html → HTML elements / Elementos HTML; json → JSON response / Respuesta JSON; regex → Text / regex / Texto / regex |
| `recipe.records` · text | Repeating record / Registro repetido<br>Each bounded regex match is one record. Name and ID extraction run inside that record. / Cada coincidencia limitada es un registro. Nombre e ID se extraen dentro de ese registro. | Load current saved/server value; illustrative fixture: (.+?)<br>([a-f0-9]{40}) | maxlength=1024 |
| `recipe.fields.name.pattern` · text | Name regex / Regex de nombre<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: (.+) | maxlength=1024 |
| `recipe.fields.id.pattern` · text | Content ID regex / Regex de id de contenido<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: (.+) | maxlength=1024 |
| `recipe.fields.group.pattern` · text | Group regex / Regex de grupo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: (.+) | maxlength=1024; Advanced disclosure |
| `recipe.fields.logo.pattern` · text | Logo regex / Regex de logotipo<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: (.+) | maxlength=1024; Advanced disclosure |
| `recipe.fields.epg_id.pattern` · text | Guide ID regex / Regex de id de guía<br>First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters. / La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: (.+) | maxlength=1024; Advanced disclosure |
| `recipe.flags` · text | Regex flags / Opciones regex<br>i ignores case; m line anchors; s includes newlines. No named groups or backreferences. / i ignora mayúsculas; m ancla líneas; s incluye saltos. Sin grupos con nombre ni referencias inversas. | Load current saved/server value; illustrative fixture: is | pattern=[ims]{0,3} |

**Contextual exits:** [Manual selection / Selección manual](workflow-prototype.html?screen=helper-manual); [Independent helper / Asistente independiente](workflow-prototype.html?screen=helper-standalone).

<a id="helper-manual"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-manual`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Select fields manually / Seleccionar campos manualmente

[Open composition](workflow-prototype.html?screen=helper-manual) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Start with one complete record, then identify its name and ID. / Empieza con un registro completo e identifica nombre e ID.

**Evidence:** [RecipeBuilder.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeBuilder.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Synthetic read-only output:**

```text
Northlight HD
0000000000000000000000000000000000000000
```

### Selection tools / Herramientas de selección

**Save timing:** explicit action. **Action:** Use selection / Usar selección. **Boundary:** `RecipeBuilder source selection`. View/preview only; no persistent data mutation.

**Consequence:** Field rule updated locally. Test the whole recipe before saving. / Regla actualizada localmente. Prueba toda la receta antes de guardar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `manual.target` · select | Assign selection to / Asignar selección a<br>Pick the repeating record first, then fields inside it. Keyboard selection works in raw text. / Elige primero el registro y después sus campos. Se puede seleccionar texto con teclado. | Load current saved/server value; illustrative fixture: records | records → Repeating record / Registro repetido; name → Name / Nombre; id → Content ID / ID de contenido; group → Group / Grupo; logo → Logo / Logotipo; epg_id → Guide ID / ID de guía |
| `manual.selection` · textarea | Selected text / Texto seleccionado<br>Show exact original text; do not translate or normalize IDs. / Muestra texto original; no traduzcas ni normalices IDs. | Load current saved/server value; illustrative fixture: Northlight HD | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Review generated field rules / Revisar reglas generadas](workflow-prototype.html?screen=helper-regex).

<a id="helper-large"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-large`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## This sample is too large to draw safely / La muestra es demasiado grande para dibujarla

[Open composition](workflow-prototype.html?screen=helper-large) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Use the original text and manual fields when a visual preview is too large. / Usa el texto original y campos manuales si la vista visual es demasiado grande.

**Evidence:** [VisualPicker.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/VisualPicker.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, too-large. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **too-large:** This sample exceeds the 32 MiB limit. Your previous sample and recipe are unchanged. Choose a smaller sample. / La muestra supera 32 MiB. La muestra y receta anteriores siguen intactas. Elige una muestra menor. Page title: Choose a smaller sample / Elige una muestra menor.

**Implementation constraint for `too-large`:** The input exceeds the admission limit. Reject before JSON parsing; retain the previous sample and recipe. / La entrada supera el límite. Rechaza antes de analizar JSON; conserva muestra y receta anteriores.

**Explanation:** Synthetic large-input state. Source support is 32 MiB; browser rendering uses a smaller bounded budget. A successful upload does not guarantee a visual preview. / Estado ficticio de muestra grande. Las fuentes admiten 32 MiB; la visualización tiene un límite menor. Subir correctamente no garantiza vista visual.

**Continue without visual rendering / Continuar sin vista visual**

- Use raw selection / Usar selección de texto: Keep sample loaded and select a repeating record / Conserva la muestra y selecciona un registro [Open related workflow](workflow-prototype.html?screen=helper-manual).
- Enter JSON paths / Introducir rutas JSON: Use object paths without rendering the full tree / Usa rutas sin dibujar todo el árbol [Open related workflow](workflow-prototype.html?screen=helper-json).
- Test on installation / Probar en instalación: Installed bounded preview supports the server-side workflow / La vista limitada de instalación permite probar en servidor [Open related workflow](workflow-prototype.html?screen=helper-installed).

### Authored composition for `too-large`

[Open this state](workflow-prototype.html?screen=helper-large&state=too-large). This replaces the default content rather than placing a warning over contradictory fixture data.

**Explanation:** This sample exceeds the 32 MiB source limit. It has not been parsed or sent for a test. Choose a smaller representative sample. / La muestra supera el límite de fuente de 32 MiB. No se ha analizado ni enviado a probar. Elige una muestra representativa menor.

**Read-only context: Limits have different purposes / Límites con fines distintos**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Source admission / Admisión de fuente | 32 MiB maximum / Máximo 32 MiB |
| Browser rendering / Visualización | Smaller bounded budget; large admitted samples may need raw/manual fields / Presupuesto menor; muestras admitidas pueden necesitar texto/campos manuales |
| Recipe document / Documento de receta | 512 KiB maximum / Máximo 512 KiB |

**Contextual exits:** [Choose a different sample / Elegir otra muestra](workflow-prototype.html?screen=helper-standalone); [Read the manual-field workflow / Ver flujo de campos manuales](workflow-prototype.html?screen=helper-manual).

<a id="helper-results"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `helper-results`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Review extraction results / Revisar resultados de extracción

[Open composition](workflow-prototype.html?screen=helper-results) · existing route/context: `/scraper/builder` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Successful extraction does not mean a stream is online. / Extraer correctamente no significa que haya señal.

**Evidence:** [RecipeResults.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/recipes/RecipeResults.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, stale. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **stale:** The recipe or sample changed after this test. Test again before saving; old results are only a reference. / La receta o muestra cambió tras probar. Vuelve a probar antes de guardar; los resultados antiguos son referencia.

**Read-only context: Synthetic test / Prueba ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Records / Registros | 4 / 4 |
| Valid / invalid / duplicate / Válidos / inválidos / duplicados | 2 / 1 / 1 / 2 / 1 / 1 |
| Pairing / Emparejamiento | Northlight HD → 0000000000000000000000000000000000000000 / Northlight HD → 0000000000000000000000000000000000000000 |

**Issues / Problemas**

- Record 3 / Registro 3: Missing content ID; skipped without pairing it with another row / Falta ID; omitido sin emparejarlo con otra fila

**Copy action:** Copy example recipe JSON / Copiar JSON de receta. Placeholder `{"schema_version":1,"name":"DEMO","version":"1.0.0","mode":"json","records":"","flags":"is","fields":{"name":{"path":"name"},"id":{"path":"id"}}}`; show success or a selectable fallback without logging the value.

**Save recipe to selected source / Guardar receta en fuente seleccionada:** Installed helper only: attach the tested recipe to Family channels? Source import remains a separate action. / Solo instalado: ¿vincular la receta probada a Family channels? Importar es otra acción.

Result copy: Recipe saved; source not imported. Standalone instead copies or exports the recipe. / Receta guardada; fuente sin importar. El asistente independiente copia o exporta.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Return to source / Volver a fuente](workflow-prototype.html?screen=source-web).

<a id="dashboard"></a>

**Simplified location:** Watch → Watch. **Composition:** primary destination. **Canonical editor:** `dashboard`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Watch / Ver

[Open composition](workflow-prototype.html?screen=dashboard) · existing route/context: `/` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Your channels. Something worth watching. / Tus canales. Algo que apetece ver.

**Evidence:** [TVDashboard.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/TVDashboard.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, first-use, partial, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **first-use:** Start by adding a channel source. A guide is optional, and HTTP channels can work without an AceStream engine. / Empieza añadiendo una fuente. La guía es opcional y los canales HTTP pueden funcionar sin motor AceStream. Page title: Welcome to AceStream / Te damos la bienvenida.
- **partial:** Upcoming events could not load. Channels and recordings remain usable. Retry events only. / No se cargaron eventos próximos. Canales y grabaciones siguen disponibles. Reintenta solo eventos.
- **art-absent:** No artwork is available. Names and actions are ready. / No hay imagen disponible. Los nombres y acciones siguen listos.
- **art-slow:** Artwork is taking longer. Continue without it. / La imagen tarda. Puedes continuar sin ella.
- **art-blocked:** Artwork could not be loaded from this address. Use the text details. / No se pudo cargar la imagen de esta dirección. Consulta los datos.
- **art-rejected:** This image type is not supported. Use the text details. / El tipo de imagen no es compatible. Consulta los datos.
- **art-oversized:** The image exceeds the safe size limit. It has not been opened. / La imagen supera el límite seguro. No se ha abierto.
- **art-decode-failed:** This image could not be displayed. Try loading it again. / No se pudo mostrar la imagen. Prueba a cargarla de nuevo.
- **art-changed:** The artwork changed. Load the new image when you are ready. / La imagen cambió. Carga la nueva cuando quieras.

**Contextual exits:** [Upcoming event preferences / Preferencias de próximos eventos](workflow-prototype.html?screen=dashboard-events).

### Authored composition for `first-use`

[Open this state](workflow-prototype.html?screen=dashboard&state=first-use). This replaces the default content rather than placing a warning over contradictory fixture data.

**Explanation:** Your catalogue is empty. Add a channel source to begin; a programme guide is optional. / Tu catálogo está vacío. Añade una fuente para empezar; la guía es opcional.

**Get ready to watch / Prepara tu televisión**

- 1 · Add a channel source / 1 · Añade una fuente: Use a website or playlist link, or an installed broadcaster. / Usa una web, lista o proveedor instalado. [Open related workflow](workflow-prototype.html?screen=setup-source).
- 2 · Optional programme guide / 2 · Guía opcional: Adds names and times; video does not require a guide. / Añade nombres y horarios; no hace falta para vídeo. [Open related workflow](workflow-prototype.html?screen=setup-guide).
- 3 · Review your channels / 3 · Revisa tus canales: Imported channels are not yet proof of signal. / Importar no demuestra señal. [Open related workflow](workflow-prototype.html?screen=channels).

**Contextual exits:** [Start setup / Empezar configuración](workflow-prototype.html?screen=setup).

<a id="live"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `live`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Watch / Ver

[Open composition](workflow-prototype.html?screen=live) · existing route/context: `/live-tv` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Choose a channel and keep browsing while you watch. / Elige un canal y sigue explorando mientras lo ves.

**Evidence:** [LiveTV.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/LiveTV.tsx)

**Permission:** live permission / public viewing policy. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, refreshing, failed, stalled, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **filtered:** No channels match Online only. Show all channels to include unknown or offline observations. Current playback continues. / Ningún canal cumple Solo con señal. Ver todos incluye estados desconocidos o sin señal. La reproducción continúa.
- **refreshing:** Updating the channel list. Your selected channel keeps playing. / Actualizando la lista. El canal elegido sigue reproduciéndose.
- **failed:** This source could not start. Retry or choose another available source. / No se pudo iniciar esta emisión. Reintenta o elige otra disponible.
- **stalled:** Video has stopped arriving. Wait a moment, retry or choose another source. / Ha dejado de llegar vídeo. Espera un momento, reintenta o elige otra emisión.
- **empty:** No channels yet. Open setup if you can manage this installation; viewers should ask its owner. / Aún no hay canales. Abre configuración si puedes administrarla; los espectadores deben pedir ayuda al propietario.
- **art-absent:** No artwork is available. Names and actions are ready. / No hay imagen disponible. Los nombres y acciones siguen listos.
- **art-slow:** Artwork is taking longer. Continue without it. / La imagen tarda. Puedes continuar sin ella.
- **art-blocked:** Artwork could not be loaded from this address. Use the text details. / No se pudo cargar la imagen de esta dirección. Consulta los datos.
- **art-rejected:** This image type is not supported. Use the text details. / El tipo de imagen no es compatible. Consulta los datos.
- **art-oversized:** The image exceeds the safe size limit. It has not been opened. / La imagen supera el límite seguro. No se ha abierto.
- **art-decode-failed:** This image could not be displayed. Try loading it again. / No se pudo mostrar la imagen. Prueba a cargarla de nuevo.
- **art-changed:** The artwork changed. Load the new image when you are ready. / La imagen cambió. Carga la nueva cuando quieras.

**Implementation constraint for `refreshing`:** Updating catalogue in the background. Keep the player and selected channel in place. / Actualizando el catálogo en segundo plano. Conserva reproductor y canal seleccionado.

**Implementation constraint for `failed`:** This source could not start. Try another eligible source or retry; do not clear the browse list. / No se inició esta emisión. Prueba otra apta o reintenta; conserva la lista.

**Implementation constraint for `stalled`:** Video is not arriving. Keep the last frame with a textual status and offer another source; do not label the channel permanently offline. / No llega vídeo. Conserva el último fotograma con estado textual y ofrece otra emisión; no declares el canal sin señal permanente.

**Player region:** Northlight · Coastlines: the Atlantic · Playing illustration · no media session / Ilustración de reproducción · sin sesión real. Static illustration only; use the media interaction contract for ownership and integrated acceptance.

**Contextual exits:** [Audio and subtitles / Audio y subtítulos](workflow-prototype.html?screen=player-tracks); [Send to TV / Enviar a TV](workflow-prototype.html?screen=casting-control); [Record programme / Grabar programa](workflow-prototype.html?screen=recording-schedule).

### Browse / Explorar

**Save timing:** explicit action. **Action:** Apply browse filter / Aplicar filtro. **Boundary:** `LiveTV URL state`. View/preview only; no persistent data mutation.

**Consequence:** Browse list updated. Selection and player identity survive filtering and the 30-second catalogue refresh. / Lista actualizada. Selección y reproductor sobreviven filtros y actualización cada 30 segundos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `live.list` · select | Browse list / Lista<br>Changing list keeps the active viewer. / Cambiar lista conserva el espectador activo. | Load current saved/server value; illustrative fixture: tv | tv → TV channels / Canales de TV; streams → Streams / Emisiones; events → Events / Eventos |
| `live.q` · search | Search / Buscar<br>Search filters only the browse list. / Solo filtra la lista. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `live.online_only` · checkbox | Online only / Solo con señal verificada<br>On by default. A recent successful check helps you choose; playback can still fail. Turn off to show all channels. / Activado por defecto. Una comprobación reciente ayuda a elegir; la reproducción aún puede fallar. Desactívalo para ver todos. | Load current saved/server value; illustrative fixture: True | Adapter/contract note: Default on for TV and streams. Latest observation is not current playback certainty. Show all uses availability=all. / Activado en TV y emisiones. La última observación no garantiza reproducción. Ver todo usa availability=all. |

**Channels and now/next / Canales y ahora/después**

- Northlight / Northlight: Now Coastlines: the Atlantic · next Inside the studio / Ahora Coastlines: the Atlantic · después Inside the studio [Open related workflow](workflow-prototype.html?screen=live).
- World 24 / World 24: No guide data · watching does not require a guide / Sin guía · no es necesaria para ver [Open related workflow](workflow-prototype.html?screen=live).

**Stop watching / Dejar de ver:** Release this browser’s viewer? Other viewers keep their own leases. / ¿Liberar este espectador? Los demás conservan sus sesiones.

Result copy: Viewer released. Catalogue stays available. / Espectador liberado. El catálogo sigue disponible.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Switch channel / Cambiar canal](workflow-prototype.html?screen=player-picker).

<a id="player-tracks"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `player-tracks`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Playback options / Opciones de reproducción

[Open composition](workflow-prototype.html?screen=player-tracks) · existing route/context: `player dialog` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Change only this viewer’s track selection. / Cambia las pistas solo de este espectador.

**Evidence:** [StreamPlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/StreamPlayerDialog.tsx)

**Permission:** viewer capability; ownership token. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, capacity. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **capacity:** All playback slots are in use. Keep the current track or retry when a slot is available. / Todas las plazas están ocupadas. Conserva la pista actual o reintenta cuando haya una libre.

**Implementation constraint for `capacity`:** No session capacity for this track change. Keep a usable prior state where lifecycle permits; show Retry or Cancel, not a blank player. / No hay capacidad para cambiar pistas. Conserva un estado útil cuando lo permita el ciclo; ofrece Reintentar o Cancelar.

### Tracks and source / Pistas y emisión

**Save timing:** explicit action. **Action:** Apply playback choice / Aplicar selección. **Boundary:** `playerService shared viewer lifecycle`. View/preview only; no persistent data mutation.

**Consequence:** Preparing the selected tracks; other viewers remain on their own sessions. / Preparando pistas; los demás conservan sus sesiones.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `player.audio_index` · select | Audio / Audio<br>Discovered input language, codec and layout. Missing metadata stays unknown. Changing it restarts only this viewer. / Idioma, códec y canales de entrada. Datos ausentes siguen desconocidos. Cambiar reinicia solo este espectador. | Load current saved/server value; illustrative fixture: 0 | 0 → Spanish · AAC · stereo / Español · AAC · estéreo; 1 → Original · AC-3 · 5.1 / Original · AC-3 · 5.1 |
| `player.subtitle_index` · select | Subtitles / Subtítulos<br>Off by default. Bitmap subtitle conversion is unsupported. / Desactivados por defecto. No se convierte subtitulado de imagen. | Load current saved/server value; illustrative fixture:  |  → Off / Desactivados; 0 → Spanish · text / Español · texto |
| `player.source` · select | Source / Emisión<br>Changing source releases this viewer’s old lease. Copied and remote links keep original tracks. / Cambiar emisión libera la sesión anterior de este espectador. Enlaces copiados y remotos conservan pistas originales. | Load current saved/server value; illustrative fixture: 1 | 1 → Northlight HD / Northlight HD; 2 → Northlight backup / Northlight backup |

**Contextual exits:** [Back to player / Volver al reproductor](workflow-prototype.html?screen=live); [Open in another player / Abrir en otro reproductor](workflow-prototype.html?screen=remote-control).

<a id="viewer"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `viewer`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Your viewing access / Tu acceso de visualización

[Open composition](workflow-prototype.html?screen=viewer) · existing route/context: `/watch` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Only your permitted viewing features appear here. / Aquí aparecen solo las funciones permitidas.

**Evidence:** [Watch.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Watch.tsx)

**Permission:** non-admin viewer / public feature policy. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, denied. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **denied:** This account cannot use recordings. Signing in again does not grant permission; ask an administrator. / Esta cuenta no puede usar grabaciones. Volver a entrar no concede permiso; pide acceso al administrador.

**Available to viewer-demo / Disponible para viewer-demo**

- Live TV / TV en directo: Granted / Permitido [Open related workflow](workflow-prototype.html?screen=live).
- Programme guide / Guía de programación: Granted / Permitido [Open related workflow](workflow-prototype.html?screen=guide-detail).
- Recordings / Grabaciones: Not granted · ask the administrator / No permitido · pide acceso al administrador

**Contextual exits:** [Sign in with another account / Entrar con otra cuenta](workflow-prototype.html?screen=access-login); [Change your password / Cambiar contraseña](workflow-prototype.html?screen=access-password).

<a id="events"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** primary destination. **Canonical editor:** `events`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Event agenda / Agenda de eventos

[Open composition](workflow-prototype.html?screen=events) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Times help you plan; they do not prove an event is live or a stream works. / Las horas ayudan a planificar; no demuestran directo ni señal.

**Evidence:** [EventAgenda.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventAgenda.tsx); [Events.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Events.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Your view / Tu vista

**Save timing:** explicit action. **Action:** Apply agenda view / Aplicar vista. **Boundary:** `eventPreferences`. View/preview only; no persistent data mutation.

**Consequence:** Display preferences changed for this browser only. / Preferencias visuales cambiadas solo en este navegador.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `agenda.zone` · text | Display timezone / Zona de visualización<br>Browser preference only; does not change source or recording timezones. / Solo preferencia del navegador; no cambia fuentes ni grabaciones. | Load current saved/server value; illustrative fixture: Europe/Madrid | No additional prototype constraint; preserve current source validation. |
| `agenda.sports` · text | Sports / Deportes<br>OR interests; original values. Empty means no interest filter. / Intereses unidos por O; valores originales. Vacío no filtra. | Load current saved/server value; illustrative fixture: Football | No additional prototype constraint; preserve current source validation. |
| `agenda.competitions` · text | Competitions / Competiciones<br>Browser display preference, distinct from provider fetch filters. / Preferencia visual, distinta de filtros de consulta al proveedor. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `agenda.teams` · text | Teams / Equipos<br>Original participant names. / Nombres originales de participantes. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `agenda.following` · checkbox | Following only / Solo seguidos<br>Following itself is installation-wide, not personal. / Seguir es para toda la instalación, no personal. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `agenda.when` · select | When / Cuándo<br>Choose the time scope; changing filters returns to the first page. / Elige ámbito temporal; cambiar filtros vuelve a primera página. | Load current saved/server value; illustrative fixture: upcoming | upcoming → Upcoming / Próximos; today → Today / Hoy; date → Choose a date / Elegir fecha; all → All saved / Todos guardados; archived → Archived / Archivados |
| `agenda.day` · date | Event date / Fecha del evento<br>Only used with Choose a date, interpreted in display timezone. / Solo con Elegir fecha; interpretada en zona de visualización. | Load current saved/server value; illustrative fixture: 2026-11-08 | enabled when agenda.when=date |
| `agenda.search` · search | Search events / Buscar eventos<br>Original event names remain unchanged. / Conserva nombres originales. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `agenda.window_days` · select | Upcoming window / Intervalo próximo<br>UI choices 7, 14, 30 days; default 14. / Opciones 7, 14, 30 días; por defecto 14. | Load current saved/server value; illustrative fixture: 14 | Advanced disclosure; 7 → 7 days / 7 días; 14 → 14 days / 14 días; 30 → 30 days / 30 días |
| `agenda.sport` · text | Sport contains / Deporte contiene<br>Free text, separate from saved interests. / Texto libre, separado de intereses guardados. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `agenda.competition` · text | Competition contains / Competición contiene<br>Free text; keeps original competition names. / Texto libre; conserva nombres originales. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `agenda.source` · text | Source / Fuente<br>Filter imported provenance without changing the source. / Filtra origen sin cambiar fuente. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |

**8 November · Europe/Madrid / 8 de noviembre · Europe/Madrid**

- 18:00 · Northlight Cup / 18:00 · Northlight Cup: Northlight United / Atelier City · time supplied by provider / Northlight United / Atelier City · hora del proveedor [Open related workflow](workflow-prototype.html?screen=event-detail).
- World friendly / World friendly: Kickoff unknown · date only / Hora desconocida · solo fecha [Open related workflow](workflow-prototype.html?screen=event-detail).

**Contextual exits:** [Add provider events / Añadir eventos de proveedor](workflow-prototype.html?screen=event-provider); [Add URL / JSON / manual event / Añadir URL / JSON / evento manual](workflow-prototype.html?screen=event-import); [Sources and retention / Fuentes y conservación](workflow-prototype.html?screen=event-sources).

**Contextual exits:** [Broadcaster links / Vínculos de emisoras](workflow-prototype.html?screen=event-broadcasters).

<a id="event-detail"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-detail`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Northlight Cup / Northlight Cup

[Open composition](workflow-prototype.html?screen=event-detail) · existing route/context: `/events?event=demo&zone=Europe/Madrid` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Review broadcasts, corrections and the guide overlay. / Revisa emisiones, correcciones y superposición en guía.

**Evidence:** [EventDetails.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventDetails.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, unknown, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unknown:** This event has a date but no confirmed start time. A timed recording needs a confirmed time. / Este evento tiene fecha, pero aún no tiene hora de inicio confirmada. Para programar una grabación hace falta una hora. Page title: World Friendly / World Friendly.
- **art-absent:** No artwork is available. Names and actions are ready. / No hay imagen disponible. Los nombres y acciones siguen listos.
- **art-slow:** Artwork is taking longer. Continue without it. / La imagen tarda. Puedes continuar sin ella.
- **art-blocked:** Artwork could not be loaded from this address. Use the text details. / No se pudo cargar la imagen de esta dirección. Consulta los datos.
- **art-rejected:** This image type is not supported. Use the text details. / El tipo de imagen no es compatible. Consulta los datos.
- **art-oversized:** The image exceeds the safe size limit. It has not been opened. / La imagen supera el límite seguro. No se ha abierto.
- **art-decode-failed:** This image could not be displayed. Try loading it again. / No se pudo mostrar la imagen. Prueba a cargarla de nuevo.
- **art-changed:** The artwork changed. Load the new image when you are ready. / La imagen cambió. Carga la nueva cuando quieras.

**Read-only context: Event details / Detalles**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Participants / Participantes | Northlight United · Atelier City / Northlight United · Atelier City |
| Time / Hora | 8 Nov 18:00 · Europe/Madrid · provider observation / 8 nov 18:00 · Europe/Madrid · dato del proveedor |
| Following / Seguimiento | Installation-wide / Toda la instalación |

**Broadcasts / Emisiones**

- Atelier / Atelier: Two regional channel choices; not yet playable / Dos opciones regionales; aún no reproducible [Open related workflow](workflow-prototype.html?screen=event-mapping).
- Event-only HTTP / HTTP solo para evento: Supported media may open the shared player without TV assignment or playlist export. / Contenido compatible puede abrir el reproductor sin asignación TV ni exportación. [Open related workflow](workflow-prototype.html?screen=live).

**Follow event / Seguir evento:** Follow for everyone using this installation? / ¿Seguir para toda la instalación?

Result copy: Event followed for the installation. / Evento seguido para toda la instalación.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Archive event / Archivar evento:** Hide from the ordinary agenda? Unarchive remains possible until opt-in retention deletes it. / ¿Ocultar de la agenda habitual? Se puede recuperar hasta que lo borre la conservación opcional.

Result copy: Archived. Unarchive is available. / Archivado. Se puede recuperar.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Correct event details / Corregir datos](workflow-prototype.html?screen=event-correct); [Choose broadcaster link / Elegir vínculo de emisora](workflow-prototype.html?screen=event-mapping); [Review guide overlay / Revisar superposición en guía](workflow-prototype.html?screen=event-overlay).

### Authored composition for `unknown`

[Open this state](workflow-prototype.html?screen=event-detail&state=unknown). This replaces the default content rather than placing a warning over contradictory fixture data.

**Read-only context: World Friendly / World Friendly**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Date / Fecha | 9 Nov 2026 / 9 nov 2026 |
| Time / Hora | Unknown / Desconocida |
| Source / Fuente | OpenFootball · synthetic fixture / OpenFootball · ejemplo ficticio |
| Source timezone / Zona de fuente | Europe/Madrid / Europe/Madrid |

**Explanation:** Keep the date-only fixture visible in the agenda. A known time can be reviewed later; date-only does not mean cancelled. / Conserva el evento con fecha en agenda. Se puede revisar hora más adelante; sin hora no significa cancelado.

**Contextual exits:** [Review event information / Revisar información](workflow-prototype.html?screen=event-correct); [Review provider scope / Revisar ámbito del proveedor](workflow-prototype.html?screen=event-provider); [Back to agenda / Volver a agenda](workflow-prototype.html?screen=events).

<a id="event-provider"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-provider`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add provider events / Añadir eventos de proveedor

[Open composition](workflow-prototype.html?screen=event-provider) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Choose source filters before fetching; review new events before importing. / Elige filtros antes de consultar y revisa eventos nuevos antes de importar.

**Evidence:** [EventProviderFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventProviderFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Provider selection / Selección de proveedor

**Save timing:** explicit action. **Action:** Preview events / Ver eventos. **Boundary:** `eventService provider preview`. View/preview only; no persistent data mutation.

**Consequence:** Preview only. WOSTI changed dates/times require review; never silently merge as rescheduling. / Solo vista previa. Cambios de fecha/hora WOSTI requieren revisión; no se fusionan como reprogramación.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `provider.provider` · select | Provider / Proveedor<br>Fixed guarded adapters, not an arbitrary executable plugin. / Adaptadores fijos protegidos, no plugins ejecutables arbitrarios. | Load current saved/server value; illustrative fixture: wosti_es | wosti_es → Fútbol en la TV · Spain / Fútbol en la TV · España; openfootball → OpenFootball / OpenFootball |
| `provider.feeds` · text | Sports feeds / Fuentes deportivas<br>WOSTI default all + automovilismo; original enum values preserved. / WOSTI por defecto all + automovilismo; conserva los valores. | Load current saved/server value; illustrative fixture: all,automovilismo | No additional prototype constraint; preserve current source validation. |
| `provider.football_competitions` · text | Football competitions / Competiciones de fútbol<br>Remove All sports to narrow football upstream requests; other selected sports remain. / Quita Todos los deportes para limitar fútbol; conserva los otros deportes. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `provider.league` · text | League / Liga<br>OpenFootball league; preserve es.1 default where selected. / Liga OpenFootball; conserva es.1 por defecto. | Load current saved/server value; illustrative fixture: es.1 | Advanced disclosure |
| `provider.season` · text | Season / Temporada<br>Current season from source; format 2026-27. / Temporada de fuente; formato 2026-27. | Load current saved/server value; illustrative fixture: 2026-27 | pattern=20[0-9]{2}-[0-9]{2}; Advanced disclosure |
| `provider.window_days` · number | Import window (days) / Ventana de importación (días)<br>Default 14; 1–30. / Por defecto 14; 1–30. | Load current saved/server value; illustrative fixture: 14 | min=1; max=30 |
| `provider.timezone` · text | Source timezone / Zona horaria de fuente<br>WOSTI uses Europe/Madrid. Date-only fixtures keep kickoff unknown. / WOSTI usa Europe/Madrid. Las fechas sin hora mantienen inicio desconocido. | Load current saved/server value; illustrative fixture: Europe/Madrid | No additional prototype constraint; preserve current source validation. |
| `provider.interests.sports` · text | Interested sports / Deportes de interés<br>OR with teams and competitions; preserve outside-filter data. / O con equipos y competiciones; conserva datos fuera del filtro. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `provider.interests.competitions` · text | Interested competitions / Competiciones de interés<br>Up to 100 original values. / Hasta 100 valores originales. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `provider.interests.teams` · text | Interested teams / Equipos de interés<br>Up to 100 original values. / Hasta 100 valores originales. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |

<a id="event-import"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-import`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add events / Añadir eventos

[Open composition](workflow-prototype.html?screen=event-import) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Paste event details, load a URL or upload JSON, then review what to import. / Introduce datos, carga una URL o un JSON y revisa qué importar.

**Evidence:** [EventImportPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventImportPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Input / Entrada

**Save timing:** explicit action. **Action:** Preview import / Ver importación. **Boundary:** `eventService preview`. View/preview only; no persistent data mutation.

**Consequence:** Read-only preview. No permanent channel is created for an event-only broadcast. / Vista sin cambios. Una emisión de evento no crea un canal permanente.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `event.input` · select | Add from / Añadir desde<br>Choose manual entry, URL, JSON or reviewed W3U event handoff. / Elige manual, URL, JSON o enlace revisado desde W3U. | Load current saved/server value; illustrative fixture: manual | manual → Manual / Manual; url → Schedule URL / URL de agenda; json → Schedule JSON / JSON de agenda |
| `event.title` · text | Event title / Título del evento<br>Original title, 1–300 characters. / Título original, 1–300 caracteres. | Load current saved/server value; illustrative fixture: Northlight Cup | required=True; maxlength=300; enabled when event.input=manual |
| `event.sport` · text | Sport / Deporte<br>Original sport value; maximum 100 characters. / Valor original; máximo 100 caracteres. | Load current saved/server value; illustrative fixture: Football | maxlength=100; enabled when event.input=manual |
| `event.competition` · text | Competition / Competición<br>Original competition, up to 200 characters. / Competición original, hasta 200 caracteres. | Load current saved/server value; illustrative fixture: Demo League | maxlength=200; enabled when event.input=manual |
| `event.starts_at` · text | Scheduled start / Inicio previsto<br>Unknown may remain blank. Ambiguous DST times require an explicit UTC offset. / Puede quedar vacío si se desconoce. Horas ambiguas requieren desfase UTC explícito. | Load current saved/server value; illustrative fixture: 2026-11-08T18:00:00+01:00 | enabled when event.input=manual |
| `event.timezone` · text | Source timezone / Zona horaria de fuente<br>Publisher’s IANA timezone; independent of display language and viewer timezone. / Zona IANA del editor; independiente del idioma y zona de visualización. | Load current saved/server value; illustrative fixture: Europe/Madrid | required=True; enabled when event.input=manual |
| `event.broadcaster` · text | Broadcaster / Emisora<br>A name alone remains unresolved; it is not a playable stream. / Un nombre solo queda sin resolver; no es una emisión reproducible. | Load current saved/server value; illustrative fixture: Atelier | Advanced disclosure; enabled when event.input=manual |
| `event.url` · text | Stream URL / URL de emisión<br>Optional AceStream/HLS/MPEG-TS. A website remains unsupported; never infer live status from the clock. / AceStream/HLS/MPEG-TS opcional. Una web sigue incompatible; la hora no prueba directo. | Load current saved/server value; illustrative fixture:  | Advanced disclosure; enabled when event.input=manual |
| `event.schedule_url` · text | Schedule URL / URL de agenda<br>Guarded bounded fetch. New identities always require review. / Consulta limitada protegida. Las identidades nuevas requieren revisión. | Load current saved/server value; illustrative fixture:  | Advanced disclosure; enabled when event.input=url |
| `event.format` · select | Guide format / Formato de agenda<br>Version-1 event import or SportsEvent JSON/HTML JSON-LD. / Importación v1 o SportsEvent JSON/HTML JSON-LD. | Load current saved/server value; illustrative fixture: event_import | Advanced disclosure; enabled when event.input=url; event_import → Event schedule JSON v1 / Agenda JSON v1; schema_org → SportsEvent JSON-LD / SportsEvent JSON-LD |
| `event.json` · textarea | Event schedule JSON / JSON de agenda<br>Up to 500 observations per import. Stable source/external IDs; explicit offset for ambiguous time. / Hasta 500 observaciones. IDs estables; desfase explícito para hora ambigua. | Load current saved/server value; illustrative fixture:  | Advanced disclosure; enabled when event.input=json |
| `event.timeout_seconds` · number | Request timeout (seconds) / Tiempo de espera (segundos)<br>5–300; saved for URL previews and refreshes. / 5–300; se guarda para consultas y actualizaciones. | Repository default: 15 | min=5; max=300; Advanced disclosure; enabled when event.input=url |

<a id="event-review"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-review`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Review new events / Revisar eventos nuevos

[Open composition](workflow-prototype.html?screen=event-review) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Select specific event identities; no row is preselected. / Selecciona identidades concretas; ninguna fila está preseleccionada.

**Evidence:** [EventImportPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventImportPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** The preview token or source revision changed. Select again from a fresh preview; existing events are retained. / Cambió el token o revisión. Selecciona de una vista nueva; se conservan eventos existentes.

**Event observations / Observaciones:** Import only selected IDs under the current token. Existing corrections and missing broadcasts are preserved. / Importa IDs elegidos con token actual. Conserva correcciones y emisiones ausentes.

No automatic selection. Select explicit rows. Show row-specific result; expire selection on review-token/revision changes.

### Refresh scope / Ámbito de actualización

**Save timing:** explicit action. **Action:** Include refresh preference / Incluir preferencia. **Boundary:** `EventApply.refresh_source`. View/preview only; no persistent data mutation.

**Consequence:** Sent with the explicit selected import, not a separate silent import of new rows. / Se envía con la importación seleccionada, sin importar filas nuevas en silencio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `event.refresh_source` · checkbox | Refresh reviewed events automatically / Actualizar automáticamente eventos revisados<br>Opt-in for eligible URL/provider sources. W3U event schedules do not auto-refresh. / Opcional en URL/proveedores aptos. Las agendas de eventos W3U no se actualizan solas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

<a id="event-correct"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-correct`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Correct Northlight Cup / Corregir Northlight Cup

[Open composition](workflow-prototype.html?screen=event-correct) · existing route/context: `/events?event=demo` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Manual corrections survive provider refresh. / Las correcciones manuales sobreviven a actualizaciones.

**Evidence:** [EventDetails.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventDetails.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Manual correction / Corrección manual

**Save timing:** explicit action. **Action:** Save correction / Guardar corrección. **Boundary:** `eventService.update`. Submit this resource only; other sections retain independent state.

**Consequence:** Revision-checked correction saved. Source identity and original observations remain separate. / Corrección guardada con revisión. Identidad y observaciones originales siguen separadas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `event.title` · text | Event title / Título del evento<br>Original title, 1–300 characters. / Título original, 1–300 caracteres. | Load current saved/server value; illustrative fixture: Northlight Cup | required=True; maxlength=300 |
| `event.sport` · text | Sport / Deporte<br>Original sport value; maximum 100 characters. / Valor original; máximo 100 caracteres. | Load current saved/server value; illustrative fixture: Football | maxlength=100 |
| `event.competition` · text | Competition / Competición<br>Original competition, up to 200 characters. / Competición original, hasta 200 caracteres. | Load current saved/server value; illustrative fixture: Demo League | maxlength=200 |
| `event.starts_at` · text | Scheduled start / Inicio previsto<br>Unknown may remain blank. Ambiguous DST times require an explicit UTC offset. / Puede quedar vacío si se desconoce. Horas ambiguas requieren desfase UTC explícito. | Load current saved/server value; illustrative fixture: 2026-11-08T18:00:00+01:00 | No additional prototype constraint; preserve current source validation. |
| `event.timezone` · text | Source timezone / Zona horaria de fuente<br>Publisher’s IANA timezone; independent of display language and viewer timezone. / Zona IANA del editor; independiente del idioma y zona de visualización. | Load current saved/server value; illustrative fixture: Europe/Madrid | required=True |
| `event.participants` · text | Participants / Participantes<br>Up to 8 original participant names. / Hasta 8 nombres originales. | Load current saved/server value; illustrative fixture: Northlight United, Atelier City | No additional prototype constraint; preserve current source validation. |
| `event.ends_at` · text | End / Fin<br>Optional; explicit timezone-aware time if known. / Opcional; hora con zona explícita si se conoce. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `event.time_notes` · text | Time notes / Notas de horario<br>Up to 500 characters; explain uncertainty instead of inventing kickoff. / Hasta 500 caracteres; explica incertidumbre sin inventar hora. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `event.state` · select | Reported state / Estado comunicado<br>Provider/manual observation, never inferred from clock alone. / Dato de proveedor/manual, nunca deducido solo del reloj. | Load current saved/server value; illustrative fixture: unknown | unknown → Unknown / Desconocido; scheduled → Scheduled / Programado; live → Reported live / Directo comunicado; finished → Finished / Finalizado; cancelled → Cancelled / Cancelado; postponed → Postponed / Aplazado |

<a id="event-mapping"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-mapping`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Link the broadcaster Atelier / Vincular la emisora Atelier

[Open composition](workflow-prototype.html?screen=event-mapping) · existing route/context: `/events?event=demo` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Choose a regional target and the exact scope of this correction. / Elige destino regional y ámbito exacto de la corrección.

**Evidence:** [EventBroadcastMapper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventBroadcastMapper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Destination and scope / Destino y ámbito

**Save timing:** explicit action. **Action:** Save broadcaster link / Guardar vínculo. **Boundary:** `eventService broadcaster mapping`. Submit this resource only; other sections retain independent state.

**Consequence:** Source alias or event override saved according to the chosen scope; a channel link does not prove signal. / Alias o excepción guardada según ámbito; un vínculo no demuestra señal.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `broadcast.apply_to_source` · checkbox | Apply to every event from this source with this broadcaster / Aplicar a todos los eventos de esta fuente con esta emisora<br>Current default on. An event-only override wins over a source alias. / Activado por defecto. Una excepción del evento prevalece sobre el alias de fuente. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `broadcast.mode` · select | Link to / Vincular a<br>TV/guide identity or individual stream. Names and source qualifiers remain visible. / Identidad de TV/guía o emisión individual. Conserva nombres y fuentes. | Load current saved/server value; illustrative fixture: channels | channels → TV or guide channel / Canal de TV o guía; stream → Individual stream / Emisión individual |
| `broadcast.target` · select | Target / Destino<br>Choose explicitly among country/source-qualified identities. / Elige expresamente entre identidades con país y fuente. | Load current saved/server value; illustrative fixture:  | required=True;  → Choose a target / Elige destino; tv:3 → Atelier · ES · TV / Atelier · ES · TV; epg:4 → Atelier · FR · Regional guide / Atelier · FR · Regional guide |

**Use source broadcast for this event / Usar emisión original para este evento:** Keep the source broadcast here instead of its alias? Store the explicit none override. / ¿Conservar aquí la emisión original en vez del alias? Guarda la excepción none explícita.

Result copy: Event uses its source broadcast. Other events keep the alias. / El evento usa su emisión original. Otros conservan el alias.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="event-overlay"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-overlay`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Review XMLTV overlay / Revisar superposición XMLTV

[Open composition](workflow-prototype.html?screen=event-overlay) · existing route/context: `/events?event=demo` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Preview affected programme slots before adding an event to exported guide data. / Revisa programas afectados antes de añadir el evento a la guía exportada.

**Evidence:** [EventGuideOverlay.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventGuideOverlay.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Preview fingerprint changed. Nothing applied; review the new interval and target. / Cambió la huella. No se aplicó nada; revisa nuevo intervalo y destino.

### Overlay interval / Intervalo de superposición

**Save timing:** explicit action. **Action:** Preview overlay / Ver superposición. **Boundary:** `eventService overlay preview`. View/preview only; no persistent data mutation.

**Consequence:** Review the exact channel, times and affected programmes before applying. / Revisa canal, horarios y programas afectados antes de aplicar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `overlay.broadcast_id` · select | Linked broadcast / Emisión vinculada<br>Only a resolved channel/guide target is eligible. / Solo es apto un destino de canal/guía resuelto. | Load current saved/server value; illustrative fixture: atelier | atelier → Atelier → Sample guide : atelier.example / Atelier → Sample guide : atelier.example |
| `overlay.ends_at` · text | Overlay end with UTC offset / Fin con desfase UTC<br>Explicit end required; maximum 12 hours. Does not change the event’s reported end. / Fin explícito; máximo 12 horas. No cambia el fin comunicado del evento. | Load current saved/server value; illustrative fixture: 2026-11-08T20:00:00+01:00 | required=True |

**Affected exported interval / Intervalo exportado afectado**

- 18:00–20:00 · Northlight Cup / 18:00–20:00 · Northlight Cup: Original guide rows and recording IDs remain intact / Se conservan filas originales e IDs de grabación

**Apply reviewed overlay / Aplicar superposición revisada:** Apply only this preview fingerprint? Changed schedule or target suspends the overlay. / ¿Aplicar solo esta huella? Cambios de horario o destino suspenden la superposición.

Result copy: Overlay applied to export. Original guide rows remain. / Superposición aplicada a exportación. Se conservan programas originales.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="event-sources"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-sources`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Event sources and retention / Fuentes de eventos y conservación

[Open composition](workflow-prototype.html?screen=event-sources) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Refresh reviewed identities; keep new events for manual review. / Actualiza identidades revisadas; reserva eventos nuevos para revisión.

**Evidence:** [EventSourcesPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/EventSourcesPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Saved sources / Fuentes guardadas**

- Demo schedule / Demo schedule: Enabled · 14-day window · reviewed identities only / Activada · 14 días · solo identidades revisadas [Open related workflow](workflow-prototype.html?screen=event-provider).

### Automatic deletion / Eliminación automática

**Save timing:** explicit action. **Action:** Save event retention / Guardar conservación. **Boundary:** `eventService retention`. Submit this resource only; other sections retain independent state.

**Consequence:** Retention saved; applies during existing daily cleanup, not immediately on this screen. / Conservación guardada; se aplica en limpieza diaria, no inmediatamente aquí.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `events.ended_days` · number | Keep ended events (days) / Conservar eventos terminados (días)<br>0 disables; 1–3650 days. Followed events are protected. / 0 desactiva; 1–3650 días. Los eventos seguidos están protegidos. | Load current saved/server value; illustrative fixture: 0 | min=0; max=3650 |
| `events.archived_days` · number | Keep archived events (days) / Conservar archivados (días)<br>0 disables. Archive can be reversed before retention deletes eligible rows. / 0 desactiva. Se puede desarchivar antes de que la conservación borre filas elegibles. | Load current saved/server value; illustrative fixture: 0 | min=0; max=3650 |

**Remove event source / Eliminar fuente de eventos:** Remove its refresh configuration? Imported events, corrections and broadcasts remain. / ¿Eliminar su configuración de actualización? Se conservan eventos, correcciones y emisiones.

Result copy: Source removed; imported events retained. / Fuente eliminada; eventos conservados.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Manage source broadcaster aliases / Gestionar alias de emisoras](workflow-prototype.html?screen=event-mapping).

<a id="connections"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** primary destination. **Canonical editor:** `connections`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Where would you like to watch? / ¿Dónde quieres ver la TV?

[Open composition](workflow-prototype.html?screen=connections) · existing route/context: `proposed orientation layer` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Each destination keeps its own setup and access rules. / Cada destino conserva su configuración y acceso.

**Evidence:** [IntegrationPage.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/IntegrationPage.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Where would you like to watch? / ¿Dónde quieres ver la TV?**

- This browser / Este navegador: Playback setup and current sessions. / Configuración de reproducción y sesiones. [Open related workflow](workflow-prototype.html?screen=browser-player).
- TVs and players / TV y reproductores: Send to a TV, or open VLC and Kodi. / Envía a una TV o abre VLC y Kodi. [Open related workflow](workflow-prototype.html?screen=casting).
- Media servers / Servidores multimedia: Plex, Jellyfin and tuner settings. / Plex, Jellyfin y sintonizador. [Open related workflow](workflow-prototype.html?screen=media-server).
- Playlists / Listas: Export channels with the right address and format. / Exporta canales con dirección y formato adecuados. [Open related workflow](workflow-prototype.html?screen=playlist).
- Notifications / Notificaciones: Choose where useful alerts are sent. / Elige dónde recibir avisos útiles. [Open related workflow](workflow-prototype.html?screen=notifications).

**Contextual exits:** [Address used by other devices / Dirección para otros dispositivos](workflow-prototype.html?screen=public-address).

<a id="browser-player"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** section. **Canonical editor:** `browser-player`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Browser player / Reproductor web

[Open composition](workflow-prototype.html?screen=browser-player) · existing route/context: `/integrations/web-player` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Read capabilities without starting playback. / Consulta capacidades sin iniciar reproducción.

**Evidence:** [WebPlayerSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/WebPlayerSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, unavailable. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unavailable:** This installation cannot start browser playback with the current configuration. Review the missing service or setting below. / Esta instalación no puede iniciar reproducción con la configuración actual. Revisa el servicio o ajuste que falta.
- **partial:** Session query failed. Viewer count is unknown, not zero. / Falló la consulta de sesiones. Cantidad desconocida, no cero.

**Implementation constraint for `unavailable`:** Show the reported missing capability; HTTP media can work without AceStream. / Muestra la capacidad que falta; HTTP puede funcionar sin AceStream.

**Contextual exits:** [Playback setup / Configurar reproducción](workflow-prototype.html?screen=playback-settings); [Current sessions / Sesiones actuales](workflow-prototype.html?screen=player-sessions).

**Read-only context: Synthetic capabilities / Capacidades ficticias**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Player / Reproductor | Available · FFmpeg ready / Disponible · FFmpeg listo |
| Sessions / Sesiones | 1 of 3 / 1 de 3 |
| Route / Ruta | Direct · active sessions keep their original route / Directa · sesiones activas conservan su ruta |

**Playing / En reproducción**

- Northlight HD / Northlight HD: 2 viewers · matching audio/subtitles share a session / 2 espectadores · mismas pistas comparten sesión

**Contextual exits:** [Open Live TV / Abrir TV en directo](workflow-prototype.html?screen=live); [Playback settings / Ajustes de reproducción](workflow-prototype.html?screen=playback-settings); [Capacity and startup budget / Capacidad y tiempo de inicio](workflow-prototype.html?screen=runtime-playback).

**Contextual exits:** [Session ownership / Propiedad de sesiones](workflow-prototype.html?screen=player-sessions).

<a id="public-address"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `public-address`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Address for players / Dirección para reproductores

[Open composition](workflow-prototype.html?screen=public-address) · existing route/context: `/integrations/public-address` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** One saved address, with the correct proxy prefix. / Una dirección guardada, con prefijo de proxy correcto.

**Evidence:** [PublicAddressSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/PublicAddressSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Effective address · synthetic / Dirección efectiva · ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Address / Dirección | https://tv.example.invalid/app / https://tv.example.invalid/app |
| Source / Origen | Saved override / Valor guardado |
| Runtime fallback / Alternativa de ejecución | Empty / Vacío |

### Saved override / Dirección guardada

**Save timing:** explicit action. **Action:** Save address / Guardar dirección. **Boundary:** `configService public-base-url`. Submit this resource only; other sections retain independent state.

**Consequence:** New generated links use this address; copied links are unchanged. / Los enlaces nuevos usan esta dirección; los copiados no cambian.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `address.public_base_url` · url | Player-facing address / Dirección para reproductores<br>HTTP(S), no credentials or fragment. Preserve proxy prefix. Empty removes this override. / HTTP(S), sin credenciales ni fragmento. Conserva prefijo. Vacío elimina este valor. | Load current saved/server value; illustrative fixture: https://tv.example.invalid/app | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Playlist context / Contexto de lista](workflow-prototype.html?screen=playlist); [TV-specific override / Dirección específica para TV](workflow-prototype.html?screen=casting-settings); [Runtime precedence / Prioridad de ejecución](workflow-prototype.html?screen=runtime-network).

<a id="casting"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `casting`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## TV casting / Enviar a TV

[Open composition](workflow-prototype.html?screen=casting) · existing route/context: `/integrations/tv-casting` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Find Google Cast receivers on the permitted home connection. / Busca receptores Google Cast desde la conexión permitida.

**Evidence:** [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx)

**Permission:** cast capabilities / server devices / effective home rule. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, denied. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **empty:** No TVs found. Turn on the TV and enable Cast. Check reachability; current source has no manual Cast-device editor. / No se encontraron TVs. Enciende la TV y activa Cast. Revisa la red; no existe editor manual de receptores Cast.
- **denied:** This connection or account cannot control TVs. Review the access requirements or ask the owner for permission. / Esta conexión o cuenta no puede controlar televisores. Revisa los requisitos o pide permiso al propietario.

**Implementation constraint for `denied`:** This connection or account cannot control server TVs. Show the capability reason; retry is not permission. / Esta conexión o cuenta no puede controlar TVs. Muestra el motivo; reintentar no concede permiso.

**Contextual exits:** [Send to a TV / Enviar a una TV](workflow-prototype.html?screen=casting); [VLC, Kodi and other players / VLC, Kodi y otros reproductores](workflow-prototype.html?screen=remote-player).

**Read-only context: Synthetic access / Acceso ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Connection / Conexión | Verified private connection / Conexión privada verificada |
| Permission / Permiso | cast_server / cast_server |
| Discovery / Búsqueda | Bounded multicast / private server IPv4 /24 / Multidifusión limitada / IPv4 privada del servidor /24 |

**Find TVs / Buscar televisores:** Search the bounded home network? Up to 20 seconds. / ¿Buscar en la red doméstica limitada? Hasta 20 segundos.

Result copy: Fixture discovery found Living room DEMO. / La búsqueda ficticia encontró Living room DEMO.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Receivers / Receptores**

- Living room DEMO / Living room DEMO: Synthetic receiver / Receptor ficticio [Open related workflow](workflow-prototype.html?screen=casting-control).

**Contextual exits:** [Casting settings / Ajustes de TV](workflow-prototype.html?screen=casting-settings); [Public HTTPS at home / HTTPS público desde casa](workflow-prototype.html?screen=casting-trust); [Choose a channel / Elegir canal](workflow-prototype.html?screen=live).

<a id="casting-settings"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `casting-settings`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Casting settings / Ajustes de TV

[Open composition](workflow-prototype.html?screen=casting-settings) · existing route/context: `/integrations/tv-casting` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Original video is the default. / El vídeo original es la opción inicial.

**Evidence:** [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx)

**Permission:** administrator / recognized open-mode configuration capability. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Video and connection / Vídeo y conexión

**Save timing:** explicit action. **Action:** Save casting settings / Guardar ajustes de TV. **Boundary:** `castService.saveSettings`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved independently of IPTV and proxy trust. / Guardado independientemente de IPTV y confianza de proxy.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `cast.compatibility_conversion` · checkbox | Offer H.264 conversion / Ofrecer conversión H.264<br>Off; at most one 720p/30 fps stream. CPU conversion yields to recordings. / Desactivada; máximo una emisión 720p/30 fps. Cede recursos a grabaciones. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `cast.cast_media_url` · text | Application address for TVs / Dirección de app para TVs<br>Optional, max 2048; blank uses browser address. Preserve proxy prefix. / Opcional, máximo 2048; vacío usa dirección del navegador. Conserva prefijo. | Load current saved/server value; illustrative fixture:  | maxlength=2048; Advanced disclosure |
| `cast.home_networks` · text | Allowed home visitor networks / Redes domésticas de visitantes<br>Max 16 CIDRs; visitors, not TV IPs. Blank preserves automatic private recognition. / Máximo 16 CIDR; visitantes, no IPs de TVs. Vacío conserva reconocimiento privado. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `cast.remote_casting` · checkbox | Allow permitted accounts away from home / Permitir cuentas autorizadas fuera de casa<br>Requires accounts and explicit opt-in. Never enables public HTTP accounts. / Requiere cuentas y activación explícita. Nunca permite cuentas por HTTP público. | Load current saved/server value; illustrative fixture: False | Advanced disclosure |

<a id="casting-trust"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `casting-trust`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Public HTTPS at home / HTTPS público desde casa

[Open composition](workflow-prototype.html?screen=casting-trust) · existing route/context: `/integrations/tv-casting` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Review the scope before trusting this connection. / Revisa el ámbito antes de confiar en la conexión.

**Evidence:** [TvCasting.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/integrations/TvCasting.tsx)

**Permission:** administrator / public HTTPS / home not yet verified. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Shared internet connections share this trust. Repeat if your public address changes. Never permits accounts on public HTTP. / Las conexiones compartidas comparten confianza. Repite si cambia la dirección. Nunca permite cuentas por HTTP público.

### Home confirmation / Confirmación doméstica

**Save timing:** explicit action. **Action:** Trust this connection / Confiar en esta conexión. **Boundary:** `castService.trustHome`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved for Cast only. / Guardado solo para Cast.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `cast.trust_home` · checkbox | I am on my home network now / Estoy en mi red doméstica<br>Admin only; not needed for a verified private-IP connection. / Solo administrador; innecesario en conexión privada verificada. | Load current saved/server value; illustrative fixture: False | required=True |

<a id="casting-control"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `casting-control`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Living room DEMO / Living room DEMO

[Open composition](workflow-prototype.html?screen=casting-control) · existing route/context: `player casting options` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Control only the exact media owned by this app. / Controla solo el contenido exacto de esta app.

**Evidence:** [CastControls.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/CastControls.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, ownership-lost, recording-priority. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **ownership-lost:** The TV is now playing different media. Controls for your previous playback are unavailable. / La TV está reproduciendo otro contenido. Los controles de tu reproducción anterior no están disponibles.
- **recording-priority:** Video conversion is waiting while a recording uses the resources. Try the original video if your TV supports it. / La conversión espera mientras una grabación usa los recursos. Prueba el vídeo original si tu TV lo admite.

**Implementation constraint for `ownership-lost`:** TV now plays other media. Stop/cleanup must leave it alone. / La TV reproduce otro contenido. Detener/limpiar debe respetarlo.

**Implementation constraint for `recording-priority`:** Conversion yielded to recording. Show whether original playback is still available. / La conversión cedió a grabación. Indica si el original sigue disponible.

**Read-only context: Synthetic owned media / Contenido propio ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Channel / Canal | Northlight / Northlight |
| Mode / Modo | Original video / Vídeo original |
| Ownership / Propiedad | Exact media ID verified / ID exacto verificado |

### Playback options / Opciones

**Save timing:** explicit action. **Action:** Apply example control / Aplicar control ficticio. **Boundary:** `castService.command`. View/preview only; no persistent data mutation.

**Consequence:** Owned command acknowledged in fixture. / Orden propia confirmada en ejemplo.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `cast.compatibility` · checkbox | Compatible video for this cast / Vídeo compatible para este envío<br>Only if offered and capacity permits. / Solo si está disponible y hay capacidad. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `cast.volume` · range | Volume (%) / Volumen (%)<br>0–100%. Changes apply immediately to the media you are controlling. / 0–100 %. Los cambios se aplican al momento al contenido que controlas. | Load current saved/server value; illustrative fixture: 50 | min=0; max=100; Adapter/contract note: Display 0–100; API 0–1. Immediate owned-session command. / Muestra 0–100; API 0–1. Orden inmediata de sesión propia. |

**Stop this cast / Detener envío:** Stop only if this exact owned media is still playing. Never stop another app’s replacement. / Detén solo si sigue el contenido propio exacto. Nunca detengas su sustitución por otra app.

Result copy: Owned cast stopped. Browser ownership remains separate. / Envío propio detenido. Navegador independiente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Replace receiver media / Sustituir contenido del receptor:** Explicitly replace the receiver’s current media with Northlight? / ¿Sustituir expresamente el contenido actual por Northlight?

Result copy: Replacement requested with replace=true. / Sustitución solicitada con replace=true.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="remote-player"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `remote-player`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Set up VLC or Kodi / Configurar VLC o Kodi

[Open composition](workflow-prototype.html?screen=remote-player) · existing route/context: `/integrations/remote-players` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Saving a player does not start playback. / Guardar un reproductor no inicia reproducción.

**Evidence:** [RemotePlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/RemotePlayerDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Player connection / Conexión

**Save timing:** explicit action. **Action:** Save player / Guardar reproductor. **Boundary:** `remotePlayerService create / update`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved. Probe and playback remain explicit actions. / Guardado. Consulta y reproducción siguen siendo explícitas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `remote.name` · text | Player name / Nombre del reproductor<br>1–255 characters; duplicate names rejected. / 1–255 caracteres; duplicados rechazados. | Load current saved/server value; illustrative fixture: Study DEMO | required=True; maxlength=255 |
| `remote.kind` · select | Player / Reproductor<br>Each driver uses its own credentials. / Cada controlador usa sus credenciales. | Load current saved/server value; illustrative fixture: vlc | vlc → VLC desktop / VLC escritorio; vlc_android → VLC Android 3.6+ / VLC Android 3.6+; kodi → Kodi / Kodi |
| `remote.host` · text | Host / Host<br>Private hostname or IP, no scheme. Changing host/port clears authentication. / Nombre o IP privada, sin protocolo. Cambiar host/puerto borra autenticación. | Load current saved/server value; illustrative fixture: player.example.invalid | required=True |
| `remote.port` · number | Port / Puerto<br>1–65535; desktop 8080, Android 8443. / 1–65535; escritorio 8080, Android 8443. | Load current saved/server value; illustrative fixture: 8080 | min=1; max=65535 |
| `remote.username` · text | Kodi username / Usuario Kodi<br>Kodi only; default kodi. / Solo Kodi; por defecto kodi. | Load current saved/server value; illustrative fixture: kodi | Advanced disclosure |
| `remote.password` · password | Player password / Contraseña del reproductor<br>Blank keeps a saved password only at an unchanged address. / Vacío conserva contraseña solo si no cambió la dirección. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | No additional prototype constraint; preserve current source validation. |
| `remote.base_url_id` · select | Stream link format / Formato de enlace<br>Default relay. Acexy always uses relay; direct honors supported formats. / Por defecto app. Acexy siempre usa app; directo respeta formatos. | Load current saved/server value; illustrative fixture:  |  → Server relay / A través de la app; demo → Demo format / Formato de ejemplo |

**Test connection / Probar conexión:** Probe without starting media? / ¿Consultar sin iniciar contenido?

Result copy: Fixture reachable; authentication and control capabilities are separate. / Ejemplo accesible; autenticación y capacidades independientes.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [VLC Android pairing / Vincular VLC Android](workflow-prototype.html?screen=remote-android); [Find players / Buscar reproductores](workflow-prototype.html?screen=remote-discovery); [Playback and controls / Reproducción y controles](workflow-prototype.html?screen=remote-control).

<a id="remote-android"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `remote-android`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Pair VLC Android / Vincular VLC Android

[Open composition](workflow-prototype.html?screen=remote-android) · existing route/context: `/integrations/remote-players` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Enable Remote access and playback control in VLC; verify its certificate. / Activa acceso remoto y control en VLC; verifica su certificado.

**Evidence:** [RemotePlayerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/RemotePlayerDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, expired, changed-host. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **expired:** Code expired. Request a new challenge; never silently reuse it. / Código caducado. Solicita otro desafío; nunca reutilices en silencio.
- **changed-host:** Address changed. Clear the challenge and verify the new certificate. / Cambió dirección. Borra desafío y verifica nuevo certificado.

**Read-only context: Synthetic device check / Comprobación ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Host / Host | android.example.invalid:8443 / android.example.invalid:8443 |
| Certificate fingerprint / Huella | DEMO — NOT A DEVICE / DEMO — NOT A DEVICE |
| Code validity / Validez | 60 seconds; request another if expired / 60 segundos; solicita otro si caduca |

### Device code / Código del dispositivo

**Save timing:** explicit action. **Action:** Pair Android / Vincular Android. **Boundary:** `remotePlayerService.finishAndroidPairing`. Submit this resource only; other sections retain independent state.

**Consequence:** Paired; still save the player to retain the connection. / Vinculado; guarda el reproductor para conservar conexión.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `android.code` · text | Six-digit code / Código de seis cifras<br>From VLC Android; not a browser-pairing requirement for accounts or Cast. / De VLC Android; no es requisito de vinculación de navegador para cuentas o Cast. | Load current saved/server value; illustrative fixture:  | required=True; maxlength=6; pattern=[0-9]{6} |

**Contextual exits:** [Save paired player / Guardar reproductor](workflow-prototype.html?screen=remote-player).

<a id="remote-discovery"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `remote-discovery`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Find remote players / Buscar reproductores remotos

[Open composition](workflow-prototype.html?screen=remote-discovery) · existing route/context: `/integrations/remote-players` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Bounded private scan; review before saving. / Búsqueda privada limitada; revisa antes de guardar.

**Evidence:** [FindPlayersDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/FindPlayersDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Scan scope / Ámbito

**Save timing:** explicit action. **Action:** Find players / Buscar reproductores. **Boundary:** `remotePlayerService.scan`. View/preview only; no persistent data mutation.

**Consequence:** Suggestions only. Review and save each destination. / Solo sugerencias. Revisa y guarda cada destino.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `scan.cidr` · text | Private network (CIDR) / Red privada (CIDR)<br>Max 1024 addresses; default guessed /24. No public scan. / Máximo 1024 direcciones; sugiere /24. Sin búsqueda pública. | Load current saved/server value; illustrative fixture: 192.168.50.0/24 | required=True |
| `scan.ports` · text | Ports / Puertos<br>Up to 8, each 1–65535; default 8080. / Hasta 8, cada uno 1–65535; por defecto 8080. | Load current saved/server value; illustrative fixture: 8080 | No additional prototype constraint; preserve current source validation. |
| `scan.timeout_ms` · number | Timeout per attempt (ms) / Espera por intento (ms)<br>Default 400; 50–5000. / Por defecto 400; 50–5000. | Load current saved/server value; illustrative fixture: 400 | min=50; max=5000 |

**Synthetic result / Resultado ficticio**

- Study DEMO / Study DEMO: Possible VLC; inspect credentials / Posible VLC; revisa credenciales [Open related workflow](workflow-prototype.html?screen=remote-player).

<a id="remote-control"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `remote-control`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Send to a player / Enviar a reproductor

[Open composition](workflow-prototype.html?screen=remote-control) · existing route/context: `PlayOnMenu` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Local app handoff and remote control are separate. / Apertura local y control remoto son independientes.

**Evidence:** [PlayOnMenu.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/PlayOnMenu.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, denied, handoff. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **denied:** Requires an account and explicit opt-in. Public viewing and Cast trust do not grant remote control. / Requiere cuenta y activación expresa. Acceso público y confianza Cast no conceden control remoto.
- **handoff:** The player was asked to open. If it did not open, copy the link and open it in your player. / Se pidió abrir el reproductor. Si no se abrió, copia el enlace y ábrelo en tu reproductor.

**Implementation constraint for `handoff`:** App opening requested; do not claim playback started. Offer copy if the app did not open. / Apertura solicitada; no afirmes reproducción. Ofrece copiar si no se abrió.

**Destinations / Destinos**

- Open local VLC / Abrir VLC local: Browser may ask to open an installed app / El navegador puede pedir abrir una app
- Study DEMO / Study DEMO: Account and explicit player opt-in required / Requiere cuenta y activación expresa [Open related workflow](workflow-prototype.html?screen=remote-player).

### Control Study DEMO / Controlar Study DEMO

**Save timing:** explicit action. **Action:** Send command / Enviar orden. **Boundary:** `remotePlayerService.command`. View/preview only; no persistent data mutation.

**Consequence:** Command acknowledged; receiving app owns playback state. / Orden confirmada; la app receptora informa del estado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `remote.command` · select | Command / Orden<br>Android supports pause/resume/volume; stop on the device. / Android admite pausa/reanudación/volumen; detén en el dispositivo. | Load current saved/server value; illustrative fixture: pause | pause → Pause / Pausar; resume → Resume / Reanudar; volume → Volume / Volumen |
| `remote.volume` · number | Volume (%) / Volumen (%)<br>0–200%, where supported by this player. Changes apply immediately. / 0–200 %, si el reproductor lo permite. Los cambios se aplican al momento. | Load current saved/server value; illustrative fixture: 50 | min=0; max=200; Adapter/contract note: API 0–200; respect actual driver capability. / API 0–200; respeta capacidades del controlador. |

<a id="media-server"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `media-server`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Connect a media server / Conectar servidor multimedia

[Open composition](workflow-prototype.html?screen=media-server) · existing route/context: `/integrations/media-servers` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Save, test and connect have separate outcomes. / Guardar, probar y conectar tienen resultados separados.

**Evidence:** [MediaServerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/MediaServerDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Plex / Jellyfin / Plex / Jellyfin

**Save timing:** explicit action. **Action:** Save server / Guardar servidor. **Boundary:** `mediaServerService create / update`. Submit this resource only; other sections retain independent state.

**Consequence:** Definition saved; no connection created yet. / Definición guardada; sin conexión creada.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `media.kind` · select | Media server / Servidor multimedia<br>Kind is locked when editing. / Tipo bloqueado al editar. | Load current saved/server value; illustrative fixture: jellyfin | jellyfin → Jellyfin / Jellyfin; plex → Plex / Plex |
| `media.name` · text | Name / Nombre<br>1–255; duplicate names rejected. / 1–255; duplicados rechazados. | Load current saved/server value; illustrative fixture: Home cinema DEMO | required=True |
| `media.base_url` · url | Address / Dirección<br>As reached from scraper; max 1024 characters. / Accesible desde scraper; máximo 1024 caracteres. | Load current saved/server value; illustrative fixture: https://media.example.invalid | required=True |
| `media.api_key` · password | API key or owner token / Clave API o token<br>Jellyfin needs admin key; Plex token optional for auto refresh. Blank keeps saved secret. / Jellyfin necesita clave; token Plex opcional para actualizar. Vacío conserva secreto. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | No additional prototype constraint; preserve current source validation. |
| `media.tuner_mode` · select | How channels reach Jellyfin / Cómo llegan canales a Jellyfin<br>HDHomeRun preserves identity. Changing M3U address/format recreates channels and loses favorites. / HDHomeRun conserva identidad. Cambiar dirección/formato M3U recrea canales y pierde favoritos. | Load current saved/server value; illustrative fixture: hdhomerun | hdhomerun → HDHomeRun tuner / Sintonizador HDHomeRun; m3u → M3U + XMLTV / M3U + XMLTV |
| `media.auto_refresh` · checkbox | Refresh guide on channel changes / Actualizar guía al cambiar canales<br>On by default; runtime debounce still applies. / Activado por defecto; respeta intervalo mínimo. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `media.enabled` · checkbox | Enable integration / Activar integración<br>On by default; disabled integrations do not receive automatic refresh requests. / Activada por defecto; las desactivadas no reciben actualizaciones automáticas. | Repository default: True | No additional prototype constraint; preserve current source validation. |

**Test connection / Probar conexión:** Probe address and credentials without connecting tuner? / ¿Probar dirección y credenciales sin conectar sintonizador?

Result copy: Fixture probe succeeded. / Consulta ficticia correcta.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Connect tuner / Conectar sintonizador:** Configure this app’s tuner and guide in the server? / ¿Configurar sintonizador y guía en el servidor?

Result copy: Connected in fixture; guide refresh remains pending. / Conectado en ejemplo; guía pendiente.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Disconnect tuner / Desconectar sintonizador:** Remove app-managed connection; keep saved server definition? / ¿Quitar conexión gestionada y conservar definición?

Result copy: Disconnected; definition retained. / Desconectado; definición conservada.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Tuner limits and output / Límites y salida](workflow-prototype.html?screen=tuner).

<a id="tuner"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `tuner`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Tuner settings / Ajustes de sintonizador

[Open composition](workflow-prototype.html?screen=tuner) · existing route/context: `/integrations/media-servers` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Choose what your media server receives and how long it waits for a stream. / Elige qué recibe tu servidor multimedia y cuánto espera una emisión.

**Evidence:** [MediaServersSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/MediaServersSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Capacity and compatibility / Capacidad y compatibilidad

**Save timing:** explicit action. **Action:** Save tuner settings / Guardar ajustes. **Boundary:** `tunerService.updateSettings`. Submit this resource only; other sections retain independent state.

**Consequence:** New connections use these settings; existing ownership remains. / Nuevas conexiones usan ajustes; se conserva propiedad existente.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `tuner.friendly_name` · text | Tuner name / Nombre del sintonizador<br>Shown in Plex/Jellyfin; max 255. / Visible en Plex/Jellyfin; máximo 255. | Load current saved/server value; illustrative fixture: AceStream Scraper | No additional prototype constraint; preserve current source validation. |
| `tuner.tuner_count` · number | Streams at once / Emisiones simultáneas<br>1–16; load saved value, example 2 is not a new default. / 1–16; carga valor guardado, ejemplo 2 no es un defecto nuevo. | Load current saved/server value; illustrative fixture: 2 | min=1; max=16 |
| `tuner.max_channels` · number | Most channels to publish / Máximo de canales<br>1–1000; show omitted count. Plex constrained near 450–480. / 1–1000; muestra omitidos. Plex limitado cerca de 450–480. | Load current saved/server value; illustrative fixture: 400 | min=1; max=1000 |
| `tuner.source_start_seconds` · number | Seconds per source / Segundos por emisión<br>Default 15; 5–180; lock waiting consumes this budget. / Por defecto 15; 5–180; esperar bloqueos consume tiempo. | Load current saved/server value; illustrative fixture: 15 | min=5; max=180 |
| `tuner.startup_budget_seconds` · number | Total startup seconds / Segundos totales de inicio<br>Default 45; 5–180. Below the player timeout. / Por defecto 45; 5–180. Menor que la espera del reproductor. | Load current saved/server value; illustrative fixture: 45 | min=5; max=180 |
| `tuner.only_online` · checkbox | Publish online only / Publicar solo con señal<br>Eligibility rules apply; deletes nothing. / Aplica elegibilidad; no elimina. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `tuner.hide_unusable` · checkbox | Hide stale or repeatedly failing sources / Ocultar emisiones antiguas o con fallos repetidos<br>Off; lineup/M3U hiding only. Playlist URL may override. / Desactivado; solo oculta en listas. URL puede sobrescribir. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `tuner.plex_compatible_audio` · checkbox | Plex Desktop compatible audio / Audio compatible Plex Desktop<br>Opt-in stereo AAC/LATM; video copy unless recovery enabled. / AAC/LATM estéreo opcional; copia vídeo salvo recuperación. | Load current saved/server value; illustrative fixture: False | Advanced disclosure |
| `tuner.experimental_transcoding` · checkbox | Experimental recovery / Recuperación experimental<br>Off; CPU-intensive. Normal mode requires client reconnection after failure. / Desactivada; usa CPU. Modo normal requiere reconectar tras fallo. | Load current saved/server value; illustrative fixture: False | Advanced disclosure |

**Read-only context: Synthetic publication / Publicación ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Published / omitted / Publicados / omitidos | 3 / 0 / 3 / 0 |
| Renumbered / Renumerados | None / Ninguno |
| Client allowed / Cliente permitido | Separate tuner network policy / Política de red de sintonizador independiente |

**Contextual exits:** [Tuner networks / Redes de sintonizador](workflow-prototype.html?screen=network); [Playlist overrides / Opciones de lista](workflow-prototype.html?screen=playlist).

<a id="telegram-auth"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `telegram-auth`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Authorize Telegram sources / Autorizar fuentes Telegram

[Open composition](workflow-prototype.html?screen=telegram-auth) · existing route/context: `/integrations/telegram` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** This is a Telegram user session, separate from notification webhooks. / Es una sesión de usuario Telegram, independiente de notificaciones.

**Evidence:** [TelegramSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSection.tsx)

**Permission:** Telegram admin header + HTTPS/localhost + deployment readiness. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, unavailable, flood. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **unavailable:** Session key or encrypted storage is unavailable. Owner must fix deployment; do not ask for the API hash repeatedly. / No hay clave o almacén cifrado. El propietario debe corregir despliegue; no pidas hash repetidamente.
- **flood:** Telegram has temporarily limited sign-in attempts. Wait until the retry time shown below. / Telegram ha limitado temporalmente los intentos de acceso. Espera hasta la hora indicada.

**Implementation constraint for `flood`:** Telegram requires a wait. Show the server-provided retry time; keep source progress and prevent repeated login attempts. / Telegram exige esperar. Muestra plazo del servidor; conserva progreso y evita intentos repetidos.

**Explanation:** Requires HTTPS or localhost and the dedicated Telegram admin header token. Private-IP HTTP support for ordinary accounts does not waive this rule. / Requiere HTTPS o localhost y token administrativo de Telegram en cabecera. El HTTP privado de cuentas normales no exime esta regla.

### Private authorization / Autorización privada

**Save timing:** explicit action. **Action:** Request login code / Solicitar código. **Boundary:** `telegramService login`. Submit this resource only; other sections retain independent state.

**Consequence:** Login code requested. Continue with the code step; no source import starts. / Código solicitado. Continúa con el código; no se importa.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `telegram.admin_token` · password | Telegram admin token / Token administrativo Telegram<br>Separate deployment credential; never include in URLs or captures. / Credencial de despliegue separada; nunca en URLs o capturas. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True |
| `telegram.api_id` · number | Telegram API ID / ID API Telegram<br>Integer 1–2147483647. Deployment must provide encrypted-session storage and key. / Entero 1–2147483647. Despliegue debe aportar almacén cifrado y clave. | Load current saved/server value; illustrative fixture:  | required=True; min=1; max=2147483647 |
| `telegram.api_hash` · password | Telegram API hash / Hash API Telegram<br>Exactly 32 characters; never redisplay a saved value. / Exactamente 32 caracteres; no se vuelve a mostrar. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=32; minlength=32 |
| `telegram.phone` · tel | Phone with country code / Teléfono con prefijo<br>5–32 characters. Keep private. / 5–32 caracteres. Privado. | Load current saved/server value; illustrative fixture:  | required=True; maxlength=32; minlength=5 |

**Contextual exits:** [Source editor after authorization / Editor tras autorización](workflow-prototype.html?screen=telegram-source).

<a id="telegram-code"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `telegram-code`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Complete Telegram sign-in / Completar inicio Telegram

[Open composition](workflow-prototype.html?screen=telegram-code) · existing route/context: `/integrations/telegram` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Codes and passwords are never saved in logs or previews. / Códigos y contraseñas nunca van en registros o vistas previas.

**Evidence:** [TelegramSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSection.tsx)

**Permission:** same Telegram transport/header gate. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Login code / Código de acceso

**Save timing:** explicit action. **Action:** Verify code / Verificar código. **Boundary:** `telegramService code`. Submit this resource only; other sections retain independent state.

**Consequence:** Code verified. Two-step verification may still be required. / Código verificado. Puede faltar verificación en dos pasos.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `telegram.code` · text | Telegram login code / Código Telegram<br>1–16 characters; received through Telegram’s login flow. / 1–16 caracteres; recibido en el flujo de acceso Telegram. | Load current saved/server value; illustrative fixture:  | required=True; maxlength=16 |

### Two-step verification when required / Dos pasos cuando se requiera

**Save timing:** explicit action. **Action:** Complete authorization / Completar autorización. **Boundary:** `telegramService password`. Submit this resource only; other sections retain independent state.

**Consequence:** Encrypted user session ready. Credentials cleared from the form. / Sesión cifrada lista. Credenciales borradas del formulario.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `telegram.password` · password | Telegram two-step password / Contraseña de dos pasos Telegram<br>Only shown when required by the authorization response; up to 256 characters. / Solo si la respuesta la requiere; hasta 256 caracteres. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; maxlength=256 |

<a id="telegram-source"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `telegram-source`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Telegram source / Fuente Telegram

[Open composition](workflow-prototype.html?screen=telegram-source) · existing route/context: `/integrations/telegram` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Start with new messages; reading history is an explicit choice. / Empieza con mensajes nuevos; leer historial es una elección explícita.

**Evidence:** [TelegramSourceEditor.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/integrations/TelegramSourceEditor.tsx)

**Permission:** Telegram admin header; HTTPS/localhost; joined membership. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Chat and extraction / Chat y extracción

**Save timing:** explicit action. **Action:** Save Telegram source / Guardar fuente Telegram. **Boundary:** `telegramService source`. Submit this resource only; other sections retain independent state.

**Consequence:** Source saved; cursor and imports commit together during ingestion. No snapshot deletion on missing messages. / Fuente guardada; cursor e importaciones se guardan juntos. Mensajes ausentes no borran canales.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `telegram_source.name` · text | Source name / Nombre de fuente<br>1–100 characters. / 1–100 caracteres. | Load current saved/server value; illustrative fixture: Demo joined chat | required=True; maxlength=100 |
| `telegram_source.chat_id` · select | Joined chat / Chat al que perteneces<br>Choose a joined chat; stable numeric ID is retained, not translated label. / Elige un chat al que perteneces; conserva ID numérico, no etiqueta traducida. | Load current saved/server value; illustrative fixture: -1000000001 | -1000000001 → Demo joined chat / Demo joined chat |
| `telegram_source.topic_id` · number | Topic / Tema<br>Optional positive topic ID; only supported chat topics are offered. / ID positivo opcional; solo se ofrecen temas compatibles. | Load current saved/server value; illustrative fixture:  | min=1 |
| `telegram_source.username` · text | Resolve Telegram username / Resolver usuario Telegram<br>Explicit lookup resolves stable sender identity; not a replacement for membership checks. / Consulta expresa resuelve identidad; no sustituye comprobación de pertenencia. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `telegram_source.sender_ids` · text | Allowed sender IDs / IDs de remitentes permitidos<br>Comma-separated stable IDs, at most 100. Empty accepts all senders. / IDs estables separados por comas, máximo 100. Vacío acepta todos. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `telegram_source.include_forwards` · checkbox | Include forwarded messages / Incluir reenviados<br>On by default; sender rule chooses which identity is checked. / Activado; la regla elige qué identidad se comprueba. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `telegram_source.sender_rule` · select | Sender identity for forwards / Identidad en reenviados<br>Posting identity by default; preserve source options. / Identidad que publica por defecto; conserva opciones. | Load current saved/server value; illustrative fixture: posting | Advanced disclosure; posting → Posting sender / Quien publica; original → Original sender / Remitente original |
| `telegram_source.filter_mode` · select | Message filter mode / Modo de filtro<br>Keyword or bounded regex. Does not authorize an unbounded extraction worker. / Palabras o regex limitado. No permite trabajo sin límites. | Load current saved/server value; illustrative fixture: keyword | keyword → Keyword / Palabras; regex → Regex / Regex |
| `telegram_source.include` · text | Must include / Debe incluir<br>Optional; up to 512 characters. / Opcional; hasta 512 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=512 |
| `telegram_source.exclude` · text | Must exclude / Debe excluir<br>Optional; up to 512 characters. / Opcional; hasta 512 caracteres. | Load current saved/server value; illustrative fixture:  | maxlength=512 |
| `telegram_source.bare_ids` · checkbox | Recognize bare IDs in name/ID pairs / Reconocer IDs en parejas nombre/ID<br>True for Telegram; distinct from ordinary-source default. / Activado en Telegram; distinto del defecto de fuentes comunes. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |
| `telegram_source.history_count` · number | Initial history count / Cantidad inicial de historial<br>New source only. Default 0, at most 1000; pause retains cursor. / Solo fuente nueva. Por defecto 0, máximo 1000; pausa conserva cursor. | Load current saved/server value; illustrative fixture: 0 | min=0; max=1000 |
| `telegram_source.history_since` · datetime-local | Ignore history before / Ignorar historial anterior a<br>Optional timezone-aware cutoff; no automatic historical backfill. / Fecha opcional con zona; sin recuperación histórica automática. | Load current saved/server value; illustrative fixture:  | Advanced disclosure |
| `telegram_source.enabled` · checkbox | Source enabled / Fuente activada<br>Pause retains progress and imported channels. / Pausar conserva progreso y canales importados. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

**Preview 10 messages / Ver 10 mensajes:** Bounded preview of 1–30 messages, no import? / ¿Consulta limitada de 1–30 mensajes sin importar?

Result copy: Example: 2 extracted, 1 excluded; raw private message text is not part of public diagnostics. / Ejemplo: 2 extraídos, 1 excluido; mensajes privados no van en diagnóstico público.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Optional shared recipe editor / Editor de receta compartido](workflow-prototype.html?screen=helper-installed).

<a id="notifications"></a>

**Simplified location:** Where would you like to watch? → Where would you like to watch?. **Composition:** contextual editor or detail. **Canonical editor:** `notifications`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Notifications / Notificaciones

[Open composition](workflow-prototype.html?screen=notifications) · existing route/context: `/settings?tab=automation` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Save the webhook separately from sending a test. / Guarda el webhook por separado de enviar una prueba.

**Evidence:** [NotificationsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/NotificationsSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, masked-invalid. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **masked-invalid:** The saved address cannot be used safely. Enter a replacement address to enable notifications. / La dirección guardada no se puede usar de forma segura. Introduce otra para activar avisos.

**Implementation constraint for `masked-invalid`:** Saved URL cannot be safely displayed or validated. Keep it masked; replace explicitly, never submit the mask as a URL. / La URL guardada no se puede mostrar o validar. Mantén máscara; sustituye expresamente, nunca envíes máscara como URL.

### Notification destination / Destino de notificación

**Save timing:** explicit action. **Action:** Save webhook / Guardar webhook. **Boundary:** `configService notification-webhook`. Submit this resource only; other sections retain independent state.

**Consequence:** Destination saved only; test sending remains explicit. / Solo destino guardado; la prueba sigue siendo explícita.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `notifications.url` · url | Webhook URL / URL de webhook<br>HTTP(S), valid host/port, no whitespace or fragment. Empty turns notifications off. Treat embedded credentials as private. / HTTP(S), host/puerto válidos, sin espacios ni fragmento. Vacío desactiva. Trata credenciales incrustadas como privadas. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Send a test notification / Enviar notificación de prueba:** Send one real message to the saved destination in the implemented app? This prototype sends nothing. / ¿Enviar un mensaje real al destino guardado en la app implementada? Este prototipo no envía nada.

Result copy: Synthetic test acknowledged; show delivery failure separately from a successful settings save. / Prueba ficticia confirmada; separa fallo de entrega de guardado correcto.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Telegram ingestion is separate / Importación Telegram independiente](workflow-prototype.html?screen=telegram-auth).

<a id="warp"></a>

**Simplified location:** System status → WARP. **Composition:** section. **Canonical editor:** `warp`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## WARP / WARP

[Open composition](workflow-prototype.html?screen=warp) · existing route/context: `/warp` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Optional routing; a failed direct lookup does not enable it automatically. / Ruta opcional; un fallo directo no la activa automáticamente.

**Evidence:** [WARP.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/WARP.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Synthetic status / Estado ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Connection / Conexión | Disconnected by choice / Desconectado por elección |
| Mode / Modo | warp / warp |
| Startup / Inicio | Not configured to connect / Sin conexión automática |

### Routing mode / Modo de ruta

**Save timing:** explicit action. **Action:** Apply mode / Aplicar modo. **Boundary:** `warpService.setMode`. Submit this resource only; other sections retain independent state.

**Consequence:** Mode command accepted; read current mode again. Connection is a separate command. / Modo solicitado; lee el modo actual. Conectar es una orden separada.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `warp.mode` · select | Mode / Modo<br>Apply current supported CLI mode; connected status must come from JSON status. / Aplica modo CLI admitido; estado conectado debe venir de JSON. | Load current saved/server value; illustrative fixture: warp | warp → WARP with standard DNS / WARP con DNS estándar; warp+doh → WARP + DNS over HTTPS / WARP + DNS sobre HTTPS; warp+dot → WARP + DNS over TLS / WARP + DNS sobre TLS; doh → DNS over HTTPS only / Solo DNS sobre HTTPS; tunnel_only → Tunnel; keep current DNS / Túnel; conservar DNS actual; dot → DNS over TLS only / Solo DNS sobre TLS; proxy → SOCKS5 proxy only / Solo proxy SOCKS5 |

### Optional WARP licence / Licencia WARP opcional

**Save timing:** explicit action. **Action:** Register licence / Registrar licencia. **Boundary:** `warpService.registerLicense`. Submit this resource only; other sections retain independent state.

**Consequence:** Registration only. Do not change routing mode or reveal the submitted key. / Solo registro. No cambia modo ni muestra clave enviada.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `warp.license_key` · password | License key / Clave de licencia<br>Optional license action, minimum 8 characters; never redisplay private value. / Acción opcional, mínimo 8 caracteres; no muestres el valor privado. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | required=True; minlength=8 |

**Connect WARP / Conectar WARP:** Connect using the selected mode? A successful CLI call alone is not connected status. / ¿Conectar con el modo elegido? Éxito CLI no significa conectado.

Result copy: Connection requested; wait for JSON Connected. / Conexión solicitada; espera Connected en JSON.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Disconnect WARP / Desconectar WARP:** Disconnect optional routing? Existing traffic may be interrupted. / ¿Desconectar ruta opcional? Puede interrumpir tráfico.

Result copy: Disconnection requested; confirm observed status. / Desconexión solicitada; confirma estado observado.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Excluded hosts / Hosts excluidos](workflow-prototype.html?screen=warp-exclusions); [Saved startup behavior / Inicio guardado](workflow-prototype.html?screen=warp-startup).

<a id="warp-exclusions"></a>

**Simplified location:** System status → WARP. **Composition:** contextual editor or detail. **Canonical editor:** `warp-exclusions`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## WARP excluded hosts / Hosts excluidos de WARP

[Open composition](workflow-prototype.html?screen=warp-exclusions) · existing route/context: `/warp` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Saved desired hosts and the active CLI list can differ. / Los hosts deseados guardados pueden diferir de la lista activa.

**Evidence:** [WarpExclusionsSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/WarpExclusionsSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **partial:** The host list is saved, but some changes are not active yet. Review the pending hosts and retry applying them. / La lista está guardada, pero faltan cambios por aplicar. Revisa los hosts pendientes y reintenta.
- **conflict:** A newer exclusion revision exists. Reload desired and active lists before saving. / Existe revisión nueva. Recarga listas deseada y activa antes de guardar.

**Implementation constraint for `partial`:** Desired hosts saved, but active exclusions differ. Retry apply; do not claim fully applied. / Hosts deseados guardados, pero lista activa distinta. Reintenta aplicar; no afirmes aplicación completa.

### Desired exclusions / Exclusiones deseadas

**Save timing:** explicit action. **Action:** Save and apply exclusions / Guardar y aplicar exclusiones. **Boundary:** `warpService exclusions`. Submit this resource only; other sections retain independent state.

**Consequence:** Save the host list, then check whether WARP has applied every change. Show any hosts still waiting. / Guarda lista y comprueba si WARP aplicó cada cambio. Muestra hosts pendientes.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `warp.hosts` · textarea | Hosts outside WARP / Hosts fuera de WARP<br>At most 64 validated hosts; one per line. Empty saved list overrides environment defaults. / Máximo 64 hosts válidos; uno por línea. Lista vacía guardada sobrescribe entorno. | Load current saved/server value; illustrative fixture: example.invalid<br>media.example.invalid | No additional prototype constraint; preserve current source validation. |

**Read-only context: Saved / applied example / Ejemplo guardado / aplicado**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | 2 hosts / 2 hosts |
| Active / Activo | 1 host / 1 host |
| Result / Resultado | Partially applied; removal pending / Aplicación parcial; retirada pendiente |

<a id="warp-startup"></a>

**Simplified location:** System status → WARP. **Composition:** contextual editor or detail. **Canonical editor:** `warp-startup`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## WARP at startup / WARP al iniciar

[Open composition](workflow-prototype.html?screen=warp-startup) · existing route/context: `/warp` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** These runtime values apply after container restart. / Estos valores se aplican tras reiniciar el contenedor.

**Evidence:** [WarpStartupSection.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/WarpStartupSection.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Startup settings / Ajustes de inicio

**Save timing:** explicit action. **Action:** Save startup settings / Guardar ajustes de inicio. **Boundary:** `runtime setup API`. Submit this resource only; other sections retain independent state.

**Consequence:** Saved for the next container start. Currently running settings stay visible separately. / Guardado para próximo inicio del contenedor. Los ajustes activos se muestran por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ENABLE_WARP` · checkbox | Start bundled WARP / Iniciar WARP integrado<br>Requires installed service; saving cannot add missing image capabilities. / Requiere servicio instalado; guardar no añade capacidades de imagen. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_DNS_ONLY` · checkbox | DNS only / Solo DNS<br>Default false. Needs NET_ADMIN; no SYS_ADMIN or TUN for DNS-only. / Por defecto false. Requiere NET_ADMIN; no SYS_ADMIN ni TUN para solo DNS. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_ENABLE_NAT` · checkbox | Connect before engines start / Conectar antes de iniciar motores<br>Default false. Wait for Connected status; full tunnel needs NET_ADMIN and /dev/net/tun. / Por defecto false. Espera Connected; túnel necesita NET_ADMIN y /dev/net/tun. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_FORCE_IPV4` · checkbox | Prefer IPv4 through WARP / Preferir IPv4 por WARP<br>Default true; keep direct-route failures separate from routing changes. / Por defecto true; separa fallos directos de cambios de ruta. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

**Read-only context: Saved / applied example / Ejemplo guardado / aplicado**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved WARP / WARP guardado | Enabled / Activado |
| Applied WARP / WARP aplicado | Disabled · restart required / Desactivado · requiere reinicio |

**Contextual exits:** [Image capabilities and startup / Capacidades de imagen e inicio](workflow-prototype.html?screen=runtime-services).

<a id="settings"></a>

**Simplified location:** Settings → Settings. **Composition:** primary destination. **Canonical editor:** `settings`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Settings / Ajustes

[Open composition](workflow-prototype.html?screen=settings) · existing route/context: `/settings` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Choose one section; each editor says when it saves. / Elige una sección; cada editor indica cuándo guarda.

**Evidence:** [Settings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Settings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Make it yours / A tu gusto**

- Accounts and access / Cuentas y acceso: Give people the access they need. / Da a cada persona el acceso que necesita. [Open related workflow](workflow-prototype.html?screen=access-account).
- Appearance and language / Apariencia e idioma: One app, three ways to see it. / Una aplicación, tres formas de verla. [Open related workflow](workflow-prototype.html?screen=preferences).
- Background updates / Actualizaciones en segundo plano: When to update sources, guides and signal checks. / Cuándo actualizar fuentes, guías y señal. [Open related workflow](workflow-prototype.html?screen=automation).

**Settings beside their task / Ajustes junto a su tarea**

- Recording settings / Ajustes de grabación: Storage, capacity and retention. / Almacenamiento, capacidad y conservación. [Open related workflow](workflow-prototype.html?screen=recording-settings).
- Playback and devices / Reproducción y dispositivos: This browser, TVs, players and playlists. / Este navegador, TV, reproductores y listas. [Open related workflow](workflow-prototype.html?screen=connections).
- Guide matching / Vinculación de guía: Review matches and optional exact automation. / Revisa coincidencias y automatización exacta opcional. [Open related workflow](workflow-prototype.html?screen=guide-match).
- Advanced setup / Configuración avanzada: Runtime options, network and restart requirements. / Opciones de ejecución, red y reinicios. [Open related workflow](workflow-prototype.html?screen=runtime-playback).

<a id="playback-settings"></a>

**Simplified location:** Where would you like to watch? → Browser player. **Composition:** contextual editor or detail. **Canonical editor:** `playback-settings`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Playback settings / Ajustes de reproducción

[Open composition](workflow-prototype.html?screen=playback-settings) · existing route/context: `/settings?tab=playback` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Engine-free catalogue use remains valid. / Se puede usar el catálogo sin motor.

**Evidence:** [PlaybackRoutingFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/PlaybackRoutingFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Playback engine / Motor de reproducción

**Save timing:** explicit action. **Action:** Save engine address / Guardar dirección. **Boundary:** `configService ace-engine-url`. Submit this resource only; other sections retain independent state.

**Consequence:** Engine preference saved independently of the routing pair below. / Preferencia guardada por separado de la ruta inferior.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `engine.url` · url | Engine address / Dirección del motor<br>Optional HTTP(S) backend-reachable URL; saved value overrides runtime fallback. Blank is valid. / URL HTTP(S) accesible desde servidor opcional; guardado prevalece. Vacío es válido. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

### Playback routing / Ruta de reproducción

**Save timing:** explicit action. **Action:** Save playback route / Guardar ruta. **Boundary:** `configService playback-routing`. Submit this resource only; other sections retain independent state.

**Consequence:** New sessions use the route. Existing shared sessions keep their route and ownership until teardown. / Sesiones nuevas usan ruta. Las activas conservan ruta y propiedad hasta finalizar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `routing.use_acexy` · checkbox | Use Acexy / Usar Acexy<br>Off by default. Shared browser/tuner factories use saved routing; probes stay direct. / Desactivado por defecto. Navegador y sintonizador usan ruta; las comprobaciones siguen directas. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `routing.acexy_url` · url | Acexy origin / Origen Acexy<br>Default http://localhost:8080; HTTP(S) origin reachable from backend. One JSON setting with use_acexy. / Por defecto http://localhost:8080; origen HTTP(S) accesible. Un ajuste JSON junto a use_acexy. | Load current saved/server value; illustrative fixture: http://localhost:8080 | enabled when routing.use_acexy is on |

**Contextual exits:** [Browser capabilities / Capacidades del navegador](workflow-prototype.html?screen=browser-player); [Runtime limits / Límites de ejecución](workflow-prototype.html?screen=runtime-playback).

<a id="automation"></a>

**Simplified location:** Settings → Background updates. **Composition:** section. **Canonical editor:** `automation`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Background updates / Actualizaciones en segundo plano

[Open composition](workflow-prototype.html?screen=automation) · existing route/context: `/settings?tab=automation` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Intervals, checking-engine choice and clock anchors save independently. / Intervalos, motor de comprobación y horas se guardan independientemente.

**Evidence:** [Settings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Settings.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Scrape sources every (hours) / Actualizar fuentes cada (horas)

**Save timing:** explicit action. **Action:** Save this setting / Guardar este ajuste. **Boundary:** `configService independent setting: schedule.rescrape_interval`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success. / Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `schedule.rescrape_interval` · number | Scrape sources every (hours) / Actualizar fuentes cada (horas)<br>Current default 24; use current endpoint whole-hour validation. Saved separately. / Por defecto 24; valida horas enteras según API. Guardado separado. | Load current saved/server value; illustrative fixture: 24 | min=1 |

### Refresh guide every (hours) / Actualizar guía cada (horas)

**Save timing:** explicit action. **Action:** Save this setting / Guardar este ajuste. **Boundary:** `configService independent setting: schedule.epg_refresh_interval`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success. / Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `schedule.epg_refresh_interval` · number | Refresh guide every (hours) / Actualizar guía cada (horas)<br>Current default 6; saved separately from sources. / Por defecto 6; se guarda por separado de fuentes. | Load current saved/server value; illustrative fixture: 6 | min=1 |

### Check signal every (minutes) / Comprobar señal cada (minutos)

**Save timing:** explicit action. **Action:** Save this setting / Guardar este ajuste. **Boundary:** `configService independent setting: schedule.channel_status_interval`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success. / Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `schedule.channel_status_interval` · number | Check signal every (minutes) / Comprobar señal cada (minutos)<br>Default 60; 1–10080 minutes. / Por defecto 60; 1–10080 minutos. | Load current saved/server value; illustrative fixture: 60 | min=1; max=10080 |

### Checking engine / Motor de comprobación

**Save timing:** explicit action. **Action:** Save checking engine / Guardar comprobador. **Boundary:** `configService check-engine`. Submit this resource only; other sections retain independent state.

**Consequence:** Checker selection saved. Existing sample timestamps remain on skips and errors. / Comprobador guardado. Se conservan fechas de muestras en omisiones y errores.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `checker.use_dedicated` · checkbox | Use a dedicated checking engine / Usar motor dedicado<br>Off uses saved playback URL; neither URL means skipped checks, preserving observations. / Desactivado usa motor de reproducción; sin ambos se omite y conserva resultados. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `checker.url` · url | Checking engine URL / URL del comprobador<br>Required when enabled. Bundled checker is supervisor-owned and read-only; configured failure never falls back. / Obligatorio al activar. Integrado es solo lectura; si falla, no recurre al otro motor. | Load current saved/server value; illustrative fixture:  | enabled when checker.use_dedicated is on |

### Streams to check / Emisiones que comprobar

**Save timing:** immediate. **Action:** Apply scope / Aplicar ámbito. **Boundary:** `configService stream-check-scope`. Submit this resource only; other sections retain independent state.

**Consequence:** Check scope saved. / Ámbito de comprobación guardado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `checks.scope` · select | Check scope / Ámbito<br>Applies to scheduled and run-now scans; individual checks remain available. Current source saves selection immediately. / Se aplica a tareas y ejecución manual; sigue la comprobación individual. El código actual guarda al seleccionar. | Load current saved/server value; illustrative fixture: all | all → All active streams / Todas las activas; assigned → Assigned to active TV channels / Vinculadas a canales activos; favorites → Assigned to favorite active TV channels / Vinculadas a favoritos activos |

**Contextual exits:** [Clock start times / Horas de inicio](workflow-prototype.html?screen=schedule-anchors); [Offline stream cleanup / Limpieza de emisiones sin señal](workflow-prototype.html?screen=offline-cleanup); [Recordings / Grabaciones](workflow-prototype.html?screen=recording-settings); [Exact guide matching / Vinculación exacta](workflow-prototype.html?screen=guide-auto); [Notifications / Notificaciones](workflow-prototype.html?screen=notifications).

<a id="schedule-anchors"></a>

**Simplified location:** Settings → Background updates. **Composition:** contextual editor or detail. **Canonical editor:** `schedule-anchors`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Schedule start times / Horas de inicio

[Open composition](workflow-prototype.html?screen=schedule-anchors) · existing route/context: `/settings?tab=automation` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Jobs can wait in the FIFO queue after becoming due. / Las tareas vencidas pueden esperar en la cola FIFO.

**Evidence:** [ScheduleAnchorFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ScheduleAnchorFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Clock anchors / Horas de referencia

**Save timing:** explicit action. **Action:** Save start times / Guardar horas. **Boundary:** `configService schedule-anchors`. Submit this resource only; other sections retain independent state.

**Consequence:** Save these start times and timezone together. Save cleanup thresholds separately. / Guarda horarios y zona juntos. Guarda límites de limpieza por separado.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `anchors.timezone` · text | Schedule timezone / Zona horaria<br>IANA, default UTC. Divisible intervals retain local clock times; other intervals use elapsed time and may shift with DST. / IANA, por defecto UTC. Intervalos divisibles conservan hora local; otros usan tiempo transcurrido y pueden desplazarse. | Load current saved/server value; illustrative fixture: UTC | required=True |
| `anchors.url_scraping` · time | Source refresh start / Inicio de fuentes<br>Optional HH:MM. Blank counts from startup; next run comes from the server. DST gap advances to valid time; repeated clock anchor runs once. / HH:MM opcional. Vacío cuenta desde inicio; servidor indica próxima ejecución. Salto DST avanza a hora válida; hora repetida ejecuta una vez. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `anchors.epg_refresh` · time | Guide refresh start / Inicio de guía<br>Optional HH:MM. Blank counts from startup; next run comes from the server. DST gap advances to valid time; repeated clock anchor runs once. / HH:MM opcional. Vacío cuenta desde inicio; servidor indica próxima ejecución. Salto DST avanza a hora válida; hora repetida ejecuta una vez. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `anchors.channel_status` · time | Signal check start / Inicio de comprobaciones<br>Optional HH:MM. Blank counts from startup; next run comes from the server. DST gap advances to valid time; repeated clock anchor runs once. / HH:MM opcional. Vacío cuenta desde inicio; servidor indica próxima ejecución. Salto DST avanza a hora válida; hora repetida ejecuta una vez. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `anchors.offline_stream_cleanup` · time | Offline cleanup start / Inicio de limpieza<br>Optional HH:MM. Blank counts from startup; next run comes from the server. DST gap advances to valid time; repeated clock anchor runs once. / HH:MM opcional. Vacío cuenta desde inicio; servidor indica próxima ejecución. Salto DST avanza a hora válida; hora repetida ejecuta una vez. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Read-only context: Next run example / Ejemplo de próxima ejecución**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Due / Vence | 8 Nov · 02:30 UTC / 8 Nov · 02:30 UTC |
| Actual launch / Inicio real | May wait for an earlier queued job / Puede esperar a una tarea previa |

<a id="offline-cleanup"></a>

**Simplified location:** Settings → Background updates. **Composition:** contextual editor or detail. **Canonical editor:** `offline-cleanup`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Offline stream cleanup / Limpieza de emisiones sin señal

[Open composition](workflow-prototype.html?screen=offline-cleanup) · existing route/context: `/settings?tab=automation` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Optional deletion needs repeated, recent offline evidence. / La eliminación opcional requiere pruebas repetidas y recientes.

**Evidence:** [OfflineCleanupFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/settings/OfflineCleanupFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, deferred, refresh-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **deferred:** Cleanup deferred while watching or recording. It will be reconsidered at its next scheduled run; no immediate retry is promised. / Limpieza aplazada por reproducción/grabación. Se reconsidera en su próxima ejecución; no se promete reintento inmediato.
- **refresh-failed:** Eligible streams were removed. Some affected sources could not refresh; retry those updates. / Se eliminaron las emisiones aptas. Algunas fuentes afectadas no se actualizaron; reintenta esas actualizaciones.

**Implementation constraint for `refresh-failed`:** Eligible streams removed, but affected-source refresh failed. Report both outcomes; do not label all cleanup failed. / Se eliminaron elegibles, pero falló actualizar fuentes. Informa ambos; no marques toda la limpieza fallida.

### Cleanup policy / Política de limpieza

**Save timing:** explicit action. **Action:** Save cleanup policy / Guardar política. **Boundary:** `configService offline-cleanup`. Submit this resource only; other sections retain independent state.

**Consequence:** Save cleanup choices. Its scheduled start time is saved separately. / Guarda opciones de limpieza. Su horario de inicio se guarda por separado.

**Confirmation:** Enable or change future deletion? Only eligible recoverable source streams qualify; recent playback and active recording protect them. / ¿Activar o cambiar eliminación futura? Solo emisiones de fuentes recuperables; reproducción reciente y grabaciones las protegen.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `offline.enabled` · checkbox | Remove long-offline streams automatically / Eliminar emisiones sin señal prolongada<br>Off by default. Hiding in Live TV is independent. / Desactivado por defecto. Ocultar en TV es independiente. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `offline.offline_days` · number | Offline for at least (days) / Sin señal al menos (días)<br>Default 14; 1–365. Errors and unknown do not count as offline evidence. / Por defecto 14; 1–365. Errores y desconocido no cuentan como prueba. | Load current saved/server value; illustrative fixture: 14 | min=1; max=365 |
| `offline.interval_days` · number | Run every (days) / Ejecutar cada (días)<br>Default 7; 1–90. Viewing/recording defers work until the next scheduled run. / Por defecto 7; 1–90. Ver/grabar aplaza hasta siguiente ejecución. | Load current saved/server value; illustrative fixture: 7 | min=1; max=90 |
| `offline.remove_linked` · checkbox | Also remove TV-linked streams / Eliminar también emisiones vinculadas<br>Default false. TV channels/guides remain, but links and preference positions are lost. / Por defecto false. Conserva canales/guías, pero se pierden vínculos y preferencias. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `offline.rescrape` · checkbox | Update affected sources afterwards / Actualizar fuentes afectadas después<br>Default true. Rediscovered streams return unchecked; update failure is separate from cleanup success. / Por defecto true. Redescubiertas vuelven sin comprobar; fallo al actualizar es independiente. | Load current saved/server value; illustrative fixture: True | No additional prototype constraint; preserve current source validation. |

**Preview eligible streams / Ver emisiones elegibles:** Read a bounded preview without deleting anything? / ¿Consultar vista limitada sin eliminar nada?

Result copy: Up to 500 streams qualify in this batch. The job rechecks at execution; zero may mean insufficient recent evidence. / Hasta 500 emisiones aptas en este lote. Se revalida al ejecutar; cero puede significar pruebas insuficientes.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Save cleanup start time separately / Guardar hora por separado](workflow-prototype.html?screen=schedule-anchors); [Cleanup history / Historial de limpieza](workflow-prototype.html?screen=jobs).

<a id="network"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `network`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Network settings / Ajustes de red

[Open composition](workflow-prototype.html?screen=network) · existing route/context: `/settings?tab=network` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Keep proxy trust, IPTV networks and account transport separate. / Separa confianza de proxy, redes IPTV y transporte de cuentas.

**Evidence:** [NetworkSettingsFields.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/settings/NetworkSettingsFields.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Current policy example / Ejemplo de política**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Accounts / Cuentas | Private HTTP supported / HTTP privado admitido |
| Proxy trust / Confianza de proxy | auto · Docker bridge peers, excluding gateways / auto · pares de puente Docker, salvo pasarelas |
| Player address / Dirección para reproductores | Saved override takes precedence / Prevalece dirección guardada |

**Contextual exits:** [Edit shared runtime network fields / Editar campos de red compartidos](workflow-prototype.html?screen=runtime-network); [Viewing and IPTV policy / Política de acceso e IPTV](workflow-prototype.html?screen=access-policy); [Edit effective player address / Editar dirección efectiva](workflow-prototype.html?screen=public-address); [Cast home networks / Redes domésticas Cast](workflow-prototype.html?screen=casting-settings).

<a id="system"></a>

**Simplified location:** System status → System status. **Composition:** primary destination. **Canonical editor:** `system`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## System status / Estado del sistema

[Open composition](workflow-prototype.html?screen=system) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Show what needs attention and what is still working. / Muestra qué requiere atención y qué sigue funcionando.

**Evidence:** [SystemDashboard.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/SystemDashboard.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Dedicated checker unavailable. Playback remains independent; previous signal observations are preserved. / Comprobador dedicado no disponible. Reproducción independiente; se conservan observaciones.

**Operations / Operaciones**

- Services / Servicios: Playback ready · checker unavailable · WARP off by choice / Reproducción lista · comprobador no disponible · WARP desactivado [Open related workflow](workflow-prototype.html?screen=services).
- Maintenance queue / Cola de mantenimiento: Guide running · sources waiting / Guía en curso · fuentes esperando [Open related workflow](workflow-prototype.html?screen=jobs).
- Storage / Almacenamiento: Partial scan · filesystem free space known / Exploración parcial · espacio libre conocido [Open related workflow](workflow-prototype.html?screen=storage).
- Diagnostics / Diagnóstico: Bounded masked logs; no private raw captures / Registros limitados y ocultados; sin capturas privadas [Open related workflow](workflow-prototype.html?screen=diagnostics).

**Contextual exits:** [WARP / WARP](workflow-prototype.html?screen=warp); [Startup status / Estado de inicio](workflow-prototype.html?screen=startup).

**Contextual exits:** [Advanced setup / Configuración avanzada](workflow-prototype.html?screen=runtime-playback); [Catalogue recovery / Recuperar catálogo](workflow-prototype.html?screen=recovery); [What changed / Qué cambió](workflow-prototype.html?screen=changelog).

<a id="services"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `services`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Service controls / Controles de servicios

[Open composition](workflow-prototype.html?screen=services) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Installed, enabled and running are separate facts. / Instalado, activado y en ejecución son hechos distintos.

**Evidence:** [ServicesPanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ServicesPanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, external. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **external:** This engine is external. Bundled supervisor controls are unavailable; show its configured address without pretending Start controls it. / Motor externo. Sin controles del supervisor; muestra dirección sin fingir que Iniciar lo controla.

**Read-only context: Bundled playback engine / Motor integrado**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Installed / Instalado | Yes / Sí |
| Enabled for startup / Activado al iniciar | Yes / Sí |
| Running / En ejecución | Intentionally stopped / Detenido expresamente |

**Start playback engine / Iniciar motor:** Resume the supervised engine? It retries exits indefinitely until you Stop or the container stops. / ¿Reanudar motor supervisado? Reintenta salidas indefinidamente hasta Detener o apagar contenedor.

Result copy: Start queued to supervisor; observed health confirms running later. / Inicio en cola del supervisor; el estado observado confirmará ejecución.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Stop playback engine / Detener motor:** Stop playback engine and pause its recovery until Start/Restart or container restart? Active use may be interrupted. / ¿Detener motor y recuperación hasta Iniciar/Reiniciar o reinicio del contenedor? Puede interrumpir uso.

Result copy: Intentional stop requested. Whole-container health respects this stop. / Detención expresa solicitada. Salud del contenedor la respeta.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Restart checking engine / Reiniciar comprobador:** Restart only the configured bundled checker? Its failure never falls back to playback. / ¿Reiniciar solo comprobador integrado? Su fallo no recurre a reproducción.

Result copy: Checker restart requested independently. / Reinicio del comprobador solicitado aparte.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Other sidecars / Otros servicios**

- Acexy / IPFS / ZeroNet / Tor / Acexy / IPFS / ZeroNet / Tor: Show installed capability and supported restart only; keep their existing fast-exit budget. / Muestra capacidad y reinicio admitido; conserva límite de salidas rápidas. [Open related workflow](workflow-prototype.html?screen=runtime-services).
- WARP / WARP: Routing controls remain on WARP / Controles permanecen en WARP [Open related workflow](workflow-prototype.html?screen=warp).

<a id="jobs"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `jobs`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Scheduled job history / Historial de tareas

[Open composition](workflow-prototype.html?screen=jobs) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Waiting is not running; errors are not offline streams. / Esperar no es ejecutar; errores no son emisiones sin señal.

**Evidence:** [ScheduledJobs.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/ScheduledJobs.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Current FIFO queue / Cola FIFO actual**

- Guide refresh / Actualizar guía: Running since 16:00 · previous result separate / En curso desde 16:00 · resultado anterior separado [Open related workflow](workflow-prototype.html?screen=job-detail).
- Source refresh / Actualizar fuentes: Waiting · already queued; run-now disabled / En espera · ya en cola; ejecutar desactivado [Open related workflow](workflow-prototype.html?screen=job-detail).
- Signal checks / Comprobar señal: Waiting for app-owned playback; bounded pause budget / Esperando reproducción propia; pausa limitada [Open related workflow](workflow-prototype.html?screen=job-detail).

**Persisted history · synthetic / Historial persistido · ficticio**

- Signal checks · 15:00 / Comprobaciones · 15:00: Online 8 · offline 2 · skipped 4 · errors 1 / Con señal 8 · sin señal 2 · omitidas 4 · errores 1 [Open related workflow](workflow-prototype.html?screen=job-detail).
- Offline cleanup · yesterday / Limpieza · ayer: Deferred while recording / Aplazada por grabación [Open related workflow](workflow-prototype.html?screen=job-detail).
- Source refresh · yesterday / Fuentes · ayer: Interrupted after restart; not still running / Interrumpida tras reinicio; no sigue en curso [Open related workflow](workflow-prototype.html?screen=job-detail).

**Contextual exits:** [Schedule settings / Ajustes de tareas](workflow-prototype.html?screen=automation).

<a id="job-detail"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `job-detail`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Job run details / Detalles de ejecución

[Open composition](workflow-prototype.html?screen=job-detail) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Retain launch time, outcome and the reason for partial work. / Conserva inicio, resultado y motivo de trabajo parcial.

**Evidence:** [ScheduledJobs.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/ScheduledJobs.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Signal check · synthetic / Comprobación · ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Launched / Iniciada | 7 Nov 15:00 UTC / 7 Nov 15:00 UTC |
| Finished / Finalizada | 7 Nov 15:11 UTC / 7 Nov 15:11 UTC |
| Result / Resultado | Partial · playback pause budget exhausted / Parcial · agotada pausa por reproducción |
| Counts / Cantidades | 8 online · 2 offline · 4 skipped · 1 error / 8 con señal · 2 sin señal · 4 omitidas · 1 error |
| Stop reason / Motivo de fin | Deferred remaining work; FIFO released / Trabajo restante aplazado; cola liberada |
| Scalar result / Resultado escalar | 3 · valid result, not a malformed object / 3 · resultado válido, no objeto erróneo |

**Explanation:** Recording capture has its own coordinator; it is not blocked behind this maintenance FIFO. Run-now requests deduplicate running and waiting work. / La captura tiene coordinador propio; no espera a esta cola. Ejecutar ahora no duplica tareas en curso o en espera.

**Contextual exits:** [Diagnostics for failures / Diagnóstico de fallos](workflow-prototype.html?screen=diagnostics).

<a id="storage"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `storage`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Storage details / Detalles de almacenamiento

[Open composition](workflow-prototype.html?screen=storage) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Free space is counted once per filesystem. / El espacio libre se cuenta una vez por sistema de archivos.

**Evidence:** [StoragePanel.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/StoragePanel.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Filesystem A · synthetic / Sistema A · ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Free / Libre | 18.4 GiB / 18.4 GiB |
| Coverage / Cobertura | Cached at 16:00 · partial scan / Caché 16:00 · exploración parcial |

**Container destinations only / Solo destinos del contenedor**

- /recordings / /recordings: 6.2 GiB observed · more files may exist / 6,2 GiB observados · puede haber más [Open related workflow](workflow-prototype.html?screen=recording-storage).
- /config / /config: Unknown · scan budget reached / Desconocido · límite de exploración
- /logs / /logs: 0.08 GiB · bounded rotating logs / 0,08 GiB · registros rotativos limitados [Open related workflow](workflow-prototype.html?screen=diagnostics).

**Explanation:** Never expose host mount sources. Scans are bounded, cached, isolated and symlink-safe. Unknown sizes are not zero; destination totals may share a filesystem. / Nunca muestres rutas de origen del host. Exploración limitada, en caché y segura ante enlaces. Desconocido no es cero; destinos pueden compartir sistema.

**Refresh storage report / Actualizar informe:** Request a bounded cached scan? It may remain partial. / ¿Solicitar exploración limitada? Puede seguir parcial.

Result copy: Report refreshed in fixture; preserve timestamp and partial coverage labels. / Informe ficticio actualizado; conserva fecha y etiquetas parciales.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="diagnostics"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `diagnostics`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Logs and diagnostics / Registros y diagnóstico

[Open composition](workflow-prototype.html?screen=diagnostics) · existing route/context: `/system` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Download recent logs with sensitive values masked. Original log messages are unchanged. / Descarga registros recientes con datos sensibles ocultos. Los mensajes originales se conservan.

**Evidence:** [DiagnosticsDownload.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/DiagnosticsDownload.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, pending, success, conflict, denied, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **denied:** Enter the required administrative API token or sign in as permitted. Diagnostic availability during startup failure does not bypass auth. / Introduce token administrativo o sesión permitida. Diagnóstico durante fallo no omite autenticación.
- **partial:** One fixed log is unavailable. Export the available tails and report the omitted file, not an empty successful log. / Un registro fijo no está disponible. Exporta fragmentos disponibles e informa del omitido.

**Read-only context: Diagnostic scope / Ámbito**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Files / Archivos | Fixed scraper / service / entrypoint tails / Fragmentos fijos de scraper / servicios / entrada |
| Credentials / Credenciales | Masked by export; still review before sharing / Ocultadas al exportar; revisa antes de compartir |
| Availability / Disponibilidad | DB-independent, normal API-token checks still apply / Independiente de BD; conserva validación de token |

**Synthetic read-only output:**

```text
DEMO 16:00 checker unavailable
DEMO 16:01 guide refresh waiting
DEMO 16:02 source refresh interrupted
```

**Prepare diagnostics download / Preparar descarga de diagnóstico:** Export only bounded fixed-file tails? No environment dump or arbitrary path selection. / ¿Exportar solo fragmentos de archivos fijos? Sin volcado de entorno ni rutas arbitrarias.

Result copy: Synthetic export prepared; no private files accessed. / Exportación ficticia preparada; sin acceder a archivos privados.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="setup"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `setup`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Start with channels / Empieza por los canales

[Open composition](workflow-prototype.html?screen=setup) · existing route/context: `/setup` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Add a source and an optional guide. Engines are optional. / Añade una fuente y guía opcional. Los motores son opcionales.

**Evidence:** [Setup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Setup.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **partial:** The channel source was saved, but the guide could not be added. Retry the guide or finish without it. / La fuente se guardó, pero no se añadió la guía. Reintenta la guía o termina sin ella.

**Implementation constraint for `partial`:** Source saved, guide failed. Keep the source and offer retry of the guide or Finish without guide. / Fuente guardada, guía fallida. Conserva fuente y permite reintentar guía o terminar sin ella.

**Progress:** 1 · Channels / 1 · Canales → 2 · Optional guide / 2 · Guía opcional → 3 · Finish / 3 · Terminar.

**Saved during setup · synthetic / Guardado durante configuración · ficticio**

- Family channels / Family channels: Saved already · import waiting / Ya guardada · importación esperando [Open related workflow](workflow-prototype.html?screen=source-results).
- Programme guide / Guía de programación: Optional · shared EPG dobleM preset is an explicit choice / Opcional · EPG dobleM es elección expresa [Open related workflow](workflow-prototype.html?screen=guide-source).

**Contextual exits:** [Add another source / Añadir otra fuente](workflow-prototype.html?screen=source-auto); [Review guide matches / Revisar coincidencias](workflow-prototype.html?screen=guide-match); [Advanced connection settings / Conexiones avanzadas](workflow-prototype.html?screen=runtime-playback).

**Finish setup / Terminar configuración:** Mark onboarding complete? Sources and guides were saved as added; Finish does not atomically save them again. / ¿Marcar configuración completa? Fuentes y guías ya se guardaron; Terminar no vuelve a guardarlas atómicamente.

Result copy: Setup completed. Open Live TV or return to sources while import waits. / Configuración terminada. Abre TV o vuelve a fuentes mientras importa.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Postpone setup / Posponer configuración](workflow-prototype.html?screen=dashboard).

**Contextual exits:** [First source / Primera fuente](workflow-prototype.html?screen=setup-source).

**Contextual exits:** [Optional guide / Guía opcional](workflow-prototype.html?screen=setup-guide).

<a id="startup"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `startup`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Starting AceStream Scraper / Iniciando AceStream Scraper

[Open composition](workflow-prototype.html?screen=startup) · existing route/context: `outer startup gate` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Keep the interface available while startup works in the background. / Mantén la interfaz disponible durante el inicio en segundo plano.

**Evidence:** [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx)

**Permission:** normal startup / API-token policy. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, deferred, connection, token. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **deferred:** Application ready; legacy guide programmes are still importing in resumable batches. Other work remains available. / App lista; programas antiguos se importan por lotes reanudables. Sigue disponible el resto.
- **connection:** Connection lost. Retry status before offering catalogue replacement. / Conexión perdida. Reintenta estado antes de ofrecer reemplazar catálogo.
- **token:** Enter the configured API token to read protected startup information. Recovery never bypasses authentication. / Introduce token configurado para leer estado protegido. Recuperación nunca omite autenticación.

**Read-only context: Startup progress · synthetic / Progreso ficticio**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Database / Base de datos | Schema upgrade in progress / Actualizando esquema |
| Normal API / API normal | Temporarily unavailable / No disponible temporalmente |
| Large guide import / Importación de guía grande | Resumable background work; no invented completion time / Trabajo reanudable; sin tiempo inventado |

**Explanation:** Loading is not an empty catalogue. Loss of connection is not proof of database damage. / Cargar no significa catálogo vacío. Perder conexión no prueba daño en base de datos.

**Contextual exits:** [Download authenticated diagnostics / Descargar diagnóstico autenticado](workflow-prototype.html?screen=diagnostics); [Startup failure options / Opciones ante fallo de inicio](workflow-prototype.html?screen=recovery).

<a id="recovery"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `recovery`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Startup needs attention / El inicio necesita atención

[Open composition](workflow-prototype.html?screen=recovery) · existing route/context: `startup failure gate` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Start with diagnostics and retry before replacing any catalogue data. / Empieza por diagnóstico y reintento antes de sustituir datos.

**Evidence:** [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict, busy, interrupted. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **busy:** Another recovery is already running. Wait for its result before retrying. / Ya hay una recuperación en curso. Espera su resultado antes de reintentar.
- **interrupted:** A previous recovery was interrupted. Review the recovery details and retry instructions before continuing. / Se interrumpió una recuperación anterior. Revisa sus detalles e instrucciones antes de continuar.

**Implementation constraint for `busy`:** Another recovery owns the database lock. Wait for its result; do not start a competing operation. / Otra recuperación tiene el bloqueo. Espera su resultado; no inicies otra operación.

**Implementation constraint for `interrupted`:** Interrupted recovery marker found. Show its safe resume/retry instructions; never treat this as a fresh empty install. / Marca de recuperación interrumpida. Muestra instrucciones seguras; no lo trates como instalación vacía.

**Explanation:** Synthetic database-startup failure. The independent accounts store remains protected and outside catalogue recovery. / Fallo ficticio de inicio de BD. Las cuentas independientes permanecen protegidas y fuera de la recuperación.

**Contextual exits:** [Read diagnostic scope / Ver ámbito de diagnóstico](workflow-prototype.html?screen=diagnostics).

**Retry startup / Reintentar inicio:** Retry the failed startup without catalogue replacement? / ¿Reintentar inicio sin sustituir catálogo?

Result copy: Startup retry requested; watch actual progress. / Reintento solicitado; observa progreso real.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Recovery choices / Opciones de recuperación**

- Recover readable catalogue / Recuperar catálogo legible: Back up first; damaged rows can be skipped / Copia primero; se pueden omitir filas dañadas [Open related workflow](workflow-prototype.html?screen=recovery-readable).
- Start a fresh catalogue / Empezar catálogo nuevo: Back up and replace catalogue configuration / Copia y sustituye configuración del catálogo [Open related workflow](workflow-prototype.html?screen=recovery-fresh).

<a id="recovery-readable"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `recovery-readable`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Recover readable catalogue / Recuperar catálogo legible

[Open composition](workflow-prototype.html?screen=recovery-readable) · existing route/context: `startup recovery` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Review what is retained and what must be rebuilt. / Revisa qué se conserva y qué se reconstruye.

**Evidence:** [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Back up the catalogue first. Restore the source and settings data that can still be read. Damaged entries may be skipped; channel listings and activity must be rebuilt. Accounts stay unchanged. / Haz una copia del catálogo primero. Recupera las fuentes y ajustes que aún se puedan leer. Se pueden omitir datos dañados; los canales y la actividad deberán reconstruirse. Las cuentas se conservan.

### Confirmation / Confirmación

**Save timing:** explicit action. **Action:** Recover readable catalogue / Recuperar catálogo legible. **Boundary:** `startupService recovery`. Submit this resource only; other sections retain independent state.

**Consequence:** Back up the catalogue first. Restore the source and settings data that can still be read. Damaged entries may be skipped; channel listings and activity must be rebuilt. Accounts stay unchanged. / Haz una copia del catálogo primero. Recupera las fuentes y ajustes que aún se puedan leer. Se pueden omitir datos dañados; los canales y la actividad deberán reconstruirse. Las cuentas se conservan.

**Confirmation:** Back up the catalogue first. Restore the source and settings data that can still be read. Damaged entries may be skipped; channel listings and activity must be rebuilt. Accounts stay unchanged. / Haz una copia del catálogo primero. Recupera las fuentes y ajustes que aún se puedan leer. Se pueden omitir datos dañados; los canales y la actividad deberán reconstruirse. Las cuentas se conservan.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recovery.confirm` · checkbox | I understand this recovery action / Entiendo esta recuperación<br>Required. Check the consequence above before continuing. If recovery fails, review the result before trying again. / Obligatorio. Revisa las consecuencias antes de continuar. Si la recuperación falla, revisa el resultado antes de reintentar. | Load current saved/server value; illustrative fixture: False | required=True; Adapter/contract note: Required; current recovery token is revalidated on submission. No automatic destructive retries. / Obligatorio; se revalida token actual al enviar. Sin reintentos destructivos automáticos. |

**Contextual exits:** [Go back without changes / Volver sin cambios](workflow-prototype.html?screen=recovery).

<a id="recovery-fresh"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `recovery-fresh`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Start a fresh catalogue / Empezar catálogo nuevo

[Open composition](workflow-prototype.html?screen=recovery-fresh) · existing route/context: `startup recovery` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Review what is retained and what must be rebuilt. / Revisa qué se conserva y qué se reconstruye.

**Evidence:** [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Back up the catalogue first. Replace its data and set up your sources and catalogue settings again. Accounts, access restrictions and passwords stay unchanged. / Haz una copia del catálogo primero. Sustituye sus datos y vuelve a configurar las fuentes y los ajustes del catálogo. Las cuentas, restricciones de acceso y contraseñas se conservan.

### Confirmation / Confirmación

**Save timing:** explicit action. **Action:** Start a fresh catalogue / Empezar catálogo nuevo. **Boundary:** `startupService recovery`. Submit this resource only; other sections retain independent state.

**Consequence:** Back up the catalogue first. Replace its data and set up your sources and catalogue settings again. Accounts, access restrictions and passwords stay unchanged. / Haz una copia del catálogo primero. Sustituye sus datos y vuelve a configurar las fuentes y los ajustes del catálogo. Las cuentas, restricciones de acceso y contraseñas se conservan.

**Confirmation:** Back up the catalogue first. Replace its data and set up your sources and catalogue settings again. Accounts, access restrictions and passwords stay unchanged. / Haz una copia del catálogo primero. Sustituye sus datos y vuelve a configurar las fuentes y los ajustes del catálogo. Las cuentas, restricciones de acceso y contraseñas se conservan.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recovery.confirm` · checkbox | I understand this recovery action / Entiendo esta recuperación<br>Required. Check the consequence above before continuing. If recovery fails, review the result before trying again. / Obligatorio. Revisa las consecuencias antes de continuar. Si la recuperación falla, revisa el resultado antes de reintentar. | Load current saved/server value; illustrative fixture: False | required=True; Adapter/contract note: Required; current recovery token is revalidated on submission. No automatic destructive retries. / Obligatorio; se revalida token actual al enviar. Sin reintentos destructivos automáticos. |

**Contextual exits:** [Go back without changes / Volver sin cambios](workflow-prototype.html?screen=recovery).

<a id="recovery-result"></a>

**Simplified location:** System status → System status. **Composition:** contextual editor or detail. **Canonical editor:** `recovery-result`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Recovery result / Resultado de recuperación

[Open composition](workflow-prototype.html?screen=recovery-result) · existing route/context: `startup recovery` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Report backup, copied rows and omissions separately. / Informa por separado de copia, filas y omisiones.

**Evidence:** [StartupGate.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/StartupGate.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **failed:** Recovery did not finish. Preserve backup and marker; no success or fresh-start claim. Follow the returned safe retry path. / Recuperación incompleta. Conserva copia y marca; no afirmes éxito. Sigue el reintento seguro indicado.

**Read-only context: Synthetic readable recovery / Recuperación legible ficticia**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Backup / Copia | Created before changes / Creada antes de cambios |
| Recovered / Recuperado | 2 sources · 3 TV channels · 6 streams / 2 fuentes · 3 canales · 6 emisiones |
| Skipped / Omitido | 1 damaged row · listings/activity not copied / 1 fila dañada · sin programación/actividad |
| Accounts / Cuentas | Retained independently / Conservadas por separado |

**Contextual exits:** [Follow startup progress / Seguir inicio](workflow-prototype.html?screen=startup); [Review catalogue setup / Revisar configuración](workflow-prototype.html?screen=setup); [Download recovery diagnostics / Descargar diagnóstico](workflow-prototype.html?screen=diagnostics).

<a id="preferences"></a>

**Simplified location:** Settings → Language and appearance. **Composition:** section. **Canonical editor:** `preferences`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Language and appearance / Idioma y apariencia

[Open composition](workflow-prototype.html?screen=preferences) · existing route/context: `shared shell preferences` · implementation [#317](https://github.com/Pipepito/acestream-scraper/issues/317)

**Purpose:** Changes apply in this browser without restarting playback or losing a draft. / Se aplica en este navegador sin reiniciar reproducción ni perder borrador.

**Evidence:** [AppShell.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/layout/AppShell.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, storage-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **storage-failed:** Your choice applies in this tab, but could not be saved for your next visit. / Tu elección se aplica en esta pestaña, pero no se pudo guardar para la próxima visita.

**Implementation constraint for `storage-failed`:** Preference changed for this tab, but could not be saved for next time. Continue using the app; offer Retry storage. / Preferencia cambiada en esta pestaña, pero no se guardó para la próxima vez. Continúa; ofrece reintentar.

### Browser preferences / Preferencias de navegador

**Save timing:** explicit action. **Action:** Use preferences / Usar preferencias. **Boundary:** `proposed browser preference resource`. View/preview only; no persistent data mutation.

**Consequence:** Applied now in this tab. Persistence failure must not roll back the visible choice or lose a form. / Aplicado en esta pestaña. Fallo al guardar no revierte elección ni pierde formulario.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `preference.language` · select | Interface language / Idioma de interfaz<br>English / Español / system. Names, logs, URLs and IDs remain original. / English / Español / sistema. Nombres, registros, URLs e IDs se conservan. | Load current saved/server value; illustrative fixture: system | system → System default / Sistema; en → English / English; es → Español / Español |
| `preference.theme` · select | Appearance / Apariencia<br>System, light or dark; reduced motion follows the device preference. / Sistema, claro u oscuro; movimiento reducido según dispositivo. | Load current saved/server value; illustrative fixture: system | system → System default / Sistema; light → Light / Claro; dark → Dark / Oscuro |

**Explanation:** All palette/font directions in review controls remain proposals. Existing application IBM Plex/teal standards remain authoritative. / Todas las direcciones de color/tipo siguen propuestas. Los estándares IBM Plex/teal actuales siguen vigentes.

<a id="notices"></a>

**Simplified location:** System status → Settings. **Composition:** contextual editor or detail. **Canonical editor:** `notices`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Notices and session feedback / Avisos y mensajes

[Open composition](workflow-prototype.html?screen=notices) · existing route/context: `shared shell` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Notices have their own scope and consequence. / Los avisos tienen ámbito y consecuencia propios.

**Evidence:** [ApiTokenNotice.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ApiTokenNotice.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Legacy API access / Acceso API anterior

**Save timing:** explicit action. **Action:** Use API token / Usar token. **Boundary:** `apiToken browser credential`. Submit this resource only; other sections retain independent state.

**Consequence:** Token used for subsequent authenticated requests. Invalid token keeps management blocked. / Token usado en siguientes solicitudes. Si no es válido, administración bloqueada.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `legacy.token` · password | API token / Token API<br>Existing deployment header token; stored through current token policy. Never insert into administrative URLs. / Token de cabecera existente; usa política actual. Nunca en URLs administrativas. | Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource. | No additional prototype constraint; preserve current source validation. |

**Independent notices / Avisos independientes**

- Setup incomplete / Configuración incompleta: Continue or postpone; sources already saved remain / Continúa o pospón; se conservan fuentes [Open related workflow](workflow-prototype.html?screen=setup).
- New stable version available / Nueva versión estable: Manual update instructions; no auto-install. Failed checks stay quiet. / Instrucciones manuales; sin instalación automática. Fallos de consulta silenciosos. [Open related workflow](workflow-prototype.html?screen=changelog).
- What changed / Qué cambió: Per-browser read/dismiss; development notes are not proof of stable release. / Leído/oculto por navegador; notas no prueban publicación estable. [Open related workflow](workflow-prototype.html?screen=changelog).

**Dismiss update notice / Ocultar aviso:** Dismiss this version notice in this browser? / ¿Ocultar este aviso de versión en este navegador?

Result copy: Dismissed locally; changelog remains available. / Oculto localmente; historial sigue disponible.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

<a id="not-found"></a>

**Simplified location:** Watch → Settings. **Composition:** contextual editor or detail. **Canonical editor:** `not-found`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## This page is not available / Esta página no está disponible

[Open composition](workflow-prototype.html?screen=not-found) · existing route/context: `*` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** This address does not match a page. Return home or open a known section. / Esta dirección no corresponde a una página. Vuelve al inicio o abre una sección conocida.

**Evidence:** [NotFound.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/NotFound.tsx)

**Permission:** route-aware access gate. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Unknown route /sample-missing. Do not echo private query values. Existing aliases still redirect with query context. / Ruta desconocida /sample-missing. No muestres consultas privadas. Los alias existentes conservan contexto.

**Contextual exits:** [Go to dashboard / Ir al inicio](workflow-prototype.html?screen=dashboard); [TV channels / Canales de TV](workflow-prototype.html?screen=channels); [Settings / Ajustes](workflow-prototype.html?screen=settings).

**Read-only context: Compatibility examples / Ejemplos de compatibilidad**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| /channels/:id / /channels/:id | /tv-channels / /tv-channels |
| /epg/mappings / /epg/mappings | /epg?tab=rules / /epg?tab=rules |
| /catalogues / /catalogues | /scraper?tab=w3u / /scraper?tab=w3u |
| /health / /health | /system / /system |

<a id="changelog"></a>

**Simplified location:** System status → Settings. **Composition:** contextual editor or detail. **Canonical editor:** `changelog`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## What changed / Qué cambió

[Open composition](workflow-prototype.html?screen=changelog) · existing route/context: `/changelog` · implementation [#322](https://github.com/Pipepito/acestream-scraper/issues/322)

**Purpose:** Read bundled history without needing a network connection. / Lee el historial incluido sin conexión.

**Evidence:** [Changelog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Changelog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Version history · synthetic text / Historial · texto ficticio**

- v2.2.0 · development notes / v2.2.0 · notas de desarrollo: Illustrative release text, not a publication claim. Historical Markdown keeps its original language. / Texto ilustrativo, no afirma publicación. Markdown histórico conserva idioma.
- Earlier versions / Versiones anteriores: Navigation chrome is translated; source notes are identified by original language. / Navegación traducida; notas identificadas por idioma original.

**Contextual exits:** [Back to dashboard / Volver al inicio](workflow-prototype.html?screen=dashboard).

<a id="unsaved"></a>

**Simplified location:** Settings → Settings. **Composition:** contextual editor or detail. **Canonical editor:** `unsaved`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Leave with unsaved changes? / ¿Salir sin guardar?

[Open composition](workflow-prototype.html?screen=unsaved) · existing route/context: `shared dirty guard` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** A consequential guard, not a save across unrelated settings. / Una protección al salir, no guardado de ajustes independientes.

**Evidence:** [ConfirmDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ConfirmDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Example source draft / Borrador de fuente

**Save timing:** explicit action. **Action:** Save source draft / Guardar borrador. **Boundary:** `proposed form dirty guard`. Submit this resource only; other sections retain independent state.

**Consequence:** Only this source draft saved. / Solo se guardó este borrador.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `draft.source_name` · text | Source name / Nombre de fuente<br>Change this, then follow another workflow link to test Stay / Discard. / Cámbialo y sigue otro enlace para probar Quedarse / Descartar. | Load current saved/server value; illustrative fixture: Family channels | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Navigate to dashboard / Ir al inicio](workflow-prototype.html?screen=dashboard).

**Explanation:** Locale/theme changes retain dirty values, row selection, current route, focus and scroll. Page unload uses native browser protection; no crash-recovery promise. / Idioma/tema conservan valores, selección, ruta, foco y posición. Al cerrar usa protección del navegador; sin prometer recuperación tras fallo.

<a id="runtime-playback"></a>

**Simplified location:** System status → Playback runtime. **Composition:** section. **Canonical editor:** `runtime-playback`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Playback runtime / Ejecución de reproducción

[Open composition](workflow-prototype.html?screen=runtime-playback) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### Playback runtime / Ejecución de reproducción

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ACE_ENGINE_URL` · text | Playback engine address / Dirección del motor de reproducción<br>Fallback engine address; saved Playback wins. Blank permits engine-free use. / Dirección alternativa de motor; prevalece Reproducción guardada. Vacío permite uso sin motor. | Repository default:  | No additional prototype constraint; preserve current source validation. |
| `runtime.ACE_CHECK_ENGINE_URL` · text | Dedicated checking engine address / Dirección del motor de comprobación dedicado<br>External checking fallback; bundled checker is managed and unavailable never means fallback to playback. / Alternativa de comprobador externo; integrado es gestionado y su fallo no permite usar reproducción. | Repository default:  | No additional prototype constraint; preserve current source validation. |
| `runtime.PLAYER_MAX_SESSIONS` · number | Maximum browser sessions / Máximo de sesiones del navegador<br>Maximum simultaneous browser sessions, not number of viewers; matching viewers can share. / Máximo de sesiones simultáneas, no de espectadores; compatibles pueden compartir. | Repository default: 3 | min=1; max=100 |
| `runtime.PLAYER_START_TIMEOUT_SECONDS` · number | Player startup timeout (seconds) / Tiempo de espera al iniciar el reproductor (segundos)<br>Total browser startup budget in seconds, including waiting for source ownership. / Tiempo total de inicio del navegador en segundos, incluida espera de propiedad. | Repository default: 45 | min=1; max=600 |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="runtime-network"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `runtime-network`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Network runtime / Ejecución de red

[Open composition](workflow-prototype.html?screen=runtime-network) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### Network runtime / Ejecución de red

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.PUBLIC_BASE_URL` · text | Public address / Dirección para reproductores<br>Runtime fallback only. Saved Integrations address wins; preserve proxy prefix. / Solo alternativa de ejecución. Prevalece Integraciones; conserva prefijo de proxy. | Repository default:  | No additional prototype constraint; preserve current source validation. |
| `runtime.ALLOW_PRIVATE_SCRAPE_TARGETS` · checkbox | Allow sources on private networks / Permitir fuentes en redes privadas<br>Allows private source fetches; metadata addresses remain blocked. / Permite consultas a fuentes privadas; direcciones de metadatos bloqueadas. | Repository default: True | No additional prototype constraint; preserve current source validation. |
| `runtime.TUNER_ALLOWED_NETWORKS` · text | Networks allowed to use tuner routes / Redes autorizadas para las rutas de sintonizador<br>Client CIDRs for tuner routes; separate from API tokens. Asterisk opens all networks. / CIDR de clientes de sintonizador; separado de tokens. Asterisco abre todas las redes. | Repository default: 127.0.0.0/8,10.0.0.0/8,100.64.0.0/10,172.16.0.0/12,192.168.0.0/16,::1/128,fc00::/7,fe80::/10 | No additional prototype constraint; preserve current source validation. |
| `runtime.FORWARDED_ALLOW_IPS` · text | Trusted reverse proxies / Proxies inversos de confianza<br>auto trusts loopback and Docker bridge peers, not gateways. Preserve explicit overrides; do not trust the entire LAN. / auto confía en loopback y pares Docker, no pasarelas. Conserva valores explícitos; no confíes en toda la LAN. | Repository default: auto | No additional prototype constraint; preserve current source validation. |
| `runtime.CORS_ORIGINS` · text | Allowed browser origins / Orígenes del navegador permitidos<br>Comma-separated origins or JSON array for separately hosted browsers; usually unchanged. / Orígenes por comas o array JSON para navegador alojado aparte; normalmente sin cambios. | Repository default: http://localhost:3000 | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="runtime-services"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `runtime-services`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Installed services / Servicios instalados

[Open composition](workflow-prototype.html?screen=runtime-services) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### Installed services / Servicios instalados

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ENABLE_ACESTREAM_ENGINE` · checkbox | Bundled playback engine / Motor de reproducción integrado<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_ACESTREAM_CHECK_ENGINE` · checkbox | Bundled checking engine / Motor de comprobación integrado<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_ACEXY` · checkbox | Acexy / Acexy<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_IPFS` · checkbox | IPFS / IPFS<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_ZERONET` · checkbox | ZeroNet / ZeroNet<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_TOR` · checkbox | Tor for ZeroNet / Tor para ZeroNet<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ENABLE_WARP` · checkbox | WARP / WARP<br>Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies. / Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.ACESTREAM_BIND_ALL` · checkbox | Allow remote engine clients / Permitir clientes remotos del motor<br>Engine API is unauthenticated. Publish its port only to trusted clients. / API del motor sin autenticación. Publica puerto solo a clientes de confianza. | Repository default: True | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_DNS_ONLY` · checkbox | Use WARP for DNS only / Usar WARP solo para DNS<br>Encrypt DNS only; video uses the normal route. NET_ADMIN required, not SYS_ADMIN/TUN. / Cifra solo DNS; vídeo usa ruta normal. Requiere NET_ADMIN, no SYS_ADMIN/TUN. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_ENABLE_NAT` · checkbox | Connect WARP before starting engines / Conectar WARP antes de iniciar los motores<br>Wait for Connected before engines. Full tunnel needs NET_ADMIN and /dev/net/tun. / Espera Connected antes de motores. Túnel requiere NET_ADMIN y /dev/net/tun. | Repository default: False | No additional prototype constraint; preserve current source validation. |
| `runtime.WARP_FORCE_IPV4` · checkbox | Prefer IPv4 through WARP / Preferir IPv4 con WARP<br>Prefer IPv4 for WARP routing; does not authorize automatic connection on DNS failure. / Prefiere IPv4 en WARP; no autoriza conexión automática ante fallo DNS. | Repository default: True | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="runtime-advanced"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `runtime-advanced`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Advanced source runtime / Ejecución avanzada de fuentes

[Open composition](workflow-prototype.html?screen=runtime-advanced) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### Advanced source runtime / Ejecución avanzada de fuentes

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ZERONET_URL` · text | ZeroNet gateway / Pasarela ZeroNet<br>Gateway reachable inside the container; preserve persistent ZeroNet site state. / Pasarela accesible dentro del contenedor; conserva estado persistente de sitios. | Repository default: http://127.0.0.1:43110 | No additional prototype constraint; preserve current source validation. |
| `runtime.IPFS_GATEWAY_URL` · text | IPFS gateway / Pasarela IPFS<br>IPFS HTTP gateway reachable from the scraper. / Pasarela HTTP IPFS accesible desde scraper. | Repository default: http://127.0.0.1:8081 | No additional prototype constraint; preserve current source validation. |
| `runtime.SCRAPER_TIMEOUT` · number | Source timeout (seconds) / Tiempo de espera de la fuente (segundos)<br>Maximum wait per operation, in seconds. Longer waits delay a failure result. / Espera máxima por operación en segundos. Más espera retrasa informar fallos. | Repository default: 10 | min=1; max=600 |
| `runtime.SCRAPER_RETRIES` · number | Source retries / Reintentos de fuente<br>Additional source attempts after failure. Zero disables retries; work stays bounded. / Intentos adicionales tras fallo. Cero desactiva reintentos; trabajo limitado. | Repository default: 3 | min=0; max=20 |
| `runtime.ZERONET_TIMEOUT` · number | ZeroNet timeout (seconds) / Tiempo de espera de ZeroNet (segundos)<br>Maximum wait per operation, in seconds. Longer waits delay a failure result. / Espera máxima por operación en segundos. Más espera retrasa informar fallos. | Repository default: 20 | min=1; max=600 |
| `runtime.ZERONET_RETRIES` · number | ZeroNet retries / Reintentos de ZeroNet<br>Additional source attempts after failure. Zero disables retries; work stays bounded. / Intentos adicionales tras fallo. Cero desactiva reintentos; trabajo limitado. | Repository default: 5 | min=0; max=20 |
| `runtime.IPFS_TIMEOUT` · number | IPFS timeout (seconds) / Tiempo de espera de IPFS (segundos)<br>Maximum wait per operation, in seconds. Longer waits delay a failure result. / Espera máxima por operación en segundos. Más espera retrasa informar fallos. | Repository default: 30 | min=1; max=600 |
| `runtime.IPFS_RETRIES` · number | IPFS retries / Reintentos de IPFS<br>Additional source attempts after failure. Zero disables retries; work stays bounded. / Intentos adicionales tras fallo. Cero desactiva reintentos; trabajo limitado. | Repository default: 3 | min=0; max=20 |
| `runtime.CHANNEL_CLEANUP_DAYS` · number | Inactive-channel retention (days) / Conservación de canales inactivos (días)<br>Inactive-channel retention in days; distinct from opt-in verified offline cleanup. / Conservación de canales inactivos en días; distinta de limpieza opcional sin señal. | Repository default: 30 | min=0; max=36500 |
| `runtime.MEDIA_SERVER_MIN_REFRESH_MINUTES` · number | Media-server refresh debounce (minutes) / Intervalo mínimo entre actualizaciones del servidor multimedia (minutos)<br>Minimum minutes between automatic media-server refreshes; prevents duplicate work. / Minutos mínimos entre actualizaciones automáticas; evita duplicación. | Repository default: 30 | min=0; max=10080 |
| `runtime.ACESTREAM_STATUS_TIMEOUT` · number | Engine status timeout (seconds) / Tiempo de espera del estado del motor (segundos)<br>Maximum wait per operation, in seconds. Longer waits delay a failure result. / Espera máxima por operación en segundos. Más espera retrasa informar fallos. | Repository default: 10 | min=1; max=600 |
| `runtime.EPG_PROGRAM_RETENTION_HOURS` · number | Guide retention (hours) / Conservación de la guía (horas)<br>Hours to keep expired guide programmes; any negative value keeps them. / Horas de conservación de programas caducados; cualquier negativo los conserva. | Repository default: 24 | No additional prototype constraint; preserve current source validation. |
| `runtime.TZ` · text | Timezone / Zona horaria del contenedor<br>Container IANA timezone; independent of browser locale and saved schedule timezone. / Zona IANA del contenedor; independiente de idioma y zona de tareas. | Repository default: UTC | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="runtime-engine-ports"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `runtime-engine-ports`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Engine and Acexy connections / Conexiones de motor y Acexy

[Open composition](workflow-prototype.html?screen=runtime-engine-ports) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### Engine and Acexy connections / Conexiones de motor y Acexy

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ACESTREAM_HTTP_HOST` · text | Bundled engine connection host / Host de conexión al motor integrado<br>Internal bundled engine connection host, normally localhost. / Host interno de motor integrado, normalmente localhost. | Repository default: localhost | No additional prototype constraint; preserve current source validation. |
| `runtime.ACESTREAM_HTTP_PORT` · number | Bundled engine HTTP port / Puerto HTTP del motor integrado<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 6878 | min=1; max=65535 |
| `runtime.ACEXY_HOST` · text | Acexy upstream host / Host de origen de Acexy<br>Engine host reachable by Acexy within the container network. / Host de motor accesible desde Acexy en la red del contenedor. | Repository default: localhost | No additional prototype constraint; preserve current source validation. |
| `runtime.ACEXY_PORT` · number | Acexy upstream port / Puerto de origen de Acexy<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 6878 | min=1; max=65535 |
| `runtime.ACEXY_LISTEN_ADDR` · text | Acexy listen address / Dirección de escucha de Acexy<br>Internal listener such as :8080. Deployment port mappings must match. / Escucha interna como :8080. Mapeos del despliegue deben coincidir. | Repository default: :8080 | No additional prototype constraint; preserve current source validation. |
| `runtime.ACEXY_NO_RESPONSE_TIMEOUT` · text | Acexy response timeout / Tiempo de respuesta de Acexy<br>Engine response duration, e.g. 30s or 1m30s. / Duración de respuesta del motor, p. ej. 30s o 1m30s. | Repository default: 30s | No additional prototype constraint; preserve current source validation. |
| `runtime.ACEXY_BUFFER_SIZE` · text | Acexy buffer size / Búfer de Acexy<br>Buffer per stream, e.g. 4MiB; not an overall memory quota. / Búfer por emisión, p. ej. 4MiB; no es cuota total de memoria. | Repository default: 4MiB | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="runtime-gateway-ports"></a>

**Simplified location:** System status → Playback runtime. **Composition:** contextual editor or detail. **Canonical editor:** `runtime-gateway-ports`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## ZeroNet and IPFS connections / Conexiones ZeroNet e IPFS

[Open composition](workflow-prototype.html?screen=runtime-gateway-ports) · existing route/context: `/setup · Connection settings (advanced)` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Advanced settings for the next container start. Values shown are example repository defaults. / Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.

**Evidence:** [RuntimeSetup.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/RuntimeSetup.tsx); [runtime-options.json](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/config/runtime-options.json)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, managed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **conflict:** Saved settings changed elsewhere. Reload the current saved and active values before trying again. / Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.
- **managed:** This option is unavailable or controlled by the bundled service. Its current value is read-only. / Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.

**Implementation constraint for `conflict`:** Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override. / Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.

**Implementation constraint for `managed`:** Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement. / Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.

**Read-only context: Saved / applied / source / Guardado / aplicado / origen**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Saved / Guardado | Repository defaults shown for illustration / Defectos de repositorio como ejemplo |
| Applied / Aplicado | Read boot snapshot separately; do not infer from Save / Lee estado de inicio aparte; no lo deduzcas de Guardar |
| Effect / Efecto | Restart required; commands, paths and secrets stay deployment-owned / Requiere reinicio; órdenes, rutas y secretos siguen en despliegue |

### ZeroNet and IPFS connections / Conexiones ZeroNet e IPFS

**Save timing:** explicit action. **Action:** Save runtime section / Guardar sección de ejecución. **Boundary:** `setupService.update expected_revision`. Submit this resource only; other sections retain independent state.

**Consequence:** Save for the next container start. This does not restart the container or change a higher-priority app setting. / Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `runtime.ZERONET_UI_PORT` · number | ZeroNet UI port / Puerto de interfaz de ZeroNet<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 43110 | min=1; max=65535 |
| `runtime.ZERONET_FILESERVER_PORT` · number | ZeroNet peer port / Puerto de pares de ZeroNet<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 26552 | min=1; max=65535 |
| `runtime.ZERONET_UI_HOST` · text | ZeroNet allowed UI hosts / Hosts permitidos para la interfaz de ZeroNet<br>Space-separated allowed hostnames for unauthenticated UI. Trusted clients only. / Hosts permitidos por espacios para UI sin autenticación. Solo clientes de confianza. | Repository default:  | No additional prototype constraint; preserve current source validation. |
| `runtime.IPFS_API_HOST` · text | IPFS API bind address / Dirección de escucha de la API IPFS<br>Internal bind address; keep loopback unless trusted clients need the unauthenticated API. / Dirección interna; conserva loopback salvo clientes de confianza para API sin autenticación. | Repository default: 127.0.0.1 | No additional prototype constraint; preserve current source validation. |
| `runtime.IPFS_API_PORT` · number | IPFS API port / Puerto API de IPFS<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 5001 | min=1; max=65535 |
| `runtime.IPFS_GATEWAY_PORT` · number | IPFS gateway port / Puerto de pasarela IPFS<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 8081 | min=1; max=65535 |
| `runtime.IPFS_SWARM_PORT` · number | IPFS peer port / Puerto de pares IPFS<br>Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes. / Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker. | Repository default: 4001 | min=1; max=65535 |

**Contextual exits:** [Return to Settings / Volver a Ajustes](workflow-prototype.html?screen=settings); [Return to setup / Volver a configuración](workflow-prototype.html?screen=setup).

<a id="recordings"></a>

**Simplified location:** Your recordings → Your recordings. **Composition:** primary destination. **Canonical editor:** `recordings`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Your recordings / Tus grabaciones

[Open composition](workflow-prototype.html?screen=recordings) · existing route/context: `/recordings` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Upcoming captures and saved files have different actions. / Las capturas próximas y archivos guardados tienen acciones diferentes.

**Evidence:** [Recordings.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Recordings.tsx)

**Permission:** recordings; action permission separately checked. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Contextual exits:** [Schedule recording / Programar grabación](workflow-prototype.html?screen=recording-schedule); [Recording settings / Ajustes de grabación](workflow-prototype.html?screen=recording-settings).

### Find a recording / Buscar grabación

**Save timing:** explicit action. **Action:** Apply filters / Aplicar filtros. **Boundary:** `recordingService.list`. View/preview only; no persistent data mutation.

**Consequence:** Only the visible recording list changes. / Solo cambia la lista visible.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `recording.search` · search | Search recordings / Buscar grabaciones<br>Search original title or channel; reset page when changed. / Busca título o canal original; vuelve a primera página. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `recording.state` · select | Status / Estado<br>Status labels include words, never color alone. / Estados con texto, nunca solo color. | Load current saved/server value; illustrative fixture:  |  → All recordings / Todas; scheduled → Scheduled / Programada; starting → Starting / Iniciando; recording → Recording / Grabando; recovering → Recovering / Recuperando; finalizing → Finalizing / Finalizando; completed → Completed / Completada; partial → Partial / Parcial; failed → Failed / Fallida; missed → Missed / No iniciada; cancelled → Cancelled / Cancelada; deleting → Deleting / Eliminando; deleted → Deleted / Eliminada |

**Recordings · synthetic / Grabaciones · ficticias**

- Coastlines: the Atlantic / Coastlines: the Atlantic: Recovering · 18 min captured · 21:00 end / Recuperando · 18 min capturados · fin 21:00 [Open related workflow](workflow-prototype.html?screen=recording-active).
- Inside the studio / Inside the studio: Scheduled tomorrow · cancel keeps existing files / Programada mañana · cancelar conserva archivos [Open related workflow](workflow-prototype.html?screen=recording-cancel).
- World in focus / World in focus: Completed · protected · 2 parts / Completada · protegida · 2 partes [Open related workflow](workflow-prototype.html?screen=recording-parts).
- Morning report / Morning report: Missed · no eligible source · no media promised / No iniciada · sin fuente apta · sin prometer archivo [Open related workflow](workflow-prototype.html?screen=recording-storage).

**Contextual exits:** [Schedule a programme / Programar programa](workflow-prototype.html?screen=recording-schedule); [Recording settings / Ajustes de grabación](workflow-prototype.html?screen=recording-settings); [Deletion review / Revisar eliminación](workflow-prototype.html?screen=recording-delete).

<a id="channel-activity"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `channel-activity`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Stream activity / Actividad de emisión

[Open composition](workflow-prototype.html?screen=channel-activity) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Read provenance and lifecycle without confusing it with current signal. / Consulta origen e historial sin confundirlo con señal actual.

**Evidence:** [ChannelActivityLogDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelActivityLogDialog.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Northlight HD / Northlight HD**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Identifier / Identificador | 0000000000000000000000000000000000000000 / 0000000000000000000000000000000000000000 |
| Source / Fuente | Family channels / Family channels |

**Recent activity · synthetic / Actividad reciente · ficticia**

- 16:12 · verified online / 16:12 · señal verificada: Media packets identified; 12 peers observed / Paquetes identificados; 12 pares observados [Open related workflow](workflow-prototype.html?screen=stream-stats).
- 16:00 · imported / 16:00 · importada: Source import updated metadata; no online claim / Importación actualizó datos; no afirma señal
- Yesterday · inactive / Ayer · inactiva: Source no longer published the ID; retained history / Fuente dejó de publicar ID; historial conservado

**Contextual exits:** [Edit metadata / Editar datos](workflow-prototype.html?screen=stream-edit).

<a id="stream-bulk-fields"></a>

**Simplified location:** TV channels → Streams. **Composition:** contextual editor or detail. **Canonical editor:** `stream-bulk-fields`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Bulk metadata changes / Cambios de datos en lote

[Open composition](workflow-prototype.html?screen=stream-bulk-fields) · existing route/context: `/acestream-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Only selected fields are sent; blank and unchanged are different. / Solo se envían campos seleccionados; vacío y sin cambios son distintos.

**Evidence:** [AcestreamChannels.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/AcestreamChannels.tsx); [BulkOperations.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/BulkOperations.tsx); [channelService.ts](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/services/channelService.ts); [channel.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/schemas/channel.py); [channels.py](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/backend/app/api/endpoints/channels.py)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Explanation:** Synthetic selection: 2 explicit stream IDs. Review the exact selection after filtering; do not silently select the entire catalogue. / Selección ficticia: 2 IDs explícitos. Revisa selección tras filtrar; no selecciones todo el catálogo en silencio.

### Fields to change / Campos que cambiar

**Save timing:** explicit action. **Action:** Review bulk changes / Revisar cambios. **Boundary:** `BulkChannelEditRequest`. Submit this resource only; other sections retain independent state.

**Consequence:** Report success and failed IDs separately. No implicit online status editing. / Informa correctos y fallidos por ID. Sin editar estado de señal implícitamente.

**Confirmation:** Apply only the explicitly selected fields to these 2 streams? Unselected fields remain untouched. / ¿Aplicar solo los campos seleccionados a estas 2 emisiones? Los demás se conservan.. Cancel initially focused; Escape cancels; return focus to invoker.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `bulk.apply_name` · checkbox | Change Name / Cambiar Nombre<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.name` · text | Name / Nombre<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=True; enabled when bulk.apply_name is on |
| `bulk.apply_group` · checkbox | Change Group / Cambiar Grupo<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.group` · text | Group / Grupo<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=False; enabled when bulk.apply_group is on |
| `bulk.apply_logo` · checkbox | Change Logo URL / Cambiar URL de logo<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.logo` · text | Logo URL / URL de logo<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=False; enabled when bulk.apply_logo is on |
| `bulk.apply_tvg_id` · checkbox | Change TVG ID / Cambiar TVG ID<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.tvg_id` · text | TVG ID / TVG ID<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=False; enabled when bulk.apply_tvg_id is on |
| `bulk.apply_tvg_name` · checkbox | Change TVG name / Cambiar Nombre TVG<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.tvg_name` · text | TVG name / Nombre TVG<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=False; enabled when bulk.apply_tvg_name is on |
| `bulk.apply_source_url` · checkbox | Change Source URL / Cambiar URL de fuente<br>Unchecked keeps each stream’s own value. / Sin marcar conserva el valor propio. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |
| `bulk.source_url` · text | Source URL / URL de fuente<br>Blank explicitly clears this selected field; name must remain nonempty. / Vacío borra explícitamente este campo; nombre no puede quedar vacío. | Load current saved/server value; illustrative fixture:  | required=False; enabled when bulk.apply_source_url is on |
| `bulk.is_active` · select | Playlist visibility / Visibilidad en lista<br>Choose explicitly; unchanged leaves each current value. / Elige explícitamente; sin cambios conserva valores. | Load current saved/server value; illustrative fixture:  |  → Unchanged / Sin cambios; true → Show / Mostrar; false → Hide / Ocultar |
| `bulk.epg_update_protected` · select | Protect guide metadata / Proteger datos de guía<br>This does not protect the file from deletion. / No protege un archivo frente a eliminación. | Load current saved/server value; illustrative fixture:  |  → Unchanged / Sin cambios; true → Protect / Proteger; false → Allow updates / Permitir actualizaciones |

**Contextual exits:** [Selection and deletion / Selección y eliminación](workflow-prototype.html?screen=stream-bulk).

### TV-channel properties / Propiedades del canal de TV

**Save timing:** explicit action. **Action:** Review linked TV channel / Revisar canal TV vinculado. **Boundary:** `source-only contract mismatch → TVChannelUpdate`. View/preview only; no persistent data mutation.

**Consequence:** No stream metadata write. Review the TV-channel editor before changing shared properties. / No escribe datos de emisión. Revisa editor TV antes de cambiar propiedades compartidas.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `bulk.category` · text | Category / Categoría<br>This belongs to the linked TV channel. Open its editor to change it. / Pertenece al canal de TV vinculado. Abre su editor para cambiarlo. | Load current saved/server value; illustrative fixture: Documentary | readonly=True; Adapter/contract note: Belongs to the linked TV channel. Current stream bulk form exposes this without a matching stream request field; use the TV-channel editor. / Pertenece al canal de TV. El formulario actual lo muestra sin campo equivalente en solicitud de emisión; usa editor de TV. |
| `bulk.country` · text | Country / País<br>Choose the linked TV channel before editing; several selected streams may share it. / Elige canal TV antes de editar; varias emisiones pueden compartirlo. | Load current saved/server value; illustrative fixture: ES | readonly=True |
| `bulk.language` · text | Language / Idioma<br>Preserve original saved code and change once for the selected TV channel. / Conserva código guardado y cambia una vez para canal TV elegido. | Load current saved/server value; illustrative fixture: es | readonly=True |

<a id="guide-inventory"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** contextual editor or detail. **Canonical editor:** `guide-inventory`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Browse guide channels / Consultar canales de guía

[Open composition](workflow-prototype.html?screen=guide-inventory) · existing route/context: `/epg?tab=channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Keep source identity visible while browsing matching names. / Mantén fuente visible al consultar nombres parecidos.

**Evidence:** [EPGChannelInventoryTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/EPGChannelInventoryTable.tsx); [ScheduleView.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/epg/ScheduleView.tsx); [EPG.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/EPG.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Browse / Consultar

**Save timing:** explicit action. **Action:** Apply view / Aplicar vista. **Boundary:** `epgService inventory`. View/preview only; no persistent data mutation.

**Consequence:** Browse only; no assignment or refresh. / Solo consulta; sin asignar ni actualizar.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `guide.filter_source` · select | Guide source / Fuente de guía<br>Show the guide source next to each name, including when viewing all sources. / La fuente aparece junto a cada nombre, también al ver todas las fuentes. | Load current saved/server value; illustrative fixture:  | Adapter/contract note: All sources retains source-qualified rows. / Todas mantiene filas identificadas por fuente.;  → All sources / Todas; 1 → Sample guide / Sample guide; 2 → Regional guide / Regional guide |
| `guide.search` · search | Search names / Buscar nombres<br>Filter original guide names. / Filtra nombres originales. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `guide.day` · date | Schedule day / Día de programación<br>Uses display timezone; unknown or missing listings stay explicit. / Usa zona de visualización; faltas quedan explícitas. | Load current saved/server value; illustrative fixture: 2026-11-08 | No additional prototype constraint; preserve current source validation. |

**Guide identities / Identidades de guía**

- Northlight · Sample guide / Northlight · Sample guide: northlight.example · linked · 8 Nov listings / northlight.example · vinculado · programas 8 nov [Open related workflow](workflow-prototype.html?screen=guide-detail).
- Atelier · Regional guide / Atelier · Regional guide: atelier.example · not linked · ambiguous name / atelier.example · sin vínculo · nombre ambiguo [Open related workflow](workflow-prototype.html?screen=guide-choice).

**Contextual exits:** [Review matching / Revisar coincidencias](workflow-prototype.html?screen=guide-match); [Matching rules / Reglas de coincidencia](workflow-prototype.html?screen=guide-rule).

<a id="player-picker"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `player-picker`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Choose what to play / Elegir qué reproducir

[Open composition](workflow-prototype.html?screen=player-picker) · existing route/context: `shared player dialog` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** A TV channel can use alternatives; a single stream cannot. / Un canal de TV puede usar alternativas; una emisión individual no.

**Evidence:** [ChannelPickerDialog.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/ChannelPickerDialog.tsx)

**Permission:** live / channels media capability. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Catalogue choice / Elección de catálogo

**Save timing:** explicit action. **Action:** Search catalogue / Buscar en catálogo. **Boundary:** `player channel picker`. View/preview only; no persistent data mutation.

**Consequence:** Show matches only. Choosing a result is a separate playback intent. / Solo muestra resultados. Elegir uno es intención independiente.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `picker.mode` · select | What to pick / Qué elegir<br>Names remain original. Permission and availability still apply. / Nombres originales. Se aplican permisos y disponibilidad. | Load current saved/server value; illustrative fixture: tv | tv → TV channels / Canales de TV; streams → Individual streams / Emisiones individuales |
| `picker.search` · search | Channel / Canal<br>Search before selecting; loading does not stop current viewing. / Busca antes de elegir; cargar no detiene reproducción. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Choose a result / Elegir resultado:** Switching releases the current viewer and starts the selected channel; filtering alone does neither. / Cambiar libera espectador actual e inicia canal elegido; filtrar no hace ninguna.

No automatic selection. Exactly one choice. Show row-specific result; expire selection on review-token/revision changes.

**Contextual exits:** [Return to Live TV / Volver a TV en directo](workflow-prototype.html?screen=live).

<a id="player-sessions"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `player-sessions`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Playback sessions / Sesiones de reproducción

[Open composition](workflow-prototype.html?screen=player-sessions) · existing route/context: `shared player controls` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Closing your player releases your viewer; other viewers keep their session. / Cerrar tu reproductor libera tu espectador; los demás conservan sesión.

**Evidence:** [ActiveStreamsList.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/player/ActiveStreamsList.tsx)

**Permission:** live; management control may require administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Synthetic sessions / Sesiones ficticias**

- Northlight / Northlight: Direct route · 2 browser viewers · source lease owned / Ruta directa · 2 espectadores · emisión en uso [Open related workflow](workflow-prototype.html?screen=live).
- World 24 / World 24: Acexy route · cleanup belongs to Acexy / Ruta Acexy · limpieza propia de Acexy [Open related workflow](workflow-prototype.html?screen=browser-player).

**Stop this viewer / Detener este espectador:** Release only this viewer? Shared source remains while any owner still needs it. / ¿Liberar solo este espectador? La emisión continúa mientras otro la necesite.

Result copy: Viewer released once. Final stop waits for ownership and the applicable disconnect grace. / Espectador liberado una vez. Detención final respeta propiedad y plazo de desconexión.. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.

**Contextual exits:** [Choose a channel / Elegir canal](workflow-prototype.html?screen=player-picker).

<a id="dashboard-events"></a>

**Simplified location:** Watch → Watch. **Composition:** contextual editor or detail. **Canonical editor:** `dashboard-events`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Events on your home page / Eventos en tu inicio

[Open composition](workflow-prototype.html?screen=dashboard-events) · existing route/context: `/` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Browser preferences change what you see, not the event source. / Preferencias del navegador cambian la vista, no la fuente.

**Evidence:** [UpcomingEvents.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/overview/UpcomingEvents.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict, empty, filtered, partial, storage-failed. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.

- **storage-failed:** Changes apply in this tab but could not be saved for next visit. Keep your selected interests visible. / Cambios aplicados en pestaña pero sin guardar para próxima visita. Conserva intereses visibles.

### Upcoming events / Próximos eventos

**Save timing:** explicit action. **Action:** Apply home preferences / Aplicar preferencias. **Boundary:** `readEventPreferences / writeEventPreferences`. View/preview only; no persistent data mutation.

**Consequence:** Use these preferences in this browser. / Usa estas preferencias en este navegador.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `dashboard.events` · select | Events to show / Eventos que mostrar<br>All upcoming, Following or saved interests. / Todos próximos, seguidos o intereses guardados. | Load current saved/server value; illustrative fixture: all | all → All upcoming / Todos próximos; following → Following / Seguidos; interests → My interests / Mis intereses |
| `dashboard.zone` · text | Display timezone / Zona de visualización<br>Use a city timezone such as Europe/Madrid. This changes displayed times only. / Usa una zona como Europe/Madrid. Solo cambia las horas mostradas. | Load current saved/server value; illustrative fixture: Europe/Madrid | Adapter/contract note: Validate IANA zone on blur. Does not change source timezone. / Valida zona IANA al salir. No cambia zona de fuente. |
| `dashboard.sports` · text | Sports / Deportes<br>Saved interests use exact catalogue names. / Intereses usan nombres exactos. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `dashboard.competitions` · text | Competitions / Competiciones<br>Empty includes all when no interest is selected. / Vacío incluye todo si no hay intereses. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `dashboard.teams` · text | Teams / Equipos<br>Original names retained. / Se conservan nombres originales. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |

**Upcoming · synthetic / Próximos · ficticios**

- Northlight Cup / Northlight Cup: Tomorrow 20:00 · timezone Europe/Madrid / Mañana 20:00 · zona Europe/Madrid [Open related workflow](workflow-prototype.html?screen=event-detail).

**Contextual exits:** [Full agenda / Agenda completa](workflow-prototype.html?screen=events).

<a id="event-broadcasters"></a>

**Simplified location:** Event agenda → Event agenda. **Composition:** contextual editor or detail. **Canonical editor:** `event-broadcasters`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Broadcaster links / Vínculos de emisoras

[Open composition](workflow-prototype.html?screen=event-broadcasters) · existing route/context: `/events` · implementation [#319](https://github.com/Pipepito/acestream-scraper/issues/319)

**Purpose:** Review source-wide mappings without silently changing existing event corrections. / Revisa vínculos de fuente sin cambiar correcciones de eventos en silencio.

**Evidence:** [BroadcasterLinks.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/events/BroadcasterLinks.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Source-qualified mappings / Vínculos por fuente**

- Northlight · Sample events / Northlight · Sample events: 3 events · linked to Northlight TV / 3 eventos · vinculado a Northlight TV [Open related workflow](workflow-prototype.html?screen=event-mapping).
- Atelier · Regional events / Atelier · Regional events: 2 events · unresolved · choose a TV or guide identity / 2 eventos · sin resolver · elige identidad TV o guía [Open related workflow](workflow-prototype.html?screen=event-mapping).

**Explanation:** Removing a link and removing an event overlay are separate operations. The preview rechecks event revision and affected programmes. / Quitar vínculo y quitar superposición son operaciones distintas. La vista revalida revisión y programas afectados.

**Contextual exits:** [Programme overlay / Superposición de programa](workflow-prototype.html?screen=event-overlay).

<a id="setup-source"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** reuse canonical editor. **Canonical editor:** `source-web`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add your first channel source / Añadir tu primera fuente

[Open composition](workflow-prototype.html?screen=setup-source) · existing route/context: `/setup` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** Use the same guarded source editor as Sources. / Usa el mismo editor protegido de Fuentes.

**Evidence:** [SetupSources.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/setup/SetupSources.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Choose a source / Elegir fuente

**Save timing:** explicit action. **Action:** Review source editor / Revisar editor. **Boundary:** `SetupSources → source editor`. View/preview only; no persistent data mutation.

**Consequence:** Continue with the canonical source editor. Already saved sources survive leaving setup. / Continúa en editor compartido. Fuentes guardadas sobreviven al salir.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `setup.url` · url | Channel source link / Enlace de fuente<br>A website or playlist you are allowed to use. Blank is valid when choosing a broadcaster instead. / Web o lista que puedes usar. Vacío válido si eliges proveedor. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `setup.provider` · select | Broadcaster / Proveedor<br>Uses installed registry choices; selection does not fetch until you continue. / Opciones del registro instalado; no consulta hasta continuar. | Load current saved/server value; illustrative fixture:  |  → Choose a source type / Elige tipo; web → Website or playlist link / Web o lista; provider → Sample broadcaster / Proveedor ficticio |

**Contextual exits:** [Built-in broadcaster editor / Editor de proveedor integrado](workflow-prototype.html?screen=source-provider); [Skip for now / Posponer](workflow-prototype.html?screen=setup).

<a id="setup-guide"></a>

**Simplified location:** TV channels → Programme guides. **Composition:** reuse canonical editor. **Canonical editor:** `guide-source`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Optional programme guide / Guía de programación opcional

[Open composition](workflow-prototype.html?screen=setup-guide) · existing route/context: `/setup` · implementation [#318](https://github.com/Pipepito/acestream-scraper/issues/318)

**Purpose:** A guide is optional; it supplies names and times, not video. / Una guía es opcional; aporta nombres y horarios, no vídeo.

**Evidence:** [SetupGuide.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/setup/SetupGuide.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


### Choose a guide / Elegir guía

**Save timing:** explicit action. **Action:** Review guide / Revisar guía. **Boundary:** `SetupGuide → EPGSourceDialog`. View/preview only; no persistent data mutation.

**Consequence:** Reuse the shared editor; guide matching remains an explicit read-only preview first. / Reutiliza editor; vinculación empieza como vista sin cambios.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `setup.guide_name` · text | Guide name / Nombre de guía<br>Recognisable name; same validation as Programme guides. / Nombre reconocible; misma validación que Guías. | Load current saved/server value; illustrative fixture: Sample guide | No additional prototype constraint; preserve current source validation. |
| `setup.guide_url` · url | Programme guide link / Enlace de guía<br>XMLTV or supported guide URL. No fetch until explicit action. / URL XMLTV o guía admitida. Sin consulta hasta acción explícita. | Load current saved/server value; illustrative fixture:  | No additional prototype constraint; preserve current source validation. |
| `setup.saved_guide` · select | Saved programme guide / Guía guardada<br>Reuse a saved source instead of creating a duplicate. / Reutiliza fuente guardada en vez de duplicarla. | Load current saved/server value; illustrative fixture:  |  → New guide / Guía nueva; 1 → Sample guide / Sample guide |

**Contextual exits:** [Continue without a guide / Continuar sin guía](workflow-prototype.html?screen=setup); [Review channel matching / Revisar vinculación](workflow-prototype.html?screen=guide-match).

<a id="channel-inline"></a>

**Simplified location:** TV channels → TV channels. **Composition:** contextual editor or detail. **Canonical editor:** `channel-inline`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Number and favorite / Número y favorito

[Open composition](workflow-prototype.html?screen=channel-inline) · existing route/context: `/tv-channels` · implementation [#320](https://github.com/Pipepito/acestream-scraper/issues/320)

**Purpose:** Quick controls keep row actions available on desktop and phone. / Controles rápidos conservan acciones en escritorio y móvil.

**Evidence:** [ChannelNumberField.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/ChannelNumberField.tsx); [TVChannelsTable.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/components/TVChannelsTable.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, dirty, pending, success, conflict. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Read-only context: Northlight / Northlight**

| Label · EN / ES | Synthetic value or state · EN / ES |
|---|---|
| Guide identity / Identidad de guía | Sample guide : northlight.example / Sample guide : northlight.example |
| Signal / Señal | Verified 16:12 · synthetic / Verificada 16:12 · ficticia |

### Channel number / Número de canal

**Save timing:** enter-blur. **Action:** Save number / Guardar número. **Boundary:** `TVChannelUpdate.channel_number`. Submit this resource only; other sections retain independent state.

**Consequence:** Number saved. Other row actions and current filters stay available. / Número guardado. Acciones y filtros siguen disponibles.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `inline.number` · number | Number for Northlight / Número de Northlight<br>Whole number ≥0. Enter or blur saves; blank clears; Escape restores. Pending locks this field only. / Entero ≥0. Enter o salir guarda; vacío borra; Escape restaura. Pendiente bloquea solo este campo. | Load current saved/server value; illustrative fixture: 12 | min=0; step=1 |

### Favorite / Favorito

**Save timing:** immediate. **Action:** Save favorite / Guardar favorito. **Boundary:** `TVChannelUpdate.is_favorite`. Submit this resource only; other sections retain independent state.

**Consequence:** Favorite saved independently of number. / Favorito guardado independientemente del número.

| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |
|---|---|---|---|
| `inline.favorite` · checkbox | Favorite Northlight / Marcar Northlight favorito<br>Saves immediately. Failure restores last saved value and offers retry. / Guarda inmediatamente. Fallo restaura valor guardado y ofrece reintento. | Load current saved/server value; illustrative fixture: False | No additional prototype constraint; preserve current source validation. |

**Contextual exits:** [Channel details / Detalles del canal](workflow-prototype.html?screen=channel-detail); [Edit / Editar](workflow-prototype.html?screen=channel-edit); [Reorder complete catalogue / Reordenar catálogo completo](workflow-prototype.html?screen=channel-reorder); [Delete channel / Eliminar canal](workflow-prototype.html?screen=channel-delete).

<a id="sources"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** section. **Canonical editor:** `sources`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Channel sources / Fuentes de canales

[Open composition](workflow-prototype.html?screen=sources) · existing route/context: `/sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Keep your channels up to date. / Mantén tus canales al día.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Contextual exits:** [Add channels / Añadir canales](workflow-prototype.html?screen=add-channels).

**Your sources / Tus fuentes**

- Family channels / Family channels: Updated 16:00 · 3 streams · next update tomorrow / Actualizada 16:00 · 3 emisiones · próxima mañana [Open related workflow](workflow-prototype.html?screen=source-web).
- Local playlist / Local playlist: Saved · import not started / Guardada · importación sin iniciar [Open related workflow](workflow-prototype.html?screen=w3u-detail).

**Contextual exits:** [Import results / Resultados de importación](workflow-prototype.html?screen=source-results); [Saved searches / Búsquedas guardadas](workflow-prototype.html?screen=saved-search); [Excluded results / Resultados excluidos](workflow-prototype.html?screen=exclusion); [Unlinked streams / Emisiones sin fuente](workflow-prototype.html?screen=sources-orphans); [Background updates / Actualizaciones en segundo plano](workflow-prototype.html?screen=automation).

<a id="add-channels"></a>

**Simplified location:** TV channels → Channel sources. **Composition:** contextual editor or detail. **Canonical editor:** `add-channels`. The same fields/actions are used by lime, coral/navy and immersive cyan.

## Add channels / Añadir canales

[Open composition](workflow-prototype.html?screen=add-channels) · existing route/context: `/sources` · implementation [#321](https://github.com/Pipepito/acestream-scraper/issues/321)

**Purpose:** Choose where your channels come from. A programme guide can be added afterwards. / Elige de dónde vienen tus canales. Puedes añadir una guía después.

**Evidence:** [Scraper.tsx](https://github.com/Pipepito/acestream-scraper/blob/cf952afc6b4489c02b7a675ff3d634cc13d98e0b/frontend/src/pages/Scraper.tsx)

**Permission:** administrator. Preserve current server enforcement; view availability does not grant action authority.

**Rendered states:** ready, loading, error, permission, empty, filtered, partial. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.


**Choose a source / Elige una fuente**

- Website or playlist address / Dirección de web o lista: Paste a link you already have. / Pega un enlace que ya tengas. [Open related workflow](workflow-prototype.html?screen=source-web).
- Supported provider / Proveedor compatible: Use the provider’s guided form. / Usa el formulario del proveedor. [Open related workflow](workflow-prototype.html?screen=source-provider).
- W3U playlist file / Archivo de lista W3U: Review folders before importing channels. / Revisa carpetas antes de importar. [Open related workflow](workflow-prototype.html?screen=w3u).
- Find a stream / Buscar una emisión: Search, resolve and add it to a TV channel. / Busca, identifica y añade a un canal. [Open related workflow](workflow-prototype.html?screen=search).

**Contextual exits:** [Add one stream manually / Añadir una emisión a mano](workflow-prototype.html?screen=stream-edit); [Use Telegram as a source / Usar Telegram como fuente](workflow-prototype.html?screen=telegram-auth).

## Presentation-only blocks

The Watch featured area, programme cards, category navigation, recording continuation card, event category illustration and interface selector are composed by `workflow-engine.js` and styled by `presentation-presets.css`. They introduce no endpoint or permission. Watch actions enter the existing viewer lifecycle; programme details open the canonical recording/guide context. Generic art is labelled and distinct from real artwork. See [shared foundations](shared-foundations-06.md) and [resource selection](asset-selection-06.md).
