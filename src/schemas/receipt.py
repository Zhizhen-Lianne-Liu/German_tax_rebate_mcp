"""
Pydantic schemas for receipt data.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
import uuid


class ReceiptItem(BaseModel):
    """Individual line item on a receipt"""
    description: str
    amount: float = Field(..., ge=0)
    category: Optional[str] = None


class Receipt(BaseModel):
    """
    Receipt data model with validation.
    Stored in SQLite with file path reference.
    """

    # Metadata
    receipt_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    created_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)

    # Receipt details
    tax_year: int
    date: date
    merchant_name: str
    merchant_address: Optional[str] = None
    merchant_tax_id: Optional[str] = None  # Steuernummer on receipt

    # Financial
    total_amount: float = Field(..., ge=0)
    vat_amount: Optional[float] = Field(default=None, ge=0)
    vat_rate: Optional[float] = Field(default=None, ge=0, le=1)
    labor_costs: Optional[float] = Field(default=None, ge=0)  # For household/craftsman
    material_costs: Optional[float] = Field(default=None, ge=0)

    # Line items
    items: list[ReceiptItem] = Field(default_factory=list)

    # Payment
    payment_method: Literal[
        'bank_transfer',
        'debit_card',
        'credit_card',
        'direct_debit',
        'cash',
        'unknown'
    ]

    # Categorization
    category: Optional[Literal[
        'commuting',
        'home_office',
        'work_equipment',
        'household_services',
        'craftsman',
        'insurance',
        'donations',
        'professional_development',
        'uncategorized'
    ]] = 'uncategorized'
    deduction_type: Optional[Literal[
        'Werbungskosten',
        'Sonderausgaben',
        'Haushaltsnahe Dienstleistungen',
        'Handwerkerleistungen'
    ]] = None

    # Linking
    linked_deduction_id: Optional[str] = None

    # OCR metadata
    ocr_confidence: float = Field(default=0.0, ge=0, le=1)
    manually_verified: bool = False

    # Validation
    validation_status: Literal['valid', 'warning', 'invalid', 'pending'] = 'pending'
    validation_messages: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "receipt_id": "660e8400-e29b-41d4-a716-446655440000",
                "file_path": "data/receipts/2025/household_services/2025-03-15_CleanService_€120.00.pdf",
                "tax_year": 2025,
                "date": "2025-03-15",
                "merchant_name": "Berlin Clean Service GmbH",
                "total_amount": 120.0,
                "labor_costs": 120.0,
                "payment_method": "bank_transfer",
                "category": "household_services",
                "deduction_type": "Haushaltsnahe Dienstleistungen",
                "validation_status": "valid"
            }
        }

    def is_valid_for_household_service(self) -> tuple[bool, list[str]]:
        """
        Validate receipt for Haushaltsnahe Dienstleistungen deduction.

        Requirements:
        - Payment via bank transfer (NOT cash)
        - Labor costs itemized separately
        - Merchant details present
        """
        errors = []

        if self.payment_method == 'cash':
            errors.append("Household services must be paid via bank transfer (not cash)")

        if self.labor_costs is None or self.labor_costs <= 0:
            errors.append("Labor costs must be itemized separately from materials")

        if not self.merchant_address:
            errors.append("Merchant address required for household service deduction")

        return (len(errors) == 0, errors)

    def is_valid_for_craftsman(self) -> tuple[bool, list[str]]:
        """
        Validate receipt for Handwerkerleistungen deduction.

        Requirements:
        - Labor and materials separated
        - Not new construction
        - Merchant details present
        """
        errors = []
        warnings = []

        if self.labor_costs is None:
            errors.append("Labor costs must be itemized separately from materials")

        if self.payment_method == 'cash':
            warnings.append("Cash payment may be questioned by Finanzamt - bank transfer preferred")

        # Check for new construction keywords (not deductible)
        new_construction_keywords = ['neubau', 'new construction', 'erstbezug']
        if any(keyword in self.merchant_name.lower() or
               (self.items and any(keyword in item.description.lower() for item in self.items))
               for keyword in new_construction_keywords):
            errors.append("New construction work is NOT deductible as Handwerkerleistungen")

        return (len(errors) == 0, errors + warnings)

    def requires_depreciation(self) -> bool:
        """Check if work equipment requires depreciation (>€800)"""
        if self.category == 'work_equipment':
            return self.total_amount > 800
        return False
