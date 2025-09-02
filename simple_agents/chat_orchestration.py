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
    system_prompt_to_summarise_queries,
)
from simple_agents.config.user_prompts import (
    user_prompt_to_identify_query_type,
    user_prompt_to_identify_job,
    user_prompt_to_identify_location,
    get_user_prompt_for_summary,
)
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.llm_client.llm_interaction import LLMInteraction
from utils.locanto_scraper.config import DEFAULT_LOCATION, DEFAULT_JOB_TO_SEARCH
from utils.locanto_scraper.locanto_scraper import LocantoScraper
from utils.resume_extractor.resume_parser import CVParser
from utils.vector_storage.qdrant_storage import QdrantStorage


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnumeratedQueryType(Enum):
    JOB_SEARCH = "job_search"
    JOB_REQUIREMENTS = "job_requirements"
    SUGGEST_JOBS_BY_RESUME = "suggest_jobs_by_resume"
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
        self.scraped_jobs_history = {}
        self.resume_parser = resume_parser
        self.user_query_summary = None

    def start_chat(self, user_message: str) -> str | None:
        """"""
        user_query = self.summarise_user_query(
            user_query=f"user_query:{user_message}",
        )

        query_type = self.identify_user_query_type(user_query)

        if EnumeratedQueryType(query_type) in [
            EnumeratedQueryType.JOB_SEARCH,
            EnumeratedQueryType.SUGGEST_JOBS_BY_RESUME,
        ]:
            location = self.identify_location(user_query)
            job_position = self.identify_job_name(user_query)
            scraping_done = self.job_already_scraped(
                job_position=job_position, location=location
            )

            if (
                EnumeratedQueryType(query_type)
                == EnumeratedQueryType.SUGGEST_JOBS_BY_RESUME
            ):
                return "CV matching is WIP"
            if scraping_done:
                return "Already scraped and displayed"  # Implement functionality to retrieve jobs from qdrant
            job_search_update = self.scrape_jobs_and_save_them(
                job_position=job_position, location=location
            )

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

        user_prompt = f"""{user_prompt_to_identify_job} {user_query}
                """
        try:
            job_position = self.llm_client.ask_llm(
                system_prompt=system_prompt_to_identify_job,
                user_prompt=user_prompt,
                json_key="job_position",
            )
        except:
            job_position = DEFAULT_JOB_TO_SEARCH
        return job_position

    def identify_location(self, user_query: str):
        """From the user query and the conversation history,
        using an LLM, here we identify the job location user is interested in"""
        user_prompt = f"""{user_prompt_to_identify_location} {user_query}
                """
        try:
            location = self.llm_client.ask_llm(
                system_prompt=system_prompt_to_identify_location,
                user_prompt=user_prompt,
                json_key="location",
            )
        except:
            location = DEFAULT_LOCATION
        return location

    def scrape_jobs_and_save_them(
        self,
        job_position: str,
        location: str,
    ) -> Any:
        """Identify the job details, and scrape them."""
        logging.info("Extracting location and job details")
        self.update_scraped_history(job_position=job_position, location=location)
        self.scraper.job_to_search = job_position.lower().replace(" ", "+")
        self.scraper.location = location.lower()
        self.scraper.scrape()
        display_job_list = self.retrieve_latest_jobs()
        self.summarise_user_query(
            user_query=f"computer response: The user previously requested jobs for '{self.scraper.job_to_search}' in"
            f" '{self.scraper.location}', and the results have been retrieved and shown."
        )
        return display_job_list

    def retrieve_latest_jobs(self) -> list:
        job_list_to_display = [
            {key: item[key] for key in keys_to_display_jobs}
            for item in self.scraper.job_listings
            if item.get("posted_date", "No date").strip() in recent_postings
        ]
        return job_list_to_display

    def summarise_user_query(self, user_query: str) -> str:
        if self.user_query_summary is None:
            self.user_query_summary = user_query
            return user_query
        self.user_query_summary = self.llm_client.ask_llm(
            system_prompt=system_prompt_to_summarise_queries,
            user_prompt=get_user_prompt_for_summary(
                previous_summary=self.user_query_summary, latest_message=user_query
            ),
            response_type="text",
        )
        return self.user_query_summary

    def update_scraped_history(self, job_position: str, location: str):
        """Keeps track of scraped jobs and locations"""
        job_position = job_position.lower().replace(" ", "_")
        location = location.lower().replace(" ", "_")

        if job_position not in self.scraped_jobs_history:
            self.scraped_jobs_history[job_position] = []

        if location not in self.scraped_jobs_history[job_position]:
            self.scraped_jobs_history[job_position].append(location)

    def job_already_scraped(self, job_position: str, location: str) -> bool:
        job_position = job_position.lower().replace(" ", "_")
        location = location.lower().replace(" ", "_")

        return (
            job_position in self.scraped_jobs_history
            and location in self.scraped_jobs_history[job_position]
        )
