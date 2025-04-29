
// let home_url = "{% url 'home' %}";
// let set_learning_language_url = "{% url 'set_learning_language' %}";
// let set_ui_language_url = "{% url 'set_ui_language' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";
// let is_set_ui_language = {{ is_set_ui_language }};
// let languages = [
//     {% for language in languages %}
//         ["{{ language.code }}", "{{ language.name }}"],
//     {% endfor %}
// ];

let D = document;

function Globals() {
    this.language_list = D.getElementById("language_list");
    this.number_of_languages = languages.length;
}

GLOBALS = new Globals();

function init() {
    init_language_list();
}

function init_language_list() {

    var language_list_html = "<ul class='language_list'>";

    for (var i = 0; i < GLOBALS.number_of_languages; i++) {
        language_list_html += "<li class='language_item' id='language_" + i + "' onclick='select_language(" + i + ")'>";
        language_list_html += "<span>" + languages[i][1] + "</span>";
        language_list_html += "</li>";
    }

    language_list_html += "</ul>";

    GLOBALS.language_list.innerHTML = language_list_html;
    GLOBALS.language_list.style.display = "block";
    
}

function select_language(index) {

    var language_code = languages[index][0];
    
    if (is_set_ui_language) {
        var url = set_ui_language_url + "?language=" + language_code;
    } else {
        var url = set_learning_language_url + "?language=" + language_code;
    }

    //
    
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                console.log("Success");
                if (is_set_ui_language) {
                    window.location.href = home_url;
                } else {
                    window.location.href = home_url;
                }
            } else {
                console.error("Error setting language: " + response.error);
            }
        } else if (xhr.readyState == 4) {
            console.error("Failed to set language. Status: " + xhr.status + ", Response: " + xhr.responseText);
        }
    }
    xhr.send();

}

init();