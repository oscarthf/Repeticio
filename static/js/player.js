
// let get_new_exercise_url = "{% url 'get_new_exercise' %}";
// let submit_answer_url = "{% url 'submit_answer' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";

let D = document;

function Globals() {
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

function main_action() {
    
    console.log("Main action triggered.");

    if (GLOBALS.current_exercise_id == null) {
        var url = get_new_exercise_url;
        var xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4 && xhr.status == 200) {
                var response = JSON.parse(xhr.responseText);
                if (response.success) {
                    // Update the player with the new exercise
                    set_new_exercise(response.exercise);
                } else {
                    console.error("Error fetching new exercise: " + response.error);
                }
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

    exercise_html += "</div>";

    GLOBALS.player_wrapper.innerHTML = exercise_html;

}

function set_new_exercise(exercise) {
    console.log("New exercise received:", exercise);
    GLOBALS.current_exercise = exercise;
    GLOBALS.current_exercise_id = exercise.exercise_id;
    render_current_exercise();
}

function submit_answer(index) {

    if (GLOBALS.current_exercise_id == null) {
        console.error("No current exercise ID set. Cannot submit answer.");
        return;
    }

    console.log("Answer submitted for exercise " + index);
    var url = submit_answer_url;
    var xhr = new XMLHttpRequest();
    var data = JSON.stringify({"answer": index,
                                "exercise_id": GLOBALS.current_exercise_id});
    xhr.open("POST", url, true);
    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                // Handle success
                console.log("Answer submitted successfully:", response.message);
                GLOBALS.current_exercise_results = response.message;
                GLOBALS.last_exercise = GLOBALS.current_exercise;
                GLOBALS.last_exercise_id = GLOBALS.current_exercise_id;
                GLOBALS.current_exercise = null; // Reset current exercise after submission
                GLOBALS.current_exercise_id = null; // Reset current exercise ID after submission
                render_current_exercise(); // Optionally re-render the player
            } else {
                console.error("Error submitting answer: " + response.error);
            }
        }
    };
    xhr.send(data);
    
}

init();