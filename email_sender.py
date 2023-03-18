# %%
from importlib import reload
import API_details
reload(API_details)
import smtplib
import mimetypes
from email.message import EmailMessage


def attach_file_to_email(email, filename):
    """Attach a file identified by filename, to an email message"""
    with open(filename, 'rb') as f:
        file_data = f.read()
        file_type, _ = mimetypes.guess_type(filename)
        file_type = file_type.split('/', 1)
        email.add_attachment(file_data, maintype=file_type[0], subtype=file_type[1], filename=filename)

msg = EmailMessage()
msg['Subject'] = 'KIWI API data'
msg['From'] = f"{API_details.EMAIL_USERNAME}@gmail.com"
msg['To'] = f"{API_details.EMAIL_RECIPIENT}"
attach_file_to_email(msg, 'D:\COding\Python\Python web scraping\Flight tickets\Airfare-flights KIWI API\Graphs\Plotly graphs\Test1 Interactive plot.html')

#Sending the message
with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
    smtp.starttls()
    smtp.login(f"{API_details.EMAIL_USERNAME}@gmail.com", f"{API_details.EMAIL_PASSWORD}")

    smtp.send_message(msg)




# %%
