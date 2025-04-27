
// let base_url = "{% url 'home' %}";
// let user_name = "{{ user.username }}";
// let user_id = "{{ user.email }}";
// let languages = [
//     {% for language in languages %}
//         ["{{ language.code }}", "{{ language.name }}"]
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
        language_list_html += "<img src='/static/img/flags/" + languages[i][0] + ".png' alt='" + languages[i][1] + "'>";
        language_list_html += "<span>" + languages[i][1] + "</span>";
        language_list_html += "</li>";
    }

    language_list_html += "</ul>";

    GLOBALS.language_list.innerHTML = language_list_html;
    GLOBALS.language_list.style.display = "block";
    
}

function select_language(index) {

    // redirect to home but add ?language=<language_code> to the url

    var language_code = languages[index][0];
    
    var url = base_url + "?language=" + language_code;

    window.location.href = url;

}

init();