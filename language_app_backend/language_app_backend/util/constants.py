NEXT_WORD_TEMPERATURE = 0.02
MAX_HISTORY_LENGTH = 5
MAX_NUMBER_OF_EXERCISES = 5
MIN_THUMB_VOLUME = 50
VOCABULARY_REVISION_ITERATIONS = 3
VOCABULARY_REVISION_INTERVAL = 4 * 60 * 60 # 4 hours
MAX_CONCURRENT_EXERCISE_CREATIONS = 10
MAX_WORD_LENGTH = 32
DELETE_SERVER_TIMEOUT = 2 * 60# time to delete server if heartbeat has not been received
ALLOW_MAIN_SERVER_TIMEOUT = 60# time for server to wait until it is alowed to be the main server
BACKGROUND_THREAD_SLEEP_TIME = 30# time for server to wait until it is alowed to be the main server
TIMEOUT_TO_CREATE_NEW_EXERCISE = 30# time to wait until a new exercise is created

# OPENAI_MODEL_NAME = "gpt-4.1"
OPENAI_MODEL_NAME = "gpt-4o"

DO_NOT_CHECK_SUBSCRIPTION = True# This is for testing purposes only. In production, set this to False.

# OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = ["oscarthf@gmail.com"]
OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = []

CHECK_SUBSCRIPTION_INTERVAL = 10 * 60  # 10 minutes
DEFAULT_RATELIMIT = '100/h'  # Default rate limit for all views
GET_CREATED_EXERCISES_RATELIMIT = '40/m'  # Rate limit for get_created_exercises view

NUMBER_OF_ATTEMPTS_TO_CREATE_EXERCISE = 3

POSSIBLE_CRITERIA = ["a", "b", "c", "d", "e", "f"]
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
}
