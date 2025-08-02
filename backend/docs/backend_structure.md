# **Backend Folder Structure Overview**

## **🏗️ Main Directory Structure**

The backend follows a **clean architecture** pattern with clear separation of concerns:

### **📁 Root Level**
- **`src/`** - Main application source code
- **`requirements/`** - Python dependencies
- **`tests/`** - Test suites (unit & integration)
- **`docs/`** - Documentation
- **`docker/`** - Docker configuration
- **`scripts/`** - Utility scripts
- **`secrets/`** - Configuration files
- **`logs/`** - Application logs

## **🔧 Core Application Structure (`src/`)**

### **📁 API Layer (`src/api/`)**
- **`routes/`** - HTTP endpoints organized by feature:
  - `ai/` - AI-related endpoints
  - `auth.py` - Authentication routes
  - `user.py` - User management
  - `lessons.py` - Lesson management
  - `exercise.py` - Exercise handling
  - `game.py` - Game mechanics
  - `profile.py` - User profiles
  - `settings.py` - User settings
  - `support.py` - Support features
  - `translate.py` - Translation services
  - `admin.py` - Admin functionality
  - `debug.py` - Debug endpoints
- **`middleware/`** - Request/response processing
- **`schemas/`** - Data validation schemas
- **`templates/`** - HTML templates

### **📁 Features Layer (`src/features/`)**
Organized by business domain:

- **`ai/`** - AI integration & intelligence:
  - `generation/` - Content generation
  - `evaluation/` - AI evaluation logic
  - `memory/` - Spaced repetition system
  - `prompts/` - AI prompt templates
  - `gap_fill_check.py` - Exercise AI logic
  - `feedback_helpers.py` - AI feedback system

- **`auth/`** - Authentication & authorization
- **`user/`** - User management & analytics
- **`lessons/`** - Lesson content & progress
- **`exercise/`** - Exercise management
- **`vocabulary/`** - Vocabulary handling
- **`grammar/`** - Grammar detection & analysis
- **`game/`** - Game mechanics & logic
- **`translation/`** - Translation services
- **`profile/`** - User profile management
- **`settings/`** - User settings & preferences
- **`support/`** - Support & help features
- **`admin/`** - Administrative functions
- **`debug/`** - Debugging utilities
- **`progress/`** - Progress tracking

### **📁 Core Layer (`src/core/`)**
- **`database/`** - Database connections & migrations
- **`services/`** - Core business logic services
- **`utils/`** - General utilities & helpers
- **`imports.py`** - Centralized import management

### **📁 Scripts (`scripts/`)**
- **`migration_script.py`** - Database schema creation and updates

### **📁 External Layer (`src/external/`)**
- **`mistral/`** - AI API integration
- **`redis/`** - Caching layer
- **`tts/`** - Text-to-speech integration

### **📁 Shared Layer (`src/shared/`)**
- **`constants.py`** - Application constants
- **`exceptions.py`** - Custom exceptions
- **`types.py`** - Type definitions

### **📁 Configuration (`src/config/`)**
- **`app.py`** - Flask application configuration
- **`blueprint.py`** - Blueprint configuration
- **`extensions.py`** - Extension configuration

## **🎯 Key Application Files**

- **`src/main.py`** - Application entry point (primary)
- **`src/app.py`** - Backward compatibility module
- **`src/core/imports.py`** - Centralized import management

## **🔍 Architecture Benefits**

This structure provides:
- **✅ Clear separation of concerns**
- **✅ Feature-based organization**
- **✅ Scalable architecture**
- **✅ Easy testing & maintenance**
- **✅ Clean dependency management**

## **📋 Detailed Component Breakdown**

### **API Routes (`src/api/routes/`)**
Each route file handles specific HTTP endpoints:

- **`ai/`** - AI-powered features including exercise generation, feedback, and lesson creation
- **`auth.py`** - User authentication, registration, and session management
- **`user.py`** - User CRUD operations, profile management, and analytics
- **`lessons.py`** - Lesson content management and delivery
- **`lesson_progress.py`** - Progress tracking and completion status
- **`exercise.py`** - Exercise generation, submission, and evaluation
- **`game.py`** - Interactive learning games and activities
- **`profile.py`** - User profile customization and preferences
- **`settings.py`** - Application and user settings management
- **`support.py`** - Help system and user support features
- **`translate.py`** - Translation services and language tools
- **`admin.py`** - Administrative functions and user management
- **`debug.py`** - Development and debugging utilities

### **AI Features (`src/features/ai/`)**
The AI module is the core intelligence of the application:

- **`generation/`** - Content generation for exercises, lessons, and feedback
- **`evaluation/`** - AI-powered assessment of user responses and progress
- **`memory/`** - Spaced repetition algorithm for vocabulary retention
- **`prompts/`** - AI prompt templates and conversation management
- **`gap_fill_check.py`** - Exercise-specific AI logic and generation
- **`feedback_helpers.py`** - Intelligent feedback generation and analysis

### **Core Services (`src/core/`)**
Foundation services that support the entire application:

- **`database/`** - Database connection management, migrations, and ORM setup
- **`services/`** - Core business logic and data processing services
- **`utils/`** - Shared utilities for common operations across the application

### **External Integrations (`src/external/`)**
Third-party service integrations:

- **`mistral/`** - Integration with Mistral AI for advanced language processing
- **`redis/`** - Caching layer for improved performance
- **`tts/`** - Text-to-speech functionality for audio learning

## **🚀 Getting Started**

1. **Install dependencies**:
   ```bash
   pip install -r requirements/requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   python src/main.py
   ```

## **🧪 Testing**

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## **📚 Additional Documentation**

- `api.md` - API documentation
- `architecture.md` - Detailed architecture overview
- `deployment.md` - Deployment guide

---

The backend is designed as a **Flask-based REST API** with comprehensive AI integration for German language learning, featuring spaced repetition, exercise generation, and intelligent feedback systems.
