import logging
from typing import Dict, List, Any, BinaryIO
from dataclasses import dataclass
from enum import Enum


from default_prompt_responses import general_chat_response, feature_not_added
from simple_agents.config.config import recent_postings, keys_to_display_jobs
from simple_agents.config.system_prompts import (
    system_prompt_to_identify_query_type,
    system_prompt_to_identify_job,
    system_prompt_to_identify_location,
)
from simple_agents.config.user_prompts import (
    user_prompt_to_identify_query_type,
    user_prompt_to_identify_job,
    user_prompt_to_identify_location,
)
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.llm_client.llm_interaction import LLMInteraction
from utils.locanto_scraper.locanto_scraper import LocantoScraper
from utils.resume_extractor.resume_parser import CVParser
from utils.vector_storage.qdrant_storage import QdrantStorage


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnumeratedQueryType(Enum):
    JOB_SEARCH = "job_search"
    JOB_REQUIREMENTS = "job_requirements"
    COURSE_STRUCTURE = "course_structure"
    GENERAL_CHAT = "general_chat"


@dataclass
class ChatMessage:
    message: str
    message_type: str
    timestamp: float
    metadata: Dict = None


@dataclass
class JobData:
    title: str
    description: str
    suburb: str
    requirements: List[str] = None
    technical_skills: List[str] = None
    soft_skills: List[str] = None
    salary_range: str = None


class ChatbotOrchestrator:
    def __init__(
        self,
        scraper: LocantoScraper,
        feature_extractor: JobRequirementsExtractor,
        vector_storage: QdrantStorage,
        llm_client: LLMInteraction,
        resume_parser: CVParser,
    ):
        self.scraper = scraper
        self.feature_extractor = feature_extractor
        self.vector_storage = vector_storage
        self.llm_client = llm_client
        self.conversation_history = []
        self.resume_parser = resume_parser

    def start_chat(self, user_message: str) -> str | None:
        """"""
        query_type = self.identify_user_query_type(user_message)

        if EnumeratedQueryType(query_type) == EnumeratedQueryType.JOB_SEARCH:
            location = self.identify_location(user_message)
            job_position = self.identify_job_name(user_message)
            job_search_update = self.scrape_jobs_and_save_them(
                job_position=job_position, location=location
            )
            self.conversation_history.append(user_message)
            return job_search_update
        if EnumeratedQueryType(query_type) == EnumeratedQueryType.GENERAL_CHAT:
            general_chat = general_chat_response
            return general_chat

        return feature_not_added

    def identify_user_query_type(self, user_query: str):
        """ "Identifies user query type - if user wants to scrape jobs
        or wants to retrieve details of the job or a general chat"""
        user_prompt = f"""<{user_prompt_to_identify_query_type}{user_query}>
        """

        query_type = self.llm_client.ask_llm(
            system_prompt=system_prompt_to_identify_query_type,
            user_prompt=user_prompt,
            json_key="query_type",
        )
        return query_type

    def identify_job_name(self, user_query: str):
        """From the user query and the conversation history,
        using an LLM, here we identify the job name"""
        combined_query = " ".join(self.conversation_history) + " " + user_query

        user_prompt = f"""{user_prompt_to_identify_job} {combined_query}
                """
        job_position = self.llm_client.ask_llm(
            system_prompt=system_prompt_to_identify_job,
            user_prompt=user_prompt,
            json_key="job_position",
        )
        return job_position

    def identify_location(self, user_query: str):
        """From the user query and the conversation history,
        using an LLM, here we identify the job location user is interested in"""
        combined_query = "".join(self.conversation_history) + " " + user_query
        user_prompt = f"""{user_prompt_to_identify_location} {combined_query}
                """
        location = self.llm_client.ask_llm(
            system_prompt=system_prompt_to_identify_location,
            user_prompt=user_prompt,
            json_key="location",
        )
        return location

    def scrape_jobs_and_save_them(
        self,
        job_position: str,
        location: str,
    ) -> Any:
        """Identify the job details, and scrape them."""
        logging.info("Extracting location and job details")
        self.scraper.job_to_search = job_position.lower().replace(" ", "+")
        self.scraper.location = location.lower()
        self.scraper.scrape()
        display_job_list = self.retrieve_latest_jobs()
        return display_job_list

    def retrieve_latest_jobs(self) -> list:
        job_list_to_display = [
            {key: item[key] for key in keys_to_display_jobs}
            for item in self.scraper.job_listings
            if item.get("posted_date", "No date").strip() in recent_postings
        ]
        return job_list_to_display

    def parse_resume(self, resume_pdf: BinaryIO):
        self.resume_parser.parse_resume(resume_pdf=resume_pdf)
