import { useUiText } from '../i18n/useUiText';
import React from 'react';
import { Badge, Box, Button, IconButton, Tooltip } from '@mui/material';
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import CloseIcon from '@mui/icons-material/Close';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { currentRelease } from '../data/changelog';
import { markChangelogRead, useChangelogUnread } from '../hooks/useChangelog';

export default function WhatsNewNotice() {
  const tUi = useUiText();
  const unread = useChangelogUnread();
  const { pathname } = useLocation();
  if (!unread || pathname === '/changelog') return null;
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
      <Tooltip title={tUi("What’s new in {{value0}}", { value0: currentRelease.version })}>
        <Button component={RouterLink} to="/changelog" color="inherit" onClick={markChangelogRead}
          aria-label={tUi("What’s new in {{value0}}", { value0: currentRelease.version })} size="small"
          sx={{ minWidth: 44, minHeight: 44, gap: 1, color: 'text.secondary', px: 1 }}>
          <Badge variant="dot" color="primary"><ArticleOutlinedIcon fontSize="small" /></Badge>
          <Box component="span" sx={{ display: { xs: 'none', sm: 'inline' } }}>{tUi("What’s new")}</Box>
        </Button>
      </Tooltip>
      <Tooltip title={tUi("Dismiss changelog notice")}>
        <IconButton aria-label={tUi("Dismiss changelog notice")} onClick={markChangelogRead}
          sx={{ width: 44, height: 44, color: 'text.secondary' }}>
          <CloseIcon sx={{ fontSize: 16 }} />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
