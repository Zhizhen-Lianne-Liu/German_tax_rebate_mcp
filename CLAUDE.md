# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**German Tax MCP Server** - A privacy-first Model Context Protocol server that helps users navigate the German tax rebate process. Built with Python and FastMCP, it provides AI assistants with tools for profile management, document parsing, tax calculations, receipt management, and ELSTER XML generation.

**Key principle:** All processing happens locally on the user's machine. No sensitive tax data leaves their computer.

## Architecture

- **Language:** Python 3.11+ with FastMCP framework
- **Storage:** JSON (user profiles), SQLite (receipt metadata), ChromaDB (local RAG)
- **Privacy:** Fully local processing, no cloud dependencies (except optional OCR)
- **Tax Year:** 2025 rates and regulations

## Project Structure

```
src/
├── server.py              # FastMCP entry point
├── config.py              # Tax rates, constants, file paths
├── schemas/               # Pydantic data models
│   ├── profile.py        # UserProfile, Child
│   ├── receipt.py        # Receipt, ReceiptItem
│   └── deduction.py      # DeductionResult types
├── tools/                 # MCP tool implementations (to be added)
│   ├── profile_tools.py
│   ├── calculation_tools.py
│   ├── document_tools.py
│   ├── receipt_tools.py
│   ├── analysis_tools.py
│   └── output_tools.py
└── lib/                   # Core libraries (to be added)
    ├── rag_engine.py
    ├── parsers.py
    ├── ocr.py
    ├── tax_calculator.py
    └── elster_xml.py

data/                      # User data (gitignored)
├── profiles/             # JSON user profiles
├── receipts/             # Organized by year/category
├── documents/            # Lohnsteuerbescheinigung, bank statements
├── exports/              # ELSTER XML, PDF reports
└── vector_db/            # ChromaDB storage

knowledge_base/           # Tax law sources (shipped with repo)
├── estg/                # Einkommensteuergesetz sections
├── bmf_circulars/       # Ministry circulars
├── forms/               # ELSTER form instructions
└── treaties/            # Double taxation treaties
```

## Key Commands

### Development
```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run server (for MCP clients like Claude Desktop)
python src/server.py

# Test calculations directly
python -c "from src.server import calculate_commuting_deduction; print(calculate_commuting_deduction(20, 200))"
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Test specific module
pytest tests/test_calculations.py -v
```

### Knowledge Base Setup
```bash
# Ingest tax law documents into RAG (one-time setup, ~5 minutes)
python scripts/ingest_knowledge_base.py

# Update tax rates for new year
python scripts/update_tax_rates.py --year 2026
```

## Tax Rates & Constants (2025)

Located in `src/config.py` under `TaxRates2025`:

- **Basic allowance:** €11,604 (Grundfreibetrag)
- **Commuting:** €0.30/km (first 20km), €0.38/km (21st km+), max €4,500/year
- **Home office:** €6/day, max 210 days (€1,260)
- **Household services:** 20% of labor costs, max €4,000
- **Craftsman services:** 20% of labor costs, max €1,200
- **Equipment depreciation threshold:** €800

**Update these annually in January** when new BMF circulars are published.

## Code Patterns

### Adding a New MCP Tool

```python
# In src/server.py or appropriate tools/ module
@mcp.tool()
def calculate_new_deduction(param: float, optional_param: int = None) -> dict:
    """
    Brief description for the LLM.

    Longer explanation of German tax rule and what this calculates.

    Args:
        param: Description of parameter
        optional_param: Optional parameter with default

    Returns:
        Dictionary with 'amount', 'calculation', 'warnings', 'errors'
    """
    # Validation
    if param <= 0:
        return {"amount": 0.0, "errors": ["Parameter must be positive"]}

    # Calculation using TaxRates2025 constants
    amount = param * TaxRates2025.SOME_RATE

    # Return structured result
    return {
        "amount": round(amount, 2),
        "calculation": f"Explanation of calc",
        "warnings": [],
        "errors": []
    }
```

### Adding a Pydantic Schema

```python
# In src/schemas/
from pydantic import BaseModel, Field

class NewModel(BaseModel):
    """Model description"""
    field: str = Field(..., description="Field description")
    optional_field: Optional[int] = None

    class Config:
        json_schema_extra = {"example": {...}}
```

## Common Development Tasks

### Update Tax Year
1. Update constants in `src/config.py` → `TaxRates2026` class
2. Add new BMF circulars to `knowledge_base/bmf_circulars/2026/`
3. Run `python scripts/ingest_knowledge_base.py`
4. Update tests with new rates in `tests/test_calculations.py`
5. Update `src/server.py` to reference `TaxRates2026`

### Add New Receipt Category
1. Add category to `Receipt.category` Literal in `src/schemas/receipt.py`
2. Add validation rules in `Receipt` class methods
3. Add pattern matching in `src/lib/analysis.py` → `MERCHANT_PATTERNS`
4. Create folder in `data/receipts/{year}/{new_category}/`

### Add New Form Support
1. Add form to `UserProfile.get_required_forms()` in `src/schemas/profile.py`
2. Add form instructions to `knowledge_base/forms/{form_name}.md`
3. Re-run `python scripts/ingest_knowledge_base.py`
4. Add XML mapping in `src/lib/elster_xml.py`

## Testing Guidelines

### Test Structure
```python
# tests/test_calculations.py
def test_commuting_standard_distance():
    """Test commuting deduction for distance ≤ 20km"""
    result = calculate_commuting_deduction(distance_km=15, workdays=200)
    assert result['amount'] == 900.0  # 15 × 200 × 0.30
    assert not result['capped_at_max']

def test_commuting_max_cap():
    """Test that commuting deduction caps at €4,500"""
    result = calculate_commuting_deduction(distance_km=100, workdays=250)
    assert result['amount'] == 4500.0
    assert result['capped_at_max']
```

### Test Fixtures
Located in `tests/fixtures/`:
- Sample profiles: `employee_single.json`, `expat_mid_year.json`
- PDFs: `lohnsteuerbescheinigung_40k.pdf`
- Receipts: `valid_household_service.jpg`, `invalid_cash_payment.jpg`
- Bank statements: `sparkasse_2025.csv`, `n26_2025.csv`

### Running Specific Tests
```bash
# Test single function
pytest tests/test_calculations.py::test_commuting_standard_distance -v

# Test with print statements visible
pytest tests/test_calculations.py -v -s
```

## Important Notes

- **Amounts:** Use `float` (not Decimal) - acceptable precision for tax estimates
- **Dates:** ISO 8601 format (YYYY-MM-DD)
- **Encoding:** UTF-8 for all German text
- **Receipt filenames:** `{date}_{merchant}_{amount}.pdf` via `FileNaming.receipt_filename()`
- **Profile storage:** `data/profiles/current.json` is active, archive old ones to `archive/`
- **Privacy:** NEVER log or transmit Steuer-ID, income amounts, or receipt contents

## German Tax Terminology

- **Steuer-ID:** 11-digit permanent tax ID
- **Lohnsteuerbescheinigung:** Annual wage tax certificate from employer
- **Werbungskosten:** Income-related expenses (work equipment, commuting)
- **Sonderausgaben:** Special expenses (insurance, donations, alimony)
- **Haushaltsnahe Dienstleistungen:** Household services (cleaning, gardening)
- **Handwerkerleistungen:** Craftsman services (repairs, maintenance)
- **Entfernungspauschale:** Commuting allowance
- **Homeoffice-Pauschale:** Home office flat rate
- **Anlage N:** Tax form for employment income
- **Anlage Kind:** Tax form for children
- **ELSTER:** Electronic tax return system
- **Finanzamt:** Tax office
- **Steuerbescheid:** Tax assessment notice

## Debugging

### Server won't start
```bash
# Check Python version
python --version  # Must be 3.11+

# Check dependencies
pip list | grep fastmcp

# Run with debug logging
DEBUG=true python src/server.py
```

### Calculations seem wrong
```bash
# Verify tax rates
python -c "from src.config import TaxRates2025; print(vars(TaxRates2025))"

# Test calculation directly
python -c "from src.server import calculate_commuting_deduction; print(calculate_commuting_deduction(20, 200))"
```

### RAG not returning results
```bash
# Check vector DB exists
ls -lh data/vector_db/

# Re-ingest knowledge base
python scripts/ingest_knowledge_base.py --force
```

## License

Apache License 2.0 - see LICENSE file for full terms.

## Future Development Phases

This is currently **Phase 1: Foundation** (project setup, basic calculations).

Upcoming phases:
- **Phase 2:** Core tax calculations (all deduction types)
- **Phase 3:** Receipt management system
- **Phase 4:** Bank statement analysis
- **Phase 5:** RAG integration
- **Phase 6:** Output generation (ELSTER XML, PDF)
- **Phase 7:** Testing & documentation

See implementation plan for full roadmap.
