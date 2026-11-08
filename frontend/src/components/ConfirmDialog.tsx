import { useUiText } from '../i18n/useUiText';
import React, { useCallback, useEffect, useId, useRef, useState } from 'react';
import { Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from '@mui/material';

export interface ConfirmDialogProps {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel: string;
  danger?: boolean;
  busy?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

/** The app's one confirmation dialog: replaces window.confirm everywhere. */
const ConfirmDialog: React.FC<ConfirmDialogProps> = ({ open, title, body, confirmLabel, danger = false, busy = false, onConfirm, onClose }) => {
  const tUi = useUiText();
  const titleId = useId();
  const bodyId = useId();
  const cancelButton = useRef<HTMLButtonElement>(null);
  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} aria-labelledby={titleId} aria-describedby={bodyId} maxWidth="xs" fullWidth TransitionProps={{ onEntered: () => cancelButton.current?.focus() }}>
      <DialogTitle id={titleId}>{title}</DialogTitle>
      <DialogContent id={bodyId}>
        {typeof body === 'string' ? <DialogContentText>{body}</DialogContentText> : body}
      </DialogContent>
      <DialogActions>
        <Button ref={cancelButton} onClick={onClose} disabled={busy}>
          {tUi("Cancel")}</Button>
        <Button variant="contained" color={danger ? 'error' : 'primary'} onClick={onConfirm} disabled={busy} startIcon={busy ? <CircularProgress size={16} color="inherit" /> : undefined}>
          {confirmLabel}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export type ConfirmOptions = Omit<ConfirmDialogProps, 'open' | 'onConfirm' | 'onClose'>;

/** `const { confirm, dialog } = useConfirm(); if (await confirm({...})) doIt();` — render `{dialog}` once. */
export const useConfirm = (): { confirm: (opts: ConfirmOptions) => Promise<boolean>; dialog: React.ReactNode } => {
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const resolver = useRef<((value: boolean) => void) | null>(null);

  useEffect(() => () => { resolver.current?.(false); resolver.current = null; }, []);

  const settle = useCallback((value: boolean) => {
    resolver.current?.(value);
    resolver.current = null;
    setOptions(null);
  }, []);

  const confirm = useCallback((opts: ConfirmOptions) => {
    resolver.current?.(false);
    setOptions(opts);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const dialog = options ? (
    <ConfirmDialog open title={options.title} body={options.body} confirmLabel={options.confirmLabel} danger={options.danger} busy={options.busy} onConfirm={() => settle(true)} onClose={() => settle(false)} />
  ) : null;

  return { confirm, dialog };
};

export default ConfirmDialog;
