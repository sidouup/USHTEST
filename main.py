# streamlit_app.py
import streamlit as st
from navigation import make_sidebar

# Ensure the sidebar is present on all pages
make_sidebar()

# Set up session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Redirect to login page if not logged in
if not st.session_state.logged_in:
    st.switch_page("login.py")
else:
    st.title("Welcome to Student Visa CRM")
    st.write("Use the sidebar to navigate.")
