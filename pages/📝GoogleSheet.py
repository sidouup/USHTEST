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
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit#gid=1019724402"
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet

# Load data into a pandas DataFrame and ensure all data is treated as strings
data = sheet.get_all_records()
df = pd.DataFrame(data).astype(str)

# Display the editable dataframe
st.title("Student List")
edited_df = st.data_editor(df, num_rows="dynamic")

# Function to find changed rows
def find_changed_rows(original_df, edited_df):
    return edited_df[(original_df != edited_df).any(axis=1)]

# Initialize a session state variable to hold the edited data
if "edited_df" not in st.session_state:
    st.session_state.edited_df = df

# Update session state with the latest edited DataFrame
st.session_state.edited_df = edited_df

# Update Google Sheet with edited data and show changed rows
if st.button("Save Changes"):
    sheet.clear()
    sheet.update([st.session_state.edited_df.columns.values.tolist()] + st.session_state.edited_df.values.tolist())
    st.success("Changes saved successfully!")
    
    # Find and display the changed rows
    changed_rows_df = find_changed_rows(df, st.session_state.edited_df)
    if not changed_rows_df.empty:
        st.subheader("Changed Rows")
        st.dataframe(changed_rows_df)
    else:
        st.write("No changes detected.")
