import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from difflib import get_close_matches

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
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .stSelectbox, .stMultiSelect {
        margin-bottom: 10px;
    }
    .university-card {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
    }
    .university-name {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .degree-name {
        font-size: 16px;
        margin-bottom: 10px;
    }
    .info-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .create-application-btn {
        background-color: #1E90FF;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 14px;
        margin-top: 10px;
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
        
        intakes = st.multiselect("Intakes", df['Intake'].unique())
        
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
        
        if intakes:
            filtered_df = filtered_df[filtered_df['Intake'].isin(intakes)]
    else:
        filtered_df = df

    # Display results
    st.subheader(f"Showing {len(filtered_df)} results")
    
    # Create two columns for displaying university cards
    col1, col2 = st.columns(2)
    
    for index, row in filtered_df.iterrows():
        with col1 if index % 2 == 0 else col2:
            st.markdown(f"""
            <div class="university-card">
                <div class="university-name">{row['University Name']}</div>
                <div class="degree-name">{row['Degree Name']}</div>
                <div class="info-row">
                    <span>Location</span>
                    <span>{row['City']}, {row['Country']}</span>
                </div>
                <div class="info-row">
                    <span>Gross tuition fee</span>
                    <span>${row['Tuition Price']:,.0f} USD / Year</span>
                </div>
                <div class="info-row">
                    <span>Application fee</span>
                    <span>${row['Application Fee Price']:,.0f} USD</span>
                </div>
                <div class="info-row">
                    <span>Duration</span>
                    <span>{row['Duration']} months</span>
                </div>
                <a href="#" class="create-application-btn">Create application</a>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
