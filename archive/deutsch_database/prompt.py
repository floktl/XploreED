EXERCISE_TYPE = "translation"
EXERCISE_TEXT = "The dog is blue"
EXERCISE_ANSWER = "Der Hund sein blau"
LIST_OF_LESSONS = "Preposition, Sentence structure, Present"

PROMPT = f""" 
    The student did this lessons: {LIST_OF_LESSONS}
    
    Execise_type = {EXERCISE_TYPE}
    Exercise_text = {EXERCISE_TEXT}
    Answer = {EXERCISE_ANSWER}

    Please evaluate the Answer given for the Exercise Text
    return me a Json that contains this parameters:
    
    Grammar: A value 0 to 5 based on the SM2 Quality Factor
"""