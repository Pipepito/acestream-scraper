import { useEffect, useMemo, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { tvChannelService, EPGMatchAnalysisResponse, EPGMatchAnalysisRow, EPGMatchStrictness } from '../services/tvChannelService';
import { SnackbarSeverity } from './useSnackbar';

export type MatchFilter = 'all' | 'matched' | 'unmatched' | 'creatable';

export const useEPGMatchAnalysis = (selectedSourceId: number | undefined, showSnackbar: (message: string, severity: SnackbarSeverity) => void) => {
  const queryClient = useQueryClient();
  const [matchStrictness, setMatchStrictness] = useState<EPGMatchStrictness>('strict');
  const [isAnalyzingMatches, setIsAnalyzingMatches] = useState(false);
  const [isApplyingMatches, setIsApplyingMatches] = useState(false);
  const [matchAnalysis, setMatchAnalysis] = useState<EPGMatchAnalysisResponse | null>(null);
  const [matchFilter, setMatchFilter] = useState<MatchFilter>('all');
  const [selectedMatchRowIds, setSelectedMatchRowIds] = useState<number[]>([]);
  const revision = useRef(0);
  const applying = useRef(false);

  const filteredMatchRows = useMemo(() => {
    const rows = matchAnalysis?.rows || [];
    if (matchFilter === 'matched') return rows.filter(row => row.candidate_count > 0);
    if (matchFilter === 'unmatched') return rows.filter(row => row.candidate_count === 0);
    if (matchFilter === 'creatable') return rows.filter(row => row.is_creatable);
    return rows;
  }, [matchAnalysis, matchFilter]);

  useEffect(() => {
    revision.current += 1;
    setMatchAnalysis(null); setSelectedMatchRowIds([]); setMatchFilter('all'); setIsAnalyzingMatches(false);
    return () => { revision.current += 1; };
  }, [selectedSourceId, matchStrictness]);

  const handleAnalyzeMatches = async () => {
    if (applying.current) return;
    const current = ++revision.current;
    setIsAnalyzingMatches(true); setMatchAnalysis(null); setSelectedMatchRowIds([]);
    try {
      const result = await tvChannelService.analyzeEPGMatches({ strictness: matchStrictness, source_id: selectedSourceId });
      if (revision.current === current) { setMatchAnalysis(result); setMatchFilter('all'); }
    } catch {
      if (revision.current === current) showSnackbar('Could not analyze guide matches. Try again.', 'error');
    } finally {
      if (revision.current === current) setIsAnalyzingMatches(false);
    }
  };

  const handleToggleMatchRow = (row: EPGMatchAnalysisRow) => {
    if (!(row.can_apply ?? row.is_creatable) || applying.current) return;
    setSelectedMatchRowIds(prev => prev.includes(row.epg_channel_id) ? prev.filter(id => id !== row.epg_channel_id) : [...prev, row.epg_channel_id]);
  };

  const handleCreateMatchedTVChannels = async () => {
    if (!matchAnalysis || !selectedMatchRowIds.length || applying.current) return;
    applying.current = true; setIsApplyingMatches(true);
    try {
      const selected = matchAnalysis.rows.filter(row => selectedMatchRowIds.includes(row.epg_channel_id));
      const result = await tvChannelService.createFromEPGAnalysis({
        strictness: matchStrictness, epg_channel_ids: selectedMatchRowIds, source_id: selectedSourceId,
        expected_previews: Object.fromEntries(selected.map(row => [row.epg_channel_id, row.review_token ?? ''])),
      });
      for (const key of ['tvChannels', 'epg-channels', 'guide-coverage', 'acestreamChannels']) {
        void queryClient.invalidateQueries({ queryKey: [key] });
      }
      showSnackbar(`Created ${result.created_count} TV channels, assigned ${result.associated_count} streams, skipped ${result.skipped_count}${result.failure_count ? `, failed ${result.failure_count}` : ''}`, result.failure_count ? 'warning' : 'success');
    } catch {
      showSnackbar('Could not apply matches. The catalogue may have changed; analyze again before applying.', 'error');
    } finally {
      applying.current = false; setIsApplyingMatches(false); setSelectedMatchRowIds([]); setMatchAnalysis(null);
    }
  };

  return { matchStrictness, setMatchStrictness, isAnalyzingMatches, isApplyingMatches, matchAnalysis, matchFilter, setMatchFilter, selectedMatchRowIds,
    filteredMatchRows, handleAnalyzeMatches, handleToggleMatchRow, handleCreateMatchedTVChannels };
};
