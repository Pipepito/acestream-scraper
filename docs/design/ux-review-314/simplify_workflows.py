"""Review 06: one semantic workflow catalogue, three presentation presets.
Design fixtures only. Does not import application or supplier runtime code.
"""
from copy import deepcopy
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
NAV=[('dashboard','Watch','Ver'),('recordings','Recordings','Grabaciones'),('events','Events','Eventos'),('channels','Channels','Canales'),('connections','Connections','Conexiones'),('settings','Settings','Ajustes'),('system','System','Sistema')]
def p(s):
 a=s.split('|',1);return a if len(a)==2 else a*2
def links(*items):return dict(type='links',items=[dict(target=a,label=p(b)) for a,b in items])
def rows(title,items):return dict(type='rows',title=p(title),rows=[dict(title=p(a),text=p(b),target=c) for a,b,c in items])
def note(text,tone='info'):return dict(type='note',text=p(text),tone=tone)

def refine(screens):
 by={s['id']:s for s in screens}
 def add(id,title,goal,blocks,source,owner=320):
  s=dict(id=id,family='sources',title=p(title),goal=p(goal),route='/sources',source=[source],owner=owner,permission='administrator',blocks=blocks)
  screens.append(s);by[id]=s
 add('sources','Channel sources|Fuentes de canales','Keep your channels up to date.|Mantén tus canales al día.',[
  links(('add-channels','Add channels|Añadir canales')),
  rows('Your sources|Tus fuentes',[('Family channels','Updated 16:00 · 3 streams · next update tomorrow|Actualizada 16:00 · 3 emisiones · próxima mañana','source-web'),('Local playlist','Saved · import not started|Guardada · importación sin iniciar','w3u-detail')]),
  links(('source-results','Import results|Resultados de importación'),('saved-search','Saved searches|Búsquedas guardadas'),('exclusion','Excluded results|Resultados excluidos'),('sources-orphans','Unlinked streams|Emisiones sin fuente'),('automation','Background updates|Actualizaciones en segundo plano'))], 'frontend/src/pages/Sources.tsx',321)
 # Reuse an observed source path if the page has a different filename in this revision.
 by['sources']['source']=by['source-web']['source']
 add('add-channels','Add channels|Añadir canales','Choose where your channels come from. A programme guide can be added afterwards.|Elige de dónde vienen tus canales. Puedes añadir una guía después.',[
  rows('Choose a source|Elige una fuente',[
   ('Website or playlist address|Dirección de web o lista','Paste a link you already have.|Pega un enlace que ya tengas.','source-web'),
   ('Supported provider|Proveedor compatible','Use the provider’s guided form.|Usa el formulario del proveedor.','source-provider'),
   ('W3U playlist file|Archivo de lista W3U','Review folders before importing channels.|Revisa carpetas antes de importar.','w3u'),
   ('Find a stream|Buscar una emisión','Search, resolve and add it to a TV channel.|Busca, identifica y añade a un canal.','search')]),
  links(('stream-edit','Add one stream manually|Añadir una emisión a mano'),('telegram-auth','Use Telegram as a source|Usar Telegram como fuente'))],by['source-web']['source'][0],321)
 familyHome={'viewing':'dashboard','recordings':'recordings','events':'events','channels':'channels','guides':'channels','sources':'channels','extraction':'channels','playlists':'connections','integrations':'connections','settings':'settings','access':'settings','shell':'settings','system':'system','runtime':'system','setup':'system'}
 overrides={'playback-settings':'connections','telegram-auth':'channels','telegram-code':'channels','telegram-source':'channels','setup-source':'channels','setup-guide':'channels','setup':'channels','network':'system','not-found':'dashboard','changelog':'system','notices':'system'}
 groupDefault={'viewing':'dashboard','recordings':'recordings','events':'events','channels':'channels','guides':'guide-sources','sources':'sources','extraction':'sources','playlists':'playlist','integrations':'connections','settings':'settings','access':'access-account','shell':'settings','system':'system','runtime':'runtime-playback','setup':'system'}
 groupOverrides={'live':'dashboard','playback-settings':'browser-player','telegram-auth':'sources','telegram-code':'sources','telegram-source':'sources','setup-source':'sources','setup-guide':'guide-sources','setup':'sources','streams':'streams','stream-stats':'streams','stream-edit':'streams','stream-bulk':'streams','stream-match':'streams','stream-bulk-fields':'streams','channel-activity':'streams','warp':'warp','warp-exclusions':'warp','warp-startup':'warp','network':'runtime-playback','automation':'automation','schedule-anchors':'automation','offline-cleanup':'automation','preferences':'preferences','add-channels':'sources'}
 mainIds={x[0] for x in NAV}
 for s in screens:
  s['destination']=overrides.get(s['id'],familyHome[s['family']])
  s['section']=groupOverrides.get(s['id'],groupDefault[s['family']])
  s['presentation']='primary destination' if s['id'] in mainIds else 'section' if s['id'] in ['sources','guide-sources','streams','playlist','browser-player','access-account','automation','preferences','warp','runtime-playback'] else 'contextual editor or detail'
  s['designStatus']='composed; proposed; not owner-approved or implemented'
 # Stable aliases use the same canonical composition and editor, not a fork.
 by['setup-source']['canonicalId']='source-web'
 by['setup-guide']['canonicalId']='guide-source'
 by['dashboard']['title']=p('Watch|Ver')
 by['dashboard']['goal']=p('Your channels. Something worth watching.|Tus canales. Algo que apetece ver.')
 by['dashboard']['blocks']=[dict(type='watch-home'),links(('dashboard-events','Upcoming event preferences|Preferencias de próximos eventos'))]
 by['live']['title']=p('Watch|Ver')
 by['live']['goal']=p('Choose a channel and keep browsing while you watch.|Elige un canal y sigue explorando mientras lo ves.')
 by['live']['blocks'].insert(0,dict(type='watch-context'))
 for b in by['live']['blocks']:
  if b['type']=='rows':
   for r in b['rows']:r['target']='live';r['watchChannel']=r['title'][0]
 by['settings']['blocks']=[rows('Make it yours|A tu gusto',[
  ('Accounts and access|Cuentas y acceso','Give people the access they need.|Da a cada persona el acceso que necesita.','access-account'),
  ('Appearance and language|Apariencia e idioma','One app, three ways to see it.|Una aplicación, tres formas de verla.','preferences'),
  ('Background updates|Actualizaciones en segundo plano','When to update sources, guides and signal checks.|Cuándo actualizar fuentes, guías y señal.','automation')]),
  rows('Settings beside their task|Ajustes junto a su tarea',[
  ('Recording settings|Ajustes de grabación','Storage, capacity and retention.|Almacenamiento, capacidad y conservación.','recording-settings'),
  ('Playback and devices|Reproducción y dispositivos','This browser, TVs, players and playlists.|Este navegador, TV, reproductores y listas.','connections'),
  ('Guide matching|Vinculación de guía','Review matches and optional exact automation.|Revisa coincidencias y automatización exacta opcional.','guide-match'),
  ('Advanced setup|Configuración avanzada','Runtime options, network and restart requirements.|Opciones de ejecución, red y reinicios.','runtime-playback')])]
 by['connections']['blocks']=[rows('Where would you like to watch?|¿Dónde quieres ver la TV?',[
  ('This browser|Este navegador','Playback setup and current sessions.|Configuración de reproducción y sesiones.','browser-player'),
  ('TVs and players|TV y reproductores','Send to a TV, or open VLC and Kodi.|Envía a una TV o abre VLC y Kodi.','casting'),
  ('Media servers|Servidores multimedia','Plex, Jellyfin and tuner settings.|Plex, Jellyfin y sintonizador.','media-server'),
  ('Playlists|Listas','Export channels with the right address and format.|Exporta canales con dirección y formato adecuados.','playlist'),
  ('Notifications|Notificaciones','Choose where useful alerts are sent.|Elige dónde recibir avisos útiles.','notifications')]),links(('public-address','Address used by other devices|Dirección para otros dispositivos'))]
 by['casting']['blocks'].insert(0,links(('casting','Send to a TV|Enviar a una TV'),('remote-player','VLC, Kodi and other players|VLC, Kodi y otros reproductores')))
 by['browser-player']['blocks'].insert(0,links(('playback-settings','Playback setup|Configurar reproducción'),('player-sessions','Current sessions|Sesiones actuales')))
 by['channels']['blocks'].insert(0,links(('add-channels','Add channels|Añadir canales')))
 by['guide-sources']['blocks'].append(links(('guide-auto','Automatic exact matches|Coincidencias exactas automáticas')))
 # Preserve current transaction timing; avoid an invented global Save or new confirmation.
 b=next(b for b in by['guide-auto']['blocks'] if b['type']=='form');b['saveTiming']='immediate';b.pop('confirm',None)
 b['effect']=p('Saved for future successful updates. Ambiguous names still need your review.|Guardado para futuras actualizaciones correctas. Los nombres ambiguos requieren revisión.')
 scope=next(b for b in by['automation']['blocks'] if b.get('id')=='scope');scope['saveTiming']='immediate';scope['effect']=p('Check scope saved.|Ámbito de comprobación guardado.')
 by['preferences']['blocks'].insert(0,dict(type='preset-picker'))
 by['recordings']['blocks'].insert(0,dict(type='recording-feature'))
 by['recordings']['blocks'].insert(0,links(('recording-schedule','Schedule recording|Programar grabación'),('recording-settings','Recording settings|Ajustes de grabación')))
 by['events']['blocks'].insert(0,dict(type='event-feature'))
 by['event-detail']['blocks'].insert(0,dict(type='event-artwork'))
 for sid in ['channel-detail','recording-parts']:by[sid]['blocks'].insert(0,dict(type='artwork-peek'))
 # Creation settings remain independent resources; contextual links open canonical editors.
 for sid,items in {
  'source-results':[('setup-guide','Next: add a programme guide|Siguiente: añadir una guía'),('channels','Review imported channels|Revisar canales importados')],
  'guide-source':[('guide-match','Next: review guide matches|Siguiente: revisar coincidencias')],
  'guide-match':[('dashboard','Start watching|Empezar a ver')],
  'system':[('runtime-playback','Advanced setup|Configuración avanzada'),('recovery','Catalogue recovery|Recuperar catálogo'),('changelog','What changed|Qué cambió')],
  'playlist':[('public-address','Address and credentials|Dirección y credenciales'),('formats','Shared stream formats|Formatos de emisión compartidos')]
 }.items():by[sid]['blocks'].append(links(*items))
 # Each materially different image failure has a bounded, explicit next step.
 for sid in ['dashboard','live','event-detail','recording-parts','channel-detail']:
  s=by[sid]
  for key,copy in {
   'art-absent':'No artwork is available. Names and actions are ready.|No hay imagen disponible. Los nombres y acciones siguen listos.',
   'art-slow':'Artwork is taking longer. Continue without it.|La imagen tarda. Puedes continuar sin ella.',
   'art-blocked':'Artwork could not be loaded from this address. Use the text details.|No se pudo cargar la imagen de esta dirección. Consulta los datos.',
   'art-rejected':'This image type is not supported. Use the text details.|El tipo de imagen no es compatible. Consulta los datos.',
   'art-oversized':'The image exceeds the safe size limit. It has not been opened.|La imagen supera el límite seguro. No se ha abierto.',
   'art-decode-failed':'This image could not be displayed. Try loading it again.|No se pudo mostrar la imagen. Prueba a cargarla de nuevo.',
   'art-changed':'The artwork changed. Load the new image when you are ready.|La imagen cambió. Carga la nueva cuando quieras.'
  }.items():s.setdefault('states',{})[key]=copy
 for s in screens:
  for b in s['blocks']:
   for f in b.get('fields',[]):
    if f['key']=='source.scrape_bare_ids':f['default']=False
 # Keep developer constraints in the handoff, and make the common source action direct.
 for b in by['access-account']['blocks']:
  if b['type']=='note' and 'invented' in b['text'][0]:
   b['implementation_text']=b['text'];b['text']=p('Casting to your devices and controlling server devices have separate permissions. Remote control also needs to be enabled.|Enviar a tus dispositivos y controlar los del servidor tienen permisos distintos. El control remoto también debe estar activado.')
 for sid in ['source-web','source-auto','source-zeronet','source-ipfs','source-provider']:
  for b in by[sid]['blocks']:
   if b['type']=='note' and 'DNS' in b['text'][0]:b['implementation_text']=b['text'];b['text']=p('Paste a website or playlist address. Save it for later, or find its channels now.|Pega una dirección web o de lista. Guárdala para más tarde o busca sus canales ahora.')
   if b['type']=='form':
    for f in b['fields']:
     if f['key']=='source.url':f['implementation_help']=f['help'];f['help']=p('Paste the complete address. Save only keeps it for later; finding channels starts an import.|Pega la dirección completa. Solo guardar la conserva para más tarde; buscar canales inicia una importación.')
     if f['key']=='source.url_type':f['implementation_help']=f['help'];f['help']=p('Use the normal website option unless your provider asks for a specific type.|Usa la opción web normal salvo que tu proveedor indique otro tipo.')
   if b['type']=='command' and b['label'][0]=='Save and find channels':
    sourceform=next(x for x in by[sid]['blocks'] if x['type']=='form')
    b['requiresForm']=sourceform['id'];b['inlineInForm']=True;b['primary']=True;sourceform['secondaryAction']=True
    sourceform['effect']=p('Save only keeps the source. Save and find channels saves it, then queues an import separately.|Solo guardar conserva la fuente. Guardar y buscar canales la guarda y después pone una importación en cola por separado.')
 for sid,copy in {
  'recovery-readable':'Back up the catalogue first. Restore the source and settings data that can still be read. Damaged entries may be skipped; channel listings and activity must be rebuilt. Accounts stay unchanged.|Haz una copia del catálogo primero. Recupera las fuentes y ajustes que aún se puedan leer. Se pueden omitir datos dañados; los canales y la actividad deberán reconstruirse. Las cuentas se conservan.',
  'recovery-fresh':'Back up the catalogue first. Replace its data and set up your sources and catalogue settings again. Accounts, access restrictions and passwords stay unchanged.|Haz una copia del catálogo primero. Sustituye sus datos y vuelve a configurar las fuentes y los ajustes del catálogo. Las cuentas, restricciones de acceso y contraseñas se conservan.'
 }.items():
  for b in by[sid]['blocks']:
   if b['type']=='note':b['implementation_text']=b['text'];b['text']=p(copy)
   if b['type']=='form':
    b['implementation_effect']=b['effect'];b['effect']=p(copy);b['confirm']=p(copy)
    for f in b['fields']:
     f['implementation_help']=f['help'];f['help']=p('Required. Check the consequence above before continuing. If recovery fails, review the result before trying again.|Obligatorio. Revisa las consecuencias antes de continuar. Si la recuperación falla, revisa el resultado antes de reintentar.')
 # Destination/section map is the source of both navigation and documentation.
 mapping=[]
 for s in screens:
  forms=[b for b in s['blocks'] if b['type']=='form']
  canonical=by.get(s.get('canonicalId'),s)
  item=dict(id=s['id'],current=s['route'],destination=s['destination'],section=s['section'],presentation='reuse canonical editor' if s.get('canonicalId') else s['presentation'],canonical=canonical['id'],save=[dict(editor=b['id'],timing=b.get('saveTiming','explicit action'),api=b['api']) for b in canonical['blocks'] if b['type']=='form'],source=s['source'],owner=s['owner'])
  s['location']=item;mapping.append(item)
 (ROOT/'navigation-map.json').write_text(json.dumps(dict(navigation=[dict(id=a,label=[b,c]) for a,b,c in NAV],workflows=mapping),ensure_ascii=False,indent=2)+'\n')
