import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

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

# Function to load the data from the Google Sheet without caching
def load_data(sheet_url):
    client = get_google_sheet_client()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    headers = data.pop(0)
    return pd.DataFrame(data, columns=headers)

# Function to convert column index to letter
def convert_to_column_letter(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

# Function to update the data in the Google Sheet
def update_data(sheet_url, df, edited_rows):
    client = get_google_sheet_client()
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.get_worksheet(0)
    
    changes = []
    
    for row in edited_rows:
        cell_range = f"A{row+2}:{convert_to_column_letter(len(df.columns))}{row+2}"
        worksheet.update(cell_range, [df.iloc[row].tolist()])
        row_changes = df.iloc[row]
        for col in df.columns:
            if row_changes[col] != data.iloc[row][col]:
                first_name = df.at[row, 'First Name'] if 'First Name' in df.columns else 'N/A'
                last_name = df.at[row, 'Last Name'] if 'Last Name' in df.columns else 'N/A'
                changes.append(f"First Name: {first_name}, Last Name: {last_name}, Column: {col} (Original: {data.iloc[row][col]}, New: {row_changes[col]})")
    
    return changes

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
        st.write("Edited data:", edited_data)
        edited_rows = [i for i, row in edited_data.iterrows() if not row.equals(data.iloc[i])]
        st.write("Edited rows:", edited_rows)
        if edited_rows:
            try:
                with st.spinner('Saving changes...'):
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            changes = update_data(sheet_url, edited_data, edited_rows)
                            st.success("Changes saved successfully!")
                            st.write("Modified cells:")
                            for change in changes:
                                st.write(change)
                            break
                        except Exception as e:
                            if attempt < max_retries - 1:
                                time.sleep(1)  # Wait before retrying
                                continue
                            else:
                                st.error(f"An error occurred: {e}")
            except Exception as e:
                st.error(f"An error occurred: {e}")
else:
    st.dataframe(data)
