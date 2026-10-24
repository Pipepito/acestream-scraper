import { useEffect, useState } from 'react';
import { currentRelease } from '../data/changelog';

const STORAGE_KEY = 'acestream.changelog.seen.v1';
const EVENT = 'acestream-changelog-read';
let memorySeen: string | null = null;

function readSeen(): string | null {
  if (memorySeen !== null) return memorySeen;
  try { return localStorage.getItem(STORAGE_KEY); }
  catch { return memorySeen; }
}

export function markChangelogRead(): void {
  try {
    localStorage.setItem(STORAGE_KEY, currentRelease.version);
    memorySeen = null;
  }
  catch { memorySeen = currentRelease.version; }
  window.dispatchEvent(new Event(EVENT));
}

export function useChangelogUnread(): boolean {
  const [seen, setSeen] = useState(readSeen);
  useEffect(() => {
    const update = () => setSeen(readSeen());
    window.addEventListener(EVENT, update);
    window.addEventListener('storage', update);
    return () => {
      window.removeEventListener(EVENT, update);
      window.removeEventListener('storage', update);
    };
  }, []);
  return seen !== currentRelease.version;
}
