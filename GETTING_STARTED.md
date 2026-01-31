# Getting Started with German Tax MCP Server

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd /Users/lianneliu/Projects/German_tax_rebate_mcp

# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

**What this installs:**
- FastMCP (MCP server framework)
- ChromaDB (local vector database)
- sentence-transformers (local embedding model)
- Pydantic (data validation)

### Step 2: Populate the Knowledge Base

```bash
# Run the ingestion script to load tax law documents
python scripts/ingest_knowledge_base.py
```

**What this does:**
- Reads markdown files from `knowledge_base/deductions/`
- Chunks them into searchable pieces
- Generates embeddings using a local model (no cloud API needed)
- Stores in ChromaDB at `data/vector_db/`

**Expected output:**
```
==============================================================
German Tax Knowledge Base Ingestion
==============================================================

1. Initializing RAG engine...
Loading embedding model: sentence-transformers/all-MiniLM-L6-v2

2. Processing deductions (Deduction rules and examples)...
  Processing: commuting.md
    Added 8 chunks
  Processing: home_office.md
    Added 10 chunks
  Processing: household_services.md
    Added 12 chunks
  Processing: craftsman.md
    Added 14 chunks

==============================================================
Ingestion Complete!
==============================================================
Files processed: 4
Deductions collection: 44 chunks
Forms collection: 0 chunks
Tax law collection: 0 chunks

✅ RAG database ready for queries!
```

### Step 3: Test the RAG System

```bash
python -c "
from src.lib.rag_engine import get_rag

rag = get_rag()
result = rag.query('Can I deduct internet costs if I work from home?')
print('Answer:', result['answer'])
print('Confidence:', result['confidence'])
"
```

Expected output: You should see relevant information about home office deductions!

### Step 4: Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "german-tax": {
      "command": "/Users/lianneliu/Projects/German_tax_rebate_mcp/venv/bin/python",
      "args": ["/Users/lianneliu/Projects/German_tax_rebate_mcp/src/server.py"]
    }
  }
}
```

### Step 5: Restart Claude Desktop

Close and reopen Claude Desktop. You should now see the German Tax MCP server available!

---

## 📁 Prepare Your Receipts

### Organize Your Receipt Folder

Create a folder with your 2025 receipts:

```
/Users/lianneliu/Documents/2025_tax_receipts/
├── bvg_monthly_ticket.pdf
├── telekom_internet_bills/
│   ├── january.pdf
│   ├── february.pdf
│   └── ...
├── mediamarkt_laptop_receipt.pdf
├── cleaning_service_invoices/
│   └── ...
└── ...
```

**Tips:**
- Any format works: PDF, JPG, PNG
- Organize by category if you want (but not required)
- Include ALL receipts - the system will categorize them

---

## 💬 Using with Claude

### Example Conversation

```
You: "I need to file my 2025 German tax return. My receipts are in
     /Users/lianneliu/Documents/2025_tax_receipts/"

Claude: I'll help you with your tax return! Let me start by scanning your receipts.
        → Calls: start_tax_return(receipts_folder="/Users/lianneliu/Documents/2025_tax_receipts/")

        I found 47 receipts:
        - Commuting: €1,032 (BVG tickets)
        - Home office: €479 (Internet bills)
        - Work equipment: €850 (Laptop from MediaMarkt)
        - Household services: €1,440 (Cleaning service)

        Now I need some information from you:

        1. What was your gross income in 2025? (from Lohnsteuerbescheinigung, line 3)
        2. How much income tax did you already pay? (line 4)
        3. What's your marital status?
        4. What's your tax class?
        5. Do you have children? If so, how many?
        6. What's your work address?
        7. What's your home address?
        8. How many days did you work from home?
        9. What's your Steuer-ID (11-digit tax ID)?
        10. What's your postal code?

You: [Provide answers]

Claude: → Calls: answer_questions(answers={...})
        → Calls: calculate_deductions(...)

        Great! Here's your tax summary:

        📊 Deductions:
        - Commuting: €1,200 (20km × 200 days)
        - Home office: €900 (150 days × €6)
        - Work equipment: €850
        - Household services: €288 (20% of €1,440)

        Total deductions: €3,238
        Estimated refund: €1,456

        Would you like me to generate the ELSTER XML?

You: "Yes, generate the XML"

Claude: → Calls: generate_elster_xml(...)

        ✅ Created: data/exports/2025_elster.xml

        Next steps:
        1. Go to https://www.elster.de
        2. Log in to Mein ELSTER
        3. Click "Datenimport"
        4. Upload the XML file
        5. Review all fields
        6. Submit!
```

---

## 🔍 Testing RAG Queries

You can ask tax questions directly:

```
You: "Do I need to keep receipts for the commuting deduction?"

Claude: → Calls: query_tax_rules("commuting deduction receipt requirements")

        According to German tax law, you do NOT need to keep receipts for the
        Entfernungspauschale (commuting flat rate). This is a flat-rate deduction
        based only on distance and workdays. However, you should be able to prove:
        - Your work address
        - Your home address
        - The distance (can be calculated from addresses)
```

---

## 🧪 Development & Testing

### Test Individual Tools

```bash
# Test RAG query
python -c "
from src.server import query_tax_rules
result = query_tax_rules('home office internet deduction')
print(result)
"

# Test calculation
python -c "
from src.server import calculate_commuting_deduction
result = calculate_commuting_deduction(20, 200)
print(result)
"
```

### Add More Tax Law Documents

1. Create a new markdown file in `knowledge_base/deductions/`
2. Write clear explanations of tax rules
3. Re-run ingestion:
```bash
python scripts/ingest_knowledge_base.py --force
```

---

## ❓ Troubleshooting

### "No module named 'fastmcp'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

### "RAG returns no results"
```bash
# Check if knowledge base is populated
python -c "from src.lib.rag_engine import get_rag; print(get_rag().get_collection_count('deductions'))"

# Should show > 0. If 0, run ingestion:
python scripts/ingest_knowledge_base.py
```

### "ModuleNotFoundError: No module named 'config'"
```bash
# Make sure you're running from project root
cd /Users/lianneliu/Projects/German_tax_rebate_mcp
python scripts/ingest_knowledge_base.py
```

### Embedding model download is slow
The first time you run, sentence-transformers downloads a ~80MB model. This is normal and only happens once.

---

## 📚 Next Steps

1. ✅ Setup complete - Knowledge base populated
2. ⏭️ **Next**: Run simplified server and test with Claude
3. ⏭️ **Then**: Add receipt scanner (OCR)
4. ⏭️ **Then**: Build ELSTER XML generator
5. ⏭️ **Finally**: Test with real receipts!

---

## 🎯 Current MVP Status

✅ Project structure
✅ RAG engine (local, privacy-first)
✅ Knowledge base (4 deduction types)
✅ Ingestion script
✅ Tax calculation formulas (2025 rates)

🚧 In Progress:
- Simplified MCP server with 5 core tools
- Receipt scanner (OCR)
- ELSTER XML generator

The foundation is ready - now we'll build the user-facing tools!
