import json
import logging
from typing import Any

from dotenv import load_dotenv
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq

from utils.llm_client.helper_functions import extract_json_from_response

load_dotenv()


class LLMInteraction:
    def __init__(self, model: str = "gemma2-9b-it", api_key: str = None):
        if api_key is None:
            try:
                os.getenv("GROQ_API_KEY")
            except KeyError:
                logging.error("GROQ_API_KEY environment variable not set")
        self.llm = ChatGroq(model=model, temperature=0)

    def ask_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        json_key: str | None = None,
        response_type: str = "json",
    ) -> Any:
        enhanced_system_prompt = system_prompt
        if response_type == "json":
            enhanced_system_prompt = f"""
                    {system_prompt}
                    
    
                    Respond ONLY with the JSON object, no additional text.
                    """

        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages).content
        if response_type != "json":
            return response
        try:
            json_data = json.loads(response)
            if json_key is None:
                return json_data
        except json.decoder.JSONDecodeError:
            json_data = extract_json_from_response(response)
            if json_key is None:
                return json_data
        return json_data[json_key]
