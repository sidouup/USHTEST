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

# Define the expanded list of fields and their corresponding majors
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
        "International Business", "Supply Chain Management", "Economics", "Strategic Management",
        "Management"
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
    ],
    "English and ESL": [
        "English Language Studies", "ESL (English as a Second Language)"
    ],
    "Tourism and Hospitality": [
        "Tourism Management", "Hospitality Management"
    ],
    "Foundation Year": [
        "Foundation Studies", "Pathways Programs"
    ]
}

def reclassify_specialty(specialty, max_retries=3):
    # Construct the full prompt text including the list of fields and majors
    prompt_text = (
        "Classify the following specialty into one of the predefined fields and suggest a specific major within it. "
        "Answer in the format: Field - Major. "
        "Try to fit them all into one of the majors, using 'Unclassified' only as a last resort.\n"
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
            st.error(f"Failed to reclassify specialty '{specialty}': {e}. Retrying...")
            retries += 1
    
    st.error(f"Could not reclassify specialty '{specialty}' after {max_retries} attempts.")
    return "Unclassified", specialty  # Return as unclassified if all retries fail

# Streamlit App
st.title("Specialty Reclassification App")

# Upload CSV file
uploaded_file = st.file_uploader("Upload the CSV file with unclassified fields", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if 'Field' not in df.columns or 'Major' not in df.columns:
        st.error("The uploaded CSV must contain 'Field' and 'Major' columns.")
    else:
        # Filter out unclassified entries
        unclassified_df = df[df['Field'] == "Unclassified"]

        if unclassified_df.empty:
            st.info("No unclassified entries found. All specialties are classified.")
        else:
            st.write(f"Found {len(unclassified_df)} unclassified entries. Reclassifying...")

            # Initialize progress bar and status text
            progress_bar = st.progress(0)
            status_text = st.empty()
            num_unclassified = len(unclassified_df)
            checkpoint_interval = max(1, num_unclassified // 10)
            checkpoint_file = "reclassification_checkpoint.csv"

            # Multitasking using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers based on your environment's capabilities
                futures = {executor.submit(reclassify_specialty, unclassified_df.at[i, 'Adjusted Speciality']): i for i in unclassified_df.index}

                for future in as_completed(futures):
                    i = futures[future]
                    field, major = future.result()
                    df.at[i, 'Field'] = field
                    df.at[i, 'Major'] = major

                    # Update progress bar and status text
                    num_processed = len(df[df['Field'] != "Unclassified"])
                    progress_percentage = num_processed / num_unclassified
                    progress_bar.progress(progress_percentage)
                    status_text.text(f"Reclassifying row {i + 1}/{num_unclassified}")  # Show the current row number being processed

                    # Save checkpoint every 10% or at the last row
                    if num_processed % checkpoint_interval == 0 or i == unclassified_df.index[-1]:
                        df.to_csv(checkpoint_file, index=False)

            st.write("Reclassification Results:")
            st.dataframe(df)

            # Final download button for the full dataset
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Reclassified Results as CSV",
                data=csv,
                file_name='reclassified_specialities.csv',
                mime='text/csv'
            )

            # Clear the checkpoint after successful completion
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)

        # Display count of fields and majors
        st.write("### Count of Classified and Unclassified Entries")
        total_classified = df[df['Field'] != "Unclassified"].shape[0]
        total_unclassified = df[df['Field'] == "Unclassified"].shape[0]
        total_fields = df['Field'].nunique() - (1 if "Unclassified" in df['Field'].unique() else 0)  # Exclude 'Unclassified'
        total_majors = df['Major'].nunique() - (1 if "Unclassified" in df['Major'].unique() else 0)  # Exclude 'Unclassified'

        st.write(f"Total classified entries: {total_classified}")
        st.write(f"Total unclassified entries: {total_unclassified}")
        st.write(f"Total unclassified entries: {total_unclassified}")
        st.write(f"Total number of unique fields (excluding 'Unclassified'): {total_fields}")
        st.write(f"Total number of unique majors (excluding 'Unclassified'): {total_majors}")

        # Display breakdown of classified fields and majors
        classified_field_counts = df[df['Field'] != "Unclassified"]['Field'].value_counts().reset_index()
        classified_field_counts.columns = ['Field', 'Count']
        st.write("### Number of Specialties in Each Classified Field")
        st.dataframe(classified_field_counts)

        classified_major_counts = df[df['Field'] != "Unclassified"].groupby(['Field', 'Major']).size().reset_index(name='Count')
        st.write("### Number of Specialties in Each Classified Major within Each Field")
        st.dataframe(classified_major_counts)

        # Display unclassified specialties if there are any
        if total_unclassified > 0:
            st.write("### Unclassified Specialties")
            st.write("These specialties could not be classified even after reclassification attempts:")
            st.dataframe(df[df['Field'] == "Unclassified"]['Adjusted Speciality'])

        # Allow downloading of the final CSV with all classifications
        final_csv = df.to_csv(index=False)
        st.download_button(
            label="Download Final Classified CSV",
            data=final_csv,
            file_name='final_classified_specialities.csv',
            mime='text/csv'
        )
else:
    st.info("Please upload a CSV file to proceed.")
