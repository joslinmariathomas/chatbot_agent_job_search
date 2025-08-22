from langchain_ollama.llms import OllamaLLM
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict
import json


class JobRequirementsExtractor:
    def __init__(self, model: str = "llama3.2:1b"):
        self.llm = OllamaLLM(model=model, temperature=0)

    def extract_requirements(self, job_description: str) -> Dict:
        """Extract structured requirements from job description"""

        system_prompt = """You are an expert skill extractor specializing in analyzing job postings. Your task is to extract key requirements and technical skills from job descriptions with high precision.

        Extract information into these categories:
        1. REQUIRED_SKILLS: Core technical skills explicitly required
        2. PREFERRED_SKILLS: Nice-to-have or preferred skills
        3. EXPERIENCE_LEVEL: Years of experience required
        4. EDUCATION: Educational requirements
        5. TECHNOLOGIES: Specific tools, frameworks, programming languages
        6. SOFT_SKILLS: Communication, leadership, teamwork skills
        7. SALARY_RANGE: Salary ranges if present
        8. EMPLOYMENT_TYPE: Full-time,Part-time,hybrid,remote,on-site

        Rules:
        - Extract exact skill names (e.g., "Python", not "programming languages")
        - Separate required vs preferred skills
        - Include version numbers if mentioned (e.g., "Python 3.8+")
        - Extract salary ranges if present
        - Identify employment type (full-time, contract, etc.)
        """

        human_prompt = f"""
        Analyze this job description and extract structured information. Return ONLY valid JSON in this exact format:

        {{
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill3", "skill4"],
            "experience_level": "3-5 years",
            "education": ["Bachelor's in Computer Science"],
            "technologies": ["Python", "SQL", "AWS"],
            "soft_skills": ["Communication", "Problem-solving"],
            "salary_range": "$80,000 - $120,000",
            "employment_type": "full-time",
        }}

        Job Description:
        {job_description}
        """

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        response = self.llm.invoke(messages)

        try:
            extracted_data = json.loads(response)
            cleaned_data = self._clean_extracted_data(extracted_data)

            return cleaned_data

        except json.JSONDecodeError:
            return {}
    @staticmethod
    def _clean_extracted_data(data: Dict) -> Dict:
        """Clean and normalize extracted data"""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if item and item.strip():
                        normalized_item = item.strip().title()
                        if normalized_item not in cleaned_list:
                            cleaned_list.append(normalized_item)
                cleaned[key] = cleaned_list
            else:
                cleaned[key] = value.strip() if value else None

        # Merge similar categories
        all_tech_skills = cleaned.get("technologies", [])
        # Add technology mapping for common variations
        tech_mapping = {
            "Ml": "Machine Learning",
            "Ai": "Artificial Intelligence",
            "Js": "JavaScript",
            "Css": "CSS",
            "Html": "HTML",
        }

        normalized_tech = []
        for tech in all_tech_skills:
            normalized_tech.append(tech_mapping.get(tech, tech))

        cleaned["all_technologies"] = list(set(normalized_tech))

        return cleaned
