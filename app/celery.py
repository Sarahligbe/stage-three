from celery import Celery
import smtplib
from email.message import EmailMessage

# Configure Celery
celery = Celery('tasks', broker='amqp://guest@localhost//')

@celery.task
def send_email(recipient):
    msg = EmailMessage()
    msg.set_content("You have reached the endpoint successfully")
    msg['Subject'] = "Welcome!"
    msg['From'] = "youremail@gmail.com"
    msg['To'] = recipient

    #SMTP server details
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "youremail@gmail.com"
    smtp_password = "the-16-digit-app-password"

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()