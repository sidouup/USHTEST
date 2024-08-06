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

def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    df = pd.DataFrame(data).astype(str)
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')  # Convert DATE to datetime with dayfirst=True
    return df

# Function to get changed rows
def get_changed_rows(original_df, edited_df):
    # Ensure both DataFrames have the same index
    original_df = original_df.reset_index(drop=True)
    edited_df = edited_df.reset_index(drop=True)

    # Ensure both DataFrames have the same columns in the same order
    columns = list(original_df.columns)
    original_df = original_df[columns]
    edited_df = edited_df[columns]

    changed_mask = (original_df != edited_df).any(axis=1)
    return edited_df.loc[changed_mask]

# ... [rest of the code remains unchanged] ...

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        # Ensure both DataFrames have the same structure before comparison
        original_data = st.session_state.original_data.copy()
        edited_df_copy = edited_df.copy()

        # Reset index and align columns
        original_data = original_data.reset_index(drop=True)
        edited_df_copy = edited_df_copy.reset_index(drop=True)

        # Ensure both DataFrames have the same columns in the same order
        columns = list(original_data.columns)
        original_data = original_data[columns]
        edited_df_copy = edited_df_copy[columns]

        st.session_state.changed_data = get_changed_rows(original_data, edited_df_copy)
        
        # Only save data if there are actual changes
        if not st.session_state.changed_data.empty:
            if save_data(st.session_state.changed_data, spreadsheet_url):
                st.session_state.data = edited_df_copy  # Update the session state
                st.session_state.original_data = edited_df_copy.copy()  # Update the original data
                st.success("Changes saved successfully!")
                
                # Use a spinner while waiting for changes to propagate
                with st.spinner("Refreshing data..."):
                    time.sleep(2)  # Wait for 2 seconds to allow changes to propagate
                
                st.session_state.reload_data = True
                st.rerun()
            else:
                st.error("Failed to save changes. Please try again.")
        else:
            st.info("No changes detected.")
    except Exception as e:
        st.error(f"An error occurred while saving: {str(e)}")
        logging.error(f"Error details: {e}", exc_info=True)
