from abc import ABC, abstractmethod
from typing import Any


class AbstractMessageProcessor(ABC):
    def __init__(self, topic_name: str, consumer_id: str):
        self.topic_name = topic_name
        self.consumer_id = consumer_id

    @abstractmethod
    def handle_message(self, message_data: Any) -> bool:
        """
        Abstract method to process individual message data.
        Must be implemented by subclasses.

        Args:
            message_data: Parsed message data

        Returns:
            bool: True if processing succeeded, False otherwise
        """
