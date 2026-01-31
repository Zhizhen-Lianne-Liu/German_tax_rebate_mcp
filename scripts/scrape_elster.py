#!/usr/bin/env python3
"""
Scrape German tax rules from official sources:
- ELSTER (https://www.elster.de/)
- Bundesfinanzministerium (https://www.bundesfinanzministerium.de/)
- German Tax Code (https://www.gesetze-im-internet.de/estg_1997/)

Stores directly in PostgreSQL with full-text search (no API embeddings needed).
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time
import re
from typing import List, Dict, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'german_tax',
    'user': 'tax_user',
    'password': 'tax_password_local_only'
}


class TaxRuleScraper:
    """Scrape German tax rules from official sources"""

    def __init__(self, init_tables=True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

        # Connect to PostgreSQL only if needed for storage
        if init_tables:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
            self._init_tables()

    def _init_tables(self):
        """Create tables with full-text search support"""
        collections = ['tax_law', 'forms', 'deductions']

        for collection in collections:
            # Drop old table if exists (from vector version)
            self.cursor.execute(f"DROP TABLE IF EXISTS {collection} CASCADE")

            # Create new table with tsvector for full-text search
            self.cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {collection} (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    text TEXT NOT NULL,
                    url TEXT,
                    section TEXT,
                    ts_vector tsvector,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create GIN index for full-text search
            self.cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS {collection}_ts_idx
                ON {collection} USING GIN(ts_vector)
            """)

            # Create trigger to auto-update tsvector
            self.cursor.execute(f"""
                CREATE OR REPLACE FUNCTION {collection}_tsvector_trigger()
                RETURNS trigger AS $$
                BEGIN
                    NEW.ts_vector :=
                        setweight(to_tsvector('german', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('german', COALESCE(NEW.text, '')), 'B');
                    RETURN NEW;
                END
                $$ LANGUAGE plpgsql;
            """)

            self.cursor.execute(f"""
                DROP TRIGGER IF EXISTS tsvectorupdate ON {collection};
                CREATE TRIGGER tsvectorupdate
                BEFORE INSERT OR UPDATE ON {collection}
                FOR EACH ROW EXECUTE FUNCTION {collection}_tsvector_trigger();
            """)

        self.conn.commit()
        print("✅ Database tables created with full-text search support")

    def scrape_estg_sections(self) -> List[Dict]:
        """Scrape German Income Tax Act (EStG) sections"""
        print("\n📜 Scraping EStG (German Income Tax Act)...")

        base_url = "https://www.gesetze-im-internet.de/estg"
        documents = []

        # Key sections for deductions (use 2 underscores)
        sections = {
            '9': 'Werbungskosten (Work-related expenses)',
            '9a': 'Pauschbeträge für Werbungskosten (Standard deductions)',
            '35a': 'Haushaltsnahe Dienstleistungen (Household services)',
        }

        for section_num, description in sections.items():
            try:
                url = f"{base_url}/__{section_num}.html"
                print(f"  Fetching §{section_num}: {description}")

                response = self.session.get(url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract section title and content
                title_elem = soup.find('h1') or soup.find('h2')
                title = title_elem.get_text(strip=True) if title_elem else f"§{section_num} EStG"

                # Get main content
                content_div = soup.find('div', class_='jnhtml') or soup.find('div', class_='jurAbsatz')
                if content_div:
                    # Clean up HTML
                    text = content_div.get_text(separator='\n\n', strip=True)

                    # Remove excessive whitespace
                    text = re.sub(r'\n{3,}', '\n\n', text)

                    documents.append({
                        'title': title,
                        'text': text,
                        'url': url,
                        'section': f"§{section_num} EStG",
                        'source': 'EStG',
                        'category': 'tax_law'
                    })

                    print(f"    ✓ {len(text)} characters")
                else:
                    print(f"    ⚠️  No content found")

                time.sleep(0.5)  # Polite scraping

            except Exception as e:
                print(f"    ❌ Error: {e}")

        return documents

    def scrape_bmf_handbook(self) -> List[Dict]:
        """Scrape BMF Official Handbooks"""
        print("\n📘 Scraping BMF Official Handbooks...")

        documents = []

        # Try to scrape from BMF EStH (Einkommensteuer-Handbuch)
        try:
            url = "https://esth.bundesfinanzministerium.de/"
            print(f"  Fetching BMF EStH homepage...")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract main content
            content_div = soup.find('div', class_='content') or soup.find('main') or soup.find('article')

            if content_div:
                text = content_div.get_text(separator='\n\n', strip=True)
                text = re.sub(r'\n{3,}', '\n\n', text)

                documents.append({
                    'title': 'BMF Einkommensteuer-Handbuch Overview',
                    'text': text[:2000],  # Limit to first 2000 chars
                    'url': url,
                    'section': 'BMF EStH',
                    'source': 'BMF',
                    'category': 'tax_law'
                })

                print(f"    ✓ Extracted {len(text)} characters")
            else:
                print(f"    ⚠️  No content found")

        except Exception as e:
            print(f"    ⚠️  BMF website error: {e}")

        print(f"  Note: BMF handbook requires navigation - using curated content")

        return documents

    def scrape_bmf_circulars(self) -> List[Dict]:
        """Scrape BMF (Federal Ministry of Finance) circulars about deductions"""
        print("\n📋 Scraping BMF circulars...")

        # Manual entries for key BMF circulars (2025 rates)
        documents = [
            {
                'title': 'Entfernungspauschale (Commuting Allowance) 2025',
                'text': '''
                The Entfernungspauschale allows employees to deduct commuting costs.

                Rates for 2025:
                - First 20 km: €0.30 per km per working day
                - From 21st km onwards: €0.38 per km per working day
                - Maximum annual deduction: €4,500

                Calculation:
                Total deduction = (distance_km * days_worked * rate_per_km)

                Example:
                - Distance: 15 km one way
                - Working days: 220 days
                - Calculation: 15 km × 220 days × €0.30 = €990

                Requirements:
                - Only one-way distance counts
                - Only actual working days in office
                - Must be regular workplace (not home office days)

                Documentation needed:
                - Employment contract showing workplace address
                - Statement of working days in office
                ''',
                'url': 'https://www.bundesfinanzministerium.de/',
                'section': 'Entfernungspauschale',
                'source': 'BMF',
                'category': 'deductions'
            },
            {
                'title': 'Homeoffice-Pauschale (Home Office Allowance) 2025',
                'text': '''
                The Homeoffice-Pauschale allows employees to deduct home office costs.

                Rates for 2025:
                - €6 per home office day
                - Maximum 210 days per year
                - Maximum annual deduction: €1,260

                Calculation:
                Total deduction = min(days_worked_from_home * 6, 1260)

                Example:
                - Home office days: 180 days
                - Calculation: 180 × €6 = €1,080

                Requirements:
                - Full working days from home
                - Cannot combine with commuting deduction for same day
                - No separate home office room required
                - Applies even if employer provides office space

                Documentation needed:
                - Statement of home office days
                - Employment contract or employer confirmation
                ''',
                'url': 'https://www.bundesfinanzministerium.de/',
                'section': 'Homeoffice-Pauschale',
                'source': 'BMF',
                'category': 'deductions'
            },
            {
                'title': 'Haushaltsnahe Dienstleistungen (Household Services) 2025',
                'text': '''
                Tax credit for household services and craftsman services.

                Household Services (§35a EStG):
                - 20% of labor costs can be claimed as tax credit
                - Maximum €4,000 tax credit per year (on €20,000 expenses)
                - Includes: cleaning, gardening, care services
                - Must be performed at your residence
                - Payment must be bank transfer (no cash)

                Craftsman Services (§35a EStG):
                - 20% of labor costs can be claimed as tax credit
                - Maximum €1,200 tax credit per year (on €6,000 expenses)
                - Includes: renovations, repairs, maintenance
                - Materials not eligible, only labor costs
                - Must be bank transfer payment

                Example:
                - Cleaner: €3,000 labor costs → €600 tax credit
                - Plumber: €1,500 labor costs → €300 tax credit
                - Total tax credit: €900 (reduces tax owed)

                Requirements:
                - Invoice must separately show labor costs
                - Payment proof (bank statement)
                - Service at household residence
                ''',
                'url': 'https://www.bundesfinanzministerium.de/',
                'section': '§35a EStG',
                'source': 'BMF',
                'category': 'deductions'
            },
            {
                'title': 'Arbeitsmittel (Work Equipment) Deduction',
                'text': '''
                Work equipment and professional development costs are deductible as Werbungskosten.

                Examples of deductible work equipment:
                - Computer and software (if > €800, depreciate over 3 years)
                - Office furniture (desk, chair)
                - Professional books and subscriptions
                - Tools and specialized equipment
                - Work clothing (if specific to profession)

                Professional development:
                - Training courses related to current job
                - Professional certifications
                - Conference attendance
                - Professional association fees

                Simplified rule for electronics < €800:
                - Can deduct full amount in purchase year
                - No depreciation required

                Documentation needed:
                - Purchase receipts
                - Explanation of professional use
                - If personal use possible, estimate business percentage
                ''',
                'url': 'https://www.bundesfinanzministerium.de/',
                'section': 'Werbungskosten §9 EStG',
                'source': 'BMF',
                'category': 'deductions'
            },
            {
                'title': 'Werbungskostenpauschale (Standard Work-Related Deduction)',
                'text': '''
                Automatic standard deduction for all employees.

                Amount for 2025:
                - €1,230 per year (automatically applied)

                How it works:
                - You automatically get €1,230 deduction without proof
                - Only itemize work expenses if they exceed €1,230
                - If your total work expenses < €1,230, you still get €1,230

                Common expenses that may exceed €1,230:
                - Commuting: 20 km × 220 days × €0.30 = €1,320
                - Home office: 210 days × €6 = €1,260
                - Work equipment: Computer, desk, etc.
                - Professional development courses

                Strategy:
                - Calculate your total Werbungskosten
                - If > €1,230, itemize everything
                - If < €1,230, accept automatic standard deduction
                ''',
                'url': 'https://www.bundesfinanzministerium.de/',
                'section': 'Arbeitnehmer-Pauschbetrag §9a EStG',
                'source': 'BMF',
                'category': 'deductions'
            },
        ]

        for doc in documents:
            print(f"  ✓ {doc['title']}")

        return documents

    def scrape_elster_forms(self) -> List[Dict]:
        """Information about ELSTER forms"""
        print("\n📝 Adding ELSTER form information...")

        documents = [
            {
                'title': 'ELSTER Tax Return Overview',
                'text': '''
                ELSTER (Elektronische Steuererklärung) is Germany's electronic tax filing system.

                Main forms for employees (Arbeitnehmer):
                - Hauptvordruck (Main form): Personal information, income overview
                - Anlage N: Employment income and work-related expenses (Werbungskosten)
                - Anlage Vorsorgeaufwand: Insurance contributions
                - Anlage Kind: Child-related deductions

                Required information:
                - Tax ID (Steuer-Identifikationsnummer): 11 digits
                - Personal data: Name, address, birthdate
                - IBAN: For refund transfers
                - Income: Gross income and tax paid (from Lohnsteuerbescheinigung)

                Anlage N (Employment income):
                - Line 31-40: Werbungskosten (work expenses)
                - Line 31: Commuting (Entfernungspauschale)
                - Line 43: Home office (Homeoffice-Pauschale)
                - Line 41-42: Professional development
                - Line 44-48: Other work-related expenses

                Common mistakes to avoid:
                - Forgetting to claim work expenses over €1,230
                - Not claiming both commuting AND home office (for different days)
                - Missing household services tax credit
                - Incorrect calculation of working days
                ''',
                'url': 'https://www.elster.de/',
                'section': 'ELSTER Overview',
                'source': 'ELSTER',
                'category': 'forms'
            },
        ]

        for doc in documents:
            print(f"  ✓ {doc['title']}")

        return documents

    def store_documents(self, documents: List[Dict]):
        """Store documents in PostgreSQL with full-text search"""
        if not documents:
            print("  No documents to store")
            return

        print(f"\n💾 Storing {len(documents)} documents...")

        for doc in documents:
            category = doc.pop('category')

            self.cursor.execute(f"""
                INSERT INTO {category} (title, text, url, section, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                doc['title'],
                doc['text'],
                doc.get('url'),
                doc.get('section'),
                psycopg2.extras.Json({'source': doc.get('source', 'Unknown')})
            ))

        self.conn.commit()
        print("  ✅ Documents stored")

    def get_stats(self):
        """Print database statistics"""
        print("\n" + "=" * 60)
        print("Database Statistics")
        print("=" * 60)

        for collection in ['tax_law', 'forms', 'deductions']:
            self.cursor.execute(f"SELECT COUNT(*) FROM {collection}")
            count = self.cursor.fetchone()[0]
            print(f"  {collection}: {count} documents")

    def close(self):
        """Close database connection"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Main scraping process"""
    print("=" * 60)
    print("German Tax Rules Scraper")
    print("Scraping from official sources (ELSTER, BMF, EStG)")
    print("=" * 60)

    scraper = TaxRuleScraper()

    try:
        # Scrape all sources
        all_documents = []

        # 1. EStG (German Tax Code)
        all_documents.extend(scraper.scrape_estg_sections())

        # 2. BMF Circulars (Deduction rules)
        all_documents.extend(scraper.scrape_bmf_circulars())

        # 3. ELSTER Forms
        all_documents.extend(scraper.scrape_elster_forms())

        # Store everything
        scraper.store_documents(all_documents)

        # Show stats
        scraper.get_stats()

        print("\n✅ Scraping complete! RAG database ready for queries.")
        print("   Using PostgreSQL full-text search (no API needed)")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
