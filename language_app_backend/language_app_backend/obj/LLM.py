
from typing import Dict, Any, Optional, List
import json

import numpy as np

from ..util.prompts.one_blank import start_prompt as ONE_BLANK_EXERCISE_START_PROMPT
from ..util.prompts.one_blank import inspiration_exercises as ONE_BLANK_EXERCISE_INSPIRATION_EXERCISES
from ..util.prompts.two_blank import start_prompt as TWO_BLANK_EXERCISE_START_PROMPT
from ..util.prompts.two_blank import inspiration_exercises as TWO_BLANK_EXERCISE_INSPIRATION_EXERCISES
from ..util.prompts.vocabulary import (
    INITIAL_WORD_PROMPT,
)
from ..util.constants import (
    REAL_LANGUAGE_NAMES,
    OPENAI_MODEL_NAME,
    MAX_WORD_LENGTH,
)
from ..util.inference import get_inference_client

def get_language_string(language: str) -> str:

    real_language_name = REAL_LANGUAGE_NAMES[language]

    language_str = f"{real_language_name} ({language})"

    return language_str

def remove_duplicate_words(json_data: Dict[str, Any]) -> Dict[str, Any]:

    """
    Remove duplicate words from the JSON data.
    """
    
    words_so_far = set()

    for level in json_data:
        for word in json_data[level]:
            if word in words_so_far:
                json_data[level].remove(word)
            else:
                words_so_far.add(word)

    return json_data

def validate_exercise(exercise: Dict[str, Any], 
                      word_values: List[str],
                      possible_criteria: List[str]) -> bool:

    # {
    #     "word_values": ["grande"],
    #     "initial_strings": [
    #         "grande"
    #     ],
    #     "middle_strings": [
    #         "Choose the correct synonym:"
    #     ],
    #     "final_strings": [
    #         "a) enorme",
    #         "b) pequeño",
    #         "c) estrecho",
    #         "d) corto"
    #     ],
    #     "criteria": "a"
    # }

    number_of_keys = len(exercise.keys())

    if number_of_keys != 5:
        print(f"Invalid number of keys in JSON: {number_of_keys}")
        return False
    
    if not "word_values" in exercise or not "initial_strings" in exercise or not "middle_strings" in exercise or not "final_strings" in exercise or not "criteria" in exercise:
        print(f"Invalid keys in JSON: {exercise.keys()}")
        return False
    
    output_word_values = exercise["word_values"]
    output_initial_strings = exercise["initial_strings"]
    output_middle_strings = exercise["middle_strings"]
    output_final_strings = exercise["final_strings"]
    output_criteria = exercise["criteria"]

    # Check if the number of words in the output matches the input
    if len(output_word_values) != len(word_values):
        print(f"Invalid number of words in output: {len(output_word_values)}")
        return False
    
    for word_value in word_values:
        if not word_value in output_word_values:
            print(f"Invalid word in output: {word_value}")
            return False
        
    # check if the number of initial strings is correct
    if len(output_initial_strings) != 1:
        print(f"Invalid number of initial strings in output: {len(output_initial_strings)}")
        return False
    
    for initial_string in output_initial_strings:
        if not isinstance(initial_string, str):
            print(f"Invalid initial string in output: {initial_string}")
            return False
        
        if len(initial_string) < 1 or len(initial_string) > 100:
            print(f"Invalid initial string length in output: {len(initial_string)}")
            return False
    
    # check if the number of middle strings is correct
    if len(output_middle_strings) != 1:
        print(f"Invalid number of middle strings in output: {len(output_middle_strings)}")
        return False
    
    for middle_string in output_middle_strings:
        if not isinstance(middle_string, str):
            print(f"Invalid middle string in output: {middle_string}")
            return False
        
        if len(middle_string) < 1 or len(middle_string) > 100:
            print(f"Invalid middle string length in output: {len(middle_string)}")
            return False
    
    # check if the number of final strings is correct
    if len(output_final_strings) < 2 or len(output_final_strings) > 4:
        print(f"Invalid number of final strings in output: {len(output_final_strings)}")
        return False
    
    for final_string in output_final_strings:
        if not isinstance(final_string, str):
            print(f"Invalid final string in output: {final_string}")
            return False
        
        if len(final_string) < 1 or len(final_string) > 100:
            print(f"Invalid final string length in output: {len(final_string)}")
            return False
    
    if not isinstance(output_criteria, str):
        print(f"Invalid criteria in output: {output_criteria}")
        return False
    
    if not output_criteria in possible_criteria:
        print(f"Invalid criteria in output: {output_criteria}")
        return False
    
    return True

def get_inspiration_prompt(inspiration_exercises, is_one_blank):

    num_inspiration_exercises_so_far = len(inspiration_exercises)
    if num_inspiration_exercises_so_far < 3:
        for e_i in range(3 - num_inspiration_exercises_so_far):
            if is_one_blank:
                inspiration_exercise = ONE_BLANK_EXERCISE_INSPIRATION_EXERCISES[e_i]
            else:
                inspiration_exercise = TWO_BLANK_EXERCISE_INSPIRATION_EXERCISES[e_i]

    inspiration_prompt = ",\n".join([json.dumps(exercise, indend=4) for exercise in inspiration_exercises])

    return inspiration_prompt

class LLM:

    __slots__ = [
        "client",
    ]
    def __init__(self) -> None:
        """
        Initialize the LLM class.
        """

        self.client = get_inference_client()

    def create_exercise(self,
                        word_values,
                        language,
                        level,
                        inspiration_exercises,
                        possible_criteria:List[str] = ['a', 'b', 'c', 'd', 'e']) -> Dict[Any, Any]:
        """
        Create an exercise for the user from the database.
        """

        exercise = {
            "word_values": word_values,
            "number_of_words": len(word_values),
            "language": language,
            "level": level,
            "initial_strings": [],
            "middle_strings": [],
            "final_strings": [],
            "criteria": []
        }

        is_one_blank = False

        if len(word_values) == 1:
            is_one_blank = True
            query_input = ONE_BLANK_EXERCISE_START_PROMPT
            query_input += get_inspiration_prompt(inspiration_exercises, True)
        elif len(word_values) == 2:
            query_input = TWO_BLANK_EXERCISE_START_PROMPT
            query_input += get_inspiration_prompt(inspiration_exercises, False)
        else:
            print("Invalid number of words for exercise.")
            return None

        language_str = get_language_string(language)
        level_str = f"Level {level}"

        if is_one_blank:
            words_str = f"word: {word_values[0]}"
        else:
            focus_word = np.random.choice(word_values)
            words_str = f"word: {focus_word}, and use this word somewhere in the exercise too.

        query_input = query_input.replace("[TARGET LANGUAGE]", language_str)
        query_input = query_input.replace("[TARGET LEVEL]", level_str)
        query_input = query_input.replace("[TARGET WORDS]", words_str)

        response = self.client.responses.create(
            model=OPENAI_MODEL_NAME,
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
        
        is_valid = validate_exercise(json_data, 
                                     word_values,
                                     possible_criteria=possible_criteria)

        if not is_valid:
            print("Invalid exercise format")
            return None
        
        exercise["initial_strings"] = json_data["initial_strings"]
        exercise["middle_strings"] = json_data["middle_strings"]
        exercise["final_strings"] = json_data["final_strings"]
        
        criteria = json_data["criteria"].lower()
        criteria = possible_criteria.index(criteria)
        exercise["criteria"] = criteria
        
        return exercise
    
    def get_new_word(self,
                     language,
                     vocabulary_word_values) -> Optional[str]:
        
        """
        Get a new word for the given language which is not already in the vocabulary.
        """

        if not language in REAL_LANGUAGE_NAMES:
            print(f"Language '{language}' is not supported.")
            return None
        
        language_str = get_language_string(language)

        words_str = ", ".join(vocabulary_word_values)
        query_input = f"Please suggest a new word in {language_str} that is not already in the vocabulary: {words_str}."
        query_input += "\n\nPlease respond with only one word."
        query_input += "\n\nNo explanation is needed, just the word."

        response = self.client.responses.create(
            model=OPENAI_MODEL_NAME,
            input=query_input
        )

        print(response.output_text)

        if not isinstance(response.output_text, str):
            print("Invalid response format")
            return None
        

        output_value = response.output_text.strip()
        if len(output_value) < 1 or len(output_value) > MAX_WORD_LENGTH:
            print(f"Invalid output value: {output_value}")
            return None
        

        if output_value in vocabulary_word_values:
            print(f"Word '{output_value}' is already in the vocabulary.")
            return None
        
        return output_value
    
    def get_word_level(self,
                       word_value,
                       language) -> Optional[int]:

        """
        Get the level of the word for the given language.
        """

        if not language in REAL_LANGUAGE_NAMES:
            print(f"Language '{language}' is not supported.")
            return None
        
        language_str = get_language_string(language)

        query_input = f"Please estimate the CEFR level of the word '{word_value}' in {language_str}."
        query_input += "\n\nPlease respond with only one integer value, 0-2, where 0 = A1, 1 = A2, 2 = B1."
        query_input += "\n\nNo explanation is needed, just the number."



        response = self.client.responses.create(
            model=OPENAI_MODEL_NAME,
            input=query_input
        )

        print(response.output_text)

        if not response.output_text.isdigit():
            print("Invalid response format")
            return None
        
        output_value = int(response.output_text)
        if output_value < 0 or output_value > 2:
            print(f"Invalid output value: {output_value}")
            return None
        
        return output_value

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
            model=OPENAI_MODEL_NAME,
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
        
        json_data = {language: json_data[list(json_data.keys())[0]]}
        
        if len(json_data[language]) != 3:
            print(f"Invalid number of levels in JSON: {len(json_data[language])}")
            return None

        for level in json_data[language]:
            if len(json_data[language][level]) < 5:
                print(f"Invalid number of words in level {level}: {len(json_data[language][level])}")
                return None
            
            for word in json_data[language][level]:
                if not isinstance(word, str):
                    print(f"Invalid word format in level {level}: {word}")
                    return None
                
        json_data = remove_duplicate_words(json_data)

        return json_data

        
