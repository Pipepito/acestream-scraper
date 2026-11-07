/* Keep both builders mounted so switching tools preserves work. */
(() => {
  const links = document.querySelectorAll('[data-tool]');
  const panels = document.querySelectorAll('[data-tool-panel]');
  const frame = document.getElementById('recipe-tool');
  const select = () => {
    const requested = location.hash.slice(1);
    const active = ['recipes', 'docs'].includes(requested) ? requested : 'docker';
    links.forEach(link => {
      if (link.dataset.tool === active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    panels.forEach(panel => { panel.hidden = panel.dataset.toolPanel !== active; });
    if (active === 'recipes' && !frame.hasAttribute('src')) frame.src = frame.dataset.src;
  };
  window.addEventListener('hashchange', select);
  window.addEventListener('message', event => {
    if (event.origin !== location.origin || event.source !== frame.contentWindow) return;
    if (event.data?.type === 'recipe-builder-height' && Number.isFinite(event.data.height)) {
      frame.style.height = `${Math.max(900, Math.min(60000, event.data.height))}px`;
    }
  });
  select();
})();
