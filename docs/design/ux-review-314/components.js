/* Local component demonstrations. No APIs, media, persistent storage or imports. */
'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const announce = message => { $('#action-result').textContent = message; };
$('#theme-toggle').onclick = () => {
  const dark = document.body.classList.toggle('dark');
  $('#theme-toggle').setAttribute('aria-pressed', String(dark));
};

// Native dialogs provide modality; explicit focus wrapping also covers WebKit.
const openers = new WeakMap();
$$('dialog').forEach(dialog => {
  dialog.addEventListener('close', () => openers.get(dialog)?.focus());
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const controls = [...dialog.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select,textarea,[tabindex="0"]')].filter(el => el.getClientRects().length);
    const first = controls[0], last = controls.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  });
});
document.addEventListener('click', event => {
  const button = event.target.closest('button');
  if (!button || button.disabled || button.getAttribute('aria-disabled') === 'true') return;
  if (button.dataset.open) {
    const dialog = document.getElementById(button.dataset.open);
    openers.set(dialog, button); dialog.showModal();
  }
  if (button.hasAttribute('data-close')) button.closest('dialog').close();
  if (button.dataset.message) announce(button.dataset.message);
});
function toggle(button) {
  const on = button.getAttribute('aria-pressed') !== 'true';
  button.setAttribute('aria-pressed', String(on));
  return on;
}
$('#icon-favorite').onclick = event => {
  const on = toggle(event.currentTarget);
  announce(on ? 'Channel followed in this example.' : 'Channel unfollowed in this example.');
};
$('#toggle-captions').onclick = event => {
  event.currentTarget.textContent = 'Captions · ' + (toggle(event.currentTarget) ? 'On' : 'Off');
};

const menu = $('#schedule-menu'), menuTrigger = $('#menu-trigger');
const menuItems = [...menu.querySelectorAll('[role=menuitem]')];
function closeMenu(returnFocus = true) {
  menu.hidden = true; menuTrigger.setAttribute('aria-expanded', 'false');
  if (returnFocus) menuTrigger.focus();
}
function openMenu(last = false) {
  menu.hidden = false; menuTrigger.setAttribute('aria-expanded', 'true');
  (last ? menuItems.at(-1) : menuItems[0]).focus();
}
menuTrigger.onclick = () => menu.hidden ? openMenu() : closeMenu();
menuTrigger.onkeydown = event => {
  if (['ArrowDown', 'ArrowUp'].includes(event.key)) { event.preventDefault(); openMenu(event.key === 'ArrowUp'); }
};
menu.onkeydown = event => {
  const index = menuItems.indexOf(document.activeElement);
  if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeMenu(); }
  else if (event.key === 'Tab') { closeMenu(); }
  else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? menuItems.length - 1 : (index + (event.key === 'ArrowDown' ? 1 : -1) + menuItems.length) % menuItems.length;
    menuItems[next].focus();
  }
};
menu.onclick = event => {
  const item = event.target.closest('[role=menuitem]');
  if (item && item.getAttribute('aria-disabled') !== 'true') closeMenu();
};
document.addEventListener('click', event => {
  if (!menu.hidden && !event.target.closest('.ds-menu-anchor')) closeMenu(false);
});

function arrowGroup(container, items, activate) {
  container.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    const index = items.indexOf(document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + items.length) % items.length;
    items.forEach((item, i) => { item.tabIndex = i === next ? 0 : -1; });
    items[next].focus();
    if (activate) activate(items[next]);
  });
}
const toolbar = $('[role=toolbar]'), toolbarButtons = [...toolbar.querySelectorAll('button')];
arrowGroup(toolbar, toolbarButtons);
toolbarButtons.forEach(button => {
  button.addEventListener('click', () => {
    toolbarButtons.forEach(item => { item.tabIndex = item === button ? 0 : -1; });
    if (button.hasAttribute('aria-pressed')) announce(button.getAttribute('aria-label') + ': ' + (toggle(button) ? 'On' : 'Off'));
  });
});
const tabs = $$('.ds-tabs [role=tab]');
arrowGroup($('.ds-tabs'), tabs);
tabs.forEach(tab => tab.addEventListener('click', () => {
  tabs.forEach(item => {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected)); item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
  });
}));

const checks = $$('.channel-check'), all = $('#select-all');
function updateSelection() {
  const count = checks.filter(input => input.checked).length;
  all.indeterminate = count > 0 && count < checks.length;
  all.checked = count === checks.length;
  $('#selection-status').textContent = `${count} of ${checks.length} available channels selected.`;
}
checks.forEach(input => { input.onchange = updateSelection; });
all.onchange = () => { checks.forEach(input => { input.checked = all.checked; }); updateSelection(); };
updateSelection();
$('#compact-switch').onclick = event => {
  const on = event.currentTarget.getAttribute('aria-checked') !== 'true';
  event.currentTarget.setAttribute('aria-checked', String(on));
  $('#compact-state').textContent = on ? 'On' : 'Off';
  $('#density-preview').classList.toggle('compact', on);
};
$$('[name=guide-view]').forEach(input => { input.onchange = () => { $('#view-status').textContent = input.value + ' view selected.'; }; });
$('#sports-chip').onclick = event => { $('#chip-status').textContent = toggle(event.currentTarget) ? 'Only sports categories are included.' : 'All categories are included.'; };
const chipMarkup = $('#input-chips').innerHTML;
function removeChip(button) {
  const chips = $$('[data-remove-chip]'), index = chips.indexOf(button);
  button.parentElement.remove();
  const remaining = $$('[data-remove-chip]');
  $('#input-chip-status').textContent = remaining.length + ' filters selected.';
  (remaining[index] || remaining.at(-1) || $('#restore-chips')).focus();
}
$('#input-chips').onclick = event => { if (event.target.matches('[data-remove-chip]')) removeChip(event.target); };
$('#input-chips').onkeydown = event => {
  if (event.target.matches('[data-remove-chip]') && ['Delete', 'Backspace'].includes(event.key)) { event.preventDefault(); removeChip(event.target); }
};
$('#restore-chips').onclick = () => { $('#input-chips').innerHTML = chipMarkup; $('#input-chip-status').textContent = '2 filters selected.'; };
$('#channel-notes').oninput = event => { $('#notes-count').textContent = `${event.target.value.length} of 160 characters.`; };
$('#number-demo').oninput = event => {
  const n = Number(event.target.value), valid = event.target.value !== '' && Number.isInteger(n) && n >= 1;
  event.target.setAttribute('aria-invalid', String(!valid));
  $('#number-hint').textContent = valid ? 'Valid channel number.' : 'Enter a whole number of 1 or greater.';
  $('#number-hint').classList.toggle('field-error', !valid);
};
function searchChannels() {
  const query = $('#component-search').value.trim().toLowerCase();
  let count = 0;
  $$('#search-results li').forEach(row => { row.hidden = !row.dataset.search.includes(query); if (!row.hidden) count++; });
  $('#search-count').textContent = `${count} example channel${count === 1 ? '' : 's'}.`;
  $('#search-empty').hidden = count > 0;
}
$('#component-search').oninput = searchChannels;
$('#clear-search').onclick = () => { $('#component-search').value = ''; searchChannels(); $('#component-search').focus(); };
$('#suggestion-chip').onclick = () => { $('#component-search').value = 'Northlight'; searchChannels(); $('#component-search').focus(); };
$('#volume-demo').oninput = event => { $('#volume-value').textContent = event.target.value + '%'; };
function updateRange() {
  const start = Number($('#range-start').value), end = Number($('#range-end').value), valid = end > start;
  ['#range-start', '#range-end'].forEach(selector => $(selector).setAttribute('aria-invalid', String(!valid)));
  $('#range-status').textContent = valid ? `${String(start).padStart(2, '0')}:00–${String(end).padStart(2, '0')}:00. End must be after start.` : 'Choose an end hour after the start hour.';
  $('#range-status').classList.toggle('field-error', !valid);
}
$('#range-start').oninput = updateRange; $('#range-end').oninput = updateRange;
$('#schedule-form').onsubmit = event => {
  event.preventDefault();
  $('#schedule-result').textContent = `${$('#schedule-date').value} · ${$('#schedule-time').value} · ${$('#schedule-zone').value}. Example only; no recording scheduled.`;
  $('#schedule-sheet').close();
};
$$('[data-destination]').forEach(link => { link.onclick = event => {
  event.preventDefault();
  $$('[data-destination]').forEach(item => item.removeAttribute('aria-current'));
  link.setAttribute('aria-current', 'page'); $('#nav-context').textContent = link.dataset.destination;
  $('#nav-result').textContent = link.dataset.destination + ' selected in this navigation example.';
}; });
let currentPage = 1;
function paginate(delta) {
  currentPage = Math.max(1, Math.min(3, currentPage + delta));
  $('#page-count').textContent = `Page ${currentPage} of 3`;
  $('#previous-page').disabled = currentPage === 1; $('#next-page').disabled = currentPage === 3;
}
$('#previous-page').onclick = () => paginate(-1); $('#next-page').onclick = () => paginate(1);
function carousel(direction) {
  const element = $('#category-carousel');
  element.scrollBy({left: direction * element.clientWidth * .7, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
}
$('#carousel-prev').onclick = () => carousel(-1); $('#carousel-next').onclick = () => carousel(1);

const snackbar = $('#following-snackbar');
function dismissSnackbar(undo = false) {
  const returnFocus = snackbar.contains(document.activeElement);
  snackbar.hidden = true;
  if (undo) $('#following-state').textContent = 'Northlight restored to Following.';
  if (returnFocus) $('#snackbar-demo').focus();
}
$('#snackbar-demo').onclick = () => {
  $('#following-state').textContent = 'Northlight removed from Following. Undo is available in the notification.';
  snackbar.hidden = false; $('#snackbar-message').textContent = 'Northlight removed from Following.';
};
$('#snackbar-undo').onclick = () => dismissSnackbar(true); $('#snackbar-dismiss').onclick = () => dismissSnackbar();
snackbar.onkeydown = event => { if (event.key === 'Escape') { event.preventDefault(); dismissSnackbar(); } };
document.addEventListener('keydown', event => {
  if (event.altKey && event.key.toLowerCase() === 'g' && !snackbar.hidden) { event.preventDefault(); $('#snackbar-undo').focus(); }
});
$('#advance-progress').onclick = () => {
  const progress = $('#progress-demo'); progress.value = progress.value === 100 ? 0 : Math.min(100, progress.value + 20);
  $('#progress-status').textContent = `${progress.value}% · ${progress.value === 100 ? 'example complete' : 'illustrative progress, no import running'}.`;
  $('#advance-progress').textContent = progress.value === 100 ? 'Reset example' : 'Advance example';
};
const tipAnchor = $('#favorite-tip-anchor'), tip = $('#favorite-tip');
let tipTimer;
function showTip() { clearTimeout(tipTimer); tip.hidden = false; }
tipAnchor.onpointerenter = showTip; tipAnchor.addEventListener('focusin', showTip);
tipAnchor.onpointerleave = () => { clearTimeout(tipTimer); tipTimer = setTimeout(() => { if (!tipAnchor.contains(document.activeElement)) tip.hidden = true; }, 1500); };
tipAnchor.addEventListener('focusout', () => { clearTimeout(tipTimer); tip.hidden = true; });
tipAnchor.onkeydown = event => { if (event.key === 'Escape') { clearTimeout(tipTimer); tip.hidden = true; event.preventDefault(); } };
