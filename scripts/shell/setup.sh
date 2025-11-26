#!/bin/bash
# Bensley Intelligence Platform - Quick Setup Script

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Bensley Intelligence Platform - Setup                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Python 3.11+ required. You have: $python_version"
    echo "   Install Python 3.11+: https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "🔧 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  IMPORTANT: Edit .env file with your actual values!"
    echo "   Especially: DATABASE_PATH and OPENAI_API_KEY"
fi

# Move existing scripts to backend/core
echo ""
echo "📁 Organizing existing scripts..."
if [ -f "email_processor.py" ] && [ ! -f "backend/core/email_processor.py" ]; then
    mv *.py backend/core/ 2>/dev/null || true
    echo "✅ Scripts moved to backend/core/"
fi

# Create __init__.py files
echo ""
echo "🔧 Creating Python package structure..."
touch backend/__init__.py
touch backend/api/__init__.py
touch backend/core/__init__.py
touch backend/services/__init__.py
touch backend/models/__init__.py
touch backend/utils/__init__.py
echo "✅ Package structure created"

# Test API startup
echo ""
echo "🧪 Testing API..."
python3 -c "from backend.api.main import app; print('✅ API imports successfully')" || {
    echo "⚠️  API test failed - but that's okay, you may need to configure database path"
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Setup Complete! 🎉                                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your actual values:"
echo "   nano .env"
echo ""
echo "2. Start the API server:"
echo "   python3 backend/api/main.py"
echo "   or"
echo "   uvicorn backend.api.main:app --reload"
echo ""
echo "3. Open your browser to:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Check the QUICKSTART_ROADMAP.md for next steps:"
echo "   cat QUICKSTART_ROADMAP.md"
echo ""
echo "Need help? Check:"
echo "  - QUICKSTART_ROADMAP.md (12-week plan)"
echo "  - README.md (quick reference)"
echo "  - docs/ folder (detailed guides)"
echo ""
