import os
import json
import gspread
import streamlit as st
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import asyncio
import aiohttp
import threading
import re
st.set_page_config(page_title="Student Application Tracker", layout="wide")
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration


# Use Streamlit secrets for service account info
SERVICE_ACCOUNT_INFO = st.secrets["gcp_service_account"]

# Define the required scope
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

# Authenticate with Google Sheets
@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    return gspread.authorize(creds)

client = get_gsheet_client()

# Open the Google Sheet using the provided link
spreadsheet_url = "https://docs.google.com/spreadsheets/d/1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew/edit#gid=1019724402"

# Function to load data from Google Sheets
def load_data():
    spreadsheet = client.open_by_url(spreadsheet_url)
    sheet = spreadsheet.sheet1  # Adjust if you need to access a different sheet
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')  # Convert DATE to datetime with dayfirst=True
    df['Months'] = df['DATE'].dt.strftime('%B %Y')  # Create a new column 'Months' for filtering
    return df

# Function to save data to Google Sheets
def save_data(df, spreadsheet_url):
    logger.info("Attempting to save changes")
    try:
        spreadsheet = client.open_by_url(spreadsheet_url)
        sheet = spreadsheet.sheet1

        # Convert DATE column back to string
        df['DATE'] = pd.to_datetime(df['DATE'], dayfirst=True, errors='coerce')  # Ensure DATE is datetime
        df['DATE'] = df['DATE'].dt.strftime('%d/%m/%Y %H:%M:%S')

        # Replace problematic values with a placeholder
        df.replace([np.inf, -np.inf, np.nan], 'NaN', inplace=True)

        # Clear the existing sheet
        sheet.clear()

        # Update the sheet with new data
        sheet.update([df.columns.values.tolist()] + df.values.tolist())

        logger.info("Changes saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving changes: {str(e)}")
        return False

# Load data and initialize session state
if 'data' not in st.session_state or st.session_state.get('reload_data', False):
    st.session_state.data = load_data()
    st.session_state.original_data = st.session_state.data.copy()  # Keep a copy of the original data
    st.session_state.reload_data = False

# Display the editable dataframe
st.title("Student Application Tracker")

# Filters
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    agents = st.multiselect('Filter by Agent', options=st.session_state.data['Agent'].unique())

with col2:
    months_years = st.multiselect('Filter by Month', options=st.session_state.data['Months'].unique())

with col3:
    stages = st.multiselect('Filter by Stage', options=st.session_state.data['Stage'].unique())

with col4:
    schools = st.multiselect('Filter by Chosen School', options=st.session_state.data['Chosen School'].unique())

with col5:
    attempts = st.multiselect('Filter by Attempts', options=st.session_state.data['Attempts'].unique())

filtered_data = st.session_state.data.copy()

if agents:
    filtered_data = filtered_data[filtered_data['Agent'].isin(agents)]
if months_years:
    filtered_data = filtered_data[filtered_data['Months'].isin(months_years)]
if stages:
    filtered_data = filtered_data[filtered_data['Stage'].isin(stages)]
if schools:
    filtered_data = filtered_data[filtered_data['Chosen School'].isin(schools)]
if attempts:
    filtered_data = filtered_data[filtered_data['Attempts'].isin(attempts)]

# Sort filtered data for display using DATE as day-first
filtered_data['DATE'] = pd.to_datetime(filtered_data['DATE'], dayfirst=True, errors='coerce')
filtered_data.sort_values(by='DATE', inplace=True)

# Ensure all columns are treated as strings for editing
filtered_data = filtered_data.astype(str)

# Use a key for the data_editor to ensure proper updates
edited_df = st.data_editor(filtered_data, num_rows="dynamic", key="student_data")

# Update Google Sheet with edited data
if st.button("Save Changes"):
    try:
        # Convert DATE column back to string for saving
        edited_df['DATE'] = pd.to_datetime(edited_df['DATE'], dayfirst=True, errors='coerce')
        edited_df['DATE'] = edited_df['DATE'].dt.strftime('%d/%m/%Y %H:%M:%S')
        
        st.session_state.original_data.update(edited_df)  # Update the original dataset with edited data
        
        if save_data(st.session_state.original_data, spreadsheet_url):
            st.session_state.data = load_data()  # Reload the data to ensure consistency
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

def on_student_select():
    st.session_state.student_changed = True

def clear_cache_and_rerun():
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

def format_date(date_str):
    try:
        date = pd.to_datetime(date_str, dayfirst=True)
        return date.strftime('%d %B %Y')
    except ValueError:
        return date_str

def calculate_days_until_interview(interview_date):
    try:
        interview_date = pd.to_datetime(interview_date, dayfirst=True)
        today = pd.Timestamp.now().normalize()
        days_until_interview = (interview_date - today).days
        return days_until_interview if days_until_interview >= 0 else None
    except ValueError:
        return None

def handle_file_upload(student_name, document_type, uploaded_file):
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': f"{student_name}_{document_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'parents': ['your-folder-id']  # Replace with your Google Drive folder ID
    }
    
    media = MediaFileUpload(uploaded_file, resumable=True)
    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return None

def get_document_status(student_name):
    # Implement your logic to check document status in Google Drive
    # Return a dictionary with document types and their status
    # For example:
    # {
    #     "Passport": {"status": True, "files": [{"name": "passport.pdf", "webViewLink": "url"}]},
    #     "Bank Statement": {"status": False, "files": []}
    # }
    return {}

def trash_file_in_drive(file_id, student_name):
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)
    
    try:
        drive_service.files().update(fileId=file_id, body={"trashed": True}).execute()
        logger.info(f"File {file_id} trashed successfully for student {student_name}")
        return True
    except Exception as e:
        logger.error(f"Error trashing file {file_id}: {str(e)}")
        return False

def clear_session_state():
    for key in st.session_state.keys():
        del st.session_state[key]

def update_student_data():
    if 'selected_student' in st.session_state:
        selected_student = st.session_state['selected_student']
        data = st.session_state['data']
        
        for key in ['first_name', 'last_name', 'Age', 'Gender', 'phone_number', 'email', 'emergency_contact', 'address', 'attempts', 'chosen_school', 'specialite', 'duration', 'Bankstatment', 'school_entry_date', 'entry_date_in_us', 'address_us', 'email_rdv', 'password_rdv', 'embassy_itw_date', 'ds160_maker', 'password_ds160', 'secret_q', 'Prep_ITW', 'payment_date', 'payment_method', 'payment_type', 'compte', 'sevis_payment', 'application_payment', 'current_step']:
            if key in st.session_state:
                data.loc[data['Student Name'] == selected_student, key] = st.session_state[key]

        st.session_state['data'] = data
        st.session_state['student_changed'] = True

# Main function
def main():
    
    if 'student_changed' not in st.session_state:
        st.session_state.student_changed = False
    if 'upload_success' not in st.session_state:
        st.session_state.upload_success = False
    if 'selected_student' not in st.session_state:
        st.session_state.selected_student = ""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Personal"
    # Initialize other session state variables
    for key in ['visa_status', 'current_step', 'payment_date', 'payment_method', 'payment_type', 'compte', 'sevis_payment', 'application_payment']:
        if key not in st.session_state:
            st.session_state[key] = None

    # Check if we need to refresh the page
    if st.session_state.upload_success:
        st.session_state.upload_success = False
        st.rerun()

    st.markdown("""
    <style>
        .reportview-container {
            background: #f0f2f6;
        }
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1, h2, h3 {
            color: #1E3A8A;
        }
        .stSelectbox, .stTextInput {
            background-color: white;
            color: #2c3e50;
            border-radius: 5px;
            padding: 10px;
        }
        .stExpander {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 10px;
        }
        .css-1544g2n {
            padding: 2rem;
        }
        .stMetric {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stMetric .metric-label {
            font-weight: bold;
        }
        .stButton>button {
            background-color: #ff7f50;
            color: white;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #ff6347;
        }
        .stTextInput input {
            font-size: 1rem;
            padding: 10px;
            margin-bottom: 10px;
        }
        .progress-container {
            width: 100%;
            background-color: #e0e0e0;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .progress-bar {
            height: 20px;
            background-color: #4caf50;
            border-radius: 10px;
            transition: width 0.5s ease-in-out;
            text-align: center;
            line-height: 20px;
            color: white;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stCard" style="text-align: center;">
        <img src="https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png" width="150" height="150">
        <h1>The Us House</h1>
    </div>
    """, unsafe_allow_html=True)

    spreadsheet_id = "1NkW2a4_eOlDGeVxY9PZk-lEI36PvAv9XoO4ZIwl-Sew"
    
    if 'data' not in st.session_state or st.session_state.get('reload_data', False):
        data = load_data()
        st.session_state['data'] = data
        st.session_state['reload_data'] = False
    else:
        data = st.session_state['data']

    if not data.empty:
        current_steps = ["All"] + list(data['Stage'].unique())
        agents = ["All", "Nesrine", "Hamza", "Djazila","Nada"]
        school_options = ["All", "University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English ",
                          "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago", "BEA Huston", "BIA Huston",
                          "OHLA Miami", "UCDEA", "HAWAII", "Not Partner", "Not yet"]
        attempts_options = ["All", "1 st Try", "2 nd Try", "3 rd Try"]
        Gender_options = ["Male", "Female"]

        st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filter = st.selectbox("Filter by Stage", current_steps, key="status_filter")
        with col2:
            agent_filter = st.selectbox("Filter by Agent", agents, key="agent_filter")
        with col3:
            school_filter = st.selectbox("Filter by School", school_options, key="school_filter")
        with col4:
            attempts_filter = st.selectbox("Filter by Attempts", attempts_options, key="attempts_filter")

        # Apply filters
        filtered_data = data
        if status_filter != "All":
            filtered_data = filtered_data[filtered_data['Stage'] == status_filter]
        if agent_filter != "All":
            filtered_data = filtered_data[filtered_data['Agent'] == agent_filter]
        if school_filter != "All":
            filtered_data = filtered_data[filtered_data['Chosen School'] == school_filter]
        if attempts_filter != "All":
            filtered_data = filtered_data[filtered_data['Attempts'] == attempts_filter]
        
        student_names = filtered_data['Student Name'].tolist()
        
        if not filtered_data.empty:
            st.markdown('<div class="stCard" style="display: flex; justify-content: space-between;">', unsafe_allow_html=True)
            col2, col1, col3 = st.columns([3, 2, 3])
        
            with col2:
                search_query = st.selectbox(
                    "🔍 Search for a student (First or Last Name)",
                    options=student_names,
                    key="search_query",
                    index=student_names.index(st.session_state.selected_student) if st.session_state.selected_student in student_names else 0,
                    on_change=on_student_select
                )
                # After the selectbox:
                if st.session_state.student_changed or st.session_state.selected_student != search_query:
                    st.session_state.selected_student = search_query
                    st.session_state.student_changed = False
                    st.rerun()
                st.subheader("📝 Student Notes")
                
                # Get the current note for the selected student
                selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                current_note = selected_student['Note'] if 'Note' in selected_student else ""
            
                # Create a text area for note input
                new_note = st.text_area("Enter/Edit Note:", value=current_note, height=150, key="note_input")
            
                # Save button for the note
                if st.button("Save Note"):
                    # Update the note in the DataFrame
                    filtered_data.loc[filtered_data['Student Name'] == search_query, 'Note'] = new_note
                    
                    # Save the updated data back to Google Sheets
                    save_data(filtered_data, spreadsheet_id)
                    
                    st.success("Note saved successfully!")
                    
                    # Set a flag to reload data on next run
                    st.session_state['reload_data'] = True
                    
                    # Rerun the app to show updated data
                    st.rerun()
              

            
            with col1:
                st.subheader("Application Status")
                selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
                steps = ['PAYMENT & MAIL', 'APPLICATION', 'SCAN & SEND', 'ARAMEX & RDV', 'DS-160', 'ITW Prep.',  'CLIENTS ']
                current_step = selected_student['Stage']
                step_index = steps.index(current_step) if current_step in steps else 0
                progress = ((step_index + 1) / len(steps)) * 100
        
                progress_bar = f"""
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress}%;">
                        {int(progress)}%
                    </div>
                </div>
                """
                st.markdown(progress_bar, unsafe_allow_html=True)
                
                payment_date_str = selected_student['DATE']
                try:
                    payment_date = pd.to_datetime(payment_date_str, format='%d/%m/%Y %H:%M:%S', errors='coerce', dayfirst=True)
                    payment_date_value = payment_date.strftime('%d %B %Y') if not pd.isna(payment_date) else "Not set"
                except AttributeError:
                    payment_date_value = "Not set"
                
                st.write(f"**📆 Date of Payment:** {payment_date_value}")
        
                st.write(f"**🚩 Current Stage:** {current_step}")
        
                # Agent
                agent = selected_student['Agent']
                st.write(f"**🧑‍💼 Agent:** {agent}")
                
                # SEVIS Payment
                sevis_payment = selected_student['Sevis payment ?']
                sevis_icon = "✅" if selected_student['Sevis payment ?'] == "YES" else "❌"
                st.write(f"**💲 SEVIS Payment:** {sevis_icon} ({sevis_payment})")
        
                # Application Payment
                application_payment = selected_student['Application payment ?']
                application_icon = "✅" if selected_student['Application payment ?'] == "YES" else "❌"
                st.write(f"**💸 Application Payment:** {application_icon} ({application_payment})")
        
                # Visa Status
                visa_status = selected_student['Visa Result']
                st.write(f"**🛂 Visa Status:** {visa_status}")
        
                # Find the section where we display the school entry date
                entry_date = format_date(selected_student['School Entry Date'])
                st.write(f"**🏫 School Entry Date:** {entry_date}")
        
                # Days until Interview
                interview_date = selected_student['EMBASSY ITW. DATE']
                days_remaining = calculate_days_until_interview(interview_date)
                if days_remaining is not None:
                    st.metric("📅 Days until interview", days_remaining)
                else:
                    st.metric("📅 Days until interview", "N/A")
        
            with col3:
                student_name = selected_student['Student Name']
                document_status = get_document_status(student_name)
                st.subheader("Document Status")
        
                for doc_type, status_info in document_status.items():
                    icon = "✅" if status_info['status'] else "❌"
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        st.markdown(f"**{icon} {doc_type}**")
                        for file in status_info['files']:
                            st.markdown(f"- [{file['name']}]({file['webViewLink']})")
                    if status_info['status']:
                        with col2:
                            if st.button("🗑️", key=f"delete_{status_info['files'][0]['id']}", help="Delete file"):
                                file_id = status_info['files'][0]['id']
                                if trash_file_in_drive(file_id, student_name):
                                    st.session_state['reload_data'] = True
                                    clear_cache_and_rerun()
        
        else:
            st.info("No students found matching the search criteria.")

                                    
        if not filtered_data.empty:
            selected_student = filtered_data[filtered_data['Student Name'] == search_query].iloc[0]
            student_name = selected_student['Student Name']

            edit_mode = st.toggle("Edit Mode", value=False)

            # Tabs for student information
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Personal", "School", "Embassy", "Payment","Stage", "Documents"])
            
            # Options for dropdowns
            school_options = ["University", "Community College", "CCLS Miami", "CCLS NY NJ", "Connect English",
                              "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", "GT Chicago","BEA Huston","BIA Huston","OHLA Miami", "UCDEA","HAWAII","Not Partner", "Not yet"]
            
            payment_amount_options = ["159.000 DZD", "152.000 DZD", "139.000 DZD", "132.000 DZD", "36.000 DZD", "20.000 DZD", "Giveaway", "No Paiement"]
            School_paid_opt = ["YES", "NO"]
            Prep_ITW_opt = ["YES", "NO"]
            payment_type_options = ["Cash", "CCP", "Baridimob", "Bank"]
            compte_options = ["Mohamed", "Sid Ali"]
            yes_no_options = ["YES", "NO"]
            attempts_options = ["1st Try", "2nd Try", "3rd Try"]
            Gender_options = ["", "Male", "Female"]

            with tab1:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📋 Personal Information")
                if edit_mode:
                    first_name = st.text_input("First Name", selected_student['First Name'], key="first_name", on_change=update_student_data)
                    last_name = st.text_input("Last Name", selected_student['Last Name'], key="last_name", on_change=update_student_data)
                    Age = st.text_input("Age", selected_student['Age'], key="Age", on_change=update_student_data)
                    Gender = st.selectbox(
                        "Gender", 
                        Gender_options, 
                        index=Gender_options.index(selected_student['Gender']) if selected_student['Gender'] in Gender_options else 0,
                        key="Gender", 
                        on_change=update_student_data
                    )
            
                    # Updated phone number input
                    phone_number = st.text_input("Phone Number", selected_student['Phone N°'], key="phone_number", on_change=update_student_data)
                    if phone_number and not re.match(r'^\+?[0-9]+$', phone_number):
                        st.warning("Phone number should only contain digits, and optionally start with a '+'")
                    
                    email = st.text_input("Email", selected_student['E-mail'], key="email", on_change=update_student_data)
                    
                    # Updated emergency contact input
                    emergency_contact = st.text_input("Emergency Contact Number", selected_student['Emergency contact N°'], key="emergency_contact", on_change=update_student_data)
                    if emergency_contact and not re.match(r'^\+?[0-9]+$', emergency_contact):
                        st.warning("Emergency contact number should only contain digits, and optionally start with a '+'")
                    
                    address = st.text_input("Address", selected_student['Address'], key="address", on_change=update_student_data)
                    attempts = st.selectbox(
                        "Attempts", 
                        attempts_options, 
                        index=attempts_options.index(selected_student['Attempts']) if selected_student['Attempts'] in attempts_options else 0,
                        key="attempts", 
                        on_change=update_student_data
                    )
                    agentss = st.selectbox(
                        "Agent", 
                        agents, 
                        index=agents.index(selected_student['Agent']) if selected_student['Agent'] in attempts_options else 0,
                        key="Agent", 
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**First Name:** {selected_student['First Name']}")
                    st.write(f"**Last Name:** {selected_student['Last Name']}")
                    st.write(f"**Age:** {selected_student['Age']}")
                    st.write(f"**Gender:** {selected_student['Gender']}")
                    st.write(f"**Phone Number:** {selected_student['Phone N°']}")
                    st.write(f"**Email:** {selected_student['E-mail']}")
                    st.write(f"**Emergency Contact Number:** {selected_student['Emergency contact N°']}")
                    st.write(f"**Address:** {selected_student['Address']}")
                    st.write(f"**Attempts:** {selected_student['Attempts']}")
                    st.write(f"**Agent:** {selected_student['Agent']}")
                st.markdown('</div>', unsafe_allow_html=True)
                    
            with tab2:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🏫 School Information")
                if edit_mode:
                    chosen_school = st.selectbox("Chosen School", school_options, index=school_options.index(selected_student['Chosen School']) if selected_student['Chosen School'] in school_options else 0, key="chosen_school", on_change=update_student_data)
                    specialite = st.text_input("Specialite", selected_student['Specialite'], key="specialite", on_change=update_student_data)
                    duration = st.text_input("Duration", selected_student['Duration'], key="duration", on_change=update_student_data)
                    Bankstatment = st.text_input("BANK", selected_student['BANK'], key="Bankstatment", on_change=update_student_data)
                
                    school_entry_date = pd.to_datetime(selected_student['School Entry Date'], errors='coerce', dayfirst=True)
                    school_entry_date = st.date_input(
                        "School Entry Date",
                        value=school_entry_date if not pd.isna(school_entry_date) else None,
                        key="school_entry_date",
                        on_change=update_student_data
                    )
                    
                    entry_date_in_us = pd.to_datetime(selected_student['Entry Date in the US'], errors='coerce', dayfirst=True)
                    entry_date_in_us = st.date_input(
                        "Entry Date in the US",
                        value=entry_date_in_us if not pd.isna(entry_date_in_us) else None,
                        key="entry_date_in_us",
                        on_change=update_student_data
                    )
                    School_Paid = st.selectbox(
                        "School Paid", 
                        School_paid_opt, 
                        index=School_paid_opt.index(selected_student['School Paid']) if selected_student['School Paid'] in School_paid_opt else 0,
                        key="School_Paid",  # Note the capitalization here
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**Chosen School:** {selected_student['Chosen School']}")
                    st.write(f"**Specialite:** {selected_student['Specialite']}")
                    st.write(f"**Duration:** {selected_student['Duration']}")
                    st.write(f"**BANK:** {selected_student['BANK']}")
                    st.write(f"**School Entry Date:** {format_date(selected_student['School Entry Date'])}")
                    st.write(f"**Entry Date in the US:** {format_date(selected_student['Entry Date in the US'])}")
                    st.write(f"**School Paid:** {selected_student['School Paid']}")

                st.markdown('</div>', unsafe_allow_html=True)

            with tab3:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🇺🇸 Embassy Information")
                if edit_mode:
                    email_rdv = st.text_input("Email Rdv", selected_student['E-mail rdv'], key="email_rdv", on_change=update_student_data)
                    password_rdv = st.text_input("Password Rdv", selected_student['Password rdv'], key="password_rdv", on_change=update_student_data)
                    embassy_itw_date = pd.to_datetime(selected_student['EMBASSY ITW. DATE'], errors='coerce', dayfirst=True)
                    embassy_itw_date = st.date_input(
                        "Embassy Interview Date",
                        value=embassy_itw_date if not pd.isna(embassy_itw_date) else None,
                        key="embassy_itw_date",
                        on_change=update_student_data
                    )
                    ds160_maker = st.text_input("DS-160 Maker", selected_student['DS-160 maker'], key="ds160_maker", on_change=update_student_data)
                    password_ds160 = st.text_input("Password DS-160", selected_student['Password DS-160'], key="password_ds160", on_change=update_student_data)
                    secret_q = st.text_input("Secret Question", selected_student['Secret Q°'], key="secret_q", on_change=update_student_data)
                    Prep_ITW = st.selectbox(
                        "ITW Prep.", 
                        Prep_ITW_opt, 
                        index=Prep_ITW_opt.index(selected_student['Prep ITW']) if selected_student['Prep ITW'] in Prep_ITW_opt else 0,
                        key="Prep_ITW", 
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**Email Rdv:** {selected_student['E-mail rdv']}")
                    st.write(f"**Password Rdv:** {selected_student['Password rdv']}")
                    st.write(f"**Embassy Interview Date:** {format_date(selected_student['EMBASSY ITW. DATE'])}")
                    st.write(f"**DS-160 Maker:** {selected_student['DS-160 maker']}")
                    st.write(f"**Password DS-160:** {selected_student['Password DS-160']}")
                    st.write(f"**Secret Question:** {selected_student['Secret Q°']}")
                    st.write(f"**ITW Prep:** {selected_student['Prep ITW']}")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab4:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("💰 Payment Information")
                if edit_mode:
                    payment_date = pd.to_datetime(selected_student['Payment Date'], errors='coerce', dayfirst=True)
                    payment_date = st.date_input(
                        "Payment Date",
                        value=payment_date if not pd.isna(payment_date) else None,
                        key="payment_date",
                        on_change=update_student_data
                    )
                    payment_method = st.selectbox(
                        "Payment Method", 
                        payment_type_options, 
                        index=payment_type_options.index(selected_student['Payment Method']) if selected_student['Payment Method'] in payment_type_options else 0,
                        key="payment_method", 
                        on_change=update_student_data
                    )
                    payment_type = st.selectbox(
                        "Payment Type", 
                        payment_amount_options, 
                        index=payment_amount_options.index(selected_student['Payment Type']) if selected_student['Payment Type'] in payment_amount_options else 0,
                        key="payment_type", 
                        on_change=update_student_data
                    )
                    compte = st.selectbox(
                        "Compte", 
                        compte_options, 
                        index=compte_options.index(selected_student['Compte']) if selected_student['Compte'] in compte_options else 0,
                        key="compte", 
                        on_change=update_student_data
                    )
                    sevis_payment = st.selectbox(
                        "Sevis Payment", 
                        yes_no_options, 
                        index=yes_no_options.index(selected_student['Sevis payment ?']) if selected_student['Sevis payment ?'] in yes_no_options else 0,
                        key="sevis_payment", 
                        on_change=update_student_data
                    )
                    application_payment = st.selectbox(
                        "Application Payment", 
                        yes_no_options, 
                        index=yes_no_options.index(selected_student['Application payment ?']) if selected_student['Application payment ?'] in yes_no_options else 0,
                        key="application_payment", 
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**Payment Date:** {format_date(selected_student['Payment Date'])}")
                    st.write(f"**Payment Method:** {selected_student['Payment Method']}")
                    st.write(f"**Payment Type:** {selected_student['Payment Type']}")
                    st.write(f"**Compte:** {selected_student['Compte']}")
                    st.write(f"**Sevis Payment:** {selected_student['Sevis payment ?']}")
                    st.write(f"**Application Payment:** {selected_student['Application payment ?']}")
                st.markdown('</div>', unsafe_allow_html=True)
            with tab5:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("🎓 Current Step")
                if edit_mode:
                    current_step = st.selectbox(
                        "Current Step",
                        steps,
                        index=steps.index(selected_student['Stage']) if selected_student['Stage'] in steps else 0,
                        key="current_step",
                        on_change=update_student_data
                    )
                else:
                    st.write(f"**Current Step:** {selected_student['Stage']}")
                st.markdown('</div>', unsafe_allow_html=True)
            with tab6:
                st.markdown('<div class="stCard">', unsafe_allow_html=True)
                st.subheader("📂 Document Management")
                st.write("Upload new documents here. The documents will be saved to Google Drive.")
                
                for doc_type in ["Passport", "Bank Statement", "Photo"]:
                    uploaded_file = st.file_uploader(f"Upload {doc_type}", type=["pdf", "jpg", "png"], key=f"{doc_type}_uploader")
                    
                    if uploaded_file is not None:
                        file_id = handle_file_upload(student_name, doc_type, uploaded_file)
                        
                        if file_id:
                            st.success(f"{doc_type} uploaded successfully!")
                            st.session_state.upload_success = True
                            st.rerun()
                        else:
                            st.error(f"Failed to upload {doc_type}.")
                
                # Option to delete uploaded documents
                st.subheader("Delete Documents")
                document_status = get_document_status(student_name)
                
                for doc_type, status_info in document_status.items():
                    if status_info['status']:
                        for file in status_info['files']:
                            col1, col2 = st.columns([9, 1])
                            with col1:
                                st.markdown(f"- [{file['name']}]({file['webViewLink']})")
                            with col2:
                                if st.button("🗑️", key=f"delete_{file['id']}", help="Delete file"):
                                    file_id = file['id']
                                    if trash_file_in_drive(file_id, student_name):
                                        st.success(f"{file['name']} deleted successfully!")
                                        st.session_state.upload_success = True
                                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

            # Update student data
            if st.session_state.student_changed:
                update_student_data()
                st.session_state.student_changed = False

    else:
        st.warning("No data found in the Google Sheet. Please check the spreadsheet URL and try again.")
        
if __name__ == "__main__":
    main()
