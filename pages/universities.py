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
    st.title("University Search Tool")

    # Replace with your Google Sheet ID and sheet name
    SPREADSHEET_ID = "1gCxnCOhQRHtVdVMSiLaReBRJbCUz1Wn6-KJRZshneuM"  # Replace with your Google Sheet ID
    SHEET_NAME = "cleaned_universities_data"

    # Load the data
    df = load_data(SPREADSHEET_ID, SHEET_NAME)

    # Big search bar for University Name and Speciality with fuzzy matching
    search_term = st.text_input("Search for Universities or Specialities")

    if search_term:
        university_matches = fuzzy_search(search_term, df['University Name'].str.lower())
        speciality_matches = fuzzy_search(search_term, df['Adjusted Speciality'].str.lower())
        filtered_df = df[df['University Name'].str.lower().isin(university_matches) |
                         df['Adjusted Speciality'].str.lower().isin(speciality_matches)]
    else:
        filtered_df = df.copy()

    # Filters - Now in the main interface, not the sidebar
    st.write("Filters:")
    
    institution_type = st.multiselect("Institution Type", options=filtered_df['Institution Type'].unique())
    if institution_type:
        filtered_df = filtered_df[filtered_df['Institution Type'].isin(institution_type)]

    country = st.multiselect("Country", options=filtered_df['Country'].unique())
    if country:
        filtered_df = filtered_df[filtered_df['Country'].isin(country)]

    state = st.multiselect("State/Province", options=filtered_df['State/Province'].unique())
    if state:
        filtered_df = filtered_df[filtered_df['State/Province'].isin(state)]

    city = st.multiselect("City", options=filtered_df['City'].unique())
    if city:
        filtered_df = filtered_df[filtered_df['City'].isin(city)]

    level = st.multiselect("Level", options=filtered_df['Level'].unique())
    if level:
        filtered_df = filtered_df[filtered_df['Level'].isin(level)]

    # Add filters for Fields and Majors
    fields = st.multiselect("Field", options=filtered_df['Field'].unique())
    if fields:
        filtered_df = filtered_df[filtered_df['Field'].isin(fields)]
    
    majors = st.multiselect("Major", options=filtered_df['Adjusted Speciality'].unique())
    if majors:
        filtered_df = filtered_df[filtered_df['Adjusted Speciality'].isin(majors)]

    duration = st.multiselect("Duration", options=filtered_df['Duration'].unique())
    if duration:
        filtered_df = filtered_df[filtered_df['Duration'].isin(duration)]

    tuition_min, tuition_max = st.slider(
        "Tuition Price Range",
        min_value=int(filtered_df['Tuition Price'].min()),
        max_value=int(filtered_df['Tuition Price'].max()),
        value=(int(filtered_df['Tuition Price'].min()), int(filtered_df['Tuition Price'].max()))
    )
    filtered_df = filtered_df[(filtered_df['Tuition Price'] >= tuition_min) & (filtered_df['Tuition Price'] <= tuition_max)]

    application_fee_min, application_fee_max = st.slider(
        "Application Fee Range",
        min_value=int(filtered_df['Application Fee Price'].min()),
        max_value=int(filtered_df['Application Fee Price'].max()),
        value=(int(filtered_df['Application Fee Price'].min()), int(filtered_df['Application Fee Price'].max()))
    )
    filtered_df = filtered_df[(filtered_df['Application Fee Price'] >= application_fee_min) & (filtered_df['Application Fee Price'] <= application_fee_max)]

    prime = st.multiselect("Prime Benefits", options=['Incentivized', 'High Job Demand', 'Instant Offer', 'Popular'])
    for prime_benefit in prime:
        filtered_df = filtered_df[(filtered_df['prime 2'] == prime_benefit) |
                                  (filtered_df['prime 3'] == prime_benefit) |
                                  (filtered_df['prime 4'] == prime_benefit) |
                                  (filtered_df['prime 5'] == prime_benefit)]

    # Display the filtered data
    st.write("Filtered Results:")
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
