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
    if 'questions' not in st.session_state:
        st.session_state.questions = random.sample(questions, len(questions))

def welcome_page():
    st.header("Welcome to the Quiz App! 🎓", divider="rainbow")
    
    st.markdown("""
    Test your knowledge on various topics with our interactive quiz!
    
    - 10 questions on different subjects
    - 20 seconds per question
    - Multiple choice and multiple answer questions
    """)
    
    if st.button("Start Quiz", use_container_width=True):
        st.session_state.quiz_started = True
        st.experimental_rerun()
    
    st.header("How to Play", divider="gray")
    st.markdown("""
    1. Click the "Start Quiz" button to begin.
    2. Read each question carefully.
    3. Select the correct answer(s) within the time limit.
    4. Click "Submit" or wait for the timer to run out.
    5. See your results at the end of the quiz.
    
    Good luck!
    """)

def run_quiz():
    st.header(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}", divider="blue")
    
    q = st.session_state.questions[st.session_state.current_question]
    
    # Display progress
    st.progress((st.session_state.current_question) / len(st.session_state.questions))
    
    st.subheader(q["question"])
    
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
    if st.session_state.current_question >= len(st.session_state.questions):
        st.session_state.quiz_started = False
    st.experimental_rerun()

def show_results():
    st.header("Quiz Completed! 🎉", divider="rainbow")
    
    st.subheader(f"Your final score is {st.session_state.score} out of {len(st.session_state.questions)}.")
    
    percentage = (st.session_state.score / len(st.session_state.questions)) * 100
    if percentage >= 80:
        st.success(f"Excellent! You scored {percentage:.2f}%")
    elif percentage >= 60:
        st.info(f"Good job! You scored {percentage:.2f}%")
    else:
        st.warning(f"You scored {percentage:.2f}%. Keep practicing!")
    
    st.header("Performance Breakdown", divider="gray")
    for i, q in enumerate(st.session_state.questions):
        with st.expander(f"Question {i+1}"):
            st.write(q["question"])
            st.write(f"Correct answer(s): {', '.join(q['correct_answers'])}")
    
    if st.button("Restart Quiz", use_container_width=True):
        # Reset quiz state
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.quiz_started = False
        st.session_state.timer = 20
        st.session_state.selected_answers = []
        st.session_state.questions = random.sample(questions, len(questions))
        st.experimental_rerun()

def main():
    st.set_page_config(page_title="Modern Quiz App", page_icon="🧠", layout="centered")
    
    initialize_session_state()
    
    tab1, tab2, tab3 = st.tabs(["Welcome", "Quiz", "Results"])
    
    with tab1:
        welcome_page()
    
    with tab2:
        if st.session_state.quiz_started and st.session_state.current_question < len(st.session_state.questions):
            run_quiz()
        else:
            st.info("Click 'Start Quiz' on the Welcome tab to begin!")
    
    with tab3:
        if not st.session_state.quiz_started and st.session_state.current_question >= len(st.session_state.questions):
            show_results()
        else:
            st.info("Complete the quiz to see your results!")

if __name__ == "__main__":
    main()
