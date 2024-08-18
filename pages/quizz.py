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

        selected_option = st.radio("Select the correct answer:", q["options"], key=f"q{i}")

        confirm_button = st.button("Confirm", key=f"confirm_{i}")

        timer = 20  # 20 seconds for each question
        timer_placeholder = st.empty()
        progress_bar = st.progress(0)

        while timer > 0:
            progress_bar.progress((20 - timer) / 20)
            time.sleep(1)
            timer -= 1
            timer_placeholder.write(f"Time left: {timer} seconds")
            if confirm_button:
                break

        if confirm_button or timer == 0:
            if selected_option in q["correct_answers"]:
                score += 2  # Add 2 points for correct answers
                st.success(f"Correct! The answer is {selected_option}.")
            else:
                st.error(f"Incorrect! The correct answers are {', '.join(q['correct_answers'])}.")

            time.sleep(2)  # Pause to show feedback before moving to the next question

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
