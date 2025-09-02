import logging
import tempfile
from typing import BinaryIO
from docling.document_converter import DocumentConverter


class CVParser:
    def __init__(self):
        self.converter = DocumentConverter()
        self.parsed_uploaded_resume = False
        self.resume_in_text = None

    def parse_resume(self, resume_pdf: BinaryIO):
        """Parses the resume in text format but the syntax would be markdown"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(resume_pdf.read())
            tmp_path = tmp_file.name

        parsed_resume = self.converter.convert(tmp_path).document
        self.resume_in_text = parsed_resume.export_to_text()
        logging.info("Resume processed and ready for job matching!")
        self.parsed_uploaded_resume = True
