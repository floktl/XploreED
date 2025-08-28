#!/bin/bash

# Script to fix React imports with hooks in JSX files
# This changes "import React, { useState } from 'react'" to "import { useState } from 'react'"

echo "Fixing React hook imports in JSX files..."

# List of files that need fixing
files=(
    "src/components/features/auth/NameInput/Forms/LoginForm.jsx"
    "src/components/features/admin/AdminDashboard/AdminDashboard.jsx"
    "src/components/features/ai/AIExercise/Progress/ExerciseProgress.jsx"
    "src/components/features/lessons/LessonEditor/LessonEditor.jsx"
    "src/pages/Core/AdminLoginView.jsx"
    "src/pages/Core/MenuView.jsx"
    "src/pages/Core/LessonView.jsx"
    "src/pages/Core/LessonsView.jsx"
    "src/pages/Core/LessonEditView.jsx"
    "src/pages/Core/GrammarMapView.jsx"
    "src/pages/Core/TopicMemoryView.jsx"
    "src/pages/Core/VocabularyView.jsx"
    "src/pages/Core/VocabTrainerView.jsx"
    "src/pages/Core/TranslatorView.jsx"
    "src/pages/Core/SettingsView.jsx"
    "src/pages/game/LevelGameView.jsx"
    "src/pages/game/PlacementTestView.jsx"
    "src/pages/game/LevelGuessView.jsx"
    "src/pages/game/LevelUpTestView.jsx"
    "src/pages/profile/ProfileView.jsx"
    "src/pages/profile/ProfileStatsView.jsx"
    "src/pages/support/Legal/SupportView.jsx"
    "src/pages/support/Legal/TermsOfServiceView.jsx"
    "src/pages/ai/AIFeedbackView.jsx"
    "src/pages/ai/AIWeaknessLessonView.jsx"
    "src/pages/ai/AIReadingView.jsx"
)

# Process each file
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "Processing: $file"
        # Replace "import React, {" with "import {"
        sed -i '' 's/import React, {/import {/g' "$file"
    else
        echo "Warning: File not found: $file"
    fi
done

echo "React hook import cleanup completed!"
