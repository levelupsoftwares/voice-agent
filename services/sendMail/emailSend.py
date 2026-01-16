import os
import smtplib
# from config.emailAccount import senderEmail , appPassword
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv(".env.local")
senderEmail = os.getenv("SENDER_EMAIL")
appPassword= os.getenv("APP_PASSWORD")


def emailSend(emailaddress , body , subject ):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject          
        msg['From'] = "sudo.usmanbutt@gmail.com" 
        msg['To'] = emailaddress        
        msg.set_content(body)
        s = smtplib.SMTP('smtp.gmail.com',587)
        s.starttls()
        s.login(senderEmail,appPassword)
        s.send_message(msg)
        
        s.quit()

    except Exception as ex:
        print('....................email function is not working...........',repr(ex))
