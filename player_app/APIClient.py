import requests
from typing import Optional, List, Tuple, Dict, Any

class RepeticioAPIClient:

    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url.rstrip("/")

    def _post(self, endpoint: str, data: Dict) -> Dict:
        response = requests.post(f"{self.api_base_url}/{endpoint}", json=data)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str) -> Dict:
        response = requests.get(f"{self.api_base_url}/{endpoint}")
        response.raise_for_status()
        return response.json()

    def set_user_subscription(self, user_email: str, value: bool) -> bool:
        result = self._post("set_user_subscription", {"user_email": user_email, "value": value})
        return result.get("status") == "subscription updated"

    def check_subscription_pipeline(self, user_id: str) -> bool:
        result = self._post("check_subscription_pipeline", {"user_id": user_id})
        return result.get("status") == "subscription pipeline checked"

    def get_user_object(self, user_id: str) -> Optional[Dict]:
        result = self._post("get_user_object", {"user_id": user_id})
        return result.get("user_object")

    def get_learning_language(self, user_id: str) -> Optional[str]:
        result = self._post("get_learning_language", {"user_id": user_id})
        return result.get("learning_language")

    def get_user_words(self, user_id: str, learning_language: str, is_locked: bool = False) -> Optional[List]:
        result = self._post("get_user_words", {
            "user_id": user_id, 
            "learning_language": learning_language, 
            "is_locked": is_locked
        })
        return result.get("user_words")

    def create_user_if_needed(self, user_id: str) -> bool:
        result = self._post("create_user_if_needed", {"user_id": user_id})
        return result.get("status") == "user created"

    def redirect_if_new_user(self, user_id: str) -> Tuple[bool, Optional[str]]:
        result = self._post("redirect_if_new_user", {"user_id": user_id})
        return result.get("redirect_view") is not None, result.get("redirect_view")

    def get_supported_languages(self) -> List[str]:
        result = self._get("get_supported_languages")
        return result.get("supported_languages", [])

    def get_created_exercise(self, user_id: str) -> Tuple[Optional[Dict[Any, Any]], bool]:
        result = self._post("get_created_exercise", {"user_id": user_id})
        return result.get("exercise"), "exercise" in result

    def create_new_exercise(self, user_id: str) -> bool:
        result = self._post("create_new_exercise", {"user_id": user_id})
        return result.get("status") == "new exercise created"

    def apply_thumbs_up_or_down(self, user_id: str, exercise_id: str, thumbs_up: bool) -> bool:
        result = self._post("apply_thumbs_up_or_down", {
            "user_id": user_id, 
            "exercise_id": exercise_id, 
            "thumbs_up": thumbs_up
        })
        return result.get("status") == "thumbs up/down applied"

    def set_learning_language(self, user_id: str, language: str) -> bool:
        result = self._post("set_learning_language", {"user_id": user_id, "language": language})
        return result.get("status") == "learning language set"

    def set_ui_language(self, user_id: str, language: str) -> bool:
        result = self._post("set_ui_language", {"user_id": user_id, "language": language})
        return result.get("status") == "UI language set"

    def submit_answer(self, user_id: str, exercise_id: str, answer: str) -> Tuple[bool, str, bool]:
        result = self._post("submit_answer", {
            "user_id": user_id, 
            "exercise_id": exercise_id, 
            "answer": answer
        })
        return (
            result.get("status") == "answer submitted",
            result.get("message", ""),
            result.get("correct", False)
        )
