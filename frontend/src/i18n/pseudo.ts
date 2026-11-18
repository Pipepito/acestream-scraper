/** Test-only expansion. Interpolation tokens stay intact; values remain verbatim. */
export function pseudoMessage(message: string): string {
  const accents: Record<string, string> = { a: 'á', e: 'ë', i: 'ï', o: 'ö', u: 'ü', A: 'Á', E: 'Ë', I: 'Ï', O: 'Ö', U: 'Ü' };
  const expanded = message.split(/(\{\{[^}]+\}\})/).map(part => part.startsWith('{{') ? part : part.replace(/[aeiouAEIOU]/g, character => `${accents[character]}${accents[character]}`)).join('');
  return `⟦${expanded}⟧`;
}

export function pseudoMessages(messages: Record<string, string>): Record<string, string> {
  return Object.fromEntries(Object.entries(messages).map(([key, value]) => [key, pseudoMessage(value)]));
}
