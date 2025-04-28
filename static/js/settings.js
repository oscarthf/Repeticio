
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
    if (GLOBALS.user_object) {
        var user_object_string = JSON.stringify(GLOBALS.user_object, null, 2);
        GLOBALS.user_object_wrapper.innerHTML = "<pre>" + user_object_string + "</pre>";
    } else {
        GLOBALS.user_object_wrapper.innerHTML = "<p>No user object available.</p>";
    }
}

function render_user_words() {
    if (GLOBALS.user_words) {
        var user_words_string = JSON.stringify(GLOBALS.user_words, null, 2);
        GLOBALS.user_words_wrapper.innerHTML = "<pre>" + user_words_string + "</pre>";
    } else {
        GLOBALS.user_words_wrapper.innerHTML = "<p>No user words available.</p>";
    }
}

function init_settings_wrapper() {
    render_user_object();
    render_user_words();
}

init();
