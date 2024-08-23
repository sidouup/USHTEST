import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Retrieve the API key from Streamlit secrets (replace with your actual API key)
api_key = st.secrets["api_key"]

# Initialize the Google Gemini model with the updated model version and API key
try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)
except Exception as e:
    st.error(f"Failed to initialize Google Gemini model: {e}")
    st.stop()

# Define the list of big majors
big_majors = [
    "Business Administration", "Computer Science", "Nursing", "Psychology", "Biology",
    "Mechanical Engineering", "Economics", "Electrical Engineering", "Marketing",
    "Education", "Accounting", "Communications", "Political Science", "Finance",
    "Civil Engineering", "Environmental Science", "Chemistry", "Information Technology",
    "Sociology", "Criminal Justice", "Graphic Design", "International Relations", "Physics",
    "History", "Social Work", "English Literature", "Public Health", "Mathematics",
    "Architecture", "Biomedical Engineering", "Philosophy", "Hospitality Management",
    "Human Resources Management", "Anthropology", "Industrial Engineering",
    "Aerospace Engineering", "Journalism", "Fine Arts", "Culinary Arts", "Computer Engineering",
    "Pharmacy", "Cybersecurity", "Music", "Public Relations", "Software Engineering",
    "Data Science", "Linguistics", "Theater Arts", "Biochemistry", "Urban Planning"
]

def classify_specialty(specialty):
    prompt = [
        HumanMessage(
            content=[
                {"type": "text", "text": "Classify the following specialty into one of the predefined majors:"},
                {"type": "text", "text": specialty}
            ]
        )
    ]
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        st.error(f"Failed to classify specialty '{specialty}': {e}")
        return "Error"

# Streamlit App
st.title("Specialty Classification App")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if 'Adjusted Speciality' not in df.columns:
        st.error("The uploaded CSV must contain a column named 'Adjusted Speciality'.")
    else:
        # Initialize progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        num_rows = len(df)
        checkpoint_interval = num_rows // 10
        checkpoint_file = "checkpoint.csv"

        # Check if a checkpoint file exists to resume progress
        if st.session_state.get('resumed_from_checkpoint', False) and st.file_exists(checkpoint_file):
            df_checkpoint = pd.read_csv(checkpoint_file)
            df.update(df_checkpoint)
            start_index = df_checkpoint.shape[0]
            st.info(f"Resuming from last checkpoint, processed {start_index} rows.")
        else:
            start_index = 0
            st.session_state['resumed_from_checkpoint'] = True

        # Apply classification function with progress tracking
        for i in range(start_index, num_rows):
            df.at[i, 'Classified Major'] = classify_specialty(df.at[i, 'Adjusted Speciality'])

            # Update progress bar
            if (i + 1) % checkpoint_interval == 0 or i == num_rows - 1:
                progress_percentage = (i + 1) / num_rows
                progress_bar.progress(progress_percentage)
                status_text.text(f"Processing row {i + 1}/{num_rows}")

                # Save checkpoint every 10%
                df.iloc[:i + 1].to_csv(checkpoint_file, index=False)
        
        st.write("Classification Results:")
        st.dataframe(df)

        # Option to download the results
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name='classified_specialities.csv',
            mime='text/csv'
        )

        # Clear the checkpoint after successful completion
        if st.file_exists(checkpoint_file):
            st.file_remove(checkpoint_file)
