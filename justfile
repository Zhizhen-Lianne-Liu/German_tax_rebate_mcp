# German Tax MCP Server - Justfile
# https://just.systems/

# List all available commands
default:
    @just --list

# Setup: Install dependencies and populate knowledge base
setup:
    @echo "🚀 Setting up German Tax MCP Server..."
    @echo ""
    @echo "1. Installing dependencies with uv..."
    uv sync
    @echo "   ✅ Dependencies installed"
    @echo ""
    @echo "2. Populating knowledge base (RAG)..."
    uv run python scripts/ingest_knowledge_base.py
    @echo ""
    @echo "✅ Setup complete! Run 'just test' to verify."

# Create/sync virtual environment with uv
sync:
    @echo "📦 Syncing environment with uv..."
    uv sync

# Run the MCP server
run:
    @echo "🚀 Starting German Tax MCP Server..."
    uv run python src/server.py

# Populate/refresh the knowledge base
ingest:
    @echo "📚 Ingesting knowledge base..."
    uv run python scripts/ingest_knowledge_base.py

# Force re-ingest (clear and rebuild)
ingest-force:
    @echo "📚 Force re-ingesting knowledge base..."
    uv run python scripts/ingest_knowledge_base.py --force

# Test RAG system
test-rag:
    @echo "🧪 Testing RAG system..."
    @uv run python -c "from src.lib.rag_engine import get_rag; rag = get_rag(); result = rag.query('Can I deduct home office internet costs?'); print(f'\nAnswer: {result[\"answer\"][:200]}...\nConfidence: {result[\"confidence\"]}')"

# Test tax calculations
test-calc:
    @echo "🧪 Testing tax calculations..."
    @uv run python -c "from src.server import calculate_commuting_deduction, calculate_home_office_deduction; print('Commuting (20km, 200 days):', calculate_commuting_deduction(20, 200)); print('\nHome office (150 days):', calculate_home_office_deduction(150))"

# Test receipt scanner
test-receipt path:
    @echo "🧪 Testing receipt scanner on: {{path}}"
    @uv run python -c "from src.lib.receipt_scanner import scan_receipt; result = scan_receipt('{{path}}'); print(f'Merchant: {result.merchant}'); print(f'Amount: €{result.amount}'); print(f'Date: {result.date}'); print(f'Category: {result.category}'); print(f'Confidence: {result.confidence}')"

# Test ELSTER XML generation (dry run)
test-xml:
    @echo "🧪 Testing ELSTER XML generation..."
    @uv run python -c "from src.lib.elster_xml import generate_elster_xml; from src.schemas.simple import TaxQuestions, DeductionsSummary; q = TaxQuestions(gross_income=45000, income_tax_paid=9000, marital_status='single', tax_class='I', num_children=0, work_address='Berlin', home_address='Berlin', home_office_days=150, steuer_id='12345678901', postal_code='10115'); d = DeductionsSummary(estimated_refund=1234.56); path = generate_elster_xml(q, d); print(f'XML generated: {path}')"

# Run all tests
test: test-rag test-calc
    @echo ""
    @echo "✅ All tests passed!"

# Check knowledge base stats
stats:
    @echo "📊 Knowledge Base Statistics:"
    @uv run python -c "from src.lib.rag_engine import get_rag; rag = get_rag(); print(f'  Deductions: {rag.get_collection_count(\"deductions\")} chunks'); print(f'  Forms: {rag.get_collection_count(\"forms\")} chunks'); print(f'  Tax law: {rag.get_collection_count(\"tax_law\")} chunks')"

# Clean up generated files
clean:
    @echo "🧹 Cleaning up..."
    rm -rf data/vector_db/*
    rm -rf data/exports/*
    rm -rf src/__pycache__
    rm -rf src/**/__pycache__
    @echo "✅ Cleaned"

# Show system info
info:
    @echo "ℹ️  System Information:"
    @echo "  Python: $(uv run python --version)"
    @echo "  uv: $(uv --version)"
    @echo "  Project: German Tax MCP Server"
    @echo "  Location: $(pwd)"

# Development: Watch and reload (if needed)
dev:
    @echo "🔧 Development mode..."
    uv run python src/server.py

# Add a new tax deduction document
add-doc name:
    @echo "📝 Creating new deduction document: {{name}}"
    @mkdir -p knowledge_base/deductions
    @touch knowledge_base/deductions/{{name}}.md
    @echo "# {{name}}\n\n## What is it?\n\n[Description]\n\n## Rates for 2025\n\n[Rates]\n\n## How to Calculate\n\n[Formula]\n" > knowledge_base/deductions/{{name}}.md
    @echo "✅ Created: knowledge_base/deductions/{{name}}.md"
    @echo "   Edit the file, then run: just ingest"

# Validate knowledge base sources
validate-sources:
    @echo "🔍 Validating source citations..."
    uv run python scripts/source_manager.py validate

# List official sources
list-sources:
    @echo "📚 Official tax law sources..."
    uv run python scripts/source_manager.py list-sources

# Quick start guide
help:
    @echo "📖 Quick Start Guide"
    @echo ""
    @echo "Initial setup:"
    @echo "  just setup          # Install everything and populate knowledge base"
    @echo ""
    @echo "Development:"
    @echo "  just run            # Start MCP server"
    @echo "  just test           # Run tests"
    @echo "  just ingest         # Refresh knowledge base"
    @echo ""
    @echo "Utilities:"
    @echo "  just stats          # Show knowledge base stats"
    @echo "  just clean          # Clean generated files"
    @echo "  just info           # System information"
    @echo ""
    @echo "Full documentation: GETTING_STARTED.md"
