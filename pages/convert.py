import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI

# Retrieve the API key from Streamlit secrets
api_key = st.secrets["API_KEY_gemini"]

# Initialize the Google Gemini model with the updated model version and API key
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

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
        ("system", "Classify the following specialty into one of the predefined majors:"),
        ("human", specialty)
    ]
    response = llm.invoke(prompt)
    return response.content.strip()

# Streamlit App
st.title("Specialty Classification App")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    if 'Adjusted Speciality' not in df.columns:
        st.error("The uploaded CSV must contain a column named 'Adjusted Speciality'.")
    else:
        # Apply classification function
        df['Classified Major'] = df['Adjusted Speciality'].apply(classify_specialty)
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
