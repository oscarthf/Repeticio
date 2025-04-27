
from typing import Optional, Tuple, Dict, Any
import threading
import time
import datetime

import uuid

import numpy as np

from pymongo import ASCENDING as PY_MONGO_ASCENDING

from ..util.prompts.one_blank import prompts as ONE_BLANK_EXERCISE_PROMPTS
from ..util.prompts.two_blank import prompts as TWO_BLANK_EXERCISE_PROMPTS
from ..util.constants import (SUPPORTED_LANGUAGES,
                              REAL_LANGUAGE_NAMES,
                              NEXT_WORD_TEMPERATURE, 
                              MAX_HISTORY_LENGTH,
                              MAX_NUMBER_OF_EXERCISES,
                              MIN_THUMB_VOLUME,
                              MAX_WORD_LENGTH,
                              VOCABULARY_REVISION_ITERATIONS,
                              VOCABULARY_REVISION_INTERVAL)

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
    print(f"word_last_visited_times: {word_last_visited_times}")
    print(f"word_scores: {word_scores}")

    word_last_visited_times = [datetime.datetime.fromtimestamp(times[-1], tz=datetime.timezone.utc) if len(times) > 0 else datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
                               for times in word_last_visited_times ]
    current_time = datetime.datetime.now(datetime.timezone.utc)

    oldest_time = min(word_last_visited_times) if len(word_last_visited_times) else current_time
    time_since_oldest_visit = (current_time - oldest_time).total_seconds() / 3600  # in hours

    if time_since_oldest_visit <= 0:
        print("No words have been visited yet, returning random word.")
        return np.random.choice(word_keys)

    word_last_visited_times = [(current_time - time).total_seconds() for time in word_last_visited_times]

    word_last_visited_times = np.array(word_last_visited_times) / 3600
    word_last_visited_times = word_last_visited_times / time_since_oldest_visit

    word_scores = [scores[-1] if len(scores) > 0 else 0 for scores in word_scores]

    scores = np.array(word_scores)
    # average along 1st axis

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
        "subscription_status": False,
        "last_time_checked_subscription": 0,
        "languages": {
            language: {
                "current_level": 0,
            }
        }
    }

    return user_entry

def empty_exercise_id_list_doc(exercise_key) -> Dict[Any, Any]:
    """
    Create an empty exercise document for the database.
    """
    return {
        "_id": exercise_key,
        "exercise_id_list": [],
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
        "exercises_id_lists_collection",
        "exercises_collection",
        "exercise_thumbs_up_collection",
        "exercise_thumbs_down_collection",
        "llm",
        "last_time_revised_vocabulary",
        "vocabulary_background_thread",
        "clean_up_background_thread",
        "is_running",
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
        self.exercises_id_lists_collection = self.db["exercise_id_lists"]
        self.exercises_collection = self.db["exercises"]
        self.exercise_thumbs_up_collection = self.db["exercise_thumbs_up"]
        self.exercise_thumbs_down_collection = self.db["exercise_thumbs_down"]

        self.llm = llm
        self.last_time_revised_vocabulary = {}

        self.vocabulary_background_thread = None
        self.clean_up_background_thread = None

        # Create indexes on commonly queried fields
        self.create_indexes()
        self.start_background_threads()

        self.is_running = True

    def __del__(self) -> None:
        """
        Destructor to clean up the database connection.
        """
        self.is_running = False
        self.vocabulary_background_thread.join()
        self.clean_up_background_thread.join()
        
    def start_background_threads(self) -> None:
        """
        Start the background thread to revise vocabulary periodically.
        """
        self.vocabulary_background_thread = threading.Thread(target=self.vocabulary_background_function, daemon=True)
        self.vocabulary_background_thread.start()

        print("Vocabulary background thread started.")

        self.clean_up_background_thread = threading.Thread(target=self.clean_up_background_function, daemon=True)
        self.clean_up_background_thread.start()

        print("Clean up background thread started.")

    def set_last_time_checked_subscription(self, user_id, current_time) -> None:
        current_time_unix = int(current_time.timestamp())
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "last_time_checked_subscription": current_time_unix
            }}
        )

    def get_user_subscription(self, user_id) -> bool:
        """
        Get the user's subscription status from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})
        if not user:
            print(f"User {user_id} not found in the database.")
            return False

        subscription_status = user.get("subscription_status", False)
        
        if not isinstance(subscription_status, bool):
            print(f"Invalid subscription status for user {user_id}.")
            return False
        
        return subscription_status

    def set_user_subscription(self, user_id, is_active) -> None:
        """
        Set the user's subscription status in the database.
        """

        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "subscription_status": is_active
            }}
        )

    def get_last_time_checked_subscription(self, user_id) -> int:
        user = self.users_collection.find_one({"user_id": user_id})
        if not user:
            print(f"User {user_id} not found in the database.")
            return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)

        last_time_checked_subscription_unix = user.get("last_time_checked_subscription", 0)
        
        if not isinstance(last_time_checked_subscription_unix, int):
            print(f"Invalid last time checked subscription value for user {user_id}.")
            return datetime.datetime.fromtimestamp(0, tz=datetime.timezone.utc)
        
        last_time_checked_subscription = datetime.datetime.fromtimestamp(last_time_checked_subscription_unix, tz=datetime.timezone.utc)

        return last_time_checked_subscription

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
        self.exercises_id_lists_collection.create_index([('_id', PY_MONGO_ASCENDING)])

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
                level = int(level)
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
        words = list(words)

        return words
    
    def get_languages(self) -> list:
        """
        Get the list of supported languages.
        """

        class Language:
            def __init__(self, code, name):
                self.name = name
                self.code = code

        languages = [Language(key, value) for key, value in REAL_LANGUAGE_NAMES.items() if key in SUPPORTED_LANGUAGES]

        return languages
    
    def get_user_language(self,
                            user_id) -> Optional[str]:
        
        """
        Get the user's languages from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        current_language = user.get("current_language", None)

        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return None
        
        return current_language
    
    def create_user_if_needed(self, 
                              user_id,
                              language) -> bool:
        """
        Create a user in the database
        """

        if not language in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for user {user_id}.")
            return False
        
        user = self.users_collection.find_one({"user_id": user_id})

        if user:
            print(f"User {user_id} already exists in the database.")
            return True

        new_user = empty_user(user_id, 
                              language)

        self.users_collection.insert_one(new_user)
        
        print(f"User {user_id} created in the database.")

        return True
    
    def vocabulary_background_function_inner(self):
        """
        Inner function to revise vocabulary periodically.
        """
        
        for language in SUPPORTED_LANGUAGES:
            if language not in self.last_time_revised_vocabulary:
                self.last_time_revised_vocabulary[language] = 0

            current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

            if current_time - self.last_time_revised_vocabulary[language] > VOCABULARY_REVISION_INTERVAL:  # 24 hours
                self.revise_vocabulary(language)
                self.last_time_revised_vocabulary[language] = current_time

    def vocabulary_background_function(self) -> None:

        """
        Background thread to revise vocabulary periodically.
        """
    
        while self.is_running:
            
            try:
                self.vocabulary_background_function_inner()
            except Exception as e:
                print(f"Error in vocabulary background function: {e}")

            time.sleep(60 * 60)  # Run every hour

    def clean_up_background_function(self) -> None:

        """
        Background thread to clean up the database periodically.
        """

        while self.is_running:

            # ...

            time.sleep(60 * 60)  # Run every hour
            
    
    def revise_vocabulary(self,
                            language) -> bool:
        
        """
        Revise the vocabulary for the given language.
        """

        if language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for revising vocabulary.")
            return False
        
        self.populate_initial_words(language)

        vocabulary = self.words_collection.find({"language": language})

        vocabulary = list(vocabulary)

        if not len(vocabulary):
            print(f"No vocabulary found for language '{language}'.")
            return False
        
        ########################################################################

        shuffled_word_indices = np.random.permutation(len(vocabulary))

        selected_word_indices = shuffled_word_indices[:VOCABULARY_REVISION_ITERATIONS]

        for word_i in selected_word_indices:
            word_doc = vocabulary[word_i]

            word_value = word_doc["word_value"]

            revised_level = self.llm.get_word_level(word_value,
                                                    language)

            if revised_level is None:
                print(f"Failed to get word level for word '{word_value}' in language '{language}'.")
                continue

            previous_level = word_doc["level"]

            if revised_level == previous_level:
                print(f"Word '{word_value}' already at level {revised_level} in language '{language}'.")
                continue

            vocabulary[word_i]["level"] = revised_level

            word_key = word_doc["_id"]

            self.words_collection.update_one(
                {"_id": word_key},
                {"$set": {
                    "level": revised_level
                }}
            )

            print(f"Revised word '{word_value}' to level {revised_level} in language '{language}'.")

        vocabulary_word_values = [word["word_value"] for word in vocabulary]

        new_word_value = self.llm.get_new_word(language, vocabulary_word_values)

        if new_word_value is None:
            print(f"Failed to get new word for language '{language}'.")
            return False
        
        if not isinstance(new_word_value, str):
            print(f"New word value is not a string: {new_word_value}.")
            return False
        
        if new_word_value == "":
            print(f"New word value is empty.")
            return False
        
        if " " in new_word_value:
            print(f"New word value '{new_word_value}' contains spaces.")
            return False
        
        if len(new_word_value) > MAX_WORD_LENGTH:
            print(f"New word value '{new_word_value}' is too long.")
            return False
        
        if new_word_value in [word["word_value"] for word in vocabulary]:
            print(f"New word value '{new_word_value}' already exists in the vocabulary.")
            return False
        
        # create a new word document

        level = self.llm.get_word_level(new_word_value,
                                        language)
        
        if level is None:
            print(f"Failed to get word level for new word '{new_word_value}' in language '{language}'.")
            return False

        word_key = str(uuid.uuid4())
        word_doc = empty_word_document(word_key,
                                        new_word_value,
                                        language,
                                        level)
        
        self.words_collection.insert_one(word_doc)

        print(f"New word '{new_word_value}' added to the vocabulary in language '{language}'.")
        
        return True

    def get_user_object(self,
                        user_id) -> Optional[Dict[Any, Any]]:
        """
        Get the user object from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        return user
    
    def get_user_words(self,
                        user_id,
                        language,
                        is_locked) -> Optional[list]:
        """
        Get the user's words from the database.
        """

        if not language in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for user {user_id}.")
            return None
        
        if not isinstance(is_locked, bool):
            print(f"Invalid is_locked value '{is_locked}' for user {user_id}.")
            return None

        # Get the words list from the user words collection
        user_words = self.user_words_collection.find({"user_id": user_id, 
                                                      "language": language,
                                                      "is_locked": is_locked})
        
        user_words = list(user_words)
        
        if not len(user_words):
            print(f"No words found for user {user_id}.")
            return None
        
        return user_words
        
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
            words = []

        locked_words = self.get_user_words(user_id, 
                                           current_language,
                                           True)

        if locked_words is None:
            print(f"No locked words found for user {user_id}.")
            locked_words = []

        if not len(locked_words):

            print(f"No locked words found for user {user_id}.")
            # check if the user is at the max level
            current_level = language_data.get("current_level", 0)
            supported_levels = [0, 1, 2]
            if current_level >= len(supported_levels) - 1:
                print(f"User {user_id} is at the max level for language '{current_language}'.")
                return 4
            
            # add next set of words to locked words
            this_level_words = self.get_words_for_level(current_language, 
                                                        current_level)

            if not this_level_words or not len(this_level_words):
                print(f"No words found for level {current_level} in language '{current_language}'.")
                return -1

            this_level_word_keys = [word["_id"] for word in this_level_words]

            word_keys = [word["_id"] for word in words]
            this_level_word_keys_not_in_words = [word for word in this_level_word_keys if word not in word_keys]
            
            if not len(this_level_word_keys_not_in_words):
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
            
            random_word_key = np.random.choice(this_level_word_keys_not_in_words)

            (random_word, 
             success) = self.add_word_to_locked_words(user_id,
                                                        random_word_key,
                                                        current_language)
            if not success:
                print(f"Failed to add word '{random_word_key}' to locked words for user {user_id}.")
                return -1
            
            locked_words.append(random_word)
        
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
            last_scores = word.get("last_scores", [])
            if not len(last_scores):
                print(f"Word ID '{word['_id']}' has no last scores.")
                continue
            average_score = sum(last_scores) / len(last_scores)
            if average_score < 0.5:
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
    
    def get_exercise_id(self,
                        word_keys,
                        exercise_type,
                        current_language,
                        current_level) -> str:
        """
        Get an exercise id for the user from the database.
        """

        sorted_word_keys = sorted(word_keys, key=lambda x: x.lower())
        sorted_word_keys_combined = "_".join(sorted_word_keys)

        exercise_key = f"{exercise_type}__{current_language}__{current_level}__{sorted_word_keys_combined}"

        exercise_id_list_doc = self.exercises_id_lists_collection.find_one({"_id": exercise_key})

        if not exercise_id_list_doc:
            print(f"Excersize document not found for key '{exercise_key}'.")
            exercise_id_list_doc = empty_exercise_id_list_doc(exercise_key)

        print(f"Excersize document found for key '{exercise_key}'.")
        exercise_id_list = exercise_id_list_doc.get("exercise_id_list", None)

        if exercise_id_list is None:
            print(f"Exercise list not found for key '{exercise_key}'.")
            exercise_id_list = []

        if len(exercise_id_list) < MAX_NUMBER_OF_EXERCISES:
            
            exercise_id_list = self.add_to_exercise_id_list(exercise_key,
                                                            word_keys,
                                                            exercise_type,
                                                            current_language,
                                                            current_level)

        else:

            exercise_id_list = self.revise_exercise_id_list(exercise_id_list)

        exercise_id = np.random.choice(exercise_id_list)
        print(f"Excersize found for key '{exercise_key}': {exercise_id}.")

        return exercise_id
    
    def add_to_exercise_id_list(self,
                                exercise_key,
                                word_keys,
                                exercise_type,
                                current_language,
                                current_level) -> None:
        
        """
        Add a new exercise to the exercise list in the database.
        """
                         
        print(f"Needs to create new exercise for key '{exercise_key}'.")

        word_values = [self.words_collection.find_one({"_id": word_key}) for word_key in word_keys]
        word_values = [word["word_value"] for word in word_values if word is not None]
        if not len(word_values) == len(word_keys):
            print(f"Not all word keys found in the database for key '{exercise_key}'.")
            return None
        
        exercise_id_list = []
        exercise = self.llm.create_exercise(word_values,
                                            exercise_type,
                                            current_language,
                                            current_level)
        
        if exercise is None:
            print(f"Failed to create exercise for key '{exercise_key}'.")
            return None
        
        exercise_id = str(uuid.uuid4())
        
        exercise["word_keys"] = word_keys
        exercise["exercise_id"] = exercise_id
        exercise["created_at"] = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        exercise_id_list.append(exercise_id)
        self.exercises_id_lists_collection.update_one(
            {"_id": exercise_key},
            {"$set": {
                "exercise_id_list": exercise_id_list
            }},
            upsert=True
        )
        print(f"Created new exercise for key '{exercise_key}': {exercise}.")

        self.exercises_collection.update_one(
            {"exercise_id": exercise["exercise_id"]},
            {"$set": exercise},
            upsert=True
        )

        return exercise_id_list
    
    def revise_exercise_id_list(self,
                                exercise_id_list) -> list:
        
        thumbs_up_values = []
        thumbs_down_values = []
        thumb_volumes = []
        thumb_averages = []
        for exercise_id in exercise_id_list:
            # exercise_id = exercise["exercise_id"]
            thumbs_up = self.get_exercise_thumbs_up_or_down(exercise_id, True)
            thumbs_down = self.get_exercise_thumbs_up_or_down(exercise_id, False)
            thumbs_up_values.append(thumbs_up)
            thumbs_down_values.append(thumbs_down)
            thumb_volume = thumbs_up + thumbs_down
            thumb_volumes.append(thumb_volume)

            if thumb_volume < MIN_THUMB_VOLUME:
                thumb_averages.append(1)
            else:
                thumb_averages.append(thumbs_up / thumb_volume)

        worst_exercise_index = np.argmin(thumb_averages)
        worst_exercise_average = thumb_averages[worst_exercise_index]

        if worst_exercise_average > 0.5:
            print(f"All exercises are good, no need to revise.")
            return exercise_id_list
        
        # remove the worst exercise from the list
        worst_exercise_id = exercise_id_list.pop(worst_exercise_index)
        print(f"Removing worst exercise id: {worst_exercise_id}.")

        if 1:
            # remove from the exercises_by_id collection
            # worst_exercise_id = worst_exercise["exercise_id"]
            self.exercises_collection.delete_one({"exercise_id": worst_exercise_id})
            
        return exercise_id_list
        
    def submit_answer(self,
                      user_id,
                      exercise_id,
                      answer) -> Tuple[bool, str]:
        
        """
        Submit the answer to the exercise in the database.
        """

        if not exercise_id or not answer:
            return False, "Missing exercise_id or answer."
        
        # Validate the exercise_id and answer
        if not answer.isdigit():
            return False, "Answer must be a digit."

        answer = int(answer)

        if not answer >= 0 and answer <= 5:
            return False, "Answer must be between 0 and 5."

        if not isinstance(exercise_id, str):
            return False, "exercise_id must be a string."
        
        # check if exercise_id is a valid UUID
        try:
            uuid.UUID(exercise_id, version=4)
        except ValueError:
            return False, "exercise_id is not a valid UUID."
        
        ##########################################################################

        # check if exercise_id exists in the database
        exercise = self.exercises_collection.find_one({"exercise_id": exercise_id})

        if not exercise:
            print(f"Exercise ID '{exercise_id}' not found in the database.")
            return False, "Exercise ID not found in the database."
        
        exercise_criteria = exercise.get("criteria", None)

        if exercise_criteria is None:
            print(f"Exercise ID '{exercise_id}' has no criteria.")
            return False, "Exercise ID has no criteria."
        
        word_keys = exercise.get("word_keys", None)

        if word_keys is None:
            print(f"Exercise ID '{exercise_id}' has no word keys.")
            return False, "Exercise ID has no word keys."
        
        was_correct = True

        if exercise_criteria != answer:
            print(f"Exercise ID '{exercise_id}' has wrong answer: {exercise_criteria} != {answer}.")
            was_correct = False
        
        self.update_user_word_score(user_id,
                                    word_keys,
                                    was_correct)
        
        if was_correct:
            self.increase_user_xp(user_id, 1)

        if was_correct:
            return True, "Correct answer."
        else:
            return False, "Wrong answer."
        
    def increase_user_xp(self,
                            user_id,
                            xp) -> bool:
        
        """
        Increase the user's XP in the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        user_xp = user.get("xp", 0)
        
        if user_xp is None:
            print(f"User {user_id} has no XP.")
            user_xp = 0

        user_xp += xp

        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "xp": user_xp
            }}
        )
        print(f"User {user_id} XP increased by {xp}. New XP: {user_xp}.")

        return True
        
    def update_user_word_score(self,
                                user_id,
                                word_keys,
                                was_correct) -> bool:
        
        """
        Update the user's word score in the database.
        """

        for word_key in word_keys:

            user_word = self.user_words_collection.find_one({"_id": word_key,
                                                            "user_id": user_id})
            
            if not user_word:
                print(f"Word ID '{word_key}' not found in user's word list.")
                continue
            
            last_scores = user_word.get("last_scores", None)

            if last_scores is None:
                print(f"Word ID '{word_key}' has no last scores.")
                last_scores = []

            last_visited_times = user_word.get("last_visited_times", None)

            if last_visited_times is None:
                print(f"Word ID '{word_key}' has no last visited times.")
                last_visited_times = []

            # append new score and time

            time_now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

            last_scores.append(1 if was_correct else 0)
            last_visited_times.append(time_now)

            # Limit the history size

            if len(last_scores) > MAX_HISTORY_LENGTH:
                last_scores.pop(0)
                last_visited_times.pop(0)

            self.user_words_collection.update_one(
                {"_id": word_key,
                 "user_id": user_id},
                {"$set": {
                    "last_scores": last_scores,
                    "last_visited_times": last_visited_times
                }}
            )
            print(f"Updated word ID '{word_key}' for user {user_id}.")

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
            exercise_index = np.random.randint(0, len(ONE_BLANK_EXERCISE_PROMPTS))
            exercise_type = f"1_{exercise_index}"
        elif number_of_words_needed == 2:
            exercise_index = np.random.randint(0, len(TWO_BLANK_EXERCISE_PROMPTS))
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
            
        exercise_id = self.get_exercise_id(word_keys, 
                                            exercise_type,
                                            current_language,
                                            current_level)
        
        if not exercise_id:
            print(f"Failed to get exercise ID for user {user_id}.")
            return None, False
        
        print(f"Generated new exercise for user {user_id}: {exercise_id}.")

        exercise = self.exercises_collection.find_one({"exercise_id": exercise_id})

        if not exercise:
            print(f"Exercise ID '{exercise_id}' not found in the database.")
            return None, False

        return exercise, True
    
    def apply_thumbs_up_or_down(self,
                                 user_id,
                                 exercise_id,
                                 thumbs_up) -> bool:
        
        """
        Apply thumbs up or down to the exercise in the database.
        """

        if thumbs_up:
            exercise_thumbs_up_or_down = self.exercise_thumbs_up_collection.find_one({"exercise_id": exercise_id})
        else:
            exercise_thumbs_up_or_down = self.exercise_thumbs_down_collection.find_one({"exercise_id": exercise_id})

        if not exercise_thumbs_up_or_down:
            print(f"Exercise thumbs up or down not found for exercise ID '{exercise_id}'.")
            exercise_thumbs_up_or_down = {
                "exercise_id": exercise_id,
                "up_or_down_value": 0
            }

        up_or_down_value = exercise_thumbs_up_or_down.get("up_or_down_value", None)

        if not up_or_down_value:
            up_or_down_value = 0

        up_or_down_value += 1

        if thumbs_up:
            self.exercise_thumbs_up_collection.update_one(
                {"exercise_id": exercise_id},
                {"$set": {
                    "exercise_id": exercise_id,
                    "up_or_down_value": up_or_down_value
                }},
                upsert=True
            )
        else:
            self.exercise_thumbs_down_collection.update_one(
                {"exercise_id": exercise_id},
                {"$set": {
                    "exercise_id": exercise_id,
                    "up_or_down_value": up_or_down_value
                }},
                upsert=True
            )

        print(f"Applied thumbs {'up' if thumbs_up else 'down'} to exercise {exercise_id} for user {user_id}.")

    def get_exercise_thumbs_up_or_down(self,
                                        exercise_id,
                                        thumbs_up) -> int:
        
        """
        Get the thumbs up or down count for the exercise in the database.
        """

        if thumbs_up:
            exercise_thumbs_up_or_down = self.exercise_thumbs_up_collection.find_one({"exercise_id": exercise_id})
        else:
            exercise_thumbs_up_or_down = self.exercise_thumbs_down_collection.find_one({"exercise_id": exercise_id})

        if not exercise_thumbs_up_or_down:
            print(f"Exercise {exercise_id} not found in the database.")
            return 0
        
        up_or_down_value = exercise_thumbs_up_or_down.get("up_or_down_value", None)

        if not up_or_down_value:
            print(f"Exercise {exercise_id} has no thumbs up or down value.")
            return 0
            
        return up_or_down_value
        
    def add_word_to_locked_words(self, 
                                 user_id, 
                                 word_key,
                                 current_language) -> bool:
        """
        Add a word to the user's word list in the database.
        """
        
        current_user_word = self.user_words_collection.find_one({"_id": word_key,
                                                                 "user_id": user_id})
        if current_user_word:
            print(f"Word ID '{word_key}' already exists in user {user_id}'s word list.")
            return None, False

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

        return word_entry, True

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
        
        unlock_word_response = self.check_if_should_unlock_new_word(user_id)

        print(f"Unlock word response: {unlock_word_response}.")
        
        words = self.get_user_words(user_id,
                                    current_language,
                                    False)
        
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