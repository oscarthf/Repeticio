prompts = [
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence with **one blank** ( ___ ) where the correct word should go.
- Include a short instruction: "Choose the correct word to fill in the blank:"
- Provide four answer choices (a–d).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence with blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 0
}

Here are three variations:

Variation 1:
{
    "word_values": ["ir"],
    "initial_strings": [
        "Nosotros ___ al parque los domingos."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blank:"
    ],
    "final_strings": [
        "a) vamos",
        "b) van",
        "c) voy",
        "d) vas"
    ],
    "criteria": 0
}

Variation 2:
{
    "word_values": ["leer"],
    "initial_strings": [
        "Ella ___ un libro interesante."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blank:"
    ],
    "final_strings": [
        "a) lee",
        "b) lees",
        "c) leemos",
        "d) leo"
    ],
    "criteria": 0
}

Variation 3:
{
    "word_values": ["correr"],
    "initial_strings": [
        "Tú ___ muy rápido."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blank:"
    ],
    "final_strings": [
        "a) corres",
        "b) corre",
        "c) corremos",
        "d) corren"
    ],
    "criteria": 0
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence in English (or the user's base language).
- Include a short instruction: "Choose the correct translation:"
- Provide four answer choices (a–d) in the target language.
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence in English],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 0
}

Here are three variations:

Variation 1:
{
    "word_values": ["estar"],
    "initial_strings": [
        "They are tired."
    ],
    "middle_strings": [
        "Choose the correct translation:"
    ],
    "final_strings": [
        "a) Ellos están cansados.",
        "b) Ellas están feliz.",
        "c) Ellos son cansados.",
        "d) Nosotros estamos cansados."
    ],
    "criteria": 0
}

Variation 2:
{
    "word_values": ["cenar"],
    "initial_strings": [
        "We eat dinner at eight."
    ],
    "middle_strings": [
        "Choose the correct translation:"
    ],
    "final_strings": [
        "a) Nosotros cenamos a las ocho.",
        "b) Nosotros comemos a las seis.",
        "c) Nosotros desayunamos a las ocho.",
        "d) Nosotros cenamos a las diez."
    ],
    "criteria": 0
}

Variation 3:
{
    "word_values": ["escribir"],
    "initial_strings": [
        "She writes letters."
    ],
    "middle_strings": [
        "Choose the correct translation:"
    ],
    "final_strings": [
        "a) Ella escribe cartas.",
        "b) Ella lee cartas.",
        "c) Ella abre cartas.",
        "d) Ella canta canciones."
    ],
    "criteria": 0
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence where the **first word** is missing ( ___ ) and must be chosen.
- Include a short instruction: "Choose the correct first word:"
- Provide four answer choices (a–d).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence starting with a blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 0
}

Here are three variations:

Variation 1:
{
    "word_values": ["yo"],
    "initial_strings": [
        "___ estudio español todos los días."
    ],
    "middle_strings": [
        "Choose the correct first word:"
    ],
    "final_strings": [
        "a) Yo",
        "b) Tú",
        "c) Él",
        "d) Nosotros"
    ],
    "criteria": 0
}

Variation 2:
{
    "word_values": ["nosotros"],
    "initial_strings": [
        "___ viajamos a México en verano."
    ],
    "middle_strings": [
        "Choose the correct first word:"
    ],
    "final_strings": [
        "a) Nosotros",
        "b) Ellos",
        "c) Ella",
        "d) Ustedes"
    ],
    "criteria": 0
}

Variation 3:
{
    "word_values": ["ella"],
    "initial_strings": [
        "___ canta muy bien."
    ],
    "middle_strings": [
        "Choose the correct first word:"
    ],
    "final_strings": [
        "a) Ella",
        "b) Yo",
        "c) Tú",
        "d) Nosotros"
    ],
    "criteria": 0
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Write a sentence that ends with a blank ( ___ ) where the correct word must be chosen.
- Include a short instruction: "Choose the correct ending word:"
- Provide four answer choices (a–d).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence ending with a blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 0
}

Here are three variations:

Variation 1:
{
    "word_values": ["feliz"],
    "initial_strings": [
        "Hoy me siento muy ___"
    ],
    "middle_strings": [
        "Choose the correct ending word:"
    ],
    "final_strings": [
        "a) feliz",
        "b) triste",
        "c) cansado",
        "d) ocupado"
    ],
    "criteria": 0
}

Variation 2:
{
    "word_values": ["rápido"],
    "initial_strings": [
        "El tren va muy ___"
    ],
    "middle_strings": [
        "Choose the correct ending word:"
    ],
    "final_strings": [
        "a) rápido",
        "b) lento",
        "c) temprano",
        "d) tarde"
    ],
    "criteria": 0
}

Variation 3:
{
    "word_values": ["caliente"],
    "initial_strings": [
        "El café está muy ___"
    ],
    "middle_strings": [
        "Choose the correct ending word:"
    ],
    "final_strings": [
        "a) caliente",
        "b) frío",
        "c) dulce",
        "d) amargo"
    ],
    "criteria": 0
}
""",
"""
Create a multiple-choice exercise for [TARGET LANGUAGE] at [TARGET LEVEL] using the following words: [TARGET WORDS].

Instructions:
- Provide a single word.
- Include a short instruction: "Choose the correct synonym:"
- Provide four answer choices (a–d) in the target language.
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [word to find a synonym for],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": 0
}

Here are three variations:

Variation 1:
{
    "word_values": ["feliz"],
    "initial_strings": [
        "feliz"
    ],
    "middle_strings": [
        "Choose the correct synonym:"
    ],
    "final_strings": [
        "a) contento",
        "b) cansado",
        "c) ocupado",
        "d) enfermo"
    ],
    "criteria": 0
}

Variation 2:
{
    "word_values": ["rápido"],
    "initial_strings": [
        "rápido"
    ],
    "middle_strings": [
        "Choose the correct synonym:"
    ],
    "final_strings": [
        "a) veloz",
        "b) lento",
        "c) temprano",
        "d) pesado"
    ],
    "criteria": 0
}

Variation 3:
{
    "word_values": ["grande"],
    "initial_strings": [
        "grande"
    ],
    "middle_strings": [
        "Choose the correct synonym:"
    ],
    "final_strings": [
        "a) enorme",
        "b) pequeño",
        "c) estrecho",
        "d) corto"
    ],
    "criteria": 0
}
"""
]