from flask import Flask
from flask.config import T
from flask_mail import Mail, Message
from threading import Thread
from modules.sql_module import UserModule

class MailProcess:
    mail: Mail
    app: Flask
    _mtqoo:Thread|None
    tunnel_url:str|None

    def __init__(self, app:Flask, _tunnel_url:str = "") -> None:
        self.mail = Mail(app)
        self.app = app
        self._mtqoo = None
        self.tunnel_url = _tunnel_url
        
    def start_mail_thread(self, user:UserModule)->None:
        msg_title = 'Hello It is checking mail'
        #  寄件者，若參數有設置就不需再另外設置
        msg_sender = 'Sender Mail@mail_domain.com'
        #  收件者，格式為list，否則報錯
        print(f"user maile = {user.mail}")
        msg_recipients:list[str | tuple[str, str]] | None = [user.mail]
        #  郵件內容
        # msg_body = 'Hey, I am mail body!'
        # 也可以利用html做內容
        msg_html:str = f'<h1>Hey, this is verify mail. Please click <a href=\"{self.tunnel_url}/auth/mailverify?user={user.username}&mail_number={user.mail_check_number}\">this</a></h1>'
        msg = Message(subject=msg_title,
                      sender=msg_sender,
                      recipients=msg_recipients)
        # msg.body = msg_body
        msg.html = msg_html
    
        #  使用多線程
        self._mtqoo = Thread(target=self.send_async_email, args=[self.app, msg])
        self._mtqoo.start()
        print(f"You Send Mail by Flask-Mail Success!!")
    
    def send_async_email(self,app:Flask, msg:Message)->None:
    #  下面有說明
         with app.app_context():
            self.mail.send(msg)


        


