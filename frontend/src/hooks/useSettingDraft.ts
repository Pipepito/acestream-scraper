import { useEffect, useState } from 'react';
import { useUnsavedChanges } from '../components/UnsavedChanges';

/** A server refresh must never replace a field being edited. */
export function useSettingDraft<T extends string | number | boolean>(saved: T | undefined, fallback: T, pending = false) {
  const [draft, setDraft] = useState<{ initial: T; value: T } | null>(null);
  const value = draft?.value ?? saved ?? fallback;
  const dirty = draft !== null && draft.value !== draft.initial;
  useUnsavedChanges(dirty, pending);
  useEffect(() => {
    if (draft && !dirty && saved === draft.value) setDraft(null);
  }, [draft, dirty, saved]);
  return {
    value, dirty,
    change: (next: T) => setDraft(current => ({ initial: current?.initial ?? saved ?? fallback, value: next })),
    saved: (next: T) => setDraft({ initial: next, value: next }),
    discard: () => setDraft(null),
  };
}
