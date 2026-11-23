
from pathlib import Path
import pymupdf
from docx import Document


def extract_pdf(file_path):

    results = []

    pdf = pymupdf.open(file_path)

    for page_number, page in enumerate(pdf, start=1):

        text = page.get_text("text").strip()

        if text:
            results.append({
                "page": page_number,
                "text": text
            })

    pdf.close()

    return results


def extract_docx(file_path):

    document = Document(file_path)

    text = "\n".join(
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    )

    return [{"page": 1, "text": text}] if text else []


def extract_txt(file_path):

    text = Path(file_path).read_text(
        encoding="utf-8-sig"
    ).strip()

    return [{"page": 1, "text": text}] if text else []


def extract_document(file_path):

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    elif extension == ".txt":
        return extract_txt(file_path)

    else:
        raise ValueError("Unsupported file type")
