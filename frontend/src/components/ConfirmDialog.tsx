import React, { useCallback, useId, useRef, useState } from 'react';
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
  const titleId = useId();
  return (
    <Dialog open={open} onClose={busy ? undefined : onClose} aria-labelledby={titleId} maxWidth="xs" fullWidth>
      <DialogTitle id={titleId}>{title}</DialogTitle>
      <DialogContent>
        {typeof body === 'string' ? <DialogContentText>{body}</DialogContentText> : body}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={busy}>
          Cancel
        </Button>
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
