
import streamlit as st
from streamlit_option_menu import option_menu

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Login", page_icon="🔒", layout="centered")

# --- AUTHENTICATION LOGIC ---
def check_credentials(username, password):
    if username == st.secrets["admin_username"] and password == st.secrets["admin_password"]:
        return "admin"
    elif username == st.secrets["user_username"] and password == st.secrets["user_password"]:
        return "user"
    else:
        return None

# --- LOGIN FORM ---
if "logged_in" not in st.session_state:  # Check if user is already logged in
    with st.form("login_form"):
        st.markdown("<h2 style='text-align: center;'>Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")

    # Check credentials
    if submit_button:
        role = check_credentials(username, password)
        if role:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.session_state["role"] = role
            st.success("Logged in as {}".format(role))
            st.rerun()  # Refresh the page after successful login
        else:
            st.error("Invalid username or password")
else:  # --- APP CONTENT ---
    # Option menu based on user role
    role = st.session_state["role"]
    if role == "admin":  # Admin has access to all pages
        with st.sidebar:
            selected = option_menu("Main Menu", ["Home", "Analytics", "Settings"], 
                icons=['house', 'graph-up-arrow', 'gear'], menu_icon="cast", default_index=0)
            
else:  # --- APP CONTENT ---
    with st.sidebar:
        role = st.session_state["role"]
        if role == "admin":
            selected = option_menu("Main Menu", ["Home", "Analytics", "Settings"],
                icons=['house', 'graph-up-arrow', 'gear'], menu_icon="cast", default_index=0)
        elif role == "user":
            selected = option_menu("Main Menu", ["Home", "Profile"], 
                icons=['house', 'person'], menu_icon="cast", default_index=0)

    # Display the selected page
    if selected == "Home":
        pages.main.app()  # Call the app() function of the selected page
    elif selected == "Analytics" and role == "admin":
        pages.📊Statistics.py.app()
    elif selected == "Settings" and role == "admin":
        pages.📝GoogleSheet.app()
    elif selected == "Profile":
        pages.🚨Emergency.app()

    # Logout button
    st.sidebar.button("Logout", on_click=lambda: st.session_state.clear()) 
