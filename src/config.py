"""
Configuration settings for German Tax MCP Server.
Loads from environment variables and defines constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

# User data directories
PROFILES_DIR = DATA_DIR / "profiles"
RECEIPTS_DIR = DATA_DIR / "receipts"
DOCUMENTS_DIR = DATA_DIR / "documents"
EXPORTS_DIR = DATA_DIR / "exports"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Ensure directories exist
for directory in [PROFILES_DIR, RECEIPTS_DIR, DOCUMENTS_DIR, EXPORTS_DIR, VECTOR_DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Optional pre-filled profile data
STEUER_ID = os.getenv("STEUER_ID", "")
POSTAL_CODE = os.getenv("POSTAL_CODE", "")
TAX_CLASS = os.getenv("TAX_CLASS", "I")

# Cloud services (optional)
USE_CLOUD_OCR = os.getenv("USE_CLOUD_OCR", "false").lower() == "true"
GOOGLE_CLOUD_VISION_API_KEY = os.getenv("GOOGLE_CLOUD_VISION_API_KEY", "")

# Development
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Tax year constants (2025) - Update annually
class TaxRates2025:
    """German tax rates and thresholds for 2025"""

    # Income tax
    BASIC_ALLOWANCE = 11604  # Grundfreibetrag (€)
    SOLIDARITY_SURCHARGE_THRESHOLD = 18130  # Soli threshold (€)
    SOLIDARITY_SURCHARGE_RATE = 0.055  # 5.5%

    # Commuting deduction (Entfernungspauschale)
    COMMUTE_RATE_STANDARD = 0.30  # €/km for first 20km
    COMMUTE_RATE_EXTENDED = 0.38  # €/km from 21st km onwards
    COMMUTE_THRESHOLD_KM = 20
    COMMUTE_MAX_DEDUCTION = 4500  # Maximum annual deduction (€)

    # Home office (Homeoffice-Pauschale)
    HOME_OFFICE_DAILY_RATE = 6  # €/day
    HOME_OFFICE_MAX_DAYS = 210  # Maximum deductible days
    HOME_OFFICE_MAX_DEDUCTION = 1260  # 210 days × €6

    # Household services (Haushaltsnahe Dienstleistungen)
    HOUSEHOLD_SERVICE_RATE = 0.20  # 20% of labor costs
    HOUSEHOLD_SERVICE_MAX = 4000  # Maximum annual deduction (€)

    # Craftsman services (Handwerkerleistungen)
    CRAFTSMAN_RATE = 0.20  # 20% of labor costs
    CRAFTSMAN_MAX = 1200  # Maximum annual deduction (€)

    # Work equipment depreciation threshold
    EQUIPMENT_DEPRECIATION_THRESHOLD = 800  # Items >€800 require depreciation
    EQUIPMENT_IMMEDIATE_DEDUCTION_MAX = 952  # Simplified for 2023+

    # Child allowance (Kindergeld)
    KINDERGELD_MONTHLY = 250  # Per child (€) - 2025 rate
    KINDERFREIBETRAG = 6384  # Child tax allowance per child (€)

    # Insurance deduction limits (Sonderausgaben)
    PENSION_CONTRIBUTION_MAX_SINGLE = 27566  # 2025 (€)
    PENSION_CONTRIBUTION_MAX_MARRIED = 55132  # 2025 (€)

    # Standard work days per year
    STANDARD_WORK_DAYS = 230  # Typical after weekends
    AVERAGE_VACATION_DAYS = 30

# Receipt validation requirements
class ReceiptRequirements:
    """German tax office receipt requirements"""

    # Kleinbetragsrechnung (simplified receipt) threshold
    SIMPLIFIED_RECEIPT_THRESHOLD = 250  # €

    # Required fields for deductions
    HOUSEHOLD_SERVICE_REQUIRES_BANK_TRANSFER = True
    CRAFTSMAN_REQUIRES_ITEMIZATION = True  # Labor/materials separate

    # Payment methods
    VALID_PAYMENT_METHODS = [
        "bank_transfer",
        "debit_card",
        "credit_card",
        "direct_debit"
    ]
    INVALID_PAYMENT_METHODS = ["cash"]  # For household/craftsman services

    # Retention periods
    EMPLOYEE_RETENTION_YEARS = 1  # After tax assessment
    SELF_EMPLOYED_RETENTION_YEARS = 10

# RAG configuration
class RAGConfig:
    """Vector database and embedding settings"""

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 512  # tokens
    CHUNK_OVERLAP = 50  # tokens
    TOP_K_RESULTS = 3  # Number of results to return

    COLLECTIONS = {
        "tax_law": "German tax code (EStG, AO)",
        "forms": "ELSTER form instructions",
        "treaties": "Double taxation treaties"
    }

# File naming conventions
class FileNaming:
    """Standardized file naming patterns"""

    @staticmethod
    def receipt_filename(date: str, merchant: str, amount: float, extension: str = "pdf") -> str:
        """Generate standardized receipt filename"""
        # Clean merchant name (remove special chars)
        clean_merchant = "".join(c for c in merchant if c.isalnum() or c in (' ', '-', '_'))
        clean_merchant = clean_merchant.replace(' ', '_')[:30]  # Limit length
        return f"{date}_{clean_merchant}_€{amount:.2f}.{extension}"

    @staticmethod
    def export_filename(tax_year: int, export_type: str, extension: str) -> str:
        """Generate export filename"""
        return f"{tax_year}_{export_type}.{extension}"
