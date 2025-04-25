
from typing import Dict, Any

class LLM:

    __slots__ = [
        
    ]
    def __init__(self) -> None:
        """
        Initialize the LLM class.
        """
        pass

    def create_excersize(self,
                        word_keys,
                        excersize_type,
                        current_language,
                        current_level) -> Dict[Any, Any]:
        """
        Create an excersize for the user from the database.
        """

        excersize = {
            "word_keys": word_keys,
            "initial_strings": [],
            "final_strings": [],
            "criteria": []
        }

        return excersize
    