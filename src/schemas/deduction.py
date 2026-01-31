"""
Pydantic schemas for tax deduction calculations.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class DeductionResult(BaseModel):
    """Standard result format for deduction calculations"""
    amount: float = Field(..., ge=0)
    calculation: str
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class CommutingDeduction(DeductionResult):
    """Result of commuting deduction calculation"""
    distance_km: float
    workdays: int
    rate_standard: float = 0.30
    rate_extended: float = 0.38
    capped_at_max: bool = False


class HomeOfficeDeduction(DeductionResult):
    """Result of home office deduction calculation"""
    days_claimed: int
    days_used: int  # May be capped at 210
    daily_rate: float = 6.0
    max_reached: bool = False


class HouseholdServiceDeduction(DeductionResult):
    """Result of household service deduction calculation"""
    labor_costs: float
    rate: float = 0.20
    receipts_count: int
    invalid_receipts: list[str] = Field(default_factory=list)


class CraftsmanDeduction(DeductionResult):
    """Result of craftsman service deduction calculation"""
    labor_costs: float
    rate: float = 0.20
    receipts_count: int
    invalid_receipts: list[str] = Field(default_factory=list)


class RefundEstimate(BaseModel):
    """Comprehensive tax refund estimate"""
    estimated_refund: float
    confidence: Literal['high', 'medium', 'low']

    # Breakdown
    gross_income: float
    total_deductions: float
    taxable_income: float
    calculated_tax: float
    tax_paid: float

    # Deduction details
    werbungskosten: float = 0
    sonderausgaben: float = 0
    haushaltsnahe_dienstleistungen: float = 0
    handwerkerleistungen: float = 0

    # Assumptions and warnings
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "estimated_refund": 1234.56,
                "confidence": "high",
                "gross_income": 45000.0,
                "total_deductions": 5000.0,
                "taxable_income": 40000.0,
                "calculated_tax": 8500.0,
                "tax_paid": 9734.56,
                "werbungskosten": 3500.0,
                "sonderausgaben": 1500.0,
                "assumptions": [
                    "Used standard work equipment allowance (€1,230)",
                    "Assumed 30 vacation days"
                ]
            }
        }
