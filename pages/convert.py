import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from concurrent.futures import ThreadPoolExecutor, as_completed
import os  # Import os for file handling

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
    "Data Science", "Linguistics", "Theater Arts", "Biochemistry", "Urban Planning", "Artificial Intelligence"
]

def classify_specialty(specialty):
    prompt = [
        HumanMessage(
            content=[
                {"type": "text", "text": "Classify the following specialty into one of the predefined majors.answer only by the major name dont give any explanation or any thing else . give back as an output only the major selected . if it does not fit on any of the majors give back (Other) . /n majors :"},
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
                result = future.result()
                df.at[i, 'Classified Major'] = result

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
                        file_name=f'partial_classified_specialities_{i + 1}.csv',
                        mime='text/csv'
                    )

        st.write("Classification Results:")
        st.dataframe(df)

        # Final download button for the full dataset
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Final Results as CSV",
            data=csv,
            file_name='classified_specialities.csv',
            mime='text/csv'
        )

        # Clear the checkpoint after successful completion
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
