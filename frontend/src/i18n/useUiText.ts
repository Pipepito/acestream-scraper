import { useTranslation } from 'react-i18next';

/** Subscribe the owning component; changing language keeps its React identity. */
export function useUiText() {
  return useTranslation('ui').t;
}
