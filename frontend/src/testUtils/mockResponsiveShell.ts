import type { Theme } from '@mui/material/styles';
import type { useMediaQuery } from '@mui/material';

import { getShellLayout } from '../styles/layout';

interface ResponsiveShellState {
  isPhone?: boolean;
  isDesktop?: boolean;
  isWideDesktop?: boolean;
  viewportWidth?: number;
}

export const mockResponsiveShellQueries = (
  mockUseMediaQuery: jest.MockedFunction<typeof useMediaQuery>,
  theme: Theme,
  state: ResponsiveShellState = {}
) => {
  const { isPhone = false, isDesktop = true, isWideDesktop = true, viewportWidth } = state;
  const layout = getShellLayout(theme);

  mockUseMediaQuery.mockImplementation((queryInput) => {
    const query = typeof queryInput === 'function' ? queryInput(theme) : queryInput;

    if (typeof viewportWidth === 'number') {
      const minWidthMatch = query.match(/min-width:\s*([\d.]+)px/);

      if (minWidthMatch) {
        return viewportWidth >= Number(minWidthMatch[1]);
      }

      const maxWidthMatch = query.match(/max-width:\s*([\d.]+)px/);

      if (maxWidthMatch) {
        return viewportWidth <= Number(maxWidthMatch[1]);
      }
    }

    if (query.includes(`max-width:${layout.phoneMaxWidth}px`)) {
      return isPhone;
    }

    if (query.includes(`min-width:${layout.wideMinWidth}px`)) {
      return isWideDesktop;
    }

    if (query.includes(`min-width:${layout.desktopMinWidth}px`)) {
      return isDesktop;
    }

    return false;
  });
};
