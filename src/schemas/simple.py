"""
Simplified schemas for MVP.
Session-based, no persistence.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date


class TaxQuestions(BaseModel):
    """Key questions for tax calculation"""
    # From Lohnsteuerbescheinigung
    gross_income: float = Field(..., ge=0, description="Gross annual income (€)")
    income_tax_paid: float = Field(..., ge=0, description="Income tax already paid (€)")

    # Personal
    marital_status: Literal['single', 'married', 'divorced', 'widowed']
    tax_class: Literal['I', 'II', 'III', 'IV', 'V', 'VI']
    num_children: int = Field(default=0, ge=0)

    # Work
    work_address: str
    home_address: str
    home_office_days: int = Field(default=0, ge=0, le=365)

    # IDs
    steuer_id: str = Field(..., pattern=r'^\d{11}$', description="11-digit Tax ID")
    postal_code: str = Field(..., pattern=r'^\d{5}$')


class ScannedReceipt(BaseModel):
    """Result of scanning a receipt"""
    file_path: str
    date: Optional[date] = None
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
