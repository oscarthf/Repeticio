
from typing import Optional, Tuple
import datetime
import threading

import numpy as np

from ..util.constants import (SUPPORTED_LANGUAGES,
                              SUPPORTED_CEFR_LEVELS,
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

def empty_word_entry(word_key) -> dict:

    """
    Create an empty word entry for the database.
    """
    return {
        "_id": word_key,
        "last_visited_times": [],
        "last_scores": [],
    }

def empty_word_document(word_key) -> dict:

    """
    Create an empty word document for the database.
    """
    return {
        "_id": word_key,
        "level": "A1"
    }

class GlobalContainer:
    __slots__ = [
        "db_client", 
        "db",
        "words_collection",
        "users_collection",
        "insert_lock",
        "initial_words",
    ]
    def __init__(self, db_client):

        self.db_client = db_client
        self.db = db_client["language_app"]
        self.words_collection = self.db["words"]
        self.users_collection = self.db["users"]

        self.insert_lock = threading.Lock()
        
        self.initial_words = self.get_initial_word_keys()

        if not len(self.initial_words):
            self.populate_initial_words()
            self.initial_words = self.get_initial_word_keys()

    def populate_initial_words(self) -> None:

        """
        Populate the database with initial words.
        """
        
        if not len(INITIAL_WORD_KEYS_FOR_POPULATE):
            print("No initial words to populate.")
            return

        for word_key in INITIAL_WORD_KEYS_FOR_POPULATE:
            word_doc = empty_word_document(word_key)
            self.words_collection.insert_one(word_doc)

        print(f"Inserted {len(INITIAL_WORD_KEYS_FOR_POPULATE)} initial words into the database.")

    def get_initial_word_keys(self) -> list:
        """
        Get the initial (A1) words from the database.
        """
        
        initial_words = self.words_collection.find({"level": "A1"})

        if not len(initial_words):
            print("No initial words found in the database.")
            return []

        initial_word_keys = [word["_id"] for word in initial_words]

        print(f"Found {len(initial_word_keys)} initial words in the database.")
        
        return initial_word_keys

    def create_user_if_not_exists(self, 
                                  user_id) -> bool:
        """
        Create a user in the database if it does not exist.
        """
        with self.insert_lock:
            user = self.users_collection.find_one({"user_id": user_id})
            if not user:
                self.users_collection.insert_one({"user_id": user_id, 
                                                  "score": 0,
                                                  "xp": 0,
                                                  "words": [],
                                                  "locked_words": [empty_word_entry(word) for word in self.initial_words],})
                print(f"User {user_id} created in the database.")
                return True
            else:
                print(f"User {user_id} already exists in the database.")
                return False
            
    def check_if_should_unlock_new_word(self, 
                                        user_id) -> int:
        """
        Check if the user should unlock a new word based on their score.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        words = user.get("words", [])
        locked_words = user.get("locked_words", [])

        if not len(locked_words):
            print(f"No locked words found for user {user_id}.")
            return 2
        
        if not len(words):
            unlocked_word = locked_words.pop(0)
            words.append(unlocked_word)
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"words": words, "locked_words": locked_words}}
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
                {"$set": {"words": words, "locked_words": locked_words}}
            )
            print(f"Unlocked new word for user {user_id}: {unlocked_word}.")
            return 1

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

        time_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        user_words = user.get("words", [])
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
        with self.insert_lock:
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"words": user_words}}
            )
        print(f"Word ID '{word_key}' observed for user {user_id} with score {score}.")

        return True

    def add_word_to_locked_words(self, user_id, word_key):
        """
        Add a word to the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False
        
        locked_words = user.get("locked_words", [])

        word_keys = [word["_id"] for word in locked_words]
        
        if word_key in word_keys:
            print(f"Word ID '{word_key}' already exists in user's locked words list.")
            return False

        word_entry = empty_word_entry(word_key)

        locked_words.append(word_entry)
        
        with self.insert_lock:
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"locked_words": locked_words}}
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
        
        # Get the words list from the user document
        words = user.get("words", [])
        
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