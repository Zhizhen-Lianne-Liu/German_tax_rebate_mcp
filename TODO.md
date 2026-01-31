# Development TODO

## ✅ Completed (Phase 1)

- [x] Project structure and configuration
- [x] Pydantic schemas (simplified for MVP)
- [x] RAG engine (ChromaDB + sentence-transformers)
- [x] Knowledge base ingestion script
- [x] Sample tax law documents (commuting, home office, household services, craftsman)
- [x] Basic tax calculation functions

## 🚧 In Progress (Phase 2 - Simplified MVP)

### High Priority

- [ ] **Simplified server.py** with 5 core MCP tools:
  - [ ] `start_tax_return(receipts_folder)` - Scan receipts folder
  - [ ] `answer_questions(answers)` - Collect user info
  - [ ] `query_tax_rules(question)` - RAG lookup
  - [ ] `calculate_deductions(...)` - Calculate all deductions
  - [ ] `generate_elster_xml(...)` - Create ELSTER XML

- [ ] **Receipt scanner** (`src/lib/receipt_scanner.py`):
  - [ ] OCR with pytesseract
  - [ ] Auto-categorize by merchant name
  - [ ] Extract date, amount, merchant
  - [ ] Confidence scoring

- [ ] **ELSTER XML generator** (`src/lib/elster_xml.py`):
  - [ ] XML template for Anlage N
  - [ ] Map deductions to form fields
  - [ ] Validate against schema
  - [ ] Export to file

### Medium Priority

- [ ] **Error handling**:
  - [ ] Graceful OCR failures
  - [ ] Invalid receipt format handling
  - [ ] Missing answer validation

- [ ] **Testing**:
  - [ ] Unit tests for calculations
  - [ ] Integration test with sample receipts
  - [ ] RAG query accuracy tests

- [ ] **Documentation**:
  - [ ] Update README with simplified flow
  - [ ] Add example conversation flow
  - [ ] Create troubleshooting guide

### Low Priority (Post-MVP)

- [ ] Support for more receipt categories (donations, insurance)
- [ ] Bank statement analysis (CSV parser)
- [ ] Persistent user profiles (optional)
- [ ] PDF report generation
- [ ] Multi-year support (2024, 2023)
- [ ] Cloud RAG option (for easier updates)

## 📋 Next Immediate Steps

1. **Create simplified `server.py`** with 5 core tools
2. **Build receipt scanner** using pytesseract
3. **Implement ELSTER XML generator**
4. **Test end-to-end** with real receipts
5. **Update documentation**

## 🎯 MVP Definition

**A working MCP server that:**
1. Scans a folder of receipts
2. Categorizes them automatically
3. Asks user 10 key questions
4. Uses RAG to explain rules
5. Calculates deductions (2025 rates)
6. Generates importable ELSTER XML

**Success criteria:**
- Works with Claude Desktop
- Handles 50+ receipts
- Generates valid XML
- RAG answers 90% of common questions
- Full flow takes <5 minutes

## 📦 Dependencies Still Needed

All already in `requirements.txt`:
- pytesseract (OCR)
- Pillow (image processing)
- lxml (XML generation)
- PyPDF2 (PDF receipt parsing)

## 🔧 Dev Environment

```bash
# Activate venv
source venv/bin/activate

# Run ingestion (if knowledge base updated)
python scripts/ingest_knowledge_base.py

# Test RAG
python -c "from src.lib.rag_engine import get_rag; print(get_rag().query('home office deduction'))"

# Run server (when ready)
python src/server.py
```
