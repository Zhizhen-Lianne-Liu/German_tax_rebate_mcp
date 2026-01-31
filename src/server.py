#!/usr/bin/env python3
"""
German Tax MCP Server - V2 Incremental Architecture

Privacy-first MCP server for German tax rebate assistance.
Supports incremental, conversational data collection.

All processing happens locally on user's machine.

Usage:
    uv run python src/server.py
"""

from fastmcp import FastMCP
from pathlib import Path
import sys
from datetime import datetime

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config import TaxRates2025
from schemas.simple import TaxQuestions, ReceiptSummary, DeductionsSummary

# Lazy imports - only load when needed
_rag_engine = None

def get_rag_lazy():
    """Lazy load RAG engine only when first used"""
    global _rag_engine
    if _rag_engine is None:
        from lib.rag_engine import get_rag
        _rag_engine = get_rag()
    return _rag_engine

# Initialize FastMCP server
mcp = FastMCP("German Tax Assistant - V2 Incremental")

# Persistent session state (survives server restarts)
def get_session():
    """Get persistent session manager"""
    from lib.session_manager import get_session as get_session_manager
    return get_session_manager()


# ============================================================================
# TOOL 1: update_personal_info() - Flexible Incremental Data Entry
# ============================================================================

@mcp.tool()
def update_personal_info(
    # Personal identification
    first_name: str = None,
    last_name: str = None,
    birthdate: str = None,  # Format: YYYY-MM-DD
    email: str = None,
    phone: str = None,
    steuer_id: str = None,
    postal_code: str = None,
    home_address: str = None,
    iban: str = None,
    tax_advisor_prepared: bool = None,
    # Income
    gross_income: float = None,
    income_tax_paid: float = None,
    employer_name: str = None,
    # Tax status
    marital_status: str = None,
    tax_class: str = None,
    num_children: int = None,
    religion: str = None,
    # Work
    work_address: str = None,
    employment_start_date: str = None,  # Format: YYYY-MM-DD
    employment_end_date: str = None  # Format: YYYY-MM-DD
) -> dict:
    """
    Update your personal tax information incrementally.

    You can provide as many or as few fields as you want in any order.
    This tool merges your information into the session, allowing you to
    build up your tax profile piece by piece.

    Call this multiple times to add more details as needed.

    Args:
        Personal identification:
            first_name: Your first name
            last_name: Your last name
            birthdate: Date of birth (YYYY-MM-DD)
            email: Email address
            phone: Phone number (optional)
            steuer_id: 11-digit tax ID
            postal_code: 5-digit postal code
            home_address: Your home address
            iban: German IBAN (22 characters starting with DE)
            tax_advisor_prepared: Whether prepared with tax advisor

        Income:
            gross_income: Gross annual income in EUR
            income_tax_paid: Income tax already paid in EUR
            employer_name: Name of your employer

        Tax status:
            marital_status: single/married/divorced/widowed
            tax_class: I/II/III/IV/V/VI
            num_children: Number of children
            religion: rk/ev/none/other (optional)

        Work:
            work_address: Work address
            employment_start_date: If started employment this tax year (YYYY-MM-DD)
            employment_end_date: If ended employment this tax year (YYYY-MM-DD)

    Returns:
        Success status, updated fields, and overall completeness percentage

    Examples:
        # Just name:
        update_personal_info(first_name="Anna", last_name="Schmidt")

        # Just income:
        update_personal_info(gross_income=45000, income_tax_paid=9000)

        # Multiple categories:
        update_personal_info(
            first_name="Anna",
            email="anna@example.de",
            gross_income=45000
        )
    """
    from lib.helpers import calculate_overall_completeness

    sess = get_session()
    updated_fields = []

    # Prepare updates for each category
    personal_updates = {}
    income_updates = {}
    tax_status_updates = {}
    work_updates = {}

    # Map fields to categories
    if first_name: personal_updates['first_name'] = first_name; updated_fields.append('first_name')
    if last_name: personal_updates['last_name'] = last_name; updated_fields.append('last_name')
    if birthdate: personal_updates['birthdate'] = birthdate; updated_fields.append('birthdate')
    if email: personal_updates['email'] = email; updated_fields.append('email')
    if phone: personal_updates['phone'] = phone; updated_fields.append('phone')
    if steuer_id: personal_updates['steuer_id'] = steuer_id; updated_fields.append('steuer_id')
    if postal_code: personal_updates['postal_code'] = postal_code; updated_fields.append('postal_code')
    if home_address: personal_updates['home_address'] = home_address; updated_fields.append('home_address')
    if iban: personal_updates['iban'] = iban; updated_fields.append('iban')
    if tax_advisor_prepared is not None:
        personal_updates['tax_advisor_prepared'] = tax_advisor_prepared
        updated_fields.append('tax_advisor_prepared')

    if gross_income: income_updates['gross_income'] = gross_income; updated_fields.append('gross_income')
    if income_tax_paid: income_updates['income_tax_paid'] = income_tax_paid; updated_fields.append('income_tax_paid')
    if employer_name: income_updates['employer_name'] = employer_name; updated_fields.append('employer_name')

    if marital_status: tax_status_updates['marital_status'] = marital_status; updated_fields.append('marital_status')
    if tax_class: tax_status_updates['tax_class'] = tax_class; updated_fields.append('tax_class')
    if num_children is not None: tax_status_updates['num_children'] = num_children; updated_fields.append('num_children')
    if religion: tax_status_updates['religion'] = religion; updated_fields.append('religion')

    if work_address: work_updates['work_address'] = work_address; updated_fields.append('work_address')
    if employment_start_date: work_updates['employment_start_date'] = employment_start_date; updated_fields.append('employment_start_date')
    if employment_end_date: work_updates['employment_end_date'] = employment_end_date; updated_fields.append('employment_end_date')

    # Merge updates into session
    if personal_updates:
        sess.merge('personal_info', personal_updates)
    if income_updates:
        sess.merge('income_info', income_updates)
    if tax_status_updates:
        sess.merge('tax_status', tax_status_updates)
    if work_updates:
        sess.merge('work_info', work_updates)

    # Calculate completeness
    session_data = sess.get_all()
    completeness = calculate_overall_completeness(session_data)

    return {
        "success": True,
        "updated_fields": updated_fields,
        "overall_completeness": f"{completeness:.0%}",
        "message": f"✅ Information updated. You're {completeness:.0%} complete.",
        "next_step": "Continue adding information or check status with get_tax_return_status()"
    }


# ============================================================================
# TOOL 2: get_tax_return_status() - Progress Tracker
# ============================================================================

@mcp.tool()
def get_tax_return_status() -> dict:
    """
    Check the current status of your tax return preparation.

    Shows:
    - Overall progress percentage
    - What information you've provided so far
    - What calculations have been done
    - What's still needed for completion
    - Suggested next steps

    Returns:
        Detailed status report with completeness metrics

    Example:
        get_tax_return_status()
        → Shows you're 75% complete with suggestions for next steps
    """
    from lib.helpers import (
        calculate_overall_completeness,
        calculate_category_completeness,
        suggest_next_steps,
        get_missing_required_fields
    )

    sess = get_session()
    session_data = sess.get_all()

    personal = session_data.get('personal_info', {})
    income = session_data.get('income_info', {})
    tax_status = session_data.get('tax_status', {})
    work = session_data.get('work_info', {})
    calculations = session_data.get('calculations', {})
    receipts = session_data.get('receipts', {})

    # Required fields
    personal_required = ['first_name', 'last_name', 'birthdate', 'steuer_id', 'postal_code', 'home_address', 'iban', 'email']
    income_required = ['gross_income', 'income_tax_paid']
    tax_required = ['marital_status', 'tax_class']

    overall_completeness = calculate_overall_completeness(session_data)
    personal_completeness = calculate_category_completeness(personal, personal_required)
    income_completeness = calculate_category_completeness(income, income_required)
    tax_completeness = calculate_category_completeness(tax_status, tax_required)

    return {
        "overall_progress": f"{overall_completeness:.0%}",
        "sections": {
            "personal_info": {
                "completeness": f"{personal_completeness:.0%}",
                "fields_provided": [k for k, v in personal.items() if v],
                "fields_missing": [k for k in personal_required if not personal.get(k)]
            },
            "income_info": {
                "completeness": f"{income_completeness:.0%}",
                "fields_provided": [k for k, v in income.items() if v],
                "fields_missing": [k for k in income_required if not income.get(k)]
            },
            "tax_status": {
                "completeness": f"{tax_completeness:.0%}",
                "fields_provided": [k for k, v in tax_status.items() if v],
                "fields_missing": [k for k in tax_required if not tax_status.get(k)]
            },
            "calculations": {
                "completed": list(calculations.keys()),
                "results": {k: v.get('result', {}).get('amount') for k, v in calculations.items()}
            },
            "receipts": {
                "scanned": receipts.get('scanned', False),
                "total_amount": receipts.get('summary', {}).get('total_amount', 0) if receipts.get('summary') else 0
            }
        },
        "ready_to_finalize": overall_completeness >= 0.9 and len(get_missing_required_fields(session_data)) == 0,
        "next_steps": suggest_next_steps(session_data)
    }


# ============================================================================
# TOOL 3: finalize_tax_return() - Smart Orchestrator
# ============================================================================

@mcp.tool()
def finalize_tax_return(tax_year: int = 2025) -> dict:
    """
    Finalize your tax return by analyzing all collected data and generating ELSTER XML.

    This is the orchestrator tool that:
    1. Reviews all data you've provided (calculations, personal info, receipts)
    2. Identifies what's still missing for ELSTER submission
    3. If data is complete: generates XML and summary
    4. If data is incomplete: returns a list of missing required fields

    Call this when you're ready to complete your tax return.

    Args:
        tax_year: Tax year (default 2025)

    Returns:
        If complete: XML file path, summary, and refund estimate
        If incomplete: List of missing required fields with next steps

    Example:
        finalize_tax_return()
        → Either generates XML or tells you what's still needed
    """
    from lib.helpers import (
        get_missing_required_fields,
        build_tax_questions_from_session,
        complete_deductions_calculation
    )

    sess = get_session()
    session_data = sess.get_all()

    # Check for missing required fields
    missing = get_missing_required_fields(session_data)

    if missing:
        # Incomplete - return what's needed
        calculations = session_data.get('calculations', {})
        receipts = session_data.get('receipts', {})

        return {
            "status": "incomplete",
            "message": "Almost there! I need a few more details to complete your tax return:",
            "missing_required_fields": missing,
            "what_you_have": {
                "calculations_completed": list(calculations.keys()),
                "receipts_scanned": receipts.get('scanned', False),
                "total_receipt_amount": receipts.get('summary', {}).get('total_amount', 0) if receipts.get('summary') else 0
            },
            "next_step": "Use update_personal_info() to provide the missing information, then call finalize_tax_return() again."
        }

    # All required fields present - proceed with finalization
    try:
        # Build TaxQuestions from session
        questions = build_tax_questions_from_session(session_data)

        # Complete deductions calculation (uses saved calculations where available)
        deductions = complete_deductions_calculation(session_data, questions)

        # Save deductions to session
        sess.set('deductions', deductions)

        # Generate XML
        from lib.elster_xml import generate_elster_xml, generate_summary_text
        xml_path = generate_elster_xml(questions, deductions, tax_year)
        summary = generate_summary_text(questions, deductions, tax_year)

        # Mark as complete
        sess.set('xml_generated', True)

        calculations = session_data.get('calculations', {})

        return {
            "status": "complete",
            "success": True,
            "xml_file": xml_path,
            "summary": summary,
            "calculations_used": list(calculations.keys()),
            "estimated_refund": f"€{deductions.estimated_refund:,.2f}",
            "next_steps": [
                "1. Review the summary above",
                "2. Go to https://www.elster.de/eportal/login",
                "3. Log in to Mein ELSTER",
                "4. Click 'Datenimport' (Data Import)",
                f"5. Upload: {xml_path}",
                "6. Review all pre-filled fields carefully",
                "7. Submit your tax return",
                "",
                "⚠️  Keep all receipts for 1-2 years after receiving Steuerbescheid"
            ]
        }

    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "message": "An error occurred while finalizing your tax return. Please check your data and try again."
        }


# ============================================================================
# TOOL 4: calculate_commuting_deduction() - MODIFIED to save to session
# ============================================================================

@mcp.tool()
def calculate_commuting_deduction(distance_km: float, workdays: int = 200) -> dict:
    """
    Calculate commuting deduction (Entfernungspauschale).

    This tool automatically saves your calculation to the session,
    so when you're ready to finalize your tax return, this data
    will be included automatically.

    Uses 2025 rates:
    - First 20km: €0.30/km
    - Beyond 20km: €0.38/km
    - Maximum: €4,500/year

    Args:
        distance_km: One-way commute distance in kilometers
        workdays: Number of workdays (default: 200)

    Returns:
        Calculated deduction amount (automatically saved to session)

    Example:
        calculate_commuting_deduction(25, 180)
        → €1,620 (saved to your session)
    """
    # Calculate
    if distance_km <= 20:
        amount = distance_km * workdays * TaxRates2025.COMMUTE_RATE_STANDARD
    else:
        amount = (20 * workdays * TaxRates2025.COMMUTE_RATE_STANDARD) + \
                 ((distance_km - 20) * workdays * TaxRates2025.COMMUTE_RATE_EXTENDED)

    amount = min(amount, TaxRates2025.COMMUTE_MAX_DEDUCTION)

    # Save to session
    sess = get_session()
    sess.set_nested('calculations.commuting', {
        'input': {'distance_km': distance_km, 'days': workdays},
        'result': {
            'amount': round(amount, 2),
            'calculation': f'{distance_km}km × {workdays} workdays'
        },
        'calculated_at': datetime.now().isoformat()
    })

    # Also update work_info
    sess.merge('work_info', {
        'commute_distance_km': distance_km,
        'office_days': workdays
    })

    return {
        "amount": round(amount, 2),
        "calculation": f"{distance_km}km × {workdays} workdays",
        "rate": "€0.30/km (first 20km), €0.38/km (beyond 20km)",
        "max": "€4,500/year",
        "saved_to_session": True,
        "note": "✅ This calculation has been saved. When you finalize your tax return, it will be included automatically."
    }


# ============================================================================
# TOOL 5: calculate_home_office_deduction() - MODIFIED to save to session
# ============================================================================

@mcp.tool()
def calculate_home_office_deduction(days: int) -> dict:
    """
    Calculate home office deduction (Homeoffice-Pauschale).

    This tool automatically saves your calculation to the session,
    so when you're ready to finalize your tax return, this data
    will be included automatically.

    Uses 2025 rates:
    - €6 per day
    - Maximum: 210 days (€1,260)

    Args:
        days: Number of home office days

    Returns:
        Calculated deduction amount (automatically saved to session)

    Example:
        calculate_home_office_deduction(150)
        → €900 (saved to your session)
    """
    # Calculate
    days_used = min(days, TaxRates2025.HOME_OFFICE_MAX_DAYS)
    amount = days_used * TaxRates2025.HOME_OFFICE_DAILY_RATE

    # Save to session
    sess = get_session()
    sess.set_nested('calculations.home_office', {
        'input': {'days': days},
        'result': {
            'amount': round(amount, 2),
            'days_used': days_used
        },
        'calculated_at': datetime.now().isoformat()
    })

    # Also update work_info
    sess.merge('work_info', {
        'home_office_days': days
    })

    return {
        "amount": round(amount, 2),
        "days_used": days_used,
        "daily_rate": "€6",
        "max_days": 210,
        "max_deduction": "€1,260",
        "saved_to_session": True,
        "note": "✅ This calculation has been saved. When you finalize your tax return, it will be included automatically."
    }


# ============================================================================
# TOOL 6: start_tax_return() - Receipt Scanning (updated for V2 session)
# ============================================================================

@mcp.tool()
def start_tax_return(receipts_folder: str, tax_year: int = 2025) -> dict:
    """
    Start tax return process by scanning receipts folder.

    Scans all receipts (PDF, JPG, PNG, TXT) in the folder, uses OCR to extract data,
    and auto-categorizes them into tax-relevant categories.

    Results are automatically saved to the session.

    Args:
        receipts_folder: Path to folder containing receipts
        tax_year: Tax year (default 2025)

    Returns:
        Summary of scanned receipts by category
    """
    print(f"📁 Scanning receipts in: {receipts_folder}")

    # Lazy import
    from lib.receipt_scanner import scan_folder

    # Scan all receipts
    receipts = scan_folder(receipts_folder)

    if not receipts:
        return {
            "error": f"No receipts found in {receipts_folder}",
            "message": "Make sure the folder contains supported file formats",
            "supported_formats": ["pdf", "jpg", "jpeg", "png", "txt"]
        }

    # Summarize by category
    summary = ReceiptSummary()

    for receipt in receipts:
        if receipt.amount:
            if receipt.category == 'commuting':
                summary.commuting += receipt.amount
            elif receipt.category == 'home_office':
                summary.home_office += receipt.amount
            elif receipt.category == 'work_equipment':
                summary.work_equipment += receipt.amount
            elif receipt.category == 'household_services':
                summary.household_services += receipt.amount
            elif receipt.category == 'craftsman':
                summary.craftsman += receipt.amount
            elif receipt.category == 'insurance':
                summary.insurance += receipt.amount
            elif receipt.category == 'donations':
                summary.donations += receipt.amount
            else:
                summary.other += receipt.amount

            summary.total_amount += receipt.amount

    summary.total_receipts = len(receipts)

    # Store in V2 session structure
    sess = get_session()
    sess.set_nested('receipts.scanned', True)
    sess.set_nested('receipts.summary', summary.model_dump())

    return {
        "success": True,
        "tax_year": tax_year,
        "total_receipts": summary.total_receipts,
        "total_amount": f"€{summary.total_amount:,.2f}",
        "by_category": {
            "commuting": f"€{summary.commuting:,.2f}",
            "home_office": f"€{summary.home_office:,.2f}",
            "work_equipment": f"€{summary.work_equipment:,.2f}",
            "household_services": f"€{summary.household_services:,.2f}",
            "craftsman": f"€{summary.craftsman:,.2f}",
            "insurance": f"€{summary.insurance:,.2f}",
            "donations": f"€{summary.donations:,.2f}",
            "other": f"€{summary.other:,.2f}"
        },
        "saved_to_session": True,
        "next_step": "Continue with update_personal_info() or calculations, then finalize_tax_return() when ready"
    }


# ============================================================================
# TOOL 7: query_tax_rules() - RAG Tax Law Q&A (unchanged)
# ============================================================================

@mcp.tool()
def query_tax_rules(question: str, category: str = "deductions") -> dict:
    """
    Query German tax law using RAG (Retrieval-Augmented Generation).

    Ask questions about tax rules, deductions, requirements, etc.
    The system searches a local database of German tax law and returns
    relevant information with source citations.

    Args:
        question: Your tax question (e.g., "Can I deduct internet costs for home office?")
        category: 'deductions', 'forms', or 'tax_law' (default: 'deductions')

    Returns:
        Answer with sources and confidence score
    """
    try:
        rag = get_rag_lazy()
        result = rag.query(question, collection=category)

        # Defensive checks for None values
        answer = result.get('answer', 'No answer found') if result else 'No answer found'
        confidence = result.get('confidence', 0.0) if result else 0.0
        sources = result.get('sources', []) if result else []

        # Format sources safely
        formatted_sources = []
        if sources:
            for source in sources[:2]:  # Top 2 sources
                if source and isinstance(source, dict):
                    text = source.get('text', '')
                    formatted_sources.append({
                        "text": (text[:200] + "...") if text and len(text) > 200 else (text or ""),
                        "source": source.get('source', 'Unknown'),
                        "confidence": source.get('confidence', 0.0)
                    })

        return {
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "sources": formatted_sources,
            "note": "This information is based on German tax law. For complex situations, consult a Steuerberater."
        }
    except Exception as e:
        import traceback
        return {
            "question": question,
            "error": "RAG query failed",
            "details": str(e),
            "traceback": traceback.format_exc()
        }


# ============================================================================
# TOOL 8: clear_session() - Start Fresh (updated message)
# ============================================================================

@mcp.tool()
def clear_session() -> dict:
    """
    Clear all session data and start fresh.

    Use this if you want to start a new tax return or if you encounter issues.

    Returns:
        Confirmation message
    """
    sess = get_session()
    sess.clear()

    return {
        "success": True,
        "message": "✅ Session cleared. You can now start a new tax return.",
        "next_step": "Start by providing some information with update_personal_info() or calculate deductions"
    }


# ============================================================================
# Run the server
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
