Here is an adjusted and expanded `Agents.md` guide that includes **backend Python standards** alongside the existing frontend TypeScript/React standards. It also incorporates coding discipline based on the **42 coding school philosophy**, such as readability, modularity, and minimal dependencies.

---

# Project Agents.md Guide for OpenAI Codex

This `Agents.md` file provides comprehensive guidance for OpenAI Codex and other AI agents contributing to this fullstack codebase, including frontend React/Next.js and backend Python (Flask).

---

## 🔹 Project Structure for OpenAI Codex Navigation

### Frontend (React/Next.js)

* `/src`

  * `/components`: Functional React components (small, reusable, typed)
  * `/pages`: Next.js route definitions
  * `/styles`: Tailwind CSS configurations
  * `/utils`: Utility modules and shared logic
* `/public`: Static assets (Codex should not modify these)

### Backend (Flask)

* `/backend`

  * `/routes`: Flask Blueprints for each API domain (e.g., `auth.py`, `ai.py`)
  * `/utils`: Utility functions and modules (`helpers.py`, `spaced_repetition/`)
  * `/database`: SQLite wrapper functions (`fetch_one`, `insert_row`, etc.)
  * `/models`: Optional ORM-style data structure helpers
  * `/tests`: Python unit/integration tests using `pytest`

---

## ✅ General Coding Standards

### For All Code (Python + TypeScript)

* Follow modular architecture — **no giant files**, extract reusable logic into helpers
* Use meaningful, descriptive function and variable names
* Avoid global state and side effects in utilities
* Add docstrings or comments for any logic that’s not obvious
* Minimize unnecessary abstraction — **simple > clever**

---

## ⚛️ Frontend (React / TypeScript) — OpenAI Codex Rules

### React Components

* Use functional components with hooks (`useState`, `useEffect`, etc.)
* Split logic-heavy components into subcomponents or hooks
* Always use `PascalCase.tsx` for file names

### Typing and Props

* Use `interface` or `type` for prop typing
* All components must have explicit prop types — no implicit `any`

### Styling

* Use **Tailwind CSS** (utility-first) unless a clear exception exists
* Never use inline styles unless required for dynamic styling

---

## 🐍 Backend (Python / Flask) — OpenAI Codex Rules

### Code Layout and Imports

* All modules must use **absolute imports**
* Use PEP8 naming conventions:

  * `snake_case` for variables and functions
  * `PascalCase` for class names
* Group related logic into modules: `routes`, `utils`, `database`

### Flask Guidelines

* Use `Blueprint`s to separate route domains
* Use decorators like `@require_user()` for auth handling
* Avoid using `current_app`, `request`, or `g` outside app/request context

### Thread Safety

* Wrap all background threads in `with app.app_context():`
* Avoid accessing global Flask objects (`request`, `current_app`) in threads

### Logging

* Use `current_app.logger` for all internal logs
* Print debug output only when necessary and with `flush=True`

### 42 Coding Standards for Python

* No unused imports or dead code
* No magic numbers — use constants or config
* Code must run **without crashing**, and all branches must be reachable
* Keep functions short and with a single responsibility
* Group error handling at function level with clear try/except blocks
* Never rely on external frameworks or packages unless approved


## ✅ Pull Request Guidelines for OpenAI Codex

All PRs (whether backend or frontend) must:

1. Include a **clear description** of the changes
2. Reference any related issues
3. Pass all tests
4. Pass all linters/type-checkers
5. Be **focused on a single logical concern**
6. Follow the naming convention: `feature/<feature-name>` or `fix/<issue-name>`
