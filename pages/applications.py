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


# Function to generate email body
def generate_email_body(students, school):
    greeting = f"Hello {school},\n\n"
    greeting += "I hope everything is going well for you and the team!\n\n"
    body = f"Here are the details for the students who have submitted applications for {school}:\n\n"

    for student in students:
        body += f"Name: {student['name']}\n"
        body += f"Address: {student['address']}\n"
        body += f"Email: {student['email']}\n"
        body += f"Phone Number: {student['phone']}\n"
        body += f"Program Choice: {student['program']}\n"
        body += f"Start Date: {student['start_date']}\n"
        body += f"Length of Program: {student['length']}\n"
        body += "\n---\n"

    closing = "\nThank you for your help. We will proceed with the payment once you send us the link.\n\n"
    closing += "Good luck, and see you soon!\n\nBest regards,\n[Your Name]\n"

    return greeting + body + closing

# Function to generate PDF for each student and ensure all pages are A4
def generate_student_pdf(student, documents):
    pdf = FPDF(format='A4')
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Student Application: {student['name']}", ln=True, align='C')

    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Name: {student['name']}", ln=True)
    pdf.cell(200, 10, txt=f"Address: {student['address']}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {student['email']}", ln=True)
    pdf.cell(200, 10, txt=f"Phone Number: {student['phone']}", ln=True)
    pdf.cell(200, 10, txt=f"Program Choice: {student['program']}", ln=True)
    pdf.cell(200, 10, txt=f"Start Date: {student['start_date']}", ln=True)
    pdf.cell(200, 10, txt=f"Length of Program: {student['length']}", ln=True)

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

# Step 1: Login
st.title("School Application Submission")
st.header("Login with your Titan Email")

agent = st.selectbox("Select Agent", list(agents.keys()))  # Dropdown for agent selection
email_address = agents[agent]  # Fetch email based on agent
password = st.secrets[f"{agent}_password"]  # Fetch password from secrets

if st.button("Login"):
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
            server.login(email_address, password)
        st.session_state["logged_in"] = True
        st.success("Login successful! You can now submit student applications.")
    except Exception as e:
        st.error(f"Login failed: {str(e)}")

# Step 2: Student Application Submission (only if logged in)
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.header("Submit Student Applications")

    school = st.selectbox("Select School", list(school_emails.keys()))  # Dropdown list for school selection
    recipient_email = school_emails[school]  # Automatically set recipient email based on school selection

    students = []
    num_students = st.number_input("Number of Students", min_value=1, step=1)

    for i in range(num_students):
        st.subheader(f"Student {i+1}")
        first_name = st.text_input(f"First Name of Student {i+1}", key=f"first_name_{i}")
        last_name = st.text_input(f"Last Name of Student {i+1}", key=f"last_name_{i}")
        full_name = f"{first_name} {last_name}"
        address = st.text_input(f"Address of Student {i+1}", key=f"address_{i}")
        email = st.text_input(f"Email of Student {i+1}", key=f"email_{i}")
        phone = st.text_input(f"Phone Number of Student {i+1}", key=f"phone_{i}")
        program = st.text_input(f"Program Choice of Student {i+1}", key=f"program_{i}")
        start_date = st.date_input(f"Start Date of Student {i+1}", key=f"start_date_{i}")
        length = st.text_input(f"Length of Program for Student {i+1}", key=f"length_{i}")
        
        # Adding unique keys to each file uploader
        passport = st.file_uploader(f"Upload Passport for {full_name}", type=["pdf", "png", "jpg", "jpeg"], key=f"passport_{i}")
        bank_statement = st.file_uploader(f"Upload Bank Statement for {full_name}", type=["pdf", "png", "jpg", "jpeg"], key=f"bank_statement_{i}")
        affidavit = st.file_uploader(f"Upload Affidavit Support Letter for {full_name}", type=["pdf", "png", "jpg", "jpeg"], key=f"affidavit_{i}")
        sponsor_id = st.file_uploader(f"Upload Sponsor ID for {full_name}", type=["pdf", "png", "jpg", "jpeg"], key=f"sponsor_id_{i}")

        students.append({
            "name": full_name,
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
        })

# Ensure email_body is properly created and stored before sending emails

    if st.button("Generate Email Body and PDFs"):
        if all(student["name"] and student["email"] for student in students):
            email_body = generate_email_body(students, school)
            st.session_state["email_body"] = email_body  # Store the email body in session state
    
            st.text_area("Generated Email Body", email_body, height=300)  # Show the generated email body
    
            # Generate PDFs for each student
            pdf_files = []
            for student in students:
                pdf_file = generate_student_pdf(student, student["documents"])
                pdf_files.append(pdf_file)
    
            st.session_state["pdf_files"] = pdf_files  # Store generated PDF file paths in session state
    
            st.success("PDFs generated successfully!")
        else:
            st.error("Please make sure all required fields are filled out for each student.")
    
    # Ensure that "Send Email" only works if email_body is already defined
    if "email_body" in st.session_state and "pdf_files" in st.session_state:
        if st.button("Send Email"):
            email_body = st.session_state["email_body"]
    
            msg = EmailMessage()
            msg['From'] = email_address
            msg['To'] = recipient_email  # Automatically selected school email
            msg['Subject'] = "Student Applications Submission"
            msg.set_content(email_body)
    
            # Attach PDFs to the email
            for pdf_file in st.session_state["pdf_files"]:
                with open(pdf_file, "rb") as f:
                    file_data = f.read()
                    file_name = os.path.basename(pdf_file)
                    msg.add_attachment(file_data, maintype="application", subtype="pdf", filename=file_name)
    
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                    server.login(email_address, password)
                    server.send_message(msg)
    
                st.success("Email sent successfully!")
                # Cleanup: Remove PDF files after sending
                for pdf_file in st.session_state["pdf_files"]:
                    os.remove(pdf_file)
    
                # Send a copy to the agent's email address
                msg['To'] = email_address  # Send to agent's email
                with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                    server.send_message(msg)
    
                st.success(f"Copy of the email sent to {email_address}!")
                
            except Exception as e:
                st.error(f"An error occurred while sending the email: {e}")
