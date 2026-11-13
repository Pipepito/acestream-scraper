/* Local reference interactions only. No requests, storage or application calls. */
'use strict';
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
function luminance(color) {
  const values = color.match(/[\d.]+/g).slice(0, 3).map(Number).map(v => {
    const c = v / 255;
    return c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4;
  });
  return values[0] * .2126 + values[1] * .7152 + values[2] * .0722;
}
function updateTokens() {
  const style = getComputedStyle(document.body);
  $$('[data-token]').forEach(el => { el.textContent = style.getPropertyValue(el.dataset.token).trim(); });
  $$('[data-contrast]').forEach(el => {
    const pair = getComputedStyle(el);
    const values = [luminance(pair.color), luminance(pair.backgroundColor)].sort((a,b) => b-a);
    const ratio = (values[0]+.05)/(values[1]+.05);
    el.querySelector('[data-ratio]').textContent = `${ratio.toFixed(2)}:1 · ${ratio >= 4.5 ? 'AA normal text' : 'Review pairing'}`;
  });
}
$('#theme-toggle').onclick = () => {
  const dark = document.body.classList.toggle('dark');
  $('#theme-toggle').setAttribute('aria-pressed', String(dark));
  updateTokens();
};
const dialog = $('#reference-dialog');
dialog.addEventListener('keydown', event => {
  if (event.key !== 'Tab') return;
  const first = $('#dialog-cancel'), last = $('#dialog-save');
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
$('#open-dialog').onclick = () => dialog.showModal();
$('#dialog-cancel').onclick = () => dialog.close();
$('#dialog-save').onclick = () => { dialog.close(); $('#action-status').textContent = 'Example confirmed. No data was saved.'; };
dialog.addEventListener('close', () => $('#open-dialog').focus());
$('#save-demo').onclick = () => { $('#action-status').textContent = 'Success · example saved in this demonstration only.'; };
$('#error-demo').onclick = () => { $('#action-status').textContent = 'Error example · could not save. Your draft is retained. Try again.'; };
function filter(category) {
  $$('[data-filter]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.filter === category)));
  $$('[data-sport]').forEach(el => { el.hidden = category !== 'all' && el.dataset.sport !== category; });
  $('#filter-status').textContent = category === 'all' ? 'Showing Football and Tennis examples.' : `Showing ${category} example.`;
}
$$('[data-filter]').forEach(el => { el.onclick = () => filter(el.dataset.filter); });
$('#clear-demo').onclick = () => { filter('all'); $('#filter-status').textContent = 'Filters cleared. Showing Football and Tennis examples.'; };
$('#favorite-demo').onclick = () => {
  const selected = $('#favorite-demo').getAttribute('aria-pressed') !== 'true';
  $('#favorite-demo').setAttribute('aria-pressed', String(selected));
  $('#favorite-demo span:last-child').textContent = selected ? 'Following example' : 'Follow example';
};
$('#example-number').oninput = () => {
  const value = $('#example-number').value;
  const valid = value !== '' && Number.isInteger(Number(value)) && Number(value) >= 1;
  $('#example-number').setAttribute('aria-invalid', String(!valid));
  $('#number-error').textContent = valid ? 'Valid channel number.' : 'Enter a whole number of 1 or greater.';
  $('#number-error').classList.toggle('field-error', !valid);
};
$('#retry-demo').onclick = () => { $('#retry-status').textContent = 'Retry demonstration succeeded. No guide was requested.'; };
$('#play-demo').onclick = () => {
  const playing = $('#play-demo').getAttribute('aria-pressed') !== 'true';
  $('#play-demo').setAttribute('aria-pressed', String(playing));
  $('#play-demo .icon').className = 'icon icon-' + (playing ? 'pause' : 'play');
  $('#play-demo span:last-child').textContent = playing ? 'Pause example' : 'Play example';
  $('#player-status').textContent = (playing ? 'Playing' : 'Paused') + ' example. No media is loaded.';
};
$('#mute-demo').onclick = () => {
  const muted = $('#mute-demo').getAttribute('aria-pressed') !== 'true';
  $('#mute-demo').setAttribute('aria-pressed', String(muted));
  $('#mute-demo').textContent = muted ? 'Unmute example' : 'Mute example';
};
const motion = matchMedia('(prefers-reduced-motion: reduce)');
function updateMotion() { $('#motion-status').textContent = motion.matches ? 'Your preference: reduced motion is active.' : 'Your preference: standard motion.'; }
motion.addEventListener('change', updateMotion);
updateMotion();
updateTokens();
