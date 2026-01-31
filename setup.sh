#!/bin/bash
# Setup script for German Tax MCP Server

set -e  # Exit on error

echo "=================================================="
echo "German Tax MCP Server - Setup"
echo "=================================================="

# Check Python version
echo ""
echo "1. Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found: Python $python_version"

if [[ $(echo "$python_version 3.11" | awk '{print ($1 >= $2)}') -eq 0 ]]; then
    echo "   ⚠️  Python 3.11+ required. Please install and try again."
    exit 1
fi

# Create virtual environment
echo ""
echo "2. Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Virtual environment created"
else
    echo "   ℹ️  Virtual environment already exists"
fi

# Activate and install dependencies
echo ""
echo "3. Installing Python dependencies..."
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "   ✅ Dependencies installed"

# Check Tesseract (optional but recommended)
echo ""
echo "4. Checking for Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -n1)
    echo "   ✅ $tesseract_version"
else
    echo "   ⚠️  Tesseract not found (optional for receipt scanning)"
    echo "   Install with: brew install tesseract tesseract-lang (macOS)"
    echo "                sudo apt install tesseract-ocr tesseract-ocr-deu (Linux)"
fi

# Populate knowledge base
echo ""
echo "5. Populating knowledge base (RAG)..."
python scripts/ingest_knowledge_base.py
echo "   ✅ Knowledge base ready"

# Test RAG
echo ""
echo "6. Testing RAG system..."
python -c "from src.lib.rag_engine import get_rag; rag = get_rag(); result = rag.query('home office deduction'); print('   Query test:', 'PASSED ✅' if result['confidence'] > 0 else 'FAILED ❌')"

# Summary
echo ""
echo "=================================================="
echo "Setup Complete! 🎉"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Test server: python src/server.py"
echo "  3. Configure Claude Desktop (see GETTING_STARTED.md)"
echo ""
echo "Knowledge base stats:"
python -c "from src.lib.rag_engine import get_rag; rag = get_rag(); print(f'  - Deductions: {rag.get_collection_count(\"deductions\")} documents')"
echo ""
echo "Read GETTING_STARTED.md for full instructions!"
echo "=================================================="
