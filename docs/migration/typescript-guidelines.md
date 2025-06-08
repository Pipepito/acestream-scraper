# TypeScript Guidelines - Acestream Scraper v2

This document outlines the TypeScript coding standards and practices for the Acestream Scraper v2 frontend.

## TypeScript Standards

1. **TypeScript Only**
   - All frontend code must be written in TypeScript
   - No JavaScript (.js) files are allowed
   - All file extensions should be `.ts` or `.tsx` for React components

2. **Strict Type Checking**
   - Enable strict mode in tsconfig.json
   - No use of `any` type - be explicit with types
   - Use interfaces and types for all data structures

3. **React Component Types**
   - Use React.FC for functional components with explicit prop interfaces
   - Example:
     ```tsx
     interface ButtonProps {
       label: string;
       onClick: () => void;
       disabled?: boolean;
     }
     
     const Button: React.FC<ButtonProps> = ({ label, onClick, disabled }) => {
       // Component implementation
     };
     ```

4. **API Communication**
   - All API requests should be typed using the appropriate DTOs
   - Use the services layer for all API calls
   - All API responses and errors should be properly typed

5. **State Management**
   - Use typed React hooks
   - All state should be properly typed
   - Use React Query for server state management with proper types

## Code Organization

1. **Directory Structure**
   ```
   src/
   ├── api/            # Auto-generated API client
   ├── components/     # Reusable UI components
   ├── hooks/          # Custom React hooks
   ├── pages/          # Page-level components
   ├── services/       # API service adapters
   ├── types/          # TypeScript type definitions
   ├── utils/          # Utility functions
   └── index.tsx       # Application entry point
   ```

2. **Naming Conventions**
   - PascalCase for React components: `ChannelTable.tsx`
   - camelCase for utility functions: `formatDate.ts`
   - Use `.ts` for non-React files and `.tsx` for React components

## Development Workflow

1. **Building for Backend Integration**
   - Run `npm run build:backend` to build and copy frontend to backend
   - The backend will serve the frontend from `/` endpoint
   - All API requests will go to `/api` path

2. **API Types**
   - API types are defined in the services layer
   - Each entity should have corresponding DTOs for create, update, and response

3. **Documentation**
   - All exported components, functions, interfaces, and types should be documented with JSDoc comments

4. **Testing**
   - Write tests in TypeScript
   - All test files should use `.spec.ts` or `.spec.tsx` extensions
