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
    st.set_page_config(layout="wide")
    
    # Custom CSS for modern styling
    st.markdown("""
    <style>
    .stSelectbox, .stMultiSelect {
        margin-bottom: 10px;
    }
    .university-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 15px;
        height: 350px;  /* Set a fixed height */
        display: flex;
        flex-direction: column;
        background: linear-gradient(145deg, #f0f0f0, #d0d0d0);
        box-shadow: 4px 4px 10px #aaaaaa, -4px -4px 10px #ffffff;
        transition: transform 0.2s ease-in-out;
    }
    .university-card:hover {
        transform: translateY(-5px) scale(1.02);
    }
    .university-header {
        display: flex;
        align-items: center;
        margin-bottom: 10px;
    }
    .university-logo {
        width: 60px;
        height: 60px;
        margin-right: 15px;
        object-fit: contain;
        border-radius: 50%;
        box-shadow: 2px 2px 5px #999999;
    }
    .university-name {
        font-size: 18px;
        font-weight: bold;
        flex-grow: 1;
        color: #333333;
    }
    .speciality-name {
        font-size: 14px;
        margin-bottom: 10px;
        height: 40px;  /* Set a fixed height */
        overflow: hidden;
        color: #555555;
        font-style: italic;
    }
    .info-container {
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-size: 13px;
        color: #666666;
    }
    .create-application-btn {
        background-color: #0073e6;
        color: white;
        padding: 10px 15px;
        border-radius: 5px;
        text-align: center;
        text-decoration: none;
        display: block;
        font-size: 14px;
        font-weight: bold;
        margin-top: 15px;
        transition: background-color 0.3s ease;
    }
    .create-application-btn:hover {
        background-color: #005bb5;
    }
    .prime-tags {
        margin-bottom: 10px;
    }
    .prime-tag {
        background-color: #FFD700;
        color: black;
        padding: 3px 6px;
        border-radius: 15px;
        font-size: 12px;
        margin-right: 5px;
        display: inline-block;
        box-shadow: 1px 1px 3px #888888;
    }
    .pagination {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .pagination-btn {
        margin: 0 10px;
        background-color: #f0f0f0;
        border: none;
        padding: 8px 15px;
        border-radius: 5px;
        box-shadow: 2px 2px 5px #aaaaaa;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .pagination-btn:hover {
        background-color: #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Replace with your Google Sheet ID and sheet name
    SPREADSHEET_ID = "1gCxnCOhQRHtVdVMSiLaReBRJbCUz1Wn6-KJRZshneuM"
    SHEET_NAME = "cleaned_universities_data"

    # Load the data
    df = load_data(SPREADSHEET_ID, SHEET_NAME)

    # Sidebar for filters
    with st.sidebar:
        st.title("Filters")
        
        location = st.selectbox("Location", ["All"] + sorted(df['Country'].unique().tolist()))
        program_level = st.selectbox("Program level", ["All"] + sorted(df['Level'].unique().tolist()))
        field_of_study = st.selectbox("Field of study", ["All"] + sorted(df['Field'].unique().tolist()))
        
        tuition_min, tuition_max = st.slider(
            "Tuition fee range",
            min_value=int(df['Tuition Price'].min()),
            max_value=int(df['Tuition Price'].max()),
            value=(int(df['Tuition Price'].min()), int(df['Tuition Price'].max()))
        )
        
        apply_filters = st.button("Apply filters")

    # Main content area
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
    items_per_page = 32
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
                                    <span>Location</span>
                                    <span>{row['City']}, {row['Country']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Tuition fee</span>
                                    <span>${row['Tuition Price']:,.0f} {row['Tuition Currency']} / Year</span>
                                </div>
                                <div class="info-row">
                                    <span>Application fee</span>
                                    <span>${row['Application Fee Price']:,.0f} {row['Application Fee Currency']}</span>
                                </div>
                                <div class="info-row">
                                    <span>Duration</span>
                                    <span>{row['Duration']}</span>
                                </div>
                            </div>
                            <a href="{row['Link']}" class="create-application-btn" target="_blank">Create application</a>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

    # Pagination controls
    st.markdown('<div class="pagination">', unsafe_allow_html=True)
    if st.session_state.current_page > 1:
        if st.button("Previous", key="prev_button"):
            st.session_state.current_page -= 1
            st.rerun()
    
    st.markdown(f'<span>Page {st.session_state.current_page} of {total_pages}</span>', unsafe_allow_html=True)
    
    if st.session_state.current_page < total_pages:
        if st.button("Next", key="next_button"):
            st.session_state.current_page += 1
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
