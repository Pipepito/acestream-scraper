import React from 'react';
import { MemoryRouter, type MemoryRouterProps } from 'react-router-dom';

export const TestMemoryRouter: React.FC<MemoryRouterProps> = ({ children, ...props }) => (
  <MemoryRouter {...props}>
    {children}
  </MemoryRouter>
);
