
from typing import Optional, Tuple, Dict, Any, List
import threading
import time
import datetime

import uuid

import numpy as np

from pymongo import ASCENDING as PY_MONGO_ASCENDING

from ..util.constants import (NUMBER_OF_ATTEMPTS_TO_CREATE_EXERCISE,
                              SUPPORTED_LANGUAGES,
                              NEXT_WORD_TEMPERATURE, 
                              MAX_HISTORY_LENGTH,
                              MAX_NUMBER_OF_EXERCISES,
                              MIN_THUMB_VOLUME,
                              MAX_WORD_LENGTH,
                              VOCABULARY_REVISION_ITERATIONS,
                              VOCABULARY_REVISION_INTERVAL,
                              MAX_CONCURRENT_EXERCISE_CREATIONS,
                              DELETE_SERVER_TIMEOUT,
                              ALLOW_MAIN_SERVER_TIMEOUT,
                              BACKGROUND_THREAD_SLEEP_TIME,
                              TIMEOUT_TO_CREATE_NEW_EXERCISE,
                              POSSIBLE_CRITERIA)

def next_word(word_ids, 
              word_scores, 
              word_last_visited_times,
              temperature=NEXT_WORD_TEMPERATURE) -> str:
    
    """
    Select the next word to show to the user based on their last visited times and scores.
    """

    assert len(word_ids) == len(word_scores) == len(word_last_visited_times), "All lists must be of the same length."
    assert len(word_ids) > 0, "No words available to select from."

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
        return np.random.choice(word_ids)

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
        print(f"Best word before noise: {word_ids[best_word_index_before_noise]}")
        print(f"Best word after noise: {word_ids[best_word_index_after_noise]}")
        print(f"Temperature: {temperature}, number of words: {len(word_ids)}")

    return word_ids[best_word_index_after_noise]
    
def empty_user(user_id) -> Dict[Any, Any]:
    """
    Create an empty user document for the database.
    """

    user_entry = {
        "_id": user_id, 
        "xp": 0,
        # "ui_language": ui_language,# set after user insert
        # "current_learning_language": learning_language,# set after user insert
        "subscription_status": False,
        "last_time_checked_subscription": 0,
        "last_created_exercise_id": "",
        "last_created_exercise_time": 0,
        "learning_languages": {}
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

def empty_user_word_entry(word_id,
                            user_id,
                            word_value,
                            language) -> Dict[Any, Any]:

    """
    Create an empty word entry for the database.
    """
    word_entry = {
        "word_id": word_id,
        "user_id": user_id,
        "word_value": word_value,
        "language": language,
        "last_visited_times": [],
        "last_scores": [],
        "is_locked": True
    }

    return word_entry

def empty_word_document(word_id,
                        word_value,
                        language,
                        level) -> Dict[Any, Any]:

    """
    Create an empty word document for the database.
    """
    return {
        "_id": word_id,
        "word_value": word_value,
        "language": language,
        "level": level,
        "translations": [],
    }

class GlobalContainer:
    __slots__ = [
        "server_id",
        "is_main_server",
        "startup_time",

        "db_client", 
        "db",

        'servers_collection',
        "settings_collection",
        "words_collection",
        "user_words_collection",
        "user_thumbs_collection",
        "users_collection",
        "exercises_id_lists_collection",
        "exercises_collection",
        "exercise_thumbs_up_collection",
        "exercise_thumbs_down_collection",

        "llm",
        "possible_criteria",
        
        "last_time_revised_vocabulary",

        "vocabulary_background_thread",
        "clean_up_background_thread",
        "update_server_heartbeat_thread",
        "create_exercise_threads",
        
        "is_running",
    ]
    def __init__(self, 
                 db_client,
                 llm) -> None:
        
        print("Initializing GlobalContainer...")
        self.server_id = str(uuid.uuid4())
        print(f"Server ID: {self.server_id}")

        self.is_main_server = False
        self.startup_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        self.db_client = db_client
        self.db = db_client["language_app"]
        self.servers_collection = self.db["servers"]
        self.settings_collection = self.db["settings"]
        self.words_collection = self.db["words"]
        self.user_words_collection = self.db["user_words"]
        self.user_thumbs_collection = self.db["user_thumbs"]
        self.users_collection = self.db["users"]
        self.exercises_id_lists_collection = self.db["exercise_id_lists"]
        self.exercises_collection = self.db["exercises"]
        self.exercise_thumbs_up_collection = self.db["exercise_thumbs_up"]
        self.exercise_thumbs_down_collection = self.db["exercise_thumbs_down"]

        self.llm = llm
        self.possible_criteria = POSSIBLE_CRITERIA
        self.last_time_revised_vocabulary = {}

        self.vocabulary_background_thread = None
        self.clean_up_background_thread = None
        self.update_server_heartbeat_thread = None
        self.create_exercise_threads = []

        self.is_running = True

        self.create_indexes()

        self.register_server()

        self.start_background_threads()

    def __del__(self) -> None:
        """
        Destructor to clean up the database connection.
        """
        self.is_running = False
        print("Stopping background threads...")
        print("Joining vocabulary background thread...")
        self.vocabulary_background_thread.join()
        print("Joining clean up background thread...")
        self.clean_up_background_thread.join()
        print("Joining update server heartbeat thread...")
        self.update_server_heartbeat_thread.join()
        print("Threads stopped.")

    def check_if_is_main_server(self) -> bool:
        """
        Check if the server is the main server.
        """
        # get all servers in the database
        servers = self.servers_collection.find({})

        servers = list(servers)

        if not len(servers):
            print("No servers found in the database.")
            return False
        
        # get all servers with time since last heartbeat less than 1 minute old
        current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        original_server_ids = [server["_id"] for server in servers]

        servers = [server for server in servers if current_time - server["last_heartbeat"] < DELETE_SERVER_TIMEOUT]

        server_ids = [server["_id"] for server in servers]

        old_server_ids = [server_id for server_id in original_server_ids if server_id not in server_ids]

        if not len(servers):
            print("No servers found with recent heartbeats.")
            return False
        
        # get all servers with time since startup time more than 1 minute old
        servers = [server for server in servers if current_time - server["startup_time"] > ALLOW_MAIN_SERVER_TIMEOUT]

        if not len(servers):
            print("No servers found with old enough startup times.")
            return False
        
        # get the server with the alpha-numeric id that is the lowest
        server_ids = [server["_id"] for server in servers]

        server_ids = sorted(server_ids)

        main_server_id = server_ids[0]

        if main_server_id == self.server_id:
            print(f"Server {self.server_id} is the main server.")
            
            if len(old_server_ids):
                print(f"Removing old servers from the database: {old_server_ids}.")
                try:
                    self.servers_collection.delete_many({"_id": {"$in": old_server_ids}})
                except Exception as e:
                    print(f"Error removing old servers from the database: {e}")

            return True
        else:
            print(f"Server {self.server_id} is not the main server. Main server is {main_server_id}.")
            return False

    def register_server(self) -> None:
        """
        Register the server in the database.
        """
        first_heartbeat_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        server_entry = {
            "last_heartbeat": first_heartbeat_time,
            "startup_time": self.startup_time,
        }

        self.servers_collection.update_one(
            {"_id": self.server_id},
            {"$set": server_entry},
            upsert=True
        )
        print(f"Server {self.server_id} registered in the database.")

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

        self.update_server_heartbeat_thread = threading.Thread(target=self.update_server_heartbeat_function, daemon=True)
        self.update_server_heartbeat_thread.start()

        print("Server heartbeat background thread started.")

    def set_last_time_checked_subscription(self, user_id, current_time) -> None:
        current_time_unix = int(current_time.timestamp())
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "last_time_checked_subscription": current_time_unix
            }}
        )

    def get_user_subscription(self, user_id) -> bool:
        """
        Get the user's subscription status from the database.
        """

        user = self.users_collection.find_one({"_id": user_id})
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
            {"_id": user_id},
            {"$set": {
                "subscription_status": is_active
            }}
        )

    def get_last_time_checked_subscription(self, user_id) -> int:
        user = self.users_collection.find_one({"_id": user_id})
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
        
        # self.servers_collection.create_index([('_id', PY_MONGO_ASCENDING)], unique=True)
        self.words_collection.create_index([('language', PY_MONGO_ASCENDING), ('level', PY_MONGO_ASCENDING)])
        self.user_words_collection.create_index([('user_id', PY_MONGO_ASCENDING), ('word_id', PY_MONGO_ASCENDING)], unique=True)
        self.user_thumbs_collection.create_index([('user_id', PY_MONGO_ASCENDING), ('exercise_id', PY_MONGO_ASCENDING)], unique=True)
        # self.users_collection.create_index([('_id', PY_MONGO_ASCENDING)], unique=True)
        # self.exercises_id_lists_collection.create_index([('_id', PY_MONGO_ASCENDING)], unique=True)

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
                word_id = str(uuid.uuid4())
                word_value = word_value.replace(" ", "_")
                level = int(level)
                word_doc = empty_word_document(word_id,
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
    
    def get_supported_languages(self) -> list:
        """
        Get the list of supported languages.
        """

        class Language:
            def __init__(self, code, name):
                self.name = name
                self.code = code

        supported_languages = [Language(key, value) for key, value in SUPPORTED_LANGUAGES.items()]

        return supported_languages
    
    def get_ui_language(self,
                          user_id) -> Optional[str]:
        
        """
        Get the user's ui_language from the database.
        """
        
        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        ui_language = user.get("ui_language", None)

        if ui_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported user language '{ui_language}' for user {user_id}.")
            return None
        
        return ui_language


    def get_learning_language(self,
                              user_id) -> Optional[str]:
        
        """
        Get the user's learning_language from the database.
        """

        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        current_learning_language = user.get("current_learning_language", None)

        if current_learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_learning_language}' for user {user_id}.")
            return None
        
        return current_learning_language
    
    def set_ui_language(self,
                          user_id, 
                          ui_language) -> bool:
        
        """
        Set the user's ui_language in the database.
        """

        if ui_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{ui_language}' for user {user_id}.")
            return False
        
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "ui_language": ui_language
            }}
        )
        print(f"User {user_id} UI language set to '{ui_language}'.")

        return True
    
    def set_learning_language(self,
                              user_id, 
                              learning_language) -> bool:
        
        """
        Set the user's learning_language in the database.
        """

        if learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{learning_language}' for user {user_id}.")
            return False
        
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "current_learning_language": learning_language,
                "last_created_exercise_id": "",
                "last_created_exercise_time": 0
            }}
        )
        print(f"User {user_id} learning language set to '{learning_language}'.")

        # check if learning_language is in user["learning_languages"]:
        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        learning_languages = user.get("learning_languages", None)

        if learning_languages is None:
            learning_languages = {}

        if learning_language not in learning_languages:
            learning_languages[learning_language] = {
                "current_level": 0,
            }

        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "learning_languages": learning_languages
            }}
        )

        return True
    
    def create_user_if_needed(self, 
                              user_id) -> bool:
        """
        Create a user in the database
        """
            
        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            new_user = empty_user(user_id)
            self.users_collection.insert_one(new_user)
            print(f"User {user_id} created in the database.")

        return False
    
    def redirect_if_new_user(self, user_id) -> Tuple[bool, str]:
        """
        Redirect the user to the appropriate page based on their status.
        """

        ui_language = self.get_ui_language(user_id)

        if ui_language is not None and not ui_language in SUPPORTED_LANGUAGES:
            print(f"Unsupported user language '{ui_language}' for user {user_id}.")
            ui_language = None

        if ui_language is None:
            return False, 'select_ui_language'
            
        ######################

        learning_language = self.get_learning_language(user_id)

        if learning_language is not None and not learning_language in SUPPORTED_LANGUAGES:
            print(f"Unsupported learning language '{learning_language}' for user {user_id}.")
            learning_language = None
        
        if learning_language is None:
            return False, 'select_learning_language'

        #######################

        return True, None
    
    def vocabulary_background_function_inner(self):
        """
        Inner function to revise vocabulary periodically.
        """
        
        for language in SUPPORTED_LANGUAGES:
            
            if language not in self.last_time_revised_vocabulary:
                self.last_time_revised_vocabulary[language] = 0

            current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

            if current_time - self.last_time_revised_vocabulary[language] > VOCABULARY_REVISION_INTERVAL:  # 24 hours
                            
                self.populate_initial_words(language)

                self.revise_vocabulary(language)
            
                self.last_time_revised_vocabulary[language] = current_time

    def vocabulary_background_function(self) -> None:

        """
        Background thread to revise vocabulary periodically.
        """
    
        while self.is_running:
            
            if self.is_main_server:
                try:
                    self.vocabulary_background_function_inner()
                except Exception as e:
                    print(f"Error in vocabulary background function: {e}")

            time.sleep(BACKGROUND_THREAD_SLEEP_TIME)

    def clean_up_background_function(self) -> None:

        """
        Background thread to clean up the database periodically.
        """

        while self.is_running:

            # ...

            time.sleep(BACKGROUND_THREAD_SLEEP_TIME)
    
    def update_server_heartbeat_function_inner(self):
    
        current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        self.servers_collection.update_one(
            {"_id": self.server_id},
            {"$set": {
                "last_heartbeat": current_time
            }}
        )

        print(f"Server {self.server_id} heartbeat updated in the database.")

        self.is_main_server = self.check_if_is_main_server()

    def update_server_heartbeat_function(self):

        while self.is_running:

            try:
                self.update_server_heartbeat_function_inner()
            except Exception as e:
                print(f"Error in server heartbeat function: {e}")

            time.sleep(BACKGROUND_THREAD_SLEEP_TIME)
    
    def revise_vocabulary(self,
                            language) -> bool:
        
        """
        Revise the vocabulary for the given language.
        """

        if language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{language}' for revising vocabulary.")
            return False
        
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

            word_id = word_doc["_id"]

            self.words_collection.update_one(
                {"_id": word_id},
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

        word_id = str(uuid.uuid4())
        word_doc = empty_word_document(word_id,
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

        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None
        
        print("User object found in the database.")
        
        return user
    
    def get_inspiration_exercises(self,
                                  exercise_key) -> List[Dict[Any, Any]]:
        
        """
        Get up to 3 exercises for inspiration to create a new one
        """

        exercise_id_list_doc = self.exercises_id_lists_collection.find_one({"_id": exercise_key})
        
        if not exercise_id_list_doc:
            print(f"No exercises generated for key: {exercise_key}")
            return []
        
        exercise_id_list = exercise_id_list_doc.get("exercise_id_list", None)

        if exercise_id_list is None or not len(exercise_id_list):
            print(f"Exercise list not found for key '{exercise_key}'.")
            return []
        
        output_exercise_ids = []

        for e_i in range(3):
            random_index = np.random.randint(0, len(exercise_id_list))
            random_exercise_id = exercise_id_list.pop(random_index)
            output_exercise_ids.append(random_exercise_id)
            if not len(exercise_id_list):
                break

        output_exercises = []

        for exercise_id in output_exercise_ids:

            exercise = self.exercises_collection.find_one({"exercise_id": exercise_id})

            if not exercise:
                print(f"Exercise ID '{exercise_id}' not found in the database.")
                continue

            light_exercise = {}
            light_exercise["initial_strings"] = exercise.get("initial_strings")
            light_exercise["middle_strings"] = exercise.get("middle_strings")
            light_exercise["final_strings"] = exercise.get("final_strings")
            light_exercise["criteria"] = exercise.get("criteria")

            output_exercises.append(light_exercise)

        return output_exercises
            
    def get_user_words(self,
                        user_id,
                        language,
                        is_locked) -> Optional[List[Dict[Any, Any]]]:
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
        
        user = self.users_collection.find_one({"_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return -1
        
        current_learning_language = user.get("current_learning_language", None)
        if current_learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_learning_language}' for user {user_id}.")
            return -1

        language_data = user.get("learning_languages", {}).get(current_learning_language, None)
        if language_data is None:
            print(f"No language data found for user {user_id} in language '{current_learning_language}'.")
            return -1
        
        words = self.get_user_words(user_id, 
                                    current_learning_language,
                                    False)

        if words is None:
            print(f"No words found for user {user_id}.")
            words = []

        locked_words = self.get_user_words(user_id, 
                                           current_learning_language,
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
                print(f"User {user_id} is at the max level for language '{current_learning_language}'.")
                return 4
            
            # add next set of words to locked words
            this_level_words = self.get_words_for_level(current_learning_language, 
                                                        current_level)

            if not this_level_words or not len(this_level_words):
                print(f"No words found for level {current_level} in language '{current_learning_language}'.")
                return -1

            this_level_word_ids = [word["_id"] for word in this_level_words]

            word_ids = [word["_id"] for word in words]
            this_level_word_ids_not_in_words = [word for word in this_level_word_ids if word not in word_ids]
            
            if not len(this_level_word_ids_not_in_words):
                print(f"User {user_id} already has all words for level {current_level}.")
                current_level += 1
                # increase level
                self.users_collection.update_one(
                    {"_id": user_id},
                    {"$set": {
                        "learning_languages." + current_learning_language + ".current_level": current_level
                    }}
                )
                print(f"User {user_id} is now at level {current_level}.")
                return 3
            
            random_word_id = np.random.choice(this_level_word_ids_not_in_words)

            (random_word, 
             success) = self.add_word_to_locked_words(user_id,
                                                        random_word_id,
                                                        current_learning_language)
            if not success:
                print(f"Failed to add word '{random_word_id}' to locked words for user {user_id}.")
                return -1
            
            locked_words.append(random_word)
        
        if not len(words):
            unlocked_word = locked_words.pop(0)
            word_id = unlocked_word["word_id"]
            self.user_words_collection.update_one(
                {"word_id": word_id,
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
            word_id = unlocked_word["word_id"]
            self.user_words_collection.update_one(
                {"word_id": word_id,
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
                                  word_id, 
                                  score) -> bool:
        """
        Update the word in the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        current_learning_language = user.get("current_learning_language", None)
        if current_learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_learning_language}' for user {user_id}.")
            return False

        selected_word = self.user_words_collection.find_one({"word_id": word_id,
                                                            "user_id": user_id})

        if not selected_word:
            print(f"Word ID '{word_id}' not found in user's word list.")
            return False

        time_now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

        selected_word["last_visited_times"].append(time_now)
        selected_word["last_scores"].append(score)

        # Limit the history size
        if len(selected_word["last_visited_times"]) > MAX_HISTORY_LENGTH:
            selected_word["last_visited_times"].pop(0)
            selected_word["last_scores"].pop(0)

        self.user_words_collection.update_one(
            {"word_id": word_id,
             "user_id": user_id},
            {"$set": {
                "last_visited_times": selected_word["last_visited_times"],
                "last_scores": selected_word["last_scores"]
            }}
        )
        print(f"Updated word ID '{word_id}' for user {user_id}.")

        return True
    
    def get_exercise_id(self,
                        word_ids,
                        current_learning_language,
                        current_level) -> str:
        """
        Get an exercise id for the user from the database.
        """

        sorted_word_ids = sorted([str(word_id) for word_id in word_ids], key=lambda x: x.lower())
        sorted_word_ids_combined = "_".join(sorted_word_ids)

        number_of_words_needed = len(word_ids)

        exercise_key = f"{number_of_words_needed}__{current_learning_language}__{current_level}__{sorted_word_ids_combined}"

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
            print("Not enough exercises found, creating new one.")
            exercise_id_list = self.add_to_exercise_id_list(exercise_key,
                                                            word_ids,
                                                            current_learning_language,
                                                            current_level)

        else:
            print("Enough exercises found, selecting one.")
            exercise_id_list = self.revise_exercise_id_list(exercise_id_list)

        if not exercise_id_list or not len(exercise_id_list):
            print(f"No exercise id found for key '{exercise_key}'.")
            return None

        exercise_id = np.random.choice(exercise_id_list)
        print(f"Excersize found for key '{exercise_key}': {exercise_id}.")

        return exercise_id
    
    def add_to_exercise_id_list(self,
                                exercise_key,
                                word_ids,
                                current_learning_language,
                                current_level) -> None:
        
        """
        Add a new exercise to the exercise list in the database.
        """
                         
        print(f"Needs to create new exercise for key '{exercise_key}'.")

        word_values = [self.words_collection.find_one({"_id": word_id}) for word_id in word_ids]
        word_values = [word["word_value"] for word in word_values if word is not None]
        if not len(word_values) == len(word_ids):
            print(f"Not all word keys found in the database for key '{exercise_key}' (word_values: {word_values}, word_ids: {word_ids}).")
            return None
                
        inspiration_exercises = self.get_inspiration_exercises(exercise_key)
        
        exercise = None
        exercise_id_list = []
        num_tries = 0
        while num_tries < NUMBER_OF_ATTEMPTS_TO_CREATE_EXERCISE:
            num_tries += 1
            try:
                exercise = self.llm.create_exercise(word_values,
                                                    current_learning_language,
                                                    current_level,
                                                    inspiration_exercises)
                if exercise is not None:
                    break
                else:
                    print(f"Failed to create exercise for key '{exercise_key}' on attempt {num_tries}. Retrying...")
            except Exception as e:
                print(f"Error creating exercise for key '{exercise_key}': {e}. Retrying... (Probably OpenAI API rate limit exceeded)")
                time.sleep(10)
        
        if exercise is None:
            print(f"Failed to create exercise for key '{exercise_key}'.")
            return None
        
        exercise_id = str(uuid.uuid4())
        
        exercise["word_ids"] = word_ids
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
                      answer) -> Tuple[bool, str, bool]:
        
        """
        Submit the answer to the exercise in the database.
        """

        if not exercise_id or not answer:
            return False, "Missing exercise_id or answer.", False
        
        # get current user exercise
        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return False, "User not found in the database.", False
        
        last_created_exercise_id = user.get("last_created_exercise_id", "")

        if not last_created_exercise_id == exercise_id:
            print(f"Exercise ID '{exercise_id}' does not match user's last created exercise ID '{last_created_exercise_id}'.")
            return False, "Exercise ID does not match user's last created exercise ID.", False
        
        # Validate the exercise_id and answer
        if not answer.isdigit():
            return False, "Answer must be a digit.", False

        answer = int(answer)

        if not answer >= 0 and answer <= 5:
            return False, "Answer must be between 0 and 5.", False

        if not isinstance(exercise_id, str):
            return False, "exercise_id must be a string.", False
        
        # check if exercise_id is a valid UUID
        try:
            uuid.UUID(exercise_id, version=4)
        except ValueError:
            return False, "exercise_id is not a valid UUID.", False
        
        ##########################################################################

        exercise = self.exercises_collection.find_one({"exercise_id": exercise_id})

        if not exercise:
            print(f"Exercise ID '{exercise_id}' not found in the database.")
            return False, "Exercise ID not found in the database.", False
        
        exercise_criteria = exercise.get("criteria", None)

        if exercise_criteria is None:
            print(f"Exercise ID '{exercise_id}' has no criteria.")
            return False, "Exercise ID has no criteria.", False
        
        word_ids = exercise.get("word_ids", None)

        if word_ids is None:
            print(f"Exercise ID '{exercise_id}' has no word keys.")
            return False, "Exercise ID has no word keys.", False
        
        was_correct = True

        if exercise_criteria != answer:
            print(f"Exercise ID '{exercise_id}' has wrong answer: {exercise_criteria} != {answer}.")
            was_correct = False
        
        self.update_user_word_score(user_id,
                                    word_ids,
                                    was_correct)
        
        if was_correct:
            self.increase_user_xp(user_id, 1)

        if was_correct:
            message = "Correct answer."
        else:
            exercise_criteria_str = self.possible_criteria[exercise_criteria]
            message = f"Wrong answer. The correct answer was {exercise_criteria_str}."

        return True, message, was_correct

    def increase_user_xp(self,
                            user_id,
                            xp) -> bool:
        
        """
        Increase the user's XP in the database.
        """

        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        user_xp = user.get("xp", 0)
        
        if user_xp is None:
            print(f"User {user_id} has no XP.")
            user_xp = 0

        user_xp += xp

        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "xp": user_xp
            }}
        )
        print(f"User {user_id} XP increased by {xp}. New XP: {user_xp}.")

        return True
        
    def update_user_word_score(self,
                                user_id,
                                word_ids,
                                was_correct) -> bool:
        
        """
        Update the user's word score in the database.
        """

        for word_id in word_ids:

            user_word = self.user_words_collection.find_one({"word_id": word_id,
                                                             "user_id": user_id})
            
            if not user_word:
                print(f"Word ID '{word_id}' not found in user's word list.")
                continue
            
            last_scores = user_word.get("last_scores", None)

            if last_scores is None:
                print(f"Word ID '{word_id}' has no last scores.")
                last_scores = []

            last_visited_times = user_word.get("last_visited_times", None)

            if last_visited_times is None:
                print(f"Word ID '{word_id}' has no last visited times.")
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
                {"word_id": word_id,
                 "user_id": user_id},
                {"$set": {
                    "last_scores": last_scores,
                    "last_visited_times": last_visited_times
                }}
            )
            print(f"Updated word ID '{word_id}' for user {user_id}.")

    def get_created_exercise(self,
                             user_id) -> Tuple[Optional[Dict[Any, Any]], bool]:
        
        """
        Get the created exercise for the user from the database.
        """

        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None, False
        
        last_created_exercise_id = user.get("last_created_exercise_id", "")

        if not last_created_exercise_id:
            print(f"User {user_id} has no last created exercise ID.")
            return None, False
        
        if last_created_exercise_id == "PROCESSING":
            print(f"User {user_id} is currently creating a new exercise.")
            return None, True# also return True to indicate that the user is currently creating a new exercise

        exercise = self.exercises_collection.find_one({"exercise_id": last_created_exercise_id})

        if not exercise:
            print(f"Exercise ID '{last_created_exercise_id}' not found in the database.")
            return None, False
        
        return exercise, True
    
    def create_new_exercise(self,
                            user_id) -> bool:
        
        """
        Get a new exercise for the user from the database.
        """

        user = self.users_collection.find_one({"_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        last_created_exercise_id = user.get("last_created_exercise_id", "")

        if last_created_exercise_id == "PROCESSING":
            
            last_created_exercise_time = user.get("last_created_exercise_time", 0)

            current_time = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            if current_time - last_created_exercise_time < TIMEOUT_TO_CREATE_NEW_EXERCISE:  # 1 minute
                print(f"User {user_id} is already creating a new exercise.")
                return False
        
        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "last_created_exercise_id": "PROCESSING",
                "last_created_exercise_time": int(datetime.datetime.now(datetime.timezone.utc).timestamp())
            }}
        )

        ##################

        while len(self.create_exercise_threads) > MAX_CONCURRENT_EXERCISE_CREATIONS:
            # wait for a thread to finish
            time.sleep(1)
            print(f"Waiting for a thread to finish. Current threads: {len(self.create_exercise_threads)}.")
            for thread in self.create_exercise_threads:
                if not thread.is_alive():
                    self.create_exercise_threads.remove(thread)

        print(f"creating new exercise for {user_id}")
        create_exercise_thread = threading.Thread(target=self.create_new_exercise_inner,
                                                    args=(user_id, user),
                                                    daemon=True)
        create_exercise_thread.start()
        self.create_exercise_threads.append(create_exercise_thread)

        return True

    def create_new_exercise_inner(self, 
                                  user_id,
                                  user) -> bool:
        
        """
        Create a new exercise for the user.
        """

        current_learning_language = user.get("current_learning_language", None)
        if current_learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_learning_language}' for user {user_id}.")
            return False
        
        current_level = user.get("learning_languages", {}).get(current_learning_language, {}).get("current_level", None)
        if current_level is None:
            print(f"No current level found for user {user_id}.")
            return False
        
        number_of_words_needed = 2
        if np.random.rand() < 0.5:
            number_of_words_needed = 1

        print(f"searching for {number_of_words_needed} words for a new exercise for {user_id}")

        word_ids = []

        for _ in range(number_of_words_needed):

            (word_id, 
             success) = self.get_next_word(user_id)
            
            if not success:
                print(f"Failed to get next word for user {user_id}.")
                continue
            
            word_ids.append(word_id)

        if not len(word_ids):
            print(f"No word IDs found for user {user_id}.")
            return False
        
        exercise_id = self.get_exercise_id(word_ids, 
                                            current_learning_language,
                                            current_level)
        
        if not exercise_id:
            print(f"Failed to get exercise ID for user {user_id}.")
            return False
        
        print(f"Generated new exercise for user {user_id}: {exercise_id}.")

        self.users_collection.update_one(
            {"_id": user_id},
            {"$set": {
                "last_created_exercise_id": exercise_id
            }}
        )
        print(f"User {user_id}'s last created exercise ID set to '{exercise_id}'.")

        return True
    
    def apply_thumbs_up_or_down(self,
                                 user_id,
                                 exercise_id,
                                 thumbs_up) -> bool:
        
        """
        Apply thumbs up or down to the exercise in the database.
        """

        # validate exercise_id
        if not exercise_id or not isinstance(exercise_id, str):
            print(f"Invalid exercise_id '{exercise_id}' for user {user_id}.")
            return False
        
        try:
            uuid.UUID(exercise_id, version=4)
        except ValueError:
            print(f"Exercise ID '{exercise_id}' is not a valid UUID for user {user_id}.")
            return False
        
        # check if user already has thumbs up or down for this exercise
        user_exercise_thumbs_up_or_down = self.user_thumbs_collection.find_one({
            "user_id": user_id,
            "exercise_id": exercise_id
        })

        if user_exercise_thumbs_up_or_down:
            print(f"User {user_id} already has thumbs up or down for exercise ID '{exercise_id}'.")
            return False
        
        # validate thumbs_up
        if not isinstance(thumbs_up, bool):
            print(f"Invalid thumbs_up value '{thumbs_up}' for user {user_id}.")
            return False

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

        # add to user exercise thumbs up or down collection
        self.user_thumbs_collection.insert_one({
            "user_id": user_id,
            "exercise_id": exercise_id,
            "thumbs_up": thumbs_up
        })

        print(f"Applied thumbs {'up' if thumbs_up else 'down'} to exercise {exercise_id} for user {user_id}.")

        return True

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
                                 word_id,
                                 current_learning_language) -> bool:
        """
        Add a word to the user's word list in the database.
        """
        
        current_user_word = self.user_words_collection.find_one({"word_id": word_id,
                                                                 "user_id": user_id})
        if current_user_word:
            print(f"Word ID '{word_id}' already exists in user {user_id}'s word list.")
            return None, False
        
        word_doc = self.words_collection.find_one({"_id": word_id})

        if not word_doc:
            print(f"Word ID '{word_id}' not found in the words collection.")
            return None, False
        
        word_value = word_doc.get("word_value", None)

        if not word_value:
            print(f"Word ID '{word_id}' has no word value.")
            return None, False

        user_word_entry = empty_user_word_entry(word_id,
                                                user_id,
                                                word_value,
                                                current_learning_language)

        self.user_words_collection.update_one(
            {"word_id": word_id,
             "user_id": user_id},
            {"$set": user_word_entry},
            upsert=True
        )
        
        print(f"Word ID '{word_id}' added to user {user_id}'s word list.")

        return user_word_entry, True

    def get_next_word(self, user_id) -> Tuple[Optional[str], bool]:
        """
        Get the next word for the user from the database.
        """
        
        user = self.users_collection.find_one({"_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return None, False
        
        current_learning_language = user.get("current_learning_language", None)
        if current_learning_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_learning_language}' for user {user_id}.")
            return None, False
        
        unlock_word_response = self.check_if_should_unlock_new_word(user_id)

        print(f"Unlock word response: {unlock_word_response}.")
        
        user_words = self.get_user_words(user_id,
                                         current_learning_language,
                                         False)
        
        if user_words is None:
            print(f"No user_words found for user {user_id}.")
            return None, False
        
        if not len(user_words):
            print(f"No user_words found for user {user_id}.")
            return None, False
        
        # calculate the next word based on the last visited times and scores

        next_word_id = next_word(word_ids=[word["word_id"] for word in user_words],
                                  word_scores=[word["last_scores"] for word in user_words],
                                  word_last_visited_times=[word["last_visited_times"] for word in user_words])

        if next_word_id is None:
            print(f"No next word found for user {user_id}.")
            return None, False
        
        return next_word_id, True