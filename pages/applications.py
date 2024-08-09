import streamlit as st
from email.message import EmailMessage
import smtplib
import ssl

# Function to generate email body
def generate_email_body(students):
    greeting = "Hello [Recipient's Name],\n\n"
    greeting += "I hope everything is going well for you and the team!\n\n"
    body = "Here are the details for the students who have submitted applications:\n\n"

    for student in students:
        body += f"Name: {student['name']}\n"
        body += f"Address: {student['address']}\n"
        body += f"Email: {student['email']}\n"
        body += f"Phone Number: {student['phone']}\n"
        body += f"Program Choice: {student['program']}\n"
        body += f"Start Date: {student['start_date']}\n"
        body += f"Length of Program: {student['length']}\n"
        body += "\n---\n"

    closing = "\nThank you for your patience. We will proceed with the next steps as discussed.\n\n"
    closing += "Good luck, and see you soon!\n\nBest regards,\n[Your Name]\n"

    return greeting + body + closing

# Step 1: Login
st.title("School Application Submission")
st.header("Login with your Titan Email")

email_address = st.text_input("Email Address")
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

    if st.button("Generate and Send Email"):
        if all(student["name"] and student["email"] for student in students):
            email_body = generate_email_body(students)

            msg = EmailMessage()
            msg['From'] = email_address
            msg['To'] = "[Recipient's Email]"  # Replace with the actual recipient's email
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
        else:
            st.error("Please make sure all required fields are filled out for each student.")
