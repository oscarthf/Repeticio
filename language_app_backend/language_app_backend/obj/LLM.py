
from typing import Dict, Any
import json

from ..util.prompts.one_blank import prompts as ONE_BLANK_EXERCISE_PROMPTS
from ..util.prompts.two_blank import prompts as TWO_BLANK_EXERCISE_PROMPTS
from ..util.prompts.vocabulary import (
    REVISE_VOCABULARY_PROMPT,
    INITIAL_WORD_PROMPT
)
from ..util.constants import (
    REAL_LANGUAGE_NAMES,
    OPENAI_MODEL_NAME,
)
from ..util.inference import get_inference_client

def get_language_string(language: str) -> str:

    real_language_name = REAL_LANGUAGE_NAMES[language]

    language_str = f"{real_language_name} ({language})"

    return language_str

def validate_exercise(exercise: Dict[str, Any], word_values: list) -> bool:

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
    #     "criteria": 0
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
    
    # check if the number of criteria is correct
    if not isinstance(output_criteria, int):
        print(f"Invalid criteria in output: {output_criteria}")
        return False
    
    return True

class LLM:

    __slots__ = [
        
    ]
    def __init__(self) -> None:
        """
        Initialize the LLM class.
        """

        self.client = get_inference_client()

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

        exercise_index = exercise_type.split("_")[1]

        if len(word_values) == 1:
            query_input = ONE_BLANK_EXERCISE_PROMPTS[exercise_index]
        elif len(word_values) == 2:
            query_input = TWO_BLANK_EXERCISE_PROMPTS[exercise_index]
        else:
            print("Invalid number of words for exercise.")
            return None

        language_str = get_language_string(language)
        level_str = f"Level {level}"
        words_str = ", ".join(word_values)

        query_input = query_input.replace("[TARGET LANGUAGE]", language_str)
        query_input = query_input.replace("[TARGET LEVEL]", level_str)
        query_input = query_input.replace("[TARGET WORDS]", words_str)

        query_input += "Answers in the examples may be wrong, please respond with a correct answer in the 'criteria' field."


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
        
        is_valid = validate_exercise(json_data, word_values)

        if not is_valid:
            print("Invalid exercise format")
            return None
        
        return json_data
    
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
            model=OPENAI_MODEL_NAME,
            input=query_input
        )

        
        # ALTERNATIVE EXAMPLE
        # completion = client.chat.completions.create(
        # model="gpt-4o-mini",
        # store=True,
        # messages=[
        #     {"role": "user", "content": "write a haiku about ai"}
        # ]
        # )

        # print(completion.choices[0].message);

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

        
