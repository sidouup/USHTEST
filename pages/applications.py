import streamlit as st
import smtplib
import ssl
from email.message import EmailMessage

# Define a function to verify login credentials
def verify_login(email_address, password):
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
            server.login(email_address, password)
        return True, None  # Return True and no error message if successful
    except Exception as e:
        return False, str(e)  # Return False and the error message if it fails

# Step 1: Login
st.title("Titan Email Sender")
st.header("Login with your Titan Email")

email_address = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    login_success, error_message = verify_login(email_address, password)
    if login_success:
        st.session_state["logged_in"] = True
        st.success("Login successful! You can now compose your email.")
    else:
        st.error(f"Login failed: {error_message}")

# Step 2: Email Composition (only if logged in)
if "logged_in" in st.session_state and st.session_state["logged_in"]:
    st.header("Compose your email")

    to_email = st.text_input("Recipient Email")
    cc_email = st.text_input("CC (optional)", value="")
    bcc_email = st.text_input("BCC (optional)", value="")
    subject = st.text_input("Subject")
    body = st.text_area("Body")
    attachment = st.file_uploader("Attach a file", type=["jpg", "png", "pdf", "docx"])

    if st.button("Send Email"):
        if to_email and subject and body:
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

                # Send email
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL("smtp.titan.email", 465, context=context) as server:
                    server.login(email_address, password)
                    server.send_message(msg)

                st.success("Email sent successfully!")
            except Exception as e:
                st.error(f"An error occurred while sending the email: {e}")
        else:
            st.error("Please fill in all required fields.")
