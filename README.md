# German Tax MCP Server

Privacy-first MCP server for German tax returns with incremental, conversational data collection.

## Features

- **Fully Local** - All data stays on your machine
- **Incremental Workflow** - Explore calculations before committing personal info
- **RAG-Powered** - Query German tax law using pgvector + TF-IDF (no heavy ML dependencies)
- **Auto-Saving** - Calculations persist across sessions
- **Smart Gap Analysis** - System tells you exactly what's missing
- **ELSTER Export** - Generates submission-ready XML

## Setup

```bash
# Install dependencies
brew install just tesseract tesseract-lang docker
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <repo-url>
cd german-tax-mcp

# Start PostgreSQL + pgvector (for RAG)
docker-compose up -d

# Install Python deps + populate knowledge base (~2 min)
just setup
```

## Claude Desktop Integration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "german-tax": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/german-tax-mcp", "run", "python", "src/server.py"]
    }
  }
}
```

Restart Claude Desktop, look for 🔌 green icon.

## Usage

### V2 Incremental Workflow

**Explore first (no personal info needed):**
```
Calculate my commuting deduction: 15km, 200 days
Calculate home office for 180 days
Check my tax return status
```

**Provide info piece-by-piece:**
```
Update my info: first name Anna, email anna@example.de
Update my info: income €45000, tax paid €9000
Check my status
```

**Complete when ready:**
```
Update my info: birthdate 1990-05-15, tax ID 12345678901, postal code 10405,
home address "Prenzlauer Allee 50", IBAN DE89370400440532013000,
marital status single, tax class I

Finalize my tax return
```

✅ XML generated at `data/exports/tax_return_2025_*.xml`

### Available Tools

| Tool | Purpose |
|------|---------|
| `update_personal_info()` | Add/update info incrementally (20 optional params) |
| `get_tax_return_status()` | Check completeness, missing fields, next steps |
| `finalize_tax_return()` | Gap analysis + XML generation if complete |
| `calculate_commuting_deduction()` | Entfernungspauschale (auto-saves) |
| `calculate_home_office_deduction()` | Homeoffice-Pauschale (auto-saves) |
| `start_tax_return()` | Scan receipts folder |
| `query_tax_rules()` | RAG queries on German tax law |
| `clear_session()` | Reset all data |

## Quick Test

```bash
# After Claude Desktop restart, try this in chat:
Calculate commuting: 15km, 200 days
Check my status
```

**Expected:**
- Returns €900 deduction
- Message: "✅ This calculation has been saved"
- Status shows 0% complete, lists required fields

### Full Example

```
I want to file my 2025 tax return.

Calculate commuting: 18km, 70 office days
Calculate home office: 150 days
Scan receipts: /path/to/receipts

Check my status.

Update my info:
- First name: Anna, Last name: Schmidt
- Birthdate: 1990-05-15
- Email: anna.schmidt@example.de
- Income: €45,000, Tax paid: €9,000
- Single, tax class I
- Tax ID: 12345678901
- Postal code: 10405
- Home address: Prenzlauer Allee 50, 10405 Berlin
- IBAN: DE89370400440532013000

Finalize my tax return.
```

**Result:** ELSTER XML with ~€2,000+ refund estimate

## Session Persistence

All data saves to `data/session.json` with structure:
```json
{
  "personal_info": {...},
  "income_info": {...},
  "tax_status": {...},
  "work_info": {...},
  "calculations": {
    "commuting": {"input": {...}, "result": {...}},
    "home_office": {"input": {...}, "result": {...}}
  },
  "receipts": {"scanned": true, "summary": {...}},
  "deductions": {...}
}
```

Session persists across Claude Desktop restarts.

## Required Fields for ELSTER

- **Personal:** first_name, last_name, birthdate
- **Tax ID:** steuer_id (11 digits)
- **Address:** postal_code, home_address
- **Bank:** iban (DE + 20 digits)
- **Contact:** email
- **Income:** gross_income, income_tax_paid
- **Status:** marital_status, tax_class

Optional: phone, employer_name, religion, work_address, etc.

## 2025 Tax Rates

| Deduction | Rate | Max |
|-----------|------|-----|
| Commuting (0-20km) | €0.30/km | €4,500 |
| Commuting (21km+) | €0.38/km | €4,500 |
| Home Office | €6/day | €1,260 (210 days) |
| Household Services | 20% labor | €4,000 credit |
| Craftsman | 20% labor | €1,200 credit |

## Development

```bash
just run          # Start MCP server
just test         # Run tests
just test-rag     # Test RAG queries
just ingest       # Refresh knowledge base
just clean        # Clean generated files
```

## Troubleshooting

**MCP not connecting?**
- Verify config path in `claude_desktop_config.json`
- Check 🔌 icon is green
- Restart Claude Desktop (Cmd+Q then reopen)

**Session not persisting?**
- Check `data/session.json` exists
- Look for "DEBUG SessionManager: Saved" in console

**Finalize says incomplete?**
- Run: `Check my tax return status`
- Verify all 11 required fields provided

**Calculations not saving?**
- Look for "✅ This calculation has been saved" message
- Verify session.json has `calculations` object

## V1 vs V2

| Feature | V1 (Old) | V2 (New) |
|---------|----------|----------|
| Data entry | All 24 fields at once | Piece-by-piece |
| Exploration | Must commit first | Explore calculations first |
| Progress tracking | None | Real-time completeness % |
| Gap analysis | Manual | Automatic |
| Session resume | Restart from scratch | Pick up anywhere |
| Workflow | Rigid form | Natural conversation |

## Privacy & Security

- **No cloud uploads** - Everything runs locally
- **No external APIs** - Offline OCR and calculations
- **Open source** - Apache 2.0 licensed
- **Local storage** - Data never leaves your machine

## Disclaimer

This software provides estimates only. Users are responsible for verifying calculations and filing accuracy. For complex situations, consult a licensed Steuerberater.

Not affiliated with German Federal Ministry of Finance or ELSTER.

## License

Apache License 2.0 - see LICENSE file.

---

**Made for the German tax system 🇩🇪**

Questions? Open an issue on GitHub.
