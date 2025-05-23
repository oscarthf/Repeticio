
start_prompt = """
You are a leading expert in foreign language education, specializing in creating engaging and effective exercises for language learners.
You are on a team of experts who are creating a language learning app.
Create a multiple-choice exercise for a [TARGET LANGUAGE] course at the CEFR language level [TARGET LEVEL].
Your questions will be rated later by users, so make sure they are clear, engaging, and appropriate for the level.
Each question uses either one or two words from the vocabulary list provided by the user.
This exercise will use the following ONE word: [TARGET WORDS].

Instructions:
- Write a sentence with ONE BLANK ( ___ ) where the correct word should go.
- Make sure you use the word porvided above.
- Include a short instruction: "Choose the correct word to fill in the blank:"
- Provide 3 to 5 answer choices, (a, b, c, d, e).
- Please ensure that ONE AND ONLY ONE answer is correct (this is the hardest part!).
- Output ONLY a JSON object following this format:

{
    "initial_strings": [sentence with blank],
    "middle_strings": [instruction line],
    "final_strings": [list of answer choices],
    "criteria": [correct answer (example: "c")]
}

Here are 3 examples (may not be in [TARGET LANGUAGE], but follow the same format):
"""

inspiration_exercises = [# MUST HAVE AT LEAST 3 TO START!!!

{
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
    "criteria": ["a"]
}, 

{
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
    "criteria": ["e"]
},

{
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
    "criteria": ["b"]
}

]