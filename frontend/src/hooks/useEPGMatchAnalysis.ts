import { useEffect, useMemo, useState } from 'react';
import { useQueryClient } from 'react-query';
import {
  tvChannelService,
  EPGMatchAnalysisResponse,
  EPGMatchAnalysisRow,
  EPGMatchStrictness
} from '../services/tvChannelService';
import { SnackbarSeverity } from './useSnackbar';

export type MatchFilter = 'all' | 'matched' | 'unmatched' | 'creatable';

/**
 * Hook owning the EPG-to-TV-channel match analysis workflow state for the EPG page.
 */
export const useEPGMatchAnalysis = (
  selectedSourceId: number | undefined,
  showSnackbar: (message: string, severity: SnackbarSeverity) => void
) => {
  const queryClient = useQueryClient();
  const [matchStrictness, setMatchStrictness] = useState<EPGMatchStrictness>('balanced');
  const [isAnalyzingMatches, setIsAnalyzingMatches] = useState(false);
  const [matchAnalysis, setMatchAnalysis] = useState<EPGMatchAnalysisResponse | null>(null);
  const [matchFilter, setMatchFilter] = useState<MatchFilter>('all');
  const [selectedMatchRowIds, setSelectedMatchRowIds] = useState<number[]>([]);

  const filteredMatchRows = useMemo(() => {
    const rows = matchAnalysis?.rows || [];

    switch (matchFilter) {
      case 'matched':
        return rows.filter((row) => row.candidate_count > 0);
      case 'unmatched':
        return rows.filter((row) => row.candidate_count === 0);
      case 'creatable':
        return rows.filter((row) => row.is_creatable);
      case 'all':
      default:
        return rows;
    }
  }, [matchAnalysis, matchFilter]);

  useEffect(() => {
    setMatchAnalysis(null);
    setSelectedMatchRowIds([]);
    setMatchFilter('all');
  }, [selectedSourceId]);

  const handleAnalyzeMatches = () => {
    setIsAnalyzingMatches(true);

    queueMicrotask(() => {
      void (async () => {
        try {
          const result = await tvChannelService.analyzeEPGMatches({
            strictness: matchStrictness,
            ...(selectedSourceId !== undefined ? { source_id: selectedSourceId } : {}),
          });
          setMatchAnalysis(result);
          setMatchFilter('all');
          setSelectedMatchRowIds(result.rows.filter((row) => row.is_creatable).map((row) => row.epg_channel_id));
        } catch (error) {
          showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        } finally {
          setIsAnalyzingMatches(false);
        }
      })();
    });
  };

  const handleToggleMatchRow = (row: EPGMatchAnalysisRow) => {
    if (!row.is_creatable) {
      return;
    }

    setSelectedMatchRowIds((prev) =>
      prev.includes(row.epg_channel_id)
        ? prev.filter((id) => id !== row.epg_channel_id)
        : [...prev, row.epg_channel_id]
    );
  };

  const handleCreateMatchedTVChannels = () => {
    if (selectedMatchRowIds.length === 0) {
      return;
    }

    queueMicrotask(() => {
      void (async () => {
        try {
          const result = await tvChannelService.createFromEPGAnalysis({
            strictness: matchStrictness,
            epg_channel_ids: selectedMatchRowIds,
          });

          queryClient.invalidateQueries('tvChannels');
          queryClient.invalidateQueries('epg-channels');

          showSnackbar(
            `Created ${result.created_count} TV channels, skipped ${result.skipped_count}, associated ${result.associated_count} Acestream channels`,
            'success'
          );

          setSelectedMatchRowIds([]);
        } catch (error) {
          showSnackbar(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
        }
      })();
    });
  };

  return {
    matchStrictness,
    setMatchStrictness,
    isAnalyzingMatches,
    matchAnalysis,
    matchFilter,
    setMatchFilter,
    selectedMatchRowIds,
    filteredMatchRows,
    handleAnalyzeMatches,
    handleToggleMatchRow,
    handleCreateMatchedTVChannels
  };
};
