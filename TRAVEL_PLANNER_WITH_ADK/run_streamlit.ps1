# Quick Start Script for Travel Planner Streamlit App (Windows)

Write-Host "🌍 Travel Planner Chatbot - Quick Start (Windows)" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Check if Python is installed
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if ($null -eq $pythonPath) {
    Write-Host "❌ Python is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version
Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green

# Check if .env file exists
if (!(Test-Path ".env")) {
    Write-Host ""
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env file... Please add your Deepseek API key." -ForegroundColor Yellow
    Add-Content ".env" "DEEPSEEK_API_KEY=your_api_key_here"
    Write-Host "📝 Created .env - Update it with your Deepseek API key from: https://platform.deepseek.com/" -ForegroundColor Yellow
    Write-Host ""
}

# Install dependencies
Write-Host ""
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements_streamlit.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Verify environment
Write-Host ""
Write-Host "🔍 Verifying setup..." -ForegroundColor Cyan

# Check for travel_planner module
if (Test-Path "travel_planner") {
    Write-Host "✅ travel_planner module found" -ForegroundColor Green
} else {
    Write-Host "❌ travel_planner module not found" -ForegroundColor Red
    exit 1
}

# Check for required files
$requiredFiles = @("agent.py", "supporting_agents.py", "tools.py")
foreach ($file in $requiredFiles) {
    $filePath = "travel_planner\$file"
    if (Test-Path $filePath) {
        Write-Host "✅ Found travel_planner\$file" -ForegroundColor Green
    } else {
        Write-Host "❌ Missing travel_planner\$file" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "✅ All checks passed!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Starting Streamlit app..." -ForegroundColor Cyan
Write-Host "The app will open in your browser at http://localhost:8501" -ForegroundColor Cyan
Write-Host ""

# Start the app
streamlit run streamlit_app.py
