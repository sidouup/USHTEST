import streamlit as st
from email.message import EmailMessage
import smtplib
import ssl
from fpdf import FPDF
import PyPDF2
import os
from io import BytesIO

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

    # Get PDF as bytes
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    pdf_output = BytesIO(pdf_bytes)

    pdf_writer = PyPDF2.PdfWriter()
    
    # Add the generated PDF
    pdf_reader = PyPDF2.PdfReader(pdf_output)
    first_page = pdf_reader.pages[0]
    pdf_writer.add_page(first_page)

    # Get the size of the first page
    first_page_size = first_page.mediabox

    # Add the uploaded PDF documents
    if documents:
        for document in documents:
            if document.type == "application/pdf":
                document_bytes = BytesIO(document.read())
                pdf_reader = PyPDF2.PdfReader(document_bytes)
                for page in pdf_reader.pages:
                    try:
                        # Attempt to scale the page, but if it fails, add the page as is
                        page.scale_to(first_page_size.width, first_page_size.height)
                    except Exception as e:
                        st.warning(f"Unable to scale page in document {document.name}. Adding original page.")
                    pdf_writer.add_page(page)

    merged_pdf_path = f"{student['name'].replace(' ', '_')}_merged_application.pdf"
    with open(merged_pdf_path, "wb") as f:
        pdf_writer.write(f)

    return merged_pdf_path
    
# Agent email mapping
agents = {
    "Djazila": "djillaliourradi@theushouse.com",
    "Hamza": "djillaliourradi@theushouse.com",
    "Nessrine": "djillaliourradi@theushouse.com",
    "Nada": "djillaliourradi@theushouse.com",
    "Reda": "djillaliourradi@theushouse.com"
}

# Step 1: Login
st.title("School Application Submission")
st.header("Login with your Titan Email")

agent = st.radio("Select Agent", list(agents.keys()))  # Radio button for agent selection
email_address = "djillaliourradi@theushouse.com"  # Select email based on agent
password = st.text_input("Password", type="password")

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

    recipient_email = st.text_input("Recipient Email")  # Input for recipient email
    school = st.selectbox("Select School", ["CCLS Miami", "CCLS NY NJ", "Connect English",
                                            "CONVERSE SCHOOL", "ELI San Francisco", "F2 Visa", 
                                            "GT Chicago", "BEA Huston", "BIA Huston", "OHLA Miami", 
                                            "UCDEA", "HAWAII"])  # Dropdown list for school selection

    students = []
    num_students = st.number_input("Number of Students", min_value=1, step=1)

    for i in range(num_students):
        st.subheader(f"Student {i+1}")
        name = st.text_input(f"Name of Student {i+1}")
        address = st.text_input(f"Address of Student {i+1}")
        email = st.text_input(f"Email of Student {i+1}")
        phone = st.text_input(f"Phone Number of Student {i+1}")
        program = st.text_input(f"Program Choice of Student {i+1}")
        start_date = st.date_input(f"Start Date of Student {i+1}")
        length = st.text_input(f"Length of Program for Student {i+1}")
        documents = st.file_uploader(f"Upload documents for {name}", type=["pdf"], accept_multiple_files=True)

        students.append({
            "name": name,
            "address": address,
            "email": email,
            "phone": phone,
            "program": program,
            "start_date": start_date,
            "length": length,
            "documents": documents
        })

    if st.button("Generate Email Body and PDFs"):
        if all(student["name"] and student["email"] for student in students) and recipient_email:
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
            st.error("Please make sure all required fields are filled out for each student and that a recipient email is provided.")

    if "email_body" in st.session_state and "pdf_files" in st.session_state and st.button("Send Email"):
        email_body = st.session_state["email_body"]

        msg = EmailMessage()
        msg['From'] = email_address
        msg['To'] = recipient_email  # Use the recipient email from the input
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
        except Exception as e:
            st.error(f"An error occurred while sending the email: {e}")
