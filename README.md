# XploreED

A comprehensive German language learning platform powered by AI, featuring interactive exercises, spaced repetition, and personalized learning experiences.
Please note, that this is only a prototype to showcase the functions, the frontend is obviously not production ready, this project is currently paused, will be continued soon.

<table style="border-collapse:collapse;border-spacing:0;width:100%;margin:0;padding:0;">
  <tr>
    <td style="padding:0;margin:0;border:none;width:50%;">
      <video src="https://github.com/user-attachments/assets/378b2ae3-37ad-4ca0-bff1-2e81cfd4666a?raw=1"
             controls playsinline muted style="display:block;width:100%;height:auto;border:none;margin:0;padding:0;"></video>
    </td>
    <td style="padding:0;margin:0;border:none;width:50%;">
      <video src="https://github.com/user-attachments/assets/e4779743-d622-4e94-889c-884028de8c4c?raw=1"
             controls playsinline muted style="display:block;width:100%;height:auto;border:none;margin:0;padding:0;"></video>
    </td>
  </tr>
</table>
## ✨ Features

### 🤖 AI-Powered Learning
- **Smart Exercise Generation**: AI creates personalized German exercises based on your skill level
- **Intelligent Feedback**: Get detailed explanations and corrections for your answers
- **Adaptive Learning**: Exercises adjust to your progress and weak areas
- **Real-time AI Chat**: Ask questions and get instant German language help

### 📚 Interactive Lessons
- **Structured Content**: Organized lessons covering grammar, vocabulary, and conversation
- **Progress Tracking**: Monitor your learning journey with detailed progress analytics
- **Block-based Learning**: Lessons broken into manageable chunks for better retention

### 🎯 Spaced Repetition System
- **Smart Vocabulary Training**: Advanced spaced repetition algorithm for optimal memory retention
- **Topic Memory**: Tracks your understanding of grammar topics and concepts
- **Weakness Identification**: Automatically identifies areas that need more practice

### 🎮 Gamified Learning
- **Level-based Progression**: Advance through German proficiency levels (A1-C2)
- **Exercise Types**: Multiple exercise formats including:
  - Gap-fill exercises
  - Translation challenges
  - Grammar exercises
  - Reading comprehension
- **Performance Analytics**: Detailed statistics on your learning progress

### 👤 User Management
- **Personal Profiles**: Track your learning statistics and achievements
- **Admin Dashboard**: Comprehensive user management and analytics
- **Secure Authentication**: Safe user registration and login system

### 🌐 Modern Technology
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Real-time Updates**: Live streaming of AI responses for instant feedback
- **Dark/Light Mode**: Comfortable learning experience in any environment

## 🏗️ Technical Architecture

- **Frontend**: React with modern UI components and responsive design
- **Backend**: Flask API with comprehensive German language processing
- **AI Integration**: Mistral AI for exercise generation and feedback
- **Database**: SQLite with advanced schema for learning analytics
- **Text-to-Speech**: ElevenLabs integration for pronunciation practice

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/floktl/XploreED.git
   cd XploreED
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Run with Docker**
   ```bash
   docker compose -f docker-compose.dev.yml up
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:5050

## 📖 Documentation

For detailed technical documentation:
- **Database Structure**: `docs/diagrams/database_structure.drawio`
- **Exercise Generation Flow**: `docs/diagrams/exercise_gen.drawio`
- **System Architecture**: `docs/diagrams/schematic.drawio`
- **Development Guide**: `docs/AGENTS.md`
