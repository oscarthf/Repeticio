prompts = [
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence with **two blanks** ( ____ ____ ).
- Include a short instruction: "Choose the correct word to fill in the blanks:"
- Provide four answer choices (a-d), each with two words separated by a slash (/).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence with two blanks],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 1
}

Here are three variations:

Variation 1:
{
    "word_values": ["estar", "yo"],
    "initial_strings": [
        "____ ____ en la biblioteca."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blanks:"
    ],
    "final_strings": [
        "a) Yo / estoy",
        "b) Tú / estás",
        "c) Ellos / están",
        "d) Nosotros / están"
    ],
    "criteria": 1
}

Variation 2:
{
    "word_values": ["estar", "ella"],
    "initial_strings": [
        "____ ____ en casa."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blanks:"
    ],
    "final_strings": [
        "a) Ella / está",
        "b) Nosotros / está",
        "c) Ustedes / está",
        "d) Ellas / estoy"
    ],
    "criteria": 1
}

Variation 3:
{
    "word_values": ["ser", "ellos"],
    "initial_strings": [
        "____ ____ muy simpáticos."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blanks:"
    ],
    "final_strings": [
        "a) Ellos / son",
        "b) Ellas / es",
        "c) Tú / eres",
        "d) Nosotros / soy"
    ],
    "criteria": 1
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence where the **first two words** are missing ( ___ ___ ) and must be chosen.
- Include a short instruction: "Choose the correct first two words:"
- Provide four answer choices (a-d), where each option contains two words separated by a slash (/).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence starting with two blanks],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 1
}

Here are three variations:

Variation 1:
{
    "word_values": ["mi", "amigo"],
    "initial_strings": [
        "___ ___ vive en España."
    ],
    "middle_strings": [
        "Choose the correct first two words:"
    ],
    "final_strings": [
        "a) Mi / amigo",
        "b) Tu / amigo",
        "c) Nuestro / padre",
        "d) El / niño"
    ],
    "criteria": 1
}

Variation 2:
{
    "word_values": ["nuestra", "familia"],
    "initial_strings": [
        "___ ___ es muy grande."
    ],
    "middle_strings": [
        "Choose the correct first two words:"
    ],
    "final_strings": [
        "a) Nuestra / familia",
        "b) Mi / casa",
        "c) Su / hermana",
        "d) El / coche"
    ],
    "criteria": 1
}

Variation 3:
{
    "word_values": ["el", "profesor"],
    "initial_strings": [
        "___ ___ enseña matemáticas."
    ],
    "middle_strings": [
        "Choose the correct first two words:"
    ],
    "final_strings": [
        "a) El / profesor",
        "b) La / profesora",
        "c) Mi / amigo",
        "d) Su / madre"
    ],
    "criteria": 1
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence that ends with **two missing words** ( ___ ___ ) where the correct words must be chosen.
- Include a short instruction: "Choose the correct ending words:"
- Provide four answer choices (a-d), each consisting of two words separated by a slash (/).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence ending with two blanks],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 1
}

Here are three variations:

Variation 1:
{
    "word_values": ["muy", "feliz"],
    "initial_strings": [
        "Hoy me siento ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) muy / feliz",
        "b) algo / cansado",
        "c) un / poco",
        "d) muy / ocupado"
    ],
    "criteria": 1
}

Variation 2:
{
    "word_values": ["muy", "rápido"],
    "initial_strings": [
        "El tren va ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) muy / rápido",
        "b) bastante / lento",
        "c) poco / temprano",
        "d) demasiado / tarde"
    ],
    "criteria": 1
}

Variation 3:
{
    "word_values": ["muy", "caliente"],
    "initial_strings": [
        "El café está ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) muy / caliente",
        "b) algo / frío",
        "c) un / poco",
        "d) bastante / dulce"
    ],
    "criteria": 1
}
"""
]