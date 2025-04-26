
from typing import Dict, Any
import json

from openai import OpenAI

from ..util.prompts import (
    MULTIPLE_CHOICE_EXERCISE_PROMPT,
    FILL_IN_THE_BLANK_EXERCISE_PROMPT,
    REVISE_VOCABULARY_PROMPT,
    INITIAL_WORD_PROMPT
)
from ..util.constants import (
    REAL_LANGUAGE_NAMES,
)

def get_language_string(language: str) -> str:

    real_language_name = REAL_LANGUAGE_NAMES[language]

    language_str = f"{real_language_name} ({language})"

    return language_str

class LLM:

    __slots__ = [
        
    ]
    def __init__(self) -> None:
        """
        Initialize the LLM class.
        """

        self.client = OpenAI()

    def create_exercise(self,
                        word_values,
                        word_keys,
                        exercise_type,
                        language,
                        level) -> Dict[Any, Any]:
        """
        Create an exercise for the user from the database.
        """

        exercise = {
            "word_keys": word_keys,
            "word_values": word_values,
            "exercise_type": exercise_type,
            "language": language,
            "level": level,
            "initial_strings": [],
            "middle_strings": [],
            "final_strings": [],
            "criteria": []
        }

        if exercise_type == "multiple_choice":
            query_input = MULTIPLE_CHOICE_EXERCISE_PROMPT
        elif exercise_type == "fill_in_the_blank":
            query_input = FILL_IN_THE_BLANK_EXERCISE_PROMPT
        else:
            print(f"Exercise type '{exercise_type}' is not supported.")
            return None

        language_str = get_language_string(language)
        level_str = f"Level {level}"
        words_str = ", ".join(word_values)

        query_input = query_input.replace("[TARGET LANGUAGE]", language_str)
        query_input = query_input.replace("[TARGET LEVEL]", level_str)
        query_input = query_input.replace("[TARGET WORDS]", words_str)

        return exercise
    
    def revise_vocabulary(self,
                          language,
                          language_data) -> Dict[Any, Any]:
        """
        Revise the vocabulary for the given language.
        """

        if not language in REAL_LANGUAGE_NAMES:
            print(f"Language '{language}' is not supported.")
            return None
        
        language_str = get_language_string(language)

        query_input = REVISE_VOCABULARY_PROMPT.replace("[TARGET LANGUAGE]", language_str)

        return language_data

    def get_initial_words(self,
                          language):
        
        """
        Get the initial words for the given language.
        """

        if not language in REAL_LANGUAGE_NAMES:
            print(f"Language '{language}' is not supported.")
            return None
        
        language_str = get_language_string(language)

        query_input = INITIAL_WORD_PROMPT.replace("[TARGET LANGUAGE]", language_str)

        response = self.client.responses.create(
            model="gpt-4.1",
            input=query_input
        )

        print(response.output_text)

        if not "{" in response.output_text or not "}" in response.output_text:
            print("Invalid response format")
            return None

        start_index = response.output_text.find("{")
        end_index = response.output_text.rfind("}")

        json_string = response.output_text[start_index:end_index + 1]
        try:
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
        
        number_of_keys = len(json_data.keys())

        if number_of_keys != 1:
            print(f"Invalid number of keys in JSON: {number_of_keys}")
            return None
        
        json_data = {language: json_data[json_data.keys()[0]]}
        
        if len(json_data[language]) != 3:
            print(f"Invalid number of levels in JSON: {len(json_data[language])}")
            return None

        for level in json_data[language]:
            if len(json_data[language][level]) != 100:
                print(f"Invalid number of words in level {level}: {len(json_data[language][level])}")
                return None
            
            for word in json_data[language][level]:
                if not isinstance(word, str):
                    print(f"Invalid word format in level {level}: {word}")
                    return None

        return json_data

        
