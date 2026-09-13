# TypeScript Standards for Frontend Development

## TypeScript-Only Policy

As of v2, the Acestream Scraper frontend is developed exclusively with TypeScript. JavaScript files (.js, .jsx) are no longer allowed in the codebase.

## Rationale

- **Type Safety**: Prevents runtime errors through compile-time checks
- **Better IDE Support**: Improved autocomplete, refactoring, and navigation
- **Better Documentation**: Self-documenting code through types
- **Team Efficiency**: Easier onboarding and understanding of codebase
- **Maintainability**: Easier to refactor and extend code

## Standards

1. **Files and Extensions**:
   - All React components must use `.tsx` extension
   - All other TypeScript files must use `.ts` extension
   - No `.js` or `.jsx` files are allowed

2. **Type Definitions**:
   - All function parameters and return types must be explicitly typed
   - All component props must be defined in a named interface
   - All component state must be typed
   - Avoid using `any` type

3. **React Component Pattern**:
   ```tsx
   import React from 'react';
   
   interface MyComponentProps {
     title: string;
     onClick: () => void;
   }
   
   export const MyComponent: React.FC<MyComponentProps> = ({ title, onClick }) => {
     return (
       <div onClick={onClick}>
         {title}
       </div>
     );
   };
   ```

4. **API Types**:
   - Use types generated from OpenAPI specification
   - All API requests and responses must be properly typed

## Tools

- ESLint with TypeScript rules
- Prettier for consistent formatting
- TypeScript compiler with strict mode enabled

## Migration Path

For any existing JavaScript files:

1. Rename file extension to `.tsx` for React components or `.ts` for utilities
2. Add proper type definitions
3. Fix any type errors
4. Remove any uses of `any` by providing proper types

## Example: Converting JavaScript to TypeScript

### Before (JavaScript):

```javascript
import React, { useState } from 'react';

const UserProfile = (props) => {
  const [isEditing, setIsEditing] = useState(false);
  
  const handleEdit = () => {
    setIsEditing(!isEditing);
    if (props.onEditChange) {
      props.onEditChange(!isEditing);
    }
  };

  return (
    <div>
      <h2>{props.name}</h2>
      <p>{props.email}</p>
      <button onClick={handleEdit}>
        {isEditing ? 'Cancel' : 'Edit'}
      </button>
    </div>
  );
};

export default UserProfile;
```

### After (TypeScript):

```typescript
import React, { useState } from 'react';

interface UserProfileProps {
  name: string;
  email: string;
  onEditChange?: (isEditing: boolean) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ name, email, onEditChange }) => {
  const [isEditing, setIsEditing] = useState<boolean>(false);
  
  const handleEdit = (): void => {
    setIsEditing(!isEditing);
    if (onEditChange) {
      onEditChange(!isEditing);
    }
  };

  return (
    <div>
      <h2>{name}</h2>
      <p>{email}</p>
      <button onClick={handleEdit}>
        {isEditing ? 'Cancel' : 'Edit'}
      </button>
    </div>
  );
};

export default UserProfile;
```
