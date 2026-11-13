"""Authored, disposable design compositions. No application imports or network calls.

Run from any directory: python3 compose_workflows.py
The pinned git object supplies public schema evidence, never installation data.
"""

from pathlib import Path
import ast
from copy import deepcopy
import html
import json
import subprocess
import re
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
REV = 'cf952afc6b4489c02b7a675ff3d634cc13d98e0b'
SCREENS = []


def pair(value):
    if isinstance(value, list):
        return value
    parts = value.split('|', 1)
    return parts if len(parts) == 2 else [value, value]


def field(key, label, help, value='', kind='text', **extra):
    return dict(key=key, label=pair(label), help=pair(help), value=value, kind=kind, **extra)


def form(key, title, fields, action, effect, api, **extra):
    return dict(type='form', id=key, title=pair(title), fields=fields, action=pair(action), effect=pair(effect), api=api, **extra)


def note(text, tone='info'):
    return dict(type='note', text=pair(text), tone=tone)


def facts(title, rows):
    return dict(type='facts', title=pair(title), rows=[[pair(a), pair(b)] for a, b in rows])


def rows(title, items):
    return dict(type='rows', title=pair(title), rows=[dict(title=pair(a), text=pair(b), target=c) for a, b, c in items])


def links(*items):
    return dict(type='links', items=[dict(target=a, label=pair(b)) for a, b in items])


def code(title, text):
    return dict(type='code', title=pair(title), text=text)


def command(label, consequence, result, **extra):
    return dict(type='command', label=pair(label), consequence=pair(consequence), result=pair(result), **extra)


def choices(title, items, action, effect, **extra):
    return dict(type='choices', title=pair(title), items=[dict(id=a, title=pair(b), text=pair(c)) for a, b, c in items], action=pair(action), effect=pair(effect), **extra)


def screen(id, family, title, goal, route, source, owner, blocks, **extra):
    SCREENS.append(dict(id=id, family=family, title=pair(title), goal=pair(goal), route=route, source=source if isinstance(source, list) else [source], owner=owner, blocks=blocks, permission=extra.pop('permission', 'administrator'), **extra))


# Recording screens deliberately separate admission, capture, files and global settings.
screen(
    'recording-schedule',
    'recordings',
    'Schedule a programme|Programar una grabación',
    'Keep the programme’s exact times, or adjust them before scheduling.|Conserva el horario exacto del programa o ajústalo antes de programar.',
    '/live-tv?channel=demo',
    'frontend/src/components/recordings/RecordingDialog.tsx',
    319,
    [
        facts(
            'Coastlines: the Atlantic',
            [
                ('TV channel|Canal de TV', 'Northlight'),
                ('Programme snapshot|Horario del programa', '8 Nov 2026 · 20:00–20:45 · Europe/Madrid'),
                ('Recording source|Fuente de grabación', 'Available channel streams; may differ from the one you are watching.|Emisiones disponibles del canal; pueden diferir de la que estás viendo.'),
            ],
        ),
        form(
            'schedule',
            'Recording times|Horario de grabación',
            [
                field('recording.adjust_times', 'Adjust programme times|Ajustar horario del programa', 'Off keeps the guide’s exact instants.|Desactivado conserva los instantes exactos de la guía.', False, 'checkbox'),
                field('recording.timezone', 'Timezone|Zona horaria', 'IANA name. Browser zone for new recordings; locked when editing.|Nombre IANA. Zona del navegador para nuevas grabaciones; bloqueada al editar.', 'Europe/Madrid', contract='recordings.RecordingCreate.timezone', depends='recording.adjust_times'),
                field(
                    'recording.start_time',
                    'Start|Inicio',
                    'Allow time for the source to start. Guide changes will not move this recording.|Deja tiempo para iniciar la emisión. Los cambios de guía no moverán esta grabación.',
                    '2026-11-08T20:00',
                    'datetime-local',
                    depends='recording.adjust_times',
                    contract='recordings.RecordingCreate.start_time',
                ),
                field(
                    'recording.end_time',
                    'End|Fin',
                    'After start; at most 720 minutes. Exact programme times remain until you edit.|Posterior al inicio; máximo 720 minutos. Se conserva el horario del programa hasta que lo edites.',
                    '2026-11-08T20:45',
                    'datetime-local',
                    depends='recording.adjust_times',
                    contract='recordings.RecordingCreate.end_time',
                ),
            ],
            'Schedule recording|Programar grabación',
            '45 minutes reserved. Guide updates do not reschedule it.|45 minutos reservados. Actualizar la guía no cambia el horario.',
            'recordingService.create',
            intent=True,
        ),
        note('Needs an active TV channel with an enabled stream, recording permission and persistent storage. Opening this form records nothing.|Requiere un canal de TV activo con una emisión activada, permiso y almacenamiento persistente. Abrir el formulario no graba nada.'),
        links(('recording-dst', 'Repeated or missing clock time|Hora repetida o inexistente'), ('recording-now', 'Record now|Grabar ahora')),
    ],
    permission='recordings; management policy applies to commands',
    states={
        'capacity': 'No recording slot is available for this period. Change the time or review upcoming recordings.|No hay capacidad para este horario. Cambia la hora o revisa las próximas grabaciones.',
        'stale': 'The programme changed after you opened it. Review the saved snapshot and current guide; do not silently replace the times.|El programa cambió desde que lo abriste. Revisa la captura y la guía actual; no sustituyas el horario sin confirmación.',
    },
)
screen(
    'recording-dst',
    'recordings',
    'Choose the exact time|Elegir la hora exacta',
    'This local time happens twice when clocks go back.|Esta hora local se repite cuando se retrasa el reloj.',
    '/recordings',
    'frontend/src/utils/recordingTimes.ts',
    319,
    [
        note('Synthetic clock-change example: 25 October 2026, Europe/Madrid. The two 02:30 times are different instants.|Ejemplo del cambio de hora: 25 de octubre de 2026, Europe/Madrid. Las dos horas 02:30 son instantes distintos.', 'warning'),
        form(
            'dst',
            'Resolve both times|Precisar ambos horarios',
            [
                field(
                    'recording.start_choice',
                    'Which 02:30 start?|¿Qué inicio a las 02:30?',
                    'No choice is selected for an ambiguous edited time.|Una hora editada ambigua no tiene selección inicial.',
                    '',
                    'select',
                    options=['|Choose an instant|Elige un instante', '2026-10-25T00:30:00Z|02:30 UTC+02 · first|02:30 UTC+02 · primera', '2026-10-25T01:30:00Z|02:30 UTC+01 · second|02:30 UTC+01 · segunda'],
                    required=True,
                ),
                field(
                    'recording.end_choice',
                    'Which 02:50 end?|¿Qué fin a las 02:50?',
                    'Choose an instant after the start. We show the offset and UTC value.|Elige un instante posterior al inicio. Mostramos el desfase y el valor UTC.',
                    '',
                    'select',
                    options=['|Choose an instant|Elige un instante', '2026-10-25T00:50:00Z|02:50 UTC+02 · first|02:50 UTC+02 · primera', '2026-10-25T01:50:00Z|02:50 UTC+01 · second|02:50 UTC+01 · segunda'],
                    required=True,
                ),
            ],
            'Use these instants|Usar estos instantes',
            'The schedule uses the selected UTC instants; changing interface language does not change them.|La programación usa los instantes UTC elegidos; cambiar el idioma no los modifica.',
            'recordingService.create / edit',
            intent=True,
        ),
        note(
            'Spring gap: 29 March 2026 at 02:30 does not exist here. Keep the entered value, mark the field and require a valid time; never move it to 03:30 silently.|Salto de primavera: el 29 de marzo de 2026 a las 02:30 no existe aquí. Conserva el valor, marca el campo y exige una hora válida; nunca lo cambies a las 03:30 en silencio.'
        ),
        links(('recording-schedule', 'Back to schedule|Volver a programación')),
    ],
    states={'gap': 'This time does not exist in Europe/Madrid. Choose a time before 02:00 or from 03:00.|Esta hora no existe en Europe/Madrid. Elige una hora anterior a las 02:00 o a partir de las 03:00.'},
)
screen(
    'recording-now',
    'recordings',
    'Record now|Grabar ahora',
    'Capture this TV channel until the selected end time.|Graba este canal de TV hasta la hora elegida.',
    '/live-tv',
    'frontend/src/components/recordings/RecordingDialog.tsx',
    319,
    [
        facts('Northlight', [('Start|Inicio', 'Now · fixed when this intent opens|Ahora · fijado al abrir esta solicitud'), ('Source|Fuente', 'Selected from the TV channel’s available streams|Se elige entre las emisiones disponibles del canal')]),
        form(
            'now',
            'When should it stop?|¿Cuándo debe terminar?',
            [field('recording.end_time', 'End|Fin', '1–720 minutes from now. Server admission checks storage and capacity again.|De 1 a 720 minutos desde ahora. El servidor vuelve a comprobar espacio y capacidad.', '2026-11-07T21:00', 'datetime-local', required=True)],
            'Start recording|Iniciar grabación',
            'Recording request accepted; capture may still be starting.|Solicitud aceptada; la captura puede estar iniciándose.',
            'recordingService.create',
            intent=True,
        ),
        links(('recording-active', 'Starting and recovering|Inicio y recuperación'), ('recording-settings', 'Recording settings|Ajustes de grabación')),
    ],
)
screen(
    'recording-active',
    'recordings',
    'Recording in progress|Grabación en curso',
    'A short interruption is visible without hiding the captured parts.|Una interrupción breve queda visible sin ocultar las partes capturadas.',
    '/recordings',
    'frontend/src/pages/Recordings.tsx',
    319,
    [
        facts(
            'Coastlines: the Atlantic',
            [
                ('State|Estado', 'Recovering · trying another available source|Recuperando · probando otra emisión disponible'),
                ('Captured|Capturado', '18 min · 0.7 GiB · synthetic|18 min · 0,7 GiB · ficticio'),
                ('Planned end|Fin previsto', '21:00 · Europe/Madrid'),
                ('Gap|Interrupción', '20:18–20:20 · capture interrupted|20:18–20:20 · captura interrumpida'),
            ],
        ),
        form(
            'end',
            'Change the end time|Cambiar la hora de fin',
            [field('recording.end_time', 'End|Fin', 'Start and timezone are locked for an active recording. Save uses its current revision.|El inicio y la zona están bloqueados para una grabación activa. Se guarda con la revisión actual.', '2026-11-07T21:00', 'datetime-local')],
            'Save end time|Guardar fin',
            'The requested end changed; already captured media is retained.|Se cambió el fin solicitado; se conserva lo ya capturado.',
            'recordingService.edit',
        ),
        command(
            'Stop recording|Detener grabación',
            'Stop Coastlines: the Atlantic now? The captured part remains available if finalization succeeds.|¿Detener Coastlines: the Atlantic ahora? La parte capturada estará disponible si finaliza correctamente.',
            'Stop requested. Finalizing the captured files; this is not file deletion.|Detención solicitada. Finalizando los archivos; no se están eliminando.',
            danger=True,
        ),
        links(('recording-parts', 'Parts and gaps|Partes e interrupciones')),
    ],
    states={
        'starting': 'Waiting for an eligible source. No recorded duration is known yet.|Esperando una emisión apta. Aún no se conoce la duración grabada.',
        'finalizing': 'Capture stopped. Files are being finalized; playback is available only when a part is ready.|La captura terminó. Finalizando archivos; solo se reproducen las partes listas.',
        'interrupted': 'Restart detected. The recording journal is being recovered. Previous parts remain visible.|Se detectó un reinicio. Recuperando el registro de grabación. Las partes anteriores siguen visibles.',
    },
)
screen(
    'recording-parts',
    'recordings',
    'Parts and playback|Partes y reproducción',
    'Play each available part; the missing interval is not hidden.|Reproduce cada parte disponible; el intervalo perdido queda visible.',
    '/recordings',
    ['frontend/src/components/recordings/RecordingPlayback.tsx', 'backend/app/schemas/recordings.py'],
    319,
    [
        dict(type='player', title='Coastlines: the Atlantic', status=pair('Part 1 · ready · static player illustration|Parte 1 · lista · ilustración estática del reproductor')),
        rows(
            'Original parts|Partes originales',
            [('Part 1|Parte 1', '20:00–20:18 · 0.7 GiB · ready|20:00–20:18 · 0,7 GiB · lista', 'recording-copy'), ('Missing interval|Intervalo perdido', '20:18–20:20 · no media|20:18–20:20 · sin archivo', None), ('Part 2|Parte 2', '20:20–20:45 · 0.9 GiB · ready|20:20–20:45 · 0,9 GiB · lista', 'recording-copy')],
        ),
        choices(
            'Choose a part|Elegir parte',
            [('part1', 'Part 1|Parte 1', 'Original MPEG-TS · 18 min'), ('part2', 'Part 2|Parte 2', 'Original MPEG-TS · 25 min')],
            'Open selected part|Abrir parte seleccionada',
            'Preparing this part for browser playback. Closing releases only this viewer.|Preparando esta parte para el navegador. Cerrar libera solo este espectador.',
            single=True,
        ),
        command('Protect recording|Proteger grabación', 'Protect all saved parts from deletion and retention cleanup?|¿Proteger todas las partes frente a eliminación manual y automática?', 'Protected. Remove protection explicitly before deleting.|Protegida. Quita la protección expresamente antes de eliminar.'),
        links(('recording-delete', 'Delete files|Eliminar archivos'), ('recording-storage', 'Storage and retention|Espacio y conservación')),
    ],
    states={
        'unsupported': 'This part cannot play in the browser. Download the original or prepare a supported compatible copy.|Esta parte no se puede reproducir en el navegador. Descarga el original o prepara una copia compatible.',
        'preparing': 'Preparing playback for Part 1. Original files are unchanged.|Preparando reproducción de la Parte 1. Los originales no cambian.',
    },
)
screen(
    'recording-copy',
    'recordings',
    'Prepare a compatible copy|Preparar una copia compatible',
    'Keep the original and create an additional file for your player.|Conserva el original y crea otro archivo para tu reproductor.',
    '/recordings',
    'frontend/src/pages/Recordings.tsx',
    319,
    [
        facts('Part 1|Parte 1', [('Original', 'MPEG-TS · H.264 / AC-3 · synthetic|MPEG-TS · H.264 / AC-3 · ficticio'), ('Space|Espacio', 'The copy needs additional disk space; its final size is unknown.|La copia necesita espacio adicional; su tamaño final es desconocido.')]),
        form(
            'copy',
            'Copy type|Tipo de copia',
            [
                field(
                    'conversion.profile',
                    'Compatibility|Compatibilidad',
                    'MP4 remux keeps codecs. AAC converts audio; neither replaces the original.|MP4 conserva los códecs. AAC convierte el audio; ninguna sustituye el original.',
                    'remux',
                    'select',
                    options=['remux|MP4 · keep video and audio|MP4 · conservar vídeo y audio', 'aac|MP4 · AAC audio|MP4 · audio AAC'],
                    contract='recordings.RecordingConversion.profile',
                )
            ],
            'Prepare copy|Preparar copia',
            'Queued for preparation. Scheduled recording takes priority.|En cola de preparación. Grabar tiene prioridad.',
            'recordingService.convert',
            intent=True,
        ),
        rows(
            'Preparation|Preparación',
            [
                ('Waiting for recording|Esperando a la grabación', 'Preparation resumes when capture no longer needs the resources.|La preparación continúa cuando la captura libera los recursos.', None),
                ('Original retained|Original conservado', 'Download original remains available when no file hold prevents it.|El original sigue disponible para descargar según su estado.', None),
            ],
        ),
    ],
    states={
        'failed': 'Preparation failed. The original remains available. Retry preparation after checking storage.|La preparación falló. El original sigue disponible. Reintenta tras revisar el espacio.',
        'ready-copy': 'Compatible copy ready. Both original and copy appear under Part 1.|Copia compatible lista. El original y la copia aparecen en la Parte 1.',
    },
)
screen(
    'recording-settings',
    'recordings',
    'Recording settings|Ajustes de grabación',
    'One shared editor, reached from Recordings and Settings.|Un editor compartido, accesible desde Grabaciones y Ajustes.',
    '/settings?tab=automation',
    'frontend/src/components/recordings/RecordingSettingsFields.tsx',
    319,
    [
        note('Recording folder is deployment-owned. Example: persistent storage is available. No path is edited here.|La carpeta se configura en el despliegue. Ejemplo: hay almacenamiento persistente. Aquí no se edita la ruta.'),
        form(
            'recording-settings',
            'Capture and storage limits|Límites de captura y espacio',
            [
                field(
                    'recordings.enabled',
                    'Enable recordings|Activar grabaciones',
                    'Off by default. Disabling stops active recordings and cancels future ones; saved files remain.|Desactivado por defecto. Al desactivar se detienen las grabaciones y se cancelan las futuras; se conservan archivos.',
                    True,
                    'checkbox',
                    contract='recordings.RecordingSettings.enabled',
                ),
                field('recordings.max_concurrent', 'Simultaneous recordings|Grabaciones simultáneas', '1–4. More slots need sufficient bandwidth and storage.|1–4. Más plazas requieren ancho de banda y espacio.', 1, 'number', min=1, max=4, contract='recordings.RecordingSettings.max_concurrent'),
                field(
                    'recordings.min_free_bytes',
                    'Keep free (GiB)|Espacio libre mínimo (GiB)',
                    'Default 2 GiB; minimum 64 MiB (0.0625 GiB). API stores bytes. Low space stops capture.|Por defecto 2 GiB; mínimo 64 MiB (0,0625 GiB). La API guarda bytes. El espacio insuficiente detiene la captura.',
                    2,
                    'number',
                    min=0.0625,
                    step='any',
                    contract='recordings.RecordingSettings.min_free_bytes',
                ),
                field(
                    'recordings.max_recording_bytes',
                    'Maximum recording size (GiB)|Tamaño máximo (GiB)',
                    'Default 100 GiB; minimum 1 MiB. This is a file limit, not a duration estimate.|Por defecto 100 GiB; mínimo 1 MiB. Es un límite de tamaño, no una duración.',
                    100,
                    'number',
                    min=0.0009765625,
                    step='any',
                    contract='recordings.RecordingSettings.max_recording_bytes',
                ),
                field(
                    'recordings.retention_enabled',
                    'Delete old unprotected recordings automatically|Eliminar automáticamente grabaciones antiguas sin protección',
                    'Off keeps files until you delete them. Enabling proposes 30 days.|Desactivado conserva los archivos hasta que los elimines. Al activar se proponen 30 días.',
                    False,
                    'checkbox',
                ),
                field(
                    'recordings.retention_days',
                    'Delete after (days)|Eliminar después de (días)',
                    '1–3650. Protected, active and reader-held media cannot be deleted.|1–3650. No elimina archivos protegidos, activos o en uso.',
                    30,
                    'number',
                    min=1,
                    max=3650,
                    depends='recordings.retention_enabled',
                    contract='recordings.RecordingSettings.retention_days',
                ),
            ],
            'Save recording settings|Guardar ajustes de grabación',
            'Only recording settings are saved. Retention changes can delete eligible files on cleanup.|Solo se guardan estos ajustes. La limpieza puede eliminar archivos elegibles.',
            'recordingService.configure',
            confirm=pair(
                'Review before saving: disabling stops active recordings and cancels schedules. Retention deletes eligible unprotected files. Saved files remain when merely disabling.|Antes de guardar: desactivar detiene grabaciones y cancela programaciones. La conservación elimina archivos elegibles sin protección. Desactivar por sí solo conserva archivos.'
            ),
        ),
        links(('recording-storage', 'Review storage|Revisar almacenamiento'), ('recording-disable', 'Disable impact preview|Revisar efectos al desactivar')),
    ],
    states={'unavailable': 'Recording storage is not configured. Ask the server owner to provide a persistent RECORDINGS_DIR; settings cannot create a disk mount.|El almacenamiento no está configurado. Pide al propietario un RECORDINGS_DIR persistente; estos ajustes no crean un montaje.'},
)
screen(
    'recording-storage',
    'recordings',
    'Storage for recordings|Espacio para grabaciones',
    'Free space belongs to the recording filesystem.|El espacio libre corresponde al sistema de archivos de grabaciones.',
    '/recordings',
    'frontend/src/components/recordings/RecordingOverview.tsx',
    319,
    [
        facts(
            'Synthetic storage snapshot|Muestra ficticia de espacio',
            [('Available space|Espacio disponible', '18.4 GiB'), ('Keep free|Reserva mínima', '2 GiB'), ('Automatic deletion|Eliminación automática', 'Off|Desactivada'), ('Recorded files|Archivos grabados', '6.2 GiB · partial scan, more files may exist|6,2 GiB · exploración parcial; puede haber más archivos')],
        ),
        note('A partial scan is not the total used space. No remaining recording time is promised.|Una exploración parcial no es el total ocupado. No se promete un tiempo de grabación restante.', 'warning'),
        links(('recording-settings', 'Change limits and retention|Cambiar límites y conservación'), ('storage', 'Filesystem details|Detalles del sistema de archivos'), ('recording-parts', 'Review protected files|Revisar archivos protegidos')),
    ],
    states={'low': 'Free space is below the configured reserve. Capture stops; protected recordings remain protected.|El espacio libre está por debajo de la reserva. Se detiene la captura; las grabaciones protegidas siguen protegidas.'},
)
for id, title, body, result in [
    (
        'recording-cancel',
        'Cancel this schedule|Cancelar esta programación',
        'Coastlines: the Atlantic · 8 Nov, 20:00. This programme will not be recorded. Saved files and other schedules remain.|Coastlines: the Atlantic · 8 nov, 20:00. Este programa no se grabará. Se conservan archivos y otras programaciones.',
        'Schedule cancelled. It remains in history.|Programación cancelada. Sigue en el historial.',
    ),
    (
        'recording-delete',
        'Delete saved files|Eliminar archivos guardados',
        'Delete every original and compatible part of Coastlines: the Atlantic? This cannot be undone. The history entry remains. Protected, active or in-use media is rejected.|¿Eliminar todas las partes originales y compatibles de Coastlines: the Atlantic? Es irreversible. Se conserva el historial. Se rechazan archivos protegidos, activos o en uso.',
        'Files deleted; history remains. Space may not update until the next storage scan.|Archivos eliminados; el historial permanece. El espacio puede tardar hasta la siguiente exploración.',
    ),
    (
        'recording-disable',
        'Disable all recording|Desactivar las grabaciones',
        'Example impact: stop 1 active recording and cancel 2 schedules. Saved files remain. Recheck counts before saving; unknown counts are not zero.|Efecto de ejemplo: detener 1 grabación y cancelar 2 programaciones. Se conservan archivos. Recomprueba las cantidades; desconocido no significa cero.',
        'Recording disabled. Saved files remain available according to file state.|Grabaciones desactivadas. Los archivos guardados permanecen según su estado.',
    ),
]:
    screen(
        id,
        'recordings',
        title,
        'Review the exact consequence before continuing.|Revisa la consecuencia exacta antes de continuar.',
        '/recordings',
        'frontend/src/pages/Recordings.tsx',
        319,
        [note(body, 'warning'), command(title, body, result, danger=True), links(('recording-parts', 'Keep recording files|Conservar archivos'), ('recording-schedule', 'Upcoming schedule|Próxima programación'))],
        states={'held': 'Nothing was deleted. A file is protected, active or in use; refresh its state before retrying.|No se eliminó nada. Hay un archivo protegido, activo o en uso; actualiza su estado antes de reintentar.'} if id == 'recording-delete' else {},
    )

PERMS = [
    ('live', 'Live TV|TV en directo'),
    ('channels', 'Channels|Canales'),
    ('guide', 'Programme guide|Guía de programación'),
    ('events', 'Events|Eventos'),
    ('recordings', 'Recordings|Grabaciones'),
    ('playlists', 'Playlists|Listas de reproducción'),
    ('cast', 'Cast to my devices|Enviar a mis dispositivos'),
    ('cast_server', 'Cast to server devices|Enviar a dispositivos del servidor'),
]


def permissions(prefix, public=False):
    return [
        field(prefix + '.' + key, label, 'This feature only. Administrative access is separate.|Solo esta función. La administración es independiente.', key in ['live', 'channels', 'guide'] and not public, 'checkbox', default='false for policy; UI account seed live/channels/guide; API account default []')
        for key, label in PERMS
        if not public or key in ['live', 'channels', 'guide', 'events', 'cast']
    ]


username = field(
    'account.username',
    'Username|Usuario',
    '1–64 characters: letters, numbers, underscore, dot or hyphen. Cannot rename an existing account here.|1–64 caracteres: letras, números, guion bajo, punto o guion. Aquí no se renombra una cuenta.',
    'viewer-demo',
    required=True,
    pattern='[a-zA-Z0-9_.-]+',
    maxlength=64,
    contract='access.Credentials.username',
)
password = field(
    'account.password', 'New password|Contraseña nueva', '12–128 Unicode characters. Use a password you do not share with players.|12–128 caracteres Unicode. Usa una contraseña que no compartas con reproductores.', '', 'password', required=True, minlength=12, maxlength=128, contract='access.PasswordChange.password'
)
screen(
    'access-activate',
    'access',
    'Choose who can use this installation|Elegir quién puede usar esta instalación',
    'Accounts can be activated now or later in Settings → Access.|Las cuentas se pueden activar ahora o después en Ajustes → Acceso.',
    '/settings?tab=access',
    'frontend/src/components/access/AccountSetup.tsx',
    318,
    [
        note(
            'This synthetic example uses private-address HTTP on a home connection. Accounts are supported here; HTTP is unencrypted. Public-address HTTP is blocked.|Este ejemplo usa HTTP con dirección privada en una conexión doméstica. Admite cuentas; HTTP no cifra la conexión. HTTP con dirección pública está bloqueado.'
        ),
        form(
            'activate',
            'First administrator|Primer administrador',
            [
                field(
                    'bootstrap.enabled', 'Enable accounts|Activar cuentas', 'If off, anyone who can reach the app can manage it, subject to the existing API token.|Si se desactiva, quien acceda a la app podrá administrarla, salvo la protección del token existente.', True, 'checkbox', contract='access.Bootstrap.enabled'
                ),
                username,
                password,
                field('bootstrap.password_confirmation', 'Confirm password|Confirmar contraseña', 'Must match the new password.|Debe coincidir con la contraseña nueva.', '', 'password', required=True, equals='account.password'),
                field(
                    'bootstrap.legacy_token', 'Existing API token|Token de API existente', 'Only shown when deployment token protection exists. Sent as a header, never copied into a public URL.|Solo se muestra si existe protección de token. Se envía en cabecera, nunca en una URL pública.', '', 'password', advanced=True
                ),
                field(
                    'bootstrap.migrate_legacy_token',
                    'Keep the existing token for playback only|Conservar el token existente solo para reproducción',
                    'Required by the current activation flow when a legacy token exists. Administrative scripts need a new header credential.|Obligatorio en la activación actual si existe un token anterior. Los scripts administrativos necesitan otra credencial de cabecera.',
                    False,
                    'checkbox',
                    advanced=True,
                    contract='access.Bootstrap.migrate_legacy_token',
                ),
            ],
            'Create administrator|Crear administrador',
            'Accounts enabled. Public viewing and trusted IPTV still have separate policies.|Cuentas activadas. El acceso público y el IPTV de confianza mantienen políticas independientes.',
            'accessService.bootstrap',
            intent=True,
        ),
        links(('access-policy', 'Public viewing policy|Política de acceso público'), ('access-transport', 'Connection restrictions|Restricciones de conexión')),
    ],
    permission='bootstrap authority / legacy header; supported transport',
    states={'blocked': 'Accounts require HTTPS or the server’s private IP over a private connection. No pairing code or approval cookie is needed.|Las cuentas requieren HTTPS o la IP privada del servidor por una conexión privada. No se requiere código ni cookie de aprobación.'},
)
screen(
    'access-login',
    'access',
    'Sign in|Iniciar sesión',
    'Return to the permitted page after signing in.|Vuelve a la página permitida tras iniciar sesión.',
    '/watch',
    'frontend/src/components/access/LoginForm.tsx',
    318,
    [
        form(
            'login',
            'Your account|Tu cuenta',
            [username, field('login.password', 'Password|Contraseña', 'Enter your account password. Password reset is an owner command, not a guessed recovery link.|Introduce la contraseña de tu cuenta. El propietario puede restablecerla con un comando.', '', 'password', required=True, maxlength=128)],
            'Sign in|Iniciar sesión',
            'Signed in. Only permitted viewing features are available.|Sesión iniciada. Solo están disponibles las funciones permitidas.',
            'accessService.login',
            intent=True,
        ),
        links(('access-transport', 'Connection help|Ayuda de conexión'), ('viewer', 'Viewing permissions|Permisos de visualización')),
    ],
    permission='public sign-in',
    states={
        'expired': 'Your session expired. Sign in again. Protected data is cleared; do not replay an interrupted save automatically.|La sesión caducó. Inicia sesión otra vez. Se borran los datos protegidos; no se repite un guardado interrumpido.',
        'denied': 'Those details did not sign you in. Check the username and password; do not reveal whether an account exists.|Esos datos no permiten iniciar sesión. Revisa usuario y contraseña; no se revela si la cuenta existe.',
    },
)
screen(
    'access-account',
    'access',
    'Account permissions|Permisos de cuenta',
    'Give viewer-demo only the features they should use.|Concede a viewer-demo solo las funciones que deba usar.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        form(
            'account',
            'viewer-demo',
            [
                field('account.administrator', 'Administrator|Administrador', 'Administrators manage the installation and can use all viewing features.|Los administradores gestionan la instalación y acceden a todas las funciones.', False, 'checkbox', contract='access.AccountUpdate.administrator'),
                field(
                    'account.enabled',
                    'Account enabled|Cuenta activada',
                    'Disabling signs out this account. The last enabled administrator cannot be disabled or demoted.|Al desactivar se cierran sus sesiones. No se puede desactivar ni degradar al último administrador.',
                    True,
                    'checkbox',
                    contract='access.AccountUpdate.enabled',
                ),
                *permissions('permissions'),
            ],
            'Save account|Guardar cuenta',
            'Account updated. Its sessions are signed out and API credentials revoked when permissions change.|Cuenta actualizada. Al cambiar permisos se cierran sus sesiones y se revocan sus credenciales API.',
            'accessService.updateUser',
            confirm=pair('Changing permissions signs out viewer-demo and revokes its credentials. Players using those credentials need replacement links. Continue?|Cambiar permisos cierra las sesiones de viewer-demo y revoca sus credenciales. Los reproductores necesitan enlaces nuevos. ¿Continuar?'),
        ),
        note('No invented “remote control” permission: cast and cast_server are separate scopes. Remote access also needs the existing opt-in.|No se inventa un permiso de control remoto: cast y cast_server son ámbitos distintos. El acceso remoto requiere además la activación existente.'),
        links(('access-create', 'Create account|Crear cuenta'), ('access-sessions', 'Review sessions|Revisar sesiones')),
    ],
    states={'last-admin': 'This is the last enabled administrator. Keep it enabled and administrative, or create another administrator first. Nothing changed.|Es el último administrador activo. Mantenlo activo y administrador, o crea otro antes. No se cambió nada.'},
)
screen(
    'access-create',
    'access',
    'Create an account|Crear una cuenta',
    'Start with viewing permissions and review the exact scope.|Empieza con permisos de visualización y revisa su alcance.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        form(
            'create-account',
            'New account|Cuenta nueva',
            [username, password, field('account.administrator', 'Administrator|Administrador', 'Off by default. Giving this permission grants management access.|Desactivado por defecto. Este permiso concede administración.', False, 'checkbox'), *permissions('permissions')],
            'Create account|Crear cuenta',
            'Account created. Share its initial password through a private channel.|Cuenta creada. Comparte la contraseña inicial por un canal privado.',
            'accessService.createUser',
            intent=True,
        ),
        links(('access-account', 'Edit existing permissions|Editar permisos existentes')),
    ],
)
screen(
    'access-policy',
    'access',
    'Viewing without signing in|Ver sin iniciar sesión',
    'Public pages, IPTV clients and administrators have different access rules.|Las páginas públicas, clientes IPTV y administradores tienen reglas distintas.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        form(
            'policy',
            'Public viewing and IPTV|Acceso público e IPTV',
            [
                *permissions('public_features', True),
                field(
                    'policy.public_playlists',
                    'Allow public playlists, guides and media|Permitir listas, guías y contenido públicos',
                    'Off by default. Allows credential-free export and media routes according to policy.|Desactivado por defecto. Permite exportación y contenido sin credenciales según la política.',
                    False,
                    'checkbox',
                    contract='access.AccessPolicy.public_playlists',
                ),
                field(
                    'policy.local_iptv',
                    'Allow IPTV on trusted local networks|Permitir IPTV en redes locales de confianza',
                    'A proxy or Docker gateway alone is not evidence of local IPTV access.|Un proxy o una pasarela Docker por sí solos no prueban acceso IPTV local.',
                    False,
                    'checkbox',
                    contract='access.AccessPolicy.local_iptv',
                ),
                field(
                    'policy.local_networks',
                    'Trusted IPTV client networks|Redes de clientes IPTV de confianza',
                    'Comma-separated CIDRs; at most 16. Separate from proxy trust and Cast home networks.|CIDR separados por comas; máximo 16. Independientes de la confianza de proxy y de las redes Cast.',
                    '',
                    'text',
                    depends='policy.local_iptv',
                    contract='access.AccessPolicy.local_networks',
                ),
            ],
            'Save viewing policy|Guardar política de acceso',
            'Only viewing policy saved. Account permissions and reverse-proxy trust are unchanged.|Solo se guardó la política. Los permisos y la confianza de proxy se mantienen.',
            'accessService.savePolicy',
            confirm=pair('Review the selected public features and networks before making them accessible without sign-in.|Revisa las funciones y redes seleccionadas antes de permitir el acceso sin sesión.'),
        ),
        links(('casting-settings', 'Casting permissions and trust|Permisos y confianza de Cast'), ('network', 'Reverse proxies and tuner access|Proxies y acceso al sintonizador')),
    ],
)
screen(
    'access-password',
    'access',
    'Change your password|Cambiar tu contraseña',
    'This signs out your sessions and revokes your API credentials.|Se cerrarán tus sesiones y se revocarán tus credenciales API.',
    '/settings?tab=access',
    'frontend/src/components/access/PasswordForm.tsx',
    318,
    [
        form(
            'password',
            'Verify and replace|Verificar y sustituir',
            [
                field('password.current_password', 'Current password|Contraseña actual', 'Required to authorize the change.|Necesaria para autorizar el cambio.', '', 'password', required=True),
                password,
                field('password.password_confirmation', 'Confirm new password|Confirmar contraseña nueva', 'Must match exactly; count Unicode characters, not UTF-16 units.|Debe coincidir exactamente; cuenta caracteres Unicode, no unidades UTF-16.', '', 'password', required=True, equals='account.password'),
            ],
            'Change password|Cambiar contraseña',
            'Password changed. Sign in again and replace revoked playback/API credentials.|Contraseña cambiada. Inicia sesión y sustituye las credenciales revocadas.',
            'accessService.password',
            intent=True,
            confirm=pair('Continue and sign out every session for this account? All its API credentials will be revoked.|¿Continuar y cerrar todas las sesiones de esta cuenta? Se revocarán todas sus credenciales API.'),
        )
    ],
    permission='signed-in account; own password',
)
screen(
    'access-sessions',
    'access',
    'Login sessions|Sesiones iniciadas',
    'Review the last activity and expiry before signing a session out.|Revisa la actividad y caducidad antes de cerrar una sesión.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        rows(
            'Sessions · synthetic|Sesiones · ficticias',
            [
                ('viewer-demo · this session|viewer-demo · esta sesión', 'Created 7 Nov 16:00 · last active 16:18 · expires 8 Nov 16:00|Creada 7 nov 16:00 · activa 16:18 · caduca 8 nov 16:00', None),
                ('viewer-demo · another session|viewer-demo · otra sesión', 'Created 6 Nov 09:00 · last active 7 Nov 12:00|Creada 6 nov 09:00 · activa 7 nov 12:00', None),
            ],
        ),
        command(
            'Sign out this session|Cerrar esta sesión',
            'Sign out this session? You will return to Sign in. No other session is selected.|¿Cerrar esta sesión? Volverás al inicio de sesión. No se selecciona ninguna otra.',
            'Session signed out. Protected information is cleared.|Sesión cerrada. Se borran los datos protegidos.',
        ),
        command('Sign out the other session|Cerrar la otra sesión', 'Sign out the selected session for viewer-demo?|¿Cerrar la sesión seleccionada de viewer-demo?', 'Selected session signed out.|Sesión seleccionada cerrada.'),
        links(('access-credentials', 'Playback and API credentials|Credenciales IPTV y API')),
    ],
    states={'empty': 'No sessions were returned. Refresh before interpreting this as successful revocation.|No se devolvieron sesiones. Actualiza antes de interpretarlo como una revocación correcta.'},
)
screen(
    'access-credentials',
    'access',
    'Playback and API credentials|Credenciales de reproducción y API',
    'Create the smallest access scope your client needs.|Crea el ámbito mínimo que necesite tu cliente.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        form(
            'credential',
            'New credential|Credencial nueva',
            [
                field('credential.label', 'Credential label|Nombre de credencial', '1–80 characters; use a recognisable client name.|1–80 caracteres; usa un nombre de cliente reconocible.', 'Demo player', required=True, maxlength=80, contract='access.CredentialCreate.label'),
                field(
                    'credential.kind',
                    'Access|Acceso',
                    'Playback credentials may be used in IPTV URLs. Administrative credentials belong only in headers.|Las de reproducción pueden ir en URLs IPTV. Las administrativas solo van en cabeceras.',
                    'playback',
                    'select',
                    options=['playback|Playback only|Solo reproducción', 'admin|Administrative API|API administrativa'],
                    contract='access.CredentialCreate.kind',
                ),
            ],
            'Create credential|Crear credencial',
            'Created. The next screen shows it once. Do not include it in screenshots or support reports.|Creada. La siguiente pantalla la muestra una vez. No la incluyas en capturas o informes.',
            'accessService.issueCredential',
            intent=True,
            next='access-secret',
        ),
        command(
            'Revoke Demo player|Revocar Demo player',
            'This credential stops working. Reload IPTV clients with a replacement URL; no undo is available.|Esta credencial dejará de funcionar. Recarga los clientes IPTV con una URL nueva; no se puede deshacer.',
            'Credential revoked. Existing URLs need replacement.|Credencial revocada. Hay que sustituir las URLs.',
            danger=True,
        ),
    ],
)
screen(
    'access-secret',
    'access',
    'Save your new credential|Guardar la credencial nueva',
    'Shown once. The value below is deliberately not a usable credential.|Se muestra una vez. El valor inferior no es una credencial utilizable.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        code('New credential · placeholder|Credencial nueva · ejemplo', 'DEMO — NOT A CREDENTIAL'),
        dict(type='copy', label=pair('Copy example value|Copiar valor de ejemplo'), value='DEMO — NOT A CREDENTIAL'),
        command(
            'Dismiss credential|Ocultar credencial',
            'After dismissal you cannot reveal this credential again. Create a new one if you lose it.|Tras ocultarla no podrás volver a verla. Crea otra si la pierdes.',
            'Credential hidden. Only its label and scope remain.|Credencial oculta. Solo quedan su nombre y ámbito.',
            next='access-credentials',
        ),
        note('Copy failure must leave the value selectable and visible. Never place a secret in the page URL, analytics or persistent browser preferences.|Si falla la copia, el valor sigue visible y seleccionable. Nunca se guarda en la URL, analítica o preferencias persistentes.'),
    ],
    states={'copy-failed': 'Copy is unavailable. Select the displayed value and copy it manually before dismissing.|No se puede copiar. Selecciona el valor y cópialo manualmente antes de ocultarlo.'},
)
screen(
    'access-disable',
    'access',
    'Remove account protection|Quitar la protección de cuentas',
    'This is different from disabling one account.|Esto es distinto de desactivar una cuenta.',
    '/settings?tab=access',
    'frontend/src/components/access/AccessSettings.tsx',
    318,
    [
        note('All accounts and their credentials will be removed. Anyone who can reach the app can manage it unless deployment API-token protection remains.|Se eliminarán todas las cuentas y credenciales. Quien acceda podrá administrar la app salvo que siga protegida por el token del despliegue.', 'warning'),
        form(
            'disable-access',
            'Confirm removal|Confirmar retirada',
            [
                field('access.confirm', 'I understand account protection will be removed|Entiendo que se quitará la protección de cuentas', 'This does not delete the channel catalogue.|No elimina el catálogo de canales.', False, 'checkbox', required=True),
                field('access.current_password', 'Administrator password|Contraseña de administrador', 'Required. The independent access store is not a catalogue backup.|Obligatoria. El almacén independiente de acceso no es una copia del catálogo.', '', 'password', required=True),
            ],
            'Disable user management|Desactivar gestión de usuarios',
            'Account protection removed. Existing deployment token policy still applies.|Protección de cuentas retirada. Sigue vigente la política del token del despliegue.',
            'accessService.disable',
            intent=True,
            danger=True,
            confirm=pair('Remove every account and credential? This cannot be undone from the catalogue backup.|¿Eliminar todas las cuentas y credenciales? No se recuperan desde una copia del catálogo.'),
        ),
    ],
)
screen(
    'access-transport',
    'access',
    'Use a supported connection|Usar una conexión compatible',
    'Use the right connection for the action you need.|Usa la conexión adecuada para la acción que necesitas.',
    '/settings?tab=access',
    'frontend/src/components/access/AccountTransportNotice.tsx',
    318,
    [
        facts(
            'Connection rules|Reglas de conexión',
            [
                ('Accounts|Cuentas', 'HTTPS, or private-IP HTTP over a private connection, including Docker NAT.|HTTPS o HTTP con IP privada por una conexión privada, incluido NAT de Docker.'),
                ('Public-address HTTP|HTTP con dirección pública', 'Accounts blocked, even if this address is trusted for Cast.|Cuentas bloqueadas, aunque la dirección sea de confianza para Cast.'),
                ('Telegram authorization|Autorización Telegram', 'HTTPS or localhost plus the dedicated Telegram header token.|HTTPS o localhost y el token de cabecera de Telegram.'),
                ('IPTV clients|Clientes IPTV', 'Separate local-network and playback-credential policy.|Política independiente de redes y credenciales de reproducción.'),
            ],
        ),
        links(('access-login', 'Return to sign in|Volver al inicio de sesión'), ('public-address', 'Review player address|Revisar dirección para reproductores')),
    ],
    permission='informational; no network action',
)

FILTERS = [
    field('filter.search', 'Search|Buscar', 'Filters the complete catalogue before pagination.|Filtra el catálogo completo antes de paginar.', '', 'search'),
    field('filter.category', 'Category|Categoría', 'All categories by default. Original category names are preserved.|Todas por defecto. Se conservan los nombres originales.', '', 'select', options=['|All categories|Todas las categorías', 'Documentary|Documentary|Documentary', 'News|News|News']),
    field('filter.status', 'Status|Estado', 'Unknown is different from offline.|Desconocido es distinto de sin señal.', '', 'select', options=['|Any status|Cualquier estado', 'online|Verified signal|Señal verificada', 'offline|Offline|Sin señal', 'unknown|Unknown|Desconocido']),
    field('filter.favorite', 'Favorites only|Solo favoritos', 'Favorites belong to TV channels.|Los favoritos pertenecen a canales de TV.', False, 'checkbox'),
]
screen(
    'channels',
    'channels',
    'TV channels|Canales de TV',
    'Organize channels without losing their streams or guide links.|Organiza los canales conservando sus emisiones y vínculos de guía.',
    '/tv-channels',
    'frontend/src/pages/TVChannels.tsx',
    320,
    [
        form(
            'channel-filter',
            'Find channels|Buscar canales',
            FILTERS
            + [
                field('filter.country', 'Country|País', 'Optional original country code.|Código de país original opcional.', '', advanced=True),
                field('filter.language', 'Language|Idioma', 'Channel audio language, not interface language.|Idioma de audio del canal, no de la interfaz.', '', advanced=True),
                field('filter.active', 'Visibility|Visibilidad', 'Active and hidden channels remain manageable.|Se pueden gestionar canales activos y ocultos.', '', 'select', options=['|Any|Cualquiera', 'true|Active|Activo', 'false|Hidden|Oculto'], advanced=True),
            ],
            'Apply filters|Aplicar filtros',
            'Filters applied. The playing channel is retained.|Filtros aplicados. Se conserva el canal en reproducción.',
            'local URL / catalogue query',
            local=True,
        ),
        rows(
            'Catalogue · 3 synthetic channels|Catálogo · 3 canales ficticios',
            [('1 · Northlight', 'Favorite · verified 16:00 · Documentary|Favorito · verificado 16:00 · Documentary', 'channel-detail'), ('2 · World 24', 'Unknown · News|Desconocido · News', 'channel-detail'), ('3 · Atelier', 'Offline · checked yesterday|Sin señal · comprobado ayer', 'channel-detail')],
        ),
        links(('channel-edit', 'Add or edit a TV channel|Añadir o editar canal'), ('channel-reorder', 'Reorder complete catalogue|Reordenar catálogo completo'), ('stream-match', 'Review stream matches|Revisar coincidencias de emisiones')),
    ],
    states={'filtered': 'No channels match these filters. Clear filters to see the catalogue; this does not stop playback.|Ningún canal coincide. Quita filtros para ver el catálogo; no se detiene la reproducción.'},
)
CHANNEL_FIELDS = [
    field('tv.name', 'Channel name|Nombre del canal', 'Required. Preserve the channel’s own name in both languages.|Obligatorio. Conserva el nombre propio en ambos idiomas.', 'Northlight', required=True),
    field('tv.channel_number', 'Channel number|Número de canal', 'Blank clears the number. Inline inventory edits save on Enter or blur; this form saves with its button.|Vacío borra el número. En la lista se guarda con Intro o al salir; aquí se guarda con el botón.', 1, 'number'),
    field('tv.category', 'Category|Categoría', 'Original catalogue value.|Valor original del catálogo.', 'Documentary'),
    field('tv.is_active', 'Active|Activo', 'Hidden channels remain stored.|Los canales ocultos siguen guardados.', True, 'checkbox'),
    field('tv.is_favorite', 'Favorite|Favorito', 'Stored with this TV channel, not in this browser.|Se guarda con el canal, no en este navegador.', True, 'checkbox'),
]
CHANNEL_EXTRA = [
    field('tv.description', 'Description|Descripción', 'Optional channel description; preserve original text.|Descripción opcional; conserva su texto original.', '', kind='textarea', advanced=True),
    field('tv.logo_url', 'Logo URL|URL del logotipo', 'Optional. A failed image must not hide the channel name.|Opcional. Si falla la imagen, el nombre debe seguir visible.', 'https://images.example.invalid/northlight.png', advanced=True),
    field('tv.country', 'Country|País', 'Preserve source country or edition.|Conserva el país o edición original.', 'ES', advanced=True),
    field('tv.language', 'Language|Idioma', 'Original channel language.|Idioma original del canal.', 'es', advanced=True),
    field('tv.website', 'Website|Web', 'Optional channel website.|Web opcional del canal.', '', advanced=True),
    field('tv.epg_id', 'Guide XML ID|ID XML de guía', 'Pair with the actual guide source when identity is ambiguous.|Combina con la fuente real cuando haya ambigüedad.', 'northlight.example', advanced=True),
    field('tv.epg_source_id', 'Guide source|Fuente de guía', 'Do not choose the lowest row ID when sources collide.|No elijas el ID de fila menor si coinciden fuentes.', 'sample-guide', 'select', options=['sample-guide|Sample guide|Sample guide', 'regional-guide|Regional guide|Regional guide'], advanced=True),
]
screen(
    'channel-edit',
    'channels',
    'Edit TV channel|Editar canal de TV',
    'Keep channel identity separate from its playable streams.|Separa la identidad del canal de sus emisiones.',
    '/tv-channels/:id',
    'frontend/src/components/TVChannelFormDialog.tsx',
    320,
    [
        form('tv', 'Channel details|Datos del canal', CHANNEL_FIELDS + CHANNEL_EXTRA, 'Save channel|Guardar canal', 'Channel metadata saved. Linked streams remain separate.|Datos guardados. Las emisiones vinculadas siguen separadas.', 'tvChannelService.create / update'),
        links(('channel-detail', 'Return to channel|Volver al canal')),
    ],
)
screen(
    'channel-detail',
    'channels',
    'Northlight',
    'Choose a source, review signal, or manage guide information.|Elige una emisión, revisa la señal o gestiona la guía.',
    '/tv-channels/:id',
    'frontend/src/pages/TVChannelDetail.tsx',
    320,
    [
        facts('Channel summary|Resumen del canal', [('Number / Favorite|Número / Favorito', '1 · Yes|1 · Sí'), ('Guide|Guía', 'Sample guide : northlight.example'), ('Now / Next|Ahora / Después', 'Coastlines: the Atlantic · Inside the studio')]),
        rows('Available streams|Emisiones disponibles', [('Northlight HD', 'Verified signal · 0 peers · sample 7 Nov 16:00|Señal verificada · 0 pares · muestra 7 nov 16:00', 'stream-stats'), ('Northlight backup', 'Not checked · rates unknown|Sin comprobar · velocidades desconocidas', 'stream-stats')]),
        links(
            ('live', 'Watch / guide / record|Ver / guía / grabar'),
            ('channel-preferences', 'Preferred stream order|Orden de emisiones preferidas'),
            ('channel-assign', 'Add existing streams|Añadir emisiones existentes'),
            ('guide-detail', 'Open source-qualified guide|Abrir guía con su fuente'),
            ('channel-edit', 'Edit channel|Editar canal'),
            ('channel-delete', 'Delete channel|Eliminar canal'),
        ),
    ],
)
for sid, title, source, names, effect in [
    (
        'channel-reorder',
        'Reorder all TV channels|Reordenar todos los canales de TV',
        'frontend/src/components/TVChannelReorder.tsx',
        ['Northlight', 'World 24', 'Atelier'],
        'Consecutive numbers are saved for the complete inventory in one transaction. Cancel preserves existing numbers.|Se guardan números consecutivos para todo el inventario en una transacción. Cancelar conserva los números.',
    ),
    (
        'channel-preferences',
        'Preferred streams for Northlight|Emisiones preferidas para Northlight',
        'frontend/src/pages/TVChannelDetail.tsx',
        ['Northlight HD', 'Northlight backup', 'Northlight alternate'],
        'Preferences apply only to eligible streams; recent offline, inactive or unsupported streams stay excluded. Recent failures still deprioritize a source.|Las preferencias solo afectan a emisiones aptas; las inactivas, incompatibles o sin señal reciente siguen excluidas. Los fallos recientes reducen la prioridad.',
    ),
]:
    screen(
        sid,
        'channels',
        title,
        'Move items with arrow buttons or drag handles, then save.|Mueve elementos con flechas o arrastrando y después guarda.',
        '/tv-channels',
        source,
        320,
        [note('All 3 synthetic items are shown. Filters and pagination do not narrow this edit.|Se muestran los 3 elementos ficticios. Los filtros y la paginación no limitan esta edición.'), dict(type='reorder', names=names, effect=pair(effect)), links(('channels', 'Cancel and return|Cancelar y volver'))],
        states={'conflict': 'The inventory changed elsewhere. Nothing was saved. Reload the complete list and review your order again.|El inventario cambió en otro lugar. No se guardó nada. Recarga la lista completa y revisa el orden.'},
    )
screen(
    'streams',
    'channels',
    'Streams|Emisiones',
    'A stream is one playable source. Several can belong to one TV channel.|Una emisión es una fuente reproducible. Varias pueden pertenecer al mismo canal.',
    '/acestream-channels',
    'frontend/src/pages/AcestreamChannels.tsx',
    320,
    [
        form(
            'streams-filter',
            'Find streams|Buscar emisiones',
            FILTERS[:3]
            + [
                field('streams.source', 'Source|Fuente', 'Exact source identity; applied before count and pagination.|Identidad exacta; se filtra antes de contar y paginar.', '', 'select', options=['|All sources|Todas las fuentes', 'source-demo|Family channels|Family channels']),
                field('streams.group', 'Group|Grupo', 'Original group value.|Nombre de grupo original.', '', advanced=True),
                field('streams.active', 'Active|Activa', 'Filter enabled and disabled streams.|Filtra emisiones activadas y desactivadas.', '', 'select', options=['|Any|Cualquiera', 'true|Enabled|Activada', 'false|Disabled|Desactivada'], advanced=True),
            ],
            'Filter streams|Filtrar emisiones',
            'Catalogue filter updated.|Filtro del catálogo actualizado.',
            'channelService query',
            local=True,
        ),
        rows(
            'Signal and ownership|Señal y pertenencia',
            [
                ('Northlight HD', 'Verified signal · Family channels → Northlight|Señal verificada · Family channels → Northlight', 'stream-stats'),
                ('Atelier backup', 'Lookup found · media not verified · unassigned|ID encontrado · señal sin verificar · sin canal', 'stream-stats'),
                ('World 24 alternate', 'Check error · previous observation retained|Error al comprobar · se conserva la muestra anterior', 'stream-stats'),
            ],
        ),
        links(('stream-edit', 'Add a stream manually|Añadir una emisión manualmente'), ('stream-bulk', 'Bulk actions|Acciones en lote'), ('stream-match', 'Review name matches|Revisar coincidencias de nombre'), ('offline-cleanup', 'Offline cleanup settings|Ajustes de limpieza sin señal')),
    ],
)
screen(
    'stream-stats',
    'channels',
    'Northlight HD · observations|Northlight HD · observaciones',
    'A successful lookup is not proof that video or audio is arriving.|Encontrar el ID no demuestra que lleguen vídeo o audio.',
    '/acestream-channels',
    ['frontend/src/components/channels/StreamStatistics.tsx', 'frontend/src/components/ChannelActivityLogDialog.tsx'],
    320,
    [
        facts(
            'Last observation · synthetic|Última observación · ficticia',
            [
                ('Verified signal|Señal verificada', 'Yes · identified audio/video packets|Sí · paquetes identificados de audio/vídeo'),
                ('Engine lookup|Búsqueda en motor', 'ID found|ID encontrado'),
                ('Observed at|Observado el', '7 Nov 2026 · 16:00 UTC'),
                ('Peers|Pares', '0 · measured, not missing|0 · medido, no ausente'),
                ('Download / upload|Descarga / subida', '420 / 0 Kbytes/sec'),
                ('Encoded media bitrate|Tasa del contenido codificado', 'Unknown · different from network download rate|Desconocida · distinta de la velocidad de descarga'),
            ],
        ),
        rows('Activity|Actividad', [('16:00 · checked|16:00 · comprobada', 'Media packets verified|Paquetes de contenido verificados', None), ('15:00 · skipped|15:00 · omitida', 'Active playback protected; previous observation retained|Reproducción protegida; se conserva la muestra previa', None)]),
        command(
            'Check this stream|Comprobar esta emisión',
            'A bounded check can wait or be skipped to protect playback. Request one check?|La comprobación limitada puede esperar u omitirse para proteger la reproducción. ¿Solicitarla?',
            'Check queued. Waiting is not offline.|Comprobación en cola. Esperar no significa sin señal.',
        ),
        links(('stream-edit', 'Edit metadata|Editar datos')),
    ],
    states={
        'unknown': 'No measurement is available. Show unknown, not zero. Importing did not prove signal.|No hay medición. Muestra desconocido, no cero. Importar no demostró señal.',
        'not-found': 'The engine explicitly reported ID not found. This differs from timeout or engine error.|El motor indicó expresamente ID no encontrado. Es distinto de agotamiento de tiempo o error del motor.',
    },
)
STREAM_FIELDS = [
    field('stream.name', 'Stream name|Nombre de emisión', 'Required; original source name.|Obligatorio; nombre original de fuente.', 'Northlight HD', required=True),
    field(
        'stream.id', 'AceStream ID|ID de AceStream', '40 hexadecimal characters. Read-only after creation; never store a search infohash without resolving it.|40 caracteres hexadecimales. Solo lectura tras crear; resuelve el infohash de búsqueda antes de guardarlo.', '0' * 40, required=True, pattern='[0-9a-fA-F]{40}'
    ),
    field(
        'stream.tv_channel_id',
        'Link to TV channel|Vincular a canal de TV',
        'Optional here; shared searchable number/name/country/category picker. Add and association commit together.|Opcional aquí; selector compartido por número, nombre, país y categoría. Alta y vínculo se guardan juntos.',
        '',
        'select',
        options=['|No channel|Sin canal', '1|1 · Northlight · ES · Documentary|1 · Northlight · ES · Documentary', '2|2 · World 24 · GB · News|2 · World 24 · GB · News'],
    ),
    field('stream.group', 'Group|Grupo', 'Optional original group.|Grupo original opcional.', 'Documentary'),
    field('stream.logo', 'Logo URL|URL de logotipo', 'Optional; keeps the original URL.|Opcional; conserva la URL original.', '', advanced=True),
    field('stream.tvg_id', 'TVG ID|ID TVG', 'Guide ID written into playlists. Keep machine value intact.|ID de guía exportado en listas. Conserva su valor exacto.', 'northlight.example', advanced=True),
    field('stream.tvg_name', 'TVG name|Nombre TVG', 'Original guide name.|Nombre original de guía.', 'Northlight', advanced=True),
    field('stream.is_active', 'Show in playlist|Mostrar en listas', 'Existing editor flag; hidden streams remain stored.|Opción del editor; las emisiones ocultas siguen guardadas.', True, 'checkbox'),
    field('stream.epg_update_protected', 'Keep my guide fields|Conservar mis campos de guía', 'Protect metadata against guide updates.|Protege los datos frente a actualizaciones de guía.', False, 'checkbox'),
    field('stream.allow_excluded', 'Override this import exclusion|Ignorar esta exclusión de importación', 'Explicit manual-add exception only. Never reuse it in automatic imports.|Excepción explícita solo para alta manual. Nunca se reutiliza en importaciones automáticas.', False, 'checkbox', advanced=True),
]
screen(
    'stream-edit',
    'channels',
    'Add and link a stream|Añadir y vincular una emisión',
    'Create a stream and optionally attach it to an existing TV channel atomically.|Crea una emisión y vincúlala opcionalmente a un canal existente de forma atómica.',
    '/acestream-channels',
    ['frontend/src/components/QuickEditDialog.tsx', 'frontend/src/components/TVChannelLinkField.tsx'],
    320,
    [form('stream', 'Stream details|Datos de emisión', STREAM_FIELDS, 'Add stream|Añadir emisión', 'Stream and selected channel link saved together.|Emisión y vínculo elegidos guardados juntos.', 'channelService.create', intent=True), links(('search-add-link', 'Add from Search|Añadir desde Buscar'))],
    states={
        'conflict': 'This stream is already linked to another channel. The existing link was preserved; review it before reassignment.|Esta emisión ya está vinculada a otro canal. Se conservó el vínculo; revísalo antes de reasignar.',
        'excluded': 'An import rule excludes this stream. Only an explicit manual override may bypass it.|Una regla excluye esta emisión. Solo una excepción manual explícita permite omitirla.',
    },
)
screen(
    'stream-bulk',
    'channels',
    'Bulk stream actions|Acciones en lote',
    'Only explicitly selected streams are affected.|Solo se afectan las emisiones seleccionadas expresamente.',
    '/acestream-channels',
    ['frontend/src/components/BulkOperations.tsx', 'frontend/src/components/BatchAssignDialog.tsx'],
    320,
    [
        choices(
            'Selection|Selección',
            [('s1', 'Northlight HD', 'Family channels'), ('s2', 'Atelier backup', 'Sample catalogue')],
            'Review selected streams|Revisar emisiones seleccionadas',
            'Selection retained across pages; show total selected and hidden-by-filter count.|Se conserva la selección entre páginas; muestra el total y cuántas ocultan los filtros.',
        ),
        form(
            'bulk',
            'Apply one change|Aplicar un cambio',
            [
                field(
                    'bulk.action',
                    'Action|Acción',
                    'Unspecified metadata stays unchanged. Do not turn an empty field into a bulk clear implicitly.|Los datos no indicados se conservan. Un campo vacío no borra datos en lote implícitamente.',
                    'activate',
                    'select',
                    options=['activate|Enable|Activar', 'deactivate|Disable|Desactivar', 'group|Change group|Cambiar grupo', 'assign|Assign TV channel|Asignar canal'],
                ),
                field('bulk.group', 'New group|Grupo nuevo', 'Only sent for Change group.|Solo se envía al cambiar grupo.', 'Documentary', advanced=True),
                field('bulk.tv_channel_id', 'TV channel|Canal de TV', 'Only sent for Assign. Existing conflicting assignments require review.|Solo se envía al asignar. Los vínculos en conflicto requieren revisión.', '1', 'select', options=['1|Northlight|Northlight', '2|World 24|World 24'], advanced=True),
            ],
            'Apply selected change|Aplicar cambio seleccionado',
            'Report changed, skipped and failed rows separately; do not claim all succeeded.|Informa por separado de cambios, omisiones y fallos; no afirmes éxito total.',
            'channelService bulk commands',
            selection=True,
        ),
        command(
            'Delete selected streams|Eliminar emisiones seleccionadas',
            'Delete the selected stream records and their TV links? TV channels remain. Recheck selection and current impact.|¿Eliminar emisiones seleccionadas y sus vínculos? Se conservan canales de TV. Recomprueba selección y efecto.',
            'Selected deletion finished; review individual failures before retrying.|Eliminación terminada; revisa los fallos individuales antes de reintentar.',
            danger=True,
            selection=True,
        ),
    ],
)
screen(
    'channel-assign',
    'channels',
    'Assign existing streams|Asignar emisiones existentes',
    'Search the catalogue and select the exact sources for Northlight.|Busca en el catálogo y selecciona las emisiones exactas para Northlight.',
    '/tv-channels/:id',
    'frontend/src/components/BatchAcestreamAssignment.tsx',
    320,
    [
        choices(
            'Available streams|Emisiones disponibles',
            [('s1', 'Northlight HD', 'Unassigned · Family channels|Sin asignar · Family channels'), ('s2', 'Northlight backup', 'Currently Atelier · explicit reassignment required|Actualmente Atelier · requiere reasignación explícita')],
            'Assign selected streams|Asignar emisiones seleccionadas',
            'Show assigned, already linked and conflicting results. Moving a stream clears its previous preference position.|Muestra asignadas, ya vinculadas y conflictos. Mover una emisión borra su posición preferida anterior.',
        ),
        links(('stream-match', 'Review name suggestions|Revisar sugerencias de nombres'), ('channel-detail', 'Back to Northlight|Volver a Northlight')),
    ],
)
screen(
    'stream-match',
    'channels',
    'Match streams to TV channels|Vincular emisiones a canales de TV',
    'Similar names are optional suggestions for your review.|Los nombres parecidos son sugerencias opcionales para revisar.',
    '/tv-channels',
    'frontend/src/components/TVAutoMatchDialog.tsx',
    320,
    [
        note('This assigns streams to TV channels. It does not assign programme guides or enable exact-match automation.|Esto asigna emisiones a canales de TV. No asigna guías ni activa vinculación automática.'),
        form(
            'similar-options',
            'Suggestion options|Opciones de sugerencias',
            [
                field('matching.include_similar', 'Include similar names for review|Incluir nombres parecidos para revisar', 'Off by default; no result starts selected.|Desactivado por defecto; ningún resultado empieza seleccionado.', False, 'checkbox'),
                field('matching.assumed_country', 'Country for unlabeled entries|País para entradas sin país', 'Matching only. Explicit country and edition metadata still wins.|Solo para comparar. Los datos explícitos de país y edición tienen prioridad.', ''),
            ],
            'Refresh preview|Actualizar vista previa',
            'Preview refreshed without changing assignments.|Vista previa actualizada sin cambiar asignaciones.',
            'TVMatchOptions preview',
            local=True,
        ),
        choices(
            'Review proposed assignments|Revisar asignaciones',
            [('match1', 'Northlight HD → Northlight', 'Exact base name · country ES agrees|Nombre base exacto · coincide ES'), ('match2', 'Atelier 2 → Atelier', 'Similar name · edition differs · review required|Nombre parecido · edición distinta · requiere revisión')],
            'Apply selected assignments|Aplicar asignaciones seleccionadas',
            'One target per stream. Changing target removes its old selection; exact bulk selection respects the current filter.|Un destino por emisión. Cambiarlo quita la selección anterior; seleccionar exactas respeta el filtro.',
            single=False,
        ),
        links(('guide-match', 'Programme-guide matching is separate|La vinculación de guía es independiente')),
    ],
    states={'ambiguous': 'Northlight has two TV candidates. Select one target for that stream; do not select both or choose by row ID.|Northlight tiene dos candidatos. Elige un destino; no selecciones ambos ni elijas por ID de fila.'},
)
screen(
    'channel-delete',
    'channels',
    'Delete Northlight?|¿Eliminar Northlight?',
    'Review channel deletion separately from deleting its streams.|Revisa la eliminación del canal por separado de sus emisiones.',
    '/tv-channels',
    'frontend/src/components/TVChannelDeleteDialog.tsx',
    320,
    [
        note('The TV channel and its associations are removed. Existing stream records are retained by the channel-delete flow; source deletion has different options.|Se elimina el canal de TV y sus asociaciones. Este flujo conserva las emisiones; eliminar una fuente tiene otras opciones.', 'warning'),
        command(
            'Delete TV channel|Eliminar canal de TV',
            'Delete Northlight and its channel-specific configuration? Recheck dependent schedules and server response before claiming success.|¿Eliminar Northlight y su configuración? Recomprueba programaciones dependientes y respuesta antes de afirmar éxito.',
            'Channel removed. Refresh inventory; retained streams remain manageable.|Canal eliminado. Actualiza el catálogo; se pueden gestionar las emisiones conservadas.',
            danger=True,
        ),
    ],
)

screen(
    'guide-sources',
    'guides',
    'Programme guides|Guías de programación',
    'Add a guide, then review which channel each listing belongs to.|Añade una guía y revisa a qué canal pertenece cada programación.',
    '/epg?tab=sources',
    'frontend/src/components/EPGSourcesTable.tsx',
    320,
    [
        rows('Guide sources|Fuentes de guía', [('Sample guide', 'Enabled · updated 16:00 · 3 guide channels|Activada · actualizada 16:00 · 3 canales', 'guide-source'), ('Regional guide', 'Disabled · imported identities still exist|Desactivada · las identidades importadas siguen existiendo', 'guide-source')]),
        links(
            ('guide-source', 'Add guide source|Añadir fuente de guía'),
            ('guide-match', 'Review channel matches|Revisar coincidencias'),
            ('guide-detail', 'Browse guide channels|Consultar canales de guía'),
            ('guide-coverage', 'Coverage|Cobertura'),
            ('guide-export', 'Export XMLTV|Exportar XMLTV'),
            ('guide-rule', 'Rules|Reglas'),
        ),
    ],
)
screen(
    'guide-source',
    'guides',
    'Edit guide source|Editar fuente de guía',
    'The same editor is used in setup and guide management.|El mismo editor se usa en la configuración inicial y gestión de guías.',
    '/epg?tab=sources',
    'frontend/src/components/EPGSourceDialog.tsx',
    320,
    [
        form(
            'guide-source',
            'Source details|Datos de fuente',
            [
                field('epg.name', 'Guide name|Nombre de guía', 'Required; a recognisable source name.|Obligatorio; un nombre reconocible.', 'Sample guide', required=True),
                field('epg.url', 'Guide URL|URL de guía', 'XMLTV or a supported regional guide. Guarded fetches preserve the entire previous guide on failure.|XMLTV o una guía regional admitida. Un fallo conserva la guía anterior completa.', 'https://guide.example.invalid/listings.xml', kind='url', required=True),
                field('epg.enabled', 'Refresh this source|Actualizar esta fuente', 'Disabled sources still participate in imported-ID identity checks.|Las fuentes desactivadas siguen contando para comprobar IDs importados.', True, 'checkbox'),
            ],
            'Save guide source|Guardar fuente de guía',
            'Source saved. Refresh and reviewed matching are separate actions.|Fuente guardada. Actualizar y revisar coincidencias son acciones separadas.',
            'epgService.createSource / updateSource',
        ),
        command(
            'Refresh guide|Actualizar guía',
            'Request a bounded refresh? It may wait behind other maintenance.|¿Solicitar una actualización limitada? Puede esperar a otras tareas.',
            'Guide refresh waiting. Old listings remain until a successful import.|Actualización en espera. Se conservan los programas anteriores hasta importar correctamente.',
        ),
        command(
            'Remove guide source|Eliminar fuente de guía',
            'Remove this guide source and its imported listings? Review affected guide links; TV channels and streams are separate.|¿Eliminar esta fuente y sus programas importados? Revisa los vínculos afectados; canales y emisiones son independientes.',
            'Guide source removed; review channels without listings.|Fuente eliminada; revisa los canales sin programación.',
            danger=True,
        ),
    ],
)
screen(
    'guide-detail',
    'guides',
    'Northlight · Sample guide',
    'Source-qualified programme details and matching rules.|Programación y reglas identificadas por su fuente.',
    '/epg/channels/:id',
    'frontend/src/pages/EPGChannelDetail.tsx',
    320,
    [
        facts('Guide identity|Identidad de guía', [('Source|Fuente', 'Sample guide'), ('XML ID', 'northlight.example'), ('TV channel|Canal de TV', 'Northlight')]),
        rows(
            'Schedule · Europe/Madrid|Programación · Europe/Madrid',
            [('20:00 · Coastlines: the Atlantic', '45 min · original programme title|45 min · título original', 'recording-schedule'), ('20:45 · Inside the studio', '30 min · guide data, not verified media|30 min · datos de guía, no señal verificada', 'recording-schedule')],
        ),
        links(('guide-rule', 'Add a matching rule|Añadir regla de coincidencia'), ('guide-choice', 'Link a TV channel|Vincular canal de TV'), ('channel-edit', 'Create TV channel from guide|Crear canal de TV desde guía')),
    ],
)
screen(
    'guide-choice',
    'guides',
    'Choose the correct guide source|Elegir la fuente de guía correcta',
    'The same name can identify different channels or editions.|El mismo nombre puede identificar canales o ediciones diferentes.',
    '/epg?tab=matching',
    'frontend/src/components/EPGMatchAnalysisPanel.tsx',
    320,
    [
        choices(
            'Atelier · ambiguous match|Atelier · coincidencia ambigua',
            [('source-a', 'Atelier · Sample guide', 'ES · atelier.example · programmes 20:00/21:00|ES · atelier.example · programas 20:00/21:00'), ('source-b', 'Atelier · Regional guide', 'FR · atelier.example · programmes 20:30/21:30|FR · atelier.example · programas 20:30/21:30')],
            'Use selected identity|Usar identidad seleccionada',
            'Preserve the selected source plus XML ID. No numeric-row tie-break is allowed.|Conserva fuente e ID XML seleccionados. No se desempata por ID numérico.',
            single=True,
        ),
        links(('guide-detail', 'Inspect schedule before choosing|Revisar programación antes de elegir')),
    ],
)
screen(
    'guide-match',
    'guides',
    'Review guide matches|Revisar coincidencias de guía',
    'Preview the full source scope; explicitly select what to apply.|Revisa todas las fuentes del ámbito y selecciona qué aplicar.',
    '/epg?tab=matching',
    'frontend/src/components/EPGMatchAnalysisPanel.tsx',
    320,
    [
        form(
            'guide-scope',
            'Preview scope|Ámbito de vista previa',
            [
                field('guide.source_id', 'Guide source|Fuente de guía', 'Changing scope invalidates the old preview.|Cambiar el ámbito invalida la vista previa.', '', 'select', options=['|All sources|Todas las fuentes', 'sample|Sample guide|Sample guide']),
                field(
                    'guide.strictness',
                    'Matching level|Nivel de coincidencia',
                    'Reviewed matching only; automatic matching remains conservative and exact.|Solo para revisión; la automatización sigue siendo conservadora y exacta.',
                    'strict',
                    'select',
                    options=['strict|Strict|Estricto', 'normal|Normal|Normal', 'loose|Relaxed review|Revisión flexible'],
                ),
            ],
            'Preview matches|Ver coincidencias',
            'Preview writes nothing. Apply rechecks source scope and all imported guide IDs.|La vista previa no escribe. Aplicar revalida ámbito e IDs de todas las guías.',
            'guideSetupService preview',
            local=True,
        ),
        choices(
            'Matches|Coincidencias',
            [('guide-n', 'Northlight → Sample guide : northlight.example', 'Exact · no existing assignment changes|Exacta · no cambia asignaciones existentes'), ('guide-w', 'World 24 → Sample guide : world24.example', 'Exact · programme identity preserved|Exacta · conserva identidad de programa')],
            'Apply selected matches|Aplicar coincidencias seleccionadas',
            'Revalidate expected_previews before writing. Changed previews require a new review.|Revalida expected_previews antes de escribir. Si cambia, exige nueva revisión.',
        ),
        links(('guide-choice', 'Review ambiguous Atelier|Revisar Atelier ambiguo'), ('guide-auto', 'Automatic exact matching|Vinculación exacta automática')),
    ],
    states={'conflict': 'The source scope or preview changed. Selection is cleared; fetch and review a fresh preview. No stale row is applied.|Cambió el ámbito o la vista previa. Se borra la selección; obtén y revisa otra. No se aplica una fila obsoleta.'},
)
screen(
    'guide-rule',
    'guides',
    'Guide matching rule|Regla de coincidencia de guía',
    'Rules belong to a specific guide channel.|Las reglas pertenecen a un canal de guía concreto.',
    '/epg/channels/:id',
    'frontend/src/pages/EPGChannelDetail.tsx',
    320,
    [
        facts('Target|Destino', [('Source / channel|Fuente / canal', 'Sample guide : northlight.example')]),
        form(
            'rule',
            'Include or exclude a name|Incluir o excluir un nombre',
            [
                field('rule.search_pattern', 'Pattern|Patrón', 'Uses the existing matching pattern semantics; do not silently turn literal input into a regex.|Usa la semántica actual; no conviertas texto literal en regex sin indicarlo.', 'Northlight', required=True),
                field('rule.is_exclusion', 'Exclude this match|Excluir esta coincidencia', 'Off includes names that match; on prevents a false match.|Desactivado incluye coincidencias; activado evita una coincidencia falsa.', False, 'checkbox'),
            ],
            'Add rule|Añadir regla',
            'The next guide refresh uses the rule.|La siguiente actualización de guía usa la regla.',
            'epgService stringMappings',
            intent=True,
        ),
        command(
            'Delete rule|Eliminar regla',
            'Matching stops using this pattern from the next guide refresh.|Se deja de usar este patrón desde la siguiente actualización.',
            'Rule removed. Existing assignments are not a fresh review result.|Regla eliminada. Las asignaciones existentes no son una revisión nueva.',
            danger=True,
        ),
    ],
)
screen(
    'guide-auto',
    'guides',
    'Automatic exact matching|Vinculación exacta automática',
    'Opt in only after you understand what successful imports can change.|Activa solo después de entender qué puede cambiar tras importar.',
    '/settings?tab=automation',
    'frontend/src/components/GuideMatchingFields.tsx',
    320,
    [
        form(
            'guide-auto',
            'After successful updates|Tras actualizaciones correctas',
            [
                field(
                    'epg_matching.enabled',
                    'Enable automatic exact matching|Activar vinculación exacta automática',
                    'Off by default. Can create TV channels and assign unassigned streams after successful source or guide updates. Ambiguous names still need review.|Desactivado por defecto. Puede crear canales y asignar emisiones sin canal tras actualizar fuentes o guías. Lo ambiguo sigue necesitando revisión.',
                    False,
                    'checkbox',
                )
            ],
            'Save matching preference|Guardar preferencia',
            'Applies to future successful ingestion. Current UI saves immediately; this staged Save is a proposed interaction change requiring review.|Se aplica tras futuras importaciones correctas. La UI actual guarda al instante; este guardado por botón requiere revisión.',
            'configService epg-matching',
            confirm=pair('Enable future exact matches? Existing assignments and imported guide identities remain protected.|¿Activar futuras coincidencias exactas? Se protegen las asignaciones e identidades existentes.'),
        ),
        facts('Last result|Último resultado', [('Outcome|Resultado', 'Created 1 · assigned 2 · needs review 1|Creado 1 · asignadas 2 · requiere revisión 1'), ('Finished|Finalizado', '7 Nov 16:00 · synthetic|7 nov 16:00 · ficticio')]),
    ],
)
screen(
    'guide-export',
    'guides',
    'Export programme guide|Exportar guía de programación',
    'Use the same channel identities as your playlist.|Usa las mismas identidades de canal que tu lista.',
    '/epg?tab=export',
    'frontend/src/components/EPGXmlOutputPanel.tsx',
    320,
    [
        form(
            'xml',
            'Export options|Opciones de exportación',
            [
                field('xml.search_term', 'Search channels|Buscar canales', 'Only include matching channels.|Incluye solo canales coincidentes.', '', 'search'),
                field('xml.favorites_only', 'Favorites only|Solo favoritos', 'Uses TV-channel favorites.|Usa favoritos de canales de TV.', False, 'checkbox'),
                field('xml.days_back', 'Start of export range (days from today)|Inicio del intervalo (días desde hoy)', 'Named independently from the end. Default −1; range −14…14.|Etiqueta independiente del fin. Por defecto −1; intervalo −14…14.', -1, 'range', min=-14, max=14),
                field('xml.days_forward', 'End of export range (days from today)|Fin del intervalo (días desde hoy)', 'Default +7; range −14…14. End cannot precede start. Arrow keys change one day.|Por defecto +7; intervalo −14…14. El fin no precede al inicio. Las flechas cambian un día.', 7, 'range', min=-14, max=14),
            ],
            'Generate XMLTV|Generar XMLTV',
            'Export prepared with collision-safe IDs and validated credential propagation.|Exportación preparada con IDs sin colisiones y propagación validada de credenciales.',
            'epgService.generateXml',
            local=True,
        ),
        code('Synthetic XMLTV preview|Vista XMLTV ficticia', '<tv>\n  <channel id="sample-guide:northlight.example">\n    <display-name>Northlight</display-name>\n  </channel>\n</tv>'),
        links(('guide-coverage', 'Check coverage|Consultar cobertura'), ('playlist', 'Matching playlist|Lista correspondiente')),
    ],
)
screen(
    'guide-coverage',
    'guides',
    'Guide coverage|Cobertura de guía',
    'Missing listings are separate from missing signal.|La falta de programas es distinta de la falta de señal.',
    '/epg',
    'frontend/src/components/GuideCoverage.tsx',
    320,
    [
        facts(
            'Synthetic coverage|Cobertura ficticia',
            [('TV channels|Canales de TV', '3'), ('With source-qualified guide|Con guía identificada por fuente', '2'), ('Listings today|Programación hoy', '1 · one source could not refresh|1 · una fuente no se pudo actualizar'), ('Streams linked|Emisiones vinculadas', '4 of 6|4 de 6')],
        ),
        rows('Needs attention|Requiere atención', [('Atelier', 'Choose between two guide identities|Elige entre dos identidades de guía', 'guide-choice'), ('World 24', 'Guide linked; no programmes in the selected window|Guía vinculada; sin programas en este intervalo', 'guide-source')]),
    ],
    states={'partial': 'One guide source failed to refresh. These counts describe the last available data, not complete current coverage.|Una fuente falló. Las cifras describen los últimos datos disponibles, no la cobertura actual completa.'},
)

FORMAT_FIELDS = [
    field('format.name', 'Format name|Nombre del formato', 'Required for named formats; built-in format has no name editor.|Obligatorio en formatos propios; el integrado no permite editar el nombre.', 'Demo relay', required=True),
    field(
        'format.pattern',
        'Link pattern|Patrón del enlace',
        'Use {tv_channel_id} for a stable TV relay, {channel_id} for a stream, and optional {pid}. A plain prefix is also supported.|Usa {tv_channel_id} para un canal estable, {channel_id} para una emisión y {pid} opcional. También admite un prefijo simple.',
        'https://tv.example.invalid/app/tuner/tv/{tv_channel_id}.ts',
        required=True,
    ),
    field('format.is_default', 'Use as default|Usar por defecto', 'Setting a new default clears the old default in the same API operation.|Elegir otro predeterminado desmarca el anterior en la misma operación.', False, 'checkbox'),
]
screen(
    'playlist',
    'playlists',
    'Your playlist|Tu lista de reproducción',
    'Choose what to include, then copy the player link or download M3U.|Elige qué incluir y copia el enlace o descarga M3U.',
    '/playlist',
    ['frontend/src/components/playlist/PlaylistOptionsForm.tsx', 'frontend/src/components/playlist/PlaylistLinkPanel.tsx'],
    320,
    [
        code('Example player link · no credentials|Enlace de ejemplo · sin credenciales', 'https://tv.example.invalid/app/playlists/m3u?format=tv-relay'),
        dict(type='copy', label=pair('Copy example playlist link|Copiar enlace de ejemplo'), value='https://tv.example.invalid/app/playlists/m3u?format=tv-relay'),
        form(
            'playlist',
            'Playlist options|Opciones de lista',
            [
                field('playlist.search', 'Search channels|Buscar canales', 'Filters exported names; does not change the catalogue.|Filtra nombres exportados; no cambia el catálogo.', '', 'search'),
                field('playlist.only_online', 'Only online channels|Solo canales con señal', 'Latest verified observation is not a guarantee of present availability.|La última observación verificada no garantiza disponibilidad actual.', False, 'checkbox'),
                field('playlist.favorites_only', 'Favorite TV channels only|Solo canales favoritos', 'Unassigned streams cannot be favorites.|Las emisiones sin canal no pueden ser favoritas.', False, 'checkbox'),
                field(
                    'playlist.include_unassigned',
                    'Include unassigned streams at the end|Incluir emisiones sin canal al final',
                    'Disabled for favorites-only. Individual relay links have no TV-channel failover.|No disponible con solo favoritos. Los enlaces individuales no tienen alternativas de canal.',
                    False,
                    'checkbox',
                    unless='playlist.favorites_only',
                ),
                field(
                    'playlist.format',
                    'Stream link format|Formato de enlace',
                    'Accounts force app relay links to protect source credentials. Default uses the saved format, otherwise acestream://.|Las cuentas fuerzan enlaces de la app para proteger credenciales. Por defecto usa el formato guardado o acestream://.',
                    'tv-relay',
                    'select',
                    options=['default|Default|Predeterminado', 'tv-relay|TV channel relay|Canal de TV con alternativas', 'demo|Demo format|Formato de ejemplo'],
                ),
                field('playlist.per_source', 'List each source under its channel|Listar cada emisión bajo su canal', 'Only for TV relay formats; each source opens alone without failover.|Solo para formatos de canal; cada emisión se abre sola sin alternativas.', False, 'checkbox'),
                field('playlist.include_groups', 'Include groups|Incluir grupos', 'Repeated query parameters preserve original values, including commas inside known group names.|Los parámetros repetidos conservan valores originales y comas en nombres conocidos.', '', 'text', advanced=True),
                field('playlist.exclude_groups', 'Exclude groups|Excluir grupos', 'Exclusions remain when editing a stream format.|Se conservan exclusiones al editar un formato.', '', 'text', advanced=True),
            ],
            'Prepare M3U|Preparar M3U',
            'Export uses the chosen options and the same guide IDs as XMLTV. No source was deleted.|Usa las opciones y los mismos IDs de guía que XMLTV. No se elimina ninguna fuente.',
            'usePlaylistLink / playlistService',
            local=True,
        ),
        links(('formats', 'Manage shared stream formats|Gestionar formatos compartidos'), ('public-address', 'Address used by players|Dirección para reproductores'), ('access-credentials', 'Playback credentials|Credenciales de reproducción'), ('guide-export', 'Download matching guide|Descargar guía correspondiente')),
    ],
    states={
        'credential': 'This export needs a playback credential. Never paste an administrative header credential into a player URL.|Esta exportación necesita una credencial de reproducción. Nunca pegues una credencial administrativa en la URL.',
        'managed': 'Account policy requires relay links. The saved custom format remains stored for contexts that permit it.|La política exige enlaces de la app. Se conserva el formato propio para los contextos permitidos.',
        'filtered': 'These options produce no entries. Change filters; do not present an empty playlist as a failed server.|Estas opciones no producen entradas. Cambia filtros; una lista vacía no es un fallo del servidor.',
    },
)
screen(
    'formats',
    'playlists',
    'Stream link formats|Formatos de enlaces de emisión',
    'Shared editor used by Playlist and Settings → Stream links.|Editor compartido de Listas y Ajustes → Enlaces.',
    '/settings?tab=links',
    'frontend/src/components/StreamLinkFormatsSection.tsx',
    320,
    [
        rows('Saved formats|Formatos guardados', [('Built-in|Integrado', 'acestream:// · fallback|acestream:// · alternativa', 'format-edit'), ('Demo relay', '{tv_channel_id} · stable TV identity|{tv_channel_id} · identidad estable', 'format-edit')]),
        form('format', 'Add named format|Añadir formato', FORMAT_FIELDS, 'Save format|Guardar formato', 'Named format saved; playlist filters and selection stay in place.|Formato guardado; se mantienen los filtros y selección de lista.', 'baseUrlService.createBaseUrl', intent=True),
        form(
            'link-identifiers',
            'Advanced identifiers|Identificadores avanzados',
            [
                field('links.add_pid', 'Append PID|Añadir PID', 'Existing identifier option; keep unique direct-player PIDs and ownership rules.|Opción existente; conserva PID únicos y reglas de propiedad.', True, 'checkbox'),
                field('links.app_id', 'Use AppID|Usar AppID', 'Existing link compatibility option. Not a background-job setting.|Opción de compatibilidad de enlaces. No es un ajuste de tareas.', False, 'checkbox'),
            ],
            'Review identifier changes|Revisar cambios de identificadores',
            'Each identifier has its own existing save transaction. Report each outcome separately.|Cada identificador tiene su transacción de guardado. Informa de cada resultado por separado.',
            'configService add-pid / app-id',
            independent=True,
        ),
        links(('playlist', 'Return to playlist with filters|Volver a la lista con filtros')),
    ],
)
screen(
    'format-edit',
    'playlists',
    'Edit Demo relay|Editar Demo relay',
    'Preview the exact pattern without translating placeholders.|Revisa el patrón exacto sin traducir marcadores.',
    '/settings?tab=links',
    'frontend/src/components/StreamLinkFormatsSection.tsx',
    320,
    [
        form('edit-format', 'Pattern|Patrón', FORMAT_FIELDS[:2], 'Save pattern|Guardar patrón', 'Format updated for future generated links. Already copied links are not rewritten.|Formato actualizado para enlaces futuros. Los ya copiados no se reescriben.', 'baseUrlService.updateBaseUrl'),
        command(
            'Delete named format|Eliminar formato',
            'Delete Demo relay? Review players using this named format and show the effective fallback after removal.|¿Eliminar Demo relay? Revisa reproductores que lo usan y muestra la alternativa efectiva después.',
            'Named format removed. Refresh format selection and show the resulting effective link.|Formato eliminado. Actualiza selección y muestra el enlace efectivo.',
            danger=True,
        ),
        note('The built-in format is edited through its own pattern control and cannot be treated as a deletable named entry.|El patrón integrado se edita en su control y no se trata como una entrada propia eliminable.'),
    ],
)

SOURCE_BASE = [
    field('source.name', 'Source name (optional)|Nombre de fuente (opcional)', 'Up to 255 characters. This original name appears in source filters.|Hasta 255 caracteres. Aparece en los filtros con su nombre original.', 'Family channels', maxlength=255),
    field('source.url', 'Source address|Dirección de fuente', 'Required. Saving does not fetch or import. Preview and imports use guarded, bounded fetches.|Obligatoria. Guardar no obtiene ni importa contenido. Las consultas son protegidas y limitadas.', 'https://source.example.invalid/channels', required=True),
    field('source.enabled', 'Update this source|Actualizar esta fuente', 'Enabled by default. Disabled retains saved channels.|Activada por defecto. Desactivar conserva los canales.', True, 'checkbox'),
    field('source.scrape_bare_ids', 'Recognize bare content IDs|Reconocer IDs sin enlace', 'Off by default for ordinary sources. Broadcaster adapters disable this option.|Desactivado por defecto en fuentes comunes. Los proveedores integrados deshabilitan esta opción.', False, 'checkbox', advanced=True),
]
for sid, kind, title, detail in [
    ('source-web', 'regular', 'Web or playlist source|Fuente web o lista', 'HTTP/HTTPS pages and nested playlists keep redirect, DNS and private-network safeguards.|Las páginas HTTP/HTTPS y listas anidadas conservan las protecciones de redirección, DNS y red privada.'),
    ('source-auto', 'auto', 'Automatic source detection|Detección automática de fuente', 'The current form starts with Auto-detect. A custom recipe is optional and never proves signal.|El formulario actual empieza con detección automática. La receta es opcional y no demuestra señal.'),
    ('source-zeronet', 'zeronet', 'ZeroNet source|Fuente ZeroNet', 'Uses the configured ZeroNet gateway. Unavailable gateway is a prerequisite error, not an empty catalogue.|Usa la pasarela ZeroNet configurada. Si falta, es un requisito pendiente, no un catálogo vacío.'),
    ('source-ipfs', 'ipfs', 'IPFS source|Fuente IPFS', 'Uses the configured IPFS gateway. Preserve content identity; show bounded-fetch failures without deleting saved channels.|Usa la pasarela IPFS. Conserva la identidad; muestra fallos limitados sin borrar canales.'),
    ('source-provider', 'broadcaster', 'Built-in broadcaster|Proveedor integrado', 'Registry-backed adapters provide their own fixed address. Saving still does not import channels.|Los adaptadores del registro proporcionan su dirección fija. Guardar no importa canales.'),
]:
    fs = [dict(f) for f in SOURCE_BASE]
    if kind == 'broadcaster':
        fs.insert(
            0,
            field(
                'source.provider',
                'Built-in provider|Proveedor integrado',
                'Choose from the installed registry; unavailable registry has Retry. Existing custom names are preserved.|Elige del registro instalado; si falla, reintenta. Se conservan nombres propios.',
                'demo',
                'select',
                options=['demo|Synthetic adapter · not a real provider|Adaptador ficticio · no es real'],
            ),
        )
        fs[-1]['disabled'] = True
        fs[2]['readonly'] = True
    fs.insert(2, field('source.url_type', 'Source type|Tipo de fuente', detail, kind, 'select', options=['auto|Auto-detect|Detección automática', 'regular|Regular HTTP|HTTP común', 'zeronet|ZeroNet|ZeroNet', 'ipfs|IPFS|IPFS', 'broadcaster|Built-in broadcaster|Proveedor integrado']))
    screen(
        sid,
        'sources',
        title,
        'Save the source, then explicitly request its first import.|Guarda la fuente y solicita expresamente la primera importación.',
        '/scraper?tab=sources',
        'frontend/src/pages/Scraper.tsx',
        321,
        [
            note(detail),
            form('source', 'Source configuration|Configuración de fuente', fs, 'Save source only|Solo guardar fuente', 'Source saved; no streams imported yet.|Fuente guardada; todavía no se han importado emisiones.', 'scraperService createURL / updateURL', intent=True),
            command(
                'Save and find channels|Guardar y buscar canales',
                'Save this source, then queue one import? These are separate operations.|¿Guardar la fuente y poner una importación en cola? Son operaciones distintas.',
                'Source saved. Import waiting; if queueing fails, retry import without adding a duplicate source.|Fuente guardada. Importación en espera; si falla la cola, reintenta sin duplicar la fuente.',
                next='source-results',
            ),
            links(('helper-installed', 'Custom extraction recipe|Receta de extracción'), ('source-remove', 'Remove source|Eliminar fuente'), ('sources-orphans', 'Review orphaned streams|Revisar emisiones huérfanas')),
        ],
        states={'import-failed': 'Source saved, but import failed. Existing channels remain. Retry update; do not add the source again.|Fuente guardada, pero la importación falló. Se conservan canales. Reintenta actualizar; no vuelvas a añadirla.'},
    )
screen(
    'source-results',
    'sources',
    'Import result|Resultado de importación',
    'Saved, queued, imported and verified are different facts.|Guardado, en cola, importado y verificado son hechos distintos.',
    '/scraper',
    'frontend/src/pages/Scraper.tsx',
    321,
    [
        facts('Family channels · synthetic|Family channels · ficticio', [('Source|Fuente', 'Saved|Guardada'), ('Queue|Cola', 'Finished|Terminada'), ('Imported|Importadas', '8 new · 2 unchanged · 1 excluded|8 nuevas · 2 sin cambios · 1 excluida'), ('Signal|Señal', 'Not checked|Sin comprobar')]),
        links(('streams', 'Review imported streams|Revisar emisiones'), ('channel-assign', 'Assign TV channels|Asignar canales'), ('automation', 'Schedule updates|Programar actualizaciones')),
    ],
    states={
        'waiting': 'Waiting for the current guide refresh. A second request does not create a duplicate job.|Esperando a la actualización de guía. Otra solicitud no duplica la tarea.',
        'partial': 'Some records failed. Keep existing channels and show imported, excluded, invalid and failed counts separately.|Fallaron algunos registros. Conserva canales y separa cantidades importadas, excluidas, inválidas y fallidas.',
    },
)
screen(
    'source-remove',
    'sources',
    'Remove Family channels?|¿Eliminar Family channels?',
    'The source’s streams can be removed or retained explicitly.|Puedes eliminar o conservar expresamente sus emisiones.',
    '/scraper',
    'frontend/src/components/scraper/DeleteSourceDialog.tsx',
    321,
    [
        form(
            'remove-source',
            'Review impact|Revisar efecto',
            [
                field(
                    'source.delete_streams',
                    'Also delete this source’s streams|Eliminar también sus emisiones',
                    'Current default is on. Example: 8 source-owned streams, 3 linked to TV channels. TV channels remain.|El valor actual por defecto está activado. Ejemplo: 8 emisiones, 3 vinculadas a canales. Se conservan canales de TV.',
                    True,
                    'checkbox',
                )
            ],
            'Remove source|Eliminar fuente',
            'Source removed. If streams were retained, orphan cleanup remains a separate reviewed action.|Fuente eliminada. Si se conservaron emisiones, su limpieza requiere revisión aparte.',
            'DELETE scrapers/urls/{id}?delete_streams=',
            intent=True,
            danger=True,
            confirm=pair('Remove Family channels with the selected stream-deletion choice? Existing TV channels remain.|¿Eliminar Family channels según la opción elegida para emisiones? Se conservan canales de TV.'),
        )
    ],
)
screen(
    'sources-orphans',
    'sources',
    'Streams without a saved source|Emisiones sin fuente guardada',
    'Choose only the former sources you want to clean up.|Elige solo las antiguas fuentes que quieras limpiar.',
    '/scraper',
    'frontend/src/components/scraper/OrphanedSourcesDialog.tsx',
    321,
    [
        choices(
            'Orphaned source groups|Grupos de fuentes huérfanas',
            [('orphan1', 'Former sample source', '4 streams · 1 linked to a TV channel|4 emisiones · 1 vinculada a canal'), ('orphan2', 'Old sample feed', '2 streams · none linked|2 emisiones · ninguna vinculada')],
            'Delete selected orphan streams|Eliminar huérfanas seleccionadas',
            'Server rejects sources that are configured again. Manual, W3U, Telegram and saved-search ownership is excluded.|El servidor rechaza fuentes que vuelven a estar configuradas. Se excluyen pertenencias manuales, W3U, Telegram y búsquedas.',
            danger=True,
        ),
        note('Nothing is selected initially. Previewing groups deletes nothing.|Nada está seleccionado inicialmente. Consultar los grupos no elimina nada.'),
    ],
)
screen(
    'w3u',
    'sources',
    'Review W3U catalogue|Revisar catálogo W3U',
    'Folders organize the publisher’s catalogue; they are not TV-channel assignments.|Las carpetas organizan el catálogo del editor; no son asignaciones a canales.',
    '/scraper?tab=w3u',
    'frontend/src/pages/Catalogues.tsx',
    321,
    [
        form(
            'catalogue-preview',
            'Load a catalogue preview|Consultar catálogo',
            [field('catalogue.url', 'Catalogue URL|URL de catálogo', 'Bounded structured documents only. Publisher scripts are never executed.|Solo documentos estructurados limitados. Nunca se ejecutan scripts del editor.', 'https://catalogue.example.invalid/sample.w3u', kind='url', required=True)],
            'Preview catalogue|Ver catálogo',
            'Read-only preview. Expiring token and revision protect a later import.|Vista previa sin cambios. Token temporal y revisión protegen la importación posterior.',
            'catalogueService preview',
            local=True,
        ),
        choices(
            'Sample catalogue / Live / Documentary|Sample catalogue / Live / Documentary',
            [('folder1', 'Northlight · live|Northlight · directo', 'Compatible · synthetic entry|Compatible · entrada ficticia'), ('folder2', 'Atelier · live|Atelier · directo', 'Already imported · metadata retained|Ya importada · se conservan datos')],
            'Review permanent import|Revisar importación permanente',
            'Only explicit compatible live selections can become permanent streams. VOD and events remain separate.|Solo selecciones de directo compatibles pueden ser permanentes. VOD y eventos siguen separados.',
        ),
        rows(
            'Other entries|Otras entradas',
            [
                ('Film archive', 'VOD · not imported as a channel|VOD · no se importa como canal', 'w3u-detail'),
                ('Northlight Cup', 'Event · review through Events|Evento · revisar desde Eventos', 'event-import'),
                ('Website', 'Unsupported resolver · source host only|Resolución incompatible · solo host de origen', 'w3u-detail'),
            ],
        ),
        links(('w3u-save', 'Import settings|Ajustes de importación'), ('w3u-folder', 'Assign folder streams|Asignar emisiones de carpeta')),
    ],
    states={'expired': 'Preview expired or catalogue revision changed. Load a new preview; old selection is not authorization.|Vista previa caducada o revisión cambiada. Carga otra; la selección anterior no autoriza importar.'},
)
screen(
    'w3u-save',
    'sources',
    'Save reviewed catalogue|Guardar catálogo revisado',
    'Import only selected compatible live entries.|Importa solo las entradas de directo compatibles seleccionadas.',
    '/scraper?tab=w3u',
    'frontend/src/pages/Catalogues.tsx',
    321,
    [
        form(
            'catalogue-save',
            'Catalogue and import|Catálogo e importación',
            [
                field('catalogue.name', 'Catalogue name|Nombre de catálogo', '1–255 characters.|1–255 caracteres.', 'Sample catalogue', required=True, maxlength=255),
                field(
                    'catalogue.mode',
                    'Import streams|Importar emisiones',
                    'Preserve current compatibility modes and reviewed branch selection.|Conserva modos de compatibilidad y selección revisada.',
                    'compatible',
                    'select',
                    options=['compatible|Compatible entries|Entradas compatibles', 'acestream|AceStream only|Solo AceStream'],
                ),
                field('catalogue.confirm_live', 'Import reviewed entries as permanent live channels|Importar entradas revisadas como emisiones permanentes', 'Required explicit confirmation. Preview alone writes nothing.|Confirmación explícita obligatoria. La vista previa no escribe.', False, 'checkbox', required=True),
                field(
                    'catalogue.refresh_enabled',
                    'Refresh with scheduled scraping|Actualizar con las tareas de fuentes',
                    'Opt-in. Only reviewed identities refresh automatically; missing entries and deselection do not prune saved channels.|Opcional. Solo se actualizan identidades revisadas; las ausencias o deselecciones no borran canales.',
                    False,
                    'checkbox',
                ),
            ],
            'Save catalogue|Guardar catálogo',
            'Catalogue saved with selected branches. Review per-entry outcome.|Catálogo guardado con las ramas elegidas. Revisa el resultado por entrada.',
            'catalogueService save',
            intent=True,
        ),
        command(
            'Remove catalogue|Eliminar catálogo',
            'Remove refresh configuration? Imported channels remain, including partially refreshed entries.|¿Eliminar la configuración de actualización? Se conservan canales, incluidos los actualizados parcialmente.',
            'Catalogue removed; imported streams retained.|Catálogo eliminado; emisiones conservadas.',
            danger=True,
        ),
    ],
)
screen(
    'w3u-detail',
    'sources',
    'Catalogue entry details|Detalles de entrada',
    'Keep supported media separate from a publisher website or VOD.|Distingue contenido compatible de web del editor o VOD.',
    '/scraper?tab=w3u',
    'frontend/src/pages/Catalogues.tsx',
    321,
    [
        facts(
            'Film archive',
            [
                ('Type|Tipo', 'VOD · excluded from live-channel import|VOD · excluido de importación de directo'),
                ('Origin host|Host de origen', 'catalogue.example.invalid'),
                ('Header names|Nombres de cabecera', 'User-Agent · Referer · no values shown|User-Agent · Referer · sin valores'),
                ('State|Estado', 'Retained original metadata|Datos originales conservados'),
            ],
        ),
        form(
            'w3u-browse',
            'Browse options|Opciones de consulta',
            [
                field('catalogue.search', 'Search catalogue|Buscar en catálogo', 'Local reviewed inventory.|Inventario local revisado.', '', 'search'),
                field('catalogue.content_type', 'Content type|Tipo de contenido', 'Live, event, VOD or unknown.|Directo, evento, VOD o desconocido.', 'all', 'select', options=['all|All|Todos', 'live|Live|Directo', 'event|Event|Evento', 'vod|VOD|VOD', 'unknown|Unknown|Desconocido']),
                field('catalogue.show', 'Show|Mostrar', 'Review supported, unsupported and imported states.|Revisa estados compatibles, incompatibles e importados.', 'all', 'select', options=['all|All entries|Todas las entradas', 'compatible|Compatible|Compatibles', 'imported|Imported|Importadas']),
                field('catalogue.artwork', 'Load publisher artwork|Cargar imágenes del editor', 'Explicit opt-in; failing artwork leaves original names visible.|Activación explícita; si falla la imagen el nombre sigue visible.', False, 'checkbox'),
            ],
            'Apply view options|Aplicar opciones',
            'View updated; no import or playback started.|Vista actualizada; no se importó ni reprodujo.',
            'local catalogue view',
            local=True,
        ),
    ],
)
screen(
    'w3u-folder',
    'sources',
    'Assign a catalogue folder|Asignar una carpeta del catálogo',
    'This explicit action is separate from importing streams.|Esta acción expresa es independiente de importar emisiones.',
    '/scraper?tab=w3u',
    'frontend/src/components/catalogues/FolderMatchDialog.tsx',
    320,
    [
        form(
            'folder',
            'Sample catalogue / Live / Northlight',
            [
                field('folder.tv_channel_id', 'Existing TV channel|Canal de TV existente', 'Choose an existing channel or a new name, not both.|Elige un canal o un nombre nuevo, no ambos.', '1', 'select', options=['|Create a channel instead|Crear un canal', '1|Northlight|Northlight']),
                field('folder.create_name', 'New channel name|Nombre de canal nuevo', 'Used only when creating a new TV channel.|Solo se usa al crear un canal nuevo.', '', advanced=True),
                field('folder.reassign', 'Move already assigned streams|Mover emisiones ya asignadas', 'Off preserves existing assignments. Deepest folders are processed first in reviewed batch matching.|Desactivado conserva vínculos. En lote se procesan primero las carpetas más profundas.', False, 'checkbox'),
            ],
            'Assign reviewed folder|Asignar carpeta revisada',
            'Commit atomically; changed or vanished rows require another review. Unimported streams are skipped.|Guardado atómico; filas cambiadas o ausentes requieren revisar. Se omiten emisiones sin importar.',
            'catalogueService folder assignment',
            intent=True,
        ),
        links(('channel-assign', 'Review destination channel|Revisar canal de destino')),
    ],
)
screen(
    'saved-search',
    'sources',
    'Saved search|Búsqueda guardada',
    'Save the definition without starting an import.|Guarda la definición sin iniciar una importación.',
    '/scraper?tab=searches',
    'frontend/src/components/imports/SavedSearchDialog.tsx',
    321,
    [
        form(
            'saved-search',
            'Search definition|Definición de búsqueda',
            [
                field('saved_search.name', 'Name|Nombre', '1–100 characters.|1–100 caracteres.', 'Northlight discovery', required=True, maxlength=100),
                field('saved_search.query', 'Query|Consulta', '1–256 characters. Editing query or category pauses refresh.|1–256 caracteres. Editar consulta o categoría pausa las actualizaciones.', 'Northlight', required=True, maxlength=256),
                field('saved_search.category', 'Category|Categoría', 'Optional original search category, up to 100 characters.|Categoría original opcional, hasta 100 caracteres.', ''),
                field('saved_search.refresh_enabled', 'Refresh automatically|Actualizar automáticamente', 'New searches start paused. Preview then explicitly enable after reviewing.|Las nuevas empiezan pausadas. Consulta resultados y activa expresamente después.', False, 'checkbox'),
            ],
            'Save search|Guardar búsqueda',
            'Definition saved only. Existing memberships and channels are retained.|Solo se guardó la definición. Se conservan pertenencias y canales.',
            'savedSearchService save',
            intent=True,
        ),
        links(('saved-search-preview', 'Preview and run|Consultar y ejecutar'), ('exclusion', 'Review import exclusions|Revisar exclusiones')),
    ],
)
screen(
    'saved-search-preview',
    'sources',
    'Preview a saved search|Consultar búsqueda guardada',
    'Resolve results and inspect exclusions before queueing an additive import.|Resuelve resultados y revisa exclusiones antes de poner una importación aditiva en cola.',
    '/scraper?tab=searches',
    'frontend/src/components/imports/SavedSearches.tsx',
    321,
    [
        facts('Northlight discovery', [('Preview|Vista previa', '2 importable · 1 excluded · 1 unresolved|2 importables · 1 excluida · 1 sin resolver'), ('Preview expiry|Caducidad', '5 minutes · bound to definition revision|5 minutos · ligada a la revisión')]),
        command(
            'Run this search|Ejecutar esta búsqueda',
            'Import eligible results additively? The definition, exclusion policy and run ownership are checked again.|¿Importar resultados aptos de forma aditiva? Se revalidan definición, exclusiones y propiedad de ejecución.',
            'Waiting in maintenance queue. A second request cannot duplicate this run.|Esperando en la cola. Otra solicitud no duplica esta ejecución.',
        ),
        rows(
            'Recent runs|Ejecuciones recientes',
            [
                ('7 Nov 16:00 · partial|7 nov 16:00 · parcial', '2 added · 1 excluded · 1 unresolved|2 añadidas · 1 excluida · 1 sin resolver', None),
                ('6 Nov 16:00 · interrupted|6 nov 16:00 · interrumpida', 'Restart interrupted the old run; existing channels retained|El reinicio interrumpió la ejecución; canales conservados', None),
            ],
        ),
    ],
)
screen(
    'exclusion',
    'sources',
    'Import exclusion rule|Regla de exclusión de importación',
    'Affects future permanent imports, not existing channels or playback.|Afecta a futuras importaciones permanentes, no a canales existentes ni reproducción.',
    '/scraper?tab=exclusions',
    'frontend/src/components/imports/ImportExclusions.tsx',
    321,
    [
        form(
            'exclusion',
            'Rule|Regla',
            [
                field(
                    'exclusion.kind',
                    'Match by|Comparar por',
                    'Use the current supported literal rule type; no arbitrary regex execution.|Usa el tipo literal admitido; no se ejecuta regex arbitrario.',
                    'name_contains',
                    'select',
                    options=['name_contains|Name contains|Nombre contiene', 'name_exact|Exact name|Nombre exacto', 'channel_id|Exact content ID|ID de contenido exacto'],
                ),
                field('exclusion.value', 'Value|Valor', '1–256 characters. Original matching value is not translated.|1–256 caracteres. No se traduce el valor de comparación.', 'Demo unwanted', required=True, maxlength=256),
                field('exclusion.enabled', 'Rule enabled|Regla activada', 'On by default.|Activada por defecto.', True, 'checkbox'),
                field('exclusion.note', 'Note (optional)|Nota (opcional)', 'Up to 500 characters for the operator.|Hasta 500 caracteres para el operador.', '', kind='textarea', maxlength=500),
            ],
            'Save exclusion|Guardar exclusión',
            'Policy revision advanced. Pending imports recheck it before applying.|Revisión de política actualizada. Las importaciones pendientes la revalidan.',
            'importExclusionService save',
        ),
        command('Preview impact|Ver efecto', 'Preview a bounded sample without deleting existing channels?|¿Consultar una muestra limitada sin eliminar canales?', '3 of 200 sampled candidates match. Partial sample is not a catalogue-wide count.|Coinciden 3 de 200 candidatos de muestra. No es el total del catálogo.'),
        command('Delete rule|Eliminar regla', 'Future imports can admit these candidates again. Existing channels are not rewritten.|Las futuras importaciones pueden admitir candidatos. No se reescriben canales existentes.', 'Rule deleted.|Regla eliminada.', danger=True),
    ],
)

screen(
    'search',
    'sources',
    'Find new streams|Buscar emisiones nuevas',
    'Search the provider catalogue, not only your saved streams.|Busca en el catálogo del proveedor, no solo en tus emisiones guardadas.',
    '/search',
    'frontend/src/pages/Search.tsx',
    321,
    [
        form(
            'search',
            'Discovery search|Búsqueda de nuevas emisiones',
            [
                field('search.query', 'Search|Buscar', 'Original programme or channel name. Search results are not imported automatically.|Nombre original del programa o canal. Los resultados no se importan solos.', 'Northlight', required=True),
                field('search.category', 'Category|Categoría', 'Optional provider category.|Categoría opcional del proveedor.', ''),
            ],
            'Search catalogue|Buscar en catálogo',
            'Results are catalogue infohashes. Resolve Add or Play before using a content ID.|Los resultados son infohashes. Resuelve Añadir o Reproducir antes de usar un ID.',
            'searchService.search',
            local=True,
        ),
        rows('Synthetic results|Resultados ficticios', [('Northlight HD', 'Not saved · broadcast check not requested|Sin guardar · sin comprobación solicitada', 'search-add-link'), ('Northlight alternate', 'Excluded by rule · import requires review|Excluida por regla · requiere revisión', 'search-add-link')]),
        links(('saved-search', 'Save this search|Guardar búsqueda'), ('stream-edit', 'Add a known content ID|Añadir un ID conocido')),
    ],
    states={'engine': 'The playback engine could not resolve the selected catalogue ID. Nothing was saved or played; retry resolution when it is available.|El motor no pudo resolver el ID seleccionado. No se guardó ni reprodujo nada; reintenta cuando esté disponible.'},
)
screen(
    'search-add-link',
    'sources',
    'Add and link Northlight HD|Añadir y vincular Northlight HD',
    'Resolve the result, then import and assign it together.|Resuelve el resultado; después importa y asigna juntos.',
    '/search',
    'frontend/src/components/search/AddAndLinkDialog.tsx',
    321,
    [
        note('Catalogue infohash → resolved content ID → one atomic Add and Link. Resolution alone creates no channel or playback session.|Infohash → ID resuelto → alta y vínculo atómicos. Resolver no crea canales ni inicia reproducción.'),
        form(
            'add-link',
            'Select a TV channel|Seleccionar canal de TV',
            [
                field(
                    'add_link.tv_channel_id',
                    'TV channel|Canal de TV',
                    'Required. Shared picker searches number, name, country and category. Preserve existing conflicting assignment.|Obligatorio. Selector compartido por número, nombre, país y categoría. Conserva asignaciones en conflicto.',
                    '',
                    'select',
                    options=['|Choose a TV channel|Elige un canal', '1|1 · Northlight · ES · Documentary|1 · Northlight · ES · Documentary', '2|2 · World 24 · GB · News|2 · World 24 · GB · News'],
                    required=True,
                )
            ],
            'Add and link|Añadir y vincular',
            'Stream imported and linked in one transaction, or neither change applied.|Emisión importada y vinculada en una transacción, o no se aplica ninguno de los cambios.',
            'searchService.resolve + import tv_channel_id',
            intent=True,
        ),
        links(('channel-edit', 'Create a TV channel first|Crear primero un canal')),
    ],
    states={
        'unresolved': 'Resolution failed. Do not use the catalogue infohash as a content ID.|Falló la resolución. No uses el infohash del catálogo como ID.',
        'excluded': 'Import exclusion applies. Do not bypass it through Search; review the rule or explicit manual-add workflow.|Se aplica una exclusión. Buscar no la omite; revisa la regla o el alta manual expresa.',
        'catalogue-unavailable': 'TV catalogue unavailable. Keep the chosen search result and offer Retry; no partial stream import.|Catálogo de TV no disponible. Conserva el resultado y ofrece Reintentar; no importes parcialmente.',
        'conflict': 'Stream already belongs to another TV channel. Its assignment remains unchanged.|La emisión ya pertenece a otro canal. Se conserva su asignación.',
    },
)

SAMPLE = '[{"name":"Northlight HD","id":"' + '0' * 40 + '","group":"Documentary"}]'
RECIPE_HEAD = [
    field('recipe.name', 'Recipe name|Nombre de receta', '1–100 characters.|1–100 caracteres.', 'Sample paired records', required=True, maxlength=100),
    field('recipe.version', 'Recipe version|Versión de receta', 'Semantic version such as 1.0.0; schema_version remains 1.|Versión como 1.0.0; schema_version permanece en 1.', '1.0.0', required=True, pattern=r'\d+\.\d+\.\d+'),
]
screen(
    'helper-installed',
    'extraction',
    'Test a source recipe|Probar una receta de fuente',
    'Fetch a bounded sample or paste one; testing changes no source or channel.|Obtén una muestra limitada o pégala; probar no cambia fuentes ni canales.',
    '/extraction-builder',
    'frontend/src/pages/ExtractionBuilder.tsx',
    321,
    [
        form(
            'fetch',
            'Sample from installation|Muestra desde la instalación',
            [
                field('fetch.url', 'Source URL|URL de fuente', 'Guarded fetch from the installation. DNS pinning and redirects remain protected.|Consulta protegida desde la instalación. Conserva DNS fijado y redirecciones seguras.', 'https://source.example.invalid/channels', kind='url', required=True),
                field('fetch.url_type', 'Source type|Tipo de fuente', 'Auto, regular HTTP, ZeroNet or IPFS; same guarded source pipeline.|Automático, HTTP, ZeroNet o IPFS; mismo flujo protegido.', 'auto', 'select', options=['auto|Auto|Automático', 'regular|HTTP|HTTP', 'zeronet|ZeroNet|ZeroNet', 'ipfs|IPFS|IPFS']),
            ],
            'Fetch sample|Obtener muestra',
            'Sample fetched for preview only. Saved source and channels are untouched.|Muestra obtenida solo para revisar. Fuente y canales no cambian.',
            'recipeService.fetch',
            local=True,
        ),
        links(
            ('helper-html', 'HTML / visual picker|HTML / selector visual'),
            ('helper-json', 'JSON paths|Rutas JSON'),
            ('helper-regex', 'Text / regular expressions|Texto / expresiones regulares'),
            ('helper-manual', 'Raw and manual fields|Texto y campos manuales'),
            ('helper-results', 'Test and save to source|Probar y guardar en fuente'),
        ),
    ],
)
screen(
    'helper-standalone',
    'extraction',
    'Build a recipe offline|Crear una receta sin conexión',
    'This helper never connects to your installation.|Este asistente nunca se conecta a tu instalación.',
    'standalone helper',
    'frontend/src/recipes/standalone.tsx',
    321,
    [
        note('Paste a synthetic sample or choose a local file. No server address, credentials, fetch-from-installation or Save source action belongs here.|Pega una muestra ficticia o elige un archivo local. Aquí no hay dirección de servidor, credenciales, consulta a instalación ni Guardar fuente.'),
        form(
            'sample',
            'Sample input|Muestra de entrada',
            [
                field('sample.file', 'Local sample file|Archivo local de muestra', 'Read locally; never upload from this standalone helper. Sample limit 32 MiB.|Se lee localmente; nunca se sube desde el asistente independiente. Límite 32 MiB.', '', 'file'),
                field(
                    'sample.text',
                    'HTML, text or JSON sample|Muestra HTML, texto o JSON',
                    'Input limit and smaller rendering budget are different. Keep names and IDs in each record paired.|El límite de entrada y el presupuesto de visualización son distintos. Conserva nombre e ID emparejados por registro.',
                    SAMPLE,
                    'textarea',
                ),
                field(
                    'recipe.catalogue',
                    'Starter recipe|Receta inicial',
                    'Versioned fixture-tested catalogue. Choosing a new mode resets fields only after a draft warning.|Catálogo versionado y probado. Cambiar modo reinicia campos solo tras avisar del borrador.',
                    '',
                    'select',
                    options=['|Start empty|Empezar vacía', 'demo|Synthetic paired JSON|JSON emparejado ficticio'],
                ),
                field('recipe.pasted', 'Recipe JSON (optional)|JSON de receta (opcional)', 'Import up to 512 KiB, validate schema/version, then test.|Importa hasta 512 KiB, valida esquema y versión, y prueba.', '', 'textarea', advanced=True),
            ],
            'Use sample|Usar muestra',
            'Sample loaded locally. Choose fields; no channel data was written.|Muestra cargada localmente. Elige campos; no se escribió ningún canal.',
            'standalone recipe worker',
            local=True,
        ),
        links(('helper-json', 'Choose JSON fields|Elegir campos JSON'), ('helper-html', 'Choose HTML fields|Elegir campos HTML'), ('helper-regex', 'Choose regex fields|Elegir campos regex'), ('helper-large', 'Large sample path|Muestras grandes')),
    ],
    standalone=True,
)
for mode, title, record, help in [
    ('html', 'Pick fields in HTML|Elegir campos en HTML', '.channel', 'A selector finds each repeating row; field selectors are relative to that row.|Un selector encuentra cada fila; los campos se buscan dentro de ella.'),
    ('json', 'Read fields from JSON|Leer campos de JSON', 'channels', 'Records array path, or blank for a root array. Field paths are relative to each object.|Ruta del array, o vacío para array raíz. Los campos son relativos a cada objeto.'),
    ('regex', 'Read paired text records|Leer registros de texto emparejados', '(.+?)\n([a-f0-9]{40})', 'Each bounded regex match is one record. Name and ID extraction run inside that record.|Cada coincidencia limitada es un registro. Nombre e ID se extraen dentro de ese registro.'),
]:
    fs = [
        *RECIPE_HEAD,
        field(
            'recipe.mode',
            'Source format|Formato de fuente',
            'Changing format clears incompatible rules only after confirmation.|Cambiar formato borra reglas incompatibles solo tras confirmar.',
            mode,
            'select',
            options=['html|HTML elements|Elementos HTML', 'json|JSON response|Respuesta JSON', 'regex|Text / regex|Texto / regex'],
        ),
        field('recipe.records', 'Repeating record|Registro repetido', help, record, maxlength=1024),
    ]
    for key, label in [('name', 'Name|Nombre'), ('id', 'Content ID|ID de contenido'), ('group', 'Group|Grupo'), ('logo', 'Logo|Logotipo'), ('epg_id', 'Guide ID|ID de guía')]:
        en, es = pair(label)
        if mode == 'html':
            fs.extend(
                [
                    field(
                        f'recipe.fields.{key}.selector',
                        f'{en} selector|Selector de {es.lower()}',
                        'Relative to each row; blank selects the row itself. Maximum 256 characters.|Relativo a cada fila; vacío elige la fila. Máximo 256 caracteres.',
                        'a' if key in ['id', 'name'] else '',
                        maxlength=256,
                        advanced=key not in ['id', 'name'],
                    ),
                    field(f'recipe.fields.{key}.attribute', f'{en} attribute|Atributo de {es.lower()}', 'Blank reads text; href reads a link. Maximum 80 characters.|Vacío lee texto; href lee enlace. Máximo 80 caracteres.', 'href' if key == 'id' else '', maxlength=80, advanced=key not in ['id', 'name']),
                ]
            )
        if mode == 'json':
            fs.append(
                field(
                    f'recipe.fields.{key}.path',
                    f'{en} JSON path|Ruta JSON de {es.lower()}',
                    'Relative to the record. An ID array yields several streams with the same name; maximum 256 characters.|Relativa al registro. Un array de IDs produce varias emisiones del mismo nombre; máximo 256 caracteres.',
                    key,
                    maxlength=256,
                    advanced=key not in ['id', 'name'],
                )
            )
        fs.append(
            field(
                f'recipe.fields.{key}.pattern',
                f'{en} regex|Regex de {es.lower()}',
                'First capture is the value; with no capture use the full match. Optional for HTML/JSON; maximum 1024 characters.|La primera captura da el valor; sin captura se usa toda la coincidencia. Opcional en HTML/JSON; máximo 1024 caracteres.',
                '(.+)' if mode == 'regex' else '',
                maxlength=1024,
                advanced=key not in ['id', 'name'],
            )
        )
    fs.append(field('recipe.flags', 'Regex flags|Opciones regex', 'i ignores case; m line anchors; s includes newlines. No named groups or backreferences.|i ignora mayúsculas; m ancla líneas; s incluye saltos. Sin grupos con nombre ni referencias inversas.', 'is', pattern='[ims]{0,3}'))
    screen(
        'helper-' + mode,
        'extraction',
        title,
        help,
        '/extraction-builder',
        'frontend/src/recipes/RecipeFields.tsx',
        321,
        [
            dict(type='sample', mode=mode, text=SAMPLE),
            form(
                'recipe-' + mode,
                'Paired record fields|Campos emparejados',
                fs,
                'Test recipe|Probar receta',
                'Read-only bounded test. Changing sample or recipe invalidates the previous test; do not enable Save from stale results.|Prueba limitada sin cambios. Cambiar muestra o receta invalida la prueba anterior; no permitas guardar resultados antiguos.',
                'recipeService.preview / standalone worker',
                local=True,
                next='helper-results',
            ),
            links(('helper-manual', 'Manual selection|Selección manual'), ('helper-standalone', 'Independent helper|Asistente independiente')),
        ],
        states={
            'timeout': 'The bounded test stopped before completing. Simplify the record rule or use a smaller sample. Existing channels are unchanged.|La prueba se detuvo antes de terminar. Simplifica la regla o reduce la muestra. Los canales no cambian.',
            'invalid': 'This rule is not supported. Keep the draft and show the field-level reason without running unbounded regex.|Esta regla no se admite. Conserva el borrador y muestra el motivo sin ejecutar regex sin límites.',
        },
    )
screen(
    'helper-manual',
    'extraction',
    'Select fields manually|Seleccionar campos manualmente',
    'Start with one complete record, then identify its name and ID.|Empieza con un registro completo e identifica nombre e ID.',
    '/extraction-builder',
    'frontend/src/recipes/RecipeBuilder.tsx',
    321,
    [
        code('Raw synthetic sample|Muestra ficticia', 'Northlight HD\n' + '0' * 40),
        form(
            'manual',
            'Selection tools|Herramientas de selección',
            [
                field(
                    'manual.target',
                    'Assign selection to|Asignar selección a',
                    'Pick the repeating record first, then fields inside it. Keyboard selection works in raw text.|Elige primero el registro y después sus campos. Se puede seleccionar texto con teclado.',
                    'records',
                    'select',
                    options=['records|Repeating record|Registro repetido', 'name|Name|Nombre', 'id|Content ID|ID de contenido', 'group|Group|Grupo', 'logo|Logo|Logotipo', 'epg_id|Guide ID|ID de guía'],
                ),
                field('manual.selection', 'Selected text|Texto seleccionado', 'Show exact original text; do not translate or normalize IDs.|Muestra texto original; no traduzcas ni normalices IDs.', 'Northlight HD', 'textarea'),
            ],
            'Use selection|Usar selección',
            'Field rule updated locally. Test the whole recipe before saving.|Regla actualizada localmente. Prueba toda la receta antes de guardar.',
            'RecipeBuilder source selection',
            local=True,
        ),
        links(('helper-regex', 'Review generated field rules|Revisar reglas generadas')),
    ],
)
screen(
    'helper-large',
    'extraction',
    'This sample is too large to draw safely|La muestra es demasiado grande para dibujarla',
    'Keep the raw/manual workflow available.|Mantén disponible el flujo de texto y campos manuales.',
    '/extraction-builder',
    'frontend/src/recipes/VisualPicker.tsx',
    321,
    [
        note(
            'Synthetic large-input state. Source support is 32 MiB; browser rendering uses a smaller bounded budget. A successful upload does not guarantee a visual preview.|Estado ficticio de muestra grande. Las fuentes admiten 32 MiB; la visualización tiene un límite menor. Subir correctamente no garantiza vista visual.',
            'warning',
        ),
        rows(
            'Continue without visual rendering|Continuar sin vista visual',
            [
                ('Use raw selection|Usar selección de texto', 'Keep sample loaded and select a repeating record|Conserva la muestra y selecciona un registro', 'helper-manual'),
                ('Enter JSON paths|Introducir rutas JSON', 'Use object paths without rendering the full tree|Usa rutas sin dibujar todo el árbol', 'helper-json'),
                ('Test on installation|Probar en instalación', 'Installed bounded preview supports the server-side workflow|La vista limitada de instalación permite probar en servidor', 'helper-installed'),
            ],
        ),
    ],
    states={'too-large': 'The input exceeds the admission limit. Reject before JSON parsing; retain the previous sample and recipe.|La entrada supera el límite. Rechaza antes de analizar JSON; conserva muestra y receta anteriores.'},
)
screen(
    'helper-results',
    'extraction',
    'Review extraction results|Revisar resultados de extracción',
    'Successful extraction does not mean a stream is online.|Extraer correctamente no significa que haya señal.',
    '/extraction-builder',
    'frontend/src/recipes/RecipeResults.tsx',
    321,
    [
        facts('Synthetic test|Prueba ficticia', [('Records|Registros', '4'), ('Valid / invalid / duplicate|Válidos / inválidos / duplicados', '2 / 1 / 1'), ('Pairing|Emparejamiento', 'Northlight HD → ' + '0' * 40)]),
        rows('Issues|Problemas', [('Record 3|Registro 3', 'Missing content ID; skipped without pairing it with another row|Falta ID; omitido sin emparejarlo con otra fila', None)]),
        dict(type='copy', label=pair('Copy example recipe JSON|Copiar JSON de receta'), value='{"schema_version":1,"name":"DEMO","version":"1.0.0","mode":"json","records":"","flags":"is","fields":{"name":{"path":"name"},"id":{"path":"id"}}}'),
        command(
            'Save recipe to selected source|Guardar receta en fuente seleccionada',
            'Installed helper only: attach the tested recipe to Family channels? Source import remains a separate action.|Solo instalado: ¿vincular la receta probada a Family channels? Importar es otra acción.',
            'Recipe saved; source not imported. Standalone instead copies or exports the recipe.|Receta guardada; fuente sin importar. El asistente independiente copia o exporta.',
            installedOnly=True,
        ),
        links(('source-web', 'Return to source|Volver a fuente')),
    ],
    states={'stale': 'The recipe or sample changed after this test. Test again before saving; old results are only a reference.|La receta o muestra cambió tras probar. Vuelve a probar antes de guardar; los resultados antiguos son referencia.'},
)

screen(
    'dashboard',
    'viewing',
    'Ready when you are|Todo preparado',
    'Watch, find your recordings or see what is coming up.|Ve la TV, encuentra tus grabaciones o consulta lo próximo.',
    '/',
    'frontend/src/pages/TVDashboard.tsx',
    319,
    [
        dict(type='feature', title='Coastlines: the Atlantic', text=pair('Northlight · documentary · synthetic programme artwork|Northlight · documental · ilustración ficticia'), target='live'),
        rows(
            'Your television|Tu televisión',
            [
                ('Browse 3 channels|Explorar 3 canales', '2 have a recent verified signal; this is not a promise of present playback.|2 tienen señal verificada reciente; no garantiza reproducción actual.', 'live'),
                ('Saved recordings|Grabaciones guardadas', 'Coastlines: the Atlantic · ready|Coastlines: the Atlantic · lista', 'recording-parts'),
                ('Northlight Cup', 'Tomorrow · kickoff not confirmed|Mañana · hora sin confirmar', 'event-detail'),
            ],
        ),
        facts('Next content updates|Próximas actualizaciones', [('Sources|Fuentes', 'In 25 min|En 25 min'), ('Guide|Guía', 'Waiting behind source update|Esperando actualización de fuentes'), ('Signal checks|Comprobaciones', 'Unknown · schedule unavailable|Desconocido · horario no disponible')]),
        links(('playlist', 'Open playlist dialog|Abrir diálogo de lista'), ('system', 'System status|Estado del sistema')),
    ],
    states={
        'first-use': 'Start by adding a channel source. A guide is optional, and HTTP channels can work without an AceStream engine.|Empieza añadiendo una fuente. La guía es opcional y los canales HTTP pueden funcionar sin motor AceStream.',
        'partial': 'Upcoming events could not load. Channels and recordings remain usable. Retry events only.|No se cargaron eventos próximos. Canales y grabaciones siguen disponibles. Reintenta solo eventos.',
    },
)
screen(
    'live',
    'viewing',
    'Live TV|TV en directo',
    'Browse without interrupting the channel already playing.|Explora sin interrumpir el canal en reproducción.',
    '/live-tv',
    'frontend/src/pages/LiveTV.tsx',
    319,
    [
        dict(type='player', title='Northlight · Coastlines: the Atlantic', status=pair('Playing illustration · no media session|Ilustración de reproducción · sin sesión real')),
        links(('player-tracks', 'Audio and subtitles|Audio y subtítulos'), ('casting-control', 'Send to TV|Enviar a TV'), ('recording-schedule', 'Record programme|Grabar programa')),
        form(
            'browse',
            'Browse|Explorar',
            [
                field('live.list', 'Browse list|Lista', 'Changing list keeps the active viewer.|Cambiar lista conserva el espectador activo.', 'tv', 'select', options=['tv|TV channels|Canales de TV', 'streams|Streams|Emisiones', 'events|Events|Eventos']),
                field('live.q', 'Search|Buscar', 'Search filters only the browse list.|Solo filtra la lista.', '', 'search'),
                field(
                    'live.online_only',
                    'Online only|Solo con señal verificada',
                    'Default on for TV and streams. Latest observation is not current playback certainty. Show all uses availability=all.|Activado en TV y emisiones. La última observación no garantiza reproducción. Ver todo usa availability=all.',
                    True,
                    'checkbox',
                ),
            ],
            'Apply browse filter|Aplicar filtro',
            'Browse list updated. Selection and player identity survive filtering and the 30-second catalogue refresh.|Lista actualizada. Selección y reproductor sobreviven filtros y actualización cada 30 segundos.',
            'LiveTV URL state',
            local=True,
        ),
        rows(
            'Channels and now/next|Canales y ahora/después',
            [('Northlight', 'Now Coastlines: the Atlantic · next Inside the studio|Ahora Coastlines: the Atlantic · después Inside the studio', 'channel-detail'), ('World 24', 'No guide data · watching does not require a guide|Sin guía · no es necesaria para ver', 'channel-detail')],
        ),
        command('Stop watching|Dejar de ver', 'Release this browser’s viewer? Other viewers keep their own leases.|¿Liberar este espectador? Los demás conservan sus sesiones.', 'Viewer released. Catalogue stays available.|Espectador liberado. El catálogo sigue disponible.'),
    ],
    permission='live permission / public viewing policy',
    states={
        'filtered': 'No channels match Online only. Show all channels to include unknown or offline observations. Current playback continues.|Ningún canal cumple Solo con señal. Ver todos incluye estados desconocidos o sin señal. La reproducción continúa.',
        'refreshing': 'Updating catalogue in the background. Keep the player and selected channel in place.|Actualizando el catálogo en segundo plano. Conserva reproductor y canal seleccionado.',
        'failed': 'This source could not start. Try another eligible source or retry; do not clear the browse list.|No se inició esta emisión. Prueba otra apta o reintenta; conserva la lista.',
        'stalled': 'Video is not arriving. Keep the last frame with a textual status and offer another source; do not label the channel permanently offline.|No llega vídeo. Conserva el último fotograma con estado textual y ofrece otra emisión; no declares el canal sin señal permanente.',
        'empty': 'No channels yet. Open setup if you can manage this installation; viewers should ask its owner.|Aún no hay canales. Abre configuración si puedes administrarla; los espectadores deben pedir ayuda al propietario.',
    },
)
screen(
    'player-tracks',
    'viewing',
    'Playback options|Opciones de reproducción',
    'Change only this viewer’s track selection.|Cambia las pistas solo de este espectador.',
    'player dialog',
    'frontend/src/components/player/StreamPlayerDialog.tsx',
    319,
    [
        form(
            'tracks',
            'Tracks and source|Pistas y emisión',
            [
                field(
                    'player.audio_index',
                    'Audio|Audio',
                    'Discovered input language, codec and layout. Missing metadata stays unknown. Changing it restarts only this viewer.|Idioma, códec y canales de entrada. Datos ausentes siguen desconocidos. Cambiar reinicia solo este espectador.',
                    '0',
                    'select',
                    options=['0|Spanish · AAC · stereo|Español · AAC · estéreo', '1|Original · AC-3 · 5.1|Original · AC-3 · 5.1'],
                ),
                field('player.subtitle_index', 'Subtitles|Subtítulos', 'Off by default. Bitmap subtitle conversion is unsupported.|Desactivados por defecto. No se convierte subtitulado de imagen.', '', 'select', options=['|Off|Desactivados', '0|Spanish · text|Español · texto']),
                field(
                    'player.source',
                    'Source|Emisión',
                    'Changing source releases this viewer’s old lease. Copied and remote links keep original tracks.|Cambiar emisión libera la sesión anterior de este espectador. Enlaces copiados y remotos conservan pistas originales.',
                    '1',
                    'select',
                    options=['1|Northlight HD|Northlight HD', '2|Northlight backup|Northlight backup'],
                ),
            ],
            'Apply playback choice|Aplicar selección',
            'Preparing the selected tracks; other viewers remain on their own sessions.|Preparando pistas; los demás conservan sus sesiones.',
            'playerService shared viewer lifecycle',
            local=True,
        ),
        links(('live', 'Back to player|Volver al reproductor'), ('remote-control', 'Open in another player|Abrir en otro reproductor')),
    ],
    permission='viewer capability; ownership token',
    states={'capacity': 'No session capacity for this track change. Keep a usable prior state where lifecycle permits; show Retry or Cancel, not a blank player.|No hay capacidad para cambiar pistas. Conserva un estado útil cuando lo permita el ciclo; ofrece Reintentar o Cancelar.'},
)
screen(
    'viewer',
    'viewing',
    'Your viewing access|Tu acceso de visualización',
    'Only your permitted viewing features appear here.|Aquí aparecen solo las funciones permitidas.',
    '/watch',
    'frontend/src/pages/Watch.tsx',
    318,
    [
        rows(
            'Available to viewer-demo|Disponible para viewer-demo', [('Live TV|TV en directo', 'Granted|Permitido', 'live'), ('Programme guide|Guía de programación', 'Granted|Permitido', 'guide-detail'), ('Recordings|Grabaciones', 'Not granted · ask the administrator|No permitido · pide acceso al administrador', None)]
        ),
        links(('access-login', 'Sign in with another account|Entrar con otra cuenta'), ('access-password', 'Change your password|Cambiar contraseña')),
    ],
    permission='non-admin viewer / public feature policy',
    states={'denied': 'This account cannot use recordings. Signing in again does not grant permission; ask an administrator.|Esta cuenta no puede usar grabaciones. Volver a entrar no concede permiso; pide acceso al administrador.'},
)

EVENT_FIELDS = [
    field('event.title', 'Event title|Título del evento', 'Original title, 1–300 characters.|Título original, 1–300 caracteres.', 'Northlight Cup', required=True, maxlength=300),
    field('event.sport', 'Sport|Deporte', 'Original sport value; maximum 100 characters.|Valor original; máximo 100 caracteres.', 'Football', maxlength=100),
    field('event.competition', 'Competition|Competición', 'Original competition, up to 200 characters.|Competición original, hasta 200 caracteres.', 'Demo League', maxlength=200),
    field('event.starts_at', 'Scheduled start|Inicio previsto', 'Unknown may remain blank. Ambiguous DST times require an explicit UTC offset.|Puede quedar vacío si se desconoce. Horas ambiguas requieren desfase UTC explícito.', '2026-11-08T18:00:00+01:00'),
    field('event.timezone', 'Source timezone|Zona horaria de fuente', 'Publisher’s IANA timezone; independent of display language and viewer timezone.|Zona IANA del editor; independiente del idioma y zona de visualización.', 'Europe/Madrid', required=True),
    field('event.broadcaster', 'Broadcaster|Emisora', 'A name alone remains unresolved; it is not a playable stream.|Un nombre solo queda sin resolver; no es una emisión reproducible.', 'Atelier', advanced=True),
    field('event.url', 'Stream URL|URL de emisión', 'Optional AceStream/HLS/MPEG-TS. A website remains unsupported; never infer live status from the clock.|AceStream/HLS/MPEG-TS opcional. Una web sigue incompatible; la hora no prueba directo.', '', advanced=True),
]
screen(
    'events',
    'events',
    'Event agenda|Agenda de eventos',
    'Times help you plan; they do not prove an event is live or a stream works.|Las horas ayudan a planificar; no demuestran directo ni señal.',
    '/events',
    'frontend/src/components/events/EventAgenda.tsx',
    319,
    [
        form(
            'agenda',
            'Your view|Tu vista',
            [
                field('agenda.zone', 'Display timezone|Zona de visualización', 'Browser preference only; does not change source or recording timezones.|Solo preferencia del navegador; no cambia fuentes ni grabaciones.', 'Europe/Madrid'),
                field('agenda.sports', 'Sports|Deportes', 'OR interests; original values. Empty means no interest filter.|Intereses unidos por O; valores originales. Vacío no filtra.', 'Football'),
                field('agenda.competitions', 'Competitions|Competiciones', 'Browser display preference, distinct from provider fetch filters.|Preferencia visual, distinta de filtros de consulta al proveedor.', ''),
                field('agenda.teams', 'Teams|Equipos', 'Original participant names.|Nombres originales de participantes.', ''),
                field('agenda.following', 'Following only|Solo seguidos', 'Following itself is installation-wide, not personal.|Seguir es para toda la instalación, no personal.', False, 'checkbox'),
            ],
            'Apply agenda view|Aplicar vista',
            'Display preferences changed for this browser only.|Preferencias visuales cambiadas solo en este navegador.',
            'eventPreferences',
            local=True,
        ),
        rows(
            '8 November · Europe/Madrid|8 de noviembre · Europe/Madrid',
            [('18:00 · Northlight Cup', 'Northlight United / Atelier City · time supplied by provider|Northlight United / Atelier City · hora del proveedor', 'event-detail'), ('World friendly', 'Kickoff unknown · date only|Hora desconocida · solo fecha', 'event-detail')],
        ),
        links(('event-provider', 'Add provider events|Añadir eventos de proveedor'), ('event-import', 'Add URL / JSON / manual event|Añadir URL / JSON / evento manual'), ('event-sources', 'Sources and retention|Fuentes y conservación')),
    ],
)
screen(
    'event-detail',
    'events',
    'Northlight Cup',
    'Review broadcasts, corrections and the guide overlay.|Revisa emisiones, correcciones y superposición en guía.',
    '/events?event=demo&zone=Europe/Madrid',
    'frontend/src/components/events/EventDetails.tsx',
    319,
    [
        facts('Event details|Detalles', [('Participants|Participantes', 'Northlight United · Atelier City'), ('Time|Hora', '8 Nov 18:00 · Europe/Madrid · provider observation|8 nov 18:00 · Europe/Madrid · dato del proveedor'), ('Following|Seguimiento', 'Installation-wide|Toda la instalación')]),
        rows(
            'Broadcasts|Emisiones',
            [
                ('Atelier', 'Two regional channel choices; not yet playable|Dos opciones regionales; aún no reproducible', 'event-mapping'),
                ('Event-only HTTP|HTTP solo para evento', 'Supported media may open the shared player without TV assignment or playlist export.|Contenido compatible puede abrir el reproductor sin asignación TV ni exportación.', 'live'),
            ],
        ),
        command('Follow event|Seguir evento', 'Follow for everyone using this installation?|¿Seguir para toda la instalación?', 'Event followed for the installation.|Evento seguido para toda la instalación.'),
        command('Archive event|Archivar evento', 'Hide from the ordinary agenda? Unarchive remains possible until opt-in retention deletes it.|¿Ocultar de la agenda habitual? Se puede recuperar hasta que lo borre la conservación opcional.', 'Archived. Unarchive is available.|Archivado. Se puede recuperar.'),
        links(('event-correct', 'Correct event details|Corregir datos'), ('event-mapping', 'Choose broadcaster link|Elegir vínculo de emisora'), ('event-overlay', 'Review guide overlay|Revisar superposición en guía')),
    ],
)
screen(
    'event-provider',
    'events',
    'Add provider events|Añadir eventos de proveedor',
    'Choose source filters before fetching; review new events before importing.|Elige filtros antes de consultar y revisa eventos nuevos antes de importar.',
    '/events',
    'frontend/src/components/events/EventProviderFields.tsx',
    319,
    [
        form(
            'provider',
            'Provider selection|Selección de proveedor',
            [
                field('provider.provider', 'Provider|Proveedor', 'Fixed guarded adapters, not an arbitrary executable plugin.|Adaptadores fijos protegidos, no plugins ejecutables arbitrarios.', 'wosti', 'select', options=['wosti|WOSTI Spain|WOSTI España', 'openfootball|OpenFootball|OpenFootball']),
                field('provider.feeds', 'Sports feeds|Fuentes deportivas', 'WOSTI default all + automovilismo; original enum values preserved.|WOSTI por defecto all + automovilismo; conserva los valores.', 'all,automovilismo'),
                field('provider.football_competitions', 'Football competitions|Competiciones de fútbol', 'Remove All sports to narrow football upstream requests; other selected sports remain.|Quita Todos los deportes para limitar fútbol; conserva los otros deportes.', '', advanced=True),
                field('provider.league', 'League|Liga', 'OpenFootball league; preserve es.1 default where selected.|Liga OpenFootball; conserva es.1 por defecto.', 'es.1', advanced=True),
                field('provider.season', 'Season|Temporada', 'Current season from source; format 2026-27.|Temporada de fuente; formato 2026-27.', '2026-27', pattern='20[0-9]{2}-[0-9]{2}', advanced=True),
                field('provider.window_days', 'Import window (days)|Ventana de importación (días)', 'Default 14; 1–30.|Por defecto 14; 1–30.', 14, 'number', min=1, max=30),
                field('provider.timezone', 'Source timezone|Zona horaria de fuente', 'WOSTI uses Europe/Madrid. Date-only fixtures keep kickoff unknown.|WOSTI usa Europe/Madrid. Las fechas sin hora mantienen inicio desconocido.', 'Europe/Madrid'),
                field('provider.interests.sports', 'Interested sports|Deportes de interés', 'OR with teams and competitions; preserve outside-filter data.|O con equipos y competiciones; conserva datos fuera del filtro.', '', advanced=True),
                field('provider.interests.competitions', 'Interested competitions|Competiciones de interés', 'Up to 100 original values.|Hasta 100 valores originales.', '', advanced=True),
                field('provider.interests.teams', 'Interested teams|Equipos de interés', 'Up to 100 original values.|Hasta 100 valores originales.', '', advanced=True),
            ],
            'Preview events|Ver eventos',
            'Preview only. WOSTI changed dates/times require review; never silently merge as rescheduling.|Solo vista previa. Cambios de fecha/hora WOSTI requieren revisión; no se fusionan como reprogramación.',
            'eventService provider preview',
            local=True,
            next='event-review',
        )
    ],
)
screen(
    'event-import',
    'events',
    'Add events|Añadir eventos',
    'Manual, URL and JSON paths share the reviewed import contract.|Los flujos manual, URL y JSON comparten la importación revisada.',
    '/events',
    'frontend/src/components/events/EventImportPanel.tsx',
    319,
    [
        form(
            'event-import',
            'Input|Entrada',
            [
                field('event.input', 'Add from|Añadir desde', 'Choose manual entry, URL, JSON or reviewed W3U event handoff.|Elige manual, URL, JSON o enlace revisado desde W3U.', 'manual', 'select', options=['manual|Manual|Manual', 'url|Schedule URL|URL de agenda', 'json|Schedule JSON|JSON de agenda']),
                *EVENT_FIELDS,
                field('event.schedule_url', 'Schedule URL|URL de agenda', 'Guarded bounded fetch. New identities always require review.|Consulta limitada protegida. Las identidades nuevas requieren revisión.', '', advanced=True),
                field(
                    'event.format',
                    'Guide format|Formato de agenda',
                    'Version-1 event import or SportsEvent JSON/HTML JSON-LD.|Importación v1 o SportsEvent JSON/HTML JSON-LD.',
                    'event_import',
                    'select',
                    options=['event_import|EventImport v1|EventImport v1', 'sports_event|SportsEvent JSON-LD|SportsEvent JSON-LD'],
                    advanced=True,
                ),
                field('event.json', 'Event schedule JSON|JSON de agenda', 'Up to 500 observations per import. Stable source/external IDs; explicit offset for ambiguous time.|Hasta 500 observaciones. IDs estables; desfase explícito para hora ambigua.', '', kind='textarea', advanced=True),
                field('event.timeout_seconds', 'Request timeout (seconds)|Tiempo de espera (segundos)', '5–300; saved for URL previews and refreshes.|5–300; se guarda para consultas y actualizaciones.', 30, 'number', min=5, max=300, advanced=True),
            ],
            'Preview import|Ver importación',
            'Read-only preview. No permanent channel is created for an event-only broadcast.|Vista sin cambios. Una emisión de evento no crea un canal permanente.',
            'eventService preview',
            local=True,
            next='event-review',
        )
    ],
)
screen(
    'event-review',
    'events',
    'Review new events|Revisar eventos nuevos',
    'Select specific event identities; no row is preselected.|Selecciona identidades concretas; ninguna fila está preseleccionada.',
    '/events',
    'frontend/src/components/events/EventImportPanel.tsx',
    319,
    [
        choices(
            'Event observations|Observaciones',
            [('event1', 'Northlight Cup', '8 Nov · 18:00 Europe/Madrid · new|8 nov · 18:00 Europe/Madrid · nuevo'), ('event2', 'World friendly', '8 Nov · kickoff unknown · date only|8 nov · hora desconocida · solo fecha')],
            'Import selected events|Importar eventos seleccionados',
            'Import only selected IDs under the current token. Existing corrections and missing broadcasts are preserved.|Importa IDs elegidos con token actual. Conserva correcciones y emisiones ausentes.',
        ),
        form(
            'event-refresh',
            'Refresh scope|Ámbito de actualización',
            [
                field(
                    'event.refresh_source', 'Refresh reviewed events automatically|Actualizar automáticamente eventos revisados', 'Opt-in for eligible URL/provider sources. W3U event schedules do not auto-refresh.|Opcional en URL/proveedores aptos. Las agendas de eventos W3U no se actualizan solas.', False, 'checkbox'
                )
            ],
            'Include refresh preference|Incluir preferencia',
            'Sent with the explicit selected import, not a separate silent import of new rows.|Se envía con la importación seleccionada, sin importar filas nuevas en silencio.',
            'EventApply.refresh_source',
            local=True,
        ),
    ],
    states={'conflict': 'The preview token or source revision changed. Select again from a fresh preview; existing events are retained.|Cambió el token o revisión. Selecciona de una vista nueva; se conservan eventos existentes.'},
)
screen(
    'event-correct',
    'events',
    'Correct Northlight Cup|Corregir Northlight Cup',
    'Manual corrections survive provider refresh.|Las correcciones manuales sobreviven a actualizaciones.',
    '/events?event=demo',
    'frontend/src/components/events/EventDetails.tsx',
    319,
    [
        form(
            'correction',
            'Manual correction|Corrección manual',
            EVENT_FIELDS[:5]
            + [
                field('event.participants', 'Participants|Participantes', 'Up to 8 original participant names.|Hasta 8 nombres originales.', 'Northlight United, Atelier City'),
                field('event.ends_at', 'End|Fin', 'Optional; explicit timezone-aware time if known.|Opcional; hora con zona explícita si se conoce.', ''),
                field('event.time_notes', 'Time notes|Notas de horario', 'Up to 500 characters; explain uncertainty instead of inventing kickoff.|Hasta 500 caracteres; explica incertidumbre sin inventar hora.', ''),
                field(
                    'event.state',
                    'Reported state|Estado comunicado',
                    'Provider/manual observation, never inferred from clock alone.|Dato de proveedor/manual, nunca deducido solo del reloj.',
                    'unknown',
                    'select',
                    options=['unknown|Unknown|Desconocido', 'scheduled|Scheduled|Programado', 'live|Reported live|Directo comunicado', 'finished|Finished|Finalizado', 'cancelled|Cancelled|Cancelado'],
                ),
            ],
            'Save correction|Guardar corrección',
            'Revision-checked correction saved. Source identity and original observations remain separate.|Corrección guardada con revisión. Identidad y observaciones originales siguen separadas.',
            'eventService.update',
        )
    ],
)
screen(
    'event-mapping',
    'events',
    'Link the broadcaster Atelier|Vincular la emisora Atelier',
    'Choose a regional target and the exact scope of this correction.|Elige destino regional y ámbito exacto de la corrección.',
    '/events?event=demo',
    'frontend/src/components/events/EventBroadcastMapper.tsx',
    319,
    [
        form(
            'broadcast-link',
            'Destination and scope|Destino y ámbito',
            [
                field(
                    'broadcast.apply_to_source',
                    'Apply to every event from this source with this broadcaster|Aplicar a todos los eventos de esta fuente con esta emisora',
                    'Current default on. An event-only override wins over a source alias.|Activado por defecto. Una excepción del evento prevalece sobre el alias de fuente.',
                    True,
                    'checkbox',
                ),
                field(
                    'broadcast.mode',
                    'Link to|Vincular a',
                    'TV/guide identity or individual stream. Names and source qualifiers remain visible.|Identidad de TV/guía o emisión individual. Conserva nombres y fuentes.',
                    'channels',
                    'select',
                    options=['channels|TV or guide channel|Canal de TV o guía', 'stream|Individual stream|Emisión individual'],
                ),
                field(
                    'broadcast.target',
                    'Target|Destino',
                    'Choose explicitly among country/source-qualified identities.|Elige expresamente entre identidades con país y fuente.',
                    '',
                    'select',
                    options=['|Choose a target|Elige destino', 'tv:3|Atelier · ES · TV|Atelier · ES · TV', 'epg:4|Atelier · FR · Regional guide|Atelier · FR · Regional guide'],
                    required=True,
                ),
            ],
            'Save broadcaster link|Guardar vínculo',
            'Source alias or event override saved according to the chosen scope; a channel link does not prove signal.|Alias o excepción guardada según ámbito; un vínculo no demuestra señal.',
            'eventService broadcaster mapping',
            intent=True,
        ),
        command(
            'Use source broadcast for this event|Usar emisión original para este evento',
            'Keep the source broadcast here instead of its alias? Store the explicit none override.|¿Conservar aquí la emisión original en vez del alias? Guarda la excepción none explícita.',
            'Event uses its source broadcast. Other events keep the alias.|El evento usa su emisión original. Otros conservan el alias.',
        ),
    ],
)
screen(
    'event-overlay',
    'events',
    'Review XMLTV overlay|Revisar superposición XMLTV',
    'Preview affected programme slots before adding an event to exported guide data.|Revisa programas afectados antes de añadir el evento a la guía exportada.',
    '/events?event=demo',
    'frontend/src/components/events/EventGuideOverlay.tsx',
    319,
    [
        form(
            'overlay',
            'Overlay interval|Intervalo de superposición',
            [
                field('overlay.broadcast_id', 'Linked broadcast|Emisión vinculada', 'Only a resolved channel/guide target is eligible.|Solo es apto un destino de canal/guía resuelto.', 'atelier', 'select', options=['atelier|Atelier → Sample guide : atelier.example|Atelier → Sample guide : atelier.example']),
                field('overlay.ends_at', 'Overlay end with UTC offset|Fin con desfase UTC', 'Explicit end required; maximum 12 hours. Does not change the event’s reported end.|Fin explícito; máximo 12 horas. No cambia el fin comunicado del evento.', '2026-11-08T20:00:00+01:00', required=True),
            ],
            'Preview overlay|Ver superposición',
            'Preview returns a fingerprint. Apply must match the same event revision, time and target.|Devuelve una huella. Aplicar exige misma revisión, horario y destino.',
            'eventService overlay preview',
            local=True,
        ),
        rows('Affected exported interval|Intervalo exportado afectado', [('18:00–20:00 · Northlight Cup', 'Original guide rows and recording IDs remain intact|Se conservan filas originales e IDs de grabación', None)]),
        command(
            'Apply reviewed overlay|Aplicar superposición revisada',
            'Apply only this preview fingerprint? Changed schedule or target suspends the overlay.|¿Aplicar solo esta huella? Cambios de horario o destino suspenden la superposición.',
            'Overlay applied to export. Original guide rows remain.|Superposición aplicada a exportación. Se conservan programas originales.',
        ),
    ],
    states={'conflict': 'Preview fingerprint changed. Nothing applied; review the new interval and target.|Cambió la huella. No se aplicó nada; revisa nuevo intervalo y destino.'},
)
screen(
    'event-sources',
    'events',
    'Event sources and retention|Fuentes de eventos y conservación',
    'Refresh reviewed identities; keep new events for manual review.|Actualiza identidades revisadas; reserva eventos nuevos para revisión.',
    '/events',
    'frontend/src/components/events/EventSourcesPanel.tsx',
    319,
    [
        rows('Saved sources|Fuentes guardadas', [('Demo schedule', 'Enabled · 14-day window · reviewed identities only|Activada · 14 días · solo identidades revisadas', 'event-provider')]),
        form(
            'event-retention',
            'Automatic deletion|Eliminación automática',
            [
                field('events.ended_days', 'Keep ended events (days)|Conservar eventos terminados (días)', '0 disables; 1–3650 days. Followed events are protected.|0 desactiva; 1–3650 días. Los eventos seguidos están protegidos.', 0, 'number', min=0, max=3650),
                field('events.archived_days', 'Keep archived events (days)|Conservar archivados (días)', '0 disables. Archive can be reversed before retention deletes eligible rows.|0 desactiva. Se puede desarchivar antes de que la conservación borre filas elegibles.', 0, 'number', min=0, max=3650),
            ],
            'Save event retention|Guardar conservación',
            'Retention saved; applies during existing daily cleanup, not immediately on this screen.|Conservación guardada; se aplica en limpieza diaria, no inmediatamente aquí.',
            'eventService retention',
        ),
        command(
            'Remove event source|Eliminar fuente de eventos',
            'Remove its refresh configuration? Imported events, corrections and broadcasts remain.|¿Eliminar su configuración de actualización? Se conservan eventos, correcciones y emisiones.',
            'Source removed; imported events retained.|Fuente eliminada; eventos conservados.',
            danger=True,
        ),
        links(('event-mapping', 'Manage source broadcaster aliases|Gestionar alias de emisoras')),
    ],
)
screen(
    'connections',
    'integrations',
    'Where would you like to watch?|¿Dónde quieres ver la TV?',
    'Each destination keeps its own setup and access rules.|Cada destino conserva su configuración y acceso.',
    'proposed orientation layer',
    'frontend/src/components/integrations/IntegrationPage.tsx',
    322,
    [
        rows(
            'Choose a destination|Elige un destino',
            [
                ('Browser|Navegador', 'Availability and sessions|Disponibilidad y sesiones', 'browser-player'),
                ('Google Cast TV', 'Home receivers and original-video compatibility|Receptores y compatibilidad', 'casting'),
                ('VLC / Kodi', 'Manual entry and remote opt-in|Alta manual y activación remota', 'remote-player'),
                ('Plex / Jellyfin', 'Tuner, playlists and guide|Sintonizador, listas y guía', 'media-server'),
            ],
        ),
        links(('public-address', 'Address for players|Dirección para reproductores'), ('telegram-auth', 'Telegram sources|Fuentes Telegram'), ('notifications', 'Notifications|Notificaciones')),
    ],
)
screen(
    'browser-player',
    'integrations',
    'Browser player|Reproductor web',
    'Read capabilities without starting playback.|Consulta capacidades sin iniciar reproducción.',
    '/integrations/web-player',
    'frontend/src/components/integrations/WebPlayerSection.tsx',
    322,
    [
        facts('Synthetic capabilities|Capacidades ficticias', [('Player|Reproductor', 'Available · FFmpeg ready|Disponible · FFmpeg listo'), ('Sessions|Sesiones', '1 of 3|1 de 3'), ('Route|Ruta', 'Direct · active sessions keep their original route|Directa · sesiones activas conservan su ruta')]),
        rows('Playing|En reproducción', [('Northlight HD', '2 viewers · matching audio/subtitles share a session|2 espectadores · mismas pistas comparten sesión', None)]),
        links(('live', 'Open Live TV|Abrir TV en directo'), ('playback-settings', 'Playback settings|Ajustes de reproducción'), ('runtime-playback', 'Capacity and startup budget|Capacidad y tiempo de inicio')),
    ],
    states={'unavailable': 'Show the reported missing capability; HTTP media can work without AceStream.|Muestra la capacidad que falta; HTTP puede funcionar sin AceStream.', 'partial': 'Session query failed. Viewer count is unknown, not zero.|Falló la consulta de sesiones. Cantidad desconocida, no cero.'},
)
screen(
    'public-address',
    'integrations',
    'Address for players|Dirección para reproductores',
    'One saved address, with the correct proxy prefix.|Una dirección guardada, con prefijo de proxy correcto.',
    '/integrations/public-address',
    'frontend/src/components/integrations/PublicAddressSection.tsx',
    322,
    [
        facts('Effective address · synthetic|Dirección efectiva · ficticia', [('Address|Dirección', 'https://tv.example.invalid/app'), ('Source|Origen', 'Saved override|Valor guardado'), ('Runtime fallback|Alternativa de ejecución', 'Empty|Vacío')]),
        form(
            'address',
            'Saved override|Dirección guardada',
            [field('address.public_base_url', 'Player-facing address|Dirección para reproductores', 'HTTP(S), no credentials or fragment. Preserve proxy prefix. Empty removes this override.|HTTP(S), sin credenciales ni fragmento. Conserva prefijo. Vacío elimina este valor.', 'https://tv.example.invalid/app', 'url')],
            'Save address|Guardar dirección',
            'New generated links use this address; copied links are unchanged.|Los enlaces nuevos usan esta dirección; los copiados no cambian.',
            'configService public-base-url',
        ),
        links(('playlist', 'Playlist context|Contexto de lista'), ('casting-settings', 'TV-specific override|Dirección específica para TV'), ('runtime-network', 'Runtime precedence|Prioridad de ejecución')),
    ],
)
screen(
    'casting',
    'integrations',
    'TV casting|Enviar a TV',
    'Find Google Cast receivers on the permitted home connection.|Busca receptores Google Cast desde la conexión permitida.',
    '/integrations/tv-casting',
    'frontend/src/pages/integrations/TvCasting.tsx',
    322,
    [
        facts('Synthetic access|Acceso ficticio', [('Connection|Conexión', 'Verified private connection|Conexión privada verificada'), ('Permission|Permiso', 'cast_server'), ('Discovery|Búsqueda', 'Bounded multicast / private server IPv4 /24|Multidifusión limitada / IPv4 privada del servidor /24')]),
        command('Find TVs|Buscar televisores', 'Search the bounded home network? Up to 20 seconds.|¿Buscar en la red doméstica limitada? Hasta 20 segundos.', 'Fixture discovery found Living room DEMO.|La búsqueda ficticia encontró Living room DEMO.'),
        rows('Receivers|Receptores', [('Living room DEMO', 'Synthetic receiver|Receptor ficticio', 'casting-control')]),
        links(('casting-settings', 'Casting settings|Ajustes de TV'), ('casting-trust', 'Public HTTPS at home|HTTPS público desde casa'), ('live', 'Choose a channel|Elegir canal')),
    ],
    permission='cast capabilities / server devices / effective home rule',
    states={
        'empty': 'No TVs found. Turn on the TV and enable Cast. Check reachability; current source has no manual Cast-device editor.|No se encontraron TVs. Enciende la TV y activa Cast. Revisa la red; no existe editor manual de receptores Cast.',
        'denied': 'This connection or account cannot control server TVs. Show the capability reason; retry is not permission.|Esta conexión o cuenta no puede controlar TVs. Muestra el motivo; reintentar no concede permiso.',
    },
)
screen(
    'casting-settings',
    'integrations',
    'Casting settings|Ajustes de TV',
    'Original video is the default.|El vídeo original es la opción inicial.',
    '/integrations/tv-casting',
    'frontend/src/pages/integrations/TvCasting.tsx',
    322,
    [
        form(
            'cast-settings',
            'Video and connection|Vídeo y conexión',
            [
                field('cast.compatibility_conversion', 'Offer H.264 conversion|Ofrecer conversión H.264', 'Off; at most one 720p/30 fps stream. CPU conversion yields to recordings.|Desactivada; máximo una emisión 720p/30 fps. Cede recursos a grabaciones.', False, 'checkbox'),
                field('cast.cast_media_url', 'Application address for TVs|Dirección de app para TVs', 'Optional, max 2048; blank uses browser address. Preserve proxy prefix.|Opcional, máximo 2048; vacío usa dirección del navegador. Conserva prefijo.', '', advanced=True, maxlength=2048),
                field('cast.home_networks', 'Allowed home visitor networks|Redes domésticas de visitantes', 'Max 16 CIDRs; visitors, not TV IPs. Blank preserves automatic private recognition.|Máximo 16 CIDR; visitantes, no IPs de TVs. Vacío conserva reconocimiento privado.', '', advanced=True),
                field(
                    'cast.remote_casting', 'Allow permitted accounts away from home|Permitir cuentas autorizadas fuera de casa', 'Requires accounts and explicit opt-in. Never enables public HTTP accounts.|Requiere cuentas y activación explícita. Nunca permite cuentas por HTTP público.', False, 'checkbox', advanced=True
                ),
            ],
            'Save casting settings|Guardar ajustes de TV',
            'Saved independently of IPTV and proxy trust.|Guardado independientemente de IPTV y confianza de proxy.',
            'castService.saveSettings',
        )
    ],
    permission='administrator / recognized open-mode configuration capability',
)
screen(
    'casting-trust',
    'integrations',
    'Public HTTPS at home|HTTPS público desde casa',
    'Review the scope before trusting this connection.|Revisa el ámbito antes de confiar en la conexión.',
    '/integrations/tv-casting',
    'frontend/src/pages/integrations/TvCasting.tsx',
    322,
    [
        note('Shared internet connections share this trust. Repeat if your public address changes. Never permits accounts on public HTTP.|Las conexiones compartidas comparten confianza. Repite si cambia la dirección. Nunca permite cuentas por HTTP público.', 'warning'),
        form(
            'trust',
            'Home confirmation|Confirmación doméstica',
            [field('cast.trust_home', 'I am on my home network now|Estoy en mi red doméstica', 'Admin only; not needed for a verified private-IP connection.|Solo administrador; innecesario en conexión privada verificada.', False, 'checkbox', required=True)],
            'Trust this connection|Confiar en esta conexión',
            'Saved for Cast only.|Guardado solo para Cast.',
            'castService.trustHome',
            intent=True,
        ),
    ],
    permission='administrator / public HTTPS / home not yet verified',
)
screen(
    'casting-control',
    'integrations',
    'Living room DEMO',
    'Control only the exact media owned by this app.|Controla solo el contenido exacto de esta app.',
    'player casting options',
    'frontend/src/components/player/CastControls.tsx',
    322,
    [
        facts('Synthetic owned media|Contenido propio ficticio', [('Channel|Canal', 'Northlight'), ('Mode|Modo', 'Original video|Vídeo original'), ('Ownership|Propiedad', 'Exact media ID verified|ID exacto verificado')]),
        form(
            'cast-control',
            'Playback options|Opciones',
            [
                field('cast.compatibility', 'Compatible video for this cast|Vídeo compatible para este envío', 'Only if offered and capacity permits.|Solo si está disponible y hay capacidad.', False, 'checkbox'),
                field('cast.volume', 'Volume (%)|Volumen (%)', 'Display 0–100; API 0–1. Immediate owned-session command.|Muestra 0–100; API 0–1. Orden inmediata de sesión propia.', 50, 'range', min=0, max=100),
            ],
            'Apply example control|Aplicar control ficticio',
            'Owned command acknowledged in fixture.|Orden propia confirmada en ejemplo.',
            'castService.command',
            local=True,
        ),
        command(
            'Stop this cast|Detener envío',
            'Stop only if this exact owned media is still playing. Never stop another app’s replacement.|Detén solo si sigue el contenido propio exacto. Nunca detengas su sustitución por otra app.',
            'Owned cast stopped. Browser ownership remains separate.|Envío propio detenido. Navegador independiente.',
        ),
        command('Replace receiver media|Sustituir contenido del receptor', 'Explicitly replace the receiver’s current media with Northlight?|¿Sustituir expresamente el contenido actual por Northlight?', 'Replacement requested with replace=true.|Sustitución solicitada con replace=true.'),
    ],
    states={
        'ownership-lost': 'TV now plays other media. Stop/cleanup must leave it alone.|La TV reproduce otro contenido. Detener/limpiar debe respetarlo.',
        'recording-priority': 'Conversion yielded to recording. Show whether original playback is still available.|La conversión cedió a grabación. Indica si el original sigue disponible.',
    },
)
REMOTE = [
    field('remote.name', 'Player name|Nombre del reproductor', '1–255 characters; duplicate names rejected.|1–255 caracteres; duplicados rechazados.', 'Study DEMO', required=True, maxlength=255),
    field('remote.kind', 'Player|Reproductor', 'Each driver uses its own credentials.|Cada controlador usa sus credenciales.', 'vlc', 'select', options=['vlc|VLC desktop|VLC escritorio', 'vlc_android|VLC Android 3.6+|VLC Android 3.6+', 'kodi|Kodi|Kodi']),
    field('remote.host', 'Host|Host', 'Private hostname or IP, no scheme. Changing host/port clears authentication.|Nombre o IP privada, sin protocolo. Cambiar host/puerto borra autenticación.', 'player.example.invalid', required=True),
    field('remote.port', 'Port|Puerto', '1–65535; desktop 8080, Android 8443.|1–65535; escritorio 8080, Android 8443.', 8080, 'number', min=1, max=65535),
    field('remote.username', 'Kodi username|Usuario Kodi', 'Kodi only; default kodi.|Solo Kodi; por defecto kodi.', 'kodi', advanced=True),
    field('remote.password', 'Player password|Contraseña del reproductor', 'Blank keeps a saved password only at an unchanged address.|Vacío conserva contraseña solo si no cambió la dirección.', '', 'password'),
    field('remote.base_url_id', 'Stream link format|Formato de enlace', 'Default relay. Acexy always uses relay; direct honors supported formats.|Por defecto app. Acexy siempre usa app; directo respeta formatos.', '', 'select', options=['|Server relay|A través de la app', 'demo|Demo format|Formato de ejemplo']),
]
screen(
    'remote-player',
    'integrations',
    'Set up VLC or Kodi|Configurar VLC o Kodi',
    'Saving a player does not start playback.|Guardar un reproductor no inicia reproducción.',
    '/integrations/remote-players',
    'frontend/src/components/integrations/RemotePlayerDialog.tsx',
    322,
    [
        form('remote', 'Player connection|Conexión', REMOTE, 'Save player|Guardar reproductor', 'Saved. Probe and playback remain explicit actions.|Guardado. Consulta y reproducción siguen siendo explícitas.', 'remotePlayerService create / update'),
        command('Test connection|Probar conexión', 'Probe without starting media?|¿Consultar sin iniciar contenido?', 'Fixture reachable; authentication and control capabilities are separate.|Ejemplo accesible; autenticación y capacidades independientes.'),
        links(('remote-android', 'VLC Android pairing|Vincular VLC Android'), ('remote-discovery', 'Find players|Buscar reproductores'), ('remote-control', 'Playback and controls|Reproducción y controles')),
    ],
)
screen(
    'remote-android',
    'integrations',
    'Pair VLC Android|Vincular VLC Android',
    'Enable Remote access and playback control in VLC; verify its certificate.|Activa acceso remoto y control en VLC; verifica su certificado.',
    '/integrations/remote-players',
    'frontend/src/components/integrations/RemotePlayerDialog.tsx',
    322,
    [
        facts('Synthetic device check|Comprobación ficticia', [('Host', 'android.example.invalid:8443'), ('Certificate fingerprint|Huella', 'DEMO — NOT A DEVICE'), ('Code validity|Validez', '60 seconds; request another if expired|60 segundos; solicita otro si caduca')]),
        form(
            'android-pair',
            'Device code|Código del dispositivo',
            [field('android.code', 'Six-digit code|Código de seis cifras', 'From VLC Android; not a browser-pairing requirement for accounts or Cast.|De VLC Android; no es requisito de vinculación de navegador para cuentas o Cast.', '', 'text', required=True, pattern='[0-9]{6}', maxlength=6)],
            'Pair Android|Vincular Android',
            'Paired; still save the player to retain the connection.|Vinculado; guarda el reproductor para conservar conexión.',
            'remotePlayerService.finishAndroidPairing',
            intent=True,
        ),
        links(('remote-player', 'Save paired player|Guardar reproductor')),
    ],
    states={'expired': 'Code expired. Request a new challenge; never silently reuse it.|Código caducado. Solicita otro desafío; nunca reutilices en silencio.', 'changed-host': 'Address changed. Clear the challenge and verify the new certificate.|Cambió dirección. Borra desafío y verifica nuevo certificado.'},
)
screen(
    'remote-discovery',
    'integrations',
    'Find remote players|Buscar reproductores remotos',
    'Bounded private scan; review before saving.|Búsqueda privada limitada; revisa antes de guardar.',
    '/integrations/remote-players',
    'frontend/src/components/integrations/FindPlayersDialog.tsx',
    322,
    [
        form(
            'scan',
            'Scan scope|Ámbito',
            [
                field('scan.cidr', 'Private network (CIDR)|Red privada (CIDR)', 'Max 1024 addresses; default guessed /24. No public scan.|Máximo 1024 direcciones; sugiere /24. Sin búsqueda pública.', '192.168.50.0/24', required=True),
                field('scan.ports', 'Ports|Puertos', 'Up to 8, each 1–65535; default 8080.|Hasta 8, cada uno 1–65535; por defecto 8080.', '8080'),
                field('scan.timeout_ms', 'Timeout per attempt (ms)|Espera por intento (ms)', 'Default 400; 50–5000.|Por defecto 400; 50–5000.', 400, 'number', min=50, max=5000),
            ],
            'Find players|Buscar reproductores',
            'Suggestions only. Review and save each destination.|Solo sugerencias. Revisa y guarda cada destino.',
            'remotePlayerService.scan',
            local=True,
        ),
        rows('Synthetic result|Resultado ficticio', [('Study DEMO', 'Possible VLC; inspect credentials|Posible VLC; revisa credenciales', 'remote-player')]),
    ],
)
screen(
    'remote-control',
    'integrations',
    'Send to a player|Enviar a reproductor',
    'Local app handoff and remote control are separate.|Apertura local y control remoto son independientes.',
    'PlayOnMenu',
    'frontend/src/components/player/PlayOnMenu.tsx',
    322,
    [
        rows('Destinations|Destinos', [('Open local VLC|Abrir VLC local', 'Browser may ask to open an installed app|El navegador puede pedir abrir una app', None), ('Study DEMO', 'Account and explicit player opt-in required|Requiere cuenta y activación expresa', 'remote-player')]),
        form(
            'remote-command',
            'Control Study DEMO|Controlar Study DEMO',
            [
                field('remote.command', 'Command|Orden', 'Android supports pause/resume/volume; stop on the device.|Android admite pausa/reanudación/volumen; detén en el dispositivo.', 'pause', 'select', options=['pause|Pause|Pausar', 'resume|Resume|Reanudar', 'volume|Volume|Volumen']),
                field('remote.volume', 'Volume (%)|Volumen (%)', 'API 0–200; respect actual driver capability.|API 0–200; respeta capacidades del controlador.', 50, 'number', min=0, max=200),
            ],
            'Send command|Enviar orden',
            'Command acknowledged; receiving app owns playback state.|Orden confirmada; la app receptora informa del estado.',
            'remotePlayerService.command',
            local=True,
        ),
    ],
    states={
        'denied': 'Requires an account and explicit opt-in. Public viewing and Cast trust do not grant remote control.|Requiere cuenta y activación expresa. Acceso público y confianza Cast no conceden control remoto.',
        'handoff': 'App opening requested; do not claim playback started. Offer copy if the app did not open.|Apertura solicitada; no afirmes reproducción. Ofrece copiar si no se abrió.',
    },
)
MEDIA = [
    field('media.kind', 'Media server|Servidor multimedia', 'Kind is locked when editing.|Tipo bloqueado al editar.', 'jellyfin', 'select', options=['jellyfin|Jellyfin|Jellyfin', 'plex|Plex|Plex']),
    field('media.name', 'Name|Nombre', '1–255; duplicate names rejected.|1–255; duplicados rechazados.', 'Home cinema DEMO', required=True),
    field('media.base_url', 'Address|Dirección', 'As reached from scraper; max 1024 characters.|Accesible desde scraper; máximo 1024 caracteres.', 'https://media.example.invalid', 'url', required=True),
    field('media.api_key', 'API key or owner token|Clave API o token', 'Jellyfin needs admin key; Plex token optional for auto refresh. Blank keeps saved secret.|Jellyfin necesita clave; token Plex opcional para actualizar. Vacío conserva secreto.', '', 'password'),
    field(
        'media.tuner_mode',
        'How channels reach Jellyfin|Cómo llegan canales a Jellyfin',
        'HDHomeRun preserves identity. Changing M3U address/format recreates channels and loses favorites.|HDHomeRun conserva identidad. Cambiar dirección/formato M3U recrea canales y pierde favoritos.',
        'hdhomerun',
        'select',
        options=['hdhomerun|HDHomeRun tuner|Sintonizador HDHomeRun', 'm3u|M3U + XMLTV|M3U + XMLTV'],
    ),
    field('media.auto_refresh', 'Refresh guide on channel changes|Actualizar guía al cambiar canales', 'On by default; runtime debounce still applies.|Activado por defecto; respeta intervalo mínimo.', True, 'checkbox'),
]
screen(
    'media-server',
    'integrations',
    'Connect a media server|Conectar servidor multimedia',
    'Save, test and connect have separate outcomes.|Guardar, probar y conectar tienen resultados separados.',
    '/integrations/media-servers',
    'frontend/src/components/integrations/MediaServerDialog.tsx',
    322,
    [
        form('media', 'Plex / Jellyfin', MEDIA, 'Save server|Guardar servidor', 'Definition saved; no connection created yet.|Definición guardada; sin conexión creada.', 'mediaServerService create / update'),
        command('Test connection|Probar conexión', 'Probe address and credentials without connecting tuner?|¿Probar dirección y credenciales sin conectar sintonizador?', 'Fixture probe succeeded.|Consulta ficticia correcta.'),
        command('Connect tuner|Conectar sintonizador', 'Configure this app’s tuner and guide in the server?|¿Configurar sintonizador y guía en el servidor?', 'Connected in fixture; guide refresh remains pending.|Conectado en ejemplo; guía pendiente.'),
        command('Disconnect tuner|Desconectar sintonizador', 'Remove app-managed connection; keep saved server definition?|¿Quitar conexión gestionada y conservar definición?', 'Disconnected; definition retained.|Desconectado; definición conservada.', danger=True),
        links(('tuner', 'Tuner limits and output|Límites y salida')),
    ],
)
screen(
    'tuner',
    'integrations',
    'Tuner settings|Ajustes de sintonizador',
    'Stable channel IDs and bounded startup.|IDs estables e inicio limitado.',
    '/integrations/media-servers',
    'frontend/src/components/integrations/MediaServersSection.tsx',
    322,
    [
        form(
            'tuner',
            'Capacity and compatibility|Capacidad y compatibilidad',
            [
                field('tuner.friendly_name', 'Tuner name|Nombre del sintonizador', 'Shown in Plex/Jellyfin; max 255.|Visible en Plex/Jellyfin; máximo 255.', 'AceStream Scraper'),
                field('tuner.tuner_count', 'Streams at once|Emisiones simultáneas', '1–16; load saved value, example 2 is not a new default.|1–16; carga valor guardado, ejemplo 2 no es un defecto nuevo.', 2, 'number', min=1, max=16),
                field('tuner.max_channels', 'Most channels to publish|Máximo de canales', '1–1000; show omitted count. Plex constrained near 450–480.|1–1000; muestra omitidos. Plex limitado cerca de 450–480.', 400, 'number', min=1, max=1000),
                field('tuner.source_start_seconds', 'Seconds per source|Segundos por emisión', 'Default 15; 5–180; lock waiting consumes this budget.|Por defecto 15; 5–180; esperar bloqueos consume tiempo.', 15, 'number', min=5, max=180),
                field('tuner.startup_budget_seconds', 'Total startup seconds|Segundos totales de inicio', 'Default 45; 5–180. Below the player timeout.|Por defecto 45; 5–180. Menor que la espera del reproductor.', 45, 'number', min=5, max=180),
                field('tuner.only_online', 'Publish online only|Publicar solo con señal', 'Eligibility rules apply; deletes nothing.|Aplica elegibilidad; no elimina.', False, 'checkbox'),
                field('tuner.hide_unusable', 'Hide stale or repeatedly failing sources|Ocultar emisiones antiguas o con fallos repetidos', 'Off; lineup/M3U hiding only. Playlist URL may override.|Desactivado; solo oculta en listas. URL puede sobrescribir.', False, 'checkbox'),
                field('tuner.plex_compatible_audio', 'Plex Desktop compatible audio|Audio compatible Plex Desktop', 'Opt-in stereo AAC/LATM; video copy unless recovery enabled.|AAC/LATM estéreo opcional; copia vídeo salvo recuperación.', False, 'checkbox', advanced=True),
                field('tuner.experimental_transcoding', 'Experimental recovery|Recuperación experimental', 'Off; CPU-intensive. Normal mode requires client reconnection after failure.|Desactivada; usa CPU. Modo normal requiere reconectar tras fallo.', False, 'checkbox', advanced=True),
            ],
            'Save tuner settings|Guardar ajustes',
            'New connections use these settings; existing ownership remains.|Nuevas conexiones usan ajustes; se conserva propiedad existente.',
            'tunerService.updateSettings',
        ),
        facts('Synthetic publication|Publicación ficticia', [('Published / omitted|Publicados / omitidos', '3 / 0'), ('Renumbered|Renumerados', 'None|Ninguno'), ('Client allowed|Cliente permitido', 'Separate tuner network policy|Política de red de sintonizador independiente')]),
        links(('network', 'Tuner networks|Redes de sintonizador'), ('playlist', 'Playlist overrides|Opciones de lista')),
    ],
)
screen(
    'telegram-auth',
    'integrations',
    'Authorize Telegram sources|Autorizar fuentes Telegram',
    'This is a Telegram user session, separate from notification webhooks.|Es una sesión de usuario Telegram, independiente de notificaciones.',
    '/integrations/telegram',
    'frontend/src/components/integrations/TelegramSection.tsx',
    322,
    [
        note('Requires HTTPS or localhost and the dedicated Telegram admin header token. Private-IP HTTP support for ordinary accounts does not waive this rule.|Requiere HTTPS o localhost y token administrativo de Telegram en cabecera. El HTTP privado de cuentas normales no exime esta regla.', 'warning'),
        form(
            'telegram-auth',
            'Private authorization|Autorización privada',
            [
                field('telegram.admin_token', 'Telegram admin token|Token administrativo Telegram', 'Separate deployment credential; never include in URLs or captures.|Credencial de despliegue separada; nunca en URLs o capturas.', '', 'password', required=True),
                field('telegram.api_id', 'Telegram API ID|ID API Telegram', 'Integer 1–2147483647. Deployment must provide encrypted-session storage and key.|Entero 1–2147483647. Despliegue debe aportar almacén cifrado y clave.', '', 'number', min=1, max=2147483647, required=True),
                field('telegram.api_hash', 'Telegram API hash|Hash API Telegram', 'Exactly 32 characters; never redisplay a saved value.|Exactamente 32 caracteres; no se vuelve a mostrar.', '', 'password', minlength=32, maxlength=32, required=True),
                field('telegram.phone', 'Phone with country code|Teléfono con prefijo', '5–32 characters. Keep private.|5–32 caracteres. Privado.', '', 'tel', minlength=5, maxlength=32, required=True),
            ],
            'Request login code|Solicitar código',
            'Login code requested. Continue with the code step; no source import starts.|Código solicitado. Continúa con el código; no se importa.',
            'telegramService login',
            intent=True,
            next='telegram-code',
        ),
        links(('telegram-source', 'Source editor after authorization|Editor tras autorización')),
    ],
    permission='Telegram admin header + HTTPS/localhost + deployment readiness',
    states={
        'unavailable': 'Session key or encrypted storage is unavailable. Owner must fix deployment; do not ask for the API hash repeatedly.|No hay clave o almacén cifrado. El propietario debe corregir despliegue; no pidas hash repetidamente.',
        'flood': 'Telegram requires a wait. Show the server-provided retry time; keep source progress and prevent repeated login attempts.|Telegram exige esperar. Muestra plazo del servidor; conserva progreso y evita intentos repetidos.',
    },
)
screen(
    'telegram-code',
    'integrations',
    'Complete Telegram sign-in|Completar inicio Telegram',
    'Codes and passwords are never saved in logs or previews.|Códigos y contraseñas nunca van en registros o vistas previas.',
    '/integrations/telegram',
    'frontend/src/components/integrations/TelegramSection.tsx',
    322,
    [
        form(
            'telegram-code',
            'Login code|Código de acceso',
            [field('telegram.code', 'Telegram login code|Código Telegram', '1–16 characters; received through Telegram’s login flow.|1–16 caracteres; recibido en el flujo de acceso Telegram.', '', 'text', required=True, maxlength=16)],
            'Verify code|Verificar código',
            'Code verified. Two-step verification may still be required.|Código verificado. Puede faltar verificación en dos pasos.',
            'telegramService code',
            intent=True,
        ),
        form(
            'telegram-password',
            'Two-step verification when required|Dos pasos cuando se requiera',
            [field('telegram.password', 'Telegram two-step password|Contraseña de dos pasos Telegram', 'Only shown when required by the authorization response; up to 256 characters.|Solo si la respuesta la requiere; hasta 256 caracteres.', '', 'password', required=True, maxlength=256)],
            'Complete authorization|Completar autorización',
            'Encrypted user session ready. Credentials cleared from the form.|Sesión cifrada lista. Credenciales borradas del formulario.',
            'telegramService password',
            intent=True,
            next='telegram-source',
        ),
    ],
    permission='same Telegram transport/header gate',
)
screen(
    'telegram-source',
    'integrations',
    'Telegram source|Fuente Telegram',
    'Start with new messages; reading history is an explicit choice.|Empieza con mensajes nuevos; leer historial es una elección explícita.',
    '/integrations/telegram',
    'frontend/src/components/integrations/TelegramSourceEditor.tsx',
    322,
    [
        form(
            'telegram-source',
            'Chat and extraction|Chat y extracción',
            [
                field('telegram_source.name', 'Source name|Nombre de fuente', '1–100 characters.|1–100 caracteres.', 'Demo joined chat', required=True, maxlength=100),
                field(
                    'telegram_source.chat_id',
                    'Joined chat|Chat al que perteneces',
                    'Choose a joined chat; stable numeric ID is retained, not translated label.|Elige un chat al que perteneces; conserva ID numérico, no etiqueta traducida.',
                    '-1000000001',
                    'select',
                    options=['-1000000001|Demo joined chat|Demo joined chat'],
                ),
                field('telegram_source.topic_id', 'Topic|Tema', 'Optional positive topic ID; only supported chat topics are offered.|ID positivo opcional; solo se ofrecen temas compatibles.', '', 'number', min=1),
                field('telegram_source.username', 'Resolve Telegram username|Resolver usuario Telegram', 'Explicit lookup resolves stable sender identity; not a replacement for membership checks.|Consulta expresa resuelve identidad; no sustituye comprobación de pertenencia.', '', advanced=True),
                field('telegram_source.sender_ids', 'Allowed sender IDs|IDs de remitentes permitidos', 'Comma-separated stable IDs, at most 100. Empty accepts all senders.|IDs estables separados por comas, máximo 100. Vacío acepta todos.', '', advanced=True),
                field('telegram_source.include_forwards', 'Include forwarded messages|Incluir reenviados', 'On by default; sender rule chooses which identity is checked.|Activado; la regla elige qué identidad se comprueba.', True, 'checkbox'),
                field(
                    'telegram_source.sender_rule',
                    'Sender identity for forwards|Identidad en reenviados',
                    'Posting identity by default; preserve source options.|Identidad que publica por defecto; conserva opciones.',
                    'posting',
                    'select',
                    options=['posting|Posting sender|Quien publica', 'original|Original sender|Remitente original'],
                    advanced=True,
                ),
                field('telegram_source.filter_mode', 'Message filter mode|Modo de filtro', 'Keyword or bounded regex. Does not authorize an unbounded extraction worker.|Palabras o regex limitado. No permite trabajo sin límites.', 'keyword', 'select', options=['keyword|Keyword|Palabras', 'regex|Regex|Regex']),
                field('telegram_source.include', 'Must include|Debe incluir', 'Optional; up to 512 characters.|Opcional; hasta 512 caracteres.', '', maxlength=512),
                field('telegram_source.exclude', 'Must exclude|Debe excluir', 'Optional; up to 512 characters.|Opcional; hasta 512 caracteres.', '', maxlength=512),
                field('telegram_source.bare_ids', 'Recognize bare IDs in name/ID pairs|Reconocer IDs en parejas nombre/ID', 'True for Telegram; distinct from ordinary-source default.|Activado en Telegram; distinto del defecto de fuentes comunes.', True, 'checkbox'),
                field('telegram_source.history_count', 'Initial history count|Cantidad inicial de historial', 'New source only. Default 0, at most 1000; pause retains cursor.|Solo fuente nueva. Por defecto 0, máximo 1000; pausa conserva cursor.', 0, 'number', min=0, max=1000),
                field('telegram_source.history_since', 'Ignore history before|Ignorar historial anterior a', 'Optional timezone-aware cutoff; no automatic historical backfill.|Fecha opcional con zona; sin recuperación histórica automática.', '', 'datetime-local', advanced=True),
                field('telegram_source.enabled', 'Source enabled|Fuente activada', 'Pause retains progress and imported channels.|Pausar conserva progreso y canales importados.', True, 'checkbox'),
            ],
            'Save Telegram source|Guardar fuente Telegram',
            'Source saved; cursor and imports commit together during ingestion. No snapshot deletion on missing messages.|Fuente guardada; cursor e importaciones se guardan juntos. Mensajes ausentes no borran canales.',
            'telegramService source',
        ),
        command(
            'Preview 10 messages|Ver 10 mensajes',
            'Bounded preview of 1–30 messages, no import?|¿Consulta limitada de 1–30 mensajes sin importar?',
            'Example: 2 extracted, 1 excluded; raw private message text is not part of public diagnostics.|Ejemplo: 2 extraídos, 1 excluido; mensajes privados no van en diagnóstico público.',
        ),
        links(('helper-installed', 'Optional shared recipe editor|Editor de receta compartido')),
    ],
    permission='Telegram admin header; HTTPS/localhost; joined membership',
)
screen(
    'notifications',
    'integrations',
    'Notifications|Notificaciones',
    'Save the webhook separately from sending a test.|Guarda el webhook por separado de enviar una prueba.',
    '/settings?tab=automation',
    'frontend/src/components/NotificationsSection.tsx',
    322,
    [
        form(
            'webhook',
            'Notification destination|Destino de notificación',
            [
                field(
                    'notifications.url',
                    'Webhook URL|URL de webhook',
                    'HTTP(S), valid host/port, no whitespace or fragment. Empty turns notifications off. Treat embedded credentials as private.|HTTP(S), host/puerto válidos, sin espacios ni fragmento. Vacío desactiva. Trata credenciales incrustadas como privadas.',
                    '',
                    'url',
                )
            ],
            'Save webhook|Guardar webhook',
            'Destination saved only; test sending remains explicit.|Solo destino guardado; la prueba sigue siendo explícita.',
            'configService notification-webhook',
        ),
        command(
            'Send a test notification|Enviar notificación de prueba',
            'Send one real message to the saved destination in the implemented app? This prototype sends nothing.|¿Enviar un mensaje real al destino guardado en la app implementada? Este prototipo no envía nada.',
            'Synthetic test acknowledged; show delivery failure separately from a successful settings save.|Prueba ficticia confirmada; separa fallo de entrega de guardado correcto.',
        ),
        links(('telegram-auth', 'Telegram ingestion is separate|Importación Telegram independiente')),
    ],
    states={'masked-invalid': 'Saved URL cannot be safely displayed or validated. Keep it masked; replace explicitly, never submit the mask as a URL.|La URL guardada no se puede mostrar o validar. Mantén máscara; sustituye expresamente, nunca envíes máscara como URL.'},
)
screen(
    'warp',
    'system',
    'WARP',
    'Optional routing; a failed direct lookup does not enable it automatically.|Ruta opcional; un fallo directo no la activa automáticamente.',
    '/warp',
    'frontend/src/pages/WARP.tsx',
    322,
    [
        facts('Synthetic status|Estado ficticio', [('Connection|Conexión', 'Disconnected by choice|Desconectado por elección'), ('Mode|Modo', 'warp'), ('Startup|Inicio', 'Not configured to connect|Sin conexión automática')]),
        form(
            'warp-mode',
            'Mode and license|Modo y licencia',
            [
                field(
                    'warp.mode',
                    'Mode|Modo',
                    'Apply current supported CLI mode; connected status must come from JSON status.|Aplica modo CLI admitido; estado conectado debe venir de JSON.',
                    'warp',
                    'select',
                    options=['warp|Full tunnel|Túnel completo', 'doh|DNS only|Solo DNS', 'warp+doh|WARP + DNS|WARP + DNS', 'proxy|Proxy|Proxy'],
                ),
                field('warp.license_key', 'License key|Clave de licencia', 'Optional license action, minimum 8 characters; never redisplay private value.|Acción opcional, mínimo 8 caracteres; no muestres el valor privado.', '', 'password', minlength=8),
            ],
            'Apply selected setting|Aplicar ajuste elegido',
            'Mode and registration use separate commands; no atomic save across them.|Modo y registro usan órdenes separadas; sin guardado atómico.',
            'warpService mode / license',
            independent=True,
        ),
        command('Connect WARP|Conectar WARP', 'Connect using the selected mode? A successful CLI call alone is not connected status.|¿Conectar con el modo elegido? Éxito CLI no significa conectado.', 'Connection requested; wait for JSON Connected.|Conexión solicitada; espera Connected en JSON.'),
        command('Disconnect WARP|Desconectar WARP', 'Disconnect optional routing? Existing traffic may be interrupted.|¿Desconectar ruta opcional? Puede interrumpir tráfico.', 'Disconnection requested; confirm observed status.|Desconexión solicitada; confirma estado observado.', danger=True),
        links(('warp-exclusions', 'Excluded hosts|Hosts excluidos'), ('warp-startup', 'Saved startup behavior|Inicio guardado')),
    ],
)
screen(
    'warp-exclusions',
    'system',
    'WARP excluded hosts|Hosts excluidos de WARP',
    'Saved desired hosts and the active CLI list can differ.|Los hosts deseados guardados pueden diferir de la lista activa.',
    '/warp',
    'frontend/src/components/WarpExclusionsSection.tsx',
    322,
    [
        form(
            'exclusions',
            'Desired exclusions|Exclusiones deseadas',
            [field('warp.hosts', 'Hosts outside WARP|Hosts fuera de WARP', 'At most 64 validated hosts; one per line. Empty saved list overrides environment defaults.|Máximo 64 hosts válidos; uno por línea. Lista vacía guardada sobrescribe entorno.', 'example.invalid\nmedia.example.invalid', 'textarea')],
            'Save and apply exclusions|Guardar y aplicar exclusiones',
            'Revision-checked save, then application. Preserve unrelated CLI exclusions and pending removals on partial failure.|Guardado con revisión y luego aplicación. Conserva exclusiones CLI ajenas y retiradas pendientes.',
            'warpService exclusions',
        ),
        facts('Saved / applied example|Ejemplo guardado / aplicado', [('Saved|Guardado', '2 hosts'), ('Active|Activo', '1 host'), ('Result|Resultado', 'Partially applied; removal pending|Aplicación parcial; retirada pendiente')]),
    ],
    states={
        'partial': 'Desired hosts saved, but active exclusions differ. Retry apply; do not claim fully applied.|Hosts deseados guardados, pero lista activa distinta. Reintenta aplicar; no afirmes aplicación completa.',
        'conflict': 'A newer exclusion revision exists. Reload desired and active lists before saving.|Existe revisión nueva. Recarga listas deseada y activa antes de guardar.',
    },
)
screen(
    'warp-startup',
    'system',
    'WARP at startup|WARP al iniciar',
    'These runtime values apply after container restart.|Estos valores se aplican tras reiniciar el contenedor.',
    '/warp',
    'frontend/src/components/WarpStartupSection.tsx',
    322,
    [
        form(
            'warp-runtime',
            'Startup settings|Ajustes de inicio',
            [
                field('runtime.ENABLE_WARP', 'Start bundled WARP|Iniciar WARP integrado', 'Requires installed service; saving cannot add missing image capabilities.|Requiere servicio instalado; guardar no añade capacidades de imagen.', False, 'checkbox'),
                field('runtime.WARP_DNS_ONLY', 'DNS only|Solo DNS', 'Default false. Needs NET_ADMIN; no SYS_ADMIN or TUN for DNS-only.|Por defecto false. Requiere NET_ADMIN; no SYS_ADMIN ni TUN para solo DNS.', False, 'checkbox'),
                field('runtime.WARP_ENABLE_NAT', 'Connect before engines start|Conectar antes de iniciar motores', 'Default false. Wait for Connected status; full tunnel needs NET_ADMIN and /dev/net/tun.|Por defecto false. Espera Connected; túnel necesita NET_ADMIN y /dev/net/tun.', False, 'checkbox'),
                field('runtime.WARP_FORCE_IPV4', 'Prefer IPv4 through WARP|Preferir IPv4 por WARP', 'Default true; keep direct-route failures separate from routing changes.|Por defecto true; separa fallos directos de cambios de ruta.', True, 'checkbox'),
            ],
            'Save startup settings|Guardar ajustes de inicio',
            'Saved runtime revision; currently applied boot values remain until restart.|Revisión guardada; valores aplicados no cambian hasta reiniciar.',
            'runtime setup API',
        ),
        facts('Saved / applied example|Ejemplo guardado / aplicado', [('Saved WARP|WARP guardado', 'Enabled|Activado'), ('Applied WARP|WARP aplicado', 'Disabled · restart required|Desactivado · requiere reinicio')]),
        links(('runtime-services', 'Image capabilities and startup|Capacidades de imagen e inicio')),
    ],
)
screen(
    'settings',
    'settings',
    'Settings|Ajustes',
    'Choose one section; each editor says when it saves.|Elige una sección; cada editor indica cuándo guarda.',
    '/settings',
    'frontend/src/pages/Settings.tsx',
    318,
    [
        rows(
            'Settings sections|Secciones',
            [
                ('Playback|Reproducción', 'Engine address and saved route|Dirección de motor y ruta guardada', 'playback-settings'),
                ('Automation|Automatización', 'Independent schedules and cleanup policies|Horarios y políticas independientes', 'automation'),
                ('Stream links|Enlaces', 'Shared formats and PID/AppID|Formatos compartidos y PID/AppID', 'formats'),
                ('Access|Acceso', 'Accounts, public viewing and credentials|Cuentas, acceso público y credenciales', 'access-account'),
                ('Network|Red', 'Runtime, proxies and tuner networks|Ejecución, proxies y redes IPTV', 'network'),
            ],
        ),
        links(('recording-settings', 'Recording settings|Ajustes de grabación'), ('guide-auto', 'Exact guide matching|Coincidencias exactas'), ('notifications', 'Notifications|Notificaciones'), ('preferences', 'Language and appearance|Idioma y apariencia')),
    ],
)
screen(
    'playback-settings',
    'settings',
    'Playback settings|Ajustes de reproducción',
    'Engine-free catalogue use remains valid.|Se puede usar el catálogo sin motor.',
    '/settings?tab=playback',
    'frontend/src/components/player/PlaybackRoutingFields.tsx',
    318,
    [
        form(
            'engine-url',
            'Playback engine|Motor de reproducción',
            [field('engine.url', 'Engine address|Dirección del motor', 'Optional HTTP(S) backend-reachable URL; saved value overrides runtime fallback. Blank is valid.|URL HTTP(S) accesible desde servidor opcional; guardado prevalece. Vacío es válido.', '', 'url')],
            'Save engine address|Guardar dirección',
            'Engine preference saved independently of the routing pair below.|Preferencia guardada por separado de la ruta inferior.',
            'configService ace-engine-url',
        ),
        form(
            'route',
            'Playback routing|Ruta de reproducción',
            [
                field('routing.use_acexy', 'Use Acexy|Usar Acexy', 'Off by default. Shared browser/tuner factories use saved routing; probes stay direct.|Desactivado por defecto. Navegador y sintonizador usan ruta; las comprobaciones siguen directas.', False, 'checkbox'),
                field(
                    'routing.acexy_url',
                    'Acexy origin|Origen Acexy',
                    'Default http://localhost:8080; HTTP(S) origin reachable from backend. One JSON setting with use_acexy.|Por defecto http://localhost:8080; origen HTTP(S) accesible. Un ajuste JSON junto a use_acexy.',
                    'http://localhost:8080',
                    'url',
                    depends='routing.use_acexy',
                ),
            ],
            'Save playback route|Guardar ruta',
            'New sessions use the route. Existing shared sessions keep their route and ownership until teardown.|Sesiones nuevas usan ruta. Las activas conservan ruta y propiedad hasta finalizar.',
            'configService playback-routing',
        ),
        links(('browser-player', 'Browser capabilities|Capacidades del navegador'), ('runtime-playback', 'Runtime limits|Límites de ejecución')),
    ],
)
screen(
    'automation',
    'settings',
    'Background updates|Actualizaciones en segundo plano',
    'Intervals, checking-engine choice and clock anchors save independently.|Intervalos, motor de comprobación y horas se guardan independientemente.',
    '/settings?tab=automation',
    'frontend/src/pages/Settings.tsx',
    318,
    [
        form(
            'intervals',
            'Repeat intervals|Intervalos',
            [
                field('schedule.rescrape_interval', 'Scrape sources every (hours)|Actualizar fuentes cada (horas)', 'Current default 24; use current endpoint whole-hour validation. Saved separately.|Por defecto 24; valida horas enteras según API. Guardado separado.', 24, 'number', min=1),
                field('schedule.epg_refresh_interval', 'Refresh guide every (hours)|Actualizar guía cada (horas)', 'Current default 6; saved separately from sources.|Por defecto 6; se guarda por separado de fuentes.', 6, 'number', min=1),
                field('schedule.channel_status_interval', 'Check signal every (minutes)|Comprobar señal cada (minutos)', 'Default 60; 1–10080 minutes.|Por defecto 60; 1–10080 minutos.', 60, 'number', min=1, max=10080),
            ],
            'Save interval|Guardar intervalo',
            'Each interval updates its own endpoint immediately; report partial outcomes honestly.|Cada intervalo actualiza su API; informa resultados parciales.',
            'configService individual interval endpoints',
            independent=True,
        ),
        form(
            'checker',
            'Checking engine|Motor de comprobación',
            [
                field('checker.use_dedicated', 'Use a dedicated checking engine|Usar motor dedicado', 'Off uses saved playback URL; neither URL means skipped checks, preserving observations.|Desactivado usa motor de reproducción; sin ambos se omite y conserva resultados.', False, 'checkbox'),
                field(
                    'checker.url',
                    'Checking engine URL|URL del comprobador',
                    'Required when enabled. Bundled checker is supervisor-owned and read-only; configured failure never falls back.|Obligatorio al activar. Integrado es solo lectura; si falla, no recurre al otro motor.',
                    '',
                    'url',
                    depends='checker.use_dedicated',
                ),
            ],
            'Save checking engine|Guardar comprobador',
            'Checker selection saved. Existing sample timestamps remain on skips and errors.|Comprobador guardado. Se conservan fechas de muestras en omisiones y errores.',
            'configService check-engine',
        ),
        form(
            'scope',
            'Streams to check|Emisiones que comprobar',
            [
                field(
                    'checks.scope',
                    'Check scope|Ámbito',
                    'Applies to scheduled and run-now scans; individual checks remain available. Current source saves selection immediately.|Se aplica a tareas y ejecución manual; sigue la comprobación individual. El código actual guarda al seleccionar.',
                    'all',
                    'select',
                    options=['all|All active streams|Todas las activas', 'assigned|Assigned to active TV channels|Vinculadas a canales activos', 'favorites|Assigned to favorite active TV channels|Vinculadas a favoritos activos'],
                )
            ],
            'Apply scope|Aplicar ámbito',
            'Scope saved independently; this button is a proposed explicit-save treatment.|Ámbito guardado por separado; el botón es una propuesta de guardado explícito.',
            'configService stream-check-scope',
        ),
        links(('schedule-anchors', 'Clock start times|Horas de inicio'), ('offline-cleanup', 'Offline stream cleanup|Limpieza de emisiones sin señal'), ('recording-settings', 'Recordings|Grabaciones'), ('guide-auto', 'Exact guide matching|Vinculación exacta'), ('notifications', 'Notifications|Notificaciones')),
    ],
)
screen(
    'schedule-anchors',
    'settings',
    'Schedule start times|Horas de inicio',
    'Jobs can wait in the FIFO queue after becoming due.|Las tareas vencidas pueden esperar en la cola FIFO.',
    '/settings?tab=automation',
    'frontend/src/components/ScheduleAnchorFields.tsx',
    318,
    [
        form(
            'anchors',
            'Clock anchors|Horas de referencia',
            [
                field(
                    'anchors.timezone',
                    'Schedule timezone|Zona horaria',
                    'IANA, default UTC. Divisible intervals retain local clock times; other intervals use elapsed time and may shift with DST.|IANA, por defecto UTC. Intervalos divisibles conservan hora local; otros usan tiempo transcurrido y pueden desplazarse.',
                    'UTC',
                    required=True,
                ),
                *[
                    field(
                        'anchors.' + key,
                        label,
                        'Optional HH:MM. Blank counts from startup; next run comes from the server. DST gap advances to valid time; repeated clock anchor runs once.|HH:MM opcional. Vacío cuenta desde inicio; servidor indica próxima ejecución. Salto DST avanza a hora válida; hora repetida ejecuta una vez.',
                        '',
                        'time',
                    )
                    for key, label in [('url_scraping', 'Source refresh start|Inicio de fuentes'), ('epg_refresh', 'Guide refresh start|Inicio de guía'), ('channel_status', 'Signal check start|Inicio de comprobaciones'), ('offline_stream_cleanup', 'Offline cleanup start|Inicio de limpieza')]
                ],
            ],
            'Save start times|Guardar horas',
            'All anchors and timezone save in one schedule transaction. Cleanup thresholds and intervals are separate saves.|Horas y zona se guardan en una transacción. Umbrales e intervalos se guardan aparte.',
            'configService schedule-anchors',
        ),
        facts('Next run example|Ejemplo de próxima ejecución', [('Due|Vence', '8 Nov · 02:30 UTC'), ('Actual launch|Inicio real', 'May wait for an earlier queued job|Puede esperar a una tarea previa')]),
    ],
)
screen(
    'offline-cleanup',
    'settings',
    'Offline stream cleanup|Limpieza de emisiones sin señal',
    'Optional deletion needs repeated, recent offline evidence.|La eliminación opcional requiere pruebas repetidas y recientes.',
    '/settings?tab=automation',
    'frontend/src/components/settings/OfflineCleanupFields.tsx',
    318,
    [
        form(
            'offline',
            'Cleanup policy|Política de limpieza',
            [
                field('offline.enabled', 'Remove long-offline streams automatically|Eliminar emisiones sin señal prolongada', 'Off by default. Hiding in Live TV is independent.|Desactivado por defecto. Ocultar en TV es independiente.', False, 'checkbox'),
                field('offline.offline_days', 'Offline for at least (days)|Sin señal al menos (días)', 'Default 14; 1–365. Errors and unknown do not count as offline evidence.|Por defecto 14; 1–365. Errores y desconocido no cuentan como prueba.', 14, 'number', min=1, max=365),
                field('offline.interval_days', 'Run every (days)|Ejecutar cada (días)', 'Default 7; 1–90. Viewing/recording defers work until the next scheduled run.|Por defecto 7; 1–90. Ver/grabar aplaza hasta siguiente ejecución.', 7, 'number', min=1, max=90),
                field('offline.remove_linked', 'Also remove TV-linked streams|Eliminar también emisiones vinculadas', 'Default false. TV channels/guides remain, but links and preference positions are lost.|Por defecto false. Conserva canales/guías, pero se pierden vínculos y preferencias.', False, 'checkbox'),
                field(
                    'offline.rescrape',
                    'Update affected sources afterwards|Actualizar fuentes afectadas después',
                    'Default true. Rediscovered streams return unchecked; update failure is separate from cleanup success.|Por defecto true. Redescubiertas vuelven sin comprobar; fallo al actualizar es independiente.',
                    True,
                    'checkbox',
                ),
            ],
            'Save cleanup policy|Guardar política',
            'Policy saved only. Saving the start time is a separate schedule transaction.|Solo política guardada. Hora de inicio es otra transacción.',
            'configService offline-cleanup',
            confirm=pair('Enable or change future deletion? Only eligible recoverable source streams qualify; recent playback and active recording protect them.|¿Activar o cambiar eliminación futura? Solo emisiones de fuentes recuperables; reproducción reciente y grabaciones las protegen.'),
        ),
        command(
            'Preview eligible streams|Ver emisiones elegibles',
            'Read a bounded preview without deleting anything?|¿Consultar vista limitada sin eliminar nada?',
            'Up to 500 streams qualify in this batch. The job rechecks at execution; zero may mean insufficient recent evidence.|Hasta 500 emisiones aptas en este lote. Se revalida al ejecutar; cero puede significar pruebas insuficientes.',
        ),
        links(('schedule-anchors', 'Save cleanup start time separately|Guardar hora por separado'), ('jobs', 'Cleanup history|Historial de limpieza')),
    ],
    states={
        'deferred': 'Cleanup deferred while watching or recording. It will be reconsidered at its next scheduled run; no immediate retry is promised.|Limpieza aplazada por reproducción/grabación. Se reconsidera en su próxima ejecución; no se promete reintento inmediato.',
        'refresh-failed': 'Eligible streams removed, but affected-source refresh failed. Report both outcomes; do not label all cleanup failed.|Se eliminaron elegibles, pero falló actualizar fuentes. Informa ambos; no marques toda la limpieza fallida.',
    },
)
screen(
    'network',
    'settings',
    'Network settings|Ajustes de red',
    'Keep proxy trust, IPTV networks and account transport separate.|Separa confianza de proxy, redes IPTV y transporte de cuentas.',
    '/settings?tab=network',
    'frontend/src/components/settings/NetworkSettingsFields.tsx',
    318,
    [
        facts(
            'Current policy example|Ejemplo de política',
            [
                ('Accounts|Cuentas', 'Private HTTP supported|HTTP privado admitido'),
                ('Proxy trust|Confianza de proxy', 'auto · Docker bridge peers, excluding gateways|auto · pares de puente Docker, salvo pasarelas'),
                ('Player address|Dirección para reproductores', 'Saved override takes precedence|Prevalece dirección guardada'),
            ],
        ),
        links(
            ('runtime-network', 'Edit shared runtime network fields|Editar campos de red compartidos'), ('access-policy', 'Viewing and IPTV policy|Política de acceso e IPTV'), ('public-address', 'Edit effective player address|Editar dirección efectiva'), ('casting-settings', 'Cast home networks|Redes domésticas Cast')
        ),
    ],
)
screen(
    'system',
    'system',
    'System status|Estado del sistema',
    'Show what needs attention and what is still working.|Muestra qué requiere atención y qué sigue funcionando.',
    '/system',
    'frontend/src/pages/SystemDashboard.tsx',
    322,
    [
        note('Dedicated checker unavailable. Playback remains independent; previous signal observations are preserved.|Comprobador dedicado no disponible. Reproducción independiente; se conservan observaciones.', 'warning'),
        rows(
            'Operations|Operaciones',
            [
                ('Services|Servicios', 'Playback ready · checker unavailable · WARP off by choice|Reproducción lista · comprobador no disponible · WARP desactivado', 'services'),
                ('Maintenance queue|Cola de mantenimiento', 'Guide running · sources waiting|Guía en curso · fuentes esperando', 'jobs'),
                ('Storage|Almacenamiento', 'Partial scan · filesystem free space known|Exploración parcial · espacio libre conocido', 'storage'),
                ('Diagnostics|Diagnóstico', 'Bounded masked logs; no private raw captures|Registros limitados y ocultados; sin capturas privadas', 'diagnostics'),
            ],
        ),
        links(('warp', 'WARP'), ('startup', 'Startup status|Estado de inicio')),
    ],
)
screen(
    'services',
    'system',
    'Service controls|Controles de servicios',
    'Installed, enabled and running are separate facts.|Instalado, activado y en ejecución son hechos distintos.',
    '/system',
    'frontend/src/components/ServicesPanel.tsx',
    322,
    [
        facts('Bundled playback engine|Motor integrado', [('Installed|Instalado', 'Yes|Sí'), ('Enabled for startup|Activado al iniciar', 'Yes|Sí'), ('Running|En ejecución', 'Intentionally stopped|Detenido expresamente')]),
        command(
            'Start playback engine|Iniciar motor',
            'Resume the supervised engine? It retries exits indefinitely until you Stop or the container stops.|¿Reanudar motor supervisado? Reintenta salidas indefinidamente hasta Detener o apagar contenedor.',
            'Start queued to supervisor; observed health confirms running later.|Inicio en cola del supervisor; el estado observado confirmará ejecución.',
        ),
        command(
            'Stop playback engine|Detener motor',
            'Stop playback engine and pause its recovery until Start/Restart or container restart? Active use may be interrupted.|¿Detener motor y recuperación hasta Iniciar/Reiniciar o reinicio del contenedor? Puede interrumpir uso.',
            'Intentional stop requested. Whole-container health respects this stop.|Detención expresa solicitada. Salud del contenedor la respeta.',
            danger=True,
        ),
        command('Restart checking engine|Reiniciar comprobador', 'Restart only the configured bundled checker? Its failure never falls back to playback.|¿Reiniciar solo comprobador integrado? Su fallo no recurre a reproducción.', 'Checker restart requested independently.|Reinicio del comprobador solicitado aparte.'),
        rows(
            'Other sidecars|Otros servicios',
            [('Acexy / IPFS / ZeroNet / Tor', 'Show installed capability and supported restart only; keep their existing fast-exit budget.|Muestra capacidad y reinicio admitido; conserva límite de salidas rápidas.', 'runtime-services'), ('WARP', 'Routing controls remain on WARP|Controles permanecen en WARP', 'warp')],
        ),
    ],
    states={'external': 'This engine is external. Bundled supervisor controls are unavailable; show its configured address without pretending Start controls it.|Motor externo. Sin controles del supervisor; muestra dirección sin fingir que Iniciar lo controla.'},
)
screen(
    'jobs',
    'system',
    'Scheduled job history|Historial de tareas',
    'Waiting is not running; errors are not offline streams.|Esperar no es ejecutar; errores no son emisiones sin señal.',
    '/system',
    'frontend/src/components/overview/ScheduledJobs.tsx',
    322,
    [
        rows(
            'Current FIFO queue|Cola FIFO actual',
            [
                ('Guide refresh|Actualizar guía', 'Running since 16:00 · previous result separate|En curso desde 16:00 · resultado anterior separado', 'job-detail'),
                ('Source refresh|Actualizar fuentes', 'Waiting · already queued; run-now disabled|En espera · ya en cola; ejecutar desactivado', 'job-detail'),
                ('Signal checks|Comprobar señal', 'Waiting for app-owned playback; bounded pause budget|Esperando reproducción propia; pausa limitada', 'job-detail'),
            ],
        ),
        rows(
            'Persisted history · synthetic|Historial persistido · ficticio',
            [
                ('Signal checks · 15:00|Comprobaciones · 15:00', 'Online 8 · offline 2 · skipped 4 · errors 1|Con señal 8 · sin señal 2 · omitidas 4 · errores 1', 'job-detail'),
                ('Offline cleanup · yesterday|Limpieza · ayer', 'Deferred while recording|Aplazada por grabación', 'job-detail'),
                ('Source refresh · yesterday|Fuentes · ayer', 'Interrupted after restart; not still running|Interrumpida tras reinicio; no sigue en curso', 'job-detail'),
            ],
        ),
        links(('automation', 'Schedule settings|Ajustes de tareas')),
    ],
)
screen(
    'job-detail',
    'system',
    'Job run details|Detalles de ejecución',
    'Retain launch time, outcome and the reason for partial work.|Conserva inicio, resultado y motivo de trabajo parcial.',
    '/system',
    'frontend/src/components/overview/ScheduledJobs.tsx',
    322,
    [
        facts(
            'Signal check · synthetic|Comprobación · ficticia',
            [
                ('Launched|Iniciada', '7 Nov 15:00 UTC'),
                ('Finished|Finalizada', '7 Nov 15:11 UTC'),
                ('Result|Resultado', 'Partial · playback pause budget exhausted|Parcial · agotada pausa por reproducción'),
                ('Counts|Cantidades', '8 online · 2 offline · 4 skipped · 1 error|8 con señal · 2 sin señal · 4 omitidas · 1 error'),
                ('Stop reason|Motivo de fin', 'Deferred remaining work; FIFO released|Trabajo restante aplazado; cola liberada'),
                ('Scalar result|Resultado escalar', '3 · valid result, not a malformed object|3 · resultado válido, no objeto erróneo'),
            ],
        ),
        note('Recording capture has its own coordinator; it is not blocked behind this maintenance FIFO. Run-now requests deduplicate running and waiting work.|La captura tiene coordinador propio; no espera a esta cola. Ejecutar ahora no duplica tareas en curso o en espera.'),
        links(('diagnostics', 'Diagnostics for failures|Diagnóstico de fallos')),
    ],
)
screen(
    'storage',
    'system',
    'Storage details|Detalles de almacenamiento',
    'Free space is counted once per filesystem.|El espacio libre se cuenta una vez por sistema de archivos.',
    '/system',
    'frontend/src/components/overview/StoragePanel.tsx',
    322,
    [
        facts('Filesystem A · synthetic|Sistema A · ficticio', [('Free|Libre', '18.4 GiB'), ('Coverage|Cobertura', 'Cached at 16:00 · partial scan|Caché 16:00 · exploración parcial')]),
        rows(
            'Container destinations only|Solo destinos del contenedor',
            [
                ('/recordings', '6.2 GiB observed · more files may exist|6,2 GiB observados · puede haber más', 'recording-storage'),
                ('/config', 'Unknown · scan budget reached|Desconocido · límite de exploración', None),
                ('/logs', '0.08 GiB · bounded rotating logs|0,08 GiB · registros rotativos limitados', 'diagnostics'),
            ],
        ),
        note(
            'Never expose host mount sources. Scans are bounded, cached, isolated and symlink-safe. Unknown sizes are not zero; destination totals may share a filesystem.|Nunca muestres rutas de origen del host. Exploración limitada, en caché y segura ante enlaces. Desconocido no es cero; destinos pueden compartir sistema.'
        ),
        command(
            'Refresh storage report|Actualizar informe', 'Request a bounded cached scan? It may remain partial.|¿Solicitar exploración limitada? Puede seguir parcial.', 'Report refreshed in fixture; preserve timestamp and partial coverage labels.|Informe ficticio actualizado; conserva fecha y etiquetas parciales.'
        ),
    ],
)
screen(
    'diagnostics',
    'system',
    'Logs and diagnostics|Registros y diagnóstico',
    'Download bounded masked tails; raw log language stays original.|Descarga fragmentos limitados con datos ocultos; conserva idioma de registros.',
    '/system',
    'frontend/src/components/DiagnosticsDownload.tsx',
    322,
    [
        facts(
            'Diagnostic scope|Ámbito',
            [
                ('Files|Archivos', 'Fixed scraper / service / entrypoint tails|Fragmentos fijos de scraper / servicios / entrada'),
                ('Credentials|Credenciales', 'Masked by export; still review before sharing|Ocultadas al exportar; revisa antes de compartir'),
                ('Availability|Disponibilidad', 'DB-independent, normal API-token checks still apply|Independiente de BD; conserva validación de token'),
            ],
        ),
        code('Synthetic log excerpt · not a live log|Ejemplo de registro ficticio', 'DEMO 16:00 checker unavailable\nDEMO 16:01 guide refresh waiting\nDEMO 16:02 source refresh interrupted'),
        command(
            'Prepare diagnostics download|Preparar descarga de diagnóstico',
            'Export only bounded fixed-file tails? No environment dump or arbitrary path selection.|¿Exportar solo fragmentos de archivos fijos? Sin volcado de entorno ni rutas arbitrarias.',
            'Synthetic export prepared; no private files accessed.|Exportación ficticia preparada; sin acceder a archivos privados.',
        ),
    ],
    states={
        'denied': 'Enter the required administrative API token or sign in as permitted. Diagnostic availability during startup failure does not bypass auth.|Introduce token administrativo o sesión permitida. Diagnóstico durante fallo no omite autenticación.',
        'partial': 'One fixed log is unavailable. Export the available tails and report the omitted file, not an empty successful log.|Un registro fijo no está disponible. Exporta fragmentos disponibles e informa del omitido.',
    },
)
screen(
    'setup',
    'setup',
    'Start with channels|Empieza por los canales',
    'Add a source and an optional guide. Engines are optional.|Añade una fuente y guía opcional. Los motores son opcionales.',
    '/setup',
    'frontend/src/pages/Setup.tsx',
    318,
    [
        dict(type='steps', items=[pair('1 · Channels|1 · Canales'), pair('2 · Optional guide|2 · Guía opcional'), pair('3 · Finish|3 · Terminar')]),
        rows(
            'Saved during setup · synthetic|Guardado durante configuración · ficticio',
            [('Family channels', 'Saved already · import waiting|Ya guardada · importación esperando', 'source-results'), ('Programme guide|Guía de programación', 'Optional · shared EPG dobleM preset is an explicit choice|Opcional · EPG dobleM es elección expresa', 'guide-source')],
        ),
        links(('source-auto', 'Add another source|Añadir otra fuente'), ('guide-match', 'Review guide matches|Revisar coincidencias'), ('runtime-playback', 'Advanced connection settings|Conexiones avanzadas')),
        command(
            'Finish setup|Terminar configuración',
            'Mark onboarding complete? Sources and guides were saved as added; Finish does not atomically save them again.|¿Marcar configuración completa? Fuentes y guías ya se guardaron; Terminar no vuelve a guardarlas atómicamente.',
            'Setup completed. Open Live TV or return to sources while import waits.|Configuración terminada. Abre TV o vuelve a fuentes mientras importa.',
            next='dashboard',
        ),
        links(('dashboard', 'Postpone setup|Posponer configuración')),
    ],
    states={'partial': 'Source saved, guide failed. Keep the source and offer retry of the guide or Finish without guide.|Fuente guardada, guía fallida. Conserva fuente y permite reintentar guía o terminar sin ella.'},
)
screen(
    'startup',
    'setup',
    'Starting AceStream Scraper|Iniciando AceStream Scraper',
    'Keep the interface available while startup works in the background.|Mantén la interfaz disponible durante el inicio en segundo plano.',
    'outer startup gate',
    'frontend/src/components/StartupGate.tsx',
    318,
    [
        facts(
            'Startup progress · synthetic|Progreso ficticio',
            [
                ('Database|Base de datos', 'Schema upgrade in progress|Actualizando esquema'),
                ('Normal API|API normal', 'Temporarily unavailable|No disponible temporalmente'),
                ('Large guide import|Importación de guía grande', 'Resumable background work; no invented completion time|Trabajo reanudable; sin tiempo inventado'),
            ],
        ),
        note('Loading is not an empty catalogue. Loss of connection is not proof of database damage.|Cargar no significa catálogo vacío. Perder conexión no prueba daño en base de datos.'),
        links(('diagnostics', 'Download authenticated diagnostics|Descargar diagnóstico autenticado'), ('recovery', 'Startup failure options|Opciones ante fallo de inicio')),
    ],
    permission='normal startup / API-token policy',
    states={
        'deferred': 'Application ready; legacy guide programmes are still importing in resumable batches. Other work remains available.|App lista; programas antiguos se importan por lotes reanudables. Sigue disponible el resto.',
        'connection': 'Connection lost. Retry status before offering catalogue replacement.|Conexión perdida. Reintenta estado antes de ofrecer reemplazar catálogo.',
        'token': 'Enter the configured API token to read protected startup information. Recovery never bypasses authentication.|Introduce token configurado para leer estado protegido. Recuperación nunca omite autenticación.',
    },
)
screen(
    'recovery',
    'setup',
    'Startup needs attention|El inicio necesita atención',
    'Start with diagnostics and retry before replacing any catalogue data.|Empieza por diagnóstico y reintento antes de sustituir datos.',
    'startup failure gate',
    'frontend/src/components/StartupGate.tsx',
    318,
    [
        note('Synthetic database-startup failure. The independent accounts store remains protected and outside catalogue recovery.|Fallo ficticio de inicio de BD. Las cuentas independientes permanecen protegidas y fuera de la recuperación.', 'warning'),
        links(('diagnostics', 'Read diagnostic scope|Ver ámbito de diagnóstico')),
        command('Retry startup|Reintentar inicio', 'Retry the failed startup without catalogue replacement?|¿Reintentar inicio sin sustituir catálogo?', 'Startup retry requested; watch actual progress.|Reintento solicitado; observa progreso real.'),
        rows(
            'Recovery choices|Opciones de recuperación',
            [
                ('Recover readable catalogue|Recuperar catálogo legible', 'Back up first; damaged rows can be skipped|Copia primero; se pueden omitir filas dañadas', 'recovery-readable'),
                ('Start a fresh catalogue|Empezar catálogo nuevo', 'Back up and replace catalogue configuration|Copia y sustituye configuración del catálogo', 'recovery-fresh'),
            ],
        ),
    ],
    states={
        'busy': 'Another recovery owns the database lock. Wait for its result; do not start a competing operation.|Otra recuperación tiene el bloqueo. Espera su resultado; no inicies otra operación.',
        'interrupted': 'Interrupted recovery marker found. Show its safe resume/retry instructions; never treat this as a fresh empty install.|Marca de recuperación interrumpida. Muestra instrucciones seguras; no lo trates como instalación vacía.',
    },
)
for id, title, effect in [
    (
        'recovery-readable',
        'Recover readable catalogue|Recuperar catálogo legible',
        'Back up database and migration files first. Copy readable source/configuration rows in supported order; damaged rows may be skipped. Listings and activity are not copied. Accounts are independent.|Copia primero BD y archivos de migración. Copia fuentes/configuración legibles en orden; pueden omitirse filas dañadas. No se copian programación ni actividad. Cuentas independientes.',
    ),
    (
        'recovery-fresh',
        'Start a fresh catalogue|Empezar catálogo nuevo',
        'Back up database and migration files first, then replace catalogue data and reconfigure catalogue settings. Accounts and their fail-closed marker remain separate; this is not a password reset.|Copia primero BD y migración; después sustituye catálogo y reconfigura ajustes. Cuentas y marca de protección son independientes; no restablece contraseñas.',
    ),
]:
    screen(
        id,
        'setup',
        title,
        'Review what is retained and what must be rebuilt.|Revisa qué se conserva y qué se reconstruye.',
        'startup recovery',
        'frontend/src/components/StartupGate.tsx',
        318,
        [
            note(effect, 'warning'),
            form(
                id,
                'Confirmation|Confirmación',
                [
                    field(
                        'recovery.confirm',
                        'I understand this recovery action|Entiendo esta recuperación',
                        'Required; current recovery token is revalidated on submission. No automatic destructive retries.|Obligatorio; se revalida token actual al enviar. Sin reintentos destructivos automáticos.',
                        False,
                        'checkbox',
                        required=True,
                    )
                ],
                title,
                effect,
                'startupService recovery',
                intent=True,
                danger=True,
                confirm=pair(effect),
                next='recovery-result',
            ),
            links(('recovery', 'Go back without changes|Volver sin cambios')),
        ],
    )
screen(
    'recovery-result',
    'setup',
    'Recovery result|Resultado de recuperación',
    'Report backup, copied rows and omissions separately.|Informa por separado de copia, filas y omisiones.',
    'startup recovery',
    'frontend/src/components/StartupGate.tsx',
    318,
    [
        facts(
            'Synthetic readable recovery|Recuperación legible ficticia',
            [
                ('Backup|Copia', 'Created before changes|Creada antes de cambios'),
                ('Recovered|Recuperado', '2 sources · 3 TV channels · 6 streams|2 fuentes · 3 canales · 6 emisiones'),
                ('Skipped|Omitido', '1 damaged row · listings/activity not copied|1 fila dañada · sin programación/actividad'),
                ('Accounts|Cuentas', 'Retained independently|Conservadas por separado'),
            ],
        ),
        links(('startup', 'Follow startup progress|Seguir inicio'), ('setup', 'Review catalogue setup|Revisar configuración'), ('diagnostics', 'Download recovery diagnostics|Descargar diagnóstico')),
    ],
    states={'failed': 'Recovery did not finish. Preserve backup and marker; no success or fresh-start claim. Follow the returned safe retry path.|Recuperación incompleta. Conserva copia y marca; no afirmes éxito. Sigue el reintento seguro indicado.'},
)
screen(
    'preferences',
    'shell',
    'Language and appearance|Idioma y apariencia',
    'Changes apply in this browser without restarting playback or losing a draft.|Se aplica en este navegador sin reiniciar reproducción ni perder borrador.',
    'shared shell preferences',
    'frontend/src/components/layout/AppShell.tsx',
    317,
    [
        form(
            'preferences',
            'Browser preferences|Preferencias de navegador',
            [
                field(
                    'preference.language',
                    'Interface language|Idioma de interfaz',
                    'English / Español / system. Names, logs, URLs and IDs remain original.|English / Español / sistema. Nombres, registros, URLs e IDs se conservan.',
                    'system',
                    'select',
                    options=['system|System default|Sistema', 'en|English|English', 'es|Español|Español'],
                ),
                field('preference.theme', 'Appearance|Apariencia', 'System, light or dark; reduced motion follows the device preference.|Sistema, claro u oscuro; movimiento reducido según dispositivo.', 'system', 'select', options=['system|System default|Sistema', 'light|Light|Claro', 'dark|Dark|Oscuro']),
            ],
            'Use preferences|Usar preferencias',
            'Applied now in this tab. Persistence failure must not roll back the visible choice or lose a form.|Aplicado en esta pestaña. Fallo al guardar no revierte elección ni pierde formulario.',
            'proposed browser preference resource',
            local=True,
        ),
        note('All palette/font directions in review controls remain proposals. Existing application IBM Plex/teal standards remain authoritative.|Todas las direcciones de color/tipo siguen propuestas. Los estándares IBM Plex/teal actuales siguen vigentes.'),
    ],
    states={'storage-failed': 'Preference changed for this tab, but could not be saved for next time. Continue using the app; offer Retry storage.|Preferencia cambiada en esta pestaña, pero no se guardó para la próxima vez. Continúa; ofrece reintentar.'},
)
screen(
    'notices',
    'shell',
    'Notices and session feedback|Avisos y mensajes',
    'Notices have their own scope and consequence.|Los avisos tienen ámbito y consecuencia propios.',
    'shared shell',
    'frontend/src/components/ApiTokenNotice.tsx',
    318,
    [
        form(
            'api-token',
            'Legacy API access|Acceso API anterior',
            [field('legacy.token', 'API token|Token API', 'Existing deployment header token; stored through current token policy. Never insert into administrative URLs.|Token de cabecera existente; usa política actual. Nunca en URLs administrativas.', '', 'password')],
            'Use API token|Usar token',
            'Token used for subsequent authenticated requests. Invalid token keeps management blocked.|Token usado en siguientes solicitudes. Si no es válido, administración bloqueada.',
            'apiToken browser credential',
            intent=True,
        ),
        rows(
            'Independent notices|Avisos independientes',
            [
                ('Setup incomplete|Configuración incompleta', 'Continue or postpone; sources already saved remain|Continúa o pospón; se conservan fuentes', 'setup'),
                ('New stable version available|Nueva versión estable', 'Manual update instructions; no auto-install. Failed checks stay quiet.|Instrucciones manuales; sin instalación automática. Fallos de consulta silenciosos.', 'changelog'),
                ('What changed|Qué cambió', 'Per-browser read/dismiss; development notes are not proof of stable release.|Leído/oculto por navegador; notas no prueban publicación estable.', 'changelog'),
            ],
        ),
        command('Dismiss update notice|Ocultar aviso', 'Dismiss this version notice in this browser?|¿Ocultar este aviso de versión en este navegador?', 'Dismissed locally; changelog remains available.|Oculto localmente; historial sigue disponible.'),
    ],
)
screen(
    'not-found',
    'shell',
    'This page is not available|Esta página no está disponible',
    'Keep useful route context and offer a safe way back.|Conserva contexto útil y ofrece vuelta segura.',
    '*',
    'frontend/src/pages/NotFound.tsx',
    318,
    [
        note('Unknown route /sample-missing. Do not echo private query values. Existing aliases still redirect with query context.|Ruta desconocida /sample-missing. No muestres consultas privadas. Los alias existentes conservan contexto.'),
        links(('dashboard', 'Go to dashboard|Ir al inicio'), ('channels', 'TV channels|Canales de TV'), ('settings', 'Settings|Ajustes')),
        facts('Compatibility examples|Ejemplos de compatibilidad', [('/channels/:id', '/tv-channels'), ('/epg/mappings', '/epg?tab=rules'), ('/catalogues', '/scraper?tab=w3u'), ('/health', '/system')]),
    ],
    permission='route-aware access gate',
)
screen(
    'changelog',
    'shell',
    'What changed|Qué cambió',
    'Read bundled history without needing a network connection.|Lee el historial incluido sin conexión.',
    '/changelog',
    'frontend/src/pages/Changelog.tsx',
    322,
    [
        rows(
            'Version history · synthetic text|Historial · texto ficticio',
            [
                ('v2.2.0 · development notes|v2.2.0 · notas de desarrollo', 'Illustrative release text, not a publication claim. Historical Markdown keeps its original language.|Texto ilustrativo, no afirma publicación. Markdown histórico conserva idioma.', None),
                ('Earlier versions|Versiones anteriores', 'Navigation chrome is translated; source notes are identified by original language.|Navegación traducida; notas identificadas por idioma original.', None),
            ],
        ),
        links(('dashboard', 'Back to dashboard|Volver al inicio')),
    ],
)
screen(
    'unsaved',
    'shell',
    'Leave with unsaved changes?|¿Salir sin guardar?',
    'A consequential guard, not a save across unrelated settings.|Una protección al salir, no guardado de ajustes independientes.',
    'shared dirty guard',
    'frontend/src/components/ConfirmDialog.tsx',
    318,
    [
        form(
            'unsaved-example',
            'Example source draft|Borrador de fuente',
            [field('draft.source_name', 'Source name|Nombre de fuente', 'Change this, then follow another workflow link to test Stay / Discard.|Cámbialo y sigue otro enlace para probar Quedarse / Descartar.', 'Family channels')],
            'Save source draft|Guardar borrador',
            'Only this source draft saved.|Solo se guardó este borrador.',
            'proposed form dirty guard',
        ),
        links(('dashboard', 'Navigate to dashboard|Ir al inicio')),
        note('Locale/theme changes retain dirty values, row selection, current route, focus and scroll. Page unload uses native browser protection; no crash-recovery promise.|Idioma/tema conservan valores, selección, ruta, foco y posición. Al cerrar usa protección del navegador; sin prometer recuperación tras fallo.'),
    ],
)


# Shared runtime editor, reused by setup / Network / contextual service links.
def source_text(path):
    return subprocess.check_output(['git', 'show', REV + ':' + path], cwd=ROOT, text=True)


runtime = json.loads(source_text('backend/app/config/runtime-options.json'))
runtime_labels = {}
for line in (ROOT / 'runtime-field-inventory.md').read_text().splitlines():
    if line.startswith('| ') and ' / ' in line:
        parts = [v.strip() for v in line.split('|')[1:-1]]
        if len(parts) > 2:
            runtime_labels[parts[0]] = parts[2].split(' / ', 1)[-1]
RUNTIME_HELP = {
    'ACE_ENGINE_URL': 'Fallback engine address; saved Playback wins. Blank permits engine-free use.|Dirección alternativa de motor; prevalece Reproducción guardada. Vacío permite uso sin motor.',
    'ACE_CHECK_ENGINE_URL': 'External checking fallback; bundled checker is managed and unavailable never means fallback to playback.|Alternativa de comprobador externo; integrado es gestionado y su fallo no permite usar reproducción.',
    'PLAYER_MAX_SESSIONS': 'Maximum simultaneous browser sessions, not number of viewers; matching viewers can share.|Máximo de sesiones simultáneas, no de espectadores; compatibles pueden compartir.',
    'PLAYER_START_TIMEOUT_SECONDS': 'Total browser startup budget in seconds, including waiting for source ownership.|Tiempo total de inicio del navegador en segundos, incluida espera de propiedad.',
    'PUBLIC_BASE_URL': 'Runtime fallback only. Saved Integrations address wins; preserve proxy prefix.|Solo alternativa de ejecución. Prevalece Integraciones; conserva prefijo de proxy.',
    'ALLOW_PRIVATE_SCRAPE_TARGETS': 'Allows private source fetches; metadata addresses remain blocked.|Permite consultas a fuentes privadas; direcciones de metadatos bloqueadas.',
    'TUNER_ALLOWED_NETWORKS': 'Client CIDRs for tuner routes; separate from API tokens. Asterisk opens all networks.|CIDR de clientes de sintonizador; separado de tokens. Asterisco abre todas las redes.',
    'FORWARDED_ALLOW_IPS': 'auto trusts loopback and Docker bridge peers, not gateways. Preserve explicit overrides; do not trust the entire LAN.|auto confía en loopback y pares Docker, no pasarelas. Conserva valores explícitos; no confíes en toda la LAN.',
    'CORS_ORIGINS': 'Comma-separated origins or JSON array for separately hosted browsers; usually unchanged.|Orígenes por comas o array JSON para navegador alojado aparte; normalmente sin cambios.',
    'ACESTREAM_BIND_ALL': 'Engine API is unauthenticated. Publish its port only to trusted clients.|API del motor sin autenticación. Publica puerto solo a clientes de confianza.',
    'WARP_DNS_ONLY': 'Encrypt DNS only; video uses the normal route. NET_ADMIN required, not SYS_ADMIN/TUN.|Cifra solo DNS; vídeo usa ruta normal. Requiere NET_ADMIN, no SYS_ADMIN/TUN.',
    'WARP_ENABLE_NAT': 'Wait for Connected before engines. Full tunnel needs NET_ADMIN and /dev/net/tun.|Espera Connected antes de motores. Túnel requiere NET_ADMIN y /dev/net/tun.',
    'WARP_FORCE_IPV4': 'Prefer IPv4 for WARP routing; does not authorize automatic connection on DNS failure.|Prefiere IPv4 en WARP; no autoriza conexión automática ante fallo DNS.',
    'ZERONET_URL': 'Gateway reachable inside the container; preserve persistent ZeroNet site state.|Pasarela accesible dentro del contenedor; conserva estado persistente de sitios.',
    'IPFS_GATEWAY_URL': 'IPFS HTTP gateway reachable from the scraper.|Pasarela HTTP IPFS accesible desde scraper.',
    'CHANNEL_CLEANUP_DAYS': 'Inactive-channel retention in days; distinct from opt-in verified offline cleanup.|Conservación de canales inactivos en días; distinta de limpieza opcional sin señal.',
    'MEDIA_SERVER_MIN_REFRESH_MINUTES': 'Minimum minutes between automatic media-server refreshes; prevents duplicate work.|Minutos mínimos entre actualizaciones automáticas; evita duplicación.',
    'EPG_PROGRAM_RETENTION_HOURS': 'Hours to keep expired guide programmes; any negative value keeps them.|Horas de conservación de programas caducados; cualquier negativo los conserva.',
    'TZ': 'Container IANA timezone; independent of browser locale and saved schedule timezone.|Zona IANA del contenedor; independiente de idioma y zona de tareas.',
    'ACESTREAM_HTTP_HOST': 'Internal bundled engine connection host, normally localhost.|Host interno de motor integrado, normalmente localhost.',
    'ACEXY_HOST': 'Engine host reachable by Acexy within the container network.|Host de motor accesible desde Acexy en la red del contenedor.',
    'ACEXY_LISTEN_ADDR': 'Internal listener such as :8080. Deployment port mappings must match.|Escucha interna como :8080. Mapeos del despliegue deben coincidir.',
    'ACEXY_NO_RESPONSE_TIMEOUT': 'Engine response duration, e.g. 30s or 1m30s.|Duración de respuesta del motor, p. ej. 30s o 1m30s.',
    'ACEXY_BUFFER_SIZE': 'Buffer per stream, e.g. 4MiB; not an overall memory quota.|Búfer por emisión, p. ej. 4MiB; no es cuota total de memoria.',
    'ZERONET_UI_HOST': 'Space-separated allowed hostnames for unauthenticated UI. Trusted clients only.|Hosts permitidos por espacios para UI sin autenticación. Solo clientes de confianza.',
    'IPFS_API_HOST': 'Internal bind address; keep loopback unless trusted clients need the unauthenticated API.|Dirección interna; conserva loopback salvo clientes de confianza para API sin autenticación.',
}
groups = {}
for option in runtime:
    key = option['name']
    help = RUNTIME_HELP.get(key)
    if not help:
        if key.startswith('ENABLE_'):
            help = 'Requires installed image capability, matching permissions/volumes/ports. Save does not install software; restart applies.|Requiere capacidad instalada, permisos/volúmenes/puertos. Guardar no instala software; aplica tras reiniciar.'
        elif 'TIMEOUT' in key:
            help = 'Maximum wait per operation, in seconds. Longer waits delay a failure result.|Espera máxima por operación en segundos. Más espera retrasa informar fallos.'
        elif 'RETRIES' in key:
            help = 'Additional source attempts after failure. Zero disables retries; work stays bounded.|Intentos adicionales tras fallo. Cero desactiva reintentos; trabajo limitado.'
        elif 'PORT' in key:
            help = 'Internal service port, 1–65535. Update published deployment mappings separately; no automatic Docker changes.|Puerto interno, 1–65535. Actualiza mapeos de despliegue aparte; sin cambios automáticos Docker.'
        else:
            raise ValueError('Missing runtime copy ' + key)
    f = field('runtime.' + key, option['label'] + '|' + runtime_labels[key], help, option['default'], 'checkbox' if option['kind'] == 'boolean' else 'number' if option['kind'] in ['integer', 'number'] else 'text', default=option['default'], runtime=True)
    if 'minimum' in option:
        f['min'] = option['minimum']
    if 'maximum' in option:
        f['max'] = option['maximum']
    group = option['group']
    if group in ['acestream', 'acexy']:
        group = 'engine-ports'
    if group in ['zeronet', 'ipfs']:
        group = 'gateway-ports'
    groups.setdefault(group, []).append(f)
for group, fs in groups.items():
    title = {
        'playback': 'Playback runtime|Ejecución de reproducción',
        'network': 'Network runtime|Ejecución de red',
        'services': 'Installed services|Servicios instalados',
        'advanced': 'Advanced source runtime|Ejecución avanzada de fuentes',
        'engine-ports': 'Engine and Acexy connections|Conexiones de motor y Acexy',
        'gateway-ports': 'ZeroNet and IPFS connections|Conexiones ZeroNet e IPFS',
    }[group]
    screen(
        'runtime-' + group,
        'runtime',
        title,
        'Shared revision-checked runtime editor; shown values are repository defaults, not installation data.|Editor compartido con revisión; valores de repositorio, no de instalación.',
        '/setup · Connection settings (advanced)',
        ['frontend/src/pages/RuntimeSetup.tsx', 'backend/app/config/runtime-options.json'],
        318,
        [
            facts(
                'Saved / applied / source|Guardado / aplicado / origen',
                [
                    ('Saved|Guardado', 'Repository defaults shown for illustration|Defectos de repositorio como ejemplo'),
                    ('Applied|Aplicado', 'Read boot snapshot separately; do not infer from Save|Lee estado de inicio aparte; no lo deduzcas de Guardar'),
                    ('Effect|Efecto', 'Restart required; commands, paths and secrets stay deployment-owned|Requiere reinicio; órdenes, rutas y secretos siguen en despliegue'),
                ],
            ),
            form(
                'runtime-' + group,
                title,
                fs,
                'Save runtime section|Guardar sección de ejecución',
                'Atomic revision-checked runtime save. Does not restart container or overwrite higher-priority application settings.|Guardado atómico con revisión. No reinicia contenedor ni sobrescribe ajustes de mayor prioridad.',
                'setupService.update expected_revision',
            ),
            links(('settings', 'Return to Settings|Volver a Ajustes'), ('setup', 'Return to setup|Volver a configuración')),
        ],
        states={
            'conflict': 'Runtime revision changed. Reload saved and applied values; never silently overwrite an explicit proxy override.|Cambió revisión. Recarga guardado y aplicado; nunca sobrescribas proxy explícito en silencio.',
            'managed': 'Installed capability is unavailable or supervisor-owned. Explain why the field is read-only; do not fake enablement.|Capacidad ausente o gestionada por supervisor. Explica solo lectura; no finjas activación.',
        },
    )


# Review-04 source reconciliation. Deliberate corrections, not application changes.
def get_screen(key):
    return next(s for s in SCREENS if s['id'] == key)


def fields_of(key):
    return [f for b in get_screen(key)['blocks'] for f in b.get('fields', [])]


def get_field(key):
    return next(f for s in SCREENS for b in s['blocks'] for f in b.get('fields', []) if f['key'] == key)


def add_fields(key, fields):
    next(b for b in get_screen(key)['blocks'] if b['type'] == 'form')['fields'].extend(fields)


get_field('guide.strictness')['options'] = ['strict|Strict|Estricto', 'balanced|Balanced|Equilibrado', 'loose|Relaxed review|Revisión flexible']
get_field('exclusion.kind')['options'] = ['name_contains|Name contains|Nombre contiene', 'name_equals|Exact name|Nombre exacto', 'stream_id_equals|Exact content ID|ID de contenido exacto']
get_field('catalogue.show')['options'] = ['all|All entries|Todas las entradas', 'favorites|Favorites|Favoritas', 'recent|Recently opened|Abiertas recientemente']
get_field('catalogue.confirm_live').pop('required', None)
get_field('catalogue.confirm_live')['help'] = pair('Off saves the catalogue only. On imports only the reviewed compatible live entries; confirmation is required for import.|Desactivado guarda solo el catálogo. Activado importa solo entradas de directo compatibles revisadas; importar exige confirmación.')
get_screen('w3u-save')['blocks'].insert(1, note('Save only is valid. Import and refresh permissions are separate: enabling refresh must not admit new unreviewed identities.|Guardar sin importar es válido. Importar y actualizar tienen permisos separados: activar actualización no admite identidades sin revisar.'))
get_field('provider.provider')['options'] = ['wosti_es|Fútbol en la TV · Spain|Fútbol en la TV · España', 'openfootball|OpenFootball|OpenFootball']
get_field('provider.provider')['value'] = 'wosti_es'
get_field('event.format')['options'] = ['event_import|Event schedule JSON v1|Agenda JSON v1', 'schema_org|SportsEvent JSON-LD|SportsEvent JSON-LD']
get_field('event.state')['options'].append('postponed|Postponed|Aplazado')
get_field('event.timeout_seconds')['value'] = 15
get_field('event.timeout_seconds')['default'] = 15
for s in SCREENS:
    if s['route'] == '/extraction-builder':
        s['route'] = '/scraper/builder'
    for b in s['blocks']:
        for f in b.get('fields', []):
            if f.get('depends') == 'provider.provider' and f.get('equals') == 'wosti':
                f['equals'] = 'wosti_es'

# Separate commands must have independently reviewable save boundaries.
warp = get_screen('warp')
wform = next(b for b in warp['blocks'] if b['type'] == 'form')
mode, license = wform['fields']
mode['options'] = [
    'warp|WARP with standard DNS|WARP con DNS estándar',
    'warp+doh|WARP + DNS over HTTPS|WARP + DNS sobre HTTPS',
    'warp+dot|WARP + DNS over TLS|WARP + DNS sobre TLS',
    'doh|DNS over HTTPS only|Solo DNS sobre HTTPS',
    'tunnel_only|Tunnel; keep current DNS|Túnel; conservar DNS actual',
    'dot|DNS over TLS only|Solo DNS sobre TLS',
    'proxy|SOCKS5 proxy only|Solo proxy SOCKS5',
]
i = warp['blocks'].index(wform)
warp['blocks'][i : i + 1] = [
    form('warp-mode', 'Routing mode|Modo de ruta', [mode], 'Apply mode|Aplicar modo', 'Mode command accepted; read current mode again. Connection is a separate command.|Modo solicitado; lee el modo actual. Conectar es una orden separada.', 'warpService.setMode'),
    form('warp-license', 'Optional WARP licence|Licencia WARP opcional', [license], 'Register licence|Registrar licencia', 'Registration only. Do not change routing mode or reveal the submitted key.|Solo registro. No cambia modo ni muestra clave enviada.', 'warpService.registerLicense', intent=True),
]
license['required'] = True
add_fields('media-server', [field('media.enabled', 'Enable integration|Activar integración', 'On by default; disabled integrations do not receive automatic refresh requests.|Activada por defecto; las desactivadas no reciben actualizaciones automáticas.', True, 'checkbox', default=True)])
add_fields(
    'events',
    [
        field(
            'agenda.when',
            'When|Cuándo',
            'Choose the time scope; changing filters returns to the first page.|Elige ámbito temporal; cambiar filtros vuelve a primera página.',
            'upcoming',
            'select',
            options=['upcoming|Upcoming|Próximos', 'today|Today|Hoy', 'date|Choose a date|Elegir fecha', 'all|All saved|Todos guardados', 'archived|Archived|Archivados'],
        ),
        field('agenda.day', 'Event date|Fecha del evento', 'Only used with Choose a date, interpreted in display timezone.|Solo con Elegir fecha; interpretada en zona de visualización.', '2026-11-08', 'date', depends='agenda.when', equals='date'),
        field('agenda.search', 'Search events|Buscar eventos', 'Original event names remain unchanged.|Conserva nombres originales.', '', 'search'),
        field('agenda.window_days', 'Upcoming window|Intervalo próximo', 'UI choices 7, 14, 30 days; default 14.|Opciones 7, 14, 30 días; por defecto 14.', '14', 'select', options=['7|7 days|7 días', '14|14 days|14 días', '30|30 days|30 días'], advanced=True),
        field('agenda.sport', 'Sport contains|Deporte contiene', 'Free text, separate from saved interests.|Texto libre, separado de intereses guardados.', '', advanced=True),
        field('agenda.competition', 'Competition contains|Competición contiene', 'Free text; keeps original competition names.|Texto libre; conserva nombres originales.', '', advanced=True),
        field('agenda.source', 'Source|Fuente', 'Filter imported provenance without changing the source.|Filtra origen sin cambiar fuente.', '', advanced=True),
    ],
)
get_screen('events')['source'].append('frontend/src/pages/Events.tsx')

presence = ['|Any|Cualquiera', 'yes|Present|Presente', 'no|Missing|Ausente']
add_fields(
    'channels',
    [
        field('filter.epg', 'Guide mapping|Vinculación de guía', 'A guide link is separate from verified media signal.|El vínculo de guía es independiente de señal.', '', 'select', options=['|Any|Cualquiera', 'yes|Mapped|Vinculada', 'no|Not mapped|Sin vincular'], advanced=True),
        field(
            'filter.epg_source_id', 'Guide source|Fuente de guía', 'Source-qualified choice; never infer by display name alone.|Elección identificada por fuente; no deduzcas solo por nombre.', '', 'select', options=['|All sources|Todas', '1|Sample guide|Sample guide', '2|Regional guide|Regional guide'], advanced=True
        ),
        field(
            'filter.streams',
            'Attached streams|Emisiones asignadas',
            'Catalogue-wide filter, before sorting and pagination.|Filtro de catálogo completo, antes de ordenar y paginar.',
            '',
            'select',
            options=['|Any|Cualquiera', 'any|With streams|Con emisiones', 'none|Without streams|Sin emisiones', 'multiple|Multiple streams|Varias emisiones'],
            advanced=True,
        ),
        field(
            'filter.signal',
            'Stream signal|Señal de emisiones',
            'Latest identified A/V packets; ID-found alone is not signal.|Últimos paquetes A/V identificados; ID encontrado no es señal.',
            '',
            'select',
            options=['|Any|Cualquiera', 'verified|At least one verified|Alguna verificada', 'unverified|None verified|Ninguna verificada', 'unknown|All not checked|Ninguna comprobada'],
            advanced=True,
        ),
        *[
            field('filter.' + k, en + '|' + es, 'Presence only. Blank means no filter.|Solo presencia. Vacío no filtra.', '', 'select', options=presence, advanced=True)
            for k, en, es in [('number', 'Channel number', 'Número'), ('logo_url', 'Logo', 'Logo'), ('website', 'Website', 'Web'), ('description', 'Description', 'Descripción')]
        ],
        *[
            field('filter.' + k, en + '|' + es, 'Non-negative whole number; blank removes this bound.|Entero no negativo; vacío elimina límite.', '', 'number', min=0, step=1, advanced=True)
            for k, en, es in [('min_number', 'Minimum number', 'Número mínimo'), ('max_number', 'Maximum number', 'Número máximo'), ('min_streams', 'Minimum streams', 'Emisiones mínimas'), ('max_streams', 'Maximum streams', 'Emisiones máximas')]
        ],
    ],
)
get_screen('channels')['source'].extend(['frontend/src/components/TVChannelFilters.tsx', 'frontend/src/components/TVChannelsTable.tsx'])
add_fields('streams', [field('streams.assigned', 'Linked to TV channel|Vinculada a canal de TV', 'Blank includes both; filtering never changes association.|Vacío incluye ambas; filtrar no cambia asociación.', '', 'select', options=['|Any|Cualquiera', 'true|Linked|Vinculada', 'false|Not linked|Sin vincular'])])
get_screen('streams')['source'].append('frontend/src/components/channels/ChannelFilterBar.tsx')
get_screen('stream-edit')['blocks'].insert(
    1, note('Create-only ID and allow-excluded fields disappear when editing; the existing ID remains read-only. The online observation is not an editable claim of signal.|ID y excepción de exclusión solo al crear; al editar el ID es solo lectura. La observación de señal no es una afirmación editable.')
)

screen(
    'recordings',
    'recordings',
    'Your recordings|Tus grabaciones',
    'Upcoming captures and saved files have different actions.|Las capturas próximas y archivos guardados tienen acciones diferentes.',
    '/recordings',
    'frontend/src/pages/Recordings.tsx',
    319,
    [
        form(
            'recording-filter',
            'Find a recording|Buscar grabación',
            [
                field('recording.search', 'Search recordings|Buscar grabaciones', 'Search original title or channel; reset page when changed.|Busca título o canal original; vuelve a primera página.', '', 'search'),
                field(
                    'recording.state',
                    'Status|Estado',
                    'Status labels include words, never color alone.|Estados con texto, nunca solo color.',
                    '',
                    'select',
                    options=[
                        '|All recordings|Todas',
                        *[
                            a + '|' + b + '|' + c
                            for a, b, c in [
                                ('scheduled', 'Scheduled', 'Programada'),
                                ('starting', 'Starting', 'Iniciando'),
                                ('recording', 'Recording', 'Grabando'),
                                ('recovering', 'Recovering', 'Recuperando'),
                                ('finalizing', 'Finalizing', 'Finalizando'),
                                ('completed', 'Completed', 'Completada'),
                                ('partial', 'Partial', 'Parcial'),
                                ('failed', 'Failed', 'Fallida'),
                                ('missed', 'Missed', 'No iniciada'),
                                ('cancelled', 'Cancelled', 'Cancelada'),
                                ('deleting', 'Deleting', 'Eliminando'),
                                ('deleted', 'Deleted', 'Eliminada'),
                            ]
                        ],
                    ],
                ),
            ],
            'Apply filters|Aplicar filtros',
            'Only the visible recording list changes.|Solo cambia la lista visible.',
            'recordingService.list',
            local=True,
        ),
        rows(
            'Recordings · synthetic|Grabaciones · ficticias',
            [
                ('Coastlines: the Atlantic', 'Recovering · 18 min captured · 21:00 end|Recuperando · 18 min capturados · fin 21:00', 'recording-active'),
                ('Inside the studio', 'Scheduled tomorrow · cancel keeps existing files|Programada mañana · cancelar conserva archivos', 'recording-cancel'),
                ('World in focus', 'Completed · protected · 2 parts|Completada · protegida · 2 partes', 'recording-parts'),
                ('Morning report', 'Missed · no eligible source · no media promised|No iniciada · sin fuente apta · sin prometer archivo', 'recording-storage'),
            ],
        ),
        links(('recording-schedule', 'Schedule a programme|Programar programa'), ('recording-settings', 'Recording settings|Ajustes de grabación'), ('recording-delete', 'Deletion review|Revisar eliminación')),
    ],
    permission='recordings; action permission separately checked',
)
screen(
    'channel-activity',
    'channels',
    'Stream activity|Actividad de emisión',
    'Read provenance and lifecycle without confusing it with current signal.|Consulta origen e historial sin confundirlo con señal actual.',
    '/acestream-channels',
    'frontend/src/components/ChannelActivityLogDialog.tsx',
    320,
    [
        facts('Northlight HD', [('Identifier|Identificador', '0000000000000000000000000000000000000000'), ('Source|Fuente', 'Family channels')]),
        rows(
            'Recent activity · synthetic|Actividad reciente · ficticia',
            [
                ('16:12 · verified online|16:12 · señal verificada', 'Media packets identified; 12 peers observed|Paquetes identificados; 12 pares observados', 'stream-stats'),
                ('16:00 · imported|16:00 · importada', 'Source import updated metadata; no online claim|Importación actualizó datos; no afirma señal', None),
                ('Yesterday · inactive|Ayer · inactiva', 'Source no longer published the ID; retained history|Fuente dejó de publicar ID; historial conservado', None),
            ],
        ),
        links(('stream-edit', 'Edit metadata|Editar datos')),
    ],
)
screen(
    'stream-bulk-fields',
    'channels',
    'Bulk metadata changes|Cambios de datos en lote',
    'Only selected fields are sent; blank and unchanged are different.|Solo se envían campos seleccionados; vacío y sin cambios son distintos.',
    '/acestream-channels',
    'frontend/src/pages/AcestreamChannels.tsx',
    320,
    [
        note('Synthetic selection: 2 explicit stream IDs. Review the exact selection after filtering; do not silently select the entire catalogue.|Selección ficticia: 2 IDs explícitos. Revisa selección tras filtrar; no selecciones todo el catálogo en silencio.'),
        form(
            'bulk-fields',
            'Fields to change|Campos que cambiar',
            [
                *[
                    f
                    for key, label in [('name', 'Name|Nombre'), ('group', 'Group|Grupo'), ('logo', 'Logo URL|URL de logo'), ('tvg_id', 'TVG ID'), ('tvg_name', 'TVG name|Nombre TVG'), ('source_url', 'Source URL|URL de fuente')]
                    for f in [
                        field('bulk.apply_' + key, 'Change ' + label.split('|')[0] + '|Cambiar ' + (label.split('|')[-1]), 'Unchecked keeps each stream’s own value.|Sin marcar conserva el valor propio.', False, 'checkbox'),
                        field('bulk.' + key, label, 'Blank explicitly clears this selected field; name must remain nonempty.|Vacío borra explícitamente este campo; nombre no puede quedar vacío.', '', depends='bulk.apply_' + key, required=key == 'name'),
                    ]
                ],
                field('bulk.is_active', 'Playlist visibility|Visibilidad en lista', 'Choose explicitly; unchanged leaves each current value.|Elige explícitamente; sin cambios conserva valores.', '', 'select', options=['|Unchanged|Sin cambios', 'true|Show|Mostrar', 'false|Hide|Ocultar']),
                field('bulk.epg_update_protected', 'Protect guide metadata|Proteger datos de guía', 'This does not protect the file from deletion.|No protege un archivo frente a eliminación.', '', 'select', options=['|Unchanged|Sin cambios', 'true|Protect|Proteger', 'false|Allow updates|Permitir actualizaciones']),
            ],
            'Review bulk changes|Revisar cambios',
            'Report success and failed IDs separately. No implicit online status editing.|Informa correctos y fallidos por ID. Sin editar estado de señal implícitamente.',
            'BulkChannelEditRequest',
            confirm=pair('Apply only the explicitly selected fields to these 2 streams? Unselected fields remain untouched.|¿Aplicar solo los campos seleccionados a estas 2 emisiones? Los demás se conservan.'),
        ),
        links(('stream-bulk', 'Selection and deletion|Selección y eliminación')),
    ],
)
screen(
    'guide-inventory',
    'guides',
    'Browse guide channels|Consultar canales de guía',
    'Keep source identity visible while browsing matching names.|Mantén fuente visible al consultar nombres parecidos.',
    '/epg?tab=channels',
    ['frontend/src/components/EPGChannelInventoryTable.tsx', 'frontend/src/components/epg/ScheduleView.tsx', 'frontend/src/pages/EPG.tsx'],
    320,
    [
        form(
            'guide-browse',
            'Browse|Consultar',
            [
                field('guide.filter_source', 'Guide source|Fuente de guía', 'All sources retains source-qualified rows.|Todas mantiene filas identificadas por fuente.', '', 'select', options=['|All sources|Todas', '1|Sample guide|Sample guide', '2|Regional guide|Regional guide']),
                field('guide.search', 'Search names|Buscar nombres', 'Filter original guide names.|Filtra nombres originales.', '', 'search'),
                field('guide.day', 'Schedule day|Día de programación', 'Uses display timezone; unknown or missing listings stay explicit.|Usa zona de visualización; faltas quedan explícitas.', '2026-11-08', 'date'),
            ],
            'Apply view|Aplicar vista',
            'Browse only; no assignment or refresh.|Solo consulta; sin asignar ni actualizar.',
            'epgService inventory',
            local=True,
        ),
        rows(
            'Guide identities|Identidades de guía',
            [('Northlight · Sample guide', 'northlight.example · linked · 8 Nov listings|northlight.example · vinculado · programas 8 nov', 'guide-detail'), ('Atelier · Regional guide', 'atelier.example · not linked · ambiguous name|atelier.example · sin vínculo · nombre ambiguo', 'guide-choice')],
        ),
        links(('guide-match', 'Review matching|Revisar coincidencias'), ('guide-rule', 'Matching rules|Reglas de coincidencia')),
    ],
)
screen(
    'player-picker',
    'viewing',
    'Choose what to play|Elegir qué reproducir',
    'A TV channel can use alternatives; a single stream cannot.|Un canal de TV puede usar alternativas; una emisión individual no.',
    'shared player dialog',
    'frontend/src/components/player/ChannelPickerDialog.tsx',
    319,
    [
        form(
            'picker',
            'Catalogue choice|Elección de catálogo',
            [
                field('picker.mode', 'What to pick|Qué elegir', 'Names remain original. Permission and availability still apply.|Nombres originales. Se aplican permisos y disponibilidad.', 'tv', 'select', options=['tv|TV channels|Canales de TV', 'streams|Individual streams|Emisiones individuales']),
                field('picker.search', 'Channel|Canal', 'Search before selecting; loading does not stop current viewing.|Busca antes de elegir; cargar no detiene reproducción.', '', 'search'),
            ],
            'Search catalogue|Buscar en catálogo',
            'Show matches only. Choosing a result is a separate playback intent.|Solo muestra resultados. Elegir uno es intención independiente.',
            'player channel picker',
            local=True,
        ),
        choices(
            'Choose a result|Elegir resultado',
            [('northlight', 'Northlight', 'TV channel · 2 eligible sources|Canal de TV · 2 emisiones aptas'), ('world24', 'World 24', 'TV channel · no verified recent signal|Canal de TV · sin señal reciente verificada')],
            'Use selected channel|Usar canal elegido',
            'Switching releases the current viewer and starts the selected channel; filtering alone does neither.|Cambiar libera espectador actual e inicia canal elegido; filtrar no hace ninguna.',
            single=True,
        ),
        links(('live', 'Return to Live TV|Volver a TV en directo')),
    ],
    permission='live / channels media capability',
)
screen(
    'player-sessions',
    'viewing',
    'Playback sessions|Sesiones de reproducción',
    'Closing your player releases your viewer; other viewers keep their session.|Cerrar tu reproductor libera tu espectador; los demás conservan sesión.',
    'shared player controls',
    'frontend/src/components/player/ActiveStreamsList.tsx',
    319,
    [
        rows('Synthetic sessions|Sesiones ficticias', [('Northlight', 'Direct route · 2 browser viewers · source lease owned|Ruta directa · 2 espectadores · emisión en uso', 'live'), ('World 24', 'Acexy route · cleanup belongs to Acexy|Ruta Acexy · limpieza propia de Acexy', 'browser-player')]),
        command(
            'Stop this viewer|Detener este espectador',
            'Release only this viewer? Shared source remains while any owner still needs it.|¿Liberar solo este espectador? La emisión continúa mientras otro la necesite.',
            'Viewer released once. Final stop waits for ownership and the applicable disconnect grace.|Espectador liberado una vez. Detención final respeta propiedad y plazo de desconexión.',
        ),
        links(('player-picker', 'Choose a channel|Elegir canal')),
    ],
    permission='live; management control may require administrator',
)
screen(
    'dashboard-events',
    'viewing',
    'Events on your home page|Eventos en tu inicio',
    'Browser preferences change what you see, not the event source.|Preferencias del navegador cambian la vista, no la fuente.',
    '/',
    'frontend/src/components/overview/UpcomingEvents.tsx',
    319,
    [
        form(
            'dashboard-events',
            'Upcoming events|Próximos eventos',
            [
                field('dashboard.events', 'Events to show|Eventos que mostrar', 'All upcoming, Following or saved interests.|Todos próximos, seguidos o intereses guardados.', 'all', 'select', options=['all|All upcoming|Todos próximos', 'following|Following|Seguidos', 'interests|My interests|Mis intereses']),
                field('dashboard.zone', 'Display timezone|Zona de visualización', 'Validate IANA zone on blur. Does not change source timezone.|Valida zona IANA al salir. No cambia zona de fuente.', 'Europe/Madrid'),
                field('dashboard.sports', 'Sports|Deportes', 'Saved interests use exact catalogue names.|Intereses usan nombres exactos.', ''),
                field('dashboard.competitions', 'Competitions|Competiciones', 'Empty includes all when no interest is selected.|Vacío incluye todo si no hay intereses.', ''),
                field('dashboard.teams', 'Teams|Equipos', 'Original names retained.|Se conservan nombres originales.', ''),
            ],
            'Apply home preferences|Aplicar preferencias',
            'Browser-only preference; do not create an application-wide settings transaction.|Preferencia local; no crea transacción global de ajustes.',
            'readEventPreferences / writeEventPreferences',
            local=True,
        ),
        rows('Upcoming · synthetic|Próximos · ficticios', [('Northlight Cup', 'Tomorrow 20:00 · timezone Europe/Madrid|Mañana 20:00 · zona Europe/Madrid', 'event-detail')]),
        links(('events', 'Full agenda|Agenda completa')),
    ],
    states={'storage-failed': 'Changes apply in this tab but could not be saved for next visit. Keep your selected interests visible.|Cambios aplicados en pestaña pero sin guardar para próxima visita. Conserva intereses visibles.'},
)
screen(
    'event-broadcasters',
    'events',
    'Broadcaster links|Vínculos de emisoras',
    'Review source-wide mappings without silently changing existing event corrections.|Revisa vínculos de fuente sin cambiar correcciones de eventos en silencio.',
    '/events',
    'frontend/src/components/events/BroadcasterLinks.tsx',
    319,
    [
        rows(
            'Source-qualified mappings|Vínculos por fuente',
            [('Northlight · Sample events', '3 events · linked to Northlight TV|3 eventos · vinculado a Northlight TV', 'event-mapping'), ('Atelier · Regional events', '2 events · unresolved · choose a TV or guide identity|2 eventos · sin resolver · elige identidad TV o guía', 'event-mapping')],
        ),
        note('Removing a link and removing an event overlay are separate operations. The preview rechecks event revision and affected programmes.|Quitar vínculo y quitar superposición son operaciones distintas. La vista revalida revisión y programas afectados.'),
        links(('event-overlay', 'Programme overlay|Superposición de programa')),
    ],
)
screen(
    'setup-source',
    'setup',
    'Add your first channel source|Añadir tu primera fuente',
    'Use the same guarded source editor as Sources.|Usa el mismo editor protegido de Fuentes.',
    '/setup',
    'frontend/src/components/setup/SetupSources.tsx',
    318,
    [
        form(
            'first-source',
            'Choose a source|Elegir fuente',
            [
                field('setup.url', 'Channel source link|Enlace de fuente', 'A website or playlist you are allowed to use. Blank is valid when choosing a broadcaster instead.|Web o lista que puedes usar. Vacío válido si eliges proveedor.', '', 'url'),
                field(
                    'setup.provider',
                    'Broadcaster|Proveedor',
                    'Uses installed registry choices; selection does not fetch until you continue.|Opciones del registro instalado; no consulta hasta continuar.',
                    '',
                    'select',
                    options=['|Choose a source type|Elige tipo', 'web|Website or playlist link|Web o lista', 'provider|Sample broadcaster|Proveedor ficticio'],
                ),
            ],
            'Review source editor|Revisar editor',
            'Continue with the canonical source editor. Already saved sources survive leaving setup.|Continúa en editor compartido. Fuentes guardadas sobreviven al salir.',
            'SetupSources → source editor',
            local=True,
            next='source-web',
        ),
        links(('source-provider', 'Built-in broadcaster editor|Editor de proveedor integrado'), ('setup', 'Skip for now|Posponer')),
    ],
)
screen(
    'setup-guide',
    'setup',
    'Optional programme guide|Guía de programación opcional',
    'A guide is optional; it supplies names and times, not video.|Una guía es opcional; aporta nombres y horarios, no vídeo.',
    '/setup',
    'frontend/src/components/setup/SetupGuide.tsx',
    318,
    [
        form(
            'setup-guide',
            'Choose a guide|Elegir guía',
            [
                field('setup.guide_name', 'Guide name|Nombre de guía', 'Recognisable name; same validation as Programme guides.|Nombre reconocible; misma validación que Guías.', 'Sample guide'),
                field('setup.guide_url', 'Programme guide link|Enlace de guía', 'XMLTV or supported guide URL. No fetch until explicit action.|URL XMLTV o guía admitida. Sin consulta hasta acción explícita.', '', 'url'),
                field('setup.saved_guide', 'Saved programme guide|Guía guardada', 'Reuse a saved source instead of creating a duplicate.|Reutiliza fuente guardada en vez de duplicarla.', '', 'select', options=['|New guide|Guía nueva', '1|Sample guide|Sample guide']),
            ],
            'Review guide|Revisar guía',
            'Reuse the shared editor; guide matching remains an explicit read-only preview first.|Reutiliza editor; vinculación empieza como vista sin cambios.',
            'SetupGuide → EPGSourceDialog',
            local=True,
            next='guide-source',
        ),
        links(('setup', 'Continue without a guide|Continuar sin guía'), ('guide-match', 'Review channel matching|Revisar vinculación')),
    ],
)
for owner, target, label in [
    ('dashboard', 'dashboard-events', 'Home event preferences|Preferencias de eventos'),
    ('streams', 'channel-activity', 'Activity details|Detalles de actividad'),
    ('stream-bulk', 'stream-bulk-fields', 'All editable metadata|Todos los datos editables'),
    ('guide-sources', 'guide-inventory', 'Guide inventory and day|Inventario y día'),
    ('browser-player', 'player-sessions', 'Session ownership|Propiedad de sesiones'),
    ('live', 'player-picker', 'Switch channel|Cambiar canal'),
    ('events', 'event-broadcasters', 'Broadcaster links|Vínculos de emisoras'),
    ('setup', 'setup-source', 'First source|Primera fuente'),
    ('setup', 'setup-guide', 'Optional guide|Guía opcional'),
]:
    get_screen(owner)['blocks'].append(links((target, label)))
# Every independently persisted option is composed as its own transaction.
for sid, bid in [('formats', 'link-identifiers'), ('automation', 'intervals')]:
    s = get_screen(sid)
    b = next(b for b in s['blocks'] if b.get('id') == bid)
    index = s['blocks'].index(b)
    s['blocks'][index : index + 1] = [
        form(
            bid + '-' + str(i),
            f['label'],
            [f],
            'Save this setting|Guardar este ajuste',
            'Only this setting is saved. Other drafts stay unsaved; report this request’s own failure or success.|Solo se guarda este ajuste. Otros borradores siguen sin guardar; informa resultado propio.',
            'configService independent setting: ' + f['key'],
        )
        for i, f in enumerate(b['fields'])
    ]
channel_form = next(b for b in get_screen('channels')['blocks'] if b['type'] == 'form')
channel_form['fields'] = [f for f in channel_form['fields'] if f['key'] != 'filter.active']
get_field('filter.status')['options'] = ['|Any status|Cualquier estado', 'true|Active|Activo', 'false|Inactive|Inactivo']
get_field('filter.status')['help'] = pair('Active or inactive TV channels. Verified signal is a separate advanced filter.|Canales activos o inactivos. Señal verificada es otro filtro avanzado.')
get_field('filter.favorite').update(kind='select', value='', options=['|Any|Cualquiera', 'true|Favorites|Favoritos', 'false|Not favorites|No favoritos'])
for s in SCREENS:
    for b in s['blocks']:
        for f in b.get('fields', []):
            if f['key'].startswith('permissions.'):
                f['unless'] = 'account.administrator'
            if f['key'] == 'runtime.WARP_FORCE_IPV4' and isinstance(f['value'], str):
                f['value'] = f['value'].lower() in ['true', '1']

FAMILIES = {
    k: pair(v)
    for k, v in {
        'recordings': 'Recordings|Grabaciones',
        'access': 'Accounts and access|Cuentas y acceso',
        'channels': 'Channels and streams|Canales y emisiones',
        'guides': 'Programme guides|Guías de programación',
        'playlists': 'Playlists and formats|Listas y formatos',
        'sources': 'Sources and search|Fuentes y búsqueda',
        'extraction': 'Extraction recipes|Recetas de extracción',
        'viewing': 'Viewing|Visualización',
        'events': 'Events|Eventos',
        'integrations': 'Integrations|Integraciones',
        'system': 'System and jobs|Sistema y tareas',
        'settings': 'Settings|Ajustes',
        'setup': 'Setup and recovery|Configuración y recuperación',
        'shell': 'Navigation and shared surfaces|Navegación y superficies compartidas',
        'runtime': 'Advanced runtime|Ejecución avanzada',
    }.items()
}
STATE_LABELS = {
    k: pair(v)
    for k, v in {
        'ready': 'Ready|Lista',
        'loading': 'Loading|Cargando',
        'empty': 'Empty|Vacía',
        'filtered': 'No filter matches|Sin coincidencias',
        'error': 'Request error|Error de solicitud',
        'permission': 'Permission denied|Permiso denegado',
        'dirty': 'Unsaved changes|Cambios sin guardar',
        'pending': 'Pending|Pendiente',
        'success': 'Accepted|Aceptada',
        'conflict': 'Changed revision|Revisión cambiada',
        'partial': 'Partial result|Resultado parcial',
        'ambiguous': 'Ambiguous|Ambigua',
        'blocked': 'Blocked|Bloqueada',
        'busy': 'Already running|Ya en ejecución',
        'capacity': 'No capacity|Sin capacidad',
        'catalogue-unavailable': 'Catalogue unavailable|Catálogo no disponible',
        'changed-host': 'Host changed|Host cambiado',
        'connection': 'Connection lost|Conexión perdida',
        'copy-failed': 'Copy failed|Copia fallida',
        'credential': 'Credential required|Requiere credencial',
        'deferred': 'Background migration|Migración en segundo plano',
        'denied': 'Access denied|Acceso denegado',
        'engine': 'Engine unavailable|Motor no disponible',
        'excluded': 'Import excluded|Importación excluida',
        'expired': 'Expired|Caducada',
        'external': 'External service|Servicio externo',
        'failed': 'Failed|Fallida',
        'finalizing': 'Finalizing|Finalizando',
        'first-use': 'First use|Primer uso',
        'flood': 'Wait before retry|Espera antes de reintentar',
        'gap': 'Missing local time|Hora inexistente',
        'handoff': 'Player handoff|Transferencia al reproductor',
        'held': 'File in use|Archivo en uso',
        'import-failed': 'Import failed|Importación fallida',
        'interrupted': 'Interrupted|Interrumpida',
        'invalid': 'Invalid input|Entrada inválida',
        'last-admin': 'Last administrator|Último administrador',
        'low': 'Low storage|Poco espacio',
        'managed': 'Managed setting|Ajuste gestionado',
        'masked-invalid': 'Stored value invalid|Valor guardado inválido',
        'not-found': 'ID not found|ID no encontrado',
        'ownership-lost': 'Media ownership changed|Propiedad de contenido cambiada',
        'preparing': 'Preparing|Preparando',
        'ready-copy': 'Copy ready|Copia lista',
        'recording-priority': 'Recording takes priority|Prioridad de grabación',
        'refresh-failed': 'Refresh failed|Actualización fallida',
        'refreshing': 'Refreshing|Actualizando',
        'stale': 'Stale review|Revisión obsoleta',
        'stalled': 'Playback stalled|Reproducción detenida',
        'starting': 'Starting|Iniciando',
        'storage-failed': 'Preference not saved|Preferencia no guardada',
        'timeout': 'Time limit reached|Tiempo agotado',
        'token': 'API token required|Requiere token API',
        'too-large': 'Sample too large|Muestra demasiado grande',
        'unavailable': 'Unavailable|No disponible',
        'unknown': 'Unknown observation|Observación desconocida',
        'unresolved': 'Unresolved identity|Identidad sin resolver',
        'unsupported': 'Unsupported|No compatible',
        'waiting': 'Waiting in queue|Esperando en cola',
    }.items()
}


def prepare():
    ids = {s['id'] for s in SCREENS}
    assert len(ids) == len(SCREENS)
    for s in SCREENS:
        assert s['family'] in FAMILIES, s['family']
        has_form = any(b['type'] == 'form' for b in s['blocks'])
        has_rows = any(b['type'] in ['rows', 'choices'] for b in s['blocks'])
        s['baseStates'] = ['loading', 'error', 'permission'] + (['dirty', 'pending', 'success', 'conflict'] if has_form else []) + (['empty', 'filtered', 'partial'] if has_rows else [])
        if any(b['type'] in ['command', 'choices', 'reorder'] for b in s['blocks']):
            s['baseStates'] = list(dict.fromkeys(s['baseStates'] + ['pending', 'success', 'conflict']))
        s['states'] = {k: pair(v) for k, v in s.get('states', {}).items()}
        for p in s['source']:
            source_text(p)  # fail on stale evidence path
        for b in s['blocks']:
            if b.get('next'):
                assert b['next'] in ids
            for row in b.get('items', []) + b.get('rows', []):
                if isinstance(row, dict) and row.get('target'):
                    assert row['target'] in ids, row['target']
            for f in b.get('fields', []):
                if f['kind'] == 'select':
                    assert str(f['value']) in [o.split('|')[0] for o in f['options']], f
    return dict(revision=REV, screens=SCREENS, families=FAMILIES, stateLabels=STATE_LABELS)


def md(v):
    return str(v).replace('|', '&#124;').replace('\n', '<br>')


def display_spec(b):
    typ = b['type']
    out = []
    if typ == 'facts':
        out += ['**Read-only context: ' + ' / '.join(b['title']) + '**', '', '| Label · EN / ES | Synthetic value or state · EN / ES |', '|---|---|']
        out += ['| ' + md(' / '.join(k)) + ' | ' + md(' / '.join(v)) + ' |' for k, v in b['rows']]
    elif typ == 'rows':
        out += ['**' + ' / '.join(b['title']) + '**', '']
        for row in b['rows']:
            target = f' [Open related workflow](workflow-prototype.html?screen={row["target"]}).' if row.get('target') else ''
            out.append('- ' + ' / '.join(row['title']) + ': ' + ' / '.join(row['text']) + target)
    elif typ == 'links':
        out += ['**Contextual exits:** ' + '; '.join('[' + ' / '.join(row['label']) + '](workflow-prototype.html?screen=' + row['target'] + ')' for row in b['items']) + '.']
    elif typ == 'player':
        out += ['**Player region:** ' + b['title'] + ' · ' + ' / '.join(b['status']) + '. Static illustration only; use the media interaction contract for ownership and integrated acceptance.']
    elif typ in ['code', 'sample']:
        out += ['**Synthetic ' + ('sample' if typ == 'sample' else 'read-only output') + ':**', '', '```text', b['text'], '```']
    elif typ == 'copy':
        out += ['**Copy action:** ' + ' / '.join(b['label']) + '. Placeholder `' + b['value'] + '`; show success or a selectable fallback without logging the value.']
    elif typ == 'feature':
        out += ['**Featured item:** ' + b['title'] + ' · ' + ' / '.join(b['text']) + f'. [Open context](workflow-prototype.html?screen={b["target"]}).']
    elif typ == 'steps':
        out += ['**Progress:** ' + ' → '.join(' / '.join(v) for v in b['items']) + '.']
    return out + [''] if out else []


def schema_inventory():
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', REV, 'backend/app/schemas'], cwd=ROOT.parents[2], text=True).splitlines()
    result = []
    for p in paths:
        if not p.endswith('.py'):
            continue
        tree = ast.parse(source_text(p))
        for c in tree.body:
            if not isinstance(c, ast.ClassDef):
                continue
            for n in c.body:
                if not isinstance(n, ast.AnnAssign) or not isinstance(n.target, ast.Name):
                    continue
                result.append(dict(path=p, line=n.lineno, model=c.name, key=n.target.id, type=ast.unparse(n.annotation), default=ast.unparse(n.value) if n.value else 'required / inherited validation', contract=p.rsplit('/', 1)[1][:-3] + '.' + c.name + '.' + n.target.id))
    return result


def build():
    data = prepare()
    schemas = schema_inventory()
    contracts = {x['contract']: x for x in schemas}
    (ROOT / 'workflow-data.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'workflow-data.js').write_text('// Generated by compose_workflows.py; synthetic data only.\nwindow.WORKFLOWS = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    spec = [
        '# Composed workflow specification · review 04',
        '',
        f'Application evidence pinned to `{REV}`. Composed design proposals, author-reviewed through the recorded checks; not user-approved or implemented. {len(SCREENS)} compositions; {sum(len(b.get("fields", [])) for s in SCREENS for b in s["blocks"])} field occurrences. Original names and machine values remain unchanged.',
        '',
        'Read [interaction contracts](interaction-contracts.md), [source contracts](source-contracts.md), [traceability](traceability-matrix.md), [rendered verification](verification-review-04.md) and [acceptance protocols](acceptance-protocols.md). The local prototype is intentionally not an API/client implementation. Adapter names below describe integration boundaries; use the linked current source for exact callable signatures and request paths.',
        '',
        '## How to implement this specification',
        '',
        'A screen is a composed workflow, not necessarily a new route. Dialog-intent compositions can reuse the existing dialog host; on phones use a full-height dialog with the same accessible title, safe Cancel, focus return and dirty guard. Do not add routes merely to mirror this gallery. Existing routing, account gates and API transactions remain authoritative.',
        '',
        'Every form below inherits validation before submission, disabled pending submission, local inline errors, server-error draft retention, explicit stale-conflict review, a safe cancel, and the stated transaction boundary. “Default” distinguishes repository defaults from illustrative saved values. A fixture is never permission to change defaults. Blank, null, zero and unknown remain distinct. Server validation remains authoritative; the prototype models representative checks.',
        '',
        'Select options are written as `machine value → English / Español`. Optional field values, domain data, IDs, addresses, dates and logs must not be translated. Credentials never persist in prototype storage. All numbers in screenshots are synthetic.',
        '',
    ]
    matrix = [
        '# Surface → evidence → composition → interaction → verification → acceptance',
        '',
        f'Current public source: `{REV}`. Each row is an authored, composed design proposal. “Rendered” evidence is the current [verification run](verification-review-04.md), not an implementation or user-approval claim. Exact field rows and state lists appear in the linked specification.',
        '',
        'This matrix covers every composed surface and field occurrence. [Source control map](source-control-map.md) records the current input-bearing TSX modules, including reused controls; [source contracts](source-contracts.md) preserves request/response constraints separately from visual fields. Historical screenshots are not new passes.',
        '',
    ]
    for s in SCREENS:
        sid = s['id']
        href = 'workflow-prototype.html?screen=' + sid
        links_source = '; '.join(f'[{p.rsplit("/", 1)[-1]}](https://github.com/Pipepito/acestream-scraper/blob/{REV}/{p})' for p in dict.fromkeys(s['source']))
        states = ['ready', *dict.fromkeys(s['baseStates'] + list(s['states']))]
        spec += [
            f'<a id="{sid}"></a>',
            f'## {s["title"][0]} / {s["title"][1]}',
            '',
            f'[Open composition]({href}) · existing route/context: `{s["route"]}` · implementation [#{s["owner"]}](https://github.com/Pipepito/acestream-scraper/issues/{s["owner"]})',
            '',
            f'**Purpose:** {s["goal"][0]} / {s["goal"][1]}',
            '',
            f'**Evidence:** {links_source}',
            '',
            f'**Permission:** {s["permission"]}. Preserve current server enforcement; view availability does not grant action authority.',
            '',
            f'**Rendered states:** {", ".join(states)}. Use the prototype state selector. Error/conflict states preserve a draft, but never grant permission to replay a stale operation.',
            '',
        ]
        for k, v in s['states'].items():
            spec += [f'- **{k}:** {v[0]} / {v[1]}' + (' Page title: ' + ' / '.join(s['stateTitles'][k]) + '.' if k in s.get('stateTitles', {}) else '')]
        spec += ['']
        for key, copy in s.get('implementation_states', {}).items():
            spec += [f'**Implementation constraint for `{key}`:** ' + ' / '.join(copy), '']
        for b in s['blocks']:
            typ = b['type']
            if typ == 'form':
                spec += [
                    f'### {b["title"][0]} / {b["title"][1]}',
                    '',
                    f'**Save timing:** {b.get("saveTiming", "explicit action")}. **Action:** {b["action"][0]} / {b["action"][1]}. **Boundary:** `{b["api"]}`. ' + ('View/preview only; no persistent data mutation.' if b.get('local') else 'Submit this resource only; other sections retain independent state.'),
                    '',
                    f'**Consequence:** {b["effect"][0]} / {b["effect"][1]}',
                    '',
                ]
                if b.get('confirm'):
                    spec += [f'**Confirmation:** {b["confirm"][0]} / {b["confirm"][1]}. Cancel initially focused; Escape cancels; return focus to invoker.', '']
                spec += ['| Field and control | EN / ES label and help | Default / fixture | Constraints and dependencies |', '|---|---|---|---|']
                for f in b['fields']:
                    constraints = []
                    for key in ['required', 'min', 'max', 'step', 'maxlength', 'minlength', 'pattern', 'readonly', 'disabled']:
                        if key in f:
                            constraints.append(key + '=' + str(f[key]))
                    if f.get('implementation_help'):
                        constraints.append('Adapter/contract note: ' + ' / '.join(f['implementation_help']))
                    if f.get('advanced'):
                        constraints.append('Advanced disclosure')
                    if f.get('depends'):
                        constraints.append('enabled when ' + f['depends'] + ('=' + str(f['equals']) if 'equals' in f else ' is on'))
                    if f.get('unless'):
                        constraints.append('disabled when ' + f['unless'] + ' is on')
                    if f.get('options'):
                        constraints.append('; '.join(o.split('|')[0] + ' → ' + ' / '.join(o.split('|')[1:]) for o in f['options']))
                    contract = contracts.get(f.get('contract', ''))
                    if contract:
                        constraints.append(f'[API constraint](source-contracts.md#{uid(contract["contract"])})')
                    default = 'Repository default: ' + str(f['default']) if 'default' in f else 'Load current saved/server value; illustrative fixture: ' + str(f['value'])
                    if f['kind'] == 'password':
                        default = 'Never read back a saved secret. Empty input; omit/clear/replace semantics follow this resource.'
                    spec.append('| `' + f['key'] + '` · ' + f['kind'] + ' | ' + md(' / '.join(f['label'])) + '<br>' + md(' / '.join(f['help'])) + ' | ' + md(default) + ' | ' + md('; '.join(constraints) or 'No additional prototype constraint; preserve current source validation.') + ' |')
                spec += ['']
            elif typ in ['choices', 'command', 'reorder']:
                label = b.get('title', b.get('label', pair('Reorder')))
                detail = b.get('effect', b.get('consequence', pair('')))
                spec += [f'**{label[0]} / {label[1]}:** ' + ' / '.join(detail), '']
                if typ == 'choices':
                    spec += ['No automatic selection. ' + ('Exactly one choice.' if b.get('single') else 'Select explicit rows.') + ' Show row-specific result; expire selection on review-token/revision changes.', '']
                if typ == 'command':
                    spec += ['Result copy: ' + ' / '.join(b['result']) + '. Recheck eligibility/ownership at execution; do not treat acceptance as completed work.', '']
            elif typ == 'note':
                spec += ['**Explanation:** ' + ' / '.join(b['text']), '']
            else:
                spec += display_spec(b)
        for state, blocks in s.get('stateBlocks', {}).items():
            spec += [f'### Authored composition for `{state}`', '', f'[Open this state]({href}&state={state}). This replaces the default content rather than placing a warning over contradictory fixture data.', '']
            for b in blocks:
                if b['type'] == 'note':
                    spec += ['**Explanation:** ' + ' / '.join(b['text']), '']
                elif b['type'] == 'form':
                    spec += ['**Retained editor:** ' + ' / '.join(b['title']) + '. Same fields and transaction defined above; state eligibility can disable editing.', '']
                elif b['type'] == 'command':
                    spec += ['**Retained command:** ' + ' / '.join(b['label']) + '. Disabled while finalizing or recovering the interrupted journal.', '']
                else:
                    spec += display_spec(b)
        matrix += [
            f'<a id="{sid}"></a>',
            f'## {s["title"][0]}',
            '',
            '| Current surface / fields / states | Source evidence | Composition and interaction | Rendered evidence | Remaining acceptance owner |',
            '|---|---|---|---|---|',
            f'| `{s["route"]}`; '
            + md(', '.join(f['key'] for b in s['blocks'] for f in b.get('fields', [])) or 'read/control surface')
            + '; '
            + md(', '.join(states))
            + f' | {links_source} | [Composed screen]({href}); [specification](workflow-specification.md#{sid}) | [Desktop EN](workflow-exports/{sid}-en.jpg), [phone ES](workflow-exports/{sid}-es.jpg); [run](verification-review-04.md) | #{s["owner"]}: implement against source, integrated states and contracts; #317 localization; #324 manual AT/device and end-to-end acceptance. Unapproved / unimplemented. |',
            '',
        ]
    (ROOT / 'workflow-specification.md').write_text('\n'.join(spec))
    (ROOT / 'traceability-matrix.md').write_text('\n'.join(matrix))
    contract_doc = [
        '# Current source contract appendix',
        '',
        f'Machine-extracted public Pydantic annotations/default expressions from `{REV}`. These are evidence, not a new API, UI or exhaustive validator interpretation. Required inherited validators, model validators and service enforcement remain authoritative. Response/transport-only fields are intentionally not editable controls. Use each linked source to inspect validators and inheritance.',
        '',
    ]
    for x in schemas:
        contract_doc += [f'<a id="{uid(x["contract"])}"></a>', f'### `{x["contract"]}`', '', f'[{x["path"]}:{x["line"]}](https://github.com/Pipepito/acestream-scraper/blob/{REV}/{x["path"]}#L{x["line"]}) · type `{x["type"]}`', '', '```python', x['default'], '```', '']
    (ROOT / 'source-contracts.md').write_text('\n'.join(contract_doc))
    build_control_map()
    build_gallery()
    print(json.dumps(dict(screens=len(SCREENS), field_occurrences=sum(len(b.get('fields', [])) for s in SCREENS for b in s['blocks']), schema_fields=len(schemas)), indent=2))


def uid(value):
    return re.sub(r'[^a-z0-9_-]', '-', value.lower())


def build_control_map():
    # Include dynamic labels by mapping their containing module, not pretending a regex is a field audit.
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', REV, 'frontend/src'], cwd=ROOT.parents[2], text=True).splitlines()
    bysource = defaultdict(list)
    for s in SCREENS:
        for p in s['source']:
            bysource[p].append(s['id'])
    shared = {
        'NewPasswordField': ['access-create', 'access-password'],
        'RemotePlayersSection': ['remote-player', 'remote-control', 'remote-discovery'],
        'PlaylistDialog': ['playlist'],
        'AdvancedSearch': ['channels', 'streams'],
        'AssignTVChannelDialog': ['channel-assign'],
        'ChannelTable': ['streams'],
        'CheckEngineFields': ['automation'],
        'EPGChannelInventoryTable': ['guide-inventory'],
        'NavBar': ['settings', 'preferences'],
        'StreamCheckScopeField': ['automation'],
        'TVChannelFilters': ['channels'],
        'TVChannelsTable': ['channels', 'channel-reorder'],
        'WhatsNewNotice': ['notices'],
        'ChannelCardList': ['streams'],
        'ChannelFilterBar': ['streams'],
        'NowNext': ['guide-detail'],
        'RulesTab': ['guide-rule'],
        'ScheduleView': ['guide-inventory'],
        'EventArtwork': ['event-detail'],
        'EventInterestFields': ['events', 'dashboard-events'],
        'PageHeader': ['dashboard'],
        'BrowseModeToggle': ['live'],
        'EventList': ['live', 'events'],
        'StreamList': ['live'],
        'TVChannelList': ['live'],
        'SourceChips': ['player-tracks'],
        'GuideRecordingSelector': ['recording-schedule', 'player-picker'],
        'NetworkSettings': ['network'],
        'RecipeFields': ['helper-html', 'helper-json', 'helper-regex'],
        'VisualPicker': ['helper-html'],
        'JsonPicker': ['helper-json'],
        'RecipeResults': ['helper-results'],
        'ContentSection': ['settings'],
        'SetupWizard': ['setup'],
        'App': ['not-found', 'settings'],
    }
    doc = [
        '# Current source control map',
        '',
        f'Source `{REV}`. Module-level census of input/dialog/route surfaces. Static label examples are an audit aid, not a claim that regex discovers all dynamic fields. Each module is paired with authored compositions and the detailed field/spec ledger. Headless hooks and API response properties are evidence rather than extra visual screens.',
        '',
        '| Source module | Literal control labels (sample) | Composed use |',
        '|---|---|---|',
    ]
    unmapped = []
    for p in paths:
        if not p.endswith('.tsx') or '.test.' in p or '__tests__' in p:
            continue
        text = source_text(p)
        if not re.search(r'<(?:TextField|Select|Checkbox|Switch|Slider|Dialog|Drawer|Autocomplete|Route)\b', text):
            continue
        name = p.rsplit('/', 1)[-1][:-4]
        mapped = bysource.get(p) or shared.get(name)
        if not mapped:
            # Unmapped low-level wrappers are documented explicitly, not silently marked covered.
            if name in ['ConfirmDialog']:
                mapped = ['unsaved', 'recovery-fresh']
            else:
                unmapped.append(p)
                mapped = []
        labels = re.findall(r'(?:label|placeholder)=["\']([^"\']+)["\']', text)
        doc.append(f'| [{name}](https://github.com/Pipepito/acestream-scraper/blob/{REV}/{p}) | ' + md('; '.join(dict.fromkeys(labels))) + ' | ' + (', '.join(f'[{x}](workflow-specification.md#{x})' for x in mapped) or '**RECONCILE BEFORE HANDOFF**') + ' |')
    (ROOT / 'source-control-map.md').write_text('\n'.join(doc) + '\n')
    if unmapped:
        print('UNMAPPED CONTROL MODULES:', json.dumps(unmapped))


def build_gallery():
    style = 'body{font:16px/1.6 Inter,system-ui,sans-serif;margin:0;background:#f5f3ef;color:#202232}main{max-width:1400px;margin:auto;padding:28px}h1{font-size:clamp(28px,4vw,48px);line-height:1.1}a{color:inherit;text-underline-offset:4px}a:focus-visible{outline:3px solid #744017;outline-offset:5px}.links{display:flex;flex-wrap:wrap;gap:14px}.links a{padding:10px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:28px}.card{border-top:1px solid #85838d;padding-top:20px;min-width:0}.card p{color:#626272}.thumbs{display:flex;align-items:start;gap:12px}.thumbs a:first-child{width:72%}.thumbs a:last-child{width:28%}img{width:100%;height:240px;object-fit:cover;object-position:top;border:1px solid #85838d;border-radius:4px}h2{margin-top:44px}h3{font-size:20px}code{overflow-wrap:anywhere}.note{padding:20px;background:#eeece7}nav{border-block:1px solid #85838d;padding:16px 0}@media(max-width:500px){main{padding:20px 16px}}'
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AceStream · complete workflow review</title><style>'
        + style
        + '</style></head><body><main><h1>AceStream Scraper<br>Workflow design review</h1><p>'
        + str(len(SCREENS))
        + ' composed workflows · English / Español · light / dark · desktop / phone</p><p class="note">Synthetic design proposals. Composed and checked as recorded, not approved or implemented. Existing IBM Plex / teal application standards remain authoritative. No installation requests, media sessions or real credentials.</p><div class="links"><a href="index.html">Earlier gallery</a><a href="workflow-specification.md">Field and interaction specification</a><a href="traceability-matrix.md">Evidence matrix</a><a href="verification-review-04.md">Current verification</a><a href="acceptance-protocols.md">Remaining acceptance</a></div><h2>Comparable directions</h2><p>Same workflow and foundations. Review color and typographic emphasis independently; none is an accepted rebrand.</p><div class="links">'
    ]
    for d, label in [('calm', 'Calm'), ('broadcast', 'Expressive')]:
        for c in ['coral', 'lime']:
            parts.append(f'<a href="workflow-prototype.html?screen=recordings&direction={d}&palette={c}&theme=dark">{label} · {c}</a>')
    parts.append('</div><nav aria-label="Workflow families" class="links">' + ''.join(f'<a href="#{k}">{v[0]}</a>' for k, v in FAMILIES.items()) + '</nav>')
    for family, labels in FAMILIES.items():
        group = [s for s in SCREENS if s['family'] == family]
        if not group:
            continue
        parts.append(f'<section id="{family}"><h2>{labels[0]} / {labels[1]}</h2><div class="grid">')
        for s in group:
            sid = s['id']
            parts.append(
                f'<article class="card"><h3><a href="workflow-prototype.html?screen={sid}">{html.escape(s["title"][0])}</a></h3><p>{html.escape(s["goal"][0])}</p><div class="thumbs"><a href="workflow-exports/{sid}-en.jpg"><img loading="lazy" src="workflow-exports/{sid}-en.jpg" alt="{html.escape(s["title"][0])} · English light desktop"></a><a href="workflow-exports/{sid}-es.jpg"><img loading="lazy" src="workflow-exports/{sid}-es.jpg" alt="{html.escape(s["title"][1])} · Español dark phone"></a></div><div class="links"><a href="workflow-prototype.html?screen={sid}&lang=es&theme=dark">Probar en español</a><a href="workflow-specification.md#{sid}">Fields and states</a></div></article>'
            )
        parts.append('</div></section>')
    parts.append('</main></body></html>')
    (ROOT / 'workflow-gallery.html').write_text('\n'.join(parts) + '\n')


screen(
    'channel-inline',
    'channels',
    'Number and favorite|Número y favorito',
    'Quick controls keep row actions available on desktop and phone.|Controles rápidos conservan acciones en escritorio y móvil.',
    '/tv-channels',
    ['frontend/src/components/ChannelNumberField.tsx', 'frontend/src/components/TVChannelsTable.tsx'],
    320,
    [
        facts('Northlight', [('Guide identity|Identidad de guía', 'Sample guide : northlight.example'), ('Signal|Señal', 'Verified 16:12 · synthetic|Verificada 16:12 · ficticia')]),
        form(
            'inline-number',
            'Channel number|Número de canal',
            [field('inline.number', 'Number for Northlight|Número de Northlight', 'Whole number ≥0. Enter or blur saves; blank clears; Escape restores. Pending locks this field only.|Entero ≥0. Enter o salir guarda; vacío borra; Escape restaura. Pendiente bloquea solo este campo.', 12, 'number', min=0, step=1)],
            'Save number|Guardar número',
            'Number saved. Other row actions and current filters stay available.|Número guardado. Acciones y filtros siguen disponibles.',
            'TVChannelUpdate.channel_number',
            saveTiming='enter-blur',
        ),
        form(
            'inline-favorite',
            'Favorite|Favorito',
            [field('inline.favorite', 'Favorite Northlight|Marcar Northlight favorito', 'Saves immediately. Failure restores last saved value and offers retry.|Guarda inmediatamente. Fallo restaura valor guardado y ofrece reintento.', False, 'checkbox')],
            'Save favorite|Guardar favorito',
            'Favorite saved independently of number.|Favorito guardado independientemente del número.',
            'TVChannelUpdate.is_favorite',
            saveTiming='immediate',
        ),
        links(('channel-detail', 'Channel details|Detalles del canal'), ('channel-edit', 'Edit|Editar'), ('channel-reorder', 'Reorder complete catalogue|Reordenar catálogo completo'), ('channel-delete', 'Delete channel|Eliminar canal')),
    ],
)
get_screen('channels')['blocks'].append(links(('channel-inline', 'Number and favorite controls|Controles de número y favorito')))
add_fields(
    'channels',
    [
        field('filter.sort', 'Sort by|Ordenar por', 'Applied after catalogue-wide filters and before pagination.|Después de filtros de catálogo y antes de paginar.', 'name', 'select', options=['name|Name|Nombre', 'channel_number|Number|Número', 'category|Category|Categoría', 'country|Country|País']),
        field('filter.page_size', 'Rows per page|Filas por página', 'Changing size resets to first page. Counts describe filtered total.|Cambiar tamaño vuelve a primera página. Recuento del total filtrado.', '25', 'select', options=['10|10|10', '25|25|25', '50|50|50', '100|100|100']),
    ],
)
get_field('xml.days_back')['help'] = pair('Display offset default −1. Existing API stores days_back=1; translate offset to its absolute day count. Do not change stored sign silently.|Desfase visible −1. API actual guarda days_back=1; traduce a recuento absoluto. No cambies signo guardado en silencio.')

# Preserve source-only contract gaps explicitly instead of making unsupported
# writes appear successful in a polished replacement.
get_screen('stream-bulk-fields')['source'].extend(['frontend/src/components/BulkOperations.tsx', 'frontend/src/services/channelService.ts', 'backend/app/schemas/channel.py', 'backend/app/api/endpoints/channels.py'])
get_screen('stream-bulk-fields')['blocks'].append(
    form(
        'bulk-tv-properties',
        'TV-channel properties|Propiedades del canal de TV',
        [
            field(
                'bulk.category',
                'Category|Categoría',
                'Belongs to the linked TV channel. Current stream bulk form exposes this without a matching stream request field; use the TV-channel editor.|Pertenece al canal de TV. El formulario actual lo muestra sin campo equivalente en solicitud de emisión; usa editor de TV.',
                'Documentary',
                readonly=True,
            ),
            field('bulk.country', 'Country|País', 'Choose the linked TV channel before editing; several selected streams may share it.|Elige canal TV antes de editar; varias emisiones pueden compartirlo.', 'ES', readonly=True),
            field('bulk.language', 'Language|Idioma', 'Preserve original saved code and change once for the selected TV channel.|Conserva código guardado y cambia una vez para canal TV elegido.', 'es', readonly=True),
        ],
        'Review linked TV channel|Revisar canal TV vinculado',
        'No stream metadata write. Review the TV-channel editor before changing shared properties.|No escribe datos de emisión. Revisa editor TV antes de cambiar propiedades compartidas.',
        'source-only contract mismatch → TVChannelUpdate',
        local=True,
        next='channel-edit',
    )
)

# Novice-facing action copy; retain implementation detail in the handoff metadata.
DISPLAY_COPY = {
    'guide-match': ('effect', 'The guide may have changed. Apply only after the latest preview has been reviewed.|La guía puede haber cambiado. Aplica solo tras revisar la vista más reciente.'),
    'guide-auto': ('effect', 'Use exact matches after future successful updates. Ambiguous matches still need your review.|Usa coincidencias exactas tras futuras actualizaciones correctas. Las ambiguas requieren revisión.'),
    'w3u': ('effect', 'Preview only. If this review expires, load a fresh preview before importing.|Solo vista previa. Si caduca la revisión, carga otra antes de importar.'),
    'exclusion': ('effect', 'Saved. Future imports use this rule; existing channels stay unchanged.|Guardado. Las futuras importaciones usan esta regla; los canales existentes se conservan.'),
    'channel-reorder': ('effect', 'Save consecutive numbers for all channels together. Cancel keeps the saved numbers.|Guarda números consecutivos para todos los canales juntos. Cancelar conserva los números guardados.'),
    'event-overlay': ('effect', 'Review the exact channel, times and affected programmes before applying.|Revisa canal, horarios y programas afectados antes de aplicar.'),
    'warp-exclusions': ('effect', 'Save the host list, then check whether WARP has applied every change. Show any hosts still waiting.|Guarda lista y comprueba si WARP aplicó cada cambio. Muestra hosts pendientes.'),
    'warp-startup': ('effect', 'Saved for the next container start. Currently running settings stay visible separately.|Guardado para próximo inicio del contenedor. Los ajustes activos se muestran por separado.'),
    'schedule-anchors': ('effect', 'Save these start times and timezone together. Save cleanup thresholds separately.|Guarda horarios y zona juntos. Guarda límites de limpieza por separado.'),
    'offline-cleanup': ('effect', 'Save cleanup choices. Its scheduled start time is saved separately.|Guarda opciones de limpieza. Su horario de inicio se guarda por separado.'),
    'dashboard-events': ('effect', 'Use these preferences in this browser.|Usa estas preferencias en este navegador.'),
}
for sid, (key, copy) in DISPLAY_COPY.items():
    for b in get_screen(sid)['blocks']:
        if key in b:
            b['implementation_' + key] = b[key]
            b[key] = pair(copy)
for s in SCREENS:
    if s['family'] == 'runtime':
        for b in s['blocks']:
            if b['type'] == 'form':
                b['implementation_effect'] = b['effect']
                b['effect'] = pair('Save for the next container start. This does not restart the container or change a higher-priority app setting.|Guarda para próximo inicio. No reinicia contenedor ni cambia un ajuste de app con prioridad mayor.')


# Conditional form modes and intentional local-draft ownership.
for screen_data in SCREENS:
    for block_data in screen_data['blocks']:
        if block_data.get('local') and screen_data['family'] in ['extraction', 'events', 'setup'] and block_data.get('id') not in ['agenda', 'event-refresh']:
            block_data['guardDraft'] = True
for block_data in get_screen('stream-match')['blocks']:
    if block_data['type'] == 'choices':
        block_data['items'][1]['requires'] = 'matching.include_similar'
import_form = next(b for b in get_screen('event-import')['blocks'] if b['type'] == 'form')
import_form['fields'] = deepcopy(import_form['fields'])
for f in import_form['fields']:
    if f['key'] == 'event.input':
        continue
    f['depends'] = 'event.input'
    f['equals'] = 'json' if f['key'] == 'event.json' else 'url' if f['key'] in ['event.schedule_url', 'event.format', 'event.timeout_seconds'] else 'manual'

get_field('xml.days_back')['max'] = 0
get_field('xml.days_back')['help'] = pair('Start 0–14 days before today; display default −1. The API stores days_back=1, so convert this offset to its absolute count.|Inicio de 0 a 14 días antes de hoy; defecto visible −1. API guarda days_back=1; convierte el desfase a recuento absoluto.')

# Material state changes receive their own composition, rather than a banner
# contradicting the populated fixture underneath it.
get_screen('dashboard')['stateBlocks'] = {
    'first-use': [
        note('Your catalogue is empty. Add a channel source to begin; a programme guide is optional.|Tu catálogo está vacío. Añade una fuente para empezar; la guía es opcional.'),
        rows(
            'Get ready to watch|Prepara tu televisión',
            [
                ('1 · Add a channel source|1 · Añade una fuente', 'Use a website or playlist link, or an installed broadcaster.|Usa una web, lista o proveedor instalado.', 'setup-source'),
                ('2 · Optional programme guide|2 · Guía opcional', 'Adds names and times; video does not require a guide.|Añade nombres y horarios; no hace falta para vídeo.', 'setup-guide'),
                ('3 · Review your channels|3 · Revisa tus canales', 'Imported channels are not yet proof of signal.|Importar no demuestra señal.', 'channels'),
            ],
        ),
        links(('setup', 'Start setup|Empezar configuración')),
    ]
}
get_screen('access-activate')['stateBlocks'] = {
    'blocked': [
        note('Accounts cannot be activated over public-address HTTP. Open this installation using HTTPS, or its private address from your home network.|No se pueden activar cuentas por HTTP público. Abre la instalación por HTTPS o por su dirección privada desde casa.', 'warning'),
        facts('Connection|Conexión', [('Address type|Tipo de dirección', 'Public hostname · unencrypted HTTP|Nombre público · HTTP sin cifrar'), ('Password entry|Entrada de contraseña', 'Unavailable on this connection|No disponible en esta conexión')]),
        links(('access-transport', 'Supported connections|Conexiones compatibles')),
    ]
}
get_screen('stream-stats')['stateBlocks'] = {
    'unknown': [
        facts(
            'Northlight HD · no measurement yet|Northlight HD · sin medición',
            [
                ('Verified signal|Señal verificada', 'Not checked|Sin comprobar'),
                ('Engine ID lookup|Búsqueda de ID', 'Unknown|Desconocida'),
                ('Peers|Pares', 'Unknown · not zero|Desconocido · no es cero'),
                ('Download / upload|Descarga / subida', 'Unknown · no observation time|Desconocido · sin hora de observación'),
                ('Encoded bitrate|Bitrate codificado', 'Unknown|Desconocido'),
            ],
        ),
        note('A skipped check does not create a new observation or move its timestamp. Keep any older observation with its original time.|Una comprobación omitida no crea observación ni mueve su hora. Conserva una observación anterior con su hora original.'),
        links(('automation', 'Review checking engine|Revisar motor de comprobación'), ('streams', 'Back to streams|Volver a emisiones')),
    ]
}
get_screen('helper-large')['stateBlocks'] = {
    'too-large': [
        note('This sample exceeds the 32 MiB source limit. It has not been parsed or sent for a test. Choose a smaller representative sample.|La muestra supera el límite de fuente de 32 MiB. No se ha analizado ni enviado a probar. Elige una muestra representativa menor.', 'warning'),
        facts(
            'Limits have different purposes|Límites con fines distintos',
            [
                ('Source admission|Admisión de fuente', '32 MiB maximum|Máximo 32 MiB'),
                ('Browser rendering|Visualización', 'Smaller bounded budget; large admitted samples may need raw/manual fields|Presupuesto menor; muestras admitidas pueden necesitar texto/campos manuales'),
                ('Recipe document|Documento de receta', '512 KiB maximum|Máximo 512 KiB'),
            ],
        ),
        links(('helper-standalone', 'Choose a different sample|Elegir otra muestra'), ('helper-manual', 'Read the manual-field workflow|Ver flujo de campos manuales')),
    ]
}
event_unknown = get_screen('event-detail')
event_unknown.setdefault('states', {})['unknown'] = 'Only a date is known. Do not invent midnight or offer a timed recording from an unknown kickoff.|Solo se conoce fecha. No inventes medianoche ni ofrezcas grabación horaria sin inicio conocido.'
event_unknown['stateBlocks'] = {
    'unknown': [
        facts('World Friendly', [('Date|Fecha', '9 Nov 2026|9 nov 2026'), ('Time|Hora', 'Unknown|Desconocida'), ('Source|Fuente', 'OpenFootball · synthetic fixture|OpenFootball · ejemplo ficticio'), ('Source timezone|Zona de fuente', 'Europe/Madrid')]),
        note('Keep the date-only fixture visible in the agenda. A known time can be reviewed later; date-only does not mean cancelled.|Conserva el evento con fecha en agenda. Se puede revisar hora más adelante; sin hora no significa cancelado.'),
        links(('event-correct', 'Review event information|Revisar información'), ('event-provider', 'Review provider scope|Revisar ámbito del proveedor'), ('events', 'Back to agenda|Volver a agenda')),
    ]
}
for st, label in [('starting', 'Starting · waiting for source|Iniciando · esperando emisión'), ('finalizing', 'Finalizing saved parts|Finalizando partes guardadas'), ('interrupted', 'Interrupted · recovering journal|Interrumpida · recuperando registro')]:
    blocks = deepcopy(get_screen('recording-active')['blocks'])
    fact = next(b for b in blocks if b['type'] == 'facts')
    for row in fact['rows']:
        if row[0][0] == 'State':
            row[1] = pair(label)
        if st == 'starting' and row[0][0] in ['Captured', 'Gap']:
            row[1] = pair('No captured media yet|Todavía sin contenido capturado')
    get_screen('recording-active').setdefault('stateBlocks', {})[st] = blocks

get_screen('dashboard')['stateTitles'] = {'first-use': pair('Welcome to AceStream|Te damos la bienvenida')}
get_screen('event-detail')['stateTitles'] = {'unknown': pair('World Friendly')}
get_screen('event-detail')['stateLabels'] = {'unknown': pair('Time not confirmed|Hora sin confirmar')}
get_screen('event-detail')['states']['unknown'] = 'This event has a date but no confirmed start time. A timed recording needs a confirmed time.|Este evento tiene fecha, pero aún no tiene hora de inicio confirmada. Para programar una grabación hace falta una hora.'
get_screen('access-activate')['states']['blocked'] = 'Open this installation with HTTPS, or use its private address while connected to your home network.|Abre la instalación por HTTPS o usa su dirección privada desde tu red doméstica.'

# Product copy stays plain; detailed adapter/security constraints remain in the spec.
FIELD_COPY = {
    'recording.timezone': 'Use a city timezone such as Europe/Madrid. New recordings start with your browser timezone; it cannot change when editing.|Usa una zona como Europe/Madrid. Las nuevas grabaciones usan la del navegador; no cambia al editar.',
    'recordings.min_free_bytes': 'Default 2 GiB; minimum 64 MiB (0.0625 GiB). Recording stops if free space falls below this limit.|Por defecto 2 GiB; mínimo 64 MiB (0,0625 GiB). La grabación se detiene si el espacio libre baja del límite.',
    'filter.epg_source_id': 'Choose the guide source as well as the channel name to avoid mixing identical names.|Elige la fuente de guía además del nombre para distinguir nombres iguales.',
    'xml.days_back': 'Start up to 14 days before today. Default: yesterday (−1).|Empieza hasta 14 días antes de hoy. Por defecto: ayer (−1).',
    'format.is_default': 'Use this format by default. It replaces the previous default selection.|Usa este formato por defecto. Sustituye la selección anterior.',
    'live.online_only': 'On by default. A recent successful check helps you choose; playback can still fail. Turn off to show all channels.|Activado por defecto. Una comprobación reciente ayuda a elegir; la reproducción aún puede fallar. Desactívalo para ver todos.',
    'cast.volume': '0–100%. Changes apply immediately to the media you are controlling.|0–100 %. Los cambios se aplican al momento al contenido que controlas.',
    'remote.volume': '0–200%, where supported by this player. Changes apply immediately.|0–200 %, si el reproductor lo permite. Los cambios se aplican al momento.',
    'bulk.category': 'This belongs to the linked TV channel. Open its editor to change it.|Pertenece al canal de TV vinculado. Abre su editor para cambiarlo.',
    'guide.filter_source': 'Show the guide source next to each name, including when viewing all sources.|La fuente aparece junto a cada nombre, también al ver todas las fuentes.',
    'dashboard.zone': 'Use a city timezone such as Europe/Madrid. This changes displayed times only.|Usa una zona como Europe/Madrid. Solo cambia las horas mostradas.',
}
for s in SCREENS:
    for b in s['blocks']:
        for f in b.get('fields', []):
            if f['key'] in FIELD_COPY:
                f['implementation_help'] = f['help']
                f['help'] = pair(FIELD_COPY[f['key']])
            if s['id'] == 'recording-active' and f['key'] == 'recording.end_time':
                f['implementation_help'] = f['help']
                f['help'] = pair('Only the end time can change during recording. The start and timezone stay fixed.|Solo se puede cambiar el fin durante la grabación. El inicio y la zona permanecen fijos.')


def product_state(sid, key, copy):
    s = get_screen(sid)
    s.setdefault('implementation_states', {})[key] = pair(s['states'][key])
    s['states'][key] = copy


for sid, key, copy in [
    ('recording-schedule', 'stale', 'The programme changed after you opened it. Compare the saved times with the current guide before scheduling.|El programa cambió desde que lo abriste. Compara los horarios guardados con la guía actual antes de programar.'),
    ('access-login', 'expired', 'Your session expired. Sign in again, then review any unfinished changes before saving.|Tu sesión caducó. Inicia sesión y revisa los cambios pendientes antes de guardarlos.'),
    ('access-login', 'denied', 'Those details did not sign you in. Check the username and password and try again.|No se pudo iniciar sesión. Comprueba el usuario y la contraseña e inténtalo de nuevo.'),
    ('stream-stats', 'unknown', 'There is no measurement yet. Importing a channel does not check whether video or audio is arriving.|Aún no hay medición. Importar un canal no comprueba si llega vídeo o audio.'),
    ('stream-match', 'ambiguous', 'Two TV channels have similar names. Review their details and choose one for this stream.|Dos canales de TV tienen nombres parecidos. Revisa sus datos y elige uno para esta emisión.'),
    ('playlist', 'filtered', 'No channels match these options. Change the filters to include channels in the playlist.|Ningún canal coincide con estas opciones. Cambia los filtros para incluir canales en la lista.'),
    ('source-results', 'partial', 'Some records could not be imported. Existing channels remain available; review the results below.|Algunos registros no se pudieron importar. Los canales existentes siguen disponibles; revisa los resultados.'),
    ('search-add-link', 'unresolved', 'The playable stream could not be identified. Try resolving it again before adding it.|No se pudo identificar la emisión reproducible. Reintenta resolverla antes de añadirla.'),
    ('search-add-link', 'catalogue-unavailable', 'The TV-channel list could not load. Your selected result is retained. Retry before adding and linking it.|No se pudo cargar la lista de TV. Se conserva el resultado elegido. Reintenta antes de añadirlo y vincularlo.'),
    ('helper-large', 'too-large', 'This sample exceeds the 32 MiB limit. Your previous sample and recipe are unchanged. Choose a smaller sample.|La muestra supera 32 MiB. La muestra y receta anteriores siguen intactas. Elige una muestra menor.'),
    ('live', 'refreshing', 'Updating the channel list. Your selected channel keeps playing.|Actualizando la lista. El canal elegido sigue reproduciéndose.'),
    ('live', 'failed', 'This source could not start. Retry or choose another available source.|No se pudo iniciar esta emisión. Reintenta o elige otra disponible.'),
    ('live', 'stalled', 'Video has stopped arriving. Wait a moment, retry or choose another source.|Ha dejado de llegar vídeo. Espera un momento, reintenta o elige otra emisión.'),
    ('player-tracks', 'capacity', 'All playback slots are in use. Keep the current track or retry when a slot is available.|Todas las plazas están ocupadas. Conserva la pista actual o reintenta cuando haya una libre.'),
    ('browser-player', 'unavailable', 'This installation cannot start browser playback with the current configuration. Review the missing service or setting below.|Esta instalación no puede iniciar reproducción con la configuración actual. Revisa el servicio o ajuste que falta.'),
    ('casting', 'denied', 'This connection or account cannot control TVs. Review the access requirements or ask the owner for permission.|Esta conexión o cuenta no puede controlar televisores. Revisa los requisitos o pide permiso al propietario.'),
    ('casting-control', 'ownership-lost', 'The TV is now playing different media. Controls for your previous playback are unavailable.|La TV está reproduciendo otro contenido. Los controles de tu reproducción anterior no están disponibles.'),
    ('casting-control', 'recording-priority', 'Video conversion is waiting while a recording uses the resources. Try the original video if your TV supports it.|La conversión espera mientras una grabación usa los recursos. Prueba el vídeo original si tu TV lo admite.'),
    ('remote-control', 'handoff', 'The player was asked to open. If it did not open, copy the link and open it in your player.|Se pidió abrir el reproductor. Si no se abrió, copia el enlace y ábrelo en tu reproductor.'),
    ('telegram-auth', 'flood', 'Telegram has temporarily limited sign-in attempts. Wait until the retry time shown below.|Telegram ha limitado temporalmente los intentos de acceso. Espera hasta la hora indicada.'),
    ('notifications', 'masked-invalid', 'The saved address cannot be used safely. Enter a replacement address to enable notifications.|La dirección guardada no se puede usar de forma segura. Introduce otra para activar avisos.'),
    ('warp-exclusions', 'partial', 'The host list is saved, but some changes are not active yet. Review the pending hosts and retry applying them.|La lista está guardada, pero faltan cambios por aplicar. Revisa los hosts pendientes y reintenta.'),
    ('offline-cleanup', 'refresh-failed', 'Eligible streams were removed. Some affected sources could not refresh; retry those updates.|Se eliminaron las emisiones aptas. Algunas fuentes afectadas no se actualizaron; reintenta esas actualizaciones.'),
    ('setup', 'partial', 'The channel source was saved, but the guide could not be added. Retry the guide or finish without it.|La fuente se guardó, pero no se añadió la guía. Reintenta la guía o termina sin ella.'),
    ('recovery', 'busy', 'Another recovery is already running. Wait for its result before retrying.|Ya hay una recuperación en curso. Espera su resultado antes de reintentar.'),
    ('recovery', 'interrupted', 'A previous recovery was interrupted. Review the recovery details and retry instructions before continuing.|Se interrumpió una recuperación anterior. Revisa sus detalles e instrucciones antes de continuar.'),
    ('preferences', 'storage-failed', 'Your choice applies in this tab, but could not be saved for your next visit.|Tu elección se aplica en esta pestaña, pero no se pudo guardar para la próxima visita.'),
]:
    product_state(sid, key, copy)
for sid in ['helper-html', 'helper-json', 'helper-regex']:
    product_state(sid, 'invalid', 'This extraction rule is not supported. Your draft is retained. Correct the highlighted field before testing again.|Esta regla no es compatible. Se conserva el borrador. Corrige el campo marcado antes de probar de nuevo.')
for s in SCREENS:
    if s['family'] == 'runtime':
        s['implementation_goal'] = s['goal']
        s['goal'] = pair('Advanced settings for the next container start. Values shown are example repository defaults.|Ajustes avanzados para el próximo inicio del contenedor. Se muestran valores predeterminados de ejemplo.')
        product_state(s['id'], 'conflict', 'Saved settings changed elsewhere. Reload the current saved and active values before trying again.|Los ajustes guardados cambiaron. Recarga los valores guardados y activos antes de reintentar.')
        product_state(s['id'], 'managed', 'This option is unavailable or controlled by the bundled service. Its current value is read-only.|Esta opción no está disponible o la controla el servicio integrado. Su valor actual es de solo lectura.')
for sid, copy in {
    'stream-edit': 'Add a stream and optionally link it to an existing TV channel in the same step.|Añade una emisión y, si quieres, vincúlala a un canal de TV en el mismo paso.',
    'helper-large': 'Use the original text and manual fields when a visual preview is too large.|Usa el texto original y campos manuales si la vista visual es demasiado grande.',
    'event-import': 'Paste event details, load a URL or upload JSON, then review what to import.|Introduce datos, carga una URL o un JSON y revisa qué importar.',
    'tuner': 'Choose what your media server receives and how long it waits for a stream.|Elige qué recibe tu servidor multimedia y cuánto espera una emisión.',
    'diagnostics': 'Download recent logs with sensitive values masked. Original log messages are unchanged.|Descarga registros recientes con datos sensibles ocultos. Los mensajes originales se conservan.',
    'not-found': 'This address does not match a page. Return home or open a known section.|Esta dirección no corresponde a una página. Vuelve al inicio o abre una sección conocida.',
}.items():
    s = get_screen(sid)
    s['implementation_goal'] = s['goal']
    s['goal'] = pair(copy)
get_screen('helper-large').setdefault('stateTitles', {})['too-large'] = pair('Choose a smaller sample|Elige una muestra menor')
get_screen('recording-active')['stateTitles'] = {'starting': pair('Starting recording|Iniciando grabación'), 'finalizing': pair('Finalizing recording|Finalizando grabación'), 'interrupted': pair('Recovering recording|Recuperando grabación')}
# The state-specific copy of this editor retains the same field help.
for blocks in get_screen('recording-active')['stateBlocks'].values():
    for b in blocks:
        if b['type'] == 'form':
            for f in b['fields']:
                f['help'] = pair('The end time can change only while capture is active.|El fin solo se puede cambiar mientras la captura esté activa.')
get_screen('stream-stats')['stateBlocks']['unknown'][1]['text'] = pair('Skipped checks leave the last known measurement unchanged. If a previous measurement exists, its original time stays visible.|Las comprobaciones omitidas conservan la última medición. Si hay una anterior, se mantiene visible su hora original.')
get_field('xml.days_forward')['help'] = pair('Default: 7 days ahead. Choose from 14 days before to 14 days after today; the end cannot precede the start.|Por defecto: 7 días después. Elige entre 14 días antes y 14 después de hoy; el fin no puede preceder al inicio.')
for b in get_screen('guide-export')['blocks']:
    if b['type'] == 'form':
        b['implementation_effect'] = b['effect']
        b['effect'] = pair('A guide file is prepared for the selected channels and dates. Its channel names match the playlist.|Se prepara una guía para los canales y fechas elegidos. Los nombres coinciden con la lista.')

if __name__ == '__main__':
    from simplify_workflows import refine

    refine(SCREENS)
    build()
    from compose_review06 import build as build_review06

    build_review06()
