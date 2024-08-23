import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# Retrieve the API key from Streamlit secrets
api_key = st.secrets.get("api_key")
if not api_key:
    st.error("API_KEY_gemini not found in Streamlit secrets. Please add it.")
    st.stop()

# Initialize the Google Gemini model with the updated model version and API key
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
except Exception as e:
    st.error(f"Failed to initialize Google Gemini model: {e}")
    st.stop()

# Define the list of fields and their corresponding majors
fields_and_majors = {
    "Computer Science and Information Technology": [
        "Computer Science Fundamentals", "Software Engineering", 
        "Artificial Intelligence and Machine Learning", "Data Science and Analytics", 
        "Cybersecurity", "Information Systems and Management", "Networking and Telecommunications", 
        "Web Development and Internet Technologies", "Human-Computer Interaction", 
        "Database Systems and Big Data"
    ],
    "Business and Management": [
        "Business Administration", "Marketing", "Finance and Accounting", 
        "Human Resource Management", "Entrepreneurship", "Operations Management", 
        "International Business", "Supply Chain Management", "Economics", "Strategic Management"
    ],
    "Engineering and Technology": [
        "Mechanical Engineering", "Electrical Engineering", "Civil Engineering", 
        "Chemical Engineering", "Aerospace Engineering", "Biomedical Engineering", 
        "Environmental Engineering", "Industrial Engineering", 
        "Materials Science and Engineering", "Robotics and Automation"
    ],
    "Natural Sciences": [
        "Physics", "Chemistry", "Biology", "Earth Sciences (Geology, Meteorology)", 
        "Environmental Science", "Astronomy and Astrophysics", "Mathematics", 
        "Statistics", "Ecology and Evolution", "Oceanography"
    ],
    "Social Sciences": [
        "Psychology", "Sociology", "Anthropology", "Political Science", 
        "Economics", "Geography", "Criminology and Criminal Justice", 
        "Linguistics", "International Relations", "Gender Studies"
    ],
    "Arts and Humanities": [
        "History", "Philosophy", "Literature", "Languages and Linguistics", 
        "Art History", "Religious Studies", "Cultural Studies", "Music", 
        "Theatre and Performing Arts", "Visual Arts (Painting, Sculpture)"
    ],
    "Health and Medicine": [
        "Medicine and Surgery", "Nursing", "Pharmacy", "Public Health", 
        "Dentistry", "Veterinary Science", "Biomedical Sciences", 
        "Nutrition and Dietetics", "Physical Therapy", "Occupational Therapy"
    ],
    "Education": [
        "Early Childhood Education", "Primary Education", "Secondary Education", 
        "Special Education", "Higher Education", "Educational Technology", 
        "Curriculum and Instruction", "Educational Psychology", 
        "Adult Education", "Physical Education"
    ],
    "Law and Legal Studies": [
        "Law", "International Law", "Corporate Law", "Criminal Law", 
        "Environmental Law", "Intellectual Property Law", "Human Rights Law", 
        "Tax Law", "Family Law", "Labor and Employment Law"
    ],
    "Miscellaneous and Emerging Fields": [
        "Environmental Sustainability", "Sports Management", 
        "Media and Communication Studies", "Journalism", 
        "Library and Information Science", "Urban Planning", 
        "Fashion Design", "Culinary Arts", "Hospitality Management", 
        "Ethics and Social Responsibility"
    ]
}

def classify_specialty(specialty, max_retries=3):
    # Construct the full prompt text including the list of fields and majors
    prompt_text = (
        "Classify the following specialty into one of the predefined fields and suggest a specific major within it. "
        "Answer in the format: Field - Major. "
        "If it does not fit into any of the fields, return 'Unclassified - {specialty}'.\n"
        "but try to fit them all into one of the majors . try to use unclassify as the last resort"
        f"Specialty: {specialty}\n"
        "Fields and Majors:\n"
    )
    
    for field, majors in fields_and_majors.items():
        majors_list = ", ".join(majors)
        prompt_text += f"{field}: {majors_list}\n"
    
    prompt = [HumanMessage(content=prompt_text)]
    
    retries = 0
    while retries < max_retries:
        try:
            response = llm.invoke(prompt)
            result = response.content.strip()
            
            # Split the result into field and major
            if " - " in result:
                field, major = result.split(" - ", 1)
                if field in fields_and_majors and major in fields_and_majors[field]:
                    return field, major
                else:
                    return "Unclassified", specialty
            else:
                return "Unclassified", specialty
        except Exception as e:
            st.error(f"Failed to classify specialty '{specialty}': {e}. Retrying...")
            retries += 1
    
    st.error(f"Could not classify specialty '{specialty}' after {max_retries} attempts.")
    return "Unclassified", specialty  # Return as unclassified if all retries fail

# Streamlit App
st.title("Specialty Classification App")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if 'Adjusted Speciality' not in df.columns:
        st.error("The uploaded CSV must contain a column named 'Adjusted Speciality'.")
    else:
        # Add columns for Field and Major
        if 'Field' not in df.columns:
            df['Field'] = ''
        if 'Major' not in df.columns:
            df['Major'] = ''

        # Initialize progress bar and status text
        progress_bar = st.progress(0)
        status_text = st.empty()
        num_rows = len(df)
        checkpoint_interval = num_rows // 10
        checkpoint_file = "checkpoint.csv"

        # Check if a checkpoint file exists to resume progress
        if 'resumed_from_checkpoint' in st.session_state and st.session_state['resumed_from_checkpoint'] and os.path.exists(checkpoint_file):
            df_checkpoint = pd.read_csv(checkpoint_file)
            df.update(df_checkpoint)
            start_index = df_checkpoint.shape[0]
            st.info(f"Resuming from last checkpoint, processed {start_index} rows.")
        else:
            start_index = 0
            st.session_state['resumed_from_checkpoint'] = True

        # Multitasking using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers based on your environment's capabilities
            futures = {executor.submit(classify_specialty, df.at[i, 'Adjusted Speciality']): i for i in range(start_index, num_rows)}

            for future in as_completed(futures):
                i = futures[future]
                field, major = future.result()
                df.at[i, 'Field'] = field
                df.at[i, 'Major'] = major

                # Update progress bar and status text
                progress_percentage = (i + 1) / num_rows
                progress_bar.progress(progress_percentage)
                status_text.text(f"Processing row {i + 1}/{num_rows}")  # Show the current row number being processed

                # Save checkpoint every 10% or at the last row
                if (i + 1) % checkpoint_interval == 0 or i == num_rows - 1:
                    df.iloc[:i + 1].to_csv(checkpoint_file, index=False)

                # Allow download every 1000 rows
                if (i + 1) % 1000 == 0 or i == num_rows - 1:
                    partial_csv = df.iloc[:i + 1].to_csv(index=False)
                    st.download_button(
                        label=f"Download CSV after {i + 1} rows",
                        data=partial_csv,
                        file_name=f'partial_classified_specialities_{i + 1
