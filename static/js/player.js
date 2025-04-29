
// let create_new_exercise_url = "{% url 'create_new_exercise' %}";
// let get_created_exercise_url = "{% url 'get_created_exercise' %}";
// let apply_thumbs_up_url = "{% url 'apply_thumbs_up_or_down' %}";
// let submit_answer_url = "{% url 'submit_answer' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";

let D = document;

function Globals() {
    this.UPDATE_INTERVAL = 2000; // 2 seconds
    this.player_wrapper = D.getElementById("player_wrapper");
    this.main_action_button = D.getElementById("main_action_button");
    this.current_exercise_id = null;
    this.current_exercise = null;
    this.current_exercise_results = null;
    this.last_exercise = null;
    this.last_exercise_id = null;
}

GLOBALS = new Globals();

function init() {
    init_main_action_button();
    init_player_wrapper();
}

function init_main_action_button() {
    GLOBALS.main_action_button.addEventListener("click", function() {
        main_action();
    });
}

function init_player_wrapper() {
    GLOBALS.player_wrapper.innerHTML = "<p>Player content goes here...</p>";
}

function get_created_exercise() {
    console.log("Fetching created exercise...");

    if (GLOBALS.current_exercise_id != null) {
        console.log("Current exercise ID is already set. No need to fetch a new one.");
        return;
    }

    var url = get_created_exercise_url;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                // Update the player with the new exercise
                if (response.exercise == null) {
                    console.log("Still processing.");
                    // try again after 30 seconds
                    setTimeout(function() {
                        get_created_exercise();
                    }, GLOBALS.UPDATE_INTERVAL); // 30 seconds
                } else {
                    set_new_exercise(response.exercise);
                    console.log("Exercise fetched successfully");
                }
            } else {
                console.error("Error fetching exercise: " + response.error);
                // try again after 30 seconds
                setTimeout(function() {
                    get_created_exercise();
                }, GLOBALS.UPDATE_INTERVAL); // 30 seconds
            }
        } else if (xhr.readyState == 4) {
            console.error("Failed to fetch exercise. Status: " + xhr.status + ", Response: " + xhr.responseText);
            // try again after 30 seconds
            setTimeout(function() {
                get_created_exercise();
            }, GLOBALS.UPDATE_INTERVAL); // 30 seconds
        }
    }
    xhr.send();
}

function show_loading_message(message) {
    console.log(message);
    GLOBALS.player_wrapper.innerHTML = "<p>" + message + "</p>";
    GLOBALS.main_action_button.disabled = true; // Disable the button while loading
}

function main_action() {
    
    console.log("Main action triggered.");

    if (GLOBALS.current_exercise_id == null) {
        show_loading_message("Creating new exercise...");
        var url = create_new_exercise_url;
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.success) {
                    console.log("New exercise created:", response.message);
                    // set timeout for 30 seconds
                    setTimeout(function() {
                        get_created_exercise();
                    }, GLOBALS.UPDATE_INTERVAL); // 30 seconds
                } else {
                    console.error("Error fetching new exercise: " + response.error);
                }
            } else if (xhr.readyState == 4) {
                console.error("Failed to create new exercise. Status: " + xhr.status + ", Response: " + xhr.responseText);
            }
        };
        xhr.send();
    } else {
        console.log("Current exercise already set. No need to fetch a new one.");
    }

}

function render_current_exercise() {

    console.log("Rendering current exercise:", GLOBALS.current_exercise);
    
    if (GLOBALS.current_exercise == null) {
        console.error("No current exercise to render.");
        return;
    }

    var exercise_html = "<div class='exercise'>";

    var initial_strings = GLOBALS.current_exercise.initial_strings;
    
    if (initial_strings == null || initial_strings.length == 0) {
        console.error("No initial strings provided for the exercise.");
        return;
    }

    var middle_strings = GLOBALS.current_exercise.middle_strings;

    if (middle_strings == null || middle_strings.length == 0) {
        console.error("No middle strings provided for the exercise.");
        return;
    }

    var final_strings = GLOBALS.current_exercise.final_strings;

    if (final_strings == null || final_strings.length == 0) {
        console.error("No final strings provided for the exercise.");
        return;
    }

    //

    //

    exercise_html += "<div class='initial_strings'>";
    for (var i = 0; i < initial_strings.length; i++) {

        exercise_html += "<div class='initial_string'>" + initial_strings[i] + "</div>";

    }
    exercise_html += "</div>";

    exercise_html += "<div class='middle_strings'>";

    for (var i = 0; i < middle_strings.length; i++) {
        exercise_html += "<div class='middle_string'>" + middle_strings[i] + "</div>";
    }
    exercise_html += "</div>";

    exercise_html += "<div class='final_strings'>";
    for (var i = 0; i < final_strings.length; i++) {
        exercise_html += "<div class='final_string' onclick='submit_answer(" + i + ")'>" + final_strings[i] + "</div>";
    }
    exercise_html += "</div>";

    // thumbs up and thumbs down buttons

    exercise_html += "<div id='thumbs_buttons'>";
    exercise_html += "<button class='thumbs_up' onclick='apply_thumbs_up(true)'>👍</button>";
    exercise_html += "<button class='thumbs_down' onclick='apply_thumbs_up(false)'>👎</button>";
    exercise_html += "</div>";

    exercise_html += "</div>";

    GLOBALS.player_wrapper.innerHTML = exercise_html;

}

function set_new_exercise(exercise) {
    console.log("New exercise received:", exercise);
    GLOBALS.current_exercise = exercise;
    GLOBALS.current_exercise_id = exercise.exercise_id;
    GLOBALS.current_exercise_results = null; // Reset results for the new exercise
    GLOBALS.last_exercise = null; // Reset last exercise
    GLOBALS.last_exercise_id = null; // Reset last exercise ID
    GLOBALS.main_action_button.disabled = false; // Enable the button after setting the exercise
    render_current_exercise();
}

function render_results() {
    console.log("Rendering results for exercise ID:", GLOBALS.current_exercise_id);
        
    if (GLOBALS.current_exercise_results == null) {
        console.error("No results to render.");
        return;
    }

    var results_html = "<div class='results'>";
    
    var result = GLOBALS.current_exercise_results;
    results_html += "<div class='result'>";
    results_html += "<p>" + result.message + "</p>";
    results_html += "</div>";
    
    results_html += "</div>";
    
    GLOBALS.player_wrapper.innerHTML += results_html;
}

function apply_thumbs_up(is_positive) {

    console.log("Applying thumbs up:", is_positive);

    if (GLOBALS.current_exercise_id == null) {
        console.error("No current exercise ID set. Cannot apply thumbs up.");
        return;
    }

    var is_positive_str = is_positive ? "true" : "false";

    var url = apply_thumbs_up_url + "?is_positive=" + is_positive_str + "&exercise_id=" + GLOBALS.current_exercise_id;

    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                console.log("Thumbs up applied successfully:", response.message);
                GLOBALS.current_exercise_results = response;
                render_thumbs_up_results(is_positive);
            } else {
                console.error("Error applying thumbs up: " + response.error);
            }
        } else if (xhr.readyState == 4) {
            console.error("Failed to apply thumbs up. Status: " + xhr.status + ", Response: " + xhr.responseText);
        }
    }
    xhr.send();
}

function render_thumbs_up_results(is_positive) {
    console.log("Rendering thumbs up results:", is_positive);

    var thumbs_buttons = D.getElementById("thumbs_buttons");

    thumbs_buttons.innerHTML = "<p>Thank you for your feedback!</p>";

}

function submit_answer(index) {

    if (GLOBALS.current_exercise_id == null) {
        console.error("No current exercise ID set. Cannot submit answer.");
        return;
    }

    console.log("Answer submitted for exercise " + index);
    var url = submit_answer_url + "?answer=" + index + "&exercise_id=" + GLOBALS.current_exercise_id;
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                console.log("Answer submitted successfully:", response.message);
                GLOBALS.current_exercise_results = response;
                GLOBALS.last_exercise = GLOBALS.current_exercise; // Save the last exercise
                GLOBALS.last_exercise_id = GLOBALS.current_exercise_id; // Save the last exercise ID
                GLOBALS.current_exercise = null; // Reset current exercise
                GLOBALS.current_exercise_id = null; // Reset current exercise ID after submission
                // hide thumbs buttons
                var thumbs_buttons = D.getElementById("thumbs_buttons");
                if (thumbs_buttons) {
                    thumbs_buttons.style.display = "none"; // Hide thumbs buttons
                }
                render_results();
            } else {
                console.error("Error submitting answer: " + response.error);
            }
        } else if (xhr.readyState == 4) {
            console.error("Failed to submit answer. Status: " + xhr.status + ", Response: " + xhr.responseText);
        }
    };
    xhr.send();
}

init();
