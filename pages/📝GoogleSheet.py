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
    return pd.DataFrame(data).astype(str)

# Function to get changed rows
def get_changed_rows(original_df, edited_df):
    if original_df.shape != edited_df.shape:
        return edited_df  # If shapes are different, consider all rows as changed
    
    changed_mask = (original_df != edited_df).any(axis=1)
    return edited_df[changed_mask]

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

# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.reload_data = False

# Always ensure original_data is initialized
if 'original_data' not in st.session_state:
    st.session_state.original_data = st.session_state.data.copy()

# Extract month and year for filtering
st.session_state.data['DATE'] = pd.to_datetime(st.session_state.data['DATE'], errors='coerce')
st.session_state.data['Month'] = st.session_state.data['DATE'].dt.strftime('%Y-%m').fillna('Invalid Date')
months = ["All"] + sorted(st.session_state.data['Month'].unique())

# Define filter options
current_steps = ["All"] + list(st.session_state.data['Stage'].unique())
agents = ["All", "Nesrine", "Hamza", "Djazila", "Nada"]
school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English", "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston", "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
attempts_options = ["All", "1 st Try", "2 nd Try", "3 rd Try"]

# Standardize colors for agents
agent_colors = {
    "Nesrine": "background-color: #FF00FF",  # Light lavender
    "Hamza": "background-color: yellow",
    "Djazila": "background-color: red"
}

# Sidebar for agent color reference
st.sidebar.header("Agent Color Reference")
for agent, color in agent_colors.items():
    st.sidebar.markdown(f"<div style='{color};padding: 5px;'>{agent}</div>", unsafe_allow_html=True)

# Filter widgets
col1, col2, col3, col4 = st.columns(4)
with col1:
    stage_filter = st.selectbox("Filter by Stage", current_steps, key="stage_filter")
with col2:
    agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
with col3:
    school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
with col4:
    attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")
with col1:
    month_filter = st.selectbox("Filter by Month", months, key="month_filter")

# Apply filters
filtered_data = st.session_state.data
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

# Function to apply colors
def highlight_agent(row):
    agent = row['Agent']
    return [agent_colors.get(agent, '')] * len(row)

# Editable table
st.title("Student List")
edited_df = st.data_editor(filtered_data, num_rows="dynamic", key="student_data")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        st.session_state.changed_data = get_changed_rows(st.session_state.original_data, edited_df)  # Store changed data
        
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

# Function to highlight changed rows
def highlight_changes(row):
    return ['background-color: yellow' if row.name in changed_rows else '' for _ in row]

# Highlight changed rows
changed_rows = st.session_state.changed_data.index if 'changed_data' in st.session_state else []

# Apply styling and display the dataframe
styled_df = edited_df.style.apply(highlight_agent, axis=1).apply(highlight_changes, axis=1)
st.dataframe(styled_df)
