# XplorED - Backend (New Structure)

This is the restructured backend for the XplorED application, organized with clean architecture principles.

## 🏗️ Architecture Overview

### **API Layer** (`src/api/`)
- **Routes**: HTTP endpoints organized by feature
- **Middleware**: Authentication, logging, error handling
- **Schemas**: Request/response validation schemas

### **Core Layer** (`src/core/`)
- **Database**: Connection management and migrations
- **Services**: Core business logic services
- **Utils**: General utilities and helpers

### **Features Layer** (`src/features/`)
- **Auth**: Authentication and authorization
- **User**: User management
- **Exercise**: Exercise generation and management
- **AI**: AI integration, evaluation, and memory
- **Vocabulary**: Vocabulary management
- **Grammar**: Grammar detection and analysis
- **Game**: Game mechanics
- **Progress**: Progress tracking and level management

### **External Layer** (`src/external/`)
- **Mistral**: AI API integration
- **Redis**: Caching layer
- **TTS**: Text-to-speech integration

### **Shared Layer** (`src/shared/`)
- **Constants**: Application constants
- **Exceptions**: Custom exceptions
- **Types**: Type definitions and data structures

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements/base.txt
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

## 📁 Key Files

- `src/main.py`: Application entry point
- `src/config/app.py`: Flask app configuration
- `src/api/routes/`: HTTP endpoints
- `src/features/ai/`: AI functionality
- `src/features/ai/memory/`: Spaced repetition system

## 🔧 Development

### **Adding New Features**
1. Create feature folder in `src/features/`
2. Add `models.py`, `repository.py`, `service.py`
3. Add routes in `src/api/routes/`
4. Add tests in `tests/`

### **AI Integration**
- Prompts: `src/features/ai/prompts/`
- Evaluation: `src/features/ai/evaluation/`
- Generation: `src/features/ai/generation/`
- Memory: `src/features/ai/memory/`

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## 📚 Documentation

- `docs/api.md`: API documentation
- `docs/architecture.md`: Architecture overview
- `docs/deployment.md`: Deployment guide

## 🔄 Migration from Old Structure

This structure replaces the old `backend/` folder. The migration preserves all functionality while organizing code into a clean, maintainable structure.

### **Key Improvements**
- **Clear separation of concerns**
- **Feature-based organization**
- **Better testability**
- **Scalable architecture**
- **Improved maintainability**
