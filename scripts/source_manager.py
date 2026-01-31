#!/usr/bin/env python3
"""
Source Manager for German Tax Knowledge Base

Manages official sources and ensures all knowledge base files have proper citations.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import date


@dataclass
class OfficialSource:
    """Represents an official German tax law source"""
    source_id: str
    title: str
    source_type: str  # 'bmf_schreiben', 'estg', 'handbook', 'elster_doc'
    url: Optional[str]
    date_published: Optional[date]
    legal_reference: Optional[str]  # e.g., "§9 EStG", "§35a EStG"
    description: str

    def to_citation(self) -> str:
        """Generate a formatted citation"""
        parts = [f"**{self.title}**"]

        if self.legal_reference:
            parts.append(f"({self.legal_reference})")

        if self.date_published:
            parts.append(f"dated {self.date_published.strftime('%B %d, %Y')}")

        if self.url:
            parts.append(f"[Link]({self.url})")

        return " ".join(parts)


# Official Sources Registry
OFFICIAL_SOURCES = {
    # Homeoffice-Pauschale
    "bmf_2023_08_15_homeoffice": OfficialSource(
        source_id="bmf_2023_08_15_homeoffice",
        title="BMF-Schreiben zur Homeoffice-Pauschale",
        source_type="bmf_schreiben",
        url="https://www.bundesfinanzministerium.de",
        date_published=date(2023, 8, 15),
        legal_reference="§9 Abs. 1 Satz 3 Nr. 6a EStG",
        description="Official guidance on home office flat rate deduction (€6/day, max 210 days)"
    ),

    # Entfernungspauschale
    "estg_9_entfernungspauschale": OfficialSource(
        source_id="estg_9_entfernungspauschale",
        title="Einkommensteuergesetz (EStG) §9 - Werbungskosten",
        source_type="estg",
        url="https://www.gesetze-im-internet.de/estg/__9.html",
        date_published=None,
        legal_reference="§9 Abs. 1 Satz 3 Nr. 4 EStG",
        description="Commuting deduction: €0.30/km (first 20km), €0.38/km (21km+)"
    ),

    # §35a EStG - Haushaltsnahe Dienstleistungen
    "estg_35a_haushaltsnahe": OfficialSource(
        source_id="estg_35a_haushaltsnahe",
        title="Einkommensteuergesetz (EStG) §35a - Haushaltsnahe Dienstleistungen",
        source_type="estg",
        url="https://www.gesetze-im-internet.de/estg/__35a.html",
        date_published=None,
        legal_reference="§35a Abs. 2 EStG",
        description="Household services: 20% of labor costs, max €4,000 deduction"
    ),

    # §35a EStG - Handwerkerleistungen
    "estg_35a_handwerker": OfficialSource(
        source_id="estg_35a_handwerker",
        title="Einkommensteuergesetz (EStG) §35a - Handwerkerleistungen",
        source_type="estg",
        url="https://www.gesetze-im-internet.de/estg/__35a.html",
        date_published=None,
        legal_reference="§35a Abs. 3 EStG",
        description="Craftsman services: 20% of labor costs, max €1,200 deduction"
    ),

    # BMF Einkommensteuer-Handbuch
    "bmf_esth_2024": OfficialSource(
        source_id="bmf_esth_2024",
        title="Amtliches Einkommensteuer-Handbuch 2024",
        source_type="handbook",
        url="https://esth.bundesfinanzministerium.de/",
        date_published=date(2024, 1, 1),
        legal_reference=None,
        description="Official BMF handbook covering all EStG provisions"
    ),

    # BMF Lohnsteuer-Handbuch 2025
    "bmf_lsth_2025": OfficialSource(
        source_id="bmf_lsth_2025",
        title="Amtliches Lohnsteuer-Handbuch 2025",
        source_type="handbook",
        url="https://esth.bundesfinanzministerium.de/lsth/2025/",
        date_published=date(2025, 1, 1),
        legal_reference=None,
        description="Official wage tax handbook for 2025"
    ),

    # ELSTER
    "elster_dev_portal": OfficialSource(
        source_id="elster_dev_portal",
        title="ELSTER Developer Portal",
        source_type="elster_doc",
        url="https://www.elster.de/elsterweb/entwickler",
        date_published=None,
        legal_reference=None,
        description="Official ELSTER XML schema and ERiC SDK documentation"
    ),
}


def validate_markdown_citations(file_path: Path) -> dict:
    """
    Validate that a markdown file has proper source citations.

    Returns:
        dict with 'valid': bool, 'sources_found': List[str], 'issues': List[str]
    """
    content = file_path.read_text(encoding='utf-8')

    issues = []
    sources_found = []

    # Check for Sources section
    if "## Sources" not in content and "## Official Sources" not in content:
        issues.append("Missing '## Sources' or '## Official Sources' section")

    # Check for source IDs in content
    for source_id, source in OFFICIAL_SOURCES.items():
        if source_id in content or (source.legal_reference and source.legal_reference in content):
            sources_found.append(source_id)

    if not sources_found:
        issues.append("No recognized official sources found")

    return {
        'valid': len(issues) == 0,
        'sources_found': sources_found,
        'issues': issues
    }


def generate_sources_section(source_ids: List[str]) -> str:
    """Generate a formatted Sources section for markdown files"""
    lines = [
        "",
        "## Official Sources",
        "",
        "This information is based on the following official German tax law sources:",
        ""
    ]

    for source_id in source_ids:
        if source_id in OFFICIAL_SOURCES:
            source = OFFICIAL_SOURCES[source_id]
            lines.append(f"- {source.to_citation()}")
            lines.append(f"  - {source.description}")
            lines.append("")

    lines.append("**Note:** Always verify current rates and regulations with the latest BMF publications or consult a Steuerberater for complex situations.")
    lines.append("")

    return "\n".join(lines)


def add_sources_to_file(file_path: Path, source_ids: List[str]):
    """Add or update the Sources section in a markdown file"""
    content = file_path.read_text(encoding='utf-8')

    # Remove existing Sources section if present
    if "## Sources" in content or "## Official Sources" in content:
        # Find and remove the section
        lines = content.split('\n')
        new_lines = []
        in_sources_section = False

        for line in lines:
            if line.startswith("## Sources") or line.startswith("## Official Sources"):
                in_sources_section = True
                continue
            elif in_sources_section and line.startswith("## "):
                in_sources_section = False

            if not in_sources_section:
                new_lines.append(line)

        content = '\n'.join(new_lines).strip()

    # Add new Sources section at the end
    sources_section = generate_sources_section(source_ids)
    new_content = content + "\n\n" + sources_section

    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ Added sources to {file_path.name}")


def validate_knowledge_base(kb_dir: Path):
    """Validate all markdown files in knowledge base"""
    print("\n📊 Validating Knowledge Base Citations\n")
    print("=" * 60)

    all_valid = True

    for md_file in kb_dir.rglob("*.md"):
        result = validate_markdown_citations(md_file)

        status = "✅" if result['valid'] else "❌"
        print(f"\n{status} {md_file.relative_to(kb_dir)}")

        if result['sources_found']:
            print(f"   Sources: {', '.join(result['sources_found'])}")

        if result['issues']:
            all_valid = False
            for issue in result['issues']:
                print(f"   ⚠️  {issue}")

    print("\n" + "=" * 60)

    if all_valid:
        print("✅ All files have proper citations!")
    else:
        print("❌ Some files need citation updates")

    return all_valid


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Project root
    project_root = Path(__file__).parent.parent
    kb_dir = project_root / "knowledge_base"

    if len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate_knowledge_base(kb_dir)
    elif len(sys.argv) > 1 and sys.argv[1] == "list-sources":
        print("\n📚 Official Sources Registry\n")
        print("=" * 80)
        for source_id, source in OFFICIAL_SOURCES.items():
            print(f"\n🔹 {source_id}")
            print(f"   {source.title}")
            print(f"   Type: {source.source_type}")
            if source.legal_reference:
                print(f"   Legal ref: {source.legal_reference}")
            if source.url:
                print(f"   URL: {source.url}")
            print(f"   {source.description}")
    else:
        print("Usage:")
        print("  python source_manager.py validate       - Validate all markdown files")
        print("  python source_manager.py list-sources   - List all official sources")
