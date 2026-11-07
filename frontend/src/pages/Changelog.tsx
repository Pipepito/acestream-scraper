import React, { useEffect } from 'react';
import { Box, Chip, Link, Stack, Typography } from '@mui/material';
import PageHeader from '../components/layout/PageHeader';
import StatusLine from '../components/StatusLine';
import ContentSection from '../components/layout/ContentSection';
import { currentRelease, releases } from '../data/changelog';
import { markChangelogRead } from '../hooks/useChangelog';

/** Render the small link subset accepted by the release-note generator, never HTML. */
export function ReleaseNoteText({ text }: { text: string }) {
  const pattern = /\[([^\]\n[]+)\]\((https:\/\/github\.com\/[A-Za-z0-9_./-]+)\)/g;
  const parts: React.ReactNode[] = [];
  let end = 0;
  for (const match of Array.from(text.matchAll(pattern))) {
    const start = match.index!;
    parts.push(text.slice(end, start));
    parts.push(<Link key={start} href={match[2]} target="_blank" rel="noopener noreferrer">{match[1]}</Link>);
    end = start + match[0].length;
  }
  parts.push(text.slice(end));
  return <>{parts}</>;
}

export default function Changelog() {
  useEffect(markChangelogRead, []);
  return (
    <Box>
      <PageHeader title="Changelog" subtitle="Changes by version, included with your installation." />
      <StatusLine items={[{ label: 'Build notes', value: currentRelease.version }, { label: 'Versions', value: releases.length }]} />
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Notes for this build: {currentRelease.version}. Development builds may include changes before a stable release is published.
      </Typography>
      <Stack component="nav" aria-label="Release versions" direction="row" spacing={2} useFlexGap flexWrap="wrap" sx={{ mb: 3 }}>
        {releases.map((release) => <Link key={release.version} href={`#${release.version}`} sx={{ py: 1 }}>{release.version}</Link>)}
      </Stack>
      {releases.map((release, index) => (
        <Box key={release.version} id={release.version} sx={{ scrollMarginTop: 88, mb: 3 }}>
          <ContentSection title={release.version} description={release.summary}
            actions={index === 0 ? <Chip size="small" label="Included in this build" /> : undefined}>
            {release.sections.map((section) => (
              <Box key={section.title} sx={{ mt: 2 }}>
                <Typography component="h3" variant="subtitle1" fontWeight={600}>{section.title}</Typography>
                <Box component="ul" sx={{ pl: 2.5, mt: 1, mb: 2, maxWidth: '80ch' }}>
                  {section.items.map((item) => <Typography component="li" key={item} sx={{ mb: 1, overflowWrap: 'anywhere' }}><ReleaseNoteText text={item} /></Typography>)}
                </Box>
              </Box>
            ))}
          </ContentSection>
        </Box>
      ))}
      <Link href="https://github.com/Pipepito/acestream-scraper/releases" target="_blank" rel="noopener noreferrer">Published releases on GitHub (opens in a new tab)</Link>
    </Box>
  );
}
