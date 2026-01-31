#!/usr/bin/env python3
"""
German Tax MCP Server - Simplified MVP

Privacy-first MCP server for German tax rebate assistance.
All processing happens locally on user's machine.

Usage:
    uv run python src/server.py
"""

from fastmcp import FastMCP
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config import TaxRates2025
from lib.rag_engine import get_rag
from lib.receipt_scanner import scan_folder
from lib.elster_xml import generate_elster_xml, generate_summary_text
from schemas.simple import TaxQuestions, ReceiptSummary, DeductionsSummary

# Initialize FastMCP server
mcp = FastMCP("German Tax Assistant")

# Global session state (in-memory for simplicity)
session = {
    'receipts': [],
    'receipt_summary': None,
    'questions': None,
    'deductions': None
}


@mcp.tool()
def start_tax_return(receipts_folder: str, tax_year: int = 2025) -> dict:
    """
    Start tax return process by scanning receipts folder.

    Scans all receipts (PDF, JPG, PNG) in the folder, uses OCR to extract data,
    and auto-categorizes them into tax-relevant categories.

    Args:
        receipts_folder: Path to folder containing receipts
        tax_year: Tax year (default 2025)

    Returns:
        Summary of scanned receipts by category and next steps
    """
    print(f"📁 Scanning receipts in: {receipts_folder}")

    # Scan all receipts
    receipts = scan_folder(receipts_folder)

    if not receipts:
        return {
            "error": f"No receipts found in {receipts_folder}",
            "message": "Make sure the folder contains PDF, JPG, or PNG files",
            "supported_formats": ["pdf", "jpg", "jpeg", "png"]
        }

    # Store in session
    session['receipts'] = receipts

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

    session['receipt_summary'] = summary

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
        "next_step": "I'll need to ask you some questions. Use answer_questions() with your details."
    }


@mcp.tool()
def answer_questions(
    gross_income: float,
    income_tax_paid: float,
    marital_status: str,
    tax_class: str,
    num_children: int,
    work_address: str,
    home_address: str,
    home_office_days: int,
    steuer_id: str,
    postal_code: str
) -> dict:
    """
    Provide answers to key tax questions.

    Args:
        gross_income: Gross annual income in EUR (from Lohnsteuerbescheinigung line 3)
        income_tax_paid: Income tax already paid in EUR (line 4)
        marital_status: 'single', 'married', 'divorced', or 'widowed'
        tax_class: 'I', 'II', 'III', 'IV', 'V', or 'VI'
        num_children: Number of children
        work_address: Work address (for commute calculation)
        home_address: Home address
        home_office_days: Days worked from home in the year
        steuer_id: Your 11-digit tax ID
        postal_code: 5-digit postal code

    Returns:
        Confirmation and next steps
    """
    try:
        questions = TaxQuestions(
            gross_income=gross_income,
            income_tax_paid=income_tax_paid,
            marital_status=marital_status,
            tax_class=tax_class,
            num_children=num_children,
            work_address=work_address,
            home_address=home_address,
            home_office_days=home_office_days,
            steuer_id=steuer_id,
            postal_code=postal_code
        )

        session['questions'] = questions

        return {
            "success": True,
            "message": "✅ Information received and validated",
            "summary": {
                "gross_income": f"€{gross_income:,.2f}",
                "tax_paid": f"€{income_tax_paid:,.2f}",
                "marital_status": marital_status,
                "tax_class": tax_class,
                "children": num_children,
                "home_office_days": home_office_days
            },
            "next_step": "Use calculate_deductions() to compute your tax deductions"
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Please check your inputs and try again"
        }


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
    rag = get_rag()
    result = rag.query(question, collection=category)

    return {
        "question": question,
        "answer": result['answer'],
        "confidence": result['confidence'],
        "sources": [
            {
                "text": source['text'][:200] + "...",
                "source": source['source'],
                "confidence": source['confidence']
            }
            for source in result['sources'][:2]  # Top 2 sources
        ],
        "note": "This information is based on German tax law. For complex situations, consult a Steuerberater."
    }


@mcp.tool()
def calculate_deductions() -> dict:
    """
    Calculate all tax deductions based on receipts and your answers.

    Uses German tax rates for 2025:
    - Commuting: €0.30/km (first 20km), €0.38/km (21km+)
    - Home office: €6/day (max 210 days)
    - Household services: 20% of labor (max €4,000)
    - Craftsman: 20% of labor (max €1,200)

    Returns:
        Detailed breakdown of all deductions and estimated refund
    """
    if not session.get('questions'):
        return {
            "error": "Please call answer_questions() first",
            "next_step": "Provide your tax information using answer_questions()"
        }

    if not session.get('receipt_summary'):
        return {
            "error": "Please call start_tax_return() first to scan receipts",
            "next_step": "Scan your receipts folder using start_tax_return(receipts_folder)"
        }

    questions = session['questions']
    receipt_summary = session['receipt_summary']

    # Calculate commuting deduction
    # Simplified: assume average distance based on addresses (in real app, use geocoding)
    # For now, estimate 15km if both addresses provided
    commute_distance = 15  # km (placeholder)
    office_days = 230 - questions.home_office_days - 30  # Standard days - home office - vacation
    office_days = max(0, office_days)

    if commute_distance <= 20:
        commuting_deduction = commute_distance * office_days * TaxRates2025.COMMUTE_RATE_STANDARD
    else:
        commuting_deduction = (20 * office_days * TaxRates2025.COMMUTE_RATE_STANDARD) + \
                              ((commute_distance - 20) * office_days * TaxRates2025.COMMUTE_RATE_EXTENDED)

    commuting_deduction = min(commuting_deduction, TaxRates2025.COMMUTE_MAX_DEDUCTION)

    # Calculate home office deduction
    home_office_days_capped = min(questions.home_office_days, TaxRates2025.HOME_OFFICE_MAX_DAYS)
    home_office_deduction = home_office_days_capped * TaxRates2025.HOME_OFFICE_DAILY_RATE

    # Work equipment (from receipts)
    work_equipment_deduction = receipt_summary.work_equipment

    # Household services (20% of labor, max €4,000 deduction)
    household_service_deduction = min(
        receipt_summary.household_services * TaxRates2025.HOUSEHOLD_SERVICE_RATE,
        TaxRates2025.HOUSEHOLD_SERVICE_MAX
    )

    # Craftsman (20% of labor, max €1,200 deduction)
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

    # Estimate refund (simplified calculation)
    # Real calculation would use progressive tax brackets
    taxable_income = questions.gross_income - total_deductions
    estimated_tax = taxable_income * 0.25  # Rough estimate (actual is progressive)
    estimated_refund = questions.income_tax_paid - estimated_tax

    # Add household/craftsman reductions (direct tax reductions, not deductions from income)
    estimated_refund += household_service_deduction + craftsman_deduction

    # Store in session
    deductions = DeductionsSummary(
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

    session['deductions'] = deductions

    return {
        "success": True,
        "deductions": {
            "commuting": f"€{deductions.commuting_deduction:,.2f}",
            "home_office": f"€{deductions.home_office_deduction:,.2f}",
            "work_equipment": f"€{deductions.work_equipment_deduction:,.2f}",
            "household_services": f"€{deductions.household_service_deduction:,.2f} (20% of €{receipt_summary.household_services:,.2f} labor)",
            "craftsman": f"€{deductions.craftsman_deduction:,.2f} (20% of €{receipt_summary.craftsman:,.2f} labor)",
            "insurance": f"€{deductions.insurance_deduction:,.2f}",
            "donations": f"€{deductions.donations_deduction:,.2f}"
        },
        "total_deductions": f"€{deductions.total_deductions:,.2f}",
        "estimated_refund": f"€{deductions.estimated_refund:,.2f}",
        "confidence": "medium" if estimated_refund > 0 else "low",
        "note": "This is an estimate. Final calculation by Finanzamt may differ.",
        "next_step": "Use generate_elster_xml() to create your ELSTER import file"
    }


@mcp.tool()
def generate_elster_xml_file(tax_year: int = 2025) -> dict:
    """
    Generate ELSTER XML file for import to Mein ELSTER.

    Creates an XML file that can be imported into the official German tax system.
    File is saved to data/exports/ folder.

    Args:
        tax_year: Tax year (default 2025)

    Returns:
        Path to XML file and submission instructions
    """
    if not session.get('questions') or not session.get('deductions'):
        return {
            "error": "Please complete previous steps first",
            "required_steps": [
                "1. start_tax_return(receipts_folder)",
                "2. answer_questions(...)",
                "3. calculate_deductions()"
            ]
        }

    questions = session['questions']
    deductions = session['deductions']

    # Generate XML
    xml_path = generate_elster_xml(questions, deductions, tax_year)

    # Generate human-readable summary
    summary = generate_summary_text(questions, deductions, tax_year)

    return {
        "success": True,
        "xml_file": xml_path,
        "summary": summary,
        "next_steps": [
            "1. Go to https://www.elster.de/eportal/login",
            "2. Log in to Mein ELSTER",
            "3. Click 'Datenimport' (Data Import)",
            f"4. Upload: {xml_path}",
            "5. Review all pre-filled fields carefully",
            "6. Submit your tax return",
            "",
            "⚠️  Keep all receipts for 1-2 years after receiving Steuerbescheid"
        ],
        "estimated_refund": f"€{deductions.estimated_refund:,.2f}"
    }


# Basic calculation helpers (also available as standalone tools)
@mcp.tool()
def calculate_commuting_deduction(distance_km: float, workdays: int = None) -> dict:
    """Calculate commuting deduction (Entfernungspauschale) - standalone helper"""
    if workdays is None:
        workdays = 200  # Default

    if distance_km <= 20:
        amount = distance_km * workdays * 0.30
    else:
        amount = (20 * workdays * 0.30) + ((distance_km - 20) * workdays * 0.38)

    amount = min(amount, 4500)

    return {
        "amount": round(amount, 2),
        "calculation": f"{distance_km}km × {workdays} workdays",
        "rate": "€0.30/km (first 20km), €0.38/km (beyond 20km)",
        "max": "€4,500/year"
    }


@mcp.tool()
def calculate_home_office_deduction(days: int) -> dict:
    """Calculate home office deduction (Homeoffice-Pauschale) - standalone helper"""
    days_used = min(days, 210)
    amount = days_used * 6

    return {
        "amount": round(amount, 2),
        "days_used": days_used,
        "daily_rate": "€6",
        "max_days": 210,
        "max_deduction": "€1,260"
    }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
