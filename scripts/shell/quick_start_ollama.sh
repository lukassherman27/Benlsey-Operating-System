#!/bin/bash
################################################################################
# BENSLEY INTELLIGENCE - OLLAMA QUICK START
# Sets up local AI model in 5 minutes with zero training
################################################################################

set -e  # Exit on error

echo "================================================================================"
echo "BENSLEY INTELLIGENCE - OLLAMA QUICK START"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Install Ollama (local model runtime)"
echo "  2. Download Mistral-7B model"
echo "  3. Create custom model with Bensley business context"
echo "  4. Test the model with sample email"
echo ""
echo "Time required: ~5 minutes (depending on download speed)"
echo "No training needed - works immediately!"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

################################################################################
# STEP 1: Install Ollama
################################################################################

echo ""
echo "================================================================================"
echo "STEP 1: Installing Ollama..."
echo "================================================================================"

if command -v ollama &> /dev/null; then
    echo "✓ Ollama already installed"
else
    echo "Installing Ollama via Homebrew..."
    brew install ollama
    echo "✓ Ollama installed"
fi

################################################################################
# STEP 2: Start Ollama Server
################################################################################

echo ""
echo "================================================================================"
echo "STEP 2: Starting Ollama server..."
echo "================================================================================"

# Check if already running
if pgrep -x "ollama" > /dev/null; then
    echo "✓ Ollama server already running"
else
    echo "Starting Ollama server in background..."
    ollama serve > /tmp/ollama.log 2>&1 &
    sleep 2
    echo "✓ Ollama server started"
fi

################################################################################
# STEP 3: Download Mistral Model
################################################################################

echo ""
echo "================================================================================"
echo "STEP 3: Downloading Mistral-7B model..."
echo "================================================================================"
echo "This may take 2-3 minutes (4GB download)..."

ollama pull mistral
echo "✓ Mistral-7B downloaded"

################################################################################
# STEP 4: Export Training Data
################################################################################

echo ""
echo "================================================================================"
echo "STEP 4: Exporting business context..."
echo "================================================================================"

cd "$(dirname "$0")"

# Check if training data already exists
if [ -f ~/Desktop/BDS_SYSTEM/TRAINING_DATA/business_context.json ]; then
    echo "✓ Training data already exists"
else
    echo "Running export_training_data.py..."
    python3 export_training_data.py
fi

# Check if system prompt exists
if [ -f ~/Desktop/BDS_SYSTEM/LOCAL_MODELS/system_prompt.txt ]; then
    echo "✓ System prompt already exists"
else
    echo "Running fine_tune_model.py to generate system prompt..."
    python3 fine_tune_model.py
fi

################################################################################
# STEP 5: Create Custom Bensley Model
################################################################################

echo ""
echo "================================================================================"
echo "STEP 5: Creating custom Bensley model..."
echo "================================================================================"

# Create Modelfile with business context
cd ~/Desktop/BDS_SYSTEM/LOCAL_MODELS/

cat > Modelfile <<EOF
FROM mistral

SYSTEM """$(cat system_prompt.txt)"""

PARAMETER temperature 0.1
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
EOF

echo "✓ Modelfile created"

# Create custom model
echo "Building bensley-email-assistant model..."
ollama create bensley-email-assistant -f Modelfile
echo "✓ Custom model created"

################################################################################
# STEP 6: Test the Model
################################################################################

echo ""
echo "================================================================================"
echo "STEP 6: Testing model with sample email..."
echo "================================================================================"
echo ""

# Test with sample email
echo "Input:"
echo "------"
echo "Subject: Re: Fee proposal for MAL-24-02 - Maldives Luxury Resort"
echo "From: director@maldivesresorts.com"
echo "Preview: Thank you for the proposal. The $2.5M design fee is acceptable..."
echo ""
echo "Output:"
echo "-------"

ollama run bensley-email-assistant "Categorize this email:

Subject: Re: Fee proposal for MAL-24-02 - Maldives Luxury Resort
From: director@maldivesresorts.com
Preview: Thank you for the proposal. The \$2.5M design fee is acceptable. We'd like to schedule a call next week to discuss the timeline and next steps. When is Bill available?

Return JSON only." 2>/dev/null | head -30

################################################################################
# COMPLETE
################################################################################

echo ""
echo "================================================================================"
echo "SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo "Your local AI model is ready to use!"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the model:"
echo "   python3 local_model_inference.py test"
echo ""
echo "2. Process uncategorized emails:"
echo "   python3 local_model_inference.py process 50"
echo ""
echo "3. Compare accuracy with Claude:"
echo "   python3 local_model_inference.py compare"
echo ""
echo "4. If accuracy > 90%, integrate with backend:"
echo "   Edit backend/services/ai_service.py"
echo "   Set USE_LOCAL_MODEL=true in .env"
echo ""
echo "5. To improve accuracy further:"
echo "   - Add human training data: python3 manual_training_feedback.py"
echo "   - Re-export and fine-tune (see LOCAL_MODEL_GUIDE.md)"
echo ""
echo "Model info:"
echo "  • Name: bensley-email-assistant"
echo "  • Base: Mistral-7B-Instruct"
echo "  • Method: Prompt engineering with business context"
echo "  • Cost: \$0 per email"
echo "  • Privacy: 100% local, no external API calls"
echo ""
echo "To use the model directly:"
echo "  ollama run bensley-email-assistant 'Categorize this email: ...'"
echo ""
echo "Ollama server is running in background. To stop:"
echo "  killall ollama"
echo ""
