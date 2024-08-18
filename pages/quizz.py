import streamlit as st
import random
import time
from email.message import EmailMessage
import smtplib
import ssl

# Custom CSS for a more appealing look
st.set_page_config(page_title="Enhanced Quiz App", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .stApp {
        max-width: 800px;
        margin: 0 auto;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .stTextInput>div>div>input {
        border-radius: 12px;
    }
    .stSelectbox>div>div>select {
        border-radius: 12px;
    }
    h1, h2, h3 {
        color: #333;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .correct {
        color: green;
        font-weight: bold;
    }
    .incorrect {
        color: red;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Sample questions and answers
questions = [
    {
        "question": "Which of the following are programming languages?",
        "options": ["Python", "Java", "HTML", "CSS"],
        "correct_answers": ["Python", "Java"],
        "multiple": True
    },
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answers": ["Paris"],
        "multiple": False
    },
    {
        "question": "Which of these are planets in our solar system?",
        "options": ["Earth", "Mars", "Pluto", "Sun"],
        "correct_answers": ["Earth", "Mars"],
        "multiple": True
    },
    {
        "question": "Which of these is a prime number?",
        "options": ["2", "4", "6", "8"],
        "correct_answers": ["2"],
        "multiple": False
    },
    {
        "question": "What are the colors in the French flag?",
        "options": ["Blue", "White", "Red", "Green"],
        "correct_answers": ["Blue", "White", "Red"],
        "multiple": True
    },
]

# Agent list
agents = ["Djazila", "Hamza", "Nessrine", "Nada", "Reda"]

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
    if 'show_result' not in st.session_state:
        st.session_state.show_result = False

def reset_quiz_state():
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.quiz_started = False
    st.session_state.quiz_completed = False
    st.session_state.timer = 20
    st.session_state.selected_answers = []
    st.session_state.questions = random.sample(questions, len(questions))
    st.session_state.user_answers = []
    st.session_state.logged_in = False
    st.session_state.selected_agent = None
    st.session_state.show_result = False

def login():
    st.title("Agent Login 🔐")
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        agent = st.selectbox("Select Agent 👤", agents)
        
        if st.button("Login 🚀", key="login_button"):
            try:
                email = st.secrets["Djazila_email"]  # All agents use the same email
                password = st.secrets["Djazila_password"]  # All agents use the same password
                
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                    server.login(email, password)
                
                st.session_state.logged_in = True
                st.session_state.email_address = email
                st.session_state.password = password
                st.session_state.selected_agent = agent
                st.success(f"Login successful for {agent}! 🎉")
                st.info("Quiz results will be sent to: sidouminto@gmail.com")
            except Exception as e:
                st.error(f"Login failed ❌: {str(e)}")

def welcome_and_start():
    st.title(f"Welcome, Agent {st.session_state.selected_agent}! 🎓")
    
    st.markdown("""
    ### Test your knowledge on various topics with our interactive quiz!
    
    - 5 questions on different subjects
    - 20 seconds per question
    - Single and multiple-choice questions
    """)
    
    if st.button("Start Quiz", key="start_quiz_button"):
        st.session_state.quiz_started = True
        st.rerun()

def run_quiz():
    if not st.session_state.quiz_started:
        welcome_and_start()
        return

    if st.session_state.current_question >= len(st.session_state.questions):
        st.session_state.quiz_completed = True
        st.session_state.quiz_started = False
        send_email_results()  # Automatically send results
        st.rerun()
        return

    q = st.session_state.questions[st.session_state.current_question]
    
    st.title(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
    st.progress((st.session_state.current_question) / len(st.session_state.questions))
    
    st.header(q["question"])
    
    if q["multiple"]:
        selected_options = st.multiselect("Select all that apply:", q["options"])
    else:
        selected_option = st.radio("Select one option:", q["options"])
        selected_options = [selected_option] if selected_option else []
    
    if st.button("Submit", key="submit_button"):
        st.session_state.show_result = True
        check_answer(q, selected_options)
    
    if st.session_state.show_result:
        display_result(q, selected_options)
    
    # Visual timer
    progress_bar = st.progress(0)
    timer_text = st.empty()

    while st.session_state.timer > 0 and not st.session_state.show_result:
        progress_bar.progress(1 - (st.session_state.timer / 20))
        timer_text.text(f"Time Remaining: {st.session_state.timer} seconds")
        time.sleep(1)
        st.session_state.timer -= 1
        if st.session_state.timer <= 0:
            st.session_state.show_result = True
            check_answer(q, selected_options)
        st.rerun()

def check_answer(q, selected_options):
    st.session_state.user_answers.append(selected_options)
    if set(selected_options) == set(q["correct_answers"]):
        st.session_state.score += 1

def display_result(q, selected_options):
    for option in q["options"]:
        if option in q["correct_answers"]:
            if option in selected_options:
                st.markdown(f'<p class="correct">✅ {option}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<p class="correct">⭕ {option} (Correct answer you missed)</p>', unsafe_allow_html=True)
        elif option in selected_options:
            st.markdown(f'<p class="incorrect">❌ {option}</p>', unsafe_allow_html=True)
        else:
            st.text(option)
    
    if st.button("Next Question", key="next_question_button"):
        next_question()

def next_question():
    st.session_state.current_question += 1
    st.session_state.timer = 20
    st.session_state.show_result = False
    if st.session_state.current_question >= len(st.session_state.questions):
        st.session_state.quiz_completed = True
        st.session_state.quiz_started = False
        send_email_results()  # Automatically send results
    st.rerun()

def show_results():
    st.title("Quiz Completed! 🎉")
    
    st.header(f"Your final score is {st.session_state.score} out of {len(st.session_state.questions)}.")
    
    percentage = (st.session_state.score / len(st.session_state.questions)) * 100
    if percentage >= 80:
        st.success(f"Excellent! You scored {percentage:.2f}%")
    elif percentage >= 60:
        st.info(f"Good job! You scored {percentage:.2f}%")
    else:
        st.warning(f"You scored {percentage:.2f}%. Keep practicing!")
    
    st.subheader("Performance Breakdown")
    for i, (q, user_answer) in enumerate(zip(st.session_state.questions, st.session_state.user_answers)):
        with st.expander(f"Question {i+1}"):
            st.write(q["question"])
            st.write("Your answer(s):")
            for option in q["options"]:
                if option in user_answer:
                    if option in q["correct_answers"]:
                        st.markdown(f'<p class="correct">✅ {option}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<p class="incorrect">❌ {option}</p>', unsafe_allow_html=True)
                elif option in q["correct_answers"]:
                    st.markdown(f'<p class="correct">⭕ {option} (Correct answer you missed)</p>', unsafe_allow_html=True)
            st.write(f"Correct answer(s): {', '.join(q['correct_answers'])}")
    
    if st.button("Retake Quiz", key="retake_quiz_button"):
        reset_quiz_state()
        st.rerun()

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
        msg['To'] = "sidouminto@gmail.com"  # Always send to this email
        msg['Subject'] = f"Quiz Results for Agent {st.session_state.selected_agent}"
        msg.set_content(email_body)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
            server.login(st.session_state.email_address, st.session_state.password)
            server.send_message(msg)

        st.success(f"Results sent to sidouminto@gmail.com successfully!")
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")

def main():
    initialize_session_state()
    
    if not st.session_state.logged_in:
        login()
    elif not st.session_state.quiz_started and not st.session_state.quiz_completed:
        welcome_and_start()
    elif st.session_state.quiz_started:
        run_quiz()
    elif st.session_state.quiz_completed:
        show_results()

if __name__ == "__main__":
    main()
