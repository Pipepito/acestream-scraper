/* Disposable synthetic interaction model. No fetch, application imports, storage or media. */
'use strict';
(() => {
const screens = window.WORKFLOWS.screens;
const q = new URLSearchParams(location.search);
let current = screens.find(s => s.id === q.get('screen')) || screens[0];
let language = q.get('lang') === 'es' ? 'es' : 'en';
let state = q.get('state') || 'ready';
let theme = q.get('theme') === 'dark' ? 'dark' : 'light';
let palette = q.get('palette') === 'lime' ? 'lime' : 'coral';
let direction = q.get('direction') === 'broadcast' ? 'broadcast' : 'calm';
let context = q.get('context') === 'standalone' || current.id === 'helper-standalone' ? 'standalone' : 'installed';
const drafts = new Map(), baseline = new Map(), selected = new Map(), results = new Map(), orders = new Map();
const pendingForms = new Set();
let nextDialog = null, lastFocus = null;
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = v => Array.isArray(v) ? (v[language === 'es' ? 1 : 0] ?? v[0]) : String(v ?? '');
const tr = (en,es) => language === 'es' ? es : en;
const uid = key => key.replace(/[^a-z0-9_-]/gi, '-');
const formKey = b => current.id + ':' + b.id;
function value(f) { return drafts.has(f.key) ? drafts.get(f.key) : f.value; }
function initialize() {
 current.blocks.forEach(b => (b.fields || []).forEach(f => {
  if (!drafts.has(f.key)) { drafts.set(f.key, f.value); baseline.set(f.key, f.value); }
 }));
 if (!orders.has(current.id)) {
  const block = current.blocks.find(b => b.type === 'reorder');
  if (block) orders.set(current.id, [...block.names]);
 }
}
function dirty(b) { return b.fields?.some(f => String(value(f)) !== String(baseline.get(f.key))); }
function hasDirty() { return current.blocks.some(b=>dirty(b)&&(!b.local||b.guardDraft)) || current.blocks.some(b => b.type === 'reorder' && JSON.stringify(orders.get(current.id)) !== JSON.stringify(b.names)); }
function selectionCount(){return Array.from(selected.entries()).filter(([key])=>key.startsWith(current.id+':')).reduce((n,[,items])=>n+items.length,0);}
function rangeUnit(f,spoken=false){const singular=Math.abs(Number(value(f)))===1;return f.key.startsWith('xml.')?tr(spoken?(singular?'day from today':'days from today'):(singular?'day':'days'),spoken?(singular?'día desde hoy':'días desde hoy'):(singular?'día':'días')):tr(spoken?'percent':'%',spoken?'por ciento':'%');}
function active(f) {
 if (f.disabled || f.readonly) return false;
 if (f.depends && !(f.equals !== undefined ? String(drafts.get(f.depends)) === String(f.equals) : drafts.get(f.depends))) return false;
 if (f.unless && drafts.get(f.unless)) return false;
 return true;
}
function url(id, extra={}) {
 const p = new URLSearchParams({screen:id,lang:language,theme,palette,direction,...extra});
 if (context==='standalone') p.set('context',context);
 if (q.get('presentation')==='1') p.set('presentation','1');
 return 'workflow-prototype.html?' + p;
}
function link(id,label,cls='') { return `<a class="${cls}" href="${esc(url(id))}" data-screen="${esc(id)}">${esc(t(label))}</a>`; }
function announce(text) { $('#announce').textContent=t(text); }
function button(label,action,extra='',cls='') { return `<button type="button" class="button ${cls}" data-action="${action}" ${extra}>${esc(t(label))}</button>`; }
function navigation(drawer=false) {
 const nav=[['Watch|Ver',[['dashboard','Home|Inicio'],['live','Live TV|TV en directo'],['events','Events|Eventos'],['recordings','Recordings|Grabaciones']]],['Manage|Gestionar',[['channels','TV channels|Canales de TV'],['streams','Streams|Emisiones'],['guide-sources','Programme guides|Guías'],['source-web','Sources|Fuentes'],['search','Search|Buscar'],['playlist','Playlists|Listas']]],['Integrations|Integraciones',[['connections','Connections|Conexiones'],['casting','TV casting|Enviar a TV'],['remote-player','Remote players|Reproductores remotos'],['media-server','Media servers|Servidores multimedia'],['warp','WARP']]],['System|Sistema',[['settings','Settings|Ajustes'],['system','System status|Estado del sistema'],['setup','Setup|Configuración inicial'],['changelog','What changed|Qué cambió']]]];
 return `<aside class="sidebar"><a class="brand" data-screen="dashboard" href="${url('dashboard')}">AceStream<br>Scraper</a><nav aria-label="${tr('Main navigation','Navegación principal')}">${nav.map(([g,items])=>`<div class="navgroup"><p>${esc(t(g.split('|')))}</p>${items.map(([id,l])=>`<a href="${url(id)}" data-screen="${id}" ${current.id===id?'aria-current="page"':''}>${esc(t(l.split('|')))}</a>`).join('')}</div>`).join('')}</nav><div class="navfoot">${tr('Synthetic review workspace','Espacio de revisión ficticio')}<br>${link('preferences',['Language and appearance','Idioma y apariencia'])}</div></aside>`;
}
function renderField(f) {
 const id='f-'+uid(f.key), v=value(f), help=id+'-help', error=id+'-error';
 const common=`id="${id}" name="${esc(f.key)}" data-field="${esc(f.key)}" aria-describedby="${help} ${error}" ${active(f)?'':'disabled'} ${f.readonly?'readonly':''} ${f.required?'required':''}`;
 const attrs=['min','max','step','maxlength','minlength','pattern'].filter(k=>f[k]!==undefined&&!(f.kind==='password'&&['maxlength','minlength'].includes(k))).map(k=>`${k}="${esc(f[k])}"`).join(' ');
 const required=f.required?tr(' (required)',' (obligatorio)'):'';
 let control;
 if(f.kind==='checkbox') control=`<label class="check" for="${id}"><input type="checkbox" ${common} ${v?'checked':''}><span>${esc(t(f.label)+required)}</span></label>`;
 else {
  let input;
  if(f.kind==='select') input=`<select ${common}>${(f.options||[]).map(o=>{const [a,en,es]=o.split('|');return `<option value="${esc(a)}" ${String(v)===a?'selected':''}>${esc(language==='es'?(es||en):en)}</option>`}).join('')}</select>`;
  else if(f.kind==='textarea') input=`<textarea ${common} ${attrs}>${esc(v)}</textarea>`;
  else if(f.kind==='file') input=`<input type="file" class="visually-hidden-file" tabindex="-1" ${common} accept=".txt,.html,.json,.m3u,.w3u">${button(['Choose local file','Elegir archivo local'],'choose-file',`data-file-id="${id}"`)}<p id="${id}-name" role="status">${v?esc(String(v).split(/[\\/]/).pop()):tr('No file chosen','Ningún archivo elegido')}</p>`;
  else input=`<input type="${esc(f.kind)}" ${common} ${attrs} value="${esc(v)}" ${f.kind==='password'?'autocomplete="off"':''}>`;
  control=`<label for="${id}">${esc(t(f.label)+required)}</label>${input}${f.kind==='range'?`<output for="${id}">${esc(v)} ${rangeUnit(f)}</output>`:''}`;
 }
 return `<div class="field ${f.kind==='textarea'?'wide':''}">${control}<p id="${help}">${esc(t(f.help))}</p><p class="field-error" id="${error}" aria-live="polite"></p></div>`;
}
function renderForm(b,index) {
 const fs=b.fields.filter(f=>!f.advanced), adv=b.fields.filter(f=>f.advanced);
 return `<section class="workflow-block"><h2 id="title-${b.id}">${esc(t(b.title))}</h2><form class="workflow-form" id="form-${b.id}" data-block="${index}" data-save-timing="${b.saveTiming||'explicit'}" aria-labelledby="title-${b.id}" novalidate><div class="fields">${fs.map(renderField).join('')}</div>${adv.length?`<details><summary>${tr('Advanced options','Opciones avanzadas')} · ${adv.length}</summary><div class="fields">${adv.map(renderField).join('')}</div></details>`:''}<div class="savebar"><span class="form-effect"><strong>${tr('After this action:','Después de esta acción:')}</strong> ${esc(t(b.effect))}</span><div><button type="button" class="button" data-action="reset" data-block="${index}">${tr('Cancel changes','Cancelar cambios')}</button><button type="submit" class="button ${b.danger?'danger':'primary'}">${esc(t(b.action))}</button></div></div><div class="workflow-status" role="status">${esc(t(results.get(formKey(b))||''))}</div></form></section>`;
}
function block(b,index) {
 const title=b.title?`<h2>${esc(t(b.title))}</h2>`:'';
 if(b.installedOnly && context==='standalone')return '';
 if(b.type==='form')return renderForm(b,index);
 if(b.type==='note')return `<div class="workflow-block"><div class="notice ${esc(b.tone)}"><span aria-hidden="true">i</span><p>${esc(t(b.text))}</p></div></div>`;
 if(b.type==='links')return `<div class="workflow-links">${b.items.filter(i=>!(context==='standalone' && ['helper-installed','source-web'].includes(i.target))).map(i=>link(i.target,i.label)).join('')}</div>`;
 if(b.type==='facts')return `<section class="workflow-block">${title}<dl class="workflow-facts">${b.rows.map(([k,v])=>`<div><dt>${esc(t(k))}</dt><dd>${esc(t(v))}</dd></div>`).join('')}</dl></section>`;
 if(b.type==='rows')return `<section class="workflow-block">${title}<ul class="workflow-rows">${b.rows.map(r=>`<li><strong>${r.target?link(r.target,r.title):esc(t(r.title))}</strong><p>${esc(t(r.text))}</p>${r.target?`<span aria-hidden="true">↗</span>`:''}</li>`).join('')}</ul></section>`;
 if(b.type==='code')return `<section class="workflow-block">${title}<pre class="workflow-code" tabindex="0">${esc(b.text)}</pre></section>`;
 if(b.type==='copy')return `<section class="workflow-block">${button(b.label,'copy',`data-block="${index}"`)}<div class="workflow-status" role="status" data-result="${index}"></div></section>`;
 if(b.type==='command')return `<section class="workflow-block"><p>${esc(t(b.consequence))}</p>${button(b.label,'command',`data-block="${index}" ${b.selection&&!selectionCount()?'disabled':''}`,b.danger?'danger':'')}<div class="workflow-status" role="status" data-result="${index}">${esc(t(results.get(current.id+':command:'+index)||''))}</div></section>`;
 if(b.type==='choices') {
  const picked=selected.get(current.id+':'+index)||[];
  return `<section class="workflow-block"><fieldset><legend>${esc(t(b.title))}</legend>${b.items.map(item=>`<label class="choice-row" ${item.requires?`data-requires="${esc(item.requires)}"`:""}><input type="${b.single?'radio':'checkbox'}" name="choice-${index}" value="${esc(item.id)}" data-choice="${index}" ${picked.includes(item.id)?'checked':''}><span><strong>${esc(t(item.title))}</strong><small>${esc(t(item.text))}</small></span></label>`).join('')}</fieldset><p class="selection-status" data-selection="${index}">${picked.length} ${tr('selected · nothing is selected automatically','seleccionadas · ninguna se selecciona automáticamente')}</p>${button(b.action,'apply-choice',`data-block="${index}" ${!picked.length?'disabled':''}`,b.danger?'danger':'primary')}<div class="workflow-status" role="status" data-result="${index}"></div></section>`;
 }
 if(b.type==='player')return `<section class="workflow-block"><div class="workflow-player" id="synthetic-player" data-session="fixture-viewer-1"><span class="play-glyph" aria-hidden="true">▷</span><h2>${esc(t(b.title))}</h2><p>${esc(t(['failed','stalled','preparing','unsupported'].includes(state)?(current.states?.[state]||b.status):b.status))}</p>${link('player-tracks',['Audio and subtitles','Audio y subtítulos'])}</div></section>`;
 if(b.type==='feature')return `<section class="workflow-feature"><p class="eyebrow">${tr('NOW ON YOUR GUIDE','AHORA EN TU GUÍA')}</p><h2>${esc(t(b.title))}</h2><p>${esc(t(b.text))}</p>${link(b.target,['Open Live TV','Abrir TV en directo'],'button primary')}</section>`;
 if(b.type==='steps')return `<ol class="steps">${b.items.map((v,i)=>`<li ${!i?'aria-current="step"':''}>${esc(t(v))}</li>`).join('')}</ol>`;
 if(b.type==='sample')return `<section class="workflow-block"><h2>${tr('Safe sample workspace','Área de muestra segura')}</h2><p>${tr('Synthetic local sample. Scripts, media and remote resources never run here.','Muestra local ficticia. Aquí no se ejecutan scripts, contenido ni recursos remotos.')}</p><div class="sample-row"><strong>Northlight HD</strong><code>000000…0000</code><span>Documentary</span></div><details><summary>${tr('View original sample','Ver muestra original')}</summary><pre class="workflow-code" tabindex="0">${esc(b.text)}</pre></details></section>`;
 if(b.type==='reorder')return `<section class="workflow-block"><h2>${tr('Complete inventory · 3 items','Inventario completo · 3 elementos')}</h2><p>${tr('Drag a handle or use the Up and Down buttons. Numbers preview the proposed order.','Arrastra un asa o usa Subir y Bajar. Los números muestran el orden propuesto.')}</p><ol class="order-list">${orders.get(current.id).map((name,i)=>`<li class="order-row" data-position="${i}"><span class="order-position">${i+1}</span><strong>${esc(name)}</strong><div class="order-actions">${button(['Drag '+name,'Arrastrar '+name],'drag',`draggable="true" data-position="${i}" aria-label="${esc(tr('Drag ','Arrastrar ')+name)}"`)}${button(['Up','Subir'],'up',`data-position="${i}" ${i===0?'disabled':''} aria-label="${esc(tr('Move ','Mover ')+name+tr(' up',' arriba'))}"`)}${button(['Down','Bajar'],'down',`data-position="${i}" ${i===2?'disabled':''} aria-label="${esc(tr('Move ','Mover ')+name+tr(' down',' abajo'))}"`)}</div></li>`).join('')}</ol><p>${esc(t(b.effect))}</p><div class="actions">${button(['Cancel order','Cancelar orden'],'reset-order')}${button(['Save complete order','Guardar orden completo'],'save-order','','primary')}</div><div class="workflow-status" role="status" id="order-result"></div></section>`;
 return '';
}
const stateText={
 loading:['Loading this view. Existing playback continues; no new action is submitted.','Cargando vista. La reproducción existente continúa; no se envía ninguna acción.'],
 empty:['No items yet. Use the named creation or setup link below; nothing is imported automatically.','Todavía no hay elementos. Usa el enlace de creación o configuración; no se importa automáticamente.'],
 filtered:['No items match these filters. Clear filters to return to the complete inventory.','No hay coincidencias con estos filtros. Límpialos para volver al inventario completo.'],
 error:['This request failed. Your last saved values and draft are retained. Retry this transaction only.','La solicitud falló. Se conservan valores guardados y borrador. Reintenta solo esta operación.'],
 permission:['Your account cannot perform this action. Ask the server owner for the required permission; only the owner can change your access.','Tu cuenta no permite esta acción. Pide el permiso al propietario; solo el propietario puede cambiar tu acceso.'],
 dirty:['Unsaved changes in this section. Saving another section will not save this draft.','Cambios sin guardar en esta sección. Guardar otra sección no guarda este borrador.'],
 pending:['Request pending. Duplicate submission is blocked; wait for the result of this transaction.','Solicitud pendiente. Se bloquea duplicación; espera el resultado de esta operación.'],
 success:['Synthetic request accepted. Check the operation-specific result below; acceptance is not proof that background work finished.','Solicitud ficticia aceptada. Revisa el resultado específico; aceptar no prueba que terminó el trabajo.'],
 conflict:['The saved revision changed. Refresh and review before applying again. No automatic overwrite.','Cambió la revisión guardada. Actualiza y revisa antes de aplicar. Sin sobrescritura automática.'],
 partial:['Some items need attention. Successful results are available below; review the remaining items.','Algunos elementos requieren atención. Los resultados correctos están disponibles; revisa los restantes.']
};
function stateOptions() { return ['ready',...new Set([...(current.baseStates||['loading','error','permission']),...Object.keys(current.states||{})])]; }
function renderState() {
 if(state==='ready')return '';
 const msg=current.states?.[state] || stateText[state] || [state,state];
 return `<section class="workflow-state ${['error','failed','conflict','denied'].includes(state)?'error':state==='success'?'success':''}" role="status"><h2>${esc(t(current.stateLabels?.[state]||(window.WORKFLOWS.stateLabels||{})[state]||[state,state]))}</h2><p>${esc(t(typeof msg==='string'?msg.split('|'):msg))}</p>${['loading','pending'].includes(state)?'':button(current.id==='live'&&['failed','stalled'].includes(state)?['Retry playback','Reintentar reproducción']:['Review current view','Revisar vista actual'],'clear-state')}</section>`;
}
function toolbar() {
 const select=(id,label,opts,val)=>`<label for="${id}">${esc(t(label))}<select id="${id}">${opts.map(([v,l])=>`<option value="${esc(v)}" ${v===val?'selected':''}>${esc(t(l))}</option>`).join('')}</select></label>`;
 return `<div class="study-tools" role="region" aria-label="${tr('Review controls','Controles de revisión')}">${select('screen-select',['Composed workflow','Flujo compuesto'],screens.map(s=>[s.id,s.title]),current.id)}${select('state-select',['Example state','Estado de ejemplo'],stateOptions().map(k=>[k,current.stateLabels?.[k]||window.WORKFLOWS.stateLabels[k]||[k,k]]),state)}${select('lang-select',['Language','Idioma'],[['en',['English','English']],['es',['Español','Español']]],language)}${select('theme-select',['Theme','Tema'],[['light',['Light','Claro']],['dark',['Dark','Oscuro']]],theme)}${select('palette-select',['Palette proposal','Propuesta de color'],[['coral',['Coral','Coral']],['lime',['Lime','Lima']]],palette)}${select('direction-select',['Direction proposal','Propuesta de dirección'],[['calm',['Calm','Calma']],['broadcast',['Expressive','Expresiva']]],direction)}</div>`;
}
function render(keepFocus=false) {
 initialize();
 const focused=keepFocus?document.activeElement?.id:null, scroll=scrollY;
 const openDetails=keepFocus?$$('details[open]').map(e=>e.closest('form')?.id||''):[];
 const player=keepFocus?$('#synthetic-player'):null;
 const pickedFiles=keepFocus?$$('input[type=file]').filter(e=>e.files?.length):[];
 document.documentElement.lang=language;
 $('.skip').textContent=tr('Skip to content','Ir al contenido');
 $('#drawer').setAttribute('aria-label',tr('Navigation','Navegación'));
 const screenTitle=t(current.stateTitles?.[state]||current.title);
 document.title=screenTitle+' · AceStream design study';
 document.body.className=[theme,palette,direction,q.get('presentation')==='1'?'presentation':''].join(' ');
 $('#app').innerHTML=`<div class="study-label" role="region" aria-label="${tr('Design proposal notice','Aviso de propuesta de diseño')}">${tr('DESIGN PROPOSAL · synthetic data · no connection to an installation · not approved or implemented','PROPUESTA DE DISEÑO · datos ficticios · sin conexión a una instalación · sin aprobar ni implementar')}<a href="workflow-gallery.html">${tr('All workflows','Todos los flujos')}</a></div>${toolbar()}<header class="phone-header"><strong>${context==='standalone'?tr('AceStream · Recipe helper','AceStream · Recetas'):'AceStream Scraper'}</strong>${context==='standalone'?'':button(['Menu','Menú'],'menu','aria-haspopup="dialog" id="menu-open"')}</header><div class="study-layout">${context==='standalone'?'':navigation()}<main id="main" tabindex="-1"><header class="workflow-head"><p class="eyebrow">${esc(t(window.WORKFLOWS.families[current.family]||[current.family,current.family]))}</p><h1>${esc(screenTitle)}</h1><p>${esc(t(current.goal))}</p></header>${renderState()}<div id="workflow-content">${(current.stateBlocks?.[state]||current.blocks).map(block).join('')}</div><details class="handoff"><summary>${tr('Design handoff and evidence','Especificación y evidencia')}</summary><p>${tr('Current route','Ruta actual')}: <code>${esc(current.route)}</code><br>${tr('Permission contract','Contrato de permisos')}: ${esc(current.permission)}</p><p>${tr('Implementation owner','Responsable de implementación')}: <a href="https://github.com/Pipepito/acestream-scraper/issues/${current.owner}">#${current.owner}</a></p><p><a href="https://github.com/Pipepito/acestream-scraper/blob/bdc88af0aeacae55e395e138d30d7b1f328bf765/docs/design/ux-review-314/workflow-specification.md#${current.id}">${tr('Fields, states and acceptance','Campos, estados y aceptación')}</a> · <a href="https://github.com/Pipepito/acestream-scraper/blob/bdc88af0aeacae55e395e138d30d7b1f328bf765/docs/design/ux-review-314/traceability-matrix.md#${current.id}">${tr('Source and verification','Fuente y verificación')}</a></p></details></main></div>`;
 if(context==='standalone')$('.study-layout').style.gridTemplateColumns='1fr';
 if(player && $('#synthetic-player')) { const fresh=$('#synthetic-player'); player.querySelector('p').textContent=fresh.querySelector('p').textContent; player.querySelector('a').textContent=fresh.querySelector('a').textContent; fresh.replaceWith(player); }
 pickedFiles.forEach(input=>document.getElementById(input.id)?.replaceWith(input));
 openDetails.forEach(id=>{if(id)$('#'+id+' details')?.setAttribute('open','');});
 wire(); updateForms(false); updateStateLocks();applyViewFilters();
 if(focused)document.getElementById(focused)?.focus({preventScroll:true});
 if(keepFocus)scrollTo(0,scroll);
}
function updateStateLocks() {
 if(['permission','pending','loading','conflict','expired','stale','last-admin','blocked','denied','held','ownership-lost'].includes(state)||(current.id==='recording-active'&&['finalizing','interrupted'].includes(state))) $$('#workflow-content button:not([data-action=copy]),#workflow-content input,#workflow-content select,#workflow-content textarea').forEach(e=>e.disabled=true);
 if(['empty','filtered'].includes(state))$$('.workflow-rows li,.choice-row,.workflow-facts').forEach(e=>e.hidden=true);
}
function getError(f,el) {
 if(!active(f))return '';
 const v=value(f);
 if(f.required && (f.kind==='checkbox'?!v:!String(v).trim()))return tr('Complete this required field.','Completa este campo obligatorio.');
 if(f.kind==='number' && v!=='' && (Number.isNaN(Number(v))||(f.min!==undefined && +v<f.min)||(f.max!==undefined && +v>f.max)))return tr(`Use a value${f.min!==undefined?' ≥ '+f.min:''}${f.max!==undefined?' ≤ '+f.max:''}.`,`Usa un valor${f.min!==undefined?' ≥ '+f.min:''}${f.max!==undefined?' ≤ '+f.max:''}.`);
 if(f.kind==='url' && v && !/^https?:\/\/[^\s/]+/i.test(v))return tr('Enter a complete HTTP or HTTPS address.','Introduce una dirección HTTP o HTTPS completa.');
 if(f.key==='account.password' && v && ([...String(v)].length<12 || [...String(v)].length>128))return tr('Use 12–128 characters.','Usa 12–128 caracteres.');
 if(f.key.endsWith('password_confirmation') && v!==drafts.get('account.password'))return tr('Passwords must match.','Las contraseñas deben coincidir.');
 if(f.key==='recording.end_choice' && v && drafts.get('recording.start_choice') && v<=drafts.get('recording.start_choice'))return tr('Choose an end after the selected start instant.','Elige un fin posterior al instante de inicio.');
 if(f.key==='recording.end_time' && drafts.get('recording.start_time') && (new Date(v)-new Date(drafts.get('recording.start_time'))<=0 || new Date(v)-new Date(drafts.get('recording.start_time'))>720*60000))return tr('End must be after start and within 720 minutes.','Fin posterior al inicio y dentro de 720 minutos.');
 if(f.key==='recording.start_time' && String(v).startsWith('2026-03-29T02:') && drafts.get('recording.timezone')==='Europe/Madrid')return tr('This local time does not exist. Choose a valid time.','Esta hora local no existe. Elige una hora válida.');
 if(f.key==='xml.days_forward' && +v < +drafts.get('xml.days_back'))return tr('End cannot precede start.','El fin no puede preceder al inicio.');
 if(f.pattern && v && !(new RegExp(f.pattern)).test(v))return tr('Use the format described for this field.','Usa el formato indicado para este campo.');
 if(f.minlength && v && [...String(v)].length<f.minlength)return tr(`Use at least ${f.minlength} characters.`,`Usa al menos ${f.minlength} caracteres.`);
 if(f.maxlength && [...String(v)].length>f.maxlength)return tr(`Use at most ${f.maxlength} characters.`,`Usa como máximo ${f.maxlength} caracteres.`);
 return '';
}
function updateForms(showErrors) {
 current.blocks.forEach(b=>{
  if(b.type!=='form')return;
  const form=$('#form-'+b.id); if(!form)return;
  let invalid=false;
  b.fields.forEach(f=>{
   const el=document.getElementById('f-'+uid(f.key));if(!el)return;
   el.disabled=!active(f);
   const error=getError(f,el);invalid ||= !!error;
   const output=document.getElementById(el.id+'-error');
   if(showErrors || el.getAttribute('aria-invalid')==='true') {output.textContent=error;el.setAttribute('aria-invalid',String(!!error));}
   if(f.kind==='range'){el.setAttribute('aria-valuetext',value(f)+' '+rangeUnit(f,true));el.parentElement.querySelector('output').textContent=value(f)+' '+rangeUnit(f);}
  });
  const selCount=selectionCount();
  const busy=pendingForms.has(formKey(b));
  form.querySelector('[type=submit]').disabled=busy||invalid||!(b.local||b.intent||dirty(b))||(b.selection&&!selCount);
  form.querySelector('[data-action=reset]').disabled=!dirty(b)||busy;
  if(busy)form.querySelectorAll('input,select,textarea').forEach(e=>e.disabled=true);
 });
 $$('[data-requires]').forEach(el=>{el.hidden=!drafts.get(el.dataset.requires);el.querySelector('input').disabled=el.hidden;});
 $$('[data-action=command]').forEach(el=>{const b=current.blocks[el.dataset.block];if(b.selection)el.disabled=!selectionCount();});
 updateStateLocks();
}
function confirm(title,body,onConfirm,action=null) {
 lastFocus=document.activeElement;nextDialog=onConfirm;
 $('#confirm-title').textContent=t(title);$('#confirm-body').textContent=t(body);
 $('#confirm-cancel').textContent=tr('Cancel','Cancelar');$('#confirm-commit').textContent=t(action||[ 'Continue','Continuar']);
 $('#confirm').showModal();$('#confirm-cancel').focus();
}
function closeConfirm() {$('#confirm').close();if(lastFocus?.isConnected)lastFocus.focus();}
function navigate(id) {
 const target=screens.find(s=>s.id===id);if(!target)return;
 const perform=()=>{drafts.clear();baseline.clear();selected.clear();results.clear();current=target;state='ready';if(id==='helper-standalone')context='standalone';if(id==='helper-installed')context='installed';history.pushState({},'',url(id));render();$('#main').focus();scrollTo(0,0);};
 if(hasDirty()) confirm(['Leave with unsaved changes?','¿Salir sin guardar?'],['Only the current unsaved draft will be discarded. Saved sections stay saved.','Solo se descartará el borrador actual. Las secciones guardadas se conservan.'],perform,['Discard and leave','Descartar y salir']);else perform();
}
function applyViewFilters(){
 const key=current.id==='live'?'live.q':current.id==='recordings'?'recording.search':current.id==='channels'||current.id==='streams'?'filter.search':current.id==='events'?'agenda.search':null;
 if(!key)return;const query=String(drafts.get(key)||'').trim().toLocaleLowerCase(language);
 const rows=$$('.workflow-rows li');rows.forEach(row=>row.hidden=['empty','filtered'].includes(state)||(!!query&&!row.textContent.toLocaleLowerCase(language).includes(query)));
 let empty=$('#local-filter-empty');if(!empty){empty=document.createElement('p');empty.id='local-filter-empty';empty.setAttribute('role','status');$('.workflow-rows')?.after(empty);}
 empty.textContent=rows.length&&rows.every(r=>r.hidden)?tr('No matching items. Clear the search to show all. Current playback continues.','Sin coincidencias. Borra la búsqueda para mostrar todo. La reproducción continúa.'):'';
}
function finishForm(b) {
 const operationKey=formKey(b),operationScreen=current.id;
 pendingForms.add(operationKey);updateForms(false);
 const status=$('#form-'+b.id+' .workflow-status');status.textContent=tr('Request pending…','Solicitud pendiente…');
 setTimeout(()=>{
  pendingForms.delete(operationKey);
  if(current.id!==operationScreen)return;
  b.fields.forEach(f=>baseline.set(f.key,value(f)));
  results.set(operationKey,b.effect);status.textContent=t(b.effect);updateForms(false);announce(b.effect);
  if(b.next)navigate(b.next);
 },180);
}
function orderMove(from,to) {
 const list=orders.get(current.id);if(to<0||to>=list.length)return;
 const [item]=list.splice(from,1);list.splice(to,0,item);render(true);
 $(`.order-row[data-position="${to}"] [data-action=drag]`).focus();announce([item+' moved to '+(to+1),item+' movido a '+(to+1)]);
}
function wire() {
 $$('[data-screen]').forEach(a=>a.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey)return;e.preventDefault();if($('#drawer').open)$('#drawer').close();navigate(a.dataset.screen);}));
 $('#screen-select').addEventListener('change',e=>{const id=e.target.value;e.target.value=current.id;navigate(id);});
 ['lang','theme','palette','direction'].forEach(key=>$('#'+key+'-select').addEventListener('change',e=>{if(key==='lang')language=e.target.value;if(key==='theme')theme=e.target.value;if(key==='palette')palette=e.target.value;if(key==='direction')direction=e.target.value;history.replaceState({},'',url(current.id,{state}));render(true);}));
 $('#state-select').addEventListener('change',e=>{state=e.target.value;if(['conflict','expired','stale','empty','filtered'].includes(state))selected.clear();history.replaceState({},'',url(current.id,{state}));render(true);announce(current.states?.[state]||stateText[state]||state);});
 $$('[data-field]').forEach(el=>el.addEventListener('input',()=>{drafts.set(el.dataset.field,el.type==='checkbox'?el.checked:el.value);if(el.type==='file')document.getElementById(el.id+'-name').textContent=el.files?.[0]?.name||tr('No file chosen','Ningún archivo elegido');if(el.dataset.field==='matching.include_similar'){for(const key of selected.keys())if(key.startsWith(current.id+':'))selected.delete(key);$$('[data-choice]').forEach(e=>e.checked=false);$$('[data-action=apply-choice]').forEach(e=>e.disabled=true);$$('[data-selection]').forEach(e=>e.textContent='0 '+tr('selected','seleccionadas'));}if(el.dataset.field==='recipe.mode'&&current.id!=='helper-'+el.value){const target='helper-'+el.value;confirm(['Change sample format?','¿Cambiar formato de muestra?'],['This replaces field rules with the chosen format example. Cancel keeps your draft.','Sustituye reglas por el ejemplo del formato elegido. Cancelar conserva borrador.'],()=>{drafts.clear();baseline.clear();navigate(target);});}updateForms(true);applyViewFilters();if(el.closest('form').dataset.saveTiming==='immediate')el.closest('form').requestSubmit();}));
 $$('[data-save-timing=enter-blur] input').forEach(el=>{el.addEventListener('blur',()=>{if(!pendingForms.has(formKey(current.blocks[el.closest('form').dataset.block])))el.closest('form').requestSubmit();});el.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();drafts.set(el.dataset.field,baseline.get(el.dataset.field));el.value=baseline.get(el.dataset.field);updateForms(true);}});});
 $$('form.workflow-form').forEach(el=>el.addEventListener('submit',e=>{e.preventDefault();updateForms(true);if(el.querySelector('[type=submit]').disabled)return;const b=current.blocks[el.dataset.block];if(b.confirm)confirm(b.title,b.confirm,()=>finishForm(b),b.action);else finishForm(b);}));
 $$('[data-choice]').forEach(el=>el.addEventListener('change',()=>{const i=el.dataset.choice;const values=$$(`[data-choice="${i}"]:checked`).map(e=>e.value);selected.set(current.id+':'+i,values);$(`[data-selection="${i}"]`).textContent=values.length+' '+tr('selected','seleccionadas');$(`[data-action=apply-choice][data-block="${i}"]`).disabled=!values.length;updateForms(false);}));
 $$('[data-action]').forEach(el=>el.addEventListener('click',async()=>{
  const action=el.dataset.action, b=current.blocks[el.dataset.block];
  if(action==='choose-file')document.getElementById(el.dataset.fileId).click();
  if(action==='menu'){$('#drawer').innerHTML=button(['Close menu','Cerrar menú'],'close-menu','class="drawer-close"')+navigation(true);$('#drawer').showModal();$('#drawer button').focus();$('#drawer button').onclick=()=>{$('#drawer').close();$('#menu-open').focus();};$$('#drawer [data-screen]').forEach(a=>a.onclick=e=>{e.preventDefault();$('#drawer').close();navigate(a.dataset.screen);});}
  if(action==='clear-state'){state='ready';history.replaceState({},'',url(current.id));render(true);}
  if(action==='reset'){b.fields.forEach(f=>drafts.set(f.key,baseline.get(f.key)));results.delete(formKey(b));render(true);}
  if(action==='command'&&(!b.selection||selectionCount()))confirm(b.label,b.consequence,()=>{results.set(current.id+':command:'+el.dataset.block,b.result);const out=$(`[data-result="${el.dataset.block}"]`);out.textContent=t(b.result);announce(b.result);if(b.next)navigate(b.next);},b.label);
  if(action==='apply-choice')confirm(b.action,b.effect,()=>{$(`[data-result="${el.dataset.block}"]`).textContent=t(b.effect);announce(b.effect);if(b.next)navigate(b.next);},b.action);
  if(action==='copy') { const out=$(`[data-result="${el.dataset.block}"]`);try {await navigator.clipboard.writeText(b.value);out.textContent=tr('Copied synthetic example.','Ejemplo ficticio copiado.');}catch{out.textContent=tr('Copy unavailable. Select the example text above and copy it manually.','Copia no disponible. Selecciona el ejemplo y cópialo manualmente.');} }
  if(action==='up')orderMove(+el.dataset.position,+el.dataset.position-1);
  if(action==='down')orderMove(+el.dataset.position,+el.dataset.position+1);
  if(action==='reset-order'){const r=current.blocks.find(x=>x.type==='reorder');orders.set(current.id,[...r.names]);render(true);}
  if(action==='save-order')confirm(['Save complete order?','¿Guardar orden completo?'],current.blocks.find(x=>x.type==='reorder').effect,()=>{current.blocks.find(x=>x.type==='reorder').names=[...orders.get(current.id)];$('#order-result').textContent=tr('Complete order saved for all 3 items.','Orden completo guardado para los 3 elementos.');announce($('#order-result').textContent);});
 }));
 $$('.order-row [draggable]').forEach(el=>{el.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/plain',el.dataset.position);});el.addEventListener('keydown',e=>{if(e.altKey&&['ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();orderMove(+el.dataset.position,+el.dataset.position+(e.key==='ArrowUp'?-1:1));}});});
 $$('.order-row').forEach(el=>{el.addEventListener('dragover',e=>e.preventDefault());el.addEventListener('drop',e=>{e.preventDefault();orderMove(+e.dataTransfer.getData('text/plain'),+el.dataset.position);});});
}
$('#confirm-cancel').onclick=()=>{nextDialog=null;closeConfirm();};
$('#confirm-commit').onclick=()=>{const fn=nextDialog;nextDialog=null;closeConfirm();fn?.();};
$('#confirm').addEventListener('cancel',()=>{nextDialog=null;setTimeout(()=>lastFocus?.isConnected&&lastFocus.focus(),0);});
$('#drawer').addEventListener('cancel',()=>setTimeout(()=>$('#menu-open')?.focus(),0));
// Keep keyboard traversal inside the modal, including headless browsers that
// otherwise move focus to browser chrome at the native-dialog boundary.
['confirm','drawer'].forEach(id=>document.getElementById(id).addEventListener('keydown',e=>{
 if(e.key!=='Tab')return;
 const nodes=Array.from(e.currentTarget.querySelectorAll('button,a[href],input,select,textarea,[tabindex="0"]')).filter(n=>!n.disabled&&n.getClientRects().length);
 const first=nodes[0],last=nodes[nodes.length-1];
 if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
 else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
}));
window.addEventListener('beforeunload',e=>{if(hasDirty()){e.preventDefault();e.returnValue='';}});
window.addEventListener('popstate',()=>{const next=new URLSearchParams(location.search).get('screen');history.replaceState({},'',url(current.id));navigate(next||'dashboard');});
window.__workflow={get current(){return current.id;},get state(){return state;},get dirty(){return hasDirty();},screens:screens.length};
render();
})();
