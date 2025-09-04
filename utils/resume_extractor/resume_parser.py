import json
import logging
import tempfile
from typing import BinaryIO
from docling.document_converter import DocumentConverter

from prompts.system_prompts import system_prompt_to_extract_resume_details
from prompts.user_prompts import user_prompt_to_extract_resume_details
from utils.llm_client.llm_interaction import LLMInteraction


class CVParser:
    def __init__(self):
        self.converter = DocumentConverter()
        self.resume_uploaded = False
        self.parsed_uploaded_resume = False
        self.resume_in_text = None
        self.llm = LLMInteraction()

    def parse_resume(self, resume_pdf: BinaryIO | str):
        """Parses the resume in text format but the syntax would be markdown"""
        try:
            if type(resume_pdf) == str:
                self.resume_in_text = resume_pdf
            else:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".pdf"
                ) as tmp_file:
                    tmp_file.write(resume_pdf.read())
                    tmp_path = tmp_file.name

                    parsed_resume = self.converter.convert(tmp_path).document
                    self.resume_in_text = parsed_resume.export_to_text()
            logging.info("Resume processed and ready for job matching!")
            self.parsed_uploaded_resume = True
        except Exception as e:
            logging.error(f"Failed to parse resume: {e}")

    def extract_resume_details(self) -> dict:
        """Extract structured requirements from job description"""

        response = self.llm.ask_llm(
            system_prompt=system_prompt_to_extract_resume_details,
            user_prompt=f"{user_prompt_to_extract_resume_details}{self.resume_in_text}",
        )
        try:
            cleaned_data = self.clean_extracted_data(response)
            return cleaned_data

        except json.JSONDecodeError:
            return {}

    def clean_extracted_data(self, data: dict) -> dict:
        """Clean and normalize extracted data"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if item:
                        string_items = self.flatten_strings(item=item)
                        for string_item in string_items:
                            normalized_item = string_item.strip().title()
                            if normalized_item and normalized_item not in cleaned_list:
                                cleaned_list.append(normalized_item)
                cleaned[key] = cleaned_list
            else:
                if value is not None and type(value) in [str]:
                    cleaned[key] = value.strip()

        return cleaned

    def flatten_strings(self, item):
        """Flatten nested structures and return only strings"""
        strings = []

        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, list):
            for sub_item in item:
                strings.extend(self.flatten_strings(sub_item))
        elif isinstance(item, dict):
            for value in item.values():
                strings.extend(self.flatten_strings(value))

        return strings
