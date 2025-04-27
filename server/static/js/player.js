
// let base_url = "{{ request.scheme }}://{{ request.get_host }}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";

let D = document;

function Globals() {
    this.player_wrapper = D.getElementById("player_wrapper");
    this.current_exercise_id = null;
    this.current_exercise = null;
    this.current_exercise_results = null;
    this.last_exercise = null;
    this.last_exercise_id = null;
}

GLOBALS = new Globals();

function init() {
    init_player_wrapper();
}

function init_player_wrapper() {
    GLOBALS.player_wrapper.innerHTML = "<p>Player content goes here...</p>";
}

function main_action() {
    
    console.log("Main action triggered.");

    if (GLOBALS.current_exercise_id == null) {
        var url = base_url + "/get_new_exercise";
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
    
    // ...

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
    var url = base_url + "/submit_answer";
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
