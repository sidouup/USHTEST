# File: Home.py (main page)
import streamlit as st

# Simulated user database with roles and plain text passwords
users = {
    "admin": {"password": "admin", "role": "admin"},
    "user": {"password": "user", "role": "user"},
}

def login(username, password):
    if username in users and users[username]["password"] == password:
        return users[username]["role"]
    return None

def main():
    st.title("Multi-page Streamlit App with Simple Login")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""

    if not st.session_state.logged_in:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            role = login(username, password)
            if role:
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
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.role = ""
            st.rerun()

if __name__ == "__main__":
    main()

