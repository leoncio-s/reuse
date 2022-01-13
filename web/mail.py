#from web.Mail import Mail
import re
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import render_template
import datetime
from smtplib import SMTP
import json
import os

class SendMail():
    def __init__(self, to:list):
        self.nome = to[0]
        self.username = to[1]
        self.mail = to[2]
        
        with open(os.path.dirname(os.path.dirname(__file__)) + "/.env.json") as db:
                js = json.load(db)
                self.mail_host= js['MAIL']["MAIL_SERVER"]
                self.mail_port= js['MAIL']['MAIL_PORT']
                self.mail_user= js['MAIL']['MAIL_USERNAME']
                self.mail_password = js['MAIL']["MAIL_PASSWORD"] #os.environ.get('MAIL_PASSWORD')
                self.mail_tls =  js['MAIL']["MAIL_USE_TLS"]
                self.mail_ssl =   js['MAIL']["MAIL_USE_SSL"]
                self.sender = js['MAIL']["MAIL_SENDER"]
		
        self.server = SMTP(self.mail_host, self.mail_port)
        self.server.starttls()
        self.server.login(self.mail_user, self.mail_password)
        
    
    def sendToken(self, token):
        self.token    = re.sub("[^0-9]{6}", "", token)
        
        self.assunto = "Validação de e-mail"
        
        msg = MIMEMultipart("alternative")

        msg["Subject"] =self.assunto
        msg["To"]=self.mail
        msg['From'] = self.sender
        #msg['Date'] = datetime.datetime.now(datetime.timezone.utc)
        #msg['content-type'] = 'html/plain; charset="utf-8"'
        
        context = {
            "subject": self.assunto,
            "nome": self.nome.split(" ")[0],
            "token" : self.token
        }

        text = MIMEText(f"Olá, {self.nome}!\n\n O seu código é:{self.token}", 'plaine')
        html = MIMEText(render_template("mail.html", context=context), 'html')
        
        msg.attach(html)
        
        try:
            self.server.sendmail(self.sender, self.mail, msg.as_string())
            self.server.quit()
        except Exception as e:
            raise e