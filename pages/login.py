
# login.py
import streamlit as st
from time import sleep
from navigation import make_sidebar

make_sidebar()

st.title("Welcome to Student Visa CRM")

st.write("Please log in to continue (username `admin`, password `password`).")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == "admin" and password == "password":
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("dashboard")
    else:
        st.error("Incorrect username or password")
