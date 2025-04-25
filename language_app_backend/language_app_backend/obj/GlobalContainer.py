
from typing import Optional, Tuple, Dict, Any
import datetime

import numpy as np

from ..util.constants import (EXCERSIZE_TYPES,
                              NUMBER_OF_WORDS_PER_EXCERSIZE,
                              SUPPORTED_LANGUAGES,
                              INITIAL_WORD_KEYS_FOR_POPULATE,
                              NEXT_WORD_TEMPERATURE, 
                              MAX_HISTORY_LENGTH)

# INITIAL_WORD_KEYS_FOR_POPULATE = {
#     "es": {
#         0: [
#             "ser",
#             ...
#         ],
#         ...
#     },
# }

def next_word(word_keys, 
              word_scores, 
              word_last_visited_times,
              temperature=NEXT_WORD_TEMPERATURE) -> str:
    
    """
    Select the next word to show to the user based on their last visited times and scores.
    """

    assert len(word_keys) == len(word_scores) == len(word_last_visited_times), "All lists must be of the same length."
    assert len(word_keys) > 0, "No words available to select from."

    # adjusted score = (1 - score) * (1 + time_since_last_visit) - 1

    word_last_visited_times = [datetime.datetime.fromisoformat(time) for time in word_last_visited_times]
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
                "words": [],
                "locked_words": [],
            }
        }
    }

    return user_entry

def empty_word_entry(word_key) -> Dict[Any, Any]:

    """
    Create an empty word entry for the database.
    """
    return {
        "_id": word_key,
        "last_visited_times": [],
        "last_scores": [],
    }

def empty_word_document(word_key,
                        language,
                        level) -> Dict[Any, Any]:

    """
    Create an empty word document for the database.
    """
    return {
        "_id": word_key,
        "language": language,
        "level": level,
        "translations": [],
    }

class GlobalContainer:
    __slots__ = [
        "db_client", 
        "db",
        "words_collection",
        "users_collection",
    ]
    def __init__(self, db_client):

        self.db_client = db_client
        self.db = db_client["language_app"]
        self.words_collection = self.db["words"]
        self.users_collection = self.db["users"]

        has_populated_initial_words = self.words_collection.count_documents({}) > 0

        if not has_populated_initial_words:
            self.populate_initial_words()

    def populate_initial_words(self) -> None:

        """
        Populate the database with initial words.
        """
        
        for language, language_data in INITIAL_WORD_KEYS_FOR_POPULATE.items():
            for level, word_keys in language_data.items():
                for word_key in word_keys:
                    word_doc = empty_word_document(word_key,
                                                    language,
                                                    level)
                    self.words_collection.insert_one(word_doc)

        print(f"Inserted {len(INITIAL_WORD_KEYS_FOR_POPULATE)} initial words into the database.")

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

        language_data = user.get("languages", {}).get(current_language, {})
        if not language_data:
            print(f"No language data found for user {user_id} in language '{current_language}'.")
            return -1
        
        words = language_data.get("words", [])
        locked_words = language_data.get("locked_words", [])

        if not len(locked_words):
            print(f"No locked words found for user {user_id}.")
            # check if the user is at the max level
            current_level = language_data.get("current_level", 0)
            supported_levels = INITIAL_WORD_KEYS_FOR_POPULATE[current_language].keys()
            if current_level >= len(supported_levels) - 1:
                print(f"User {user_id} is at the max level for language '{current_language}'.")
                return 4
            
            # add next set of words to locked words
            this_level_words = INITIAL_WORD_KEYS_FOR_POPULATE[current_language][current_level]

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
                                            locked_words,
                                            current_language)
        
        if not len(words):
            unlocked_word = locked_words.pop(0)
            words.append(unlocked_word)
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "languages." + current_language + ".words": words,
                    "languages." + current_language + ".locked_words": locked_words
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
            words.append(unlocked_word)
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "languages." + current_language + ".words": words,
                    "languages." + current_language + ".locked_words": locked_words
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

        time_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        user_words = user.get("languages", {}).get(current_language, {}).get("words", None)
        if user_words is None:
            print(f"No words found for user {user_id}.")
            return False
        
        word_keys = [word["_id"] for word in user_words]

        index_of_word = word_keys.index(word_key) if word_key in word_keys else -1
        
        if index_of_word == -1:
            print(f"Word ID '{word_key}' not found in user's word list.")
            return False
        
        selected_word = user_words[index_of_word]

        selected_word["last_visited_times"].append(time_now)
        selected_word["last_scores"].append(score)

        # Limit the history size
        if len(selected_word["last_visited_times"]) > MAX_HISTORY_LENGTH:
            selected_word["last_visited_times"].pop(0)
            selected_word["last_scores"].pop(0)

        user_words[index_of_word] = selected_word

        # Update the user's word list in the database
        self.users_collection.update_one(
            {"user_id": user_id, "languages." + current_language + ".words._id": word_key},
            {"$set": {
                "languages." + current_language + ".words.$.last_visited_times": selected_word["last_visited_times"],
                "languages." + current_language + ".words.$.last_scores": selected_word["last_scores"]
            }}
        )
        print(f"Updated word ID '{word_key}' for user {user_id}.")

        return True
    
    def get_new_excersize(self,
                          user_id) -> Tuple[Optional[Dict[Any, Any]], bool]:
        
        """
        Get a new excersize for the user from the database.
        """

        user = self.users_collection.find_one({"user_id": user_id})

        if not user:
            print(f"User {user_id} not found in the database.")
            return None, False
        
        current_language = user.get("current_language", None)
        if current_language not in SUPPORTED_LANGUAGES:
            print(f"Unsupported language '{current_language}' for user {user_id}.")
            return None, False
        
        excersize_type = np.random.choice(EXCERSIZE_TYPES)

        number_of_words_needed = NUMBER_OF_WORDS_PER_EXCERSIZE[excersize_type]

        word_keys = []

        for _ in range(number_of_words_needed):

            (word_key, 
            success) = self.get_next_word(user_id)
            
            if not success:
                print(f"Failed to get next word for user {user_id}.")
                return None, False
            
            word_keys.append(word_key)
            
        excersize = {
            "word_keys": word_keys,
            "excersize_type": excersize_type
        }

        print(f"Generated new excersize for user {user_id}: {excersize}.")

        return excersize, True
        
    def add_word_to_locked_words(self, 
                                 user_id, 
                                 word_key,
                                 locked_words,
                                 current_language) -> bool:
        """
        Add a word to the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        word_keys = [word["_id"] for word in locked_words]
        
        if word_key in word_keys:
            print(f"Word ID '{word_key}' already exists in user's locked words list.")
            return False

        word_entry = empty_word_entry(word_key)

        locked_words.append(word_entry)
        
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "languages." + current_language + ".locked_words": locked_words
            }}
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