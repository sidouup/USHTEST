import streamlit as st
import random
import time
from email.message import EmailMessage
import smtplib
import ssl
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
    # ... (other questions)
]

# Agent email mapping using Streamlit secrets
agents = {
    "Djazila": st.secrets["Djazila_email"],
    "Hamza": st.secrets["Hamza_email"],
    "Nessrine": st.secrets["Nessrine_email"],
    "Nada": st.secrets["Nada_email"],
    "Reda": st.secrets["Reda_email"]
}

import streamlit as st
import random
import time
from email.message import EmailMessage
import smtplib
import ssl

# Sample questions and answers (same as before)
questions = [
    # ... (previous questions)
]

# Agent email mapping using Streamlit secrets (same as before)
agents = {
    # ... (previous agent mappings)
}

def initialize_session_state():
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'timer' not in st.session_state:
        st.session_state.timer = 20
    if 'selected_answers' not in st.session_state:
        st.session_state.selected_answers = []
    if 'questions' not in st.session_state:
        st.session_state.questions = random.sample(questions, len(questions))
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []
    if 'selected_agent' not in st.session_state:
        st.session_state.selected_agent = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def reset_quiz_state():
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.quiz_started = False
    st.session_state.quiz_completed = False
    st.session_state.timer = 20
    st.session_state.selected_answers = []
    st.session_state.questions = random.sample(questions, len(questions))
    st.session_state.user_answers = []

@st.cache_resource
def get_timer():
    return st.empty()

def login():
    st.sidebar.title("Agent Login 🔐")
    agent = st.sidebar.selectbox("Select Agent 👤", list(agents.keys()))
    email_address = agents[agent]
    password = st.secrets[f"{agent}_password"]
    
    if st.sidebar.button("Login 🚀"):
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                server.login(email_address, password)
            st.session_state.logged_in = True
            st.session_state.email_address = email_address
            st.session_state.password = password
            st.session_state.selected_agent = agent
            st.sidebar.success("Login successful! 🎉")
        except Exception as e:
            st.sidebar.error(f"Login failed ❌: {str(e)}")

def welcome_and_start():
    st.header(f"Welcome, Agent {st.session_state.selected_agent}! 🎓", divider="rainbow")
    
    st.markdown("""
    Test your knowledge on various topics with our interactive quiz!
    
    - 10 questions on different subjects
    - 20 seconds per question
    - Multiple choice and multiple answer questions
    """)
    
    if st.button("Start Quiz", use_container_width=True):
        reset_quiz_state()
        st.session_state.quiz_started = True
        st.rerun()

def run_quiz():
    if not st.session_state.quiz_started:
        welcome_and_start()
        return

    if st.session_state.current_question >= len(st.session_state.questions):
        st.session_state.quiz_completed = True
        st.session_state.quiz_started = False
        st.rerun()
        return

    q = st.session_state.questions[st.session_state.current_question]
    
    st.header(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}", divider="blue")
    st.progress((st.session_state.current_question) / len(st.session_state.questions))
    
    st.subheader(q["question"])
    
    st.session_state.selected_answers = []
    for option in q["options"]:
        if st.checkbox(option, key=f"{st.session_state.current_question}_{option}"):
            st.session_state.selected_answers.append(option)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit", use_container_width=True):
            check_answer(q)
    with col2:
        if st.button("Skip", use_container_width=True):
            next_question()
    
    timer_placeholder = get_timer()
    timer_placeholder.metric("Time Remaining", f"{st.session_state.timer} seconds")

    # Timer update
    if st.session_state.timer > 0:
        time.sleep(1)
        st.session_state.timer -= 1
        if st.session_state.timer <= 0:
            check_answer(q)
        st.rerun()

def check_answer(q):
    st.session_state.user_answers.append(st.session_state.selected_answers)
    if set(st.session_state.selected_answers) == set(q["correct_answers"]):
        st.session_state.score += 1
    next_question()

def next_question():
    st.session_state.current_question += 1
    st.session_state.timer = 20
    if st.session_state.current_question >= len(st.session_state.questions):
        st.session_state.quiz_completed = True
        st.session_state.quiz_started = False
    st.rerun()

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
    for i, (q, user_answer) in enumerate(zip(st.session_state.questions, st.session_state.user_answers)):
        with st.expander(f"Question {i+1}"):
            st.write(q["question"])
            st.write("Your answer(s):")
            for option in q["options"]:
                if option in user_answer:
                    if option in q["correct_answers"]:
                        st.markdown(f"✅ <span style='color:green'>{option}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"❌ <span style='color:red'>{option}</span>", unsafe_allow_html=True)
                elif option in q["correct_answers"]:
                    st.markdown(f"⭕ <span style='color:orange'>{option}</span> (Correct answer you missed)", unsafe_allow_html=True)
            st.write(f"Correct answer(s): {', '.join(q['correct_answers'])}")
    
    if st.button("Retake Quiz", use_container_width=True):
        reset_quiz_state()
        st.rerun()
    
    if st.button("Send Results to Email", use_container_width=True):
        send_email_results()

def send_email_results():
    email_body = f"""
    Quiz Results for Agent {st.session_state.selected_agent}

    Final Score: {st.session_state.score} out of {len(st.session_state.questions)}
    Percentage: {(st.session_state.score / len(st.session_state.questions)) * 100:.2f}%

    Performance Breakdown:
    """

    for i, (q, user_answer) in enumerate(zip(st.session_state.questions, st.session_state.user_answers)):
        email_body += f"\nQuestion {i+1}: {q['question']}\n"
        email_body += f"Your answer(s): {', '.join(user_answer)}\n"
        email_body += f"Correct answer(s): {', '.join(q['correct_answers'])}\n"

    try:
        msg = EmailMessage()
        msg['From'] = st.session_state.email_address
        msg['To'] = "sidouminto@gmail.com"  # The email to send results to
        msg['Subject'] = f"Quiz Results for Agent {st.session_state.selected_agent}"
        msg.set_content(email_body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
            server.login(st.session_state.email_address, st.session_state.password)
            server.send_message(msg)

        st.success("Results sent to email successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")

def main():
    st.set_page_config(page_title="Enhanced Quiz App", page_icon="🧠", layout="centered")
    
    initialize_session_state()
    
    login()
    
    if st.session_state.logged_in:
        quiz_tab, results_tab = st.tabs(["Quiz", "Results"])
        
        with quiz_tab:
            if not st.session_state.quiz_completed:
                run_quiz()
            else:
                welcome_and_start()
        
        with results_tab:
            if st.session_state.quiz_completed:
                show_results()
            else:
                st.info("Complete the quiz to see your results!")
    else:
        st.warning("Please log in to start the quiz.")

if __name__ == "__main__":
    main()

