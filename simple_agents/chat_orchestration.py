import logging
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

from tqdm import tqdm

from default_prompt_responses import general_chat_response, feature_not_added
from simple_agents.system_prompts import (
    system_prompt_to_identify_query_type,
    system_prompt_to_identify_job,
    system_prompt_to_identify_location,
)
from simple_agents.user_prompts import (
    user_prompt_to_identify_query_type,
    user_prompt_to_identify_job,
    user_prompt_to_identify_location,
)
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.llm_client.llm_interaction import LLMInteraction
from utils.locanto_scraper.locanto_scraper import LocantoScraper
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
    ):
        self.scraper = scraper
        self.feature_extractor = feature_extractor
        self.vector_storage = vector_storage
        self.llm_client = llm_client
        self.conversation_history = []

    def start_chat(self, user_message: str) -> str | None:
        """"""
        query_type = self.identify_user_query_type(user_message)

        if EnumeratedQueryType(query_type) == EnumeratedQueryType.JOB_SEARCH:
            location = self.identify_location(user_message)
            job_position = self.identify_job_name(user_message)
            self.scrape_jobs_and_save_them(job_position=job_position, location=location)
            return "Jobs have been saved"
        if EnumeratedQueryType(query_type) == EnumeratedQueryType.GENERAL_CHAT:
            general_chat = general_chat_response
            return general_chat

        return feature_not_added

    def identify_user_query_type(self, user_query: str):
        """ "Identifies user query type - if user wants to scrape jobs
        or wants to retrieve details of the job or a general chat"""
        user_prompt = f"""{user_prompt_to_identify_query_type} {user_query}
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
    ):
        """Identify the job details, and scrape them."""
        logging.info("Extracting location and job details")
        self.scraper.job_to_search = job_position.lower().replace(" ", "+")
        self.scraper.location = location.lower()
        self.scraper.scrape()
        scraped_jobs = self.scraper.job_listings
        self.extract_features_and_save_in_qdrant(
            job_listings=scraped_jobs, job_position=job_position, location=location
        )

    def extract_features_and_save_in_qdrant(
        self, job_listings: list, job_position: str, location: str
    ):

        jobs_features_extracted_list = []
        for i in tqdm(
            range(len(job_listings)),
            desc="Extracting features from job listings",
            ncols=100,
        ):
            job_listing = job_listings[i]
            job_key_fields_extracted = self.feature_extractor.extract_requirements(
                job_description=job_listing["description"]
            )
            combined_job_details_dict = {**job_listing, **job_key_fields_extracted}
            jobs_features_extracted_list.append(combined_job_details_dict)
        if jobs_features_extracted_list:
            self.save_to_qdrant(
                job_listings=jobs_features_extracted_list,
                job_position=job_position,
                location=location,
            )

    def save_to_qdrant(
        self,
        job_listings: list[dict],
        job_position: str,
        location: str,
    ):
        storage_name = f"{job_position}-{location}"
        self.vector_storage.collection_name = storage_name
        self.vector_storage.create_collection()
        self.vector_storage.upload_points(
            points=job_listings, key_to_encode="description"
        )
