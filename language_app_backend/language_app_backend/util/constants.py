NEXT_WORD_TEMPERATURE = 0.02
MAX_HISTORY_LENGTH = 5
SUPPORTED_LANGUAGES = [
    # "en",  # English
    "es",  # Spanish
    # "fr",  # French
    # "de",  # German
    # "it",  # Italian
    # "pt",  # Portuguese
    # "ru",  # Russian
]
INITIAL_WORD_KEYS_FOR_POPULATE = {
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


EXCERSIZE_TYPES = [
    "multiple_choice",
    "fill_in_the_blank",
]
NUMBER_OF_WORDS_PER_EXCERSIZE = {
    "multiple_choice": 2,
    "fill_in_the_blank": 2,
}