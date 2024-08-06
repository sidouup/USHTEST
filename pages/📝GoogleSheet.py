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
    original_df_sorted = original_df.reset_index(drop=True)
    edited_df_sorted = edited_df.reset_index(drop=True)

    # Ensure both DataFrames have the same columns in the same order
    original_df_sorted = original_df_sorted[edited_df_sorted.columns]

    changed_mask = (original_df_sorted != edited_df_sorted).any(axis=1)
    return edited_df_sorted.loc[changed_mask]

# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.reload_data = False

# Always ensure original_data is initialized
if 'original_data' not in st.session_state:
    st.session_state.original_data = st.session_state.data.copy()

# Display the editable dataframe
st.title("Student List")

# Filters
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    agents = st.multiselect('Filter by Agent', options=st.session_state.data['Agent'].unique())

with col2:
    # Create a new column 'Months' for filtering
    st.session_state.data['Months'] = st.session_state.data['DATE'].dt.strftime('%B %Y')
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

# Use a key for the data_editor to ensure proper updates
edited_df = st.data_editor(filtered_data, num_rows="dynamic", key="student_data")

# Function to save data to Google Sheets
def save_data(changed_data, spreadsheet_url):
    logger.info("Attempting to save changes")
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        sheet = spreadsheet.sheet1

        # Convert datetime objects back to strings
        changed_data['DATE'] = changed_data['DATE'].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Replace problematic values with a placeholder
        changed_data.replace([np.inf, -np.inf, np.nan], 'NaN', inplace=True)

        # Batch update the changed rows
        updated_rows = []
        for index, row in changed_data.iterrows():
            updated_rows.append({
                'range': f'A{index + 2}',
                'values': [row.values.tolist()]
            })

        sheet.batch_update(updated_rows)

        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        st.session_state.changed_data = get_changed_rows(st.session_state.original_data, edited_df)  # Store changed data
        
        # Only save data if there are actual changes
        if not st.session_state.changed_data.empty:
            if save_data(st.session_state.changed_data, spreadsheet_url):
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
        else:
            st.info("No changes detected.")
    except Exception as e:
        st.error(f"An error occurred while saving: {str(e)}")
