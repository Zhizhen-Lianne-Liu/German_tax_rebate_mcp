"""
Receipt scanner with OCR for German receipts.
Uses pytesseract (local, no cloud API).
"""

import pytesseract
from PIL import Image
from pathlib import Path
import re
from datetime import datetime
from typing import Optional
import sys
sys.path.append(str(Path(__file__).parent.parent))
from schemas.simple import ScannedReceipt


# German merchant patterns for auto-categorization
MERCHANT_PATTERNS = {
    'commuting': [
        r'BVG',
        r'Deutsche Bahn',
        r'DB Vertrieb',
        r'MVG.*München',
        r'VRR',
        r'Verkehrsverbund',
        r'S-Bahn',
        r'U-Bahn',
    ],
    'home_office': [
        r'Telekom',
        r'Vodafone',
        r'O2',
        r'1&1',
        r'Unitymedia',
        r'Kabel Deutschland',
    ],
    'work_equipment': [
        r'MediaMarkt',
        r'Saturn',
        r'Amazon',
        r'Notebooksbilliger',
        r'Cyberport',
        r'Conrad',
    ],
    'household_services': [
        r'Reinigung',
        r'Clean.*Service',
        r'Hausmeister',
        r'Gartenpflege',
        r'Pflegedienst',
    ],
    'craftsman': [
        r'Handwerk',
        r'Meisterbetrieb',
        r'Elektriker',
        r'Klempner',
        r'Maler',
        r'Schreiner',
        r'Dachdecker',
    ],
    'insurance': [
        r'Allianz',
        r'AOK',
        r'TK.*Krankenkasse',
        r'Versicherung',
        r'HUK',
    ],
    'donations': [
        r'UNICEF',
        r'DRK',
        r'Rotes Kreuz',
        r'Caritas',
        r'Diakonie',
        r'WWF',
    ]
}


def categorize_by_merchant(merchant_name: str) -> str:
    """Auto-categorize based on merchant name patterns"""
    merchant_lower = merchant_name.lower()

    for category, patterns in MERCHANT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, merchant_name, re.IGNORECASE):
                return category

    return 'other'


def extract_date(text: str) -> Optional[datetime]:
    """Extract date from German receipt text"""
    # Common German date formats: DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
    date_patterns = [
        r'(\d{2})\.(\d{2})\.(\d{4})',
        r'(\d{2})/(\d{2})/(\d{4})',
        r'(\d{2})-(\d{2})-(\d{4})',
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                continue

    return None


def extract_amount(text: str) -> Optional[float]:
    """Extract total amount from German receipt text"""
    # Look for lines that start with total keywords (after optional whitespace)
    # This avoids matching compound words like "Material gesamt"
    # Allow optional EUR/€ symbol between keyword and amount
    total_keywords = [
        r'^\s*Gesamt:?\s*(?:EUR|€)?\s*(\d+[.,]\d{2})',  # Total with tax (most important)
        r'^\s*Total:?\s*(?:EUR|€)?\s*(\d+[.,]\d{2})',
        r'^\s*Summe:?\s*(?:EUR|€)?\s*(\d+[.,]\d{2})',   # Subtotal (less important)
        r'^\s*Betrag:?\s*(?:EUR|€)?\s*(\d+[.,]\d{2})',
    ]

    for pattern in total_keywords:
        # Use findall to get ALL matches, then take the last one (final total)
        matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
        if matches:
            # Take the last match (typically the final total)
            amount_str = matches[-1].replace(',', '.')
            try:
                return float(amount_str)
            except ValueError:
                continue

    # Fallback: look for any amount with EUR/€
    fallback_pattern = r'(\d+[.,]\d{2}).*?(?:EUR|€)'
    match = re.search(fallback_pattern, text)
    if match:
        amount_str = match.group(1).replace(',', '.')
        try:
            return float(amount_str)
        except ValueError:
            pass

    return None


def extract_merchant(text: str) -> Optional[str]:
    """Extract merchant name from receipt (usually first few lines)"""
    lines = text.split('\n')

    # Merchant is usually in first 3 lines
    for line in lines[:3]:
        line = line.strip()
        if len(line) > 3 and not line.isdigit():
            # Filter out obvious non-merchant lines
            if any(keyword in line.lower() for keyword in ['datum', 'date', 'uhrzeit', 'time', 'bon', 'receipt']):
                continue
            return line

    return None


def scan_receipt_image(file_path: str) -> ScannedReceipt:
    """
    Scan a receipt image using Tesseract OCR.

    Args:
        file_path: Path to receipt image (JPG, PNG)

    Returns:
        ScannedReceipt with extracted data
    """
    path = Path(file_path)

    if not path.exists():
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"File not found: {file_path}"
        )

    try:
        # Load image
        image = Image.open(path)

        # OCR with German language
        text = pytesseract.image_to_string(image, lang='deu')

        # Extract data
        date = extract_date(text)
        amount = extract_amount(text)
        merchant = extract_merchant(text)

        # Auto-categorize
        category = 'other'
        if merchant:
            category = categorize_by_merchant(merchant)

        # Confidence based on what we found
        confidence = 0.0
        if date:
            confidence += 0.3
        if amount:
            confidence += 0.4
        if merchant:
            confidence += 0.3

        return ScannedReceipt(
            file_path=file_path,
            date=date.date() if date else None,
            merchant=merchant,
            amount=amount,
            category=category,
            confidence=round(confidence, 2),
            ocr_text=text
        )

    except Exception as e:
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"OCR failed: {str(e)}"
        )


def scan_receipt_text(file_path: str) -> ScannedReceipt:
    """
    Scan a plain text receipt file.

    Args:
        file_path: Path to text receipt file (.txt)

    Returns:
        ScannedReceipt with extracted data
    """
    path = Path(file_path)

    if not path.exists():
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"File not found: {file_path}"
        )

    try:
        # Read text file
        text = path.read_text(encoding='utf-8')

        # Extract data using existing functions
        receipt_date = extract_date(text)
        amount = extract_amount(text)
        merchant = extract_merchant(text)

        # Auto-categorize
        category = 'other'
        if merchant:
            category = categorize_by_merchant(merchant)

        # Confidence based on what we found
        confidence = 0.0
        if receipt_date:
            confidence += 0.3
        if amount:
            confidence += 0.4
        if merchant:
            confidence += 0.3

        return ScannedReceipt(
            file_path=file_path,
            date=receipt_date.date() if receipt_date else None,
            merchant=merchant,
            amount=amount,
            category=category,
            confidence=round(confidence, 2),
            ocr_text=text
        )

    except Exception as e:
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"Text file processing failed: {str(e)}"
        )


def scan_receipt_pdf(file_path: str) -> ScannedReceipt:
    """
    Scan a PDF receipt.
    First try text extraction, fallback to OCR if needed.
    """
    import PyPDF2

    path = Path(file_path)

    if not path.exists():
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"File not found: {file_path}"
        )

    try:
        # Try text extraction first
        with open(path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()

        # If no text extracted, it's a scanned PDF - need OCR
        if len(text.strip()) < 20:
            # Convert first page to image and OCR
            # (Simplified: in production, use pdf2image)
            return ScannedReceipt(
                file_path=file_path,
                category='other',
                confidence=0.0,
                ocr_text="PDF requires OCR (not yet implemented for PDFs)"
            )

        # Extract data from text
        date = extract_date(text)
        amount = extract_amount(text)
        merchant = extract_merchant(text)

        category = 'other'
        if merchant:
            category = categorize_by_merchant(merchant)

        confidence = 0.0
        if date:
            confidence += 0.3
        if amount:
            confidence += 0.4
        if merchant:
            confidence += 0.3

        return ScannedReceipt(
            file_path=file_path,
            date=date.date() if date else None,
            merchant=merchant,
            amount=amount,
            category=category,
            confidence=round(confidence, 2),
            ocr_text=text
        )

    except Exception as e:
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"PDF processing failed: {str(e)}"
        )


def scan_receipt(file_path: str) -> ScannedReceipt:
    """
    Scan a receipt (auto-detect format).

    Args:
        file_path: Path to receipt file

    Returns:
        ScannedReceipt with extracted data
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.pdf':
        return scan_receipt_pdf(file_path)
    elif suffix in ['.jpg', '.jpeg', '.png']:
        return scan_receipt_image(file_path)
    elif suffix == '.txt':
        return scan_receipt_text(file_path)
    else:
        return ScannedReceipt(
            file_path=file_path,
            category='other',
            confidence=0.0,
            ocr_text=f"Unsupported format: {suffix}"
        )


def scan_folder(folder_path: str) -> list[ScannedReceipt]:
    """
    Scan all receipts in a folder.

    Args:
        folder_path: Path to folder containing receipts

    Returns:
        List of ScannedReceipt objects
    """
    folder = Path(folder_path)

    if not folder.exists():
        return []

    receipts = []

    # Supported formats
    patterns = ['*.pdf', '*.jpg', '*.jpeg', '*.png', '*.txt', '*.PDF', '*.JPG', '*.JPEG', '*.PNG', '*.TXT']

    for pattern in patterns:
        for file in folder.rglob(pattern):
            receipt = scan_receipt(str(file))
            receipts.append(receipt)

    return receipts
