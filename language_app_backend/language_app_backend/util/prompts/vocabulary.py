
EXAMPLE_WORD_KEYS_FOR_POPULATE = {
    "es": {
        "A1": [
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
        "A2": [
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
        "B1": [
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

INITIAL_WORD_PROMPT = """
Please generate a JSON object containing vocabulary words in [TARGET LANGUAGE] organized by CEFR levels A1, A2, and B1. 
For each level, include exactly 100 words that are common and useful at that level.
Each list should include a balanced mix of:
Common verbs (e.g. "to be", "to eat")
Everyday nouns (e.g. "house", "water", "friend")
Frequently used adjectives and adverbs (e.g. "fast", "beautiful", "often")
Basic pronouns, prepositions, and conjunctions
Phrases or expressions that are commonly used in daily conversations

Words should reflect everyday language suitable for learners up to CEFR level B1.

Format the output like this:

json
Copy code
{
    "A1": ["word1", "word2", "..."],
    "A2": ["word1", "word2", "..."],
    "B1": ["word1", "word2", "..."]
}

Do not include English translations. Only list the words as strings in arrays.

Ensure that the JSON is valid and properly formatted.
"""