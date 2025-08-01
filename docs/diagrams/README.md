# 📊 Project Diagrams

This folder contains Draw.io diagrams that document the architecture and design of the German Class Tool project.

## 📋 Diagram Files

### **`database_structure.drawio`** (539KB)
- **Purpose**: Database schema and table relationships
- **Description**: Shows the complete database structure including all tables, columns, and relationships
- **Tables**: users, results, vocab_log, lesson_content, lesson_blocks, lesson_progress, support_feedback, exercise_submissions, topic_memory, ai_user_data

### **`exercise_gen.drawio`** (114KB)
- **Purpose**: Exercise generation flow and logic
- **Description**: Illustrates how AI exercises are generated, processed, and delivered to users
- **Components**: AI integration, exercise creation, user interaction flow

### **`schematic.drawio`** (1.6MB)
- **Purpose**: Overall system architecture and component relationships
- **Description**: High-level system design showing how frontend, backend, database, and external services interact
- **Components**: React frontend, Flask backend, SQLite database, AI services, Redis cache

## 🛠️ How to Use

1. **Open with Draw.io**: Use [draw.io](https://app.diagrams.net/) or the desktop application
2. **Edit**: Make changes and save back to this folder
3. **Export**: Export as PNG, SVG, or PDF for documentation
4. **Version Control**: Changes are tracked in Git

## 📝 Notes

- All diagrams are in Draw.io format (`.drawio`)
- Keep diagrams up to date with code changes
- Use consistent naming conventions
- Consider exporting static versions for documentation

## 🔗 Related Documentation

- **Backend Structure**: See `../backend_structure.md`
- **API Documentation**: See `../api.md`
- **Deployment Guide**: See `../deployment.md`
