import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import OllamaLLM


class LLMInteraction:
    def __init__(self, model: str = "llama3.2:1b"):
        self.llm = OllamaLLM(model=model, temperature=0)

    def ask_llm(
            self,system_prompt:str,
            user_prompt:str,json_key:str
    )->str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        extracted_data = json.loads(response)
        return extracted_data[json_key]
