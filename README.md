# German Class Tool

A web application for learning German with AI-powered translation and feedback.

## Overview

This application helps users learn German through interactive translation exercises, vocabulary building, and supportive feedback. It features:

- AI-powered translation using Google's Gemini API
- Supportive feedback focused on learner well-being
- Dictionary-based fallback for offline use
- User progress tracking
- Interactive sentence ordering games
- Vocabulary building tools

## Recent Improvements

### Gemini AI Integration

The application now uses Google's Gemini AI for translation and feedback, providing a more natural and supportive learning experience:

1. **AI-Powered Translation**
   - Replaced dictionary-based translation with Gemini AI
   - Provides more natural, conversational German translations
   - Maintains dictionary-based fallback if API is unavailable

2. **Well-being Focused Feedback**
   - AI is trained to focus on the well-being of German language learners
   - Provides encouraging, constructive feedback
   - Highlights what students did well, even when there are mistakes
   - Explains grammar concepts in a friendly, accessible way

3. **AI Confidence Indicators**
   - Shows confidence levels for both translations and feedback
   - Helps users understand when the AI is certain vs. making an educated guess
   - Color-coded indicators with helpful tooltips
   - Improves transparency and builds trust in the AI assistance

4. **Pronunciation Features**
   - Text-to-speech functionality for German translations
   - Speech recognition for pronunciation practice
   - Dedicated pronunciation practice module with difficulty levels
   - Uses browser's native Web Speech API (no external API required)

5. **Learning Analytics Dashboard**
   - Comprehensive analytics dashboard for tracking progress
   - Daily activity heatmap showing learning patterns
   - Streak tracking to encourage consistent practice
   - Detailed statistics on accuracy and time spent
   - Achievement system with badges for reaching milestones

6. **Technical Implementation**
   - Added Google Generative AI Python package
   - Created a dedicated Gemini translator module
   - Implemented error handling and fallback mechanisms
   - Updated translation routes to use the new AI capabilities
   - Added analytics tracking and achievement system

## Project Structure

```
german_class_tool/
├── backend/
│   ├── app.py                    # Main Flask application
│   ├── game/
│   │   └── german_sentence_game.py  # Game logic and translation
│   ├── routes/
│   │   ├── translate.py          # Translation API endpoints
│   │   └── ...                   # Other route modules
│   ├── utils/
│   │   ├── gemini_translator.py  # Gemini AI integration
│   │   └── ...                   # Other utility modules
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/           # React components
│   │   ├── api.js                # API client functions
│   │   └── ...                   # Other frontend files
│   └── ...                       # Frontend configuration
└── ...                           # Project configuration files
```

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API key

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/floktl/german_class_tool.git
   cd german_class_tool
   ```

2. Create a `.env` file in the `backend/secrets/` directory:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ADMIN_PASSWORD=your_admin_password
   DB_FILE=user_data.db
   FRONTEND_URL=http://localhost:5173
   ```

3. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend:
   ```bash
   cd backend
   python app.py
   ```

2. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at `http://localhost:5173`

## Usage

1. **Translation Practice**
   - Enter an English sentence
   - Provide your German translation
   - Receive AI-powered feedback on your attempt
   - Listen to correct pronunciation with text-to-speech

2. **Pronunciation Practice**
   - Listen to German phrases with text-to-speech
   - Practice speaking with speech recognition
   - Get instant feedback on your pronunciation
   - Choose from different difficulty levels

3. **Learning Analytics**
   - View comprehensive statistics on your learning progress
   - Track your daily activity with a visual heatmap
   - Maintain and monitor your learning streak
   - Earn achievements for reaching learning milestones

4. **Sentence Ordering Game**
   - Arrange scrambled German words into correct order
   - Progress through increasingly difficult levels

5. **Vocabulary Building**
   - Track words you've encountered
   - Review your vocabulary list

## Development

### Git Workflow

- Use descriptive commit messages with prefixes:
  - `Add:` for new features
  - `Edit:` for modifications
  - `Del:` for removals

- Work on feature branches and merge to main when complete

### API Documentation

#### Translation API

- `POST /api/translate`
  - Request: `{ "english": "English text", "student_input": "Student's German translation" }`
  - Response: `{ "german": "Correct German", "feedback": "Feedback with HTML formatting", "translation_confidence": 85, "feedback_confidence": 90 }`

## Future Improvements

### 1. Advanced Learning Recommendations
- Implement AI-driven personalized learning recommendations
- Suggest specific exercises based on user performance data
- Create adaptive difficulty levels that adjust to user progress
- Provide custom vocabulary lists based on user interests and goals

### 2. Personalized Learning Paths
- Develop an AI-driven system to recommend personalized exercises
- Adapt difficulty based on user performance and learning style
- Create custom vocabulary lists based on user interests and goals
- Implement spaced repetition for vocabulary review
- Provide personalized study plans with daily goals

### 3. Example Sentences Database
- Build a database of example sentences for each vocabulary word
- Show contextual usage of words in different scenarios
- Allow filtering by difficulty level, topic, and grammar concepts
- Include cultural notes and usage tips for each example
- Enable users to save favorite examples for later review

### 4. Collaborative Learning Features
- Add peer review functionality for translations
- Create a community forum for language learning discussions
- Implement a system for sharing custom exercises
- Add a tandem learning feature to connect German and English speakers
- Create group challenges and leaderboards

### 5. Advanced Grammar Exercises
- Develop interactive exercises for specific grammar concepts
- Create visual grammar explanations with examples
- Implement a grammar checker for user input
- Provide contextual grammar tips based on common mistakes
- Add progressive grammar lessons with increasing difficulty
