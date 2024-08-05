# File: Home.py (main page)
import streamlit as st
import sqlite3
import uuid
from datetime import datetime, timedelta

# Simulated user database with roles and plain text passwords
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
}

# Database setup
conn = sqlite3.connect('sessions.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS sessions
             (session_id TEXT PRIMARY KEY, username TEXT, role TEXT, expiry DATETIME)''')
conn.commit()

def login(username, password):
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def create_session(username, role):
    session_id = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(days=1)
    c.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (session_id, username, role, expiry))
    conn.commit()
    return session_id

def get_session(session_id):
    c.execute("SELECT * FROM sessions WHERE session_id = ? AND expiry > ?", (session_id, datetime.now()))
    return c.fetchone()

def delete_session(session_id):
    c.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()

def main():
    st.title("Multi-page Streamlit App with Server-side Sessions")

    if 'session_id' not in st.session_state:
        st.session_state.session_id = ''

    # Check for existing session
    if st.session_state.session_id:
        session = get_session(st.session_state.session_id)
        if session:
            st.session_state.logged_in = True
            st.session_state.username = session[1]
            st.session_state.role = session[2]
        else:
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.session_id = ""

    if not st.session_state.get('logged_in', False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            role = login(username, password)
            if role:
                session_id = create_session(username, role)
                st.session_state.session_id = session_id
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = role
                st.rerun()
            else:
                st.error("Invalid username or password")
    else:
        st.write(f"Welcome, {st.session_state.username}! Your role is: {st.session_state.role}")
        st.write("You can now access other pages based on your role.")

        if st.button("Logout"):
            delete_session(st.session_state.session_id)
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.session_id = ""
            st.rerun()

if __name__ == "__main__":
    main()
