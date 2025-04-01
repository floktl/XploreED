#!/bin/bash

echo "🔧 Setting up virtual environment..."

# Step 1: Create the virtual environment if it doesn't exist
if [ ! -d "$HOME/german_env" ]; then
    python3 -m venv "$HOME/german_env"
    echo "✅ Virtual environment created at ~/german_env"
else
    echo "ℹ️ Using existing virtual environment at ~/german_env"
fi

# Step 2: Activate the environment
source "$HOME/german_env/bin/activate"

# Step 3: Upgrade pip silently
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Step 4: Install dependencies silently
echo "📦 Installing dependencies..."
pip install --quiet "numpy<2" torch transformers sentencepiece colorama

# Step 5: Run the German sentence game
echo "🚀 Launching the German Sentence Game..."
SCRIPT_PATH="$(dirname "$0")/german_sentence_game.py"
python "$SCRIPT_PATH"
