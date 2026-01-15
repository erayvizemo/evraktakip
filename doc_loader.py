import pdfplumber
import docx
import io

def extract_text_from_pdf(file_bytes):
    """
    Extracts text from a PDF file (bytes).
    """
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_bytes):
    """
    Extracts text from a DOCX file (bytes).
    """
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def load_document(uploaded_file):
    """
    Router to load document based on type.
    """
    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file.getvalue())
    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(uploaded_file.getvalue())
    else:
        return "Unsupported file format."
