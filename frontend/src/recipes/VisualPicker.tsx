import React, { useMemo, useRef, useState } from 'react';
import { Alert, Box, Button, Stack, Typography } from '@mui/material';

interface VisualPickerProps { sample: string; records: string; onPick: (selector: string, attribute: string, value: string) => void; pickingRecord: boolean }
const tags = new Set('html head body style div span section article main header footer nav aside h1 h2 h3 h4 h5 h6 p a ul ol li table thead tbody tfoot tr td th caption colgroup col label input textarea pre code b strong em i small br hr img dl dt dd figure figcaption'.split(' '));
const attrs = new Set(['class', 'id', 'title', 'style', 'colspan', 'rowspan', 'width', 'height', 'alt', 'value', 'href', 'data-acestream', 'data-acestream-id']);
export function previewDocument(sample: string): string {
  const template = document.createElement('template');
  template.innerHTML = sample;
  template.content.querySelectorAll('*').forEach(element => {
    if (!tags.has(element.tagName.toLowerCase()) || element.matches('input[type="password"],input[type="hidden"]')) { element.remove(); return; }
    Array.from(element.attributes).forEach(attr => { if (!attrs.has(attr.name)) element.removeAttribute(attr.name); });
    if (element.tagName === 'A') {
      // Keep the value for selection, never create a navigable preview link.
      element.setAttribute('data-picker-href', element.getAttribute('href') ?? '');
      element.removeAttribute('href');
    }
    if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') element.setAttribute('readonly', '');
  });
  return `<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; base-uri 'none'; form-action 'none'"><style>body{font:16px sans-serif;color:#26343a;background:#fafaf8;padding:16px;overflow-wrap:anywhere}*{cursor:crosshair!important}a{color:#007f83;text-decoration:underline}table{border-collapse:collapse}td,th{padding:8px} [data-picker-hover]{outline:2px solid #008588!important;outline-offset:2px} [data-picker-record]{background:rgba(0,133,136,.08)!important}</style></head><body>${template.innerHTML}</body></html>`;
}
function selectorPart(element: Element): string {
  const classes = Array.from(element.classList).filter(name => /^[a-zA-Z_][\w-]*$/.test(name)).slice(0, 2);
  return element.tagName.toLowerCase() + classes.map(name => `.${name}`).join('');
}
export default function VisualPicker({ sample, records, onPick, pickingRecord }: VisualPickerProps) {
  const frame = useRef<HTMLIFrameElement>(null);
  const selected = useRef<Element | null>(null);
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const srcDoc = useMemo(() => previewDocument(sample), [sample]);
  const pick = (element: Element) => {
    if (element.tagName === 'HTML' || element.tagName === 'BODY') return;
    selected.current = element;
    setDescription(selectorPart(element));
    let row: Element | null = null;
    try { row = !pickingRecord && records ? element.closest(records) : null; }
    catch { setError('The repeating row selector is invalid. Correct it before selecting a field.'); return; }
    if (!pickingRecord && !row) { setError('Select a repeating row first, then choose a field inside one of its rows.'); return; }
    setError('');
    let selector = pickingRecord ? selectorPart(element) : '';
    if (!pickingRecord && element !== row) {
      const parts: string[] = [];
      let node: Element | null = element;
      while (node && node !== row) { parts.unshift(selectorPart(node)); node = node.parentElement; }
      selector = parts.join(' > ');
    }
    const attribute = element.hasAttribute('data-picker-href') ? 'href' : element.hasAttribute('value') ? 'value' : element.hasAttribute('data-acestream-id') ? 'data-acestream-id' : element.hasAttribute('data-acestream') ? 'data-acestream' : '';
    onPick(selector, attribute, element.getAttribute(attribute === 'href' ? 'data-picker-href' : attribute) ?? element.textContent ?? '');
  };
  const attach = () => {
    const doc = frame.current?.contentDocument;
    if (!doc) return;
    doc.onclick = event => { event.preventDefault(); if ((event.target as Element)?.tagName) pick(event.target as Element); };
    doc.addEventListener('mouseover', event => {
      doc.querySelector('[data-picker-hover]')?.removeAttribute('data-picker-hover');
      const target = event.target as Element;
      if (target?.setAttribute) target.setAttribute('data-picker-hover', '');
    });
  };
  // Refresh handlers when the active assignment changes, without reloading the sample.
  React.useEffect(() => {
    const doc = frame.current?.contentDocument;
    if (!doc) return;
    const handler = (event: MouseEvent) => { event.preventDefault(); if ((event.target as Element)?.tagName) pick(event.target as Element); };
    doc.onclick = handler;
    return () => { doc.onclick = null; };
  });
  return <Stack spacing={1}>
    <Typography variant="body2">Click a field to assign it. Choose its parent to select a whole channel row. Original scripts and external assets are disabled.</Typography>
    <Stack direction="row" spacing={1} alignItems="center"><Button size="small" disabled={!description} onClick={() => { if (selected.current?.parentElement) pick(selected.current.parentElement); }}>Select parent</Button><Typography variant="caption">{description}</Typography></Stack>
    {error && <Alert severity="warning">{error}</Alert>}
    <Box component="iframe" ref={frame} title="Source visual picker" sandbox="allow-same-origin" srcDoc={srcDoc} onLoad={attach} sx={{ width: '100%', height: 380, border: '1px solid', borderColor: 'divider', borderRadius: 1 }} />
  </Stack>;
}
