import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import re

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
    
    # Extract the country code from the Location column
    df['Country'] = df['Location'].apply(lambda x: x.split(", ")[-1])
    
    # Clean the Tuition column by removing non-numeric characters and converting to integer
    df['Tuition'] = df['Tuition'].apply(lambda x: int(re.sub(r'[^\d]', '', x.split('/')[0])))
    
    return df

# Example usage in your Streamlit app
def main():
    st.title("University Search Tool")

    # Replace with your Google Sheet ID and sheet name
    SPREADSHEET_ID = "1LsYe-R3uUUN1L00drh-_-KADsU04vTBr5soIGOf33o0"
    SHEET_NAME = "Universities"

    # Load the data
    df = load_data(SPREADSHEET_ID, SHEET_NAME)

    # Filter by country
    country = st.sidebar.selectbox("Select Country", options=df['Country'].unique())
    
    # Filter by city
    city = st.sidebar.selectbox("Select City", options=df[df['Country'] == country]['City'].unique())
    
    # Filter by max tuition
    max_tuition = st.sidebar.slider("Max Tuition", min_value=int(df['Tuition'].min()), max_value=int(df['Tuition'].max()))

    # Filter the DataFrame
    filtered_df = df[(df['Country'] == country) & 
                     (df['City'] == city) & 
                     (df['Tuition'] <= max_tuition)]
    
    # Display the filtered data
    st.dataframe(filtered_df)

if __name__ == "__main__":
    main()
