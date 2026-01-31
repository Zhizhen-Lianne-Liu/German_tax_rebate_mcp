# Quick Start Guide

## ⚡ 3-Minute Setup

### 1. Install Prerequisites

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install just (command runner)
brew install just  # macOS
```

### 2. Run Setup

```bash
cd /Users/lianneliu/Projects/German_tax_rebate_mcp

# One command does everything!
just setup
```

**What happens:**
- ✅ Installs Python dependencies (fastmcp, chromadb, sentence-transformers, etc.)
- ✅ Downloads local embedding model (~80MB, runs offline)
- ✅ Ingests German tax law documents into RAG database
- ✅ Tests the system

**Expected output:**
```
🚀 Setting up German Tax MCP Server...

1. Installing dependencies with uv...
   ✅ Dependencies installed

2. Populating knowledge base (RAG)...
  Processing: commuting.md (8 chunks)
  Processing: home_office.md (10 chunks)
  Processing: household_services.md (12 chunks)
  Processing: craftsman.md (14 chunks)

✅ Setup complete! Run 'just test' to verify.
```

### 3. Test It

```bash
# Test RAG queries
just test-rag

# Test tax calculations
just test-calc

# Show knowledge base stats
just stats
```

---

## 🎯 Your Next Steps

### Option A: Use with Claude Desktop

**1. Add to Claude Desktop config:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "german-tax": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/lianneliu/Projects/German_tax_rebate_mcp",
        "run",
        "python",
        "src/server.py"
      ]
    }
  }
}
```

**2. Restart Claude Desktop**

**3. Start chatting:**
```
You: "Help me file my 2025 German tax return.
     My receipts are in ~/Documents/2025_receipts/"
```

### Option B: Develop Locally

```bash
# Run the server directly
just run

# Test individual tools
just test-calc
just test-rag

# See all commands
just --list
```

---

## 📚 Useful Commands

```bash
# Development
just run              # Start MCP server
just test             # Run all tests
just ingest           # Refresh knowledge base

# Testing
just test-rag         # Test RAG queries
just test-calc        # Test calculations
just stats            # Show database stats

# Utilities
just clean            # Clean generated files
just info             # System information
just help             # Quick reference
```

---

## 🔍 Testing the RAG System

```bash
# Query about home office
just test-rag
```

**Expected output:**
```
🧪 Testing RAG system...

Answer: The Homeoffice-Pauschale is a flat-rate deduction for
employees and self-employed individuals who work from home.
You can claim €6 per day worked from home, with a maximum of
210 days per year (€1,260 maximum deduction)...

Confidence: 0.87
```

---

## 🧮 Testing Calculations

```bash
# Test commuting and home office calculations
just test-calc
```

**Expected output:**
```
🧪 Testing tax calculations...

Commuting (20km, 200 days):
{'amount': 1200.0, 'calculation': '20km × 200 workdays', ...}

Home office (150 days):
{'amount': 900.0, 'days_used': 150, ...}
```

---

## 📊 Check Knowledge Base

```bash
just stats
```

**Expected output:**
```
📊 Knowledge Base Statistics:
  Deductions: 44 chunks
  Forms: 0 chunks
  Tax law: 0 chunks
```

---

## 🐛 Troubleshooting

### "uv: command not found"
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc
```

### "just: command not found"
```bash
# macOS
brew install just

# Linux
cargo install just
```

### "No module named 'fastmcp'"
```bash
# Re-run setup
just setup
```

### RAG returns no results
```bash
# Check knowledge base
just stats

# If 0 chunks, re-ingest
just ingest-force
```

---

## 🎓 Learn More

- **Full documentation:** `README.md`
- **Development guide:** `CLAUDE.md`
- **Implementation plan:** See commit history
- **Add tax documents:** `just add-doc <name>`

---

## 🚀 Current Status

✅ **Working:**
- RAG engine (local, privacy-first)
- Knowledge base (4 deduction types)
- Tax calculations (2025 rates)
- Setup automation (just + uv)

🚧 **In Progress:**
- Simplified MCP server (5 core tools)
- Receipt scanner (OCR)
- ELSTER XML generator

**Ready to build the remaining tools!**

---

## ⚡ Pro Tips

1. **Add custom deductions:**
   ```bash
   just add-doc insurance
   # Edit knowledge_base/deductions/insurance.md
   just ingest
   ```

2. **Test queries interactively:**
   ```bash
   uv run python
   >>> from src.lib.rag_engine import get_rag
   >>> rag = get_rag()
   >>> result = rag.query("Can I deduct childcare?")
   >>> print(result['answer'])
   ```

3. **Monitor knowledge base:**
   ```bash
   watch -n 1 just stats  # Live stats (requires watch)
   ```

---

**You're all set! 🎉 Run `just help` anytime for quick reference.**
