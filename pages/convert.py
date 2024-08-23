import pandas as pd

# Function to count the occurrences of each category in the Classified Major column
def count_categories(file_path):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(file_path)
    
    # Check if 'Classified Major' column exists
    if 'Classified Major' not in df.columns:
        print("The CSV file does not contain a 'Classified Major' column.")
        return
    
    # Count the occurrences of each category in the 'Classified Major' column
    category_counts = df['Classified Major'].value_counts()
    
    # Display the results
    print("Category counts in 'Classified Major':")
    print(category_counts)

    return category_counts

# Example usage: replace 'classified_specialities.csv' with your CSV file path
file_path = 'classified_specialities.csv'
category_counts = count_categories(file_path)

# Save the counts to a new CSV file
if category_counts is not None:
    category_counts.to_csv('category_counts.csv', index=True, header=['Count'])
    print("\nCategory counts saved to 'category_counts.csv'.")
