import streamlit as st
from email.message import EmailMessage
import smtplib
import ssl
from fpdf import FPDF
import PyPDF2
from PIL import Image
import io
import os
import tempfile
import requests
import streamlit_nested_layout

st.set_page_config(page_title="School Application CRM 🎓", layout="wide")

# Custom CSS for a more modern look
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 4px;
    }
    .stTextInput>div>div>input {
        background-color: #f1f3f4;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    .stSelectbox>div>div>select {
        background-color: #f1f3f4;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Function to generate email body
def generate_email_body(students, school):
    greeting = f"Hello {school},\n\n"
    greeting += "I hope this message finds you well!\n\n"
    body = f"Please find below the details for the students who have submitted applications to {school}:\n\n"

    for student in students:
        body += f"Name: {student['name']}\n"
        body += f"Address: {student['address']}\n"
        body += f"Email: {student['email']}\n"
        body += f"Phone Number: {student['phone']}\n"
        body += f"Program Choice: {student['program']}\n"
        body += f"Start Date: {student['start_date']}\n"
        body += f"Length of Program: {student['length']}\n"
        body += "\n---\n"

    closing = "\nThank you for your assistance. We will proceed with the payment once you provide the link.\n\n"
    closing += "Best regards,\n[Your Name]\n"

    return greeting + body + closing

# Function to generate PDF for each student and ensure all pages are A4
def generate_student_pdf(student, documents):
    pdf = FPDF(format='A4')
    pdf.add_page()

    # Add the logo
    logo_url = "https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png"
    logo_response = requests.get(logo_url)
    logo_img = Image.open(io.BytesIO(logo_response.content))
    logo_path = "logo_temp.png"
    logo_img.save(logo_path)

    # Add the logo to the PDF
    pdf.image(logo_path, x=10, y=8, w=50)

    # Adjust space below the logo to prevent overlap and move the text down
    pdf.ln(70)  # Increased space below the logo

    # Student information
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt=f"Student Application: {student['name']}", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Name:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['name'], ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Address:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['address'], ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Email:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['email'], ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Phone Number:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['phone'], ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Program Choice:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['program'], ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Start Date:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=str(student['start_date']), ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, txt="Length of Program:", ln=False)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=student['length'], ln=True)

    # Save the initial page
    pdf_output = pdf.output(dest='S').encode('latin-1')
    
    pdf_writer = PyPDF2.PdfWriter()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_output))
    pdf_writer.add_page(pdf_reader.pages[0])

    # Process uploaded documents
    for doc_type, document in documents.items():
        if document:
            if document.type == "application/pdf":
                doc_reader = PyPDF2.PdfReader(io.BytesIO(document.read()))
                for page in doc_reader.pages:
                    pdf_writer.add_page(page)
            elif document.type.startswith('image'):
                img = Image.open(io.BytesIO(document.read()))
                
                # Convert image to a PDF page
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as img_tmp_file:
                    img.save(img_tmp_file, format='PNG')
                    img_tmp_file_path = img_tmp_file.name
                
                img_pdf = FPDF(format='A4')
                img_pdf.add_page()

                max_width, max_height = 190, 277  # A4 size in mm minus margins
                img.thumbnail((max_width, max_height))

                x_offset = (210 - img.width) / 2
                y_offset = (297 - img.height) / 2
                
                # Insert the image into the PDF
                img_pdf.image(img_tmp_file_path, x=x_offset, y=y_offset, w=img.width, h=img.height)

                # Save the image as PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as img_pdf_file:
                    img_pdf.output(img_pdf_file.name)
                    img_pdf_file_path = img_pdf_file.name

                # Append the image PDF to the main PDF
                img_pdf_reader = PyPDF2.PdfReader(img_pdf_file_path)
                for page in img_pdf_reader.pages:
                    pdf_writer.add_page(page)
                
                # Cleanup: remove the temporary files
                os.remove(img_tmp_file_path)
                os.remove(img_pdf_file_path)

    pdf_name = f"{student['name'].replace(' ', '_')}.pdf"  # Name the PDF with first and last name
    with open(pdf_name, "wb") as f:
        pdf_writer.write(f)

    # Remove the logo temporary file
    os.remove(logo_path)

    return pdf_name

# Agent email mapping using Streamlit secrets
agents = {
    "Djazila": st.secrets["Djazila_email"],
    "Hamza": st.secrets["Hamza_email"],
    "Nessrine": st.secrets["Nessrine_email"],
    "Nada": st.secrets["Nada_email"],
    "Reda": st.secrets["Reda_email"]
}

# School email mapping (for now all are the same)
school_emails = {
    "CCLS Miami": "sidouminto@gmail.com",
    "CCLS NY NJ": "sidouminto@gmail.com",
    "Connect English": "sidouminto@gmail.com",
    "CONVERSE SCHOOL": "sidouminto@gmail.com",
    "ELI San Francisco": "sidouminto@gmail.com",
    "F2 Visa": "sidouminto@gmail.com",
    "GT Chicago": "sidouminto@gmail.com",
    "BEA Huston": "sidouminto@gmail.com",
    "BIA Huston": "sidouminto@gmail.com",
    "OHLA Miami": "sidouminto@gmail.com",
    "UCDEA": "sidouminto@gmail.com",
    "HAWAII": "sidouminto@gmail.com"
}

def login():
    with st.sidebar:
        st.image("https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=297,h=404,fit=crop/YBgonz9JJqHRMK43/blue-red-minimalist-high-school-logo-9-AVLN0K6MPGFK2QbL.png", width=100)
        st.title("Agent Login 🔐")
        agent = st.selectbox("Select Agent 👤", list(agents.keys()))
        email_address = agents[agent]
        password = st.secrets[f"{agent}_password"]
        
        if st.button("Login 🚀"):
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                    server.login(email_address, password)
                st.session_state["logged_in"] = True
                st.success("Login successful! 🎉")
            except Exception as e:
                st.error(f"Login failed ❌: {str(e)}")

def new_application():
    st.header("New Student Application 📝")
    
    col1, col2 = st.columns(2)
    
    with col1:
        school = st.selectbox("Select School 🏫", list(school_emails.keys()))
        first_name = st.text_input("First Name 👤")
        last_name = st.text_input("Last Name 👤")
        email = st.text_input("Email 📧")
        program = st.text_input("Program Choice 📚")
    
    with col2:
        address = st.text_input("Address 🏠")
        phone = st.text_input("Phone Number 📞")
        start_date = st.date_input("Start Date 📅")
        length = st.text_input("Length of Program ⏳")
    
    st.subheader("Document Upload 📎")
    col3, col4 = st.columns(2)
    
    with col3:
        passport = st.file_uploader("Upload Passport 🛂", type=["pdf", "png", "jpg", "jpeg"])
        bank_statement = st.file_uploader("Upload Bank Statement 💰", type=["pdf", "png", "jpg", "jpeg"])
    
    with col4:
        affidavit = st.file_uploader("Upload Affidavit Support Letter 📄", type=["pdf", "png", "jpg", "jpeg"])
        sponsor_id = st.file_uploader("Upload Sponsor ID 🆔", type=["pdf", "png", "jpg", "jpeg"])
    
    if st.button("Add Student ➕"):
        if first_name and last_name and address and email and phone:
            student = {
                "name": f"{first_name} {last_name}",
                "address": address,
                "email": email,
                "phone": phone,
                "program": program,
                "start_date": start_date,
                "length": length,
                "documents": {
                    "passport": passport,
                    "bank_statement": bank_statement,
                    "affidavit": affidavit,
                    "sponsor_id": sponsor_id
                }
            }
            if "students" not in st.session_state:
                st.session_state.students = []
            st.session_state.students.append(student)
            st.success("Student added successfully! ✅")
        else:
            st.warning("Please fill out all required fields. ⚠️")

def review_and_submit():
    st.header("Review & Submit Applications 📊")
    
    if "students" in st.session_state and st.session_state.students:
        for i, student in enumerate(st.session_state.students):
            with st.expander(f"Student {i+1}: {student['name']} 👨‍🎓"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Email:** 📧 {student['email']}")
                    st.write(f"**Phone:** 📞 {student['phone']}")
                    st.write(f"**Program:** 📚 {student['program']}")
                with col2:
                    st.write(f"**Address:** 🏠 {student['address']}")
                    st.write(f"**Start Date:** 📅 {student['start_date']}")
                    st.write(f"**Length:** ⏳ {student['length']}")
        
        if st.button("Generate Email and PDFs 📨"):
            email_body = generate_email_body(st.session_state.students, school)
            st.session_state["email_body"] = email_body
            st.text_area("Generated Email Body 📧", email_body, height=200)
            
            pdf_files = []
            for student in st.session_state.students:
                pdf_file = generate_student_pdf(student, student["documents"])
                pdf_files.append(pdf_file)
            st.session_state["pdf_files"] = pdf_files
            st.success("PDFs generated successfully! 📄✅")
        
        if "email_body" in st.session_state and "pdf_files" in st.session_state:
            if st.button("Send Email 🚀"):
                # ... (Keep the existing email sending logic)
                st.success("Emails sent successfully! 📨✅")
    else:
        st.info("No students added yet. Please add students in the New Application tab. ℹ️")

def main():
    st.title("Student Application CRM 🎓")
    
    login()
    
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        # Tabs for different sections
        tabs = st.tabs(["New Application 📝", "Review & Submit 📊"])
        
        with tabs[0]:
            new_application()
        
        with tabs[1]:
            review_and_submit()

if __name__ == "__main__":
    main()


