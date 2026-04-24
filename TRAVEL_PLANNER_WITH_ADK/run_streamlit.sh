#!/bin/bash
# Quick Start Script for Travel Planner Streamlit App

echo "🌍 Travel Planner Chatbot - Quick Start"
echo "========================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Creating .env file... Please add your Deepseek API key."
    echo "DEEPSEEK_API_KEY=your_api_key_here" > .env
    echo "📝 Created .env - Update it with your Deepseek API key from: https://platform.deepseek.com/"
    echo ""
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements_streamlit.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Verify environment
echo ""
echo "🔍 Verifying setup..."

# Check for travel_planner module
if [ -d "travel_planner" ]; then
    echo "✅ travel_planner module found"
else
    echo "❌ travel_planner module not found"
    exit 1
fi

# Check for required files
for file in agent.py supporting_agents.py tools.py; do
    if [ -f "travel_planner/$file" ]; then
        echo "✅ Found travel_planner/$file"
    else
        echo "❌ Missing travel_planner/$file"
        exit 1
    fi
done

echo ""
echo "✅ All checks passed!"
echo ""
echo "🚀 Starting Streamlit app..."
echo "The app will open in your browser at http://localhost:8501"
echo ""

# Start the app
streamlit run streamlit_app.py
