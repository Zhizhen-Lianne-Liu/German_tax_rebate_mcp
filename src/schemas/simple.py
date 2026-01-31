"""
Simplified schemas for MVP.
Session-based, no persistence.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date as DateType


class TaxQuestions(BaseModel):
    """Key questions for tax calculation - Full Taxfix parity"""

    # Personal Identification (NEW - ELSTER Hauptvordruck required)
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    birthdate: DateType = Field(..., description="Date of birth (YYYY-MM-DD)")

    # From Lohnsteuerbescheinigung
    gross_income: float = Field(..., ge=0, description="Gross annual income (€)")
    income_tax_paid: float = Field(..., ge=0, description="Income tax already paid (€)")

    # Personal
    marital_status: Literal['single', 'married', 'divorced', 'widowed']
    tax_class: Literal['I', 'II', 'III', 'IV', 'V', 'VI']
    num_children: int = Field(default=0, ge=0)

    # Religion (optional - ELSTER lines 11, 23)
    religion: Optional[Literal['rk', 'ev', 'none', 'other']] = Field(
        default=None,
        description="Religion: rk=Roman Catholic, ev=Evangelical, none=None, other=Other"
    )

    # Work
    work_address: str
    home_address: str
    home_office_days: int = Field(default=0, ge=0, le=365)

    # Employment details (NEW - Taxfix parity)
    employer_name: Optional[str] = Field(default=None, description="Name of employer")
    employment_start_date: Optional[DateType] = Field(default=None, description="Employment start date (if started this tax year)")
    employment_end_date: Optional[DateType] = Field(default=None, description="Employment end date (if ended this tax year)")

    # Commute (added for accurate calculations)
    commute_distance_km: float = Field(default=0, ge=0, description="One-way commute distance in km")
    office_days: int = Field(default=0, ge=0, le=365, description="Days actually went to office")

    # IDs
    steuer_id: str = Field(..., pattern=r'^\d{11}$', description="11-digit Tax ID")
    postal_code: str = Field(..., pattern=r'^\d{5}$')

    # Bank Details (NEW - for refunds)
    iban: str = Field(..., pattern=r'^DE\d{20}$', description="German IBAN (22 characters starting with DE)")

    # Contact (NEW - Taxfix parity)
    email: str = Field(..., description="Email address for correspondence")
    phone: Optional[str] = Field(default=None, description="Phone number (optional)")

    # Tax preparation assistance (ELSTER line 39)
    tax_advisor_prepared: bool = Field(default=False, description="Was this prepared with a tax advisor?")


class ScannedReceipt(BaseModel):
    """Result of scanning a receipt"""
    file_path: str
    date: Optional[DateType] = None
    merchant: Optional[str] = None
    amount: Optional[float] = None
    category: Optional[Literal[
        'commuting',
        'home_office',
        'work_equipment',
        'household_services',
        'craftsman',
        'insurance',
        'donations',
        'other'
    ]] = 'other'
    confidence: float = Field(default=0.0, ge=0, le=1)
    ocr_text: str = ""


class ReceiptSummary(BaseModel):
    """Summary of all scanned receipts by category"""
    commuting: float = 0
    home_office: float = 0
    work_equipment: float = 0
    household_services: float = 0
    craftsman: float = 0
    insurance: float = 0
    donations: float = 0
    other: float = 0

    total_receipts: int = 0
    total_amount: float = 0


class DeductionsSummary(BaseModel):
    """Calculated deductions"""
    commuting_deduction: float = 0
    home_office_deduction: float = 0
    work_equipment_deduction: float = 0
    household_service_deduction: float = 0
    craftsman_deduction: float = 0
    insurance_deduction: float = 0
    donations_deduction: float = 0

    total_deductions: float = 0
    estimated_refund: float = 0

    breakdown: dict = Field(default_factory=dict)
