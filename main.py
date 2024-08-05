# File: main.py
import streamlit as st
import base64
from datetime import datetime, timedelta
import json

# Get encryption key from secrets
ENCRYPTION_KEY = st.secrets["encryption_key"]

# Get users from secrets
users = st.secrets["users"]

def encrypt(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

def decrypt(data):
    return json.loads(base64.urlsafe_b64decode(data.encode()).decode())

def login(username, password):
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def init_session_state():
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'role' not in st.session_state:
        st.session_state.role = ''
    if 'expiry' not in st.session_state:
        st.session_state.expiry = None

def check_session():
    if st.session_state.logged_in:
        if st.session_state.expiry and datetime.now() > datetime.fromisoformat(st.session_state.expiry):
            st.session_state.logged_in = False
            st.session_state.username = ''
            st.session_state.role = ''
            st.session_state.expiry = None
            st.warning("Your session has expired. Please log in again.")
        else:
            # Renew session
            st.session_state.expiry = (datetime.now() + timedelta(minutes=30)).isoformat()

def main():
    st.title("Multi-page Streamlit App with Persistent Sessions")

    init_session_state()
    check_session()

    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            role = login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.session_state.expiry = (datetime.now() + timedelta(minutes=30)).isoformat()
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")
    else:
        st.write(f"Welcome, {st.session_state.username}! Your role is: {st.session_state.role}")
        st.write("You can now access other pages based on your role.")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.expiry = None
            st.experimental_rerun()

    # Store session data in local storage
    if st.session_state.logged_in:
        session_data = encrypt({
            "username": st.session_state.username,
            "role": st.session_state.role,
            "expiry": st.session_state.expiry
        })
        st.markdown(
            f"""
            <script>
                localStorage.setItem('session_data', '{session_data}');
                window.onload = function() {{
                    if (window.location.href.indexOf('session=') === -1) {{
                        window.location.href = window.location.href + '?session={session_data}';
                    }}
                }}
            </script>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <script>
                localStorage.removeItem('session_data');
            </script>
            """,
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    # Check for session data in URL parameters or local storage
    query_params = st.experimental_get_query_params()
    if "session" in query_params:
        try:
            session_data = decrypt(query_params["session"][0])
            st.session_state.logged_in = True
            st.session_state.username = session_data["username"]
            st.session_state.role = session_data["role"]
            st.session_state.expiry = session_data["expiry"]
        except:
            st.session_state.logged_in = False
    else:
        st.markdown(
            """
            <script>
                var session_data = localStorage.getItem('session_data');
                if (session_data) {
                    window.location.href = window.location.href + '?session=' + session_data;
                }
            </script>
            """,
            unsafe_allow_html=True
        )
    main()
