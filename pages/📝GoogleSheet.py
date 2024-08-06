import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the required scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate with Google Sheets
@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

client = get_gsheet_client()

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit#gid=1019724402"

@st.cache_data
def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    return pd.DataFrame(data).astype(str)

# Load data into a pandas DataFrame and ensure all data is treated as strings
if 'data' not in st.session_state:
    st.session_state.data = load_data()

# Display the editable dataframe
st.title("Student List")
edited_df = st.data_editor(st.session_state.data, num_rows="dynamic")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1
    sheet.clear()
    sheet.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
    st.session_state.data = edited_df  # Update the session state
    st.success("Changes saved successfully!")

# Display the data
st.dataframe(edited_df)
