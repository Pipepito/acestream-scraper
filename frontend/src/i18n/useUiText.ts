import { useMemo } from 'react';
import { useTranslation } from 'react-i18next';

/** Subscribe without capturing a language in an in-flight action or open dialog. */
export function useUiText() {
  const { i18n } = useTranslation('ui');
  return useMemo(() => i18n.getFixedT(null, 'ui'), [i18n]);
}
