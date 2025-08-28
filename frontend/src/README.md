# Frontend Source Structure

This directory follows a feature-based architecture with clear separation of concerns.

## Directory Structure

```
src/
├── components/
│   ├── common/           # Reusable UI components
│   │   ├── Button/
│   │   ├── Modal/
│   │   ├── Card/
│   │   ├── ErrorBoundary/
│   │   ├── BlockContentRenderer/
│   │   ├── FeedbackBlock/
│   │   ├── PrettyFeedback/
│   │   ├── TextToSpeechBox/
│   │   └── index.ts
│   ├── layout/           # Layout components
│   │   ├── RootLayout/
│   │   ├── MenuNavigation/
│   │   ├── MenuSections/
│   │   └── index.ts
│   └── features/         # Feature-specific components
│       ├── auth/
│       ├── admin/
│       ├── lessons/
│       ├── ai/
│       ├── profile/
│       ├── vocabulary/
│       ├── game/
│       ├── settings/
│       ├── support/
│       └── index.ts
├── pages/                # Page-level components (not views)
│   ├── Core/
│   ├── AI/
│   ├── Game/
│   ├── Profile/
│   ├── support/
│   └── index.ts
├── hooks/                # Custom hooks
├── services/             # API and external services
├── utils/                # Utility functions
├── types/                # TypeScript definitions
├── constants/            # App constants
└── styles/               # Global styles
```

## Import Guidelines

### Components
```javascript
// Import from specific feature
import { NameInput } from './components/features/auth';
import { AdminDashboard } from './components/features/admin';

// Import common components
import { Button, Modal } from './components/common';

// Import layout components
import { RootLayout } from './components/layout';
```

### Pages
```javascript
// Import pages
import { MenuView, LessonsView } from './pages';
```

### Services
```javascript
// Import API services
import { getMe, getRole } from './services/api';
```

### Utilities
```javascript
// Import utilities
import { useClickOutside, useMediaQuery } from './utils';
```

## Migration Notes

- All component imports have been updated to use the new structure
- Feature-specific components are now organized by domain
- Common UI components are centralized for reusability
- Layout components are separated for better organization
- Pages (formerly views) are now in their own directory
- Services are centralized for API calls
- Utilities are organized for better discoverability
