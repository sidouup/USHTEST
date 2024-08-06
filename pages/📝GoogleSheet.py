import streamlit as st
import pandas as pd
import numpy as np
from google.oauth2.service_account import Credentials
import gspread
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the required scopes
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]

# Authenticate with Google Sheets
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load data from Google Sheets
def load_data(spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data).astype(str)
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y %H:%M:%S', errors='coerce')  # Convert 'DATE' column to datetime
    df['Original_Index'] = df.index  # Track the original index
    return df

# Function to save data to Google Sheets
def save_data(df, original_df, spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = df.where(pd.notnull(df), None)  # Replace NaNs with None for gspread

    # Update only the modified rows in the original dataframe
    for idx, row in df.iterrows():
        for col in df.columns:
            if row[col] != original_df.at[idx, col]:
                sheet.update_cell(idx + 2, df.columns.get_loc(col) + 1, row[col])

# Main function
def main():
    st.title("Student List")

    # Load data from Google Sheets
    spreadsheet_id = "1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew"
    sheet_name = "Sheet1"
    df_all = load_data(spreadsheet_id, sheet_name)
    original_df_all = df_all.copy()  # Keep a copy of the original data

    # Extract month and year for filtering
    df_all['Month'] = df_all['DATE'].dt.strftime('%Y-%m').fillna('Invalid Date')
    months = ["All"] + sorted(df_all['Month'].unique())

    # Define filter options
    current_steps = ["All"] + list(df_all['Stage'].unique())
    agents = ["All"] + list(df_all['Agent'].unique())
    school_options = ["All"] + list(df_all['Chosen School'].unique())
    attempts_options = ["All"] + list(df_all['Attempts'].unique())

    # Filter buttons for stages
    stage_filter = st.selectbox("Filter by Stage", current_steps, key="stage_filter")

    # Filter widgets
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
    with col2:
        school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
    with col3:
        attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")
    with col4:
        month_filter = st.selectbox("Filter by Month", months, key="month_filter")

    # Apply filters
    filtered_data = df_all
    if stage_filter != "All":
        filtered_data = filtered_data[filtered_data['Stage'] == stage_filter]
    if agent_filter != "All":
        filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
    if school_filter != "All":
        filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
    if attempts_filter != "All":
        filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]
    if month_filter != "All":
        filtered_data = filtered_data[filtered_data['Month'] == month_filter]

    # Sort by DATE and reset index
    filtered_data = filtered_data.sort_values(by='DATE').reset_index(drop=True)

    # Keep track of the original indices of the filtered data
    filtered_data = filtered_data.reset_index(drop=False).rename(columns={'index': 'Filtered_Index'})

    # Editable table
    edit_mode = st.checkbox("Edit Mode")
    if edit_mode:
        edited_data = st.data_editor(filtered_data, num_rows="dynamic")
        if st.button("Save Changes"):
            # Ensure the edited DataFrame aligns with the original DataFrame
            edited_df_aligned = original_df_all.copy()
            edited_df_aligned.update(edited_data.drop(['Filtered_Index'], axis=1), overwrite=True)

            # Save the changes
            save_data(edited_df_aligned, original_df_all, spreadsheet_id, sheet_name)
            st.success("Changes saved successfully!")
            st.experimental_rerun()  # Rerun the script to show the updated data
    else:
        st.dataframe(filtered_data)

# Run the main function
if __name__ == "__main__":
    main()
