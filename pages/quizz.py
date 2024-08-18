import streamlit as st
import random
import time

# Sample questions and answers
questions = [
    {
        "question": "Which of the following are programming languages?",
        "options": ["Python", "Java", "HTML", "CSS"],
        "correct_answers": ["Python", "Java"]
    },
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answers": ["Paris"]
    },
    {
        "question": "Which of these are planets in our solar system?",
        "options": ["Earth", "Mars", "Pluto", "Sun"],
        "correct_answers": ["Earth", "Mars", "Pluto"]
    },
    {
        "question": "Which of these are prime numbers?",
        "options": ["2", "3", "4", "6"],
        "correct_answers": ["2", "3"]
    },
    {
        "question": "What are the colors in the French flag?",
        "options": ["Blue", "White", "Red", "Green"],
        "correct_answers": ["Blue", "White", "Red"]
    },
    {
        "question": "Which of these are mammals?",
        "options": ["Dolphin", "Shark", "Elephant", "Crocodile"],
        "correct_answers": ["Dolphin", "Elephant"]
    },
    {
        "question": "Which of these are fruits?",
        "options": ["Tomato", "Carrot", "Banana", "Lettuce"],
        "correct_answers": ["Tomato", "Banana"]
    },
    {
        "question": "Which of these are web browsers?",
        "options": ["Chrome", "Firefox", "Windows", "Safari"],
        "correct_answers": ["Chrome", "Firefox", "Safari"]
    },
    {
        "question": "What is the boiling point of water?",
        "options": ["0°C", "50°C", "100°C", "150°C"],
        "correct_answers": ["100°C"]
    },
    {
        "question": "Which of these are primary colors?",
        "options": ["Red", "Green", "Blue", "Yellow"],
        "correct_answers": ["Red", "Blue", "Yellow"]
    }
]

# Shuffle the questions
random.shuffle(questions)

def run_quiz():
    score = 0

    for i, q in enumerate(questions[:10]):
        st.header(f"Question {i+1}")
        st.write(q["question"])

        selected_options = st.multiselect("Select the correct answers:", q["options"])

        if st.button("Submit", key=i):
            if set(selected_options) == set(q["correct_answers"]):
                score += 2  # Add 2 points for correct answers
                st.success("Correct!")
            else:
                st.error("Incorrect!")
                st.write(f"Correct answers: {', '.join(q['correct_answers'])}")

            time.sleep(1)  # Pause to show feedback

        # Timer
        if st.session_state.get(f"timer_{i}") is None:
            st.session_state[f"timer_{i}"] = 20
        
        timer_placeholder = st.empty()
        while st.session_state[f"timer_{i}"] > 0:
            timer_placeholder.write(f"Time left: {st.session_state['timer_' + str(i)]} seconds")
            time.sleep(1)
            st.session_state[f"timer_{i}"] -= 1
        else:
            timer_placeholder.write("Time is up!")

        st.write("---")

    st.header("Quiz Completed!")
    st.write(f"Your final score is {score} out of 20.")
    if score >= 15:
        st.success("Well done!")
    else:
        st.error("Better luck next time!")

if __name__ == "__main__":
    st.title("Quiz App")
    run_quiz()
