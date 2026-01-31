"""
Pydantic schemas for user profile data.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date
import uuid


class Child(BaseModel):
    """Child information for tax deductions"""
    birth_year: int = Field(..., ge=1900, le=2025)
    receives_kindergeld: bool = True


class UserProfile(BaseModel):
    """
    Complete user profile for German tax filing.
    Stored as JSON in data/profiles/
    """

    # Metadata
    profile_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: date = Field(default_factory=date.today)
    updated_at: date = Field(default_factory=date.today)
    tax_year: int = Field(default=2025, ge=2020, le=2030)

    # Personal information
    marital_status: Literal['single', 'married', 'divorced', 'widowed']
    tax_class: Literal['I', 'II', 'III', 'IV', 'V', 'VI']
    children: list[Child] = Field(default_factory=list)

    # Employment
    employment_type: Literal[
        'employee',
        'self_employed',
        'mixed',
        'retired',
        'student',
        'unemployed'
    ]
    multiple_employers: bool = False
    home_office_days: int = Field(default=0, ge=0, le=365)
    work_address: Optional[str] = None
    commute_distance_km: Optional[float] = Field(default=None, ge=0)
    commute_method: Literal['car', 'public_transport', 'bicycle', 'mixed'] = 'car'

    # Residence
    home_address: str
    postal_code: str = Field(..., pattern=r'^\d{5}$')
    days_in_germany: int = Field(default=365, ge=0, le=365)
    moved_in_date: Optional[date] = None
    moved_out_date: Optional[date] = None
    previous_country: Optional[str] = None

    # Income sources
    has_employment_income: bool = True
    has_self_employment_income: bool = False
    has_rental_income: bool = False
    has_foreign_income: bool = False
    foreign_income_country: Optional[str] = None
    has_capital_gains: bool = False
    has_pension: bool = False

    # Tracking preferences
    tracks_home_office: bool = True
    has_household_services: bool = False
    has_craftsman_work: bool = False
    has_professional_training: bool = False
    has_work_equipment: bool = False

    # Reminder settings
    remind_before_deadline_days: int = Field(default=90, ge=0, le=365)
    last_reminded: Optional[date] = None

    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "550e8400-e29b-41d4-a716-446655440000",
                "tax_year": 2025,
                "marital_status": "single",
                "tax_class": "I",
                "children": [],
                "employment_type": "employee",
                "home_office_days": 150,
                "work_address": "Alexanderplatz 1, 10178 Berlin",
                "commute_distance_km": 15.0,
                "home_address": "Prenzlauer Allee 100, 10409 Berlin",
                "postal_code": "10409",
                "days_in_germany": 365,
                "has_employment_income": True
            }
        }

    def calculate_workdays(self, vacation_days: int = 30) -> int:
        """Calculate effective workdays (accounting for home office and vacation)"""
        standard_workdays = 230  # ~52 weeks × 5 days - holidays
        office_days = max(0, standard_workdays - self.home_office_days - vacation_days)
        return office_days

    def is_tax_resident(self) -> bool:
        """Check if user qualifies as German tax resident (183-day rule)"""
        return self.days_in_germany >= 183

    def requires_filing(self) -> bool:
        """
        Determine if tax filing is mandatory based on profile.

        Mandatory if:
        - Multiple employers
        - Self-employment income
        - Rental income
        - Foreign income
        - Capital gains > €801
        - Tax class VI
        - Couple with both earning (Steuerklasse III/V or IV/IV with income difference)
        """
        if self.multiple_employers:
            return True
        if self.has_self_employment_income or self.has_rental_income:
            return True
        if self.has_foreign_income:
            return True
        if self.tax_class == 'VI':
            return True

        return False

    def get_required_forms(self) -> list[str]:
        """Determine which ELSTER forms are needed based on profile"""
        forms = ['ESt 1 V']  # Main form always required

        if self.has_employment_income:
            forms.append('Anlage N')

        if self.children:
            forms.append('Anlage Kind')

        forms.append('Anlage Vorsorgeaufwand')  # Insurance (almost always applies)

        if self.has_self_employment_income:
            forms.extend(['Anlage S', 'Anlage EÜR'])

        if self.has_rental_income:
            forms.append('Anlage V')

        if self.has_foreign_income:
            forms.append('Anlage AUS')

        if self.has_capital_gains:
            forms.append('Anlage KAP')

        return forms
