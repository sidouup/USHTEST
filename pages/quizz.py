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
        "correct_answers": ["Earth", "Mars"]
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

def initialize_session_state():
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'timer' not in st.session_state:
        st.session_state.timer = 20
    if 'selected_answers' not in st.session_state:
        st.session_state.selected_answers = []

def reset_quiz():
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.quiz_started = False
    st.session_state.timer = 20
    st.session_state.selected_answers = []
    random.shuffle(questions)

def start_page():
    st.title("Welcome to the Quiz App!")
    colored_header(label="Test Your Knowledge", description="Are you ready to challenge yourself?", color_name="blue-70")
    add_vertical_space(2)
    if st.button("Start Quiz", use_container_width=True):
        st.session_state.quiz_started = True

def run_quiz():
    q = questions[st.session_state.current_question]
    
    # Display progress
    st.progress((st.session_state.current_question) / len(questions))
    
    colored_header(label=f"Question {st.session_state.current_question + 1} of {len(questions)}", description=q["question"], color_name="blue-70")
    
    # Display options as checkboxes
    st.session_state.selected_answers = []
    for option in q["options"]:
        if st.checkbox(option, key=option):
            st.session_state.selected_answers.append(option)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit", use_container_width=True):
            check_answer(q)
    with col2:
        if st.button("Skip", use_container_width=True):
            next_question()
    
    # Timer
    if 'timer' not in st.session_state:
        st.session_state.timer = 20
    
    timer_placeholder = st.empty()
    
    while st.session_state.timer > 0:
        timer_placeholder.metric("Time Remaining", f"{st.session_state.timer} seconds")
        time.sleep(1)
        st.session_state.timer -= 1
        if st.session_state.timer == 0:
            check_answer(q)
        st.experimental_rerun()

def check_answer(q):
    if set(st.session_state.selected_answers) == set(q["correct_answers"]):
        st.success("Correct!")
        st.session_state.score += 1
    else:
        st.error(f"Incorrect. The correct answer(s) were: {', '.join(q['correct_answers'])}")
    
    next_question()

def next_question():
    st.session_state.current_question += 1
    st.session_state.timer = 20
    if st.session_state.current_question >= len(questions):
        show_results()
    else:
        st.experimental_rerun()

def show_results():
    st.title("Quiz Completed!")
    st.write(f"Your final score is {st.session_state.score} out of {len(questions)}.")
    
    percentage = (st.session_state.score / len(questions)) * 100
    if percentage >= 80:
        st.success(f"Excellent! You scored {percentage:.2f}%")
    elif percentage >= 60:
        st.info(f"Good job! You scored {percentage:.2f}%")
    else:
        st.warning(f"You scored {percentage:.2f}%. Keep practicing!")
    
    if st.button("Restart Quiz", use_container_width=True):
        reset_quiz()
        st.experimental_rerun()

def main():
    st.set_page_config(page_title="Modern Quiz App", page_icon="🧠", layout="centered")
    
    initialize_session_state()
    
    if not st.session_state.quiz_started:
        start_page()
    elif st.session_state.current_question < len(questions):
        run_quiz()
    else:
        show_results()

if __name__ == "__main__":
    main()
