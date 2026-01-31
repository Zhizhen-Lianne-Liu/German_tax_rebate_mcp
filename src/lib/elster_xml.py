"""
ELSTER XML generator for German tax returns.
Creates importable XML for Mein ELSTER system.
"""

from lxml import etree
from datetime import datetime
from typing import Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from schemas.simple import TaxQuestions, DeductionsSummary
from config import EXPORTS_DIR


def generate_elster_xml(
    questions: TaxQuestions,
    deductions: DeductionsSummary,
    tax_year: int = 2025
) -> str:
    """
    Generate ELSTER-compatible XML for import to Mein ELSTER.

    Args:
        questions: User's answers to tax questions
        deductions: Calculated deductions
        tax_year: Tax year (default 2025)

    Returns:
        Path to generated XML file
    """

    # Create root element
    root = etree.Element("Elster")

    # Transfer header
    transfer_header = etree.SubElement(root, "TransferHeader")
    etree.SubElement(transfer_header, "Version").text = "11"
    etree.SubElement(transfer_header, "DataType").text = "LStA"  # Lohnsteuer-Anmeldung
    etree.SubElement(transfer_header, "Testcase").text = "false"

    # Data part
    data_part = etree.SubElement(root, "DatenTeil")

    # Nutzdatenblock (actual tax data)
    payload = etree.SubElement(data_part, "Nutzdatenblock")

    # Header info
    header = etree.SubElement(payload, "NutzdatenHeader")
    etree.SubElement(header, "Version").text = "1"
    etree.SubElement(header, "Steuernummer").text = questions.steuer_id

    # Main form (Hauptvordruck)
    main_form = etree.SubElement(payload, "Hauptvordruck")

    # Year and basic info
    etree.SubElement(main_form, "Jahr").text = str(tax_year)

    # Personal identification (NEW - Taxfix parity)
    personal = etree.SubElement(main_form, "Persoenliche_Angaben")
    etree.SubElement(personal, "Vorname").text = questions.first_name
    etree.SubElement(personal, "Nachname").text = questions.last_name
    etree.SubElement(personal, "Geburtsdatum").text = questions.birthdate.strftime('%d.%m.%Y')
    etree.SubElement(personal, "Steueridentifikationsnummer").text = questions.steuer_id

    # Address
    address = etree.SubElement(personal, "Adresse")
    etree.SubElement(address, "Strasse").text = questions.home_address
    etree.SubElement(address, "PLZ").text = questions.postal_code

    # Contact (NEW)
    etree.SubElement(personal, "Email").text = questions.email
    if questions.phone:
        etree.SubElement(personal, "Telefon").text = questions.phone

    # Tax class
    etree.SubElement(main_form, "Steuerklasse").text = questions.tax_class

    # Marital status
    if questions.marital_status == 'single':
        etree.SubElement(main_form, "Familienstand").text = "1"
    elif questions.marital_status == 'married':
        etree.SubElement(main_form, "Familienstand").text = "2"
    elif questions.marital_status == 'divorced':
        etree.SubElement(main_form, "Familienstand").text = "3"
    elif questions.marital_status == 'widowed':
        etree.SubElement(main_form, "Familienstand").text = "4"

    # Religion (NEW - Lines 11, 23)
    if questions.religion:
        religion_code = {
            'rk': 'RK',  # Roman Catholic
            'ev': 'EV',  # Evangelical
            'none': 'OK',  # Ohne Konfession
            'other': 'SO'  # Sonstige
        }.get(questions.religion, 'OK')
        etree.SubElement(main_form, "Religionsgemeinschaft").text = religion_code

    # Bank details (NEW - for refunds)
    bank = etree.SubElement(main_form, "Bankverbindung")
    etree.SubElement(bank, "IBAN").text = questions.iban
    etree.SubElement(bank, "Kontoinhaber").text = f"{questions.first_name} {questions.last_name}"

    # Tax advisor (NEW - Line 39)
    if questions.tax_advisor_prepared:
        etree.SubElement(main_form, "Steuerberater").text = "true"

    # Income (from Lohnsteuerbescheinigung)
    etree.SubElement(main_form, "Bruttolohn").text = f"{questions.gross_income:.2f}"
    etree.SubElement(main_form, "Lohnsteuer").text = f"{questions.income_tax_paid:.2f}"

    # Household services (§35a EStG)
    if deductions.household_service_deduction > 0:
        household = etree.SubElement(main_form, "HaushaltsnaheDienstleistungen")
        etree.SubElement(household, "Aufwendungen").text = f"{deductions.household_service_deduction * 5:.2f}"  # Labor costs
        etree.SubElement(household, "Steuerermäßigung").text = f"{deductions.household_service_deduction:.2f}"

    # Craftsman services (§35a EStG)
    if deductions.craftsman_deduction > 0:
        craftsman = etree.SubElement(main_form, "Handwerkerleistungen")
        etree.SubElement(craftsman, "Aufwendungen").text = f"{deductions.craftsman_deduction * 5:.2f}"  # Labor costs
        etree.SubElement(craftsman, "Steuerermäßigung").text = f"{deductions.craftsman_deduction:.2f}"

    # Anlage N (Employment income)
    anlage_n = etree.SubElement(payload, "Anlage_N")

    # Employer information (NEW - if provided)
    if questions.employer_name:
        etree.SubElement(anlage_n, "Arbeitgeber").text = questions.employer_name
    if questions.employment_start_date:
        etree.SubElement(anlage_n, "Beschaeftigungsbeginn").text = questions.employment_start_date.strftime('%d.%m.%Y')
    if questions.employment_end_date:
        etree.SubElement(anlage_n, "Beschaeftigungsende").text = questions.employment_end_date.strftime('%d.%m.%Y')

    # Commuting deduction (Entfernungspauschale)
    if deductions.commuting_deduction > 0:
        # Calculate distance and days from deduction amount
        # This is approximate - ideally store these separately
        etree.SubElement(anlage_n, "Entfernungspauschale").text = f"{deductions.commuting_deduction:.2f}"

    # Home office deduction (Homeoffice-Pauschale)
    if deductions.home_office_deduction > 0:
        home_office_days = int(deductions.home_office_deduction / 6)  # €6 per day
        etree.SubElement(anlage_n, "HomeOfficeTage").text = str(home_office_days)
        etree.SubElement(anlage_n, "HomeOfficePauschale").text = f"{deductions.home_office_deduction:.2f}"

    # Work equipment
    if deductions.work_equipment_deduction > 0:
        etree.SubElement(anlage_n, "Arbeitsmittel").text = f"{deductions.work_equipment_deduction:.2f}"

    # Anlage Kind (if children)
    if questions.num_children > 0:
        for i in range(questions.num_children):
            anlage_kind = etree.SubElement(payload, "Anlage_Kind")
            etree.SubElement(anlage_kind, "Laufenummer").text = str(i + 1)
            # Add child details here if available

    # Anlage Vorsorgeaufwand (Insurance)
    if deductions.insurance_deduction > 0:
        anlage_vorsorge = etree.SubElement(payload, "Anlage_Vorsorgeaufwand")
        etree.SubElement(anlage_vorsorge, "Krankenversicherung").text = f"{deductions.insurance_deduction:.2f}"

    # Generate XML string
    xml_string = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8'
    ).decode('utf-8')

    # Save to file
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{tax_year}_elster.xml"
    output_path = EXPORTS_DIR / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)

    return str(output_path)


def generate_summary_text(
    questions: TaxQuestions,
    deductions: DeductionsSummary,
    tax_year: int = 2025
) -> str:
    """
    Generate human-readable summary of tax return.

    Args:
        questions: User's answers
        deductions: Calculated deductions
        tax_year: Tax year

    Returns:
        Formatted text summary
    """

    summary = f"""
╔══════════════════════════════════════════════════════════════╗
║          German Tax Return Summary - {tax_year}              ║
╚══════════════════════════════════════════════════════════════╝

👤 PERSONAL INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Name:             {questions.first_name} {questions.last_name}
  Birthdate:        {questions.birthdate.strftime('%d.%m.%Y')}
  Tax ID:           {questions.steuer_id}
  Email:            {questions.email}
  Address:          {questions.home_address}
  Postal Code:      {questions.postal_code}
  IBAN:             {questions.iban[:8]}...{questions.iban[-4:]}

🏢 TAX STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Marital Status:   {questions.marital_status.capitalize()}
  Tax Class:        {questions.tax_class}
  Children:         {questions.num_children}
  Employer:         {questions.employer_name or 'Not specified'}

💰 INCOME
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Gross Income:     €{questions.gross_income:,.2f}
  Tax Paid:         €{questions.income_tax_paid:,.2f}

📝 DEDUCTIONS (Werbungskosten & Sonderausgaben)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Commuting:        €{deductions.commuting_deduction:,.2f}
  Home Office:      €{deductions.home_office_deduction:,.2f}
  Work Equipment:   €{deductions.work_equipment_deduction:,.2f}
  Insurance:        €{deductions.insurance_deduction:,.2f}
  Donations:        €{deductions.donations_deduction:,.2f}
  ─────────────────────────────────────────
  Subtotal:         €{deductions.total_deductions:,.2f}

🏠 TAX REDUCTIONS (§35a EStG)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Household Services: €{deductions.household_service_deduction:,.2f}
  Craftsman Services: €{deductions.craftsman_deduction:,.2f}

💵 ESTIMATED REFUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Estimated Refund: €{deductions.estimated_refund:,.2f}

📄 REQUIRED FORMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ ESt 1 V (Main form)
  ✓ Anlage N (Employment income)
  ✓ Anlage Vorsorgeaufwand (Insurance)
"""

    if questions.num_children > 0:
        summary += "  ✓ Anlage Kind (Children)\n"

    if deductions.household_service_deduction > 0 or deductions.craftsman_deduction > 0:
        summary += "  ✓ § 35a (Household/Craftsman services)\n"

    summary += f"""
📤 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Review this summary carefully
  2. Go to: https://www.elster.de/eportal/login
  3. Click "Datenimport" in Mein ELSTER
  4. Upload: {tax_year}_elster.xml
  5. Review all pre-filled fields
  6. Submit your tax return

⚠️  IMPORTANT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  This is an estimate. The Finanzamt makes the final calculation.
  Keep all receipts for {questions.num_children > 0 and '1 year' or '2 years'} after receiving your Steuerbescheid.
  For complex situations, consult a Steuerberater.

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    return summary
