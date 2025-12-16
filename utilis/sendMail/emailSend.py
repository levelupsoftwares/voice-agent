import smtplib
from utilis.sendMail.emailAccount import senderEmail , appPassword
from email.message import EmailMessage


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

    except:
        print('email function is not working...........')
