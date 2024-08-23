import streamlit as st
import pandas as pd

# Set the title of the Streamlit app
st.title("Count Fields and Majors in Classified CSV")

# File uploader for the user to upload a CSV file
uploaded_file = st.file_uploader("Upload the classified CSV file", type=["csv"])

# Check if a file has been uploaded
if uploaded_file:
    # Load the uploaded CSV into a pandas DataFrame
    df = pd.read_csv(uploaded_file)

    # Ensure the required columns are present in the CSV
    if 'Field' not in df.columns or 'Major' not in df.columns:
        st.error("The uploaded CSV must contain 'Field' and 'Major' columns.")
    else:
        # Count the number of occurrences of each unique field
        field_counts = df['Field'].value_counts().reset_index()
        field_counts.columns = ['Field', 'Count']

        # Count the number of occurrences of each unique major within each field
        major_counts = df.groupby(['Field', 'Major']).size().reset_index(name='Count')

        # Display the results
        st.write("### Number of Specialties in Each Field")
        st.dataframe(field_counts)

        st.write("### Number of Specialties in Each Major within Each Field")
        st.dataframe(major_counts)

        # Summary of total unique fields and majors
        total_unique_fields = df['Field'].nunique()
        total_unique_majors = df['Major'].nunique()

        st.write(f"**Total number of unique fields:** {total_unique_fields}")
        st.write(f"**Total number of unique majors:** {total_unique_majors}")
else:
    st.info("Please upload a classified CSV file to proceed.")
