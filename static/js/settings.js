
// let home_url = "{% url 'home' %}";
// let get_user_object_url = "{% url 'get_user_object' %}";
// let get_user_words_url = "{% url 'get_user_words' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";

let D = document;

function Globals() {
    this.user_object = null;
    this.user_words = null;
    this.user_object_wrapper = D.getElementById("user_object_wrapper");
    this.user_words_wrapper = D.getElementById("user_words_wrapper");
}

GLOBALS = new Globals();

function init() {
    get_user_object();
    get_user_words();
    init_settings_wrapper();
}

function get_user_object() {
    
    var url = get_user_object_url;

    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                GLOBALS.user_object = response.user;
                console.log("User object retrieved successfully:", GLOBALS.user_object);
            } else {
                console.error("Error retrieving user object:", response.error);
            }
        } else {
            console.error("Request failed with status:", xhr.status);
        }
    };
    xhr.send();
}

function get_user_words() {

    var url = get_user_words_url;

    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                console.log("User words retrieved successfully:", response.words);
            } else {
                console.error("Error retrieving user words:", response.error);
            }
        } else {
            console.error("Request failed with status:", xhr.status);
        }
    }
    xhr.send();
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

    if (GLOBALS.user_object == null) {
        GLOBALS.user_object_wrapper.innerHTML = "<p>No user object available.</p>";
        return;
    }

    var user = GLOBALS.user_object;

    var html = `<p>User ID: ${user.user_id}</p>`;
    html += `<p>XP: ${user.xp}</p>`;
    html += `<p>Current Language: ${user.current_learning_language}</p>`;
    html += `<p>Subscription Status: ${user.subscription_status ? "Active" : "Inactive"}</p>`;
    html += `<p>Last Time Checked Subscription: ${new Date(user.last_time_checked_subscription * 1000).toLocaleString()}</p>`;
    html += `<p>Last Created Exercise ID: ${user.last_created_exercise_id}</p>`;
    html += `<p>Last Created Exercise Time: ${new Date(user.last_created_exercise_time * 1000).toLocaleString()}</p>`;
    html += `<p>Languages:</p><ul>`;

    for (let lang in user.languages) {
        html += `<li>${lang} - Current Level: ${user.languages[lang].current_level}</li>`;
    }

    html += `</ul>`;

    GLOBALS.user_object_wrapper.innerHTML = html;
    
}

function render_user_words() {

    // word_entry = {
    //     "_id": word_key,
    //     "user_id": user_id,
    //     "language": language,
    //     "last_visited_times": [],
    //     "last_scores": [],
    //     "is_locked": True
    // }

    if (GLOBALS.user_words == null) {
        GLOBALS.user_words_wrapper.innerHTML = "<p>No user words available.</p>";
        return;
    }

    var html = "<ul>";

    for (let word of GLOBALS.user_words) {
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
