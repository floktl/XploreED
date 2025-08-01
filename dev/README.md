# 🛠️ Development Tools

This folder contains development environment configurations and IDE settings.

## 📁 Contents

### **IDE Configurations**
- **`.cursor.mdc`** - Cursor IDE configuration and settings
- **`.vscode/`** - Visual Studio Code workspace settings and extensions
- **`.mypy_cache/`** - Python type checking cache (auto-generated)

## 🔧 Usage

These files are automatically used by their respective tools:
- **Cursor**: Uses `.cursor.mdc` for project-specific settings
- **VS Code**: Uses `.vscode/` for workspace configuration
- **MyPy**: Uses `.mypy_cache/` for type checking performance

## 📝 Notes

- These files are development-specific and not needed for production
- IDE configurations help maintain consistent development environment
- Cache files (`.mypy_cache/`) can be safely deleted and regenerated
