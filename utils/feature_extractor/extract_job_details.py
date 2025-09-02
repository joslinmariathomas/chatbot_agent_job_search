import json
from dotenv import load_dotenv

from prompts.system_prompts import system_prompt_to_extract_job_features
from prompts.user_prompts import user_prompt_to_extract_job_features
from utils.llm_client.llm_interaction import LLMInteraction

load_dotenv()


class JobRequirementsExtractor:
    def __init__(
        self,
    ):
        self.llm = LLMInteraction()

    def extract_requirements(self, job_description: str) -> dict:
        """Extract structured requirements from job description"""

        response = self.llm.ask_llm(
            system_prompt=system_prompt_to_extract_job_features,
            user_prompt=f"{user_prompt_to_extract_job_features}{job_description}",
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
