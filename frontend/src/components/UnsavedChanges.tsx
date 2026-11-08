import React, { createContext, useCallback, useContext, useEffect, useId, useLayoutEffect, useState } from 'react';
import { useBlocker } from 'react-router-dom';
import ConfirmDialog from './ConfirmDialog';
import { useUiText } from '../i18n/useUiText';

interface EditorState { dirty: boolean; pending: boolean }
type Register = (id: string, state: EditorState | null) => void;
const UnsavedContext = createContext<Register | null>(null);

/** One navigation guard for all canonical editors, including query-string tabs. */
export function UnsavedChangesProvider({ children }: React.PropsWithChildren) {
  const t = useUiText();
  const [editors, setEditors] = useState<Record<string, EditorState>>({});
  const register = useCallback<Register>((id, state) => setEditors(previous => {
    if (previous[id]?.dirty === state?.dirty && previous[id]?.pending === state?.pending) return previous;
    const next = { ...previous };
    if (state) next[id] = state;
    else delete next[id];
    return next;
  }), []);
  const dirty = Object.values(editors).some(editor => editor.dirty);
  const pending = Object.values(editors).some(editor => editor.pending);
  const blocker = useBlocker(({ currentLocation, nextLocation }) => (dirty || pending) && (
    currentLocation.pathname !== nextLocation.pathname || currentLocation.search !== nextLocation.search
  ));
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
export function useUnsavedChanges(dirty: boolean, pending = false) {
  const register = useContext(UnsavedContext);
  const id = useId();
  useLayoutEffect(() => { register?.(id, { dirty, pending }); }, [register, id, dirty, pending]);
  useLayoutEffect(() => () => register?.(id, null), [register, id]);
}
