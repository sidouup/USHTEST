import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from difflib import get_close_matches
import math

# Use your service account info from Streamlit secrets
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the scopes
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate and build the Google Sheets service
@st.cache_resource
def get_google_sheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

# Function to load data from Google Sheets
@st.cache_data
def load_data(spreadsheet_id, sheet_name):
    client = get_google_sheet_client()
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Clean Tuition Price and Application Fee Price columns
    df['Tuition Price'] = pd.to_numeric(df['Tuition Price'], errors='coerce')
    df['Application Fee Price'] = pd.to_numeric(df['Application Fee Price'], errors='coerce')
    
    return df

# Function to implement fuzzy matching
def fuzzy_search(term, options):
    matches = get_close_matches(term.lower(), options, n=5, cutoff=0.3)
    return matches

def main():
    st.set_page_config(layout="wide", page_title="University Search Tool")
    
    # Updated Custom CSS for styling
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    body {
        font-family: 'Roboto', sans-serif;
        background-color: #ffffff;
        color: #333333;
    }
    
    .stApp {
        background-color: #ffffff;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
        padding: 10px;
    }
    
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 200px !important;
    }
    
    .stSelectbox, .stMultiSelect, .stSlider {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 5px;
        margin-bottom: 10px;
    }
    
    .university-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        height: 100%;  /* Allow height to adjust based on content */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .university-card:hover {
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .university-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .university-logo {
        width: 50px;
        height: 50px;
        margin-right: 10px;
        object-fit: contain;
    }
    
    .university-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #333333;
        flex-grow: 1;
        text-align: center; /* Center-align the text */
    }
    
    .speciality-name {
        font-size: 1rem;
        margin-bottom: 15px;
        color: #555555;
        height: auto;  /* Allow dynamic height */
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        -webkit-box-orient: vertical;
        text-align: center; /* Center-align the text */
    }
    
    .info-container {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 0.9rem; /* Slightly smaller text for info rows */
    }
    
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 0.85rem;
        color: #666666;
    }
    
    .create-application-btn {
        background-color: #1e88e5;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 1rem;
        margin-top: 10px;
        transition: background-color 0.3s ease;
        text-align: center;
    }
    
    .create-application-btn:hover {
        background-color: #1565c0;
    }
    
    .prime-tags {
        margin-bottom: 10px;
        display: flex;
        flex-wrap: wrap; /* Allow tags to wrap in smaller spaces */
        justify-content: center; /* Center-align the tags */
    }
    
    .prime-tag {
        background-color: #ffd700;
        color: #333333;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.75rem;
        margin-right: 3px;
        margin-bottom: 3px;
        display: inline-block;
    }
    
    .stButton > button {
        background-color: #1e88e5;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 1rem;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1565c0;
    }
    
    .pagination {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    
    .page-info {
        margin: 0 10px;
        font-size: 1rem;
    }
    
    h1, h2, h3 {
        text-align: center; /* Center-align headings */
        font-weight: bold;
        text-decoration: underline; /* Underline headings */
    }
    </style>
    """, unsafe_allow_html=True)

    # Replace with your Google Sheet ID and sheet name
    SPREADSHEET_ID = "1gCxnCOhQRHtVdVMSiLaReBRJbCUz1Wn6-KJRZshneuM"
    SHEET_NAME = "cleaned_universities_data"

    # Load the data
    df = load_data(SPREADSHEET_ID, SHEET_NAME)

    # Sidebar for filters
    sidebar_col, main_col = st.columns([1, 5])

    # Sidebar for filters
    with sidebar_col:
        st.sidebar.title("Filters")
        
        location = st.sidebar.selectbox("Location", ["All"] + sorted(df['Country'].unique().tolist()))
        program_level = st.sidebar.selectbox("Program level", ["All"] + sorted(df['Level'].unique().tolist()))
        field_of_study = st.sidebar.selectbox("Field of study", ["All"] + sorted(df['Field'].unique().tolist()))
        
        tuition_min, tuition_max = st.sidebar.slider(
            "Tuition fee range",
            min_value=int(df['Tuition Price'].min()),
            max_value=int(df['Tuition Price'].max()),
            value=(int(df['Tuition Price'].min()), int(df['Tuition Price'].max()))
        )
        
        apply_filters = st.sidebar.button("Apply filters")

    # Main content area
    with main_col:
        st.title("University Search Tool")

        # Search bar
        search_term = st.text_input("Search for Universities or Specialities")

        # Apply filters
        if apply_filters or search_term:
            filtered_df = df.copy()
            
            if search_term:
                university_matches = fuzzy_search(search_term, filtered_df['University Name'].str.lower())
                speciality_matches = fuzzy_search(search_term, filtered_df['Adjusted Speciality'].str.lower())
                filtered_df = filtered_df[filtered_df['University Name'].str.lower().isin(university_matches) |
                                          filtered_df['Adjusted Speciality'].str.lower().isin(speciality_matches)]
            
            if location != "All":
                filtered_df = filtered_df[filtered_df['Country'] == location]
            
            if program_level != "All":
                filtered_df = filtered_df[filtered_df['Level'] == program_level]
            
            if field_of_study != "All":
                filtered_df = filtered_df[filtered_df['Field'] == field_of_study]
            
            filtered_df = filtered_df[(filtered_df['Tuition Price'] >= tuition_min) & (filtered_df['Tuition Price'] <= tuition_max)]
        else:
            filtered_df = df

        # Pagination
        items_per_page = 16  # Changed to 16 for 4x4 grid
        total_pages = math.ceil(len(filtered_df) / items_per_page)
        
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page

        # Display results
    st.subheader(f"Showing {len(filtered_df)} results")
    
    # Create four columns for displaying university cards
    for i in range(0, min(items_per_page, len(filtered_df) - start_idx), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(filtered_df[start_idx:end_idx]):
                row = filtered_df.iloc[start_idx + i + j]
                with cols[j]:
                    prime_tags = [row[f'prime {k}'] for k in range(2, 6) if pd.notna(row[f'prime {k}'])]
                    prime_tags_html = ''.join([f'<span class="prime-tag">{tag}</span>' for tag in prime_tags])
                    
                    st.markdown(f'''
                    <div class="university-card">
                        <div class="university-header">
                            <img src="{row['Picture']}" class="university-logo" alt="{row['University Name']} logo">
                            <div class="university-name">{row['University Name']}</div>
                        </div>
                        <div class="speciality-name">{row['Speciality']}</div>
                        <div class="prime-tags">{prime_tags_html}</div>
                        <div class="info-container">
                            <div>
                                <div class="info-row">
                                    <span>Location:</span>
                                    <span>{row['City']}, {row['Country']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Tuition:</span>
                                    <span>${row['Tuition Price']:,.0f} {row['Tuition Currency']}/Year</span>
                                </div>
                                <div class="info-row">
                                    <span>Application fee:</span>
                                    <span>${row['Application Fee Price']:,.0f} {row['Application Fee Currency']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Duration:</span>
                                    <span>{row['Duration']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Level:</span>
                                    <span>{row['Level']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Field:</span>
                                    <span>{row['Field']}</span>
                                </div>
                            </div>
                            <a href="{row['Link']}" class="create-application-btn" target="_blank">Apply Now</a>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

    # Pagination controls
    col1, col2, col3 = st.columns([1,2,1])
    
    with col1:
        if st.session_state.current_page > 1:
            if st.button("◀ Previous", key=f"prev_button_{st.session_state.current_page}"):
                st.session_state.current_page -= 1
                st.rerun()
    
    with col2:
        st.markdown(f'<div class="page-info">Page {st.session_state.current_page} of {total_pages}</div>', unsafe_allow_html=True)
    
    with col3:
        if st.session_state.current_page < total_pages:
            if st.button("Next ▶", key=f"next_button_{st.session_state.current_page}"):
                st.session_state.current_page += 1
                st.rerun()

if __name__ == "__main__":
    main()
