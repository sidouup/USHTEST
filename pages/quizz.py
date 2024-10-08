import streamlit as st
import streamlit.components.v1 as components
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
</style>
""", unsafe_allow_html=True)

# Sample questions and answers with explanations
questions = [
    {
        "question": "Which of the following are programming languages?",
        "options": ["Python", "Java", "HTML", "CSS"],
        "correct_answers": ["Python", "Java"],
        "explanation": "Python and Java are programming languages. HTML and CSS are used for web development."
    },
    {
        "question": "What is the capital of France?",
        "options": ["Berlin", "Madrid", "Paris", "Rome"],
        "correct_answers": ["Paris"],
        "explanation": "The capital of France is Paris."
    },
    {
        "question": "Which of these are planets in our solar system?",
        "options": ["Earth", "Mars", "Pluto", "Sun"],
        "correct_answers": ["Earth", "Mars"],
        "explanation": "Earth and Mars are planets. The Sun is a star, and Pluto is now considered a dwarf planet."
    },
    {
        "question": "Which of these is a prime number?",
        "options": ["2", "4", "6", "8"],
        "correct_answers": ["2"],
        "explanation": "2 is the only even prime number. The others are not prime numbers."
    },
    {
        "question": "What are the colors in the French flag?",
        "options": ["Blue", "White", "Red", "Green"],
        "correct_answers": ["Blue", "White", "Red"],
        "explanation": "The French flag consists of blue, white, and red colors."
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
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False

def reset_quiz_state():
    st.session_state.current_question = 0
    st.session_state.score = 0
    st.session_state.quiz_started = False
    st.session_state.quiz_completed = False
    st.session_state.selected_answers = []
    st.session_state.questions = random.sample(questions, len(questions))
    st.session_state.user_answers = []
    st.session_state.logged_in = False
    st.session_state.selected_agent = None
    st.session_state.show_result = False
    st.session_state.answer_submitted = False
    if 'start_time' in st.session_state:
        del st.session_state.start_time

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
                st.session_state.quiz_started = True  # Automatically start the quiz after login
                st.rerun()
            except Exception as e:
                st.error(f"Login failed ❌: {str(e)}")

def run_quiz():
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
    
    if not st.session_state.answer_submitted:
        selected_options = []
        for option in q["options"]:
            if st.checkbox(option, key=f"{st.session_state.current_question}_{option}"):
                selected_options.append(option)
        
        # Submit button
        if st.button("Submit", key="submit_button"):
            st.session_state.answer_submitted = True
            st.session_state.selected_answers = selected_options
            st.rerun()
    else:
        # Display selected answers (disabled checkboxes)
        for option in q["options"]:
            st.checkbox(option, value=option in st.session_state.selected_answers, disabled=True, key=f"{st.session_state.current_question}_{option}_disabled")
        
        # Display results and explanation
        check_answer(q, st.session_state.selected_answers)
        display_result(q, st.session_state.selected_answers)
        st.write("Explanation: " + q["explanation"])
        
        # Next Question button
        if st.button("Next Question", key="next_question_button"):
            next_question()
            return

    # Visual timer (only if answer not submitted)
    if not st.session_state.answer_submitted:
        if 'start_time' not in st.session_state:
            st.session_state.start_time = time.time()

        elapsed_time = int(time.time() - st.session_state.start_time)
        remaining_time = max(20 - elapsed_time, 0)

        # Circular timer
        components.html(f"""
        <html>
        <body>
        <div style="display: flex; justify-content: center; align-items: center;">
            <svg height="100" width="100">
              <circle cx="50" cy="50" r="45" stroke="grey" stroke-width="5" fill="none" />
              <circle cx="50" cy="50" r="45" stroke="green" stroke-width="5" fill="none" stroke-dasharray="282.743" stroke-dashoffset="{{282.743 * ({remaining_time} / 20)}}" transform="rotate(-90 50 50)" />
              <text x="50%" y="50%" text-anchor="middle" stroke="black" stroke-width="1px" dy=".3em" font-size="20px">{remaining_time}</text>
            </svg>
        </div>
        </body>
        </html>
        """, height=150)

        if remaining_time == 0:
            st.session_state.answer_submitted = True
            st.session_state.selected_answers = selected_options
            st.rerun()

        time.sleep(0.1)  # Small delay to prevent excessive updates
        st.rerun()


def check_answer(q, selected_options):
    st.session_state.user_answers.append(selected_options)
    if set(selected_options) == set(q["correct_answers"]):
        st.session_state.score += 1

def display_result(q, selected_options):
    for option in q["options"]:
        if option in q["correct_answers"]:
            if option in selected_options:
                st.success(f"✅ {option}")
            else:
                st.warning(f"⭕ {option} (Correct answer you missed)")
        elif option in selected_options:
            st.error(f"❌ {option}")
        else:
            st.text(option)

def next_question():
    st.session_state.current_question += 1
    if 'start_time' in st.session_state:
        del st.session_state.start_time
    st.session_state.answer_submitted = False
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
                        st.success(f"✅ {option}")
                    else:
                        st.error(f"❌ {option}")
                elif option in q["correct_answers"]:
                    st.warning(f"⭕ {option} (Correct answer you missed)")
            st.write(f"Correct answer(s): {', '.join(q['correct_answers'])}")
            st.write(f"Explanation: {q['explanation']}")
    
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
        email_body += f"Explanation: {q['explanation']}\n"

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
    elif st.session_state.quiz_started and not st.session_state.quiz_completed:
        run_quiz()
    elif st.session_state.quiz_completed:
        show_results()

if __name__ == "__main__":
    main()
