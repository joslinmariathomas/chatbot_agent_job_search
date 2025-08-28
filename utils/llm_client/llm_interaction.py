import json
from typing import Type
import re
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import OllamaLLM
from pydantic import BaseModel


class LLMInteraction:
    def __init__(self, model: str = "llama3.2:1b"):
        self.llm = OllamaLLM(model=model, temperature=0)

    def ask_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        json_key: str,
        json_schema_reference: Type[BaseModel],
    ) -> str:
        enhanced_system_prompt = f"""
                {system_prompt}
                

                Respond ONLY with the JSON object, no additional text.
                """
        messages = [
            SystemMessage(content=enhanced_system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        try:
            json_data = json.loads(response)
        except json.decoder.JSONDecodeError:
            json_string = self.extract_json_from_response(response)
            json_data = json.loads(json_string)
        return json_data[json_key]

    @staticmethod
    def extract_json_from_response(response: str) -> str:
        """Extract JSON from LLM response, handling various formats"""
        # Strip whitespace
        response = response.strip()
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response)
        if json_match:
            json_match = json_match.group(1).strip()
            try:
                response = json.loads(json_match)
                return response
            except json.decoder.JSONDecodeError:
                if not response.startswith("{") or not response.endswith("}"):
                    response = "{" + response + "}"
                return response

        if not response.startswith("{") or not response.endswith("}"):
            response = "{" + response + "}"
        return response
