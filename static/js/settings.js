// let user = JSON.parse('{{ user_object_json|escapejs }}');
// let user_words = JSON.parse('{{ user_words_json|escapejs }}');
// let home_url = "{% url 'home' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";

let D = document;

function Globals() {
    this.user_object_wrapper = D.getElementById("user_object_wrapper");
    this.user_words_wrapper = D.getElementById("user_words_wrapper");
}

GLOBALS = new Globals();

function init() {
    init_settings_wrapper();
}

function render_user_object() {    

    // user_entry = {
    //     "user_id": "oscarthf@gmail.com", 
    //     "xp": 0,
    //     "current_learning_language": "es",
    //     "subscription_status": False,
    //     "last_time_checked_subscription": 0,
    //     "last_created_exercise_id": "",
    //     "last_created_exercise_time": 0,
    //     "learning_languages": {
    //         "es": {
    //             "current_level": 0,
    //         }
    //     }
    // }

    var html = `<p>User ID: ${user_id}</p>`;
    html += `<p>XP: ${user.xp}</p>`;
    html += `<p>Current Language: ${user.current_learning_language}</p>`;
    html += `<p>Subscription Status: ${user.subscription_status ? "Active" : "Inactive"}</p>`;
    html += `<p>Last Time Checked Subscription: ${new Date(user.last_time_checked_subscription * 1000).toLocaleString()}</p>`;
    html += `<p>Last Created Exercise ID: ${user.last_created_exercise_id}</p>`;
    html += `<p>Last Created Exercise Time: ${new Date(user.last_created_exercise_time * 1000).toLocaleString()}</p>`;
    html += `<p>Languages:</p><ul>`;

    for (let lang in user.learning_languages) {
        html += `<li>${lang} - Current Level: ${user.languages[lang].current_level}</li>`;
    }

    html += `</ul>`;

    GLOBALS.user_object_wrapper.innerHTML = html;
    
}

function render_user_words() {

    // word_entry = {
    //     "_id": word_id,
    //     "user_id": user_id,
    //     "language": language,
    //     "last_visited_times": [],
    //     "last_scores": [],
    //     "is_locked": True
    // }

    if (user_words == null) {
        GLOBALS.user_words_wrapper.innerHTML = "<p>No user words available.</p>";
        return;
    }

    var html = "<ul>";

    for (let word of user_words) {
        html += `<li>${word.word} - Last visited: ${word.last_visited_times.join(", ")}</li>`;
    }

    html += "</ul>";

    GLOBALS.user_words_wrapper.innerHTML = html;

}

function init_settings_wrapper() {
    render_user_object();
    render_user_words();
}

init();
