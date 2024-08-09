import streamlit as st
from email.message import EmailMessage
import smtplib
import ssl

# Function to generate email body
def generate_email_body(students, school):
    greeting = "Hello [Recipient's Name],\n\n"
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

# Agent email mapping
agents = {
    "Djazila": "djazila@yourdomain.com",
    "Hamza": "hamza@yourdomain.com",
    "Nessrine": "nessrine@yourdomain.com",
    "Nada": "nada@yourdomain.com",
    "Reda": "reda@yourdomain.com"
}

# Step 1: Login
st.title("School Application Submission")
st.header("Login with your Titan Email")

agent = st.radio("Select Agent", list(agents.keys()))  # Radio button for agent selection
email_address = agents[agent]  # Select email based on agent
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

        students.append({
            "name": name,
            "address": address,
            "email": email,
            "phone": phone,
            "program": program,
            "start_date": start_date,
            "length": length
        })

    if st.button("Generate Email Body"):
        if all(student["name"] and student["email"] for student in students) and recipient_email:
            email_body = generate_email_body(students, school)
            st.session_state["email_body"] = email_body  # Store the email body in session state
            st.text_area("Generated Email Body", email_body, height=300)  # Show the generated email body
        else:
            st.error("Please make sure all required fields are filled out for each student and that a recipient email is provided.")

    if "email_body" in st.session_state and st.button("Send Email"):
        email_body = st.session_state["email_body"]

        msg = EmailMessage()
        msg['From'] = "Djillaliourradi@theushouse.com"
        msg['To'] = "sidouminto@gmail.com"  # Use the recipient email from the input
        msg['Subject'] = "Student Applications Submission"
        msg.set_content(email_body)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                server.login(email_address, password)
                server.send_message(msg)

            st.success("Email sent successfully!")
        except Exception as e:
            st.error(f"An error occurred while sending the email: {e}")
