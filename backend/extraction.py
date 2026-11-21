import io
import ast
import logging
from PIL import Image
import pdfplumber

# Optional dependency: python-docx
try:
    import docx as _docx
    _DOCX_AVAILABLE = True
except ImportError:  # pragma: no cover
    _DOCX_AVAILABLE = False

# Optional dependency: pytesseract (OCR)
# OCR is intentionally DISABLED for code submissions — it cannot preserve
# Python indentation and produces unparseable output.  The flag is kept so
# that any future caller can check availability without triggering an import
# error, but extract_from_image() always raises ExtractionError.
try:
    import pytesseract as _pytesseract  # noqa: F401
    _TESSERACT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per file limit

class ExtractionError(Exception):
    """Custom exception raised when text extraction fails or produces invalid content."""
    pass

async def read_bounded_file_bytes(file_obj, max_bytes: int = MAX_FILE_SIZE_BYTES) -> bytes:
    """
    Reads an UploadFile in 64KB chunks up to max_bytes.
    Raises ExtractionError if total size exceeds max_bytes before loading into memory.
    """
    chunk_size = 64 * 1024
    total_bytes = bytearray()
    while True:
        chunk = await file_obj.read(chunk_size)
        if not chunk:
            break
        total_bytes.extend(chunk)
        if len(total_bytes) > max_bytes:
            raise ExtractionError(f"File '{file_obj.filename}' exceeds maximum allowable size limit of 10 MB.")
    return bytes(total_bytes)

def extract_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from PDF file bytes using pdfplumber with fallback."""
    if not file_bytes:
        raise ExtractionError("PDF file is empty.")
    try:
        text_content = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
        
        full_text = "\n".join(text_content).strip()
        if not full_text:
            raise ExtractionError("PDF file contained no readable text.")
        return full_text
    except ExtractionError:
        raise
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        raise ExtractionError(f"Failed to extract text from PDF: {str(e)}")

def extract_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from DOCX file bytes using python-docx."""
    if not _DOCX_AVAILABLE:
        raise ExtractionError(
            "python-docx is not installed. Install it with: pip install python-docx"
        )
    if not file_bytes:
        raise ExtractionError("DOCX file is empty.")
    try:
        doc = _docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        full_text = "\n".join(paragraphs).strip()
        if not full_text:
            raise ExtractionError("DOCX file contained no text paragraphs.")
        return full_text
    except ExtractionError:
        raise
    except Exception as e:
        logger.error(f"DOCX extraction error: {str(e)}")
        raise ExtractionError(f"Failed to extract text from Word document: {str(e)}")

def extract_from_image(file_bytes: bytes) -> str:
    """
    OCR extraction of code from images is DISABLED.

    Python indentation is semantically significant.  OCR engines cannot
    reliably preserve whitespace, causing every extracted snippet to fail
    ast.parse().  Upload a .py source file instead.
    """
    raise ExtractionError(
        "Image uploads are not supported for code submissions. "
        "Please upload a .py source file."
    )

def extract_text_from_file(file_name: str, file_bytes: bytes) -> str:
    """
    Main dispatcher: detects file type by extension, extracts text, 
    and validates syntax using ast.parse().
    """
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise ExtractionError(f"File '{file_name}' exceeds maximum allowable size limit of 10 MB.")
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""
    
    if ext == "py":
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ExtractionError("Invalid encoding in .py file, expected UTF-8.")
    elif ext == "pdf":
        text = extract_from_pdf(file_bytes)
    elif ext in ["docx", "doc"]:
        text = extract_from_docx(file_bytes)
    elif ext in ["png", "jpg", "jpeg", "bmp", "tiff", "webp"]:
        text = extract_from_image(file_bytes)
    else:
        # Fallback to UTF-8 decoding for raw text/unknown extensions
        try:
            text = file_bytes.decode("utf-8")
        except Exception:
            raise ExtractionError(f"Unsupported file format '.{ext}'. Supported formats: .py, .pdf, .docx")

    if not text or not text.strip():
        raise ExtractionError("Extracted text is empty.")

    # Validate Python AST syntax
    try:
        ast.parse(text)
    except SyntaxError as se:
        logger.warning(f"AST parsing failed for extracted text from {file_name}: {str(se)}")
        raise ExtractionError("Could not parse extracted code — please verify formatting or re-upload as .py")

    return text
