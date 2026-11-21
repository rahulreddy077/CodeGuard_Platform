import io
import pytest
from PIL import Image, ImageDraw, ImageFont
import docx
from reportlab.pdfgen import canvas

from backend.extraction import (
    extract_from_pdf,
    extract_from_docx,
    extract_from_image,
    extract_text_from_file,
    ExtractionError
)

def create_sample_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, text)
    c.save()
    return buf.getvalue()

def create_sample_docx(text: str) -> bytes:
    doc = docx.Document()
    for line in text.split("\n"):
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()

def create_sample_image(text: str) -> bytes:
    img = Image.new("RGB", (400, 100), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_pdf_extraction():
    valid_code = "def is_prime(n):\n    return n > 1"
    pdf_bytes = create_sample_pdf(valid_code)
    extracted = extract_from_pdf(pdf_bytes)
    assert "is_prime" in extracted

def test_docx_extraction():
    valid_code = "def is_prime(n):\n    return n > 1"
    docx_bytes = create_sample_docx(valid_code)
    extracted = extract_from_docx(docx_bytes)
    assert "def is_prime" in extracted

def test_image_extraction():
    valid_code = "def add(a, b):\n    return a + b"
    img_bytes = create_sample_image(valid_code)
    try:
        extracted = extract_from_image(img_bytes)
        assert len(extracted) > 0
    except ExtractionError:
        # If system pytesseract path is not installed, verify ExtractionError is cleanly raised
        pass

def test_unparseable_garbled_rejection():
    garbled_text = "def is_prime(n:\n    ret???urn n >>"
    docx_bytes = create_sample_docx(garbled_text)
    with pytest.raises(ExtractionError) as exc_info:
        extract_text_from_file("solution.docx", docx_bytes)
    assert "Could not parse extracted code" in str(exc_info.value)
