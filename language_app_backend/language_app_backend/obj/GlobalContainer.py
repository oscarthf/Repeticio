
from typing import Optional, Tuple, Dict, Any
import datetime

import uuid

import numpy as np

from pymongo import ASCENDING as PY_MONGO_ASCENDING

from ..util.prompts.one_blank import prompts as ONE_BLANK_EXERCISE_PROMPTS
from ..util.prompts.two_blank import prompts as TWO_BLANK_EXERCISE_PROMPTS
from ..util.constants import (SUPPORTED_LANGUAGES,
                              NEXT_WORD_TEMPERATURE, 
                              MAX_HISTORY_LENGTH)

def next_word(word_keys, 
              word_scores, 
              word_last_visited_times,
              temperature=NEXT_WORD_TEMPERATURE) -> str:
    
    """
    Select the next word to show to the user based on their last visited times and scores.
    """

    assert len(word_keys) == len(word_scores) == len(word_last_visited_times), "All lists must be of the same length."
    assert len(word_keys) > 0, "No words available to select from."

    # adjusted score = (1 - score) * (1 + time_since_last_visit)

    word_last_visited_times = [datetime.datetime.fromtimestamp(time, tz=datetime.timezone.utc) for time in word_last_visited_times]
    current_time = datetime.datetime.now(datetime.timezone.utc)

    oldest_time = min(word_last_visited_times) if len(word_last_visited_times) else current_time
    time_since_oldest_visit = (current_time - oldest_time).total_seconds() / 3600  # in hours

    if time_since_oldest_visit <= 0:
        print("No words have been visited yet, returning random word.")
        return np.random.choice(word_keys)

    word_last_visited_times = [(current_time - time).total_seconds() for time in word_last_visited_times]

    word_last_visited_times = np.array(word_last_visited_times) / 3600
    word_last_visited_times = word_last_visited_times / time_since_oldest_visit

    scores = np.array(word_scores)

    adjusted_scores = (1 - scores) * (1 + word_last_visited_times) - 1

    best_word_index_before_noise = np.argmax(adjusted_scores)

    # apply temperature noise
    noise = np.random.normal(0, temperature, size=adjusted_scores.shape)
    adjusted_scores = np.array(adjusted_scores) + noise

    best_word_index_after_noise = np.argmax(adjusted_scores)

    if not best_word_index_before_noise == best_word_index_after_noise:
        print(f"Best word before noise: {word_keys[best_word_index_before_noise]}")
        print(f"Best word after noise: {word_keys[best_word_index_after_noise]}")
        print(f"Temperature: {temperature}, number of words: {len(word_keys)}")

    return word_keys[best_word_index_after_noise]
    
def empty_user(user_id, language) -> Dict[Any, Any]:
    """
    Create an empty user document for the database.
    """

    user_entry = {
        "user_id": user_id, 
        "xp": 0,
        "current_language": language,
        "languages": {
            "language": {
                "current_level": 0,
            }
        }
    }

    return user_entry

def empty_exercise_doc(exercise_key) -> Dict[Any, Any]:
    """
    Create an empty exercise document for the database.
    """
    return {
        "_id": exercise_key,
        "exercise_list": [],
    }

def empty_word_entry(word_key,
                     user_id,
                     language) -> Dict[Any, Any]:

    """
    Create an empty word entry for the database.
    """
    return {
        "_id": word_key,
        "user_id": user_id,
        "language": language,
        "last_visited_times": [],
        "last_scores": [],
        "is_locked": True
    }

def empty_word_document(word_key,
                        word_value,
                        language,
                        level) -> Dict[Any, Any]:

    """
    Create an empty word document for the database.
    """
    return {
        "_id": word_key,
        "word_value": word_value,
        "language": language,
        "level": level,
        "translations": [],
    }

class GlobalContainer:
    __slots__ = [
        "db_client", 
        "db",
        "settings_collection",
        "words_collection",
        "user_words_collection",
        "users_collection",
        "exercises_collection",
    ]
    def __init__(self, 
                 db_client,
                 llm) -> None:

        self.db_client = db_client
        self.db = db_client["language_app"]
        self.settings_collection = self.db["settings"]
        self.words_collection = self.db["words"]
        self.user_words_collection = self.db["user_words"]
        self.users_collection = self.db["users"]
        self.exercises_collection = self.db["exercises"]

        self.llm = llm

        # Create indexes on commonly queried fields
        self.create_indexes()

        self.populate_initial_words()

    def create_indexes(self):

        """
        Create indexes on the database collections to speed up queries.
        """

        has_created_indexes = self.settings_collection.find_one({"_id": "indexes_created"})
        if has_created_indexes:
            print("Indexes already created in the database.")
            return
        
        ##################################################################
        
        self.words_collection.create_index([('language', PY_MONGO_ASCENDING), ('level', PY_MONGO_ASCENDING)])
        self.user_words_collection.create_index([('user_id', PY_MONGO_ASCENDING), ('_id', PY_MONGO_ASCENDING), ('is_locked', PY_MONGO_ASCENDING)])
        self.users_collection.create_index([('user_id', PY_MONGO_ASCENDING)], unique=True)
        self.exercises_collection.create_index([('_id', PY_MONGO_ASCENDING)])

        ##################################################################

        self.settings_collection.insert_one({
            "_id": "indexes_created",
            "created": True
        })
        print("Indexes created in the database.")

    def populate_initial_words(self, 
                               language) -> bool:

        """
        Populate the database with initial words.
        """

        if language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for initial words.")
            return False
        
        has_populated_initial_words = self.settings_collection.find_one({"_id": f"initial_words_populated_{language}"})

        if has_populated_initial_words:
            print("Initial words already populated in the database.")
            return False
        
        initial_words = self.llm.get_initial_words(language)

        if not initial_words:
            print("No initial words found for the language.")
            return False

        for level, word_values in initial_words[language].items():
            for word_value in word_values:
                word_key = str(uuid.uuid4())
                word_value = word_value.replace(" ", "_")
                word_doc = empty_word_document(word_key,
                                                word_value,
                                                language,
                                                level)
                self.words_collection.insert_one(word_doc)

        self.settings_collection.insert_one({
            "_id": f"initial_words_populated_{language}",
            "populated": True
        })
        print(f"Initial words populated in the database for language '{language}'.")

        return True
    
    def get_words_for_level(self,
                            language,
                            level) -> list:
        
        """
        Get words for a specific level in a specific language.
        """

        if language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for initial words.")
            return []
        
        if level not in [0, 1, 2]:
            print(f"Unsupported level '{level}' for initial words.")
            return []
        
        words = self.words_collection.find({"language": language, "level": level})

        words_list = [word["_id"] for word in words]

        print(f"Words for language '{language}' and level '{level}': {words_list}.")

        return words_list
    
    def create_user(self, 
                    user_id,
                    language) -> bool:
        """
        Create a user in the database
        """

        new_user = empty_user(user_id, 
                                language)

        self.users_collection.insert_one(new_user)
        
        print(f"User {user_id} created in the database.")
        return True
    
    def get_user_words(self,
                        user_id,
                        language,
                        is_locked) -> Optional[list]:
        """
        Get the user's words from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        # Get the words list from the user words collection
        user_words = self.user_words_collection.find({"user_id": user_id, 
                                                      "language": language,
                                                      "is_locked": is_locked})
        
        user_words = list(user_words)
        
        if not len(user_words):
            print(f"No words found for user {user_id}.")
            return None
        
        user_words_keys = [word["_id"] for word in user_words]

        return user_words_keys
        
    def check_if_should_unlock_new_word(self, 
                                        user_id) -> int:
        """
        Check if the user should unlock a new word based on their score.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return -1
        
        current_language = user.get("current_language", None)
        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return -1

        language_data = user.get("languages", {}).get(current_language, None)
        if language_data is None:
            print(f"No language data found for user {user_id} in language '{current_language}'.")
            return -1
        
        words = self.get_user_words(user_id, 
                                    current_language,
                                    False)

        if words is None:
            print(f"No words found for user {user_id}.")
            return -1

        locked_words = self.get_user_words(user_id, 
                                           current_language,
                                           True)

        if locked_words is None:
            print(f"No locked words found for user {user_id}.")
            return -1

        if not len(locked_words):
            print(f"No locked words found for user {user_id}.")
            # check if the user is at the max level
            current_level = language_data.get("current_level", 0)
            supported_levels = [0, 1, 2]
            if current_level >= len(supported_levels) - 1:
                print(f"User {user_id} is at the max level for language '{current_language}'.")
                return 4
            
            # add next set of words to locked words
            this_level_words = self.get_words_for_level(current_language, current_level)

            word_keys = [word["_id"] for word in words]
            this_level_words_not_in_words = [word for word in this_level_words if word not in word_keys]
            
            if not len(this_level_words_not_in_words):
                print(f"User {user_id} already has all words for level {current_level}.")
                current_level += 1
                # increase level
                self.users_collection.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "languages." + current_language + ".current_level": current_level
                    }}
                )
                print(f"User {user_id} is now at level {current_level}.")
                return 3
            
            random_word_key = np.random.choice(this_level_words_not_in_words)

            self.add_word_to_locked_words(user_id,
                                            random_word_key,
                                            current_language)
        
        if not len(words):
            unlocked_word = locked_words.pop(0)
            word_key = unlocked_word["_id"]
            self.user_words_collection.update_one(
                {"_id": word_key,
                 "user_id": user_id},
                {"$set": {
                    "is_locked": False
                }}
            )

            print(f"Unlocked new word for user {user_id}: {unlocked_word}.")
            return 1
        
        # count the number of words that need work
        needs_work_count = 0
        for word in words:
            if word["last_scores"][-1] < 0.5:
                needs_work_count += 1

        percentage_needs_work = needs_work_count / len(words) * 100

        print(f"User {user_id} has {percentage_needs_work:.2f}% of words needing work.")

        if percentage_needs_work > 50:
            # unlock a new word if more than 50% of words need work
            unlocked_word = locked_words.pop(0)
            word_key = unlocked_word["_id"]
            self.user_words_collection.update_one(
                {"_id": word_key,
                 "user_id": user_id},
                {"$set": {
                    "is_locked": False
                }}
            )
            print(f"Unlocked new word for user {user_id}: {unlocked_word}.")
            return 2

        else:

            print(f"User {user_id} does not need to unlock a new word.")
            return 0

    def update_word_in_user_words(self, 
                                  user_id, 
                                  word_key, 
                                  score) -> bool:
        """
        Update the word in the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        current_language = user.get("current_language", None)
        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return False

        selected_word = self.user_words_collection.find_one({"_id": word_key,
                                                            "user_id": user_id})

        if not selected_word:
            print(f"Word ID '{word_key}' not found in user's word list.")
            return False

        time_now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        selected_word["last_visited_times"].append(time_now)
        selected_word["last_scores"].append(score)

        # Limit the history size
        if len(selected_word["last_visited_times"]) > MAX_HISTORY_LENGTH:
            selected_word["last_visited_times"].pop(0)
            selected_word["last_scores"].pop(0)

        self.user_words_collection.update_one(
            {"_id": word_key,
             "user_id": user_id},
            {"$set": {
                "last_visited_times": selected_word["last_visited_times"],
                "last_scores": selected_word["last_scores"]
            }}
        )
        print(f"Updated word ID '{word_key}' for user {user_id}.")

        return True
    
    def get_exercise(self,
                        word_keys,
                        exercise_type,
                        current_language,
                        current_level) -> Dict[Any, Any]:
        """
        Get an exercise for the user from the database.
        """

        sorted_word_keys = sorted(word_keys, key=lambda x: x.lower())
        sorted_word_keys_combined = "_".join(sorted_word_keys)

        exercise_key = f"{exercise_type}__{current_language}__{current_level}__{sorted_word_keys_combined}"

        exercise_doc = self.exercises_collection.find_one({"_id": exercise_key})

        if not exercise_doc:
            print(f"Excersize document not found for key '{exercise_key}'.")
            exercise_doc = empty_exercise_doc(exercise_key)

        print(f"Excersize document found for key '{exercise_key}'.")
        exercise_list = exercise_doc.get("exercise_list", None)

        if exercise_list is None or not len(exercise_list):
            print(f"No exercise list found for key '{exercise_key}'.")
            word_values = [self.words_collection.find_one({"_id": word_key}) for word_key in word_keys]
            word_values = [word["word_value"] for word in word_values if word is not None]
            if not len(word_values) == len(word_keys):
                print(f"Not all word keys found in the database for key '{exercise_key}'.")
                return None
            
            exercise_list = []
            exercise = self.llm.create_exercise(word_values,
                                                word_keys,
                                                exercise_type,
                                                current_language,
                                                current_level)
            exercise_list.append(exercise)
            self.exercises_collection.update_one(
                {"_id": exercise_key},
                {"$set": {
                    "exercise_list": exercise_list
                }},
                upsert=True
            )
            print(f"Created new exercise for key '{exercise_key}': {exercise}.")
        else:
            exercise = np.random.choice(exercise_list)
            print(f"Excersize found for key '{exercise_key}': {exercise}.")

        return exercise
        
    def get_new_exercise(self,
                          user_id) -> Tuple[Optional[Dict[Any, Any]], bool]:
        
        """
        Get a new exercise for the user from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None, False
        
        current_language = user.get("current_language", None)
        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return None, False
        
        current_level = user.get("languages", {}).get(current_language, {}).get("current_level", None)
        if current_level is None:
            print(f"No current level found for user {user_id}.")
            return None, False
        
        number_of_words_needed = 2

        if np.random.rand() < 0.5:
            number_of_words_needed -= 1

        if number_of_words_needed == 1:
            exercise_index = np.random.choice(ONE_BLANK_EXERCISE_PROMPTS)
            exercise_type = f"1_{exercise_index}"
        elif number_of_words_needed == 2:
            exercise_index = np.random.choice(TWO_BLANK_EXERCISE_PROMPTS)
            exercise_type = f"2_{exercise_index}"
        else:
            print(f"Invalid number of words needed: {number_of_words_needed}.")
            return None, False
        
        word_keys = []

        for _ in range(number_of_words_needed):

            (word_key, 
            success) = self.get_next_word(user_id)
            
            if not success:
                print(f"Failed to get next word for user {user_id}.")
                return None, False
            
            word_keys.append(word_key)
            
        exercise = self.get_exercise(word_keys, 
                                       exercise_type,
                                       current_language,
                                       current_level)

        print(f"Generated new exercise for user {user_id}: {exercise}.")

        return exercise, True
        
    def add_word_to_locked_words(self, 
                                 user_id, 
                                 word_key,
                                 current_language) -> bool:
        """
        Add a word to the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        # check if exists in user words already

        current_user_word = self.user_words_collection.find_one({"_id": word_key,
                                                            "user_id": user_id})
        if current_user_word:
            print(f"Word ID '{word_key}' already exists in user {user_id}'s word list.")
            return False

        word_entry = empty_word_entry(word_key,
                                      user_id,
                                      current_language)

        self.user_words_collection.update_one(
            {"_id": word_key,
             "user_id": user_id},
            {"$set": word_entry},
            upsert=True
        )
        
        print(f"Word ID '{word_key}' added to user {user_id}'s word list.")

    def get_next_word(self, user_id) -> Tuple[Optional[str], bool]:
        """
        Get the next word for the user from the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return None, False
        
        current_language = user.get("current_language", None)
        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return None, False
        
        # Get the words list from the user document
        # words = user.get("words", [])
        words = user.get("languages", {}).get(current_language, {}).get("words", None)
        if words is None:
            print(f"No words found for user {user_id}.")
            return None, False
        
        if not len(words):
            print(f"No words found for user {user_id}.")
            return None, False
        
        # calculate the next word based on the last visited times and scores

        next_word_key = next_word(word_keys=[word["_id"] for word in words],
                                  word_scores=[word["last_scores"] for word in words],
                                  word_last_visited_times=[word["last_visited_times"] for word in words])

        if next_word_key is None:
            print(f"No next word found for user {user_id}.")
            return None, False
        
        return next_word_key, True