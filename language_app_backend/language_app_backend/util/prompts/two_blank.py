
start_prompt = """
Create a multiple-choice exercise for a [TARGET LANGUAGE] course at [TARGET LEVEL] 
using the following word: [TARGET WORDS].

Instructions:
- Write a sentence with TWO BLANKS ( ___ ... ___ ) where the correct word should go.
- Make sure you use BOTH words provided above.
- Include a short instruction: "Choose the correct word to fill in the blanks:"
- Provide 3 to 5 answer choices, (a, b, c, d, e).
- Output ONLY a JSON object following this format:

{
    "word_values": [list of key words (to verify you used the correct ones)],
    "initial_strings": [sentence with blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": [correct answer (example: "c")]
}

Here are 3 examples:
"""

inspiration_exercises = [# MUST HAVE AT LEAST 3 TO START!!!
{
    "word_values": ["muy", "feliz"],
    "initial_strings": [
        "Hoy me siento ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) algo / cansado",
        "b) muy / feliz",
        "c) un / poco",
        "d) muy / ocupado"
    ],
    "criteria": "b"
},

{
    "word_values": ["muy", "rápido"],
    "initial_strings": [
        "El tren va ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) poco / temprano",
        "b) bastante / lento",
        "c) muy / rápido",
        "d) demasiado / tarde"
    ],
    "criteria": "c"
},

{
    "word_values": ["muy", "caliente"],
    "initial_strings": [
        "El café está ___ ___"
    ],
    "middle_strings": [
        "Choose the correct ending words:"
    ],
    "final_strings": [
        "a) algo / frío",
        "b) un / poco",
        "c) bastante / dulce"
        "d) muy / caliente",
    ],
    "criteria": "d"
}

]