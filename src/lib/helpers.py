"""
Helper functions for V2 incremental data collection architecture.

Provides utilities for:
- Completeness calculation
- Data assembly
- Gap analysis
- Smart recommendations
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from schemas.simple import TaxQuestions, DeductionsSummary, ReceiptSummary
from config import TaxRates2025


def calculate_category_completeness(category_data: Dict[str, Any], required_fields: List[str]) -> float:
    """
    Calculate completeness percentage for a category.

    Args:
        category_data: Dictionary of category fields
        required_fields: List of required field names

    Returns:
        Completeness as a float between 0.0 and 1.0
    """
    if not required_fields:
        return 1.0

    filled_count = sum(1 for field in required_fields if category_data.get(field))
    return filled_count / len(required_fields)


def calculate_overall_completeness(session_data: Dict) -> float:
    """
    Calculate overall session completeness for ELSTER submission.

    Returns:
        Completeness as a float between 0.0 and 1.0
    """
    personal_info = session_data.get('personal_info', {})
    income_info = session_data.get('income_info', {})
    tax_status = session_data.get('tax_status', {})
    work_info = session_data.get('work_info', {})

    # Required fields for ELSTER
    personal_required = ['first_name', 'last_name', 'birthdate', 'steuer_id', 'postal_code', 'home_address', 'iban', 'email']
    income_required = ['gross_income', 'income_tax_paid']
    tax_status_required = ['marital_status', 'tax_class']
    work_required = []  # Work info is derived from calculations

    personal_complete = calculate_category_completeness(personal_info, personal_required)
    income_complete = calculate_category_completeness(income_info, income_required)
    tax_complete = calculate_category_completeness(tax_status, tax_status_required)

    # Weighted average (personal and income are most critical)
    overall = (personal_complete * 0.5) + (income_complete * 0.3) + (tax_complete * 0.2)

    return round(overall, 2)


def get_missing_required_fields(session_data: Dict) -> List[str]:
    """
    Identify missing required fields for ELSTER submission.

    Returns:
        List of missing field names with descriptions
    """
    missing = []

    personal_info = session_data.get('personal_info', {})
    income_info = session_data.get('income_info', {})
    tax_status = session_data.get('tax_status', {})

    # Check critical ELSTER fields
    if not personal_info.get('first_name'):
        missing.append("first_name - Your first name")
    if not personal_info.get('last_name'):
        missing.append("last_name - Your last name")
    if not personal_info.get('birthdate'):
        missing.append("birthdate - Your date of birth (YYYY-MM-DD)")
    if not personal_info.get('steuer_id'):
        missing.append("steuer_id - Your 11-digit tax ID")
    if not personal_info.get('postal_code'):
        missing.append("postal_code - Your 5-digit postal code")
    if not personal_info.get('home_address'):
        missing.append("home_address - Your home address")
    if not personal_info.get('iban'):
        missing.append("iban - Your IBAN for refund (22 characters starting with DE)")
    if not personal_info.get('email'):
        missing.append("email - Your email address")

    if not income_info.get('gross_income'):
        missing.append("gross_income - Your gross annual income in EUR")
    if not income_info.get('income_tax_paid'):
        missing.append("income_tax_paid - Income tax already paid in EUR")

    if not tax_status.get('marital_status'):
        missing.append("marital_status - Your marital status (single/married/divorced/widowed)")
    if not tax_status.get('tax_class'):
        missing.append("tax_class - Your tax class (I/II/III/IV/V/VI)")

    return missing


def build_tax_questions_from_session(session_data: Dict) -> TaxQuestions:
    """
    Assemble a TaxQuestions object from session data.

    Args:
        session_data: Complete session dictionary

    Returns:
        TaxQuestions Pydantic model

    Raises:
        ValueError: If required fields are missing
    """
    from datetime import datetime as dt

    personal = session_data.get('personal_info', {})
    income = session_data.get('income_info', {})
    tax_status = session_data.get('tax_status', {})
    work = session_data.get('work_info', {})

    # Convert date strings to date objects if needed
    birthdate = personal.get('birthdate')
    if isinstance(birthdate, str):
        birthdate = dt.strptime(birthdate, '%Y-%m-%d').date()

    employment_start = work.get('employment_start_date')
    if isinstance(employment_start, str):
        employment_start = dt.strptime(employment_start, '%Y-%m-%d').date()

    employment_end = work.get('employment_end_date')
    if isinstance(employment_end, str):
        employment_end = dt.strptime(employment_end, '%Y-%m-%d').date()

    return TaxQuestions(
        # Personal
        first_name=personal.get('first_name'),
        last_name=personal.get('last_name'),
        birthdate=birthdate,
        email=personal.get('email'),
        phone=personal.get('phone'),
        steuer_id=personal.get('steuer_id'),
        postal_code=personal.get('postal_code'),
        home_address=personal.get('home_address'),
        iban=personal.get('iban'),
        # Income
        gross_income=income.get('gross_income'),
        income_tax_paid=income.get('income_tax_paid'),
        # Tax status
        marital_status=tax_status.get('marital_status'),
        tax_class=tax_status.get('tax_class'),
        num_children=tax_status.get('num_children', 0),
        religion=tax_status.get('religion'),
        # Work
        work_address=work.get('work_address') or "Not specified",
        employer_name=work.get('employer_name'),
        employment_start_date=employment_start,
        employment_end_date=employment_end,
        commute_distance_km=work.get('commute_distance_km', 0),
        office_days=work.get('office_days', 0),
        home_office_days=work.get('home_office_days', 0),
        tax_advisor_prepared=personal.get('tax_advisor_prepared', False)
    )


def complete_deductions_calculation(session_data: Dict, questions: TaxQuestions) -> DeductionsSummary:
    """
    Calculate all deductions, using saved calculations where available.

    Args:
        session_data: Complete session dictionary
        questions: TaxQuestions object

    Returns:
        DeductionsSummary with all calculated deductions
    """
    calculations = session_data.get('calculations', {})
    receipts_data = session_data.get('receipts', {})

    # Get receipt summary if available
    if receipts_data.get('summary'):
        receipt_summary = ReceiptSummary(**receipts_data['summary'])
    else:
        receipt_summary = ReceiptSummary()

    # Use saved commuting calculation if available
    if 'commuting' in calculations and calculations['commuting'].get('result'):
        commuting_deduction = calculations['commuting']['result']['amount']
    else:
        # Calculate fresh
        commute_distance = questions.commute_distance_km if questions.commute_distance_km > 0 else 15
        office_days = questions.office_days if questions.office_days > 0 else max(0, 230 - questions.home_office_days - 30)

        if commute_distance <= 20:
            commuting_deduction = commute_distance * office_days * TaxRates2025.COMMUTE_RATE_STANDARD
        else:
            commuting_deduction = (20 * office_days * TaxRates2025.COMMUTE_RATE_STANDARD) + \
                                  ((commute_distance - 20) * office_days * TaxRates2025.COMMUTE_RATE_EXTENDED)

        commuting_deduction = min(commuting_deduction, TaxRates2025.COMMUTE_MAX_DEDUCTION)

    # Use saved home office calculation if available
    if 'home_office' in calculations and calculations['home_office'].get('result'):
        home_office_deduction = calculations['home_office']['result']['amount']
    else:
        # Calculate fresh
        home_office_days_capped = min(questions.home_office_days, TaxRates2025.HOME_OFFICE_MAX_DAYS)
        home_office_deduction = home_office_days_capped * TaxRates2025.HOME_OFFICE_DAILY_RATE

    # Work equipment
    work_equipment_deduction = receipt_summary.work_equipment

    # Household services
    household_service_deduction = min(
        receipt_summary.household_services * TaxRates2025.HOUSEHOLD_SERVICE_RATE,
        TaxRates2025.HOUSEHOLD_SERVICE_MAX
    )

    # Craftsman
    craftsman_deduction = min(
        receipt_summary.craftsman * TaxRates2025.CRAFTSMAN_RATE,
        TaxRates2025.CRAFTSMAN_MAX
    )

    # Insurance
    insurance_deduction = receipt_summary.insurance

    # Donations
    donations_deduction = receipt_summary.donations

    # Total deductions
    total_deductions = (
        commuting_deduction +
        home_office_deduction +
        work_equipment_deduction +
        insurance_deduction +
        donations_deduction
    )

    # Estimate refund
    taxable_income = questions.gross_income - total_deductions
    estimated_tax = taxable_income * 0.25  # Rough estimate
    estimated_refund = questions.income_tax_paid - estimated_tax
    estimated_refund += household_service_deduction + craftsman_deduction

    return DeductionsSummary(
        commuting_deduction=round(commuting_deduction, 2),
        home_office_deduction=round(home_office_deduction, 2),
        work_equipment_deduction=round(work_equipment_deduction, 2),
        household_service_deduction=round(household_service_deduction, 2),
        craftsman_deduction=round(craftsman_deduction, 2),
        insurance_deduction=round(insurance_deduction, 2),
        donations_deduction=round(donations_deduction, 2),
        total_deductions=round(total_deductions, 2),
        estimated_refund=round(estimated_refund, 2)
    )


def suggest_next_steps(session_data: Dict) -> List[str]:
    """
    Suggest what the user should do next based on current progress.

    Returns:
        List of suggested actions
    """
    suggestions = []

    missing = get_missing_required_fields(session_data)
    calculations = session_data.get('calculations', {})
    receipts = session_data.get('receipts', {})

    # Check for missing critical information
    if missing:
        suggestions.append(f"📝 Provide missing information: {', '.join([m.split(' - ')[0] for m in missing[:3]])}")
        if len(missing) > 3:
            suggestions.append(f"   ... and {len(missing) - 3} more fields")

    # Suggest calculations if not done
    if 'commuting' not in calculations:
        suggestions.append("🚗 Calculate your commuting deduction using calculate_commuting_deduction()")

    if 'home_office' not in calculations:
        suggestions.append("🏠 Calculate your home office deduction using calculate_home_office_deduction()")

    # Suggest receipt scanning if not done
    if not receipts.get('scanned'):
        suggestions.append("📄 Scan your receipts using start_tax_return() if you have any")

    # If complete, suggest finalization
    completeness = calculate_overall_completeness(session_data)
    if completeness >= 0.9 and not missing:
        suggestions.append("✅ You're ready! Call finalize_tax_return() to generate your ELSTER XML")

    if not suggestions:
        suggestions.append("✨ Everything looks good! Call finalize_tax_return() when ready.")

    return suggestions
