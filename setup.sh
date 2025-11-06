#!/bin/bash

echo "🚀 ScribeNet Setup Script"
echo "=========================="
echo ""

# Check if poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Poetry found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
poetry install

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Create data directory
echo ""
echo "📁 Creating data directory..."
mkdir -p data

echo "✅ Data directory created"

# Check config file
echo ""
if [ ! -f "config.yaml" ]; then
    echo "❌ config.yaml not found"
    echo "   Please ensure config.yaml exists in the project root"
    exit 1
else
    echo "✅ Configuration file found"
fi

echo ""
echo "=========================="
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Start vLLM server (in a separate terminal):"
echo "   vllm serve /path/to/your/model \\"
echo "     --gpu-memory-utilization 0.85 \\"
echo "     --max-model-len 32768"
echo ""
echo "2. Update config.yaml with your vLLM URL if needed"
echo ""
echo "3. Or start the API server:"
echo "   cd backend && poetry run uvicorn api.main:app --reload"
echo ""
