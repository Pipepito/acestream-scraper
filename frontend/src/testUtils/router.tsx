import React from 'react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';

const routerFutureFlags = {
  v7_startTransition: true,
  v7_relativeSplatPath: true,
} as const;

export const TestMemoryRouter: React.FC<MemoryRouterProps> = ({ children, ...props }) => (
  <MemoryRouter future={routerFutureFlags} {...props}>
    {children}
  </MemoryRouter>
);

export { routerFutureFlags };
