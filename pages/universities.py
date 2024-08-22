import streamlit as st
import pandas as pd
import re

def clean_data(df):
    # Split Location into State/Province and Country
    df[['State/Province', 'Country']] = df['Location'].str.split(', ', expand=True)
    
    # Clean Tuition: split into Price and Currency
    def split_tuition(tuition):
        if pd.isna(tuition):
            return pd.Series([None, None])
        tuition_cleaned = re.sub(r'[^\d]', '', tuition.split('/')[0])
        currency = re.findall(r'[^\d\s]', tuition.split('/')[0])[0] if len(re.findall(r'[^\d\s]', tuition.split('/')[0])) > 0 else ""
        return pd.Series([int(tuition_cleaned) if tuition_cleaned else None, currency])

    df[['Tuition Price', 'Tuition Currency']] = df['Tuition'].apply(split_tuition)
    
    # Clean Application Fee: split into Price and Currency
    def split_app_fee(fee):
        if pd.isna(fee):
            return pd.Series([None, None])
        fee_cleaned = re.sub(r'[^\d]', '', str(fee))
        currency = re.findall(r'[^\d\s]', str(fee))[0] if len(re.findall(r'[^\d\s]', str(fee))) > 0 else ""
        return pd.Series([int(fee_cleaned) if fee_cleaned else None, currency])

    df[['Application Fee Price', 'Application Fee Currency']] = df['Application fee'].apply(split_app_fee)
    
    # Classify University Name into Institution Type
    def classify_institution(name):
        if "university" in name.lower():
            return "University"
        elif "college" in name.lower():
            return "College"
        elif "institute" in name.lower():
            return "Institute"
        else:
            return "Other"

    df['Institution Type'] = df['University Name'].apply(classify_institution)
    
    # Create a new column for Speciality without the level part
    df['Adjusted Speciality'] = df['Speciality'].apply(lambda x: '-'.join(x.split('-')[1:]).strip() if '-' in x else x)
    
    # Keep all original columns, no columns are dropped
    
    return df

def main():
    st.title("Data Cleaning and Organization App")

    # Upload the file
    uploaded_file = st.file_uploader("Choose your Excel file", type=["xlsx"])

    if uploaded_file is not None:
        # Read the uploaded file
        df = pd.read_excel(uploaded_file)

        # Clean the data
        cleaned_df = clean_data(df)

        # Display the cleaned data
        st.write("Cleaned Data:")
        st.dataframe(cleaned_df)

        # Save the cleaned data to a new CSV file
        csv = cleaned_df.to_csv(index=False)
        st.download_button(
            label="Download Cleaned Data as CSV",
            data=csv,
            file_name='cleaned_universities_data.csv',
            mime='text/csv',
        )

if __name__ == "__main__":
    main()
