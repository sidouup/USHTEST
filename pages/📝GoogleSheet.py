import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load the data from the Google Sheet
@st.cache
def load_data(sheet_url):
    client = get_google_sheet_client()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    headers = data.pop(0)
    return pd.DataFrame(data, columns=headers)

# Function to update the data in the Google Sheet
def update_data(sheet_url, df, edited_rows):
    client = get_google_sheet_client()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    for row in edited_rows:
        cell_range = f"A{row+2}:{chr(65 + len(df.columns) - 1)}{row+2}"
        worksheet.update(cell_range, [df.iloc[row].tolist()])

# Load the data
sheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit?gid=1019724402#gid=1019724402"  # Replace with your Google Sheet URL
data = load_data(sheet_url)

# Display the data
st.title("Student List")
st.write("Below is the current data from the Google Sheet:")

# Edit mode
if 'edit_mode' not in st.session_state:
    st.session_state['edit_mode'] = False

def toggle_edit_mode():
    st.session_state['edit_mode'] = not st.session_state['edit_mode']

st.button("Toggle Edit Mode", on_click=toggle_edit_mode)

if st.session_state['edit_mode']:
    edited_data = st.data_editor(data, num_rows="fixed", use_container_width=True)
    if st.button("Save Changes"):
        edited_rows = [i for i, row in edited_data.iterrows() if not row.equals(data.iloc[i])]
        if edited_rows:
            try:
                update_data(sheet_url, edited_data, edited_rows)
                st.success("Changes saved successfully!")
            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    st.dataframe(data)
