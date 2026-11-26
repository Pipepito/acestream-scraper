import React, { createContext, useCallback, useContext, useEffect, useId, useLayoutEffect, useState } from 'react';
import { useBlocker } from 'react-router-dom';
import ConfirmDialog from './ConfirmDialog';
import { useUiText } from '../i18n/useUiText';

interface EditorState { dirty: boolean; pending: boolean; preservedQueryKeys?: string }
type Register = (id: string, state: EditorState | null) => void;
const UnsavedContext = createContext<Register | null>(null);

/** One navigation guard for all canonical editors, including query-string tabs. */
export function UnsavedChangesProvider({ children }: React.PropsWithChildren) {
  const t = useUiText();
  const [editors, setEditors] = useState<Record<string, EditorState>>({});
  const register = useCallback<Register>((id, state) => setEditors(previous => {
    if (previous[id]?.dirty === state?.dirty && previous[id]?.pending === state?.pending && previous[id]?.preservedQueryKeys === state?.preservedQueryKeys) return previous;
    const next = { ...previous };
    if (state) next[id] = state;
    else delete next[id];
    return next;
  }), []);
  const dirty = Object.values(editors).some(editor => editor.dirty);
  const pending = Object.values(editors).some(editor => editor.pending);
  const blocker = useBlocker(({ currentLocation, nextLocation }) => Object.values(editors).some(editor => {
    if (!editor.dirty && !editor.pending) return false;
    if (currentLocation.pathname !== nextLocation.pathname) return true;
    const current = new URLSearchParams(currentLocation.search);
    const next = new URLSearchParams(nextLocation.search);
    for (const key of editor.preservedQueryKeys?.split(',') ?? []) { current.delete(key); next.delete(key); }
    current.sort(); next.sort();
    return current.toString() !== next.toString();
  }));
  useEffect(() => {
    if (blocker.state === 'blocked' && !dirty && !pending) blocker.proceed();
  }, [blocker, dirty, pending]);
  useEffect(() => {
    if (!dirty && !pending) return;
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [dirty, pending]);
  return <UnsavedContext.Provider value={register}>
    {children}
    <ConfirmDialog open={blocker.state === 'blocked'}
      title={pending ? t('Saving changes…') : t('Discard unsaved changes?')}
      body={pending ? t('Wait for the save to finish before leaving this page.') : t('Your changes have not been saved. Stay to continue editing, or discard them and leave.')}
      confirmLabel={t('Discard and leave')} danger busy={pending}
      onConfirm={() => { if (!pending && blocker.state === 'blocked') blocker.proceed(); }}
      onClose={() => { if (blocker.state === 'blocked') blocker.reset(); }} />
  </UnsavedContext.Provider>;
}

/** Registration does not own drafts: each editor retains its existing save lifecycle. */
export function useUnsavedChanges(dirty: boolean, pending = false, preservedQueryKeys: readonly string[] = []) {
  const register = useContext(UnsavedContext);
  const id = useId();
  const keys = preservedQueryKeys.join(',');
  useLayoutEffect(() => { register?.(id, { dirty, pending, preservedQueryKeys: keys }); }, [register, id, dirty, pending, keys]);
  useLayoutEffect(() => () => register?.(id, null), [register, id]);
}
