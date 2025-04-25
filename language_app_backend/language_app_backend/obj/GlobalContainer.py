
import datetime

import threading

class GlobalContainer:
    __slots__ = [
        "db_client", 
        "db",
        "words_collection",
        "users_collection",
        "insert_lock",
    ]
    def __init__(self, db_client):

        self.db_client = db_client
        self.db = db_client["language_app"]
        self.words_collection = self.db["words"]
        self.users_collection = self.db["users"]

        self.insert_lock = threading.Lock()

    def create_user_if_not_exists(self, user_id):
        """
        Create a user in the database if it does not exist.
        """
        with self.insert_lock:
            user = self.users_collection.find_one({"user_id": user_id})
            if not user:
                self.users_collection.insert_one({"user_id": user_id, 
                                                  "score": 0,
                                                  "xp": 0,
                                                  "words": []})
                print(f"User {user_id} created in the database.")
            else:
                print(f"User {user_id} already exists in the database.")

    def update_word_score(self, user_id, word_id, score, max_history=5):
        """
        Observe a word for a user and update the score in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        word_doc = self.words_collection.find_one({"_id": word_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False

        if not word_doc:
            print(f"Word ID '{word_id}' not found in words_collection.")
            return False
        
        time_now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        user_words = user.get("words", [])
        got_word = False
        for i, word_entry in enumerate(user_words):
            if word_entry["word_id"] == word_id:
                # Update the last visited times and scores
                user_words[i]["last_visited_times"].append(time_now)
                user_words[i]["last_scores"].append(score)

                # Limit the history size
                if len(user_words[i]["last_visited_times"]) > max_history:
                    user_words[i]["last_visited_times"].pop(0)
                    user_words[i]["last_scores"].pop(0)

                got_word = True
                break

        if not got_word:
            print(f"Word ID '{word_id}' not found in user's word list.")
            return False
        
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"words": user_words}}
        )
        print(f"Word ID '{word_id}' observed for user {user_id} with score {score}.")

        return True

    def add_word(self, user_id, word_id):
        """
        Add a word to the user's word list in the database.
        """
        
        user = self.users_collection.find_one({"user_id": user_id})
        word_doc = self.words_collection.find_one({"_id": word_id})
        
        if not user:
            print(f"User {user_id} not found in the database.")
            return False

        if not word_doc:
            print(f"Word ID '{word_id}' not found in words_collection.")
            return False
        
        word_entry = {
            "word_id": word_doc["_id"],
            "last_visited_times": [],
            "last_scores": [],
        }
        
        with self.insert_lock:
            self.users_collection.update_one(
                {"user_id": user_id},
                {"$addToSet": {"words": word_entry}}
            )
            print(f"Word ID '{word_id}' added to user {user_id}'s word list.")