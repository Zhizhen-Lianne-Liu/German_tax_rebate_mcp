# German Tax MCP Server

A privacy-first Model Context Protocol server that helps users navigate the German tax rebate process with AI assistance.

## 🎯 Features

✅ **Fully Local** - All data stays on your machine, no cloud uploads
✅ **RAG-Powered** - Query up-to-date German tax law (EStG, BMF circulars, ELSTER forms)
✅ **Smart Analysis** - Auto-categorize bank transactions for deductions
✅ **Receipt Management** - OCR, validation, and audit package generation
✅ **Tax Calculations** - Accurate 2025 German tax rates and formulas
✅ **ELSTER Export** - Generate import-ready XML for official submission

## 🔒 Privacy & Security

- **No Cloud Uploads:** All processing happens locally on your computer
- **No External APIs:** Tax calculations, OCR, and document parsing run offline
- **Local Storage:** Your profiles, receipts, and documents never leave your machine
- **Open Source:** Review the code yourself - Apache 2.0 licensed

## 📋 Requirements

- **Python 3.11+**
- **Tesseract OCR** (for receipt scanning)
- **~3GB disk space** (for vector database and receipts)

## 🚀 Installation

### Prerequisites

1. **Install uv** (fast Python package manager):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv
```

2. **Install just** (command runner):
```bash
# macOS
brew install just

# Linux
cargo install just
# or: curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash
```

3. **(Optional) Install Tesseract** for receipt OCR:
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-deu
```

### Quick Setup

```bash
git clone https://github.com/yourusername/german-tax-mcp.git
cd german-tax-mcp

# One command to set up everything!
just setup
```

**What this does:**
- Installs all Python dependencies with uv
- Populates the knowledge base with German tax law
- Tests the RAG system
- Takes ~2 minutes

### Verify Installation

```bash
just test     # Run all tests
just stats    # Show knowledge base statistics
just help     # See all available commands
```

## 💻 Usage

### With Claude Desktop (Recommended)

1. Edit your Claude Desktop config file:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

2. Add the MCP server (use `uv` to run):
```json
{
  "mcpServers": {
    "german-tax": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/german-tax-mcp",
        "run",
        "python",
        "src/server.py"
      ]
    }
  }
}
```

3. Restart Claude Desktop

4. Start chatting:
```
You: "I need help filing my 2025 German tax return"

Claude will:
✓ Scan your receipts folder
✓ Ask key questions
✓ Calculate deductions
✓ Generate ELSTER XML
```

### Development Commands

```bash
just run          # Start MCP server
just test         # Run all tests
just test-rag     # Test RAG queries
just test-calc    # Test calculations
just ingest       # Refresh knowledge base
just stats        # Show database stats
just clean        # Clean generated files
just help         # Show all commands
```

### Standalone Testing

```bash
just test-calc    # Test tax calculations
just test-rag     # Test RAG system
```

## 📊 Example Workflow

### 1. Initial Profile Setup
```
You: "Create my tax profile for 2025"
Claude: → Calls create_user_profile()
        → Asks: marital status, tax class, employment, commute distance, etc.
        → Saves to data/profiles/current.json
```

### 2. Document Analysis
```
You: "Here's my Lohnsteuerbescheinigung PDF"
Claude: → Calls parse_wage_tax_statement()
        → Extracts: gross income, taxes paid, Steuer-ID
        → Stores data for refund calculation
```

### 3. Bank Statement Analysis
```
You: "Analyze my 2025 bank statement for deductions"
Claude: → Calls analyze_bank_statement()
        → Finds: BVG subscriptions (commuting), Telekom (home office),
                 MediaMarkt purchase (work equipment?)
        → Suggests potential deductions worth €2,456
```

### 4. Receipt Management
```
You: "I have a receipt for cleaning services"
Claude: → Calls scan_receipt()
        → Extracts: €120, paid via bank transfer, labor only
        → Calls validate_receipt_for_deduction()
        → ✓ Valid for Haushaltsnahe Dienstleistungen
        → Stores in data/receipts/2025/household_services/
```

### 5. Tax Calculation
```
You: "Calculate my refund estimate"
Claude: → Calls calculate_commuting_deduction() → €1,200
        → Calls calculate_home_office_deduction() → €900
        → Calls calculate_household_service_deduction() → €24
        → Calculates final refund: €1,234.56
```

### 6. ELSTER Export
```
You: "Generate my ELSTER XML"
Claude: → Calls generate_elster_xml()
        → Creates: data/exports/2025_elster.xml
        → Instructions: Import to Mein ELSTER → Review → Submit
```

## 🛠️ Available Tools

### Profile Management
- `create_user_profile()` - Interactive questionnaire
- `load_user_profile()` - Load existing profile
- `update_profile()` - Update specific fields
- `remind_profile_update()` - Check if profile needs updating

### Tax Calculations
- `calculate_commuting_deduction()` - Entfernungspauschale
- `calculate_home_office_deduction()` - Homeoffice-Pauschale
- `calculate_household_service_deduction()` - Haushaltsnahe Dienstleistungen
- `calculate_craftsman_deduction()` - Handwerkerleistungen
- `calculate_refund_estimate()` - Full refund calculation

### Document Processing
- `parse_wage_tax_statement()` - Extract data from Lohnsteuerbescheinigung
- `scan_receipt()` - OCR receipt image/PDF
- `analyze_bank_statement()` - Categorize transactions
- `detect_missing_opportunities()` - Find unclaimed deductions

### Receipt Management
- `store_receipt()` - Save and categorize receipt
- `validate_receipt_for_deduction()` - Check German tax requirements
- `generate_audit_package()` - Prepare for Finanzamt if requested

### Tax Guidance
- `query_tax_code()` - Search German tax law via RAG
- `get_required_forms()` - List ELSTER forms needed
- `locate_finanzamt()` - Find your tax office
- `check_double_taxation_treaty()` - For expats with foreign income

### Output Generation
- `generate_elster_xml()` - Create ELSTER-compatible XML
- `generate_submission_report()` - Comprehensive PDF report
- `get_submission_checklist()` - Step-by-step filing guide

## 📚 Data Storage

All user data is stored locally in the `data/` directory:

```
data/
├── profiles/
│   ├── current.json          # Your active profile
│   └── archive/              # Previous years
├── receipts/
│   └── 2025/
│       ├── commuting/        # BVG, DB tickets
│       ├── home_office/      # Internet, equipment
│       ├── household_services/  # Cleaning, gardening
│       └── craftsman/        # Repairs, maintenance
├── documents/
│   ├── lohnsteuerbescheinigung_2025.pdf
│   └── bank_statements/
├── exports/
│   ├── 2025_elster.xml       # For ELSTER import
│   └── 2025_tax_report.pdf   # Human-readable summary
└── vector_db/                # Tax law knowledge base (local)
```

## 🧪 Development

### Run Tests
```bash
pytest tests/ -v
```

### Test Specific Calculation
```bash
python -c "from src.server import calculate_home_office_deduction; print(calculate_home_office_deduction(150))"
```

### Update Knowledge Base
```bash
python scripts/ingest_knowledge_base.py --force
```

## 🔄 Annual Updates

When the new tax year begins (e.g., 2026):

1. Update tax rates in `src/config.py` → Create `TaxRates2026` class
2. Add new BMF circulars to `knowledge_base/bmf_circulars/2026/`
3. Re-run: `python scripts/ingest_knowledge_base.py`
4. Update `src/server.py` to reference new rates

## ❓ FAQ

**Q: Is my data safe?**
A: Yes! Everything runs locally. No data is uploaded to any server (unless you explicitly enable optional cloud OCR).

**Q: Does this replace a tax advisor?**
A: No. This tool helps organize and calculate, but for complex situations (self-employment, rental income, inheritance), consult a Steuerberater.

**Q: Can it submit directly to ELSTER?**
A: Not yet. It generates XML that you import to Mein ELSTER. Direct submission requires ELSTER certification (planned for future).

**Q: What about previous tax years?**
A: Currently supports 2025. You can manually backdate by editing `TaxRates2024` in `config.py`, but rates may differ.

**Q: I found a bug!**
A: Please open an issue on GitHub with details. Tax calculations are thoroughly tested, but edge cases exist.

## 🌍 For Expatriates

This tool is particularly helpful for expats because:

- **Bilingual support:** German terms explained in English
- **Double taxation treaties:** Check US-Germany, UK-Germany, etc.
- **Mid-year arrival/departure:** Handles 183-day residency rule
- **Foreign income:** Progressionsvorbehalt calculations
- **ELSTER in English:** Simplifies the German-only official system

## 🤝 Contributing

Contributions welcome! Areas needing help:

- [ ] Additional tax deduction types (e.g., childcare, education)
- [ ] More bank statement parsers (currently supports Sparkasse, N26)
- [ ] Translation of more BMF circulars
- [ ] Unit tests for edge cases
- [ ] Support for older tax years (2023, 2024)

See `CLAUDE.md` for development guidelines.

## 📜 License

Apache License 2.0 - see [LICENSE](LICENSE) file.

This project is not affiliated with the German Federal Ministry of Finance or ELSTER.

## ⚠️ Disclaimer

This software provides estimates and guidance only. While calculations are based on official German tax law, users are responsible for:

- Verifying all calculations
- Ensuring completeness of their tax return
- Maintaining required documentation
- Filing by official deadlines

For complex tax situations, consult a licensed Steuerberater.

---

**Made with 🇩🇪 for the German tax system**
Questions? Open an issue or discussion on GitHub.
