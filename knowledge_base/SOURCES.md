# Official Information Sources

This knowledge base relies exclusively on official German tax law sources to ensure accuracy and legal compliance.

## Primary Sources

### 1. Federal Ministry of Finance (BMF)

**Bundesfinanzministerium der Finanzen**

The BMF is the authoritative source for German tax law interpretation and implementation.

#### Key Resources:

- **Amtliches Einkommensteuer-Handbuch 2024**
  - URL: https://esth.bundesfinanzministerium.de/
  - Comprehensive handbook covering all EStG provisions
  - Updated annually with current tax law interpretations

- **Amtliches Lohnsteuer-Handbuch 2025**
  - URL: https://esth.bundesfinanzministerium.de/lsth/2025/
  - Wage tax handbook for 2025 assessment period
  - Includes guidance on Werbungskosten

- **BMF-Schreiben (Official Circulars)**
  - Published throughout the year
  - Provide clarification on specific tax topics
  - **Example**: BMF-Schreiben vom 15.8.2023 (Homeoffice-Pauschale guidance)

### 2. Einkommensteuergesetz (EStG)

**German Income Tax Act**

The foundational legal text for all income tax matters in Germany.

#### Key Sections for This Project:

- **§9 EStG - Werbungskosten (Income-Related Expenses)**
  - URL: https://www.gesetze-im-internet.de/estg/__9.html
  - Covers:
    - Entfernungspauschale (§9 Abs. 1 Satz 3 Nr. 4) - Commuting deduction
    - Homeoffice-Pauschale (§9 Abs. 1 Satz 3 Nr. 6a) - Home office flat rate

- **§35a EStG - Steuerermäßigung bei Aufwendungen für haushaltsnahe Beschäftigungsverhältnisse, haushaltsnahe Dienstleistungen und Handwerkerleistungen**
  - URL: https://www.gesetze-im-internet.de/estg/__35a.html
  - Covers:
    - Haushaltsnahe Dienstleistungen (§35a Abs. 2) - Household services
    - Handwerkerleistungen (§35a Abs. 3) - Craftsman services

### 3. ELSTER (Elektronische Steuererklärung)

**Official Electronic Tax Filing System**

The German federal and state tax authorities' official e-filing platform.

#### Key Resources:

- **ELSTER Developer Portal**
  - URL: https://www.elster.de/elsterweb/entwickler
  - Registration required for full access
  - Provides:
    - ERiC SDK (ELSTER Rich Client)
    - XML schema specifications
    - Interface documentation
    - Developer forum and support

- **ERiC (ELSTER Rich Client)**
  - Free C library for tax data validation and encryption
  - Used for creating compliant XML submissions
  - Available after developer registration

### 4. SmartRechner.de (Optional)

**Third-Party Tax Calculation Validator**

While not an official government source, SmartRechner.de is widely used for cross-checking tax calculations.

- **Use Case**: Validation of complex progressive tax calculations
- **Status**: Optional for MVP, recommended for production

## Current Tax Rates (2025)

All rates sourced from official BMF publications and EStG:

### Entfernungspauschale (Commuting)
- **€0.30/km** for first 20 kilometers
- **€0.38/km** from 21st kilometer onwards
- **Maximum**: €4,500/year (can be exceeded with public transport proof)
- **Source**: §9 Abs. 1 Satz 3 Nr. 4 EStG

### Homeoffice-Pauschale
- **€6/day** worked from home
- **Maximum**: 210 days/year (€1,260 total)
- **Source**: §9 Abs. 1 Satz 3 Nr. 6a EStG, BMF-Schreiben vom 15.8.2023

### Haushaltsnahe Dienstleistungen
- **20% of labor costs**
- **Maximum deduction**: €4,000/year
- **Source**: §35a Abs. 2 EStG

### Handwerkerleistungen
- **20% of labor costs + machinery**
- **Maximum deduction**: €1,200/year
- **Source**: §35a Abs. 3 EStG

## How Sources Are Used

### In Knowledge Base Files

Each markdown file in `knowledge_base/deductions/` includes:

1. **Citation at the end**: "## Official Sources" section
2. **Legal references**: EStG paragraph citations
3. **Date stamps**: For time-sensitive regulations
4. **URLs**: Direct links to official sources

### In RAG Responses

When the system answers queries:

1. **Source metadata** is included in vector embeddings
2. **Citations** are returned with answers
3. **Confidence scores** reflect source quality

### Validation

Use the source manager script to validate citations:

```bash
uv run python scripts/source_manager.py validate
uv run python scripts/source_manager.py list-sources
```

## Updates and Maintenance

### When to Update

- **Annually**: After new BMF handbooks are published (typically February/March)
- **When BMF-Schreiben are issued**: Check https://www.bundesfinanzministerium.de
- **After EStG amendments**: Usually with annual tax reform legislation

### How to Update

1. Review official BMF publications
2. Update markdown files with new rates/rules
3. Add new source citations
4. Re-run ingestion: `just ingest-force`
5. Validate: `uv run python scripts/source_manager.py validate`

## Important Disclaimers

⚠️ **This system provides information only, not legal advice**

- All information is based on official sources
- Tax law is complex and situation-dependent
- **Always recommend** users consult a Steuerberater for:
  - Complex situations
  - Large deductions
  - Audit situations
  - Business/self-employment questions

⚠️ **Timeliness**

- Tax law changes annually
- BMF guidance can be issued mid-year
- Always check publication dates
- This knowledge base was last updated: **January 2025**

## Additional Resources

### For Developers

- **Gesetze im Internet**: https://www.gesetze-im-internet.de/
  - Full text of all German laws, including EStG
  - Free, official, always current

- **BMF Service Portal**: https://www.bundesfinanzministerium.de/Content/DE/Standardartikel/Service/service.html
  - Forms, calculators, BMF-Schreiben archive

### For Users

- **ELSTER Help**: https://www.elster.de/eportal/hilfe
  - Official help documentation for tax filers

- **Finanzamt Finder**: https://www.bzst.de/
  - Find your local tax office

- **Steuerberater Search**: https://www.bstbk.de/
  - Find certified tax advisors (Bundessteuerberaterkammer)

## Questions or Issues?

If you find outdated information or missing citations:

1. Check the official BMF website for updates
2. Update the relevant markdown file
3. Run source validation
4. Submit a pull request (if contributing to open source)

**Last Updated**: January 31, 2026
**Next Review Due**: March 2026 (after 2025 tax season)
