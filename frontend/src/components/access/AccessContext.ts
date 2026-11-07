import { createContext, useContext } from 'react';
import type { AccessStatus } from '../../services/accessService';
export const AccessContext = createContext<{ status: AccessStatus; refresh: () => Promise<void> } | null>(null);
export const useAccess = () => useContext(AccessContext);
