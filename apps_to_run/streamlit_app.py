import threading
import time

import streamlit as st

from simple_agents.chat_orchestration import ChatbotOrchestrator
from format_streamlit_responses.job_listing_format import display_jobs_interactive
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.llm_client.llm_interaction import LLMInteraction
from utils.locanto_scraper.locanto_scraper import LocantoScraper
from utils.resume_extractor.resume_parser import CVParser
from utils.vector_storage.qdrant_storage import QdrantStorage


class JobChatApp:
    def __init__(
        self,
        feature_extractor_rqmt: JobRequirementsExtractor,
        vector_storage_rqmt: QdrantStorage,
        llm_client_rqmt: LLMInteraction,
        scraper_rqmt: LocantoScraper,
        resume_parser_rqmt: CVParser,
    ):
        """Initialize app state and chatbot."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "uploaded_resume" not in st.session_state:
            st.session_state.uploaded_resume = None

        if "resume_ready" not in st.session_state:
            st.session_state.resume_ready = False

        if "resume_text" not in st.session_state:
            st.session_state.resume_text = None
        self.feature_extractor = feature_extractor_rqmt
        self.vector_storage = vector_storage_rqmt
        self.llm_client = llm_client_rqmt
        self.resume_parser = resume_parser_rqmt
        self.scraper = scraper_rqmt
        self.agent = self.init_agent()

    @st.cache_resource
    def init_agent(_self):
        """Create and cache chatbot agent."""
        return ChatbotOrchestrator(
            feature_extractor=_self.feature_extractor,
            vector_storage=_self.vector_storage,
            llm_client=_self.llm_client,
            scraper=_self.scraper,
            resume_parser=_self.resume_parser,
        )

    def sidebar(self):
        """Sidebar for uploading resume."""
        with st.sidebar:
            st.header("Upload Resume")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=["pdf", "txt", "docx"],
                help="Upload your resume to get personalized job recommendations",
            )
            if uploaded_file:
                st.success(f"✅ {uploaded_file.name} uploaded successfully!")
                st.session_state.uploaded_resume = uploaded_file
                st.session_state.resume_ready = False
                threading.Thread(
                    target=self.parse_resume_background,
                    args=(uploaded_file,),
                    daemon=True,
                ).start()
                time.sleep(5)
                st.info(
                    f"✅ Resume {uploaded_file.name} processed and ready for job matching!"
                )

    def parse_resume_background(self, file):
        """Process resume in a background thread."""
        resume_text = None
        if file.type == "text/plain":
            resume_text = str(file.read(), "utf-8")
            self.agent.extract_resume_details(resume_text)
        elif file.type == "application/pdf":
            self.agent.extract_resume_details(file)
        st.session_state.resume_ready = True

    def display_chat_history(self):
        """Display stored chat messages."""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "jobs_data" in message:
                    display_jobs_interactive(message["jobs_data"])

    def handle_user_input(self, prompt: str):
        """Process user input and generate response."""
        # Store user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Process input
        with st.chat_message("assistant"):
            response = self.agent.start_chat(prompt)

            if isinstance(response, list):
                text_response = (
                    "Here are jobs filtered based on your resume:"
                    if st.session_state.resume_ready and st.session_state.resume_text
                    else "Here are the latest jobs posted in the past week:"
                )
                st.markdown(text_response)
                display_jobs_interactive(response)
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": text_response,
                        "jobs_data": response,
                    }
                )
                if not st.session_state.resume_ready:
                    st.markdown(
                        "👉 If you upload your resume, I can filter and show you jobs that best match your skills and experience."
                    )
            else:
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )

    def run(self):
        """Main entry point for the app."""
        st.title("Job Search Chatbot")

        self.sidebar()
        self.display_chat_history()

        if prompt := st.chat_input("I am an expert in job search. Let's get started!"):
            self.handle_user_input(prompt)


if __name__ == "__main__":
    feature_extractor = JobRequirementsExtractor()
    vector_storage = QdrantStorage()
    llm_client = LLMInteraction()
    scraper = LocantoScraper()
    resume_parser = CVParser()
    app = JobChatApp(
        feature_extractor_rqmt=feature_extractor,
        vector_storage_rqmt=vector_storage,
        llm_client_rqmt=llm_client,
        scraper_rqmt=scraper,
        resume_parser_rqmt=resume_parser,
    )
    app.run()
