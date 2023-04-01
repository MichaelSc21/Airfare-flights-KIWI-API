# %%
from importlib import reload
import Getting_data.API_details as API_details
reload(API_details)
import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


def send_mail(        
        send_from = f"{API_details.EMAIL_USERNAME}", 
        send_to = f"{API_details.EMAIL_RECIPIENT}", 
        subject = 'Third attempt at sending an email',
        files=[],
        username =  f"{API_details.EMAIL_USERNAME}",
        password = f"{API_details.EMAIL_PASSWORD}",
        message = 'Lets see if this works',
        server = "smtp.gmail.com",
        port = 587):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    #Creating the email message that is going to be sent
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(message))

    files_to_be_sent = []
    if isinstance(files, list):
        if len(files) == 0:
            raise KeyError("there is no files passed into the function send_mail in the email_sender file")
        for i in range(len(files)):
            files_to_be_sent.append(os.path.join(files[i]))
    else:
        files_to_be_sent.append(os.path.join(files))


    # attaching the files to the email message 
    for path in files_to_be_sent:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    #Creating a connection with the mail server and sending the email message
    smtp = smtplib.SMTP(server, port)
    smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()






if __name__ == '__main__':
    details_email = dict(        
        send_from = f"{API_details.EMAIL_USERNAME}", 
        send_to = f"{API_details.EMAIL_RECIPIENT}", 
        subject = 'Third attempt at sending an email',
        files=[API_details.FILE_GRAPH_PLOTLY],
        username =  f"{API_details.EMAIL_USERNAME}",
        password = f"{API_details.EMAIL_PASSWORD}",
        message = 'Lets see if this works',
        server = "smtp.gmail.com",
        port = 587
)
    send_mail(
        send_from = f"{API_details.EMAIL_USERNAME}@gmail.com", 
        send_to = f"{API_details.EMAIL_RECIPIENT}", 
        subject = 'Third attempt at sending an email',
        files=[os.path.join(API_details.FILE_GRAPH_PLOTLY)],
        username =  f"{API_details.EMAIL_USERNAME}@gmail.com",
        password = f"{API_details.EMAIL_PASSWORD}",
        message = 'Lets see if this works',
        server = "smtp.gmail.com",
        port = 587
        )

# %%
