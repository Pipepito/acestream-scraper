import React, { useState } from 'react';
import { IconButton, ListItemIcon, ListItemText, Menu, MenuItem, Tooltip } from '@mui/material';
import MoreHorizIcon from '@mui/icons-material/MoreHoriz';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';

export interface RowAction {
  label: string;
  onClick: () => void;
  icon?: React.ReactNode;
  danger?: boolean;
  disabled?: boolean;
  /** When set the item renders as a checkbox item. */
  checked?: boolean;
}

export interface RowActionsMenuProps {
  /** Accessible name of the trigger, e.g. "More actions for DAZN1". */
  label: string;
  actions: RowAction[];
}

/** The ⋯ menu for secondary row actions, with real text labels. */
const RowActionsMenu: React.FC<RowActionsMenuProps> = ({ label, actions }) => {
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const close = () => setAnchor(null);
  return (
    <>
      <Tooltip title="More actions">
        <IconButton size="small" aria-label={label} aria-haspopup="menu" aria-expanded={Boolean(anchor)} onClick={(event) => setAnchor(event.currentTarget)}>
          <MoreHorizIcon fontSize="small" />
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={close} MenuListProps={{ dense: true }}>
        {actions.map((action) => {
          const isCheck = action.checked !== undefined;
          return (
            <MenuItem
              key={action.label}
              role={isCheck ? 'menuitemcheckbox' : 'menuitem'}
              aria-checked={isCheck ? action.checked : undefined}
              disabled={action.disabled}
              onClick={() => {
                close();
                action.onClick();
              }}
              sx={action.danger ? { color: 'error.main' } : undefined}
            >
              {isCheck ? (
                <ListItemIcon>{action.checked ? <CheckBoxIcon fontSize="small" /> : <CheckBoxOutlineBlankIcon fontSize="small" />}</ListItemIcon>
              ) : action.icon ? (
                <ListItemIcon sx={action.danger ? { color: 'error.main' } : undefined}>{action.icon}</ListItemIcon>
              ) : null}
              <ListItemText>{action.label}</ListItemText>
            </MenuItem>
          );
        })}
      </Menu>
    </>
  );
};

export default RowActionsMenu;
