import streamlit as st
import smtplib
import ssl
from email.message import EmailMessage

# Streamlit UI
st.title("Titan Email Sender")

# Input fields for credentials
st.header("Enter your Titan email credentials")
email_address = st.text_input("Email Address")
password = st.text_input("Password", type="password")

# Email composition
st.header("Compose your email")
to_email = st.text_input("Recipient Email")
cc_email = st.text_input("CC (optional)", value="")
bcc_email = st.text_input("BCC (optional)", value="")
subject = st.text_input("Subject")
body = st.text_area("Body")
attachment = st.file_uploader("Attach a file", type=["jpg", "png", "pdf", "docx"])

# Send Email
if st.button("Send Email"):
    if email_address and password and to_email and subject and body:
        try:
            # Create email
            msg = EmailMessage()
            msg['From'] = email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.set_content(body)

            if cc_email:
                msg['Cc'] = cc_email
            if bcc_email:
                msg['Bcc'] = bcc_email

            # Attach file if uploaded
            if attachment:
                file_name = attachment.name
                msg.add_attachment(attachment.read(), maintype='application',
                                   subtype='octet-stream', filename=file_name)

            # Email sending process
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                server.login(email_address, password)
                server.send_message(msg)

            st.success("Email sent successfully!")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.error("Please fill in all required fields.")

