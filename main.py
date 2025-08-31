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
    def __init__(self):
        """Initialize app state and chatbot."""
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "uploaded_resume" not in st.session_state:
            st.session_state.uploaded_resume = None

        if "resume_ready" not in st.session_state:
            st.session_state.resume_ready = False

        if "resume_text" not in st.session_state:
            st.session_state.resume_text = None

        self.agent = self.init_agent()

    @st.cache_resource
    def init_agent(_self):
        """Create and cache chatbot agent."""
        return ChatbotOrchestrator(
            feature_extractor=JobRequirementsExtractor(),
            vector_storage=QdrantStorage(),
            llm_client=LLMInteraction(),
            scraper=LocantoScraper(),
            resume_parser=CVParser(),
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
        elif file.type == "application/pdf":
            resume_text = self.agent.parse_resume(file)
        # Save results in session_state
        st.session_state.resume_text = resume_text
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
    app = JobChatApp()
    app.run()
