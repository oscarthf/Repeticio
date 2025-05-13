

from flask import Flask, request, jsonify

from ..util.db import get_global_container

class RepeticioAPIServer:

    __slots__ = ("app", "gc")

    def __init__(self):
        self.app = Flask(__name__)
        self.gc = get_global_container()

    def run(self):

        @self.app.route("/get_do_not_check_subscription", methods=["GET"])
        def get_do_not_check_subscription():
            do_not_check_subscription = self.gc.get_do_not_check_subscription()
            if do_not_check_subscription is not None:
                return jsonify({"value": do_not_check_subscription})
            else:
                return jsonify({"error": "failed to get do_not_check_subscription"}), 500

        @self.app.route("/set_user_subscription", methods=["POST"])
        def set_user_subscription():
            data = request.json
            user_email = data.get("user_email")
            if user_email is None:
                return jsonify({"error": "user_id is required"}), 400
            value = data.get("value")
            if value is None:
                return jsonify({"error": "value is required"}), 400
            success = self.gc.set_user_subscription(user_email, value)
            if success:
                return jsonify({"status": "subscription updated"})
            else:
                return jsonify({"error": "failed to update subscription"}), 500
            
        @self.app.route("/check_subscription_pipeline", methods=["POST"])
        def check_subscription_pipeline():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            success = self.gc.check_subscription_pipeline(user_id)
            if success:
                return jsonify({"status": "subscription pipeline checked"})
            else:
                return jsonify({"error": "failed to check subscription pipeline"}), 500
            
        @self.app.route("/get_user_object", methods=["POST"])
        def get_user_object():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            user_object = self.gc.get_user_object(user_id)
            if user_object:
                return jsonify({"user_object": user_object})
            else:
                return jsonify({"error": "failed to get user object"}), 500
            
        @self.app.route("/get_learning_language", methods=["POST"])
        def get_learning_language():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            learning_language = self.gc.get_learning_language(user_id)
            if learning_language:
                return jsonify({"learning_language": learning_language})
            else:
                return jsonify({"error": "failed to get learning language"}), 500
            
        @self.app.route("/get_user_words", methods=["POST"])
        def get_user_words():
            data = request.json
            user_id = data.get("user_id")
            learning_language = data.get("learning_language")
            is_locked = data.get("is_locked", False)
            if user_id is None or learning_language is None:
                return jsonify({"error": "user_id and learning_language are required"}), 400
            user_words = self.gc.get_user_words(user_id, learning_language, is_locked)
            if user_words:
                return jsonify({"user_words": user_words})
            else:
                return jsonify({"error": "failed to get user words"}), 500
            
        @self.app.route("/create_user_if_needed", methods=["POST"])
        def create_user_if_needed():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            success = self.gc.create_user_if_needed(user_id)
            if success:
                return jsonify({"status": "user created"})
            else:
                return jsonify({"error": "failed to create user"}), 500
            
        @self.app.route("/redirect_if_new_user", methods=["POST"])
        def redirect_if_new_user():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            success, redirect_view = self.gc.redirect_if_new_user(user_id)
            if success:
                return jsonify({"redirect_view": redirect_view})
            else:
                return jsonify({"error": "failed to redirect new user"}), 500
            
        @self.app.route("/get_supported_languages", methods=["GET"])
        def get_supported_languages():
            languages = self.gc.get_supported_languages()
            if languages:
                return jsonify({"supported_languages": languages})
            else:
                return jsonify({"error": "failed to get supported languages"}), 500
            
        @self.app.route("/get_created_exercise", methods=["POST"])
        def get_created_exercise():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            exercise, success = self.gc.get_created_exercise(user_id)
            if success:
                return jsonify({"exercise": exercise})
            else:
                return jsonify({"error": "failed to get created exercise"}), 500
            
        @self.app.route("/create_new_exercise", methods=["POST"])
        def create_new_exercise():
            data = request.json
            user_id = data.get("user_id")
            if user_id is None:
                return jsonify({"error": "user_id is required"}), 400
            success = self.gc.create_new_exercise(user_id)
            if success:
                return jsonify({"status": "new exercise created"})
            else:
                return jsonify({"error": "failed to create new exercise"}), 500
            
        @self.app.route("/apply_thumbs_up_or_down", methods=["POST"])
        def apply_thumbs_up_or_down():
            data = request.json
            user_id = data.get("user_id")
            exercise_id = data.get("exercise_id")
            thumbs_up = data.get("thumbs_up")
            if user_id is None or exercise_id is None or thumbs_up is None:
                return jsonify({"error": "user_id, exercise_id and thumbs_up are required"}), 400
            success = self.gc.apply_thumbs_up_or_down(user_id, exercise_id, thumbs_up)
            if success:
                return jsonify({"status": "thumbs up/down applied"})
            else:
                return jsonify({"error": "failed to apply thumbs up/down"}), 500
            
        @self.app.route("/set_learning_language", methods=["POST"])
        def set_learning_language():
            data = request.json
            user_id = data.get("user_id")
            language = data.get("language")
            if user_id is None or language is None:
                return jsonify({"error": "user_id and language are required"}), 400
            success = self.gc.set_learning_language(user_id, language)
            if success:
                return jsonify({"status": "learning language set"})
            else:
                return jsonify({"error": "failed to set learning language"}), 500
            
        @self.app.route("/set_ui_language", methods=["POST"])
        def set_ui_language():
            data = request.json
            user_id = data.get("user_id")
            language = data.get("language")
            if user_id is None or language is None:
                return jsonify({"error": "user_id and language are required"}), 400
            success = self.gc.set_ui_language(user_id, language)
            if success:
                return jsonify({"status": "UI language set"})
            else:
                return jsonify({"error": "failed to set UI language"}), 500
            
        @self.app.route("/submit_answer", methods=["POST"])
        def submit_answer():
            data = request.json
            user_id = data.get("user_id")
            exercise_id = data.get("exercise_id")
            answer = data.get("answer")
            if user_id is None or exercise_id is None or answer is None:
                return jsonify({"error": "user_id, exercise_id and answer are required"}), 400
            success, message, correct = self.gc.submit_answer(user_id, exercise_id, answer)
            if success:
                return jsonify({"status": "answer submitted", "message": message, "correct": correct})
            else:
                return jsonify({"error": "failed to submit answer"}), 500

        self.app.run(host="0.0.0.0", port=5000)

if __name__ == "__main__":

    api = RepeticioAPIServer()
    api.run()