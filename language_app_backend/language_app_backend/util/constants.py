NEXT_WORD_TEMPERATURE = 0.02
MAX_HISTORY_LENGTH = 5
MAX_NUMBER_OF_EXERCISES = 5
MIN_THUMB_VOLUME = 50
VOCABULARY_REVISION_ITERATIONS = 3
VOCABULARY_REVISION_INTERVAL = 4 * 60 * 60 # 4 hours
MAX_CONCURRENT_EXERCISE_CREATIONS = 3
MAX_WORD_LENGTH = 32

# OPENAI_MODEL_NAME = "gpt-4.1"
OPENAI_MODEL_NAME = "gpt-4o"

DO_NOT_CHECK_SUBSCRIPTION = True# This is for testing purposes only. In production, set this to False.

# OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = ["oscarthf@gmail.com"]
OPEN_LANGUAGE_APP_ALLOWED_USER_IDS = []

CHECK_SUBSCRIPTION_INTERVAL = 10 * 60  # 10 minutes
DEFAULT_RATELIMIT = '100/h'  # Default rate limit for all views

NUMBER_OF_ATTEMPTS_TO_CREATE_EXERCISE = 5

SUPPORTED_LANGUAGES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
}
