import React from 'react';
import { Box, Chip, LinearProgress, Stack, Typography, useTheme } from '@mui/material';
import { format, parseISO } from 'date-fns';
import type { EPGProgram } from '../../services/epgService';
import { formatRelativeTime } from '../../utils/format';

export interface NowNextProps {
  programs: EPGProgram[];
  now: Date;
}

const timeRange = (program: EPGProgram): string =>
  `${format(parseISO(program.start_time), 'HH:mm')}–${format(parseISO(program.end_time), 'HH:mm')}`;

/** The programme on air right now (with progress) and the one after it. */
const NowNext: React.FC<NowNextProps> = ({ programs, now }) => {
  const theme = useTheme();
  const nowMs = now.getTime();
  const current = programs.find((program) => parseISO(program.start_time).getTime() <= nowMs && parseISO(program.end_time).getTime() > nowMs);
  const next = programs.find((program) => parseISO(program.start_time).getTime() > nowMs);

  const progress = current
    ? Math.min(100, Math.max(0, ((nowMs - parseISO(current.start_time).getTime()) / (parseISO(current.end_time).getTime() - parseISO(current.start_time).getTime())) * 100))
    : 0;

  return (
    <Box
      role="region"
      aria-label="Now and next"
      sx={{
        p: 2,
        mb: 2,
        borderRadius: 2,
        border: `1px solid ${theme.appTokens.surface.border}`,
        backgroundColor: theme.appTokens.surface.raised,
      }}
    >
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="statusMeta" component="p" color="text.secondary">
            Now
          </Typography>
          {current ? (
            <>
              <Typography component="p" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
                {current.title}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {timeRange(current)} · ends {formatRelativeTime(current.end_time, now)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={progress}
                aria-label={`${current.title} progress`}
                sx={{ mt: 1, height: 6, borderRadius: 3 }}
              />
            </>
          ) : (
            <Typography component="p" color="text.secondary">
              Nothing on air right now.
            </Typography>
          )}
        </Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="statusMeta" component="p" color="text.secondary">
            Next
          </Typography>
          {next ? (
            <>
              <Typography component="p" sx={{ fontWeight: 600, overflowWrap: 'anywhere' }}>
                {next.title}
              </Typography>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="body2" color="text.secondary">
                  {timeRange(next)} · starts {formatRelativeTime(next.start_time, now)}
                </Typography>
                {next.category ? <Chip label={next.category} size="small" variant="outlined" /> : null}
              </Stack>
            </>
          ) : (
            <Typography component="p" color="text.secondary">
              No later programme listed.
            </Typography>
          )}
        </Box>
      </Stack>
    </Box>
  );
};

export default NowNext;
