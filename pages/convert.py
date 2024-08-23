import streamlit as st
import pandas as pd

# Function to count the occurrences of each category in the Classified Major column
def count_categories(df):
    # Check if 'Classified Major' column exists
    if 'Classified Major' not in df.columns:
        st.error("The DataFrame does not contain a 'Classified Major' column.")
        return None
    
    # Count the occurrences of each category in the 'Classified Major' column
    category_counts = df['Classified Major'].value_counts()
    
    return category_counts

# Streamlit App
st.title("Category Counter for Classified Majors")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your classified CSV file", type=["csv"])
if uploaded_file:
    # Load the uploaded CSV file into a DataFrame
    df = pd.read_csv(uploaded_file)
    
    # Display the uploaded DataFrame
    st.write("Uploaded Data:")
    st.dataframe(df)

    # Count categories in the 'Classified Major' column
    category_counts = count_categories(df)
    
    if category_counts is not None:
        # Display the counts
        st.write("Category counts in 'Classified Major':")
        st.dataframe(category_counts)

        # Provide download option for the counts
        category_counts_df = category_counts.reset_index()
        category_counts_df.columns = ['Classified Major', 'Count']
        csv = category_counts_df.to_csv(index=False)
        st.download_button(
            label="Download Category Counts as CSV",
            data=csv,
            file_name='category_counts.csv',
            mime='text/csv'
        )
else:
    st.info("Please upload a CSV file to proceed.")
