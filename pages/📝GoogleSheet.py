import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the required scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate with Google Sheets
def get_gsheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

client = get_gsheet_client()

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit#gid=1019724402"

def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    df = pd.DataFrame(data).astype(str)
    df['DATE'] = pd.to_datetime(df['DATE'], format="%d/%m/%Y %H:%M:%S")
    df.sort_values(by='DATE', inplace=True)
    return df

# Function to get changed rows
def get_changed_rows(original_df, edited_df):
    original_df = original_df.reset_index(drop=True)
    edited_df = edited_df.reset_index(drop=True)
    
    if original_df.shape != edited_df.shape:
        return edited_df  # If shapes are different, consider all rows as changed
    
    changed_mask = (original_df != edited_df).any(axis=1)
    return edited_df[changed_mask]

# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.reload_data = False

# Always ensure original_data is initialized
if 'original_data' not in st.session_state:
    st.session_state.original_data = st.session_state.data.copy()

# Display the editable dataframe
st.title("Student List")

# Use a key for the data_editor to ensure proper updates
edited_df = st.data_editor(st.session_state.data, num_rows="dynamic", key="student_data")

# Sort the edited dataframe by DATE
edited_df['DATE'] = pd.to_datetime(edited_df['DATE'], format="%d/%m/%Y %H:%M:%S")
edited_df.sort_values(by='DATE', inplace=True)

# Function to save data to Google Sheets
def save_data(df, spreadsheet_url):
    logger.info("Attempting to save changes")
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        sheet = spreadsheet.sheet1
        sheet.clear()
        sheet.update([df.columns.values.tolist()] + df.values.tolist())
        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        st.session_state.changed_data = get_changed_rows(st.session_state.original_data, edited_df)  # Store changed data

        # Sort the changed data frame by DATE
        st.session_state.changed_data['DATE'] = pd.to_datetime(st.session_state.changed_data['DATE'], format="%d/%m/%Y %H:%M:%S")
        st.session_state.changed_data.sort_values(by='DATE', inplace=True)

        if save_data(edited_df, spreadsheet_url):
            st.session_state.data = edited_df  # Update the session state
            st.session_state.original_data = edited_df.copy()  # Update the original data
            st.success("Changes saved successfully!")

            # Use a spinner while waiting for changes to propagate
            with st.spinner("Refreshing data..."):
                time.sleep(2)  # Wait for 2 seconds to allow changes to propagate

            st.session_state.reload_data = True
            st.rerun()
        else:
            st.error("Failed to save changes. Please try again.")
    except Exception as e:
        st.error(f"An error occurred while saving: {str(e)}")

# Display the current state of the data
st.subheader("All Students:")
st.dataframe(st.session_state.data)

# Display only the changed students
changed_df = get_changed_rows(st.session_state.original_data, edited_df)
st.subheader("Changed Students:")
if not changed_df.empty:
    st.dataframe(changed_df)
else:
    st.info("No changes detected.")
