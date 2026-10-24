from flask import Flask
from flask_mail import Mail, Message

from modules.settings import public_base_url
from modules.sql_module import UserModule


class MailProcess:
    mail: Mail
    app: Flask

    def __init__(self, app:Flask) -> None:
        self.mail = Mail(app)
        self.app = app
        
    def send_verify_mail(self, user:UserModule)->bool:
        base_url = self._base_url()
        if base_url is None:
            return False

        msg_title = 'Hello It is checking mail'
        #  寄件者，若參數有設置就不需再另外設置
        msg_sender = 'Sender Mail@mail_domain.com'
        #  收件者，格式為list，否則報錯
        msg_recipients:list[str | tuple[str, str]] | None = [user.mail]
        #  郵件內容
        # msg_body = 'Hey, I am mail body!'
        # 也可以利用html做內容
        msg_html:str = f'<h1>Hey, this is verify mail. Please click <a href=\"{base_url}/auth/mailverify?user={user.username}&mail_number={user.mail_check_number}\">this</a></h1>'
        msg = Message(subject=msg_title,
                      sender=msg_sender,
                      recipients=msg_recipients)
        # msg.body = msg_body
        msg.html = msg_html

        return self._send(msg)

    def send_reset_mail(self, user:UserModule, reset_nu:int)->bool:
        base_url = self._base_url()
        if base_url is None:
            return False

        msg_title = 'Hello It is reset Mail'
        #  寄件者，若參數有設置就不需再另外設置
        msg_sender = 'Sender Mail@mail_domain.com'
        #  收件者，格式為list，否則報錯
        msg_recipients:list[str | tuple[str, str]] | None = [user.mail]
        #  郵件內容
        # msg_body = 'Hey, I am mail body!'
        # 也可以利用html做內容
        msg_html:str = f"<h1>Reset Password</h1><p>Hey, this is reset mail. <br>Please click <a href=\"{base_url}/auth/reset_passwd?user={user.username}&resetId={reset_nu}\">Here</a></p>"
        msg = Message(subject=msg_title,
                      sender=msg_sender,
                      recipients=msg_recipients)
        # msg.body = msg_body
        msg.html = msg_html

        return self._send(msg)

    def _base_url(self)->str | None:
        try:
            return public_base_url()
        except RuntimeError:
            self.app.logger.exception("取得對外網址失敗，無法寄信")
            return None

    def _send(self, msg:Message)->bool:
        #  同步寄送，才能知道是否寄送成功
        try:
            with self.app.app_context():
                self.mail.send(msg)
        except Exception:
            # 不記錄收件者 Email（個資），只記錄網域方便排查是否為特定信箱服務的問題
            self.app.logger.exception("寄信失敗：domain=%s", _mail_domain(msg.recipients))
            return False
        self.app.logger.info("寄信成功")
        return True


def _mail_domain(recipients: list | None) -> str:
    """只取第一位收件者的網域（例如 gmail.com），避免把完整 Email 寫進 log"""
    if not recipients:
        return "-"
    first = recipients[0]
    addr = first[1] if isinstance(first, tuple) else first   # Flask-Mail 收件者可為 (名稱, Email)
    return addr.rsplit("@", 1)[-1] if "@" in addr else "-"
