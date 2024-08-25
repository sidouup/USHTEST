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
    
    # ... (keep the existing CSS styles)

    # Replace with your Google Sheet ID and sheet name
    SPREADSHEET_ID = "1gCxnCOhQRHtVdVMSiLaReBRJbCUz1Wn6-KJRZshneuM"
    SHEET_NAME = "cleaned_universities_data"

    # Load the data
    df = load_data(SPREADSHEET_ID, SHEET_NAME)

    # Initialize session state for filters and filtered dataframe if not already present
    if 'filters' not in st.session_state:
        st.session_state.filters = {
            'country': 'All',
            'program_level': 'All',
            'field': 'All',
            'specialty': 'All',
            'institution_type': 'All',
            'major': 'All',
            'tuition_min': int(df['Tuition Price'].min()),
            'tuition_max': int(df['Tuition Price'].max())
        }
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = df

    # Main container for filters
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.filters['country'] = st.selectbox(
                "Country", 
                options=["All"] + sorted(df['Country'].unique().tolist()),
                key='country_filter'
            )
        with col2:
            st.session_state.filters['program_level'] = st.selectbox(
                "Program level", 
                options=["All"] + sorted(df['Level'].unique().tolist()),
                key='program_level_filter'
            )
        with col3:
            st.session_state.filters['field'] = st.selectbox(
                "Field", 
                options=["All"] + sorted(df['Field'].unique().tolist()),
                key='field_filter'
            )

        col4, col5, col6 = st.columns(3)
        with col4:
            st.session_state.filters['specialty'] = st.selectbox(
                "Specialty", 
                options=["All"] + sorted(df['Adjusted Speciality'].unique().tolist()),
                key='specialty_filter'
            )
        with col5:
            st.session_state.filters['institution_type'] = st.selectbox(
                "Institution Type", 
                options=["All"] + sorted(df['Institution Type'].unique().tolist()),
                key='institution_type_filter'
            )
        with col6:
            st.session_state.filters['major'] = st.selectbox(
                "Search by Major", 
                options=["All"] + sorted(df['Major'].unique().tolist()),
                key='major_filter'
            )

    st.session_state.filters['tuition_min'], st.session_state.filters['tuition_max'] = st.slider(
        "Tuition fee range (CAD)",
        min_value=int(df['Tuition Price'].min()),
        max_value=int(df['Tuition Price'].max()),
        value=(st.session_state.filters['tuition_min'], st.session_state.filters['tuition_max']),
        key='tuition_filter'
    )

    apply_filters = st.button("Apply Filter")

    if apply_filters:
        filtered_df = df.copy()
        
        if st.session_state.filters['country'] != "All":
            filtered_df = filtered_df[filtered_df['Country'] == st.session_state.filters['country']]
        
        if st.session_state.filters['program_level'] != "All":
            filtered_df = filtered_df[filtered_df['Level'] == st.session_state.filters['program_level']]
        
        if st.session_state.filters['field'] != "All":
            filtered_df = filtered_df[filtered_df['Field'] == st.session_state.filters['field']]
        
        if st.session_state.filters['specialty'] != "All":
            filtered_df = filtered_df[filtered_df['Adjusted Speciality'] == st.session_state.filters['specialty']]
        
        if st.session_state.filters['institution_type'] != "All":
            filtered_df = filtered_df[filtered_df['Institution Type'] == st.session_state.filters['institution_type']]
        
        if st.session_state.filters['major'] != "All":
            filtered_df = filtered_df[filtered_df['Major'] == st.session_state.filters['major']]
        
        filtered_df = filtered_df[
            (filtered_df['Tuition Price'] >= st.session_state.filters['tuition_min']) & 
            (filtered_df['Tuition Price'] <= st.session_state.filters['tuition_max'])
        ]
        
        st.session_state.filtered_df = filtered_df
        st.session_state.current_page = 1  # Reset to first page when new filter is applied

    # Display results
    st.subheader(f"Showing {len(st.session_state.filtered_df)} results")
    
    # Pagination
    items_per_page = 16  # Changed to 16 for a 4x4 grid
    total_pages = math.ceil(len(st.session_state.filtered_df) / items_per_page)
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    
    start_idx = (st.session_state.current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    
    # Display university cards with a consistent layout
    for i in range(0, min(items_per_page, len(st.session_state.filtered_df) - start_idx), 4):
        cols = st.columns(4)  # Create a grid layout with four columns
        for j in range(4):
            if i + j < len(st.session_state.filtered_df[start_idx:end_idx]):
                row = st.session_state.filtered_df.iloc[start_idx + i + j]
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
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
    
    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.session_state.current_page > 1:
            if st.button("◀ Previous", key="prev_button"):
                st.session_state.current_page -= 1
                st.rerun()
    with col2:
        st.markdown(f'<div class="page-info">Page {st.session_state.current_page} of {total_pages}</div>', unsafe_allow_html=True)
    with col3:
        if st.session_state.current_page < total_pages:
            if st.button("Next ▶", key="next_button"):
                st.session_state.current_page += 1
                st.rerun()


if __name__ == "__main__":
    main()
