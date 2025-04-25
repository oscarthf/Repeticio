
from typing import Dict, Any
import json

from openai import OpenAI

REAL_LANGUAGE_NAMES = {
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
}

EXAMPLE_WORD_KEYS_FOR_POPULATE = {
    "es": {
        0: [
            "ser", "estar", "tener", "hacer", "ir", "decir", "comer", "beber", "vivir", "hablar",
            "casa", "escuela", "coche", "amigo", "madre", "padre", "niño", "agua", "pan", "leche",
            "sí", "no", "hola", "adiós", "gracias", "por favor", "lo siento", "bien", "mal", "mucho",
            "poco", "grande", "pequeño", "bonito", "feo", "rápido", "lento", "caliente", "frío", "día",
            "noche", "mañana", "hoy", "ayer", "uno", "dos", "tres", "cuatro", "cinco", "más",
            "menos", "también", "pero", "porque", "cómo", "qué", "quién", "dónde", "cuándo", "por qué",
            "yo", "tú", "él", "ella", "nosotros", "vosotros", "ellos", "mi", "tu", "su",
            "este", "ese", "aquí", "allí", "muy", "ya", "siempre", "nunca", "a", "de",
            "en", "con", "sin", "para", "sobre", "entre", "abajo", "arriba", "dentro", "fuera",
            "hora", "minuto", "segundo", "trabajo", "libro", "mesa", "silla", "gato", "perro", "calle"
        ],
        1: [
            "buscar", "encontrar", "esperar", "necesitar", "entrar", "salir", "llevar", "usar", "abrir", "cerrar",
            "empezar", "terminar", "ayudar", "llamar", "viajar", "volver", "cambiar", "pagar", "comprar", "vender",
            "siempre", "a veces", "casi", "nunca", "temprano", "tarde", "seguro", "ocupado", "libre", "feliz",
            "triste", "cansado", "nervioso", "tranquilo", "sucio", "limpio", "nuevo", "viejo", "barato", "caro",
            "primero", "último", "izquierdo", "derecho", "recto", "cerca", "lejos", "norte", "sur", "este",
            "oeste", "estación", "aeropuerto", "tren", "autobús", "viaje", "maleta", "pasaporte", "dinero", "tarjeta",
            "banco", "tienda", "mercado", "supermercado", "ropa", "zapatos", "camisa", "pantalón", "chaqueta", "vestido",
            "comida", "fruta", "verdura", "carne", "pescado", "azúcar", "sal", "aceite", "arroz", "huevo",
            "cocina", "baño", "dormitorio", "salón", "ventana", "puerta", "pared", "suelo", "techo", "lugar",
            "ciudad", "pueblo", "campo", "playa", "montaña", "clima", "tiempo", "calor", "lluvia", "nieve"
        ],
        2: [
            "desear", "odiar", "gustar", "molestar", "preocupar", "sorprender", "imaginar", "recordar", "olvidar", "proponer",
            "sugerir", "intentar", "decidir", "desarrollar", "mejorar", "empeorar", "discutir", "convencer", "permitir", "prohibir",
            "deber", "soler", "parecer", "importar", "significar", "crecer", "nacer", "morir", "herir", "curar",
            "enfermedad", "medicina", "médico", "paciente", "dolor", "fiebre", "tos", "sangre", "corazón", "cuerpo",
            "mente", "espíritu", "empresa", "jefe", "compañero", "entrevista", "sueldo", "horario", "reunión", "proyecto",
            "éxito", "fracaso", "responsabilidad", "oportunidad", "decisión", "duda", "razón", "causa", "consecuencia", "problema",
            "solución", "ventaja", "desventaja", "cultura", "historia", "política", "economía", "sociedad", "religión", "medio ambiente",
            "contaminación", "naturaleza", "energía", "recurso", "tecnología", "internet", "red", "aplicación", "móvil", "correo",
            "mensaje", "señal", "archivo", "documento", "idioma", "lengua", "traducción", "significado", "expresión", "opinión",
            "argumento", "noticia", "periódico", "revista", "televisión", "canal", "programa", "película", "personaje", "escena"
        ]
    },
}

INITIAL_WORD_PROMPT = """Please generate a JSON object containing vocabulary words in [TARGET LANGUAGE] organized by CEFR levels A1 (0), A2 (1), and B1 (2). For each level, include exactly 100 words that are common and useful at that level.
Each list should include a balanced mix of:
Common verbs (e.g. "to be", "to eat")
Everyday nouns (e.g. "house", "water", "friend")
Frequently used adjectives and adverbs (e.g. "fast", "beautiful", "often")
Basic pronouns, prepositions, and conjunctions
Words should reflect everyday language suitable for learners up to CEFR level B1.

Format the output like this:

json
Copy code
{
  "xx": {
    0: ["word1", "word2", "..."],
    1: ["word1", "word2", "..."],
    2: ["word1", "word2", "..."]
  }
}
Replace "xx" with the language code (e.g., "es" for Spanish, "fr" for French).
Do not include English translations. Only list the words as strings in arrays.
"""

class LLM:

    __slots__ = [
        
    ]
    def __init__(self) -> None:
        """
        Initialize the LLM class.
        """

        self.client = OpenAI()

    def create_exercise(self,
                        word_values,
                        word_keys,
                        exercise_type,
                        current_language,
                        current_level) -> Dict[Any, Any]:
        """
        Create an exercise for the user from the database.
        """

        exercise = {
            "word_keys": word_keys,
            "word_values": word_values,
            "exercise_type": exercise_type,
            "initial_strings": [],
            "final_strings": [],
            "criteria": []
        }

        return exercise
    
    def get_initial_words(self,
                          language):
        
        """
        Get the initial words for the given language.
        """

        if not language in REAL_LANGUAGE_NAMES:
            print(f"Language '{language}' is not supported.")
            return None
        
        real_language_name = REAL_LANGUAGE_NAMES[language]

        language_str = f"{real_language_name} ({language})"

        query_input = INITIAL_WORD_PROMPT.replace("[TARGET LANGUAGE]", language_str)

        response = self.client.responses.create(
            model="gpt-4.1",
            input=query_input
        )

        print(response.output_text)

        if not "{" in response.output_text or not "}" in response.output_text:
            print("Invalid response format")
            return None

        start_index = response.output_text.find("{")
        end_index = response.output_text.rfind("}")

        json_string = response.output_text[start_index:end_index + 1]
        try:
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
        
        number_of_keys = len(json_data.keys())

        if number_of_keys != 1:
            print(f"Invalid number of keys in JSON: {number_of_keys}")
            return None
        
        json_data = {language: json_data[json_data.keys()[0]]}
        
        if len(json_data[language]) != 3:
            print(f"Invalid number of levels in JSON: {len(json_data[language])}")
            return None

        for level in json_data[language]:
            if len(json_data[language][level]) != 100:
                print(f"Invalid number of words in level {level}: {len(json_data[language][level])}")
                return None
            
            for word in json_data[language][level]:
                if not isinstance(word, str):
                    print(f"Invalid word format in level {level}: {word}")
                    return None

        return json_data

        
