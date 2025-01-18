import io
import json
from collections import defaultdict


class JsonLException(Exception):
    """
    Base Exception for JsonL class.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class JsonL:
    """
    A class for handling and validating JSONL (JSON Lines) formatted datasets.

    This class is used to:
    - Load a JSONL file into memory.
    - Validate the structure and content of the dataset based on openai specific requirements.
    - Raise exceptions for invalid data formats.
    """
    def __init__(self):
        self.dataset: list = []

    def load_dataset(self, row_data: bytes) -> None:
        """
        Load and parse the JSONL data into the dataset.

        :param row_data: The raw JSONL data in bytes.
        :type row_data: bytes
        :raises JsonLException: If the data is not in a valid JSONL format or contains invalid entries.
        :return: None
        """
        with io.BytesIO(row_data) as f:
            try:
                self.dataset = [json.loads(line) for line in f]
            except Exception as ignore:
                raise JsonLException('Incorrect training file data')

        self.validate()

    def validate(self) -> None:
        """
        Validate the loaded dataset for structural and content correctness.

        The dataset must meet the following criteria:
        - Each entry must be a dictionary.
        - Each dictionary must have a "messages" key containing a list of messages.
        - Each message must include "role" and "content" keys.
        - "role" must be one of: "system", "user", "assistant", or "function".
        - "content" must be a string, or the message must contain a "function_call".
        - At least one message in the "messages" list must have the role "assistant".

        :raises JsonLException: If the dataset contains invalid entries.
        :return: None
        """
        format_errors = defaultdict(int)

        for ex in self.dataset:
            if not isinstance(ex, dict):
                format_errors["data_type"] += 1
                continue

            messages = ex.get("messages", None)
            if not messages:
                format_errors["missing_messages_list"] += 1
                continue

            for message in messages:
                if "role" not in message or "content" not in message:
                    format_errors["message_missing_key"] += 1

                if any(k not in ("role", "content", "name", "function_call", "weight") for k in message):
                    format_errors["message_unrecognized_key"] += 1

                if message.get("role", None) not in ("system", "user", "assistant", "function"):
                    format_errors["unrecognized_role"] += 1

                content = message.get("content", None)
                function_call = message.get("function_call", None)

                if (not content and not function_call) or not isinstance(content, str):
                    format_errors["missing_content"] += 1

            if not any(message.get("role", None) == "assistant" for message in messages):
                format_errors["example_missing_assistant_message"] += 1

            if len(format_errors) != 0:
                raise JsonLException(", ".join(f"({key}: {value})" for key, value in format_errors.items()))
