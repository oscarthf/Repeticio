
start_prompt = """
Create a multiple-choice exercise for a [TARGET LANGUAGE] course at [TARGET LEVEL] 
using the following word: [TARGET WORDS].

Instructions:
- Write a sentence with ONE BLANK ( ___ ) where the correct word should go.
- Make sure you use the word porvided above.
- Include a short instruction: "Choose the correct word to fill in the blank:"
- Provide 3 to 5 answer choices, (a, b, c, d, e).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words],
    "initial_strings": [sentence with blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": [correct answer (example: "c")]
}

Here are 3 examples:
"""

inspiration_exercises = [# MUST HAVE AT LEAST 3 TO START!!!

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
    "criteria": "a"
}, 

{
    "word_values": ["leer"],
    "initial_strings": [
        "Ella ___ un libro interesante."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blank:"
    ],
    "final_strings": [
        "a) le",
        "b) lees",
        "c) leemos",
        "d) leo"
        "e) lee",
    ],
    "criteria": "e"
},

{
    "word_values": ["correr"],
    "initial_strings": [
        "Tú ___ muy rápido."
    ],
    "middle_strings": [
        "Choose the correct word to fill in the blank:"
    ],
    "final_strings": [
        "a) corre",
        "b) corres",
        "c) corremos",
        "d) corren"
    ],
    "criteria": "b"
}

]