import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# Page configuration
st.set_page_config(page_title="Student List", layout="wide")

# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Authenticate with Google Sheets
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
client = gspread.authorize(creds)

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit#gid=1019724402"
spreadsheet = client.open_by_url(spreadsheet_url)
sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet

# Load data into a pandas DataFrame
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Display the editable dataframe
st.title("Student List")
edited_df = st.experimental_data_editor(df, num_rows="dynamic")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    sheet.clear()
    sheet.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())
    st.success("Changes saved successfully!")

# Display the data
st.dataframe(edited_df)
