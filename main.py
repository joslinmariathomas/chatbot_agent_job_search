import streamlit as st

from simple_agents.chat_orchestration import ChatbotOrchestrator
from utils.feature_extractor.extract_job_details import JobRequirementsExtractor
from utils.llm_client.llm_interaction import LLMInteraction
from utils.locanto_scraper.locanto_scraper import LocantoScraper
from utils.vector_storage.qdrant_storage import QdrantStorage


@st.cache_resource
def init_agent():
    chatbot = ChatbotOrchestrator(
        feature_extractor=JobRequirementsExtractor(),
        vector_storage=QdrantStorage(),
        llm_client=LLMInteraction(),
        scraper=LocantoScraper(),
    )
    return chatbot


# Streamlit UI
st.title("AI Chatbot")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("I am an expert in job search. Let's get started!"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get agent response
    with st.chat_message("assistant"):
        agent = init_agent()
        response = agent.start_chat(prompt)  # Replace with your agent's method
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
