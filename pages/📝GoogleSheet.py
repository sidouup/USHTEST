import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
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

# Function to load data from Google Sheets
def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    df = pd.DataFrame(data).astype(str)
    df['Months'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce').dt.strftime('%B %Y')  # Create a new column 'Months' for filtering
    return df

# Function to save data to Google Sheets
def save_data(df, spreadsheet_url):
    logger.info("Attempting to save changes")
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        sheet = spreadsheet.sheet1

        # Replace problematic values with a placeholder
        df.replace([np.inf, -np.inf, np.nan], 'NaN', inplace=True)

        # Clear the existing sheet
        sheet.clear()

        # Update the sheet with new data
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False

# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.original_data = st.session_state.data.copy()  # Keep a copy of the original data
    st.session_state.reload_data = False

# Display the editable dataframe
st.title("Student List")

# Filters
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    agents = st.multiselect('Filter by Agent', options=st.session_state.data['Agent'].unique())

with col2:
    months_years = st.multiselect('Filter by Month', options=st.session_state.data['Months'].unique())

with col3:
    stages = st.multiselect('Filter by Stage', options=st.session_state.data['Stage'].unique())

with col4:
    schools = st.multiselect('Filter by Chosen School', options=st.session_state.data['Chosen School'].unique())

with col5:
    attempts = st.multiselect('Filter by Attempts', options=st.session_state.data['Attempts'].unique())

filtered_data = st.session_state.data.copy()

if agents:
    filtered_data = filtered_data[filtered_data['Agent'].isin(agents)]
if months_years:
    filtered_data = filtered_data[filtered_data['Months'].isin(months_years)]
if stages:
    filtered_data = filtered_data[filtered_data['Stage'].isin(stages)]
if schools:
    filtered_data = filtered_data[filtered_data['Chosen School'].isin(schools)]
if attempts:
    filtered_data = filtered_data[filtered_data['Attempts'].isin(attempts)]

# Sort filtered data for display
filtered_data.sort_values(by='DATE', inplace=True)

# Use a key for the data_editor to ensure proper updates
edited_df = st.editor(filtered_data, num_rows="dynamic", key="student_data")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        st.session_state.original_data.update(edited_df)  # Update the original dataset with edited data
        
        if save_data(st.session_state.original_data, spreadsheet_url):
            st.session_state.data = load_data()  # Reload the data to ensure consistency
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
